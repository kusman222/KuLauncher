from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from pathlib import Path
import shutil
import os
from core.config import get_asset_path
from gui.animations import UIAnimations

class ModsPanel(QWidget):
    def __init__(self, parent, minecraft_dir):
        super().__init__(parent)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Window)
        self.drag_pos = None
        self.minecraft_dir = minecraft_dir
        self.mods_dir = self.minecraft_dir / "mods"
        self.mods_dir.mkdir(exist_ok=True)
        self.init_ui()
        self.update_mods_list()
        
        # Анимация появления
        UIAnimations.entrance_dialog(self, duration=300)
        
    def init_ui(self):
        self.setWindowTitle("Установка модов")
        self.setFixedSize(850, 550)
        self.setAcceptDrops(True)
        
        # Черно-белая тема для панели модов
        self.setStyleSheet("""
            QWidget {
                background: #2d2d2d;
                border: 2px solid #444;
                border-radius: 15px;
            }
            QLabel {
                color: white;
                font-size: 15px;
                font-weight: bold;
            }
            QGroupBox {
                color: white;
                border: 2px solid #444;
                border-radius: 10px;
                margin-top: 12px;
                padding-top: 15px;
                font-size: 15px;
                font-weight: bold;
                background: rgba(40, 40, 40, 150);
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 8px;
                color: white;
            }
            QListWidget {
                background: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #444;
                border-radius: 8px;
                font-size: 14px;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #444;
            }
            QListWidget::item:selected {
                background: #666;
            }
            QListWidget::item:hover {
                background: rgba(60, 60, 60, 180);
            }
            QPushButton {
                background: rgba(40, 40, 40, 180);
                color: white;
                border: 2px solid #444;
                padding: 10px;
                border-radius: 8px;
                font-size: 15px;
                font-weight: bold;
            }
            QPushButton:hover {
                border: 2px solid #888;
            }
            QPushButton#deleteBtn {
                color: #FF4444;
            }
            QPushButton#deleteBtn:hover {
                border: 2px solid #FF4444;
            }
            QPushButton#closeBtn {
                background: transparent;
                border: 2px solid #444;
                border-radius: 8px;
            }
            QPushButton#closeBtn:hover {
                border: 2px solid #FF4444;
            }
        """)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        title_bar = QHBoxLayout()
        title_bar.setContentsMargins(0, 0, 0, 0)
        
        title_label = QLabel("Установка модов")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("font-size: 24px; font-weight: bold; color: white; background: transparent; border: none;")
        title_bar.addWidget(title_label)
        
        close_btn = QPushButton()
        close_btn.setObjectName("closeBtn")
        close_btn.setFixedSize(40, 40)
        close_btn.setIconSize(QSize(30, 30))
        exit_icon_path = get_asset_path("textures/exit.png")
        if os.path.exists(exit_icon_path):
            close_btn.setIcon(QIcon(exit_icon_path))
        else:
            close_btn.setText("X")
            close_btn.setStyleSheet("font-size: 16px; font-weight: bold;")
        close_btn.clicked.connect(self.close)
        title_bar.addWidget(close_btn)
        
        main_layout.addLayout(title_bar)
        
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        drop_area = QWidget()
        drop_area.setAcceptDrops(True)
        drop_area.setStyleSheet("""
            QWidget {
                background: rgba(30, 30, 30, 180);
                border: 2px dashed #444;
                border-radius: 10px;
            }
            QWidget:hover {
                border: 2px dashed #888;
            }
        """)
        drop_layout = QVBoxLayout(drop_area)
        drop_layout.setAlignment(Qt.AlignCenter)
        
        info_label = QLabel("Перетащите JAR-файлы модов сюда")
        info_label.setAlignment(Qt.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet("font-size: 18px; font-weight: bold; color: white; border: none; padding: 20px;")
        drop_layout.addWidget(info_label)
        
        self.status_label = QLabel("")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #aaa; font-size: 15px; font-weight: bold; border: none;")
        drop_layout.addWidget(self.status_label)
        
        content_layout.addWidget(drop_area)
        
        mods_group = QGroupBox("Установленные моды")
        mods_layout = QVBoxLayout(mods_group)
        
        self.mods_list = QListWidget()
        mods_layout.addWidget(self.mods_list)
        
        delete_btn = QPushButton("Удалить выбранный")
        delete_btn.setObjectName("deleteBtn")
        delete_btn.clicked.connect(self.delete_selected_mod)
        mods_layout.addWidget(delete_btn)
        
        content_layout.addWidget(mods_group)
        
        main_layout.addLayout(content_layout)

        UIAnimations.apply_press(close_btn, 2, 2)
        UIAnimations.apply_press(delete_btn, 2, 2)
        
        UIAnimations.apply_hover(close_btn)
        UIAnimations.apply_hover(delete_btn)
        UIAnimations.apply_hover(mods_group)
        UIAnimations.apply_hover(drop_area)

        # Анимация появления элементов внутри панели
        self.animate_internal_elements([title_label, drop_area, mods_group])

    def animate_internal_elements(self, elements):
        for i, widget in enumerate(elements):
            UIAnimations.fade_in(widget, duration=500, delay=i*100)

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
    
    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                if url.toLocalFile().lower().endswith('.jar'):
                    event.accept()
                    return
        event.ignore()
    
    def dropEvent(self, event):
        installed = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if file_path.lower().endswith('.jar'):
                try:
                    dest_path = self.mods_dir / Path(file_path).name
                    if not dest_path.exists():
                        shutil.copy(file_path, dest_path)
                        installed.append(Path(file_path).name)
                except Exception as e:
                    self.status_label.setText(f"Ошибка установки {Path(file_path).name}: {str(e)}")
                    return
        
        if installed:
            self.status_label.setText(f"Установлены: {', '.join(installed)}")
            self.update_mods_list()
        else:
            self.status_label.setText("Нет JAR-файлов")
    
    def update_mods_list(self):
        self.mods_list.clear()
        for mod_file in self.mods_dir.glob("*.jar"):
            self.mods_list.addItem(mod_file.name)
    
    def delete_selected_mod(self):
        item = self.mods_list.currentItem()
        if item:
            mod_name = item.text()
            mod_path = self.mods_dir / mod_name
            if mod_path.exists():
                try:
                    os.remove(mod_path)
                    self.update_mods_list()
                    self.status_label.setText(f"Мод {mod_name} удален")
                except Exception as e:
                    self.status_label.setText(f"Ошибка удаления: {str(e)}")
            else:
                self.status_label.setText("Мод не найден")
        else:
            self.status_label.setText("Выберите мод для удаления")