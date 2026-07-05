from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import os
import sys
import requests
from pathlib import Path
from core.config import get_asset_path, PROJECT_DIR
from gui.animations import UIAnimations

class AssetsCheckDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        self.setFixedSize(800, 500)
        
        self.missing_files = []
        self.drag_pos = None
        self.download_thread = None
        self.auto_close_timer = None
        self.background_label = None
        
        self.init_ui()
        self.check_assets()
        
        # Анимация появления
        UIAnimations.entrance_dialog(self, duration=400)
    
    def update_status_animated(self, text):
        """Плавная смена текста статуса."""
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

    def update_progress_animated(self, value):
        """Плавное обновление прогресс-бара."""
        if not hasattr(self, "_progress_anim"):
            self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
            self._progress_anim.setDuration(300)
            self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(int(value))
        self._progress_anim.start()
    
    def init_ui(self):
        self.set_background_image()
        
        main_container = QWidget(self)
        main_container.setGeometry(0, 0, 800, 500)
        main_container.setObjectName("mainContainer")
        main_container.setStyleSheet("""
            #mainContainer {
                background: transparent;
            }
        """)
        
        layout = QVBoxLayout(main_container)
        layout.setContentsMargins(30, 30, 30, 30)
        layout.setSpacing(20)
        
        title_container = QWidget()
        title_container.setObjectName("titleContainer")
        title_container.setStyleSheet("""
            #titleContainer {
                background: rgba(0, 0, 0, 150);
                padding: 15px;
                border: 2px solid #444;
                border-radius: 10px;
            }
        """)
        title_layout = QVBoxLayout(title_container)
        
        title_label = QLabel("KuLauncher")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 42px;
            font-weight: bold;
            color: white;
            background: transparent;
            border: none;
        """)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Проверка файлов")
        subtitle_label.setAlignment(Qt.AlignCenter)
        subtitle_label.setStyleSheet("""
            font-size: 18px;
            color: #aaa;
            background: transparent;
            border: none;
            margin-top: -5px;
        """)
        title_layout.addWidget(subtitle_label)
        
        layout.addWidget(title_container)
        layout.addStretch()
        
        status_container = QWidget()
        status_container.setObjectName("statusContainer")
        status_container.setStyleSheet("""
            #statusContainer {
                background: rgba(0, 0, 0, 150);
                padding: 20px;
                border: 2px solid #444;
                border-radius: 10px;
            }
        """)
        status_layout = QVBoxLayout(status_container)
        status_layout.setSpacing(15)
        
        self.status_label = QLabel("Проверка файлов...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("""
            color: white;
            font-size: 18px;
            background: transparent;
            border: none;
            font-weight: bold;
        """)
        status_layout.addWidget(self.status_label)
        
        self.details_label = QLabel("")
        self.details_label.setAlignment(Qt.AlignCenter)
        self.details_label.setStyleSheet("""
            color: #aaa;
            font-size: 14px;
            background: transparent;
            border: none;
            font-weight: bold;
        """)
        status_layout.addWidget(self.details_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #444;
                text-align: center;
                background: rgba(0, 0, 0, 100);
                height: 25px;
                font-size: 14px;
                color: white;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: #666;
            }
        """)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        self.files_list = QListWidget()
        self.files_list.setStyleSheet("""
            QListWidget {
                background: rgba(30, 30, 30, 150);
                color: white;
                border: 2px solid #444;
                padding: 5px;
                font-size: 14px;
                font-weight: bold;
                max-height: 100px;
            }
            QListWidget::item {
                padding: 2px;
                border-bottom: 1px solid #333;
            }
            QListWidget::item:last-child {
                border-bottom: none;
            }
        """)
        self.files_list.hide()
        status_layout.addWidget(self.files_list)
        
        layout.addWidget(status_container)
    
    def set_background_image(self):
        bg_path = get_asset_path("textures/background.jpg")
        
        if os.path.exists(bg_path):
            pixmap = QPixmap(bg_path)
            if not pixmap.isNull():
                self.background_label = QLabel(self)
                self.background_label.setGeometry(0, 0, 800, 500)
                
                scaled_pixmap = pixmap.scaled(800, 500, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
                self.background_label.setPixmap(scaled_pixmap)
                self.background_label.lower()
                
                self.setStyleSheet("""
                    QDialog {
                        background: transparent;
                    }
                """)
            else:
                self.set_fallback_background()
        else:
            self.set_fallback_background()
    
    def set_fallback_background(self):
        self.setStyleSheet("""
            QDialog {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 #1a1a1a, stop:1 #2d2d2d);
                border: 2px solid #444;
            }
        """)
    
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
    
    def check_assets(self):
        required_files = [
            "textures/background.jpg",
            "textures/settings.png",
            "textures/mods.png",
            "textures/exit.png",
            "icon.ico",
            "mine.ttf"
        ]
        
        self.missing_files = []
        existing_files = []
        corrupted_files = []
        
        for filename in required_files:
            file_path = get_asset_path(filename)
            if os.path.exists(file_path):
                if os.path.getsize(file_path) > 0:
                    existing_files.append(filename)
                else:
                    corrupted_files.append(filename)
            else:
                self.missing_files.append(filename)
        
        self.details_label.setText(f"Найдено: {len(existing_files)}/{len(required_files)}")
        
        total_problems = len(self.missing_files) + len(corrupted_files)
        
        if total_problems > 0:
            if len(corrupted_files) > 0:
                QMessageBox.critical(
                    self,
                    "KuLauncher поврежден",
                    "Обнаружены поврежденные файлы лаунчера.\n\n"
                    "Пожалуйста, переустановите KuLauncher."
                )
                self.reject()
                return
            
            if len(self.missing_files) > 0:
                self.status_label.setText(f"Отсутствует {len(self.missing_files)} файл(ов)")
                self.details_label.setText("Запуск невозможен")
                
                self.files_list.show()
                for filename in self.missing_files:
                    self.files_list.addItem(filename)
                
                QMessageBox.critical(
                    self,
                    "Ошибка",
                    f"Отсутствуют необходимые файлы KuLauncher.\n\n"
                    f"Пожалуйста, переустановите KuLauncher."
                )
                self.reject()
        else:
            self.status_label.setText("Все файлы в порядке")
            self.details_label.setText("Запуск KuLauncher...")
            QTimer.singleShot(1500, self.accept)
    
    def update_status(self, text):
        QMetaObject.invokeMethod(self, "update_status_animated",
                                 Q_ARG(str, text))
    
    def update_progress(self, value):
        QMetaObject.invokeMethod(self, "update_progress_animated",
                                 Q_ARG(int, value))
    
    def on_file_downloaded(self, filename):
        pass
    
    def on_download_finished(self, success, message):
        pass


class DownloadAssetsThread(QThread):
    progress = Signal(int)
    status = Signal(str)
    file_downloaded = Signal(str)
    finished = Signal(bool, str)
    
    def __init__(self, files_to_download):
        super().__init__()
        self.files_to_download = files_to_download
    
    def run(self):
        pass