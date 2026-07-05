from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from pathlib import Path
import json
import os
from core.config import DEFAULT_MC_VERSION, JAVA_DIR
from core.utils import create_launcher_profiles, check_java_version
from dialogs.java_install_dialog import JavaInstallDialog

class MainWindowHandlers:
    """Класс для обработчиков событий главного окна"""

    def show_settings(self):
        self.settings_page.dir_edit.setText(str(self.minecraft_dir))
        self.settings_page.memory_slider.setValue(self.memory_slider.value())
        self.animate_page_transition(self._main_stack_wrap, self._settings_stack_wrap)
    
    def show_main(self):
        self.animate_page_transition(self._settings_stack_wrap, self._main_stack_wrap)
    
    def show_mods_panel(self):
        from gui.mods_panel import ModsPanel
        self.mods_dialog = ModsPanel(self, self.minecraft_dir)
        screen = QApplication.primaryScreen().geometry()
        self.mods_dialog.move((screen.width() - self.mods_dialog.width()) // 2, (screen.height() - self.mods_dialog.height()) // 2)
        self.mods_dialog.show()
    
    def check_java_after_start(self):
        """Проверяет наличие Java после запуска"""
        # Проверяем наличие всех нужных версий Java в папке KuLauncher_java
        missing_versions = self.check_all_java_versions()
        
        if missing_versions:
            self.missing_java_versions = missing_versions
            # Проверяем в настройках, был ли уже показан диалог
            settings_path = Path.home() / ".ku_launcher_settings.json"
            java_dialog_shown = False
            
            if settings_path.exists():
                try:
                    with open(settings_path, 'r') as f:
                        data = json.load(f)
                        java_dialog_shown = data.get('java_install_dialog_shown', False)
                except:
                    pass
            
            # Показываем диалог только если он еще не был показан
            if not java_dialog_shown and not self.java_install_dialog_shown:
                reply = QMessageBox.question(
                    self,
                    "Отсутствуют версии Java",
                    f"Для работы с разными версиями Minecraft рекомендуются следующие версии Java: {', '.join(map(str, missing_versions))}.\n\n"
                    f"Хотите установить их сейчас в папку {JAVA_DIR}?\n\n"
                    f"*Это сообщение показывается только один раз*",
                    QMessageBox.Yes | QMessageBox.No
                )
                
                if reply == QMessageBox.Yes:
                    dialog = JavaInstallDialog(self, missing_versions)
                    dialog.exec()
                    # После установки обновляем список
                    self.missing_java_versions = self.check_all_java_versions()
                
                # Сохраняем флаг в настройки, что диалог был показан
                try:
                    with open(settings_path, 'r') as f:
                        data = json.load(f)
                except:
                    data = {}
                
                data['java_install_dialog_shown'] = True
                
                try:
                    with open(settings_path, 'w') as f:
                        json.dump(data, f, indent=2)
                except Exception as e:
                    print(f"Ошибка сохранения флага диалога Java: {e}")
                
                self.java_install_dialog_shown = True
        else:
            self.missing_java_versions = []
    
    def check_all_java_versions(self):
        """Проверяет наличие всех нужных версий Java в папке KuLauncher_java и возвращает список отсутствующих"""
        required_versions = [8, 17, 21]
        missing_versions = []
        
        for version in required_versions:
            # Ищем в папке KuLauncher_java
            java_path = self.find_java_by_version_in_java_dir(version)
            if not java_path:
                missing_versions.append(version)
        
        return missing_versions
    
    def find_java_by_version_in_java_dir(self, version):
        """Ищет Java указанной версии в папке KuLauncher_java"""
        if not JAVA_DIR.exists():
            return None
        
        # Рекурсивный поиск во всех подпапках
        for root, dirs, files in os.walk(JAVA_DIR):
            for file in files:
                if file.lower() in ["java.exe", "java"]:
                    java_path = Path(root) / file
                    try:
                        is_valid, msg = check_java_version(str(java_path), version)
                        if is_valid:
                            return str(java_path)
                    except:
                        continue
        
        return None
    
    def browse_directory(self):
        directory = QFileDialog.getExistingDirectory(
            self, "Выберите папку для Minecraft", str(Path.home())
        )
        if directory:
            self.settings_page.dir_edit.setText(directory)
            self.minecraft_dir = Path(directory)
            create_launcher_profiles(self.minecraft_dir)
    
    def load_settings(self):
        settings_path = Path.home() / ".ku_launcher_settings.json"
        if settings_path.exists():
            try:
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                self.minecraft_dir = Path(data.get('minecraft_dir', str(self.minecraft_dir)))
                self.name_edit.setText(data.get('username', "Player"))
                # Проверяем наличие memory_slider перед использованием
                if hasattr(self, 'memory_slider') and self.memory_slider is not None:
                    self.memory_slider.setValue(data.get('memory', 4096))
                    if hasattr(self, 'memory_label') and self.memory_label is not None:
                        self.memory_label.setText(f"{self.memory_slider.value()} MB")
                self.current_mc_version = data.get('mc_version', DEFAULT_MC_VERSION)
                self.version_label.setText(self.current_mc_version)
                
                # Определяем тип версии
                version_type = data.get('version_type', 'release')
                self.current_version_type = version_type
                
                self.version_type_label.setText(version_type)
                self.version_type_label.setStyleSheet("color: #888; font-size: 11px;")
                
                # Загружаем флаг показа диалога Java
                self.java_install_dialog_shown = data.get('java_install_dialog_shown', False)
                
            except Exception as e:
                print(f"Ошибка загрузки настроек: {e}")
                
    def save_settings(self):
        data = {
            'minecraft_dir': str(self.minecraft_dir),
            'username': self.name_edit.text(),
            'memory': self.memory_slider.value() if hasattr(self, 'memory_slider') else 4096,
            'mc_version': self.current_mc_version,
            'version_type': self.current_version_type,
            'java_install_dialog_shown': self.java_install_dialog_shown,
        }
        settings_path = Path.home() / ".ku_launcher_settings.json"
        try:
            with open(settings_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            print(f"Ошибка сохранения настроек: {e}")