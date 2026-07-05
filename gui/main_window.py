from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from pathlib import Path
import json
import os

from core.config import DEFAULT_MC_VERSION, DEFAULT_MINECRAFT_DIR, get_asset_path
from core.utils import create_launcher_profiles
from gui.widgets import BackgroundWidget
from gui.main_window_ui import MainWindowUI
from gui.main_window_handlers import MainWindowHandlers
from gui.main_window_game import MainWindowGame
from gui.settings_page import SettingsPage
from dialogs.java_install_dialog import JavaInstallDialog

class KuLauncher(QMainWindow, MainWindowUI, MainWindowHandlers, MainWindowGame):
    def __init__(self, missing_versions=None):
        super().__init__()
        MainWindowGame.__init__(self)
        
        # Текущая версия Minecraft
        self.current_mc_version = DEFAULT_MC_VERSION
        
        # Тип текущей версии (release, snapshot)
        self.current_version_type = "release"
        
        # Отсутствующие версии Java
        self.missing_java_versions = missing_versions or []
        
        # Флаг для отслеживания, был ли уже показан диалог установки Java
        self.java_install_dialog_shown = False
        
        # Путь к Java (будет определен при запуске)
        self.java_path = None
        
        # Устанавливаем флаги окна для закругленных углов
        self.setWindowFlags(Qt.FramelessWindowHint)
        self.setAttribute(Qt.WA_TranslucentBackground)
        
        self.drag_pos = None
        self.minecraft_dir = DEFAULT_MINECRAFT_DIR
        
        # Создаем контейнер с закругленными углами
        self.central_container = QWidget()
        self.central_container.setObjectName("centralContainer")
        self.central_container.setStyleSheet("""
            #centralContainer {
                background: transparent;
                border-radius: 20px;
            }
        """)
        
        # Layout для контейнера
        container_layout = QVBoxLayout(self.central_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        
        self.layer_container = QWidget()
        self.layer_container.setAttribute(Qt.WA_TranslucentBackground)
        self.layer_container.setStyleSheet("background: transparent;")
        container_layout.addWidget(self.layer_container)
        
        self.stacked_widget = QStackedWidget(self.layer_container)
        self.stacked_widget.setStyleSheet("""
            QStackedWidget {
                border-radius: 20px;
                background: transparent;
            }
        """)
        
        # Обновляем размеры при изменении
        def resize_layers(event):
            self.stacked_widget.resize(self.layer_container.size())
            QWidget.resizeEvent(self.layer_container, event)
            
        self.layer_container.resizeEvent = resize_layers
        
        # Устанавливаем контейнер как центральный виджет
        self.setCentralWidget(self.central_container)
        
        # Инициализация страниц
        self.main_page = BackgroundWidget()
        self.main_page.setAttribute(Qt.WA_TranslucentBackground, True)
        self.main_page.setStyleSheet("""
            BackgroundWidget {
                border-radius: 20px;
                background-color: transparent;
            }
        """)
        
        self.settings_page = SettingsPage(self)
        self.settings_page.setAttribute(Qt.WA_TranslucentBackground, True)
        self.settings_page.setStyleSheet("""
            SettingsPage {
                border-radius: 20px;
                background-color: transparent;
            }
        """)
        
        self.setup_main_page()

        # Обёртки без paintEvent: QGraphicsOpacityEffect на BackgroundWidget ломает QPainter
        self._main_stack_wrap = QWidget()
        _ml = QVBoxLayout(self._main_stack_wrap)
        _ml.setContentsMargins(0, 0, 0, 0)
        _ml.setSpacing(0)
        _ml.addWidget(self.main_page)

        self._settings_stack_wrap = QWidget()
        _sl = QVBoxLayout(self._settings_stack_wrap)
        _sl.setContentsMargins(0, 0, 0, 0)
        _sl.setSpacing(0)
        _sl.addWidget(self.settings_page)

        self.stacked_widget.addWidget(self._main_stack_wrap)
        self.stacked_widget.addWidget(self._settings_stack_wrap)
        self.stacked_widget.setCurrentWidget(self._main_stack_wrap)
        
        self.load_settings()
        
    def get_java_dialog_shown(self):
        """Возвращает флаг показа диалога Java из настроек"""
        settings_path = Path.home() / ".ku_launcher_settings.json"
        try:
            if settings_path.exists():
                with open(settings_path, 'r') as f:
                    data = json.load(f)
                    return data.get('java_install_dialog_shown', False)
        except:
            pass
        return False
    
    def show_java_install_dialog(self, missing_versions=None):
        """Показывает диалог установки Java с отсутствующими версиями"""
        # Проверяем настройку "больше не показывать"
        if self.get_java_dialog_shown():
            print("Диалог Java не показываем (пользователь выбрал 'больше не показывать')")
            return
            
        # Проверяем, не был ли уже показан диалог в этой сессии
        if self.java_install_dialog_shown:
            return
            
        versions = missing_versions or self.missing_java_versions
        if versions:
            dialog = JavaInstallDialog(self, versions)
            dialog.exec()
            # После установки обновляем список отсутствующих версий
            self.check_java_after_start()
            # Устанавливаем флаг, что диалог был показан
            self.java_install_dialog_shown = True
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = event.globalPos() - self.frameGeometry().topLeft()
            event.accept()
    
    def mouseMoveEvent(self, event):
        if event.buttons() == Qt.LeftButton and self.drag_pos is not None:
            self.move(event.globalPos() - self.drag_pos)
            event.accept()
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.drag_pos = None
            event.accept()
    
    def closeEvent(self, event):
        print("Закрытие лаунчера, сохранение настроек...")
        self.save_settings()
        from core.utils import create_launcher_profiles
        create_launcher_profiles(self.minecraft_dir)
            
        super().closeEvent(event)
        QApplication.instance().quit()
    
    @property
    def memory_slider(self):
        return self.settings_page.memory_slider
    
    @property
    def memory_label(self):
        return self.settings_page.memory_label