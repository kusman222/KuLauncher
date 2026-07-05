from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import os
from core.config import DEFAULT_MC_VERSION, get_asset_path
from gui.animations import UIAnimations

class MainWindowUI:
    
    def setup_main_page(self):
        main_layout = QHBoxLayout(self.main_page)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # ЛЕВОЕ МЕНЮ
        left_menu = QWidget()
        self.left_menu = left_menu
        left_menu.setMinimumWidth(0)
        left_menu.setMaximumWidth(0)
        left_menu.setStyleSheet("""
            QWidget { background: rgba(30, 30, 30, 200); border-right: 1px solid #444; }
        """)

        menu_layout = QVBoxLayout(left_menu)
        menu_layout.setContentsMargins(8, 15, 8, 15)
        menu_layout.setSpacing(12)
        menu_layout.setAlignment(Qt.AlignTop)

        # Иконка
        icon_label = QLabel()
        icon_label.setFixedSize(50, 50)
        icon_label.setAlignment(Qt.AlignCenter)
        icon_path = get_asset_path("icon.ico")
        if os.path.exists(icon_path):
            icon_pixmap = QPixmap(icon_path).scaled(40, 40, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
        icon_label.setStyleSheet("background: transparent; border: 2px solid #444; border-radius: 8px; padding: 4px;")
        menu_layout.addWidget(icon_label)

        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background: #444; max-height: 1px; margin: 5px 0;")
        menu_layout.addWidget(separator)

        # Кнопки меню
        self.mods_button = self.create_menu_button("textures/mods.png", "Моды", self.show_mods_panel)
        self.settings_button = self.create_menu_button("textures/settings.png", "Настр", self.show_settings)
        self.exit_button = self.create_menu_button("textures/exit.png", "Выход", self.close, exit=True)

        UIAnimations.apply_hover(self.mods_button)
        UIAnimations.apply_hover(self.settings_button)
        UIAnimations.apply_hover(self.exit_button)

        menu_layout.addWidget(self.mods_button)
        menu_layout.addSpacing(15)
        menu_layout.addWidget(self.settings_button)
        menu_layout.addStretch()
        menu_layout.addWidget(self.exit_button)

        main_layout.addWidget(left_menu)

        # ПРАВАЯ ЧАСТЬ
        right_content = QWidget()
        self.right_content = right_content
        right_content.setStyleSheet("background: transparent;")
        right_layout = QVBoxLayout(right_content)
        right_layout.setContentsMargins(30, 10, 30, 10)
        right_layout.setSpacing(0)

        # Верхняя панель с заголовком и информацией о версии
        top_bar = QWidget()
        top_bar.setStyleSheet("background: transparent;")
        top_bar.setFixedHeight(60)
        top_layout = QHBoxLayout(top_bar)
        top_layout.setContentsMargins(0, 0, 0, 0)
        
        # Заголовок слева
        self.title_label = QLabel("KuLauncher")
        self.title_label.setAlignment(Qt.AlignLeft)
        self.title_label.setStyleSheet("font-size: 42px; font-weight: bold; color: white; margin: 5px 0 0 0;")
        top_layout.addWidget(self.title_label)
        
        top_layout.addStretch()
        
        # Информация о версии и лицензии справа
        self.version_info = QLabel("Версия 1.3 Beta | MIT")
        self.version_info.setAlignment(Qt.AlignRight)
        self.version_info.setStyleSheet("""
            color: #888; 
            font-size: 11px; 
            font-weight: bold;
            padding: 3px 8px;
            background: rgba(40, 40, 40, 100);
            border: 1px solid #444;
            border-radius: 4px;
            max-height: 16px;
        """)
        top_layout.addWidget(self.version_info)
        
        right_layout.addWidget(top_bar)

        right_layout.addStretch(5)

        # Прогресс + статус
        self.progress_container = QWidget()
        progress_layout = QVBoxLayout(self.progress_container)
        progress_layout.setContentsMargins(0, 0, 0, 2)
        progress_layout.setSpacing(2)

        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar { border: 2px solid #444; border-radius: 5px; text-align: center;
                           background: rgba(30, 30, 30, 180); height: 25px; color: white;
                           font-size: 14px; font-weight: bold; }
            QProgressBar::chunk { background: #666; border-radius: 3px; }
        """)
        self.progress_bar.hide()
        progress_layout.addWidget(self.progress_bar)

        self.status_label = QLabel("Готов к запуску")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 14px; font-weight: bold;")
        progress_layout.addWidget(self.status_label)

        right_layout.addWidget(self.progress_container)
        right_layout.addSpacing(5)

        # Панель управления
        self.controls_container = QWidget()
        self.controls_container.setStyleSheet("background: transparent;")
        controls_layout = QHBoxLayout(self.controls_container)
        controls_layout.setSpacing(20)
        controls_layout.setContentsMargins(0, 0, 0, 5)
        controls_layout.setAlignment(Qt.AlignCenter)

        # Имя игрока
        self.name_group = QGroupBox("Имя игрока")
        self.name_group.setFixedWidth(220)
        self.name_group.setStyleSheet("""
            QGroupBox { color: white; border: 2px solid #444; border-radius: 8px; margin-top: 5px;
                        padding-top: 5px; background: rgba(40, 40, 40, 150); font-size: 14px; font-weight: bold; }
            QGroupBox::title { left: 8px; padding: 0 5px; }
        """)
        name_layout = QVBoxLayout()
        name_layout.setContentsMargins(8, 8, 8, 8)
        self.name_edit = QLineEdit("Player")
        self.name_edit.setStyleSheet("""
            QLineEdit { background: rgba(30, 30, 30, 180); color: white; border: 2px solid #444;
                        padding: 8px; border-radius: 6px; font-size: 14px; font-weight: bold; }
            QLineEdit:focus { border: 2px solid #888; }
        """)
        name_layout.addWidget(self.name_edit)
        self.name_group.setLayout(name_layout)
        UIAnimations.apply_hover(self.name_group)
        controls_layout.addWidget(self.name_group)

        # Версия
        self.version_group = QGroupBox("Версия")
        self.version_group.setFixedWidth(160)
        self.version_group.setStyleSheet("""
            QGroupBox { color: white; border: 2px solid #444; border-radius: 8px; margin-top: 5px;
                        padding-top: 5px; background: rgba(40, 40, 40, 150); font-size: 14px; font-weight: bold; }
            QGroupBox::title { left: 8px; padding: 0 5px; }
            QGroupBox:hover { border: 2px solid #888; }
        """)
        self.version_group.mousePressEvent = self.on_version_group_click
        self.version_group.enterEvent = lambda e: self.version_group.setCursor(Qt.PointingHandCursor)
        self.version_group.leaveEvent = lambda e: self.version_group.setCursor(Qt.ArrowCursor)

        version_layout = QVBoxLayout()
        version_layout.setSpacing(2)
        version_layout.setContentsMargins(5, 5, 5, 5)
        self.version_label = QLabel(self.current_mc_version)
        self.version_label.setAlignment(Qt.AlignCenter)
        self.version_label.setStyleSheet("font-size: 16px; font-weight: bold; color: white;")
        version_layout.addWidget(self.version_label)
        
        # Тип версии
        self.version_type_label = QLabel("release")
        self.version_type_label.setAlignment(Qt.AlignCenter)
        self.version_type_label.setStyleSheet("color: #888; font-size: 11px;")
        version_layout.addWidget(self.version_type_label)
        
        self.version_group.setLayout(version_layout)
        UIAnimations.apply_hover(self.version_group)
        controls_layout.addWidget(self.version_group)


        # Кнопка ИГРАТЬ
        self.play_button = QPushButton("ИГРАТЬ")
        self.play_button.setFixedSize(200, 60)
        self.play_button.setStyleSheet("""
            QPushButton { background: #666; color: white; border: 2px solid #444; border-radius: 10px;
                          font-size: 20px; font-weight: bold; letter-spacing: 2px; }
            QPushButton:hover { background: #777; border: 2px solid #888; }
            QPushButton:disabled { background: #2d2d2d; color: #666; }
        """)
        self.play_button.clicked.connect(self.launch_game)
        UIAnimations.apply_press(self.play_button, 4, 3)
        UIAnimations.apply_hover(self.play_button)
        controls_layout.addWidget(self.play_button)

        right_layout.addWidget(self.controls_container)
        main_layout.addWidget(right_content, 1)

        self.setWindowTitle("KuLauncher")
        self.setFixedSize(1100, 600)

        if os.path.exists(icon_path := get_asset_path("icon.ico")):
            self.setWindowIcon(QIcon(icon_path))

        self.start_entrance_animations()

    def create_menu_button(self, icon_name, text, slot, exit=False):
        btn = QPushButton()
        btn.setFixedSize(50, 50)
        btn.setIconSize(QSize(30, 30))
        icon_path = get_asset_path(icon_name)
        if os.path.exists(icon_path):
            btn.setIcon(QIcon(icon_path))
        else:
            btn.setText(text)
        color = "#FF4444" if exit else "#888"
        btn.setStyleSheet(f"""
            QPushButton {{ background: transparent; border: 2px solid #444; border-radius: 8px;
                          color: white; font-size: 12px; font-weight: bold; padding: 4px; }}
            QPushButton:hover {{ border: 2px solid {color}; }}
        """)
        btn.clicked.connect(slot)
        UIAnimations.apply_press(btn, 2, 2)
        return btn

    # Вход: меню + каскадное появление элементов
    def start_entrance_animations(self):
        self.entrance_group = QParallelAnimationGroup()

        # 1. Левое меню
        menu_anim = QPropertyAnimation(self.left_menu, b"maximumWidth")
        menu_anim.setStartValue(0)
        menu_anim.setEndValue(70)
        menu_anim.setDuration(400)
        menu_anim.setEasingCurve(QEasingCurve.OutCubic)
        self.entrance_group.addAnimation(menu_anim)

        # 2. Постепенное появление правой части
        self.right_opacity_effect = QGraphicsOpacityEffect(self.right_content)
        self.right_content.setGraphicsEffect(self.right_opacity_effect)
        
        fade_anim = QPropertyAnimation(self.right_opacity_effect, b"opacity")
        fade_anim.setStartValue(0.0)
        fade_anim.setEndValue(1.0)
        fade_anim.setDuration(600)
        fade_anim.setEasingCurve(QEasingCurve.InOutQuad)
        self.entrance_group.addAnimation(fade_anim)

        # 3. Каскадное появление внутренних элементов
        # Мы запустим их чуть позже
        self.entrance_group.finished.connect(self.start_staggered_elements)
        self.entrance_group.start()

    def start_staggered_elements(self):
        # Очищаем эффект с right_content, чтобы он не мешал дочерним эффектам
        self.right_content.setGraphicsEffect(None)
        
        # Список элементов для каскадного появления
        elements = [
            (self.title_label, 0),
            (self.version_info, 100),
            (self.progress_container, 200),
            (self.name_group, 300),
            (self.version_group, 400),
            (self.play_button, 500)
        ]
        
        for widget, delay in elements:
            # Используем общую анимацию (без перемещения, чтобы не ломать layout)
            UIAnimations.fade_in(widget, duration=400, delay=delay)

    def on_entrance_finished(self):
        self.left_menu.setFixedWidth(70)
        # self.right_content.setGraphicsEffect(None) # Теперь это в start_staggered_elements

    @Slot(int)
    def animate_progress(self, value):
        """Плавное обновление прогресс-бара."""
        if not hasattr(self, "_progress_anim"):
            self._progress_anim = QPropertyAnimation(self.progress_bar, b"value")
            self._progress_anim.setDuration(300)
            self._progress_anim.setEasingCurve(QEasingCurve.OutCubic)
        
        self._progress_anim.stop()
        self._progress_anim.setStartValue(self.progress_bar.value())
        self._progress_anim.setEndValue(int(value))
        self._progress_anim.start()

    @Slot(str)
    def set_status(self, text):
        """Плавная смена текста статуса."""
        if self.status_label.text() == text:
            return
            
        # Анимация затухания -> смена текста -> появление
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

    def on_version_group_click(self, event):
        if event.button() == Qt.LeftButton:
            self.show_version_selector()



    def show_version_selector(self):
        from dialogs.version_selector import VersionSelectorDialog
        dialog = VersionSelectorDialog(self, self.current_mc_version, self.current_version_type)
        if dialog.exec() == QDialog.Accepted:
            selected = dialog.get_selected_version()
            if selected:
                self.current_mc_version = selected["id"]
                self.current_version_type = selected.get("type", "release")
                self.version_label.setText(selected["id"])
                
                self.version_type_label.setText(self.current_version_type)
                self.version_type_label.setStyleSheet("color: #888; font-size: 11px;")

                self.status_label.setText(f"Выбрана версия: {selected['id']} ({self.current_version_type})")

    def show_mods_panel(self):
        from gui.mods_panel import ModsPanel
        self.mods_panel = ModsPanel(self, self.minecraft_dir)
        self.mods_panel.show()

    def show_settings(self):
        # Анимация исчезновения текущей страницы
        self.animate_page_transition(self._main_stack_wrap, self._settings_stack_wrap)

    def show_main_page(self):
        # Анимация возврата на главную
        self.animate_page_transition(self._settings_stack_wrap, self._main_stack_wrap)

    def animate_page_transition(self, old_page, new_page):
        """Мгновенное переключение с анимацией появления элементов."""
        self.stacked_widget.setCurrentWidget(new_page)
        
        if new_page == self._main_stack_wrap:
            self.start_staggered_elements()
        elif new_page == self._settings_stack_wrap:
            self.settings_page.start_staggered_elements()
