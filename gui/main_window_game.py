from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from pathlib import Path
import threading
import time
import subprocess
import os
import json
import shutil
import re
import requests
from requests.exceptions import ConnectionError, Timeout, RequestException
import minecraft_launcher_lib
from core.config import get_recommended_java_version, get_asset_path, JAVA_DIR
from core.utils import generate_offline_uuid, create_launcher_profiles, get_java_path_from_named_folder
from core.error_logger import write_error_log

# Патч для requests.get, чтобы использовать зеркало BMCLAPI при таймаутах и ошибках соединения
_original_requests_get = requests.get

def _patched_requests_get(url, *args, **kwargs):
    # Устанавливаем таймаут, чтобы не ждать вечно
    if 'timeout' not in kwargs or kwargs['timeout'] is None:
        kwargs['timeout'] = 15
        
    try:
        return _original_requests_get(url, *args, **kwargs)
    except (ConnectionError, Timeout) as e:
        # Ловим только ошибки сети
        error_str = str(e)
        print(f"Ошибка подключения к {url} ({error_str}), пробуем зеркало BMCLAPI...")
        mirror_url = url
        if "launchermeta.mojang.com" in url:
            mirror_url = url.replace("launchermeta.mojang.com", "bmclapi2.bangbang93.com")
        elif "piston-meta.mojang.com" in url:
            mirror_url = url.replace("piston-meta.mojang.com", "bmclapi2.bangbang93.com")
        elif "libraries.minecraft.net" in url:
            mirror_url = url.replace("libraries.minecraft.net", "bmclapi2.bangbang93.com/maven")
            
        if mirror_url != url:
            try:
                print(f"Повторная попытка через зеркало: {mirror_url}")
                kwargs['timeout'] = 20
                return _original_requests_get(mirror_url, *args, **kwargs)
            except Exception as mirror_e:
                print(f"Зеркало тоже недоступно: {mirror_e}")
                raise e
        raise e

requests.get = _patched_requests_get

class MainWindowGame:
    """Класс для игровых функций главного окна"""
    
    def __init__(self):
        self.install_success = False
        self.current_version_type = "release"  # release, snapshot
        self.mc_process = None
        self.mc_log_handle = None
        self.mc_log_path = None
    
    def get_java_path_for_version(self, required_version):
        """
        Возвращает путь к Java указанной версии из именованных папок
        Java8/, Java17/, Java21/ в директории KuLauncher_java
        """
        return get_java_path_from_named_folder(required_version)
    
    def check_java_installed(self, required_version):
        """
        Проверяет, установлена ли указанная версия Java в именованной папке
        """
        java_path = self.get_java_path_for_version(required_version)
        if java_path:
            self.java_path = java_path
            return True
        return False
    
    def check_internet_connection(self):
        """Проверяет наличие подключения к интернету"""
        try:
            import socket
            hosts = ["minecraft.net", "mojang.com", "google.com"]
            for host in hosts:
                try:
                    socket.create_connection((host, 80), timeout=2)
                    return True
                except:
                    continue
            return False
        except:
            return False

    
    def launch_game(self):
        """Запуск игры"""
        username = self.name_edit.text().strip()
        if not username:
            QMessageBox.critical(self, "Ошибка", "Введите имя игрока")
            return
        
        mc_version = self.current_mc_version
        
        # Используем стандартные рекомендации Java
        recommended_java = get_recommended_java_version(mc_version)
        
        print(f"Для Minecraft {mc_version} требуется Java {recommended_java}")
        
        # Проверяем наличие интернета (для установки новых версий Minecraft)
        has_internet = self.check_internet_connection()
        
        # Получаем список установленных версий Minecraft
        installed_versions = self.get_installed_versions()
        
        # Проверяем установлена ли ванильная версия
        is_version_installed = mc_version in installed_versions
        print(f"Ванильная версия {mc_version} установлена: {is_version_installed}")
        
        # Проверяем, установлена ли нужная Java в именованной папке
        java_installed = self.check_java_installed(recommended_java)
        
        print(f"Java {recommended_java} установлена: {java_installed}")
        print(f"Тип версии: {self.current_version_type}")
        print(f"Интернет: {'есть' if has_internet else 'нет'}")
        
        # Если Java не установлена - это критическая ошибка
        if not java_installed:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Minecraft {mc_version} требует Java {recommended_java},\n"
                f"но она не найдена в папке {JAVA_DIR}.\n\n"
                f"Пожалуйста, перезапустите KuLauncher для установки недостающих компонентов."
            )
            return
        
        # Проверяем, установлена ли версия Minecraft
        if not is_version_installed and not has_internet:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Версия {mc_version} не установлена.\n"
                f"Для установки требуется подключение к интернету.\n\n"
                f"Установленные версии: {', '.join(installed_versions) if installed_versions else 'нет'}"
            )
            return
        
        # Находим точный путь к Java
        java_path = self.get_java_path_for_version(recommended_java)
        if not java_path:
            QMessageBox.critical(
                self, 
                "Ошибка", 
                f"Java {recommended_java} найдена, но не удалось определить путь к исполняемому файлу.\n"
                f"Попробуйте переустановить Java."
            )
            return
        
        print(f"Используем Java {recommended_java}: {java_path}")
        
        # Создаем launcher_profiles.json если его нет
        create_launcher_profiles(self.minecraft_dir)
        
        # Блокируем кнопку запуска
        self.play_button.setEnabled(False)
        
        # Обновляем UI кнопки
        if not hasattr(self.play_button, 'icon') or self.play_button.icon().isNull():
            self.play_button.setText("ЗАГРУЗКА...")
        else:
            self.play_button.setIcon(QIcon())
            self.play_button.setText("ЗАГРУЗКА...")
        
        # Показываем прогресс бар
        self.progress_bar.show()
        self.progress_bar.setValue(0)
        
        # Запускаем поток установки и запуска
        thread = threading.Thread(
            target=self.launch_thread,
            args=(username, self.memory_slider.value(), mc_version, java_path, has_internet, recommended_java),
            daemon=True
        )
        thread.start()
    
    def launch_thread(self, username, memory_mb, mc_version, java_path, has_internet, recommended_java=8):
        """Поток установки и запуска игры"""
        try:
            # Получаем список установленных версий
            installed_versions = minecraft_launcher_lib.utils.get_installed_versions(str(self.minecraft_dir))
            installed_ids = [v["id"] for v in installed_versions]
            
            version_to_install = mc_version
            display_version = mc_version

            
            # Проверяем, установлена ли нужная версия
            version_installed = version_to_install in installed_ids
            
            # Проверяем целостность файлов версии
            version_dir = self.minecraft_dir / "versions" / version_to_install
            version_json = version_dir / f"{version_to_install}.json"
            version_jar = version_dir / f"{version_to_install}.jar"
            
            version_files_valid = version_json.exists() and version_jar.exists()
            
            print(f"Версия {version_to_install} установлена: {version_installed}, файлы целы: {version_files_valid}")
            
            # Установка если нужно
            if (not version_installed or not version_files_valid) and has_internet:
                self.update_status(f"Установка {display_version}...")
                
                # Если версия установлена но файлы повреждены, удаляем её
                if version_dir.exists() and not version_files_valid:
                    self.update_status("Удаление поврежденной установки...")
                    try:
                        shutil.rmtree(version_dir)
                        self.update_status("Поврежденные файлы удалены...")
                    except:
                        pass
                
                self.update_status(f"Установка Minecraft {version_to_install}...")
                
                try:
                    callback = {
                        "setStatus": lambda text: self.update_status(text),
                        "setProgress": lambda progress: self.update_progress(int(progress * 100)),
                        "setMax": lambda max_val: None
                    }
                    
                    minecraft_launcher_lib.install.install_minecraft_version(
                        version_to_install,
                        str(self.minecraft_dir),
                        callback=callback
                    )
                    self.install_success = True
                except Exception as e:
                    error_str = str(e)
                    if "ConnectTimeout" in error_str or "Max retries exceeded" in error_str:
                        error_str = "Ошибка сети (тайм-аут). Серверы Minecraft недоступны. Попробуйте включить VPN."
                    self.install_success = False
                    self.show_error(f"Не удалось установить {display_version}:\n{error_str}")
                    return
                
                # Повторная проверка файлов после установки
                version_dir = self.minecraft_dir / "versions" / version_to_install
                version_json = version_dir / f"{version_to_install}.json"
                version_jar = version_dir / f"{version_to_install}.jar"
                
                if not version_json.exists() or not version_jar.exists():
                    self.show_error(f"Установка завершена, но файлы не найдены: {version_to_install}")
                    return
                
            elif not version_installed and not has_internet:
                self.show_error(f"Версия {display_version} не установлена.\nДля установки требуется интернет.\n\nДоступные установленные версии: {', '.join(installed_ids)}")
                return
            else:
                self.update_status(f"Версия {display_version} уже установлена")


            
            # Докачиваем библиотеки для итоговой версии
            if has_internet and not version_files_valid:
                self.update_status(f"Проверка библиотек для {version_to_install}...")
                
                install_progress = {"max": 100, "current": 0}
                
                def set_max(max_val):
                    install_progress["max"] = max_val if max_val > 0 else 100
                
                def set_progress(val):
                    install_progress["current"] = val
                    if isinstance(val, float) and val <= 1.0:
                        percent = int(val * 100)
                    else:
                        percent = min(100, int((install_progress["current"] / install_progress["max"]) * 100))
                    self.update_progress(percent)

                install_callback = {
                    "setStatus": lambda text: self.update_status(text),
                    "setProgress": set_progress,
                    "setMax": set_max
                }
                
                try:
                    minecraft_launcher_lib.install.install_minecraft_version(
                        version_to_install,
                        str(self.minecraft_dir),
                        callback=install_callback
                    )
                except Exception as e:
                    self.show_error(f"Ошибка загрузки библиотек: {str(e)}")
                    return

            # Запускаем игру
            self.update_status("Запуск игры...")
            process = self.run_game(username, memory_mb, version_to_install, java_path)


            
            if not process:
                if self.mc_log_path and self.mc_log_path.exists():
                    log_tail = self._read_log_tail(self.mc_log_path, 50)
                    error_msg = f"Не удалось запустить игру\n\nПоследние строки лога:\n{log_tail}"
                else:
                    error_msg = "Не удалось запустить игру"
                self.show_error(error_msg)
            else:
                self.mc_process = process
                self.update_status("Игра запущена!")
                QMetaObject.invokeMethod(self, "hide_launcher_slot", Qt.QueuedConnection)
                threading.Thread(
                    target=self.wait_for_game_close,
                    args=(process,),
                    daemon=True
                ).start()
                
        except Exception as e:
            self.show_error(f"Исключение: {str(e)}")
            import traceback
            traceback.print_exc()
        finally:
            self.restore_ui()
    
    def run_game(self, username, memory_mb, version_name, java_path):
        """Запускает игру с указанными параметрами"""
        try:
            # Проверяем наличие JSON файла версии
            version_json = self.minecraft_dir / "versions" / version_name / f"{version_name}.json"
            if not version_json.exists():
                self.show_error(f"Файл версии {version_name}.json не найден")
                return None

            # Проверяем JSON на валидность
            try:
                with open(version_json, 'r', encoding='utf-8') as f:
                    version_data = json.load(f)
                    
                # Проверяем наличие обязательных полей
                if "mainClass" not in version_data:
                    self.show_error(f"Файл версии поврежден: отсутствует mainClass в {version_name}.json")
                    return None
                    

                        
            except json.JSONDecodeError as e:
                self.show_error(f"Файл версии поврежден (некорректный JSON): {str(e)}")
                return None


            
            print(f"Запуск версии {version_name} с Java {java_path}")
            
            # Формируем опции запуска
            options = {
                "username": username,
                "uuid": generate_offline_uuid(username),
                "token": "0",
                "launcherName": "KuLauncher",
                "launcherVersion": "1.0",
                "gameDirectory": str(self.minecraft_dir),
                "executablePath": java_path,
                "jvmArguments": [
                    f"-Xmx{memory_mb}M",
                    f"-Xms{max(512, memory_mb // 2)}M",
                    "-Djava.awt.headless=false",
                    "-Dminecraft.launcher.brand=KuLauncher",
                    "-Dminecraft.launcher.version=1.0"
                ]
            }
            

            
            # Получаем команду запуска через библиотеку
            try:
                command = minecraft_launcher_lib.command.get_minecraft_command(
                    version_name,
                    str(self.minecraft_dir),
                    options
                )

                print(f"Команда запуска: {' '.join(command[:5])}...")
                
                # Проверяем, что Java в команде - правильная
                if command[0] != java_path:
                    print(f"Предупреждение: библиотека предложила другую Java: {command[0]}")
                    # Заменяем Java на правильную
                    command[0] = java_path
                
                # Запускаем процесс
                creation_flags = subprocess.CREATE_NO_WINDOW | subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP if os.name == 'nt' else 0
                log_file = self._open_mc_log_file()
                try:
                    process = subprocess.Popen(
                        command,
                        cwd=str(self.minecraft_dir),
                        creationflags=creation_flags,
                        stdout=log_file,
                        stderr=subprocess.STDOUT,
                        text=True,
                        encoding="utf-8",
                        errors="replace"
                    )
                except Exception as e:
                    self._close_mc_log_file()
                    raise e

                # Проверяем, что процесс не завершился сразу
                time.sleep(3)
                
                if process.poll() is not None:
                    if self.mc_log_handle:
                        self.mc_log_handle.flush()
                    log_tail = self._read_log_tail(self.mc_log_path, 30)
                    
                    # Анализируем ошибку
                    error_msg = (
                        f"Minecraft завершился с кодом {process.returncode}.\n\n"
                        f"Последние строки лога:\n{log_tail}"
                    )
                    
                    if "Unsupported class file major version" in log_tail:
                        error_msg = "Ошибка: несовместимая версия Java.\nПопробуйте другую версию Java."
                    
                    self.show_error(error_msg)
                    self._close_mc_log_file()
                    return None

                return process
                
            except Exception as e:
                self.show_error(f"Ошибка формирования команды запуска: {str(e)}")
                import traceback
                traceback.print_exc()
                return None
                
        except Exception as e:
            self.show_error(f"Ошибка запуска: {str(e)}")
            import traceback
            traceback.print_exc()
            return None

    def _open_mc_log_file(self):
        """Открывает лог-файл запуска Minecraft для stdout/stderr."""
        logs_dir = self.minecraft_dir / "logs"
        logs_dir.mkdir(parents=True, exist_ok=True)
        self.mc_log_path = logs_dir / "launcher_game.log"
        self.mc_log_handle = open(self.mc_log_path, "w", encoding="utf-8", errors="replace")
        return self.mc_log_handle

    def _close_mc_log_file(self):
        """Безопасно закрывает лог-файл процесса игры."""
        if self.mc_log_handle:
            try:
                self.mc_log_handle.close()
            except Exception:
                pass
            finally:
                self.mc_log_handle = None

    def _read_log_tail(self, log_path, max_lines=30):
        """Возвращает последние строки лога для отображения в ошибке."""
        if not log_path or not log_path.exists():
            return "Лог не найден."
        try:
            with open(log_path, "r", encoding="utf-8", errors="replace") as f:
                lines = f.readlines()
            tail = "".join(lines[-max_lines:]).strip()
            return tail if tail else "Лог пуст."
        except Exception as e:
            return f"Не удалось прочитать лог: {e}"

    def wait_for_game_close(self, process):
        """Ожидает завершения процесса Minecraft и возвращает лаунчер."""
        try:
            process.wait()
        except Exception as e:
            print(f"Ошибка ожидания процесса Minecraft: {e}")
        finally:
            self.mc_process = None
            self._close_mc_log_file()
            QMetaObject.invokeMethod(self, "show_launcher_slot", Qt.QueuedConnection)
    
    def show_error(self, text):
        """Показывает сообщение об ошибке"""
        try:
            import sip
            if sip.isdeleted(self):
                print(f"Попытка показать ошибку после закрытия окна: {text}")
                return
        except:
            pass
            
        try:
            QMetaObject.invokeMethod(self, "show_message_box",
                                     Q_ARG(str, "Ошибка"),
                                     Q_ARG(str, text),
                                     Q_ARG(int, QMessageBox.Critical))
        except RuntimeError as e:
            if "has been deleted" in str(e):
                print(f"Попытка показать ошибку после закрытия окна: {text}")
            else:
                raise e

    def get_asset_index(self, version_name, version_data):
        """Получает правильный asset index для версии"""
        if "assetIndex" in version_data:
            if isinstance(version_data["assetIndex"], dict) and "id" in version_data["assetIndex"]:
                return version_data["assetIndex"]["id"]
            elif isinstance(version_data["assetIndex"], str):
                return version_data["assetIndex"]
        
        # Для старых версий
        for prefix in ["1.5", "1.6", "1.7", "1.8", "1.9", "1.10", "1.11", "1.12", 
                       "1.13", "1.14", "1.15", "1.16", "1.17", "1.18", "1.19", "1.20", "1.21"]:
            if version_name.startswith(prefix):
                return prefix
        
        return version_name
    
    def on_install_finished(self, success, message):
        """Обработчик завершения установки"""
        self.install_success = success
        if not success:
            self.show_error(message)
    
    def restore_ui(self):
        """Восстанавливает UI после запуска"""
        try:
            import sip
            if sip.isdeleted(self):
                return
        except:
            pass
            
        try:
            QMetaObject.invokeMethod(self, "restore_ui_slot")
        except RuntimeError:
            pass
    
    @Slot()
    def restore_ui_slot(self):
        """Слот для восстановления UI"""
        self.play_button.setEnabled(True)
        self.play_button.setText("ИГРАТЬ")
        self.play_button.setIcon(QIcon())
        self.progress_bar.hide()
        self.progress_bar.setValue(0)
    
    def update_status(self, text):
        """Обновляет статус в UI с анимацией"""
        try:
            import sip
            if sip.isdeleted(self):
                return
        except:
            pass
            
        try:
            QMetaObject.invokeMethod(self, "set_status",
                                     Q_ARG(str, text))
        except RuntimeError:
            pass
    
    def update_progress(self, value):
        """Обновляет прогресс бар с анимацией"""
        try:
            import sip
            if sip.isdeleted(self):
                return
        except:
            pass
            
        try:
            QMetaObject.invokeMethod(self, "animate_progress",
                                     Q_ARG(int, int(value)))
        except RuntimeError:
            pass
    
    @Slot(str, str, int)
    def show_message_box(self, title, text, icon):
        """Слот для показа сообщения"""
        msg = QMessageBox(self)
        msg.setIcon(icon)
        msg.setWindowTitle(title)
        msg.setText(text)
        msg.exec()
    
    @Slot()
    def delayed_close(self):
        """Закрывает лаунчер с задержкой"""
        QTimer.singleShot(2000, self.close)

    @Slot()
    def hide_launcher_slot(self):
        """Скрывает лаунчер после успешного запуска игры."""
        self.hide()

    @Slot()
    def show_launcher_slot(self):
        """Показывает лаунчер после закрытия игры."""
        self.showNormal()
        self.raise_()
        self.activateWindow()
        self.set_status("Minecraft закрыт. Лаунчер снова активен.")
    
    def get_installed_versions(self):
        """Возвращает список установленных версий"""
        try:
            versions = minecraft_launcher_lib.utils.get_installed_versions(str(self.minecraft_dir))
            return [v["id"] for v in versions]
        except Exception as e:
            print(f"Ошибка получения списка версий: {e}")
            return []
    
    def is_version_installed(self, version_name):
        """Проверяет установлена ли указанная версия"""
        installed = self.get_installed_versions()
        return version_name in installed
    
    def verify_version_files(self, version_name):
        """Проверяет целостность файлов версии"""
        version_dir = self.minecraft_dir / "versions" / version_name
        json_file = version_dir / f"{version_name}.json"
        jar_file = version_dir / f"{version_name}.jar"
        
        if not json_file.exists() or not jar_file.exists():
            return False
            
        # Проверяем JSON на валидность
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                version_data = json.load(f)
            return "mainClass" in version_data
        except:
            return False
