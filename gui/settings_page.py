from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
from core.config import DEFAULT_MC_VERSION
from gui.widgets import BackgroundWidget
from gui.animations import UIAnimations
from pathlib import Path
import psutil

class SettingsPage(BackgroundWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self.parent = parent
        self.init_ui()
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: rgba(30, 30, 30, 180);
                width: 12px;
                border: 2px solid #444;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background: #666;
                min-height: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:vertical:hover {
                background: #777;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
        """)
        
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        scroll_content.setObjectName("scrollContent")
        
        settings_layout = QVBoxLayout(scroll_content)
        settings_layout.setSpacing(20)
        settings_layout.setContentsMargins(20, 20, 20, 20)
        
        title_label = QLabel("Настройки")
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setStyleSheet("""
            font-size: 32px;
            font-weight: bold;
            color: white;
            margin: 10px;
            padding: 10px;
            background: transparent;
            border: none;
        """)
        settings_layout.addWidget(title_label)
        
        dir_group = self.create_group_box("Директория установки")
        dir_layout = QHBoxLayout()
        dir_layout.setSpacing(10)
        self.dir_edit = QLineEdit(str(self.parent.minecraft_dir))
        self.dir_edit.setReadOnly(True)
        self.dir_edit.setStyleSheet("""
            QLineEdit {
                background: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #444;
                padding: 10px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
            }
        """)
        dir_browse = QPushButton("Обзор")
        dir_browse.setStyleSheet("""
            QPushButton {
                background: rgba(40, 40, 40, 180);
                color: white;
                border: 2px solid #444;
                padding: 10px 20px;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                min-width: 100px;
            }
            QPushButton:hover {
                border: 2px solid #888;
            }
        """)
        dir_browse.clicked.connect(self.parent.browse_directory)
        dir_layout.addWidget(self.dir_edit)
        dir_layout.addWidget(dir_browse)
        
        UIAnimations.apply_press(dir_browse, 2, 2)
        UIAnimations.apply_hover(dir_browse)
        UIAnimations.apply_hover(dir_group)
            
        dir_group.setLayout(dir_layout)
        settings_layout.addWidget(dir_group)
        
        memory_group = self.create_group_box("Выделенная память")
        UIAnimations.apply_hover(memory_group)
            
        memory_layout = QVBoxLayout()
        memory_layout.setSpacing(10)
        
        memory_info_layout = QHBoxLayout()
        memory_info_layout.addWidget(QLabel("Объем памяти:"))
        memory_info_layout.addStretch()
        self.memory_label = QLabel("4096 MB")
        self.memory_label.setStyleSheet("color: white; font-size: 16px; font-weight: bold; background: transparent; border: none;")
        memory_info_layout.addWidget(self.memory_label)
        memory_layout.addLayout(memory_info_layout)
        
        self.memory_slider = QSlider(Qt.Horizontal)
        self.memory_slider.setRange(2048, 16384)
        self.memory_slider.setSingleStep(512)
        self.memory_slider.setPageStep(1024)
        self.memory_slider.setValue(4096)
        self.memory_slider.setTickInterval(1024)
        self.memory_slider.setTickPosition(QSlider.TicksBelow)
        self.memory_slider.valueChanged.connect(
            lambda v: self.memory_label.setText(f"{v} MB")
        )
        self.memory_slider.setStyleSheet("""
            QSlider::groove:horizontal {
                border: 2px solid #444;
                height: 10px;
                background: rgba(30, 30, 30, 180);
                margin: 2px 0;
                border-radius: 5px;
            }
            QSlider::handle:horizontal {
                background: #888;
                border: 2px solid #444;
                width: 22px;
                height: 22px;
                margin: -7px 0;
                border-radius: 11px;
            }
            QSlider::handle:horizontal:hover {
                background: #999;
            }
            QSlider::tick {
                background: #444;
            }
        """)
        memory_layout.addWidget(self.memory_slider)
        
        # Получаем реальное количество доступной оперативной памяти
        try:
            total_ram = psutil.virtual_memory().total // (1024 * 1024)  # в MB
            available_ram = psutil.virtual_memory().available // (1024 * 1024)
            
            # Устанавливаем максимальное значение слайдера (80% от доступной памяти)
            max_recommended = int(total_ram * 0.8)
            self.memory_slider.setMaximum(max(4096, max_recommended))
            self.memory_slider.setValue(min(4096, max_recommended))
            
            memory_hint = QLabel(
                f"Доступно ОЗУ: {total_ram} MB (рекомендуется не более {max_recommended} MB)\n"
                f"Рекомендуется: 4096 MB (4 ГБ) для оптимальной работы"
            )
        except:
            memory_hint = QLabel(
                "Рекомендуется: 4096 MB (4 ГБ) для оптимальной работы\n"
                "(не удалось определить доступную память)"
            )
        
        memory_hint.setStyleSheet("color: #aaa; font-size: 14px; font-weight: bold; padding: 5px; background: transparent; border: none;")
        memory_hint.setWordWrap(True)
        memory_layout.addWidget(memory_hint)
        
        memory_group.setLayout(memory_layout)
        settings_layout.addWidget(memory_group)
        
        back_button = QPushButton("Назад")
        back_button.setMinimumHeight(50)
        back_button.setStyleSheet("""
            QPushButton {
                background: #666;
                color: white;
                font-size: 16px;
                font-weight: bold;
                border: 2px solid #444;
                border-radius: 8px;
                margin-top: 10px;
                letter-spacing: 1px;
            }
            QPushButton:hover {
                background: #777;
                border: 2px solid #888;
            }
        """)
        back_button.clicked.connect(self.parent.show_main_page) # Исправил на show_main_page
        settings_layout.addWidget(back_button)
        UIAnimations.apply_press(back_button, 2, 2)
        UIAnimations.apply_hover(back_button)
        
        self.elements_to_animate = [
            title_label, dir_group, memory_group, back_button
        ]
        
        scroll.setWidget(scroll_content)
        main_layout.addWidget(scroll)

    def _show_frameless_message_box(self, text, icon=QMessageBox.Warning, buttons=QMessageBox.Ok):
        msg_box = QMessageBox(self)
        msg_box.setIcon(icon)
        msg_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        msg_box.setWindowTitle("")
        msg_box.setText(text)
        msg_box.setStandardButtons(buttons)
        return msg_box.exec()

    def start_staggered_elements(self):
        """Анимация появления элементов настроек."""
        for i, widget in enumerate(self.elements_to_animate):
            UIAnimations.fade_in(widget, duration=400, delay=i*100)
            
    def create_group_box(self, title):
        group = QGroupBox(title)
        group.setStyleSheet("""
            QGroupBox {
                color: white;
                border: 2px solid #444;
                border-radius: 10px;
                margin-top: 15px;
                padding-top: 15px;
                background-color: rgba(40, 40, 40, 150);
                font-size: 16px;
                font-weight: bold;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 8px;
                background: rgba(40, 40, 40, 150);
                border-radius: 4px;
                color: white;
            }
        """)
        return group
    
    def update_info(self):
        pass
