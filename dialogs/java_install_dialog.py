from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import minecraft_launcher_lib
import threading
import time
import os
import json
import shutil
import urllib.request
import zipfile
import tarfile
from pathlib import Path
from core.config import JAVA_RUNTIME_NAMES, JAVA_DIR
from core.utils import get_java_major_version
from gui.animations import UIAnimations


class JavaInstallDialog(QDialog):
    download_success_signal = Signal(str, int)
    download_error_signal = Signal(str, int)
    progress_update_signal = Signal(int)
    status_update_signal = Signal(str)
    speed_update_signal = Signal(str)
    version_complete_signal = Signal(int, bool)
    all_complete_signal = Signal()
    
    def __init__(self, parent, required_versions=None, mandatory=True):
        super().__init__(parent)
        self.parent = parent
        self.required_versions = required_versions or [8, 17, 21]
        self.mandatory = mandatory
        self.download_threads = {}
        self.is_downloading = False
        self.completed_versions = set()
        self.failed_versions = set()
        self.current_version_index = 0
        self.total_versions = len(self.required_versions)
        self.can_close = False
        self.current_speed = "0 KB/s"
        self.init_ui()
        
        self.download_success_signal.connect(self.on_download_success)
        self.download_error_signal.connect(self.on_download_error)
        self.progress_update_signal.connect(self.on_progress_update)
        self.status_update_signal.connect(self.on_status_update)
        self.speed_update_signal.connect(self.on_speed_update)
        self.version_complete_signal.connect(self.on_version_complete)
        self.all_complete_signal.connect(self.on_all_complete)
        
        QTimer.singleShot(500, self.start_all_downloads)
        
        # Анимация появления
        UIAnimations.entrance_dialog(self, duration=400)
        
    def init_ui(self):
        self.setWindowTitle("Установка Java")
        self.setFixedSize(500, 200)
        self.setModal(True)
        
        self.setWindowFlags(Qt.Dialog | Qt.FramelessWindowHint)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                border: 2px solid #444;
                border-radius: 8px;
            }
            QLabel {
                color: #ffffff;
                font-size: 13px;
                background: transparent;
            }
            QProgressBar {
                border: 2px solid #444;
                text-align: center;
                height: 25px;
                background-color: #2d2d2d;
                font-size: 13px;
                color: white;
            }
            QProgressBar::chunk {
                background-color: #666;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Установка Java")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; margin-bottom: 10px;")
        layout.addWidget(title_label)
        
        layout.addSpacing(10)
        
        self.status_label = QLabel("Подготовка к установке...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("font-size: 14px; color: #888; min-height: 30px;")
        layout.addWidget(self.status_label)
        
        self.speed_label = QLabel("Скорость: 0 KB/s")
        self.speed_label.setAlignment(Qt.AlignCenter)
        self.speed_label.setStyleSheet("font-size: 11px; color: #666; min-height: 20px;")
        layout.addWidget(self.speed_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setFormat("%p%")
        self.progress_bar.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
    
    def check_installed_java(self, version):
        version_folders = {
            8: JAVA_DIR / "Java8",
            17: JAVA_DIR / "Java17",
            21: JAVA_DIR / "Java21"
        }
        
        if version not in version_folders:
            return False
        
        java_folder = version_folders[version]
        
        if not java_folder.exists():
            return False
        
        if os.name == 'nt':
            java_exe = java_folder / "bin" / "java.exe"
        else:
            java_exe = java_folder / "bin" / "java"
        
        if java_exe.exists():
            try:
                ver = get_java_major_version(str(java_exe))
                if ver == version or (version == 17 and ver == 21):
                    print(f"Java {version} уже установлена в {java_exe}")
                    return True
            except:
                pass
        
        return False
    
    def start_all_downloads(self):
        if self.is_downloading:
            return
        
        self.is_downloading = True
        
        for version in self.required_versions[:]:
            if self.check_installed_java(version):
                print(f"Java {version} уже установлена, пропускаем")
                self.completed_versions.add(version)
                self.required_versions.remove(version)
                self.total_versions = len(self.required_versions)
        
        if not self.required_versions:
            self.status_label.setText("Установка завершена")
            self.all_complete_signal.emit()
            return
        
        self.current_version_index = 0
        self.start_next_version()
    
    def start_next_version(self):
        if self.current_version_index < len(self.required_versions):
            version = self.required_versions[self.current_version_index]
            self.start_version_download(version)
    
    def start_version_download(self, version):
        self.status_label.setText(f"Java {version} - установка...")
        self.progress_bar.setValue(0)
        self.speed_label.setText("Скорость: 0 KB/s")
        
        thread = threading.Thread(target=self.download_java_version, args=(version,), daemon=True)
        thread.start()
        self.download_threads[version] = thread
    
    def download_java_version(self, version):
        try:
            runtime_names = JAVA_RUNTIME_NAMES.get(version, ["java-runtime-gamma"])
            
            if version == 21:
                runtime_names = [
                    "java-runtime-delta",
                    "java-runtime-gamma", 
                    "java-runtime",
                    "jre-delta",
                    "jre-gamma",
                    "java-runtime-gamma.1",
                    "java-runtime-gamma.2",
                    "java-runtime-delta.1",
                    "java-runtime-delta.2"
                ]
                print(f"Для Java 21 будем пробовать варианты: {runtime_names}")
            
            version_folders = {
                8: JAVA_DIR / "Java8",
                17: JAVA_DIR / "Java17",
                21: JAVA_DIR / "Java21"
            }
            
            target_folder = version_folders.get(version)
            if not target_folder:
                raise Exception(f"Неизвестная версия Java: {version}")
            
            target_folder.mkdir(parents=True, exist_ok=True)
            
            temp_folder = JAVA_DIR / f"temp_java_{version}"
            if temp_folder.exists():
                shutil.rmtree(temp_folder)
            temp_folder.mkdir(parents=True, exist_ok=True)
            
            download_start_time = time.time()
            last_downloaded = [0]
            
            def set_status(text):
                self.status_update_signal.emit(f"Java {version} - {text}")
            
            def set_progress(progress):
                self.progress_update_signal.emit(int(progress * 100))
            
            def update_speed(current_bytes):
                elapsed = time.time() - download_start_time
                if elapsed > 0:
                    speed = current_bytes / elapsed
                    if speed < 1024:
                        speed_str = f"{speed:.1f} B/s"
                    elif speed < 1024 * 1024:
                        speed_str = f"{speed/1024:.1f} KB/s"
                    else:
                        speed_str = f"{speed/(1024*1024):.1f} MB/s"
                    self.speed_update_signal.emit(speed_str)
            
            def progress_callback(current, total):
                if total > 0:
                    percent = current / total
                    set_progress(percent)
                    update_speed(current)
            
            callback = {
                "setStatus": set_status,
                "setProgress": set_progress,
                "setMax": lambda max_val: None
            }
            
            success = False
            used_runtime = None
            
            for runtime_name in runtime_names:
                try:
                    self.status_update_signal.emit(f"Java {version} - скачивание...")
                    
                    minecraft_launcher_lib.runtime.install_jvm_runtime(
                        runtime_name,
                        str(temp_folder),
                        callback=callback
                    )
                    
                    used_runtime = runtime_name
                    success = True
                    break
                except Exception as e:
                    print(f"Ошибка с runtime {runtime_name}: {e}")
                    continue
            
            if not success:
                if version == 8:
                    self.status_update_signal.emit("Java 8 - альтернативный метод...")
                    success = self.download_java_8_alternative(temp_folder, callback, progress_callback)
                    used_runtime = "alternative"
                elif version == 17:
                    self.status_update_signal.emit("Java 17 - альтернативный метод...")
                    success = self.download_java_17_alternative(temp_folder, callback, progress_callback)
                    used_runtime = "alternative_17"
                elif version == 21:
                    self.status_update_signal.emit("Java 21 - альтернативный метод...")
                    success = self.download_java_21_alternative(temp_folder, callback, progress_callback)
                    used_runtime = "alternative_21"
            
            if not success:
                raise Exception(f"Не удалось скачать Java {version} ни одним из методов")
            
            time.sleep(2)
            
            self.status_update_signal.emit(f"Java {version} - поиск файлов...")
            
            java_exe_name = "java.exe" if os.name == 'nt' else "java"
            found_java = None
            java_root_folder = None
            
            for root, dirs, files in os.walk(temp_folder):
                if java_exe_name in files and 'bin' in root:
                    found_java = Path(root) / java_exe_name
                    java_root_folder = Path(root).parent
                    break
            
            if not found_java:
                for root, dirs, files in os.walk(temp_folder):
                    if java_exe_name in files:
                        found_java = Path(root) / java_exe_name
                        java_root_folder = Path(root)
                        break
            
            if found_java and found_java.exists():
                ver = get_java_major_version(str(found_java))
                
                version_match = (ver == version) or (version == 17 and ver == 21)
                
                if version_match:
                    print(f"Java {version} успешно скачана во временную папку: {found_java}")
                    
                    self.status_update_signal.emit(f"Java {version} - копирование...")
                    
                    if target_folder.exists():
                        for item in target_folder.iterdir():
                            try:
                                if item.is_dir():
                                    shutil.rmtree(item)
                                else:
                                    item.unlink()
                            except:
                                pass
                    
                    source_folder = java_root_folder if java_root_folder else temp_folder
                    
                    for item in source_folder.iterdir():
                        try:
                            dest = target_folder / item.name
                            if item.is_dir():
                                shutil.copytree(item, dest, dirs_exist_ok=True)
                            else:
                                shutil.copy2(item, dest)
                        except Exception as e:
                            print(f"Ошибка копирования {item}: {e}")
                    
                    time.sleep(1)
                    
                    final_java = target_folder / "bin" / java_exe_name
                    if not final_java.exists():
                        final_java = target_folder / java_exe_name
                    
                    if final_java.exists():
                        ver_after = get_java_major_version(str(final_java))
                        
                        if ver_after == version or (version == 17 and ver_after == 21):
                            print(f"Java {version} успешно установлена в {final_java}")
                            self.download_success_signal.emit(str(final_java), version)
                        else:
                            self.download_error_signal.emit(f"Версия Java изменилась после копирования: {ver_after}", version)
                    else:
                        self.download_error_signal.emit("Ошибка копирования файлов", version)
                    
                    try:
                        shutil.rmtree(temp_folder)
                    except:
                        pass
                else:
                    self.download_error_signal.emit(f"Скачана Java версии {ver}, а требуется {version}", version)
            else:
                self.download_error_signal.emit("Исполняемый файл Java не найден после скачивания", version)
                
        except Exception as e:
            print(f"Ошибка при установке Java {version}: {e}")
            import traceback
            traceback.print_exc()
            self.download_error_signal.emit(str(e), version)
    
    def download_java_8_alternative(self, temp_folder, callback, progress_callback):
        try:
            if os.name == 'nt':
                url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u442-b06/OpenJDK8U-jre_x64_windows_hotspot_8u442b06.zip"
            else:
                url = "https://github.com/adoptium/temurin8-binaries/releases/download/jdk8u442-b06/OpenJDK8U-jre_x64_linux_hotspot_8u442b06.tar.gz"
            
            callback["setStatus"](f"Скачивание Java 8...")
            
            zip_path = temp_folder / "java8.zip" if os.name == 'nt' else temp_folder / "java8.tar.gz"
            
            def download_with_progress(url, filepath):
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        downloaded = block_num * block_size
                        percent = min(100, int(downloaded * 100 / total_size))
                        callback["setProgress"](percent / 100)
                        progress_callback(downloaded, total_size)
                
                urllib.request.urlretrieve(url, str(filepath), reporthook=report_progress)
            
            download_with_progress(url, zip_path)
            
            callback["setStatus"](f"Распаковка Java 8...")
            
            def is_safe_path(base_path, path):
                try:
                    resolved = (Path(base_path) / path).resolve()
                    return str(resolved).startswith(str(Path(base_path).resolve()))
                except Exception:
                    return False
            
            if os.name == 'nt':
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        if is_safe_path(temp_folder, member.filename):
                            zip_ref.extract(member, temp_folder)
            else:
                with tarfile.open(zip_path, 'r:gz') as tar_ref:
                    for member in tar_ref.getmembers():
                        if is_safe_path(temp_folder, member.name):
                            tar_ref.extract(member, temp_folder)
            
            zip_path.unlink()
            return True
            
        except Exception as e:
            print(f"Ошибка при альтернативном скачивании Java 8: {e}")
            return False
    
    def download_java_17_alternative(self, temp_folder, callback, progress_callback):
        try:
            if os.name == 'nt':
                url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk17-2024-05-02/OpenJDK17U-jre_x64_windows_hotspot_2024-05-02.zip"
            else:
                url = "https://github.com/adoptium/temurin17-binaries/releases/download/jdk17-2024-05-02/OpenJDK17U-jre_x64_linux_hotspot_2024-05-02.tar.gz"
            
            callback["setStatus"](f"Скачивание Java 17...")
            
            zip_path = temp_folder / "java17.zip" if os.name == 'nt' else temp_folder / "java17.tar.gz"
            
            def download_with_progress(url, filepath):
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        downloaded = block_num * block_size
                        percent = min(100, int(downloaded * 100 / total_size))
                        callback["setProgress"](percent / 100)
                        progress_callback(downloaded, total_size)
                
                urllib.request.urlretrieve(url, str(filepath), reporthook=report_progress)
            
            download_with_progress(url, zip_path)
            
            callback["setStatus"](f"Распаковка Java 17...")
            
            def is_safe_path(base_path, path):
                try:
                    resolved = (Path(base_path) / path).resolve()
                    return str(resolved).startswith(str(Path(base_path).resolve()))
                except Exception:
                    return False
            
            if os.name == 'nt':
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        if is_safe_path(temp_folder, member.filename):
                            zip_ref.extract(member, temp_folder)
            else:
                with tarfile.open(zip_path, 'r:gz') as tar_ref:
                    for member in tar_ref.getmembers():
                        if is_safe_path(temp_folder, member.name):
                            tar_ref.extract(member, temp_folder)
            
            zip_path.unlink()
            return True
            
        except Exception as e:
            print(f"Ошибка при альтернативном скачивании Java 17: {e}")
            return False
    
    def download_java_21_alternative(self, temp_folder, callback, progress_callback):
        try:
            if os.name == 'nt':
                url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk21-2024-05-02/OpenJDK21U-jre_x64_windows_hotspot_2024-05-02.zip"
            else:
                url = "https://github.com/adoptium/temurin21-binaries/releases/download/jdk21-2024-05-02/OpenJDK21U-jre_x64_linux_hotspot_2024-05-02.tar.gz"
            
            callback["setStatus"](f"Скачивание Java 21...")
            
            zip_path = temp_folder / "java21.zip" if os.name == 'nt' else temp_folder / "java21.tar.gz"
            
            def download_with_progress(url, filepath):
                def report_progress(block_num, block_size, total_size):
                    if total_size > 0:
                        downloaded = block_num * block_size
                        percent = min(100, int(downloaded * 100 / total_size))
                        callback["setProgress"](percent / 100)
                        progress_callback(downloaded, total_size)
                
                urllib.request.urlretrieve(url, str(filepath), reporthook=report_progress)
            
            download_with_progress(url, zip_path)
            
            callback["setStatus"](f"Распаковка Java 21...")
            
            def is_safe_path(base_path, path):
                try:
                    resolved = (Path(base_path) / path).resolve()
                    return str(resolved).startswith(str(Path(base_path).resolve()))
                except Exception:
                    return False
            
            if os.name == 'nt':
                with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                    for member in zip_ref.infolist():
                        if is_safe_path(temp_folder, member.filename):
                            zip_ref.extract(member, temp_folder)
            else:
                with tarfile.open(zip_path, 'r:gz') as tar_ref:
                    for member in tar_ref.getmembers():
                        if is_safe_path(temp_folder, member.name):
                            tar_ref.extract(member, temp_folder)
            
            zip_path.unlink()
            return True
            
        except Exception as e:
            print(f"Ошибка при альтернативном скачивании Java 21: {e}")
            return False
    
    @Slot(int)
    def on_progress_update(self, value):
        if not hasattr(self, "_progress_anim"):
            self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
            self._progress_anim.setDuration(300)
            self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(int(value))
        self._progress_anim.start()

    @Slot(str)
    def on_status_update(self, text):
        if self.status_label.text() == text:
            return
            
        effect = QGraphicsOpacityEffect(self.status_label)
        self.status_label.setGraphicsEffect(effect)
        
        anim_out = QPropertyAnimation(effect, b"opacity")
        anim_out.setDuration(150)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.0)
        
        anim_in = QPropertyAnimation(effect, b"opacity")
        anim_in.setDuration(150)
        anim_in.setStartValue(0.0)
        anim_in.setEndValue(1.0)
        
        def on_out_finished():
            self.status_label.setText(text)
            anim_in.start()
            self._status_anim_in = anim_in
            
        anim_out.finished.connect(on_out_finished)
        anim_out.start()
        self._status_anim_out = anim_out
    
    @Slot(str)
    def on_speed_update(self, speed_text):
        self.speed_label.setText(f"Скорость: {speed_text}")
    
    @Slot(str, int)
    def on_download_success(self, java_path, version):
        self.completed_versions.add(version)
        self.version_complete_signal.emit(version, True)
        print(f"Java {version} успешно установлена в {java_path}")
    
    @Slot(str, int)
    def on_download_error(self, error_msg, version):
        self.failed_versions.add(version)
        self.version_complete_signal.emit(version, False)
        print(f"Ошибка установки Java {version}: {error_msg}")
    
    @Slot(int, bool)
    def on_version_complete(self, version, success):
        self.current_version_index += 1
        
        if self.current_version_index < len(self.required_versions):
            QTimer.singleShot(1000, self.start_next_version)
        else:
            self.all_complete_signal.emit()
    
    @Slot()
    def on_all_complete(self):
        if self.failed_versions:
            failed_text = ", ".join(map(str, self.failed_versions))
            self.status_label.setText(f"Ошибка: Java {failed_text}")
            self.status_label.setStyleSheet("color: #FF4444; font-size: 14px;")
            
            msg = QMessageBox(self)
            msg.setIcon(QMessageBox.Critical)
            msg.setWindowTitle("Ошибка установки")
            msg.setText(f"Не удалось установить Java {failed_text}")
            msg.setInformativeText(
                "Пожалуйста, проверьте подключение к интернету и перезапустите лаунчер.\n\n"
                f"Путь для Java: {JAVA_DIR}"
            )
            msg.exec()
        else:
            self.status_label.setText("Установка завершена")
            self.status_label.setStyleSheet("color: #88FF88; font-size: 14px;")
        
        self.progress_bar.setValue(100)
        self.is_downloading = False
        self.can_close = True
        
        QTimer.singleShot(2000, self.accept)
    
    def closeEvent(self, event):
        if self.can_close:
            event.accept()
        else:
            event.ignore()