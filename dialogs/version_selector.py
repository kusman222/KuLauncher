from PySide6.QtWidgets import *
from PySide6.QtCore import *
from PySide6.QtGui import *
import minecraft_launcher_lib
import threading
import shutil
import os
import json
from pathlib import Path
from core.config import VERSION_TYPES, get_asset_path
from gui.animations import UIAnimations

class VersionSelectorDialog(QDialog):
    
    def __init__(self, parent=None, current_version=None, current_type=None):
        super().__init__(parent)
        self.parent = parent
        self.current_version = current_version
        self.current_type = current_type or "release"
        self.versions = []
        self.filtered_versions = []
        self.loading_thread = None
        self.selected_version = None
        self.drag_pos = None
        self.installed_versions = []
        self.current_delete_button = None
        
        self.init_ui()
        self.load_versions()
        
        # Анимация появления
        UIAnimations.entrance_dialog(self)

    def init_ui(self):
        self.setWindowTitle("Выбор версии Minecraft")
        self.setFixedSize(850, 550)
        self.setModal(True)
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        
        self.setStyleSheet("""
            QDialog {
                background-color: #2d2d2d;
                color: white;
                border: 2px solid #444;
            }
            QLabel {
                color: white;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit {
                background: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #444;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QLineEdit:focus {
                border: 2px solid #888;
            }
            QListWidget {
                background: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #444;
                border-radius: 6px;
                outline: none;
                font-size: 12px;
                font-weight: bold;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 2px solid #444;
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
                padding: 8px 16px;
                border-radius: 6px;
                border: 2px solid #444;
                min-width: 80px;
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                border: 2px solid #888;
            }
            QPushButton:disabled {
                background: rgba(30, 30, 30, 180);
                color: #666;
                border: 2px solid #444;
            }
            QPushButton#deleteBtn {
                background: rgba(60, 40, 40, 180);
                border: 2px solid #FF4444;
                color: #FF4444;
                min-width: 20px;
                max-width: 20px;
                width: 20px;
                padding: 0px;
                font-size: 10px;
            }
            QPushButton#deleteBtn:hover {
                background: rgba(80, 50, 50, 180);
                border: 2px solid #FF6666;
                color: #FF6666;
            }
            QComboBox {
                background: rgba(30, 30, 30, 180);
                color: white;
                border: 2px solid #444;
                padding: 8px;
                border-radius: 6px;
                font-size: 12px;
                font-weight: bold;
            }
            QComboBox:hover {
                border: 2px solid #888;
            }
            QComboBox::drop-down {
                border: 0px;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #2d2d2d;
                color: white;
                selection-background-color: #666;
                border: 2px solid #444;
                font-size: 12px;
            }
            QCheckBox {
                color: white;
                spacing: 5px;
                font-size: 12px;
                font-weight: bold;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
            }
            QCheckBox::indicator:unchecked {
                border: 2px solid #444;
                background: rgba(30, 30, 30, 180);
                border-radius: 4px;
            }
            QCheckBox::indicator:checked {
                border: 2px solid #888;
                background: #666;
                border-radius: 4px;
            }
            QProgressBar {
                border: 2px solid #444;
                border-radius: 5px;
                text-align: center;
                background: rgba(30, 30, 30, 180);
                height: 20px;
                color: white;
                font-size: 11px;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background: #666;
                border-radius: 3px;
            }
            QScrollBar:vertical {
                background: rgba(30, 30, 30, 180);
                width: 8px;
                border-radius: 4px;
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
                border: none;
                background: none;
            }
            QScrollBar:horizontal {
                background: rgba(30, 30, 30, 180);
                height: 8px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal {
                background: #666;
                min-width: 20px;
                border-radius: 4px;
            }
            QScrollBar::handle:horizontal:hover {
                background: #777;
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                border: none;
                background: none;
            }
        """)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        filter_layout = QHBoxLayout()
        
        self.search_edit = QLineEdit()
        self.search_edit.setPlaceholderText("Поиск версии...")
        self.search_edit.textChanged.connect(self.filter_versions)
        filter_layout.addWidget(self.search_edit, 2)
        
        self.type_combo = QComboBox()
        self.type_combo.addItem("Все типы", "all")
        for version_type in VERSION_TYPES:
            display_name = {
                "release": "Релизы",
                "snapshot": "Снимки",
                "old_beta": "Бета",
                "old_alpha": "Альфа"
            }.get(version_type, version_type)
            self.type_combo.addItem(display_name, version_type)
        self.type_combo.currentIndexChanged.connect(self.filter_versions)
        filter_layout.addWidget(self.type_combo, 1)
        
        self.installed_checkbox = QCheckBox("Только установленные")
        self.installed_checkbox.stateChanged.connect(self.filter_versions)
        filter_layout.addWidget(self.installed_checkbox, 1)
        
        layout.addLayout(filter_layout)
        
        self.versions_list = QListWidget()
        self.versions_list.itemDoubleClicked.connect(self.accept)
        self.versions_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.versions_list.verticalScrollBar().valueChanged.connect(self.on_scroll)
        self.versions_list.setVerticalScrollMode(QAbstractItemView.ScrollPerPixel)
        layout.addWidget(self.versions_list)
        
        status_layout = QHBoxLayout()
        self.status_label = QLabel("Загрузка списка версий...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #888; font-size: 12px;")
        status_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)
        self.progress_bar.hide()
        status_layout.addWidget(self.progress_bar)
        
        layout.addLayout(status_layout)
        
        buttons_layout = QHBoxLayout()
        
        self.refresh_btn = QPushButton("Обновить")
        UIAnimations.apply_hover(self.refresh_btn)
        UIAnimations.apply_press(self.refresh_btn)
        self.refresh_btn.clicked.connect(self.load_versions)
        buttons_layout.addWidget(self.refresh_btn)
        
        buttons_layout.addStretch()
        
        self.select_btn = QPushButton("Выбрать")
        UIAnimations.apply_hover(self.select_btn)
        UIAnimations.apply_press(self.select_btn)
        self.select_btn.clicked.connect(self.accept)
        self.select_btn.setEnabled(False)
        self.select_btn.setStyleSheet("""
            QPushButton {
                background: #666;
                color: white;
                border: 2px solid #444;
            }
            QPushButton:hover {
                background: #777;
                border: 2px solid #888;
            }
        """)
        buttons_layout.addWidget(self.select_btn)
        
        self.cancel_btn = QPushButton("Отмена")
        UIAnimations.apply_hover(self.cancel_btn)
        UIAnimations.apply_press(self.cancel_btn)
        self.cancel_btn.clicked.connect(self.reject)
        buttons_layout.addWidget(self.cancel_btn)

        
        layout.addLayout(buttons_layout)
    
    def on_scroll(self):
        self.remove_delete_button()
    
    def on_selection_changed(self):
        self.remove_delete_button()
        
        current_item = self.versions_list.currentItem()
        if current_item:
            version_data = current_item.data(Qt.UserRole)
            if version_data and version_data.get("installed", False):
                self.add_delete_button_to_item(current_item)
    
    def remove_delete_button(self):
        if self.current_delete_button:
            try:
                self.current_delete_button.deleteLater()
                self.current_delete_button = None
            except:
                pass
    
    def update_delete_button_position(self):
        if self.current_delete_button and self.current_delete_button.isVisible():
            current_item = self.versions_list.currentItem()
            if current_item:
                rect = self.versions_list.visualItemRect(current_item)
                if rect.isValid() and rect.y() >= 0 and rect.y() < self.versions_list.height():
                    btn_x = rect.right() - self.current_delete_button.width() - 10
                    btn_y = rect.top() + (rect.height() - self.current_delete_button.height()) // 2
                    self.current_delete_button.move(btn_x, btn_y)
                    self.current_delete_button.show()
                else:
                    self.current_delete_button.hide()
            else:
                self.remove_delete_button()
    
    def add_delete_button_to_item(self, item):
        if self.current_delete_button:
            self.remove_delete_button()
        
        rect = self.versions_list.visualItemRect(item)
        
        if not rect.isValid() or rect.y() < 0 or rect.y() >= self.versions_list.height():
            return
        
        delete_btn = QPushButton("X", self.versions_list)
        delete_btn.setObjectName("deleteBtn")
        delete_btn.setFixedSize(20, 20)
        UIAnimations.apply_hover(delete_btn)
        UIAnimations.apply_press(delete_btn, 1, 1)
        
        delete_icon_path = get_asset_path("textures/delete.png")
        if os.path.exists(delete_icon_path):
            delete_btn.setIcon(QIcon(delete_icon_path))
            delete_btn.setIconSize(QSize(16, 16))
            delete_btn.setText("")
        
        btn_x = rect.right() - delete_btn.width() - 10
        btn_y = rect.top() + (rect.height() - delete_btn.height()) // 2
        delete_btn.move(btn_x, btn_y)
        
        version_data = item.data(Qt.UserRole)
        delete_btn.clicked.connect(lambda: self.delete_version(version_data))
        
        delete_btn.show()
        
        self.current_delete_button = delete_btn
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            if self.current_delete_button and self.current_delete_button.isVisible():
                mapped_pos = self.versions_list.mapFromGlobal(event.globalPos())
                if not self.current_delete_button.geometry().contains(mapped_pos):
                    self.remove_delete_button()
                    self.versions_list.clearSelection()
                    self.versions_list.setCurrentItem(None)
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
    
    def resizeEvent(self, event):
        super().resizeEvent(event)
        self.update_delete_button_position()
    
    def load_versions(self):
        self.versions_list.clear()
        self.remove_delete_button()
        self.versions_list.addItem("Загрузка списка версий...")
        self.versions_list.setEnabled(False)
        self.refresh_btn.setEnabled(False)
        self.select_btn.setEnabled(False)
        self.status_label.setText("Загрузка списка версий...")
        self.progress_bar.show()
        
        self.loading_thread = threading.Thread(target=self._load_versions_thread, daemon=True)
        self.loading_thread.start()
    
    def _load_versions_thread(self):
        try:
            cache_file = Path(self.parent.minecraft_dir) / "versions_cache.json" if hasattr(self.parent, 'minecraft_dir') else Path.home() / ".ku_launcher_versions_cache.json"
            
            versions = None
            import time
            
            # Попытка загрузить из кэша, если он свежий (например, менее 1 часа)
            if cache_file.exists():
                try:
                    if time.time() - cache_file.stat().st_mtime < 3600:
                        with open(cache_file, 'r', encoding='utf-8') as f:
                            # Читаем содержимое файла
                            content = f.read()
                            if content.strip():
                                try:
                                    versions = json.loads(content)
                                except json.JSONDecodeError as e:
                                    print(f"Кэш поврежден ({e}), будет загружен новый")
                                    versions = None
                except Exception as e:
                    print(f"Ошибка чтения кэша версий: {e}")
            
            # Если кэша нет или он устарел, загружаем с сервера
            if versions is None:
                versions = minecraft_launcher_lib.utils.get_version_list()
                
                # Обработка datetime объектов для сериализации
                import datetime
                for version in versions:
                    if "releaseTime" in version and isinstance(version["releaseTime"], datetime.datetime):
                        version["releaseTime"] = version["releaseTime"].isoformat()
                    if "time" in version and isinstance(version["time"], datetime.datetime):
                        version["time"] = version["time"].isoformat()
                
                try:
                    with open(cache_file, 'w', encoding='utf-8') as f:
                        json.dump(versions, f)
                except Exception as e:
                    print(f"Ошибка записи кэша версий: {e}")
            
            if hasattr(self.parent, 'minecraft_dir'):
                self.installed_versions = minecraft_launcher_lib.utils.get_installed_versions(str(self.parent.minecraft_dir))
            installed_ids = [v["id"] for v in self.installed_versions]
            
            for version in versions:
                version["installed"] = version["id"] in installed_ids
                if "releaseTime" in version and not isinstance(version["releaseTime"], str):
                    version["releaseTime"] = str(version["releaseTime"])
            
            self._versions_result = versions
            QMetaObject.invokeMethod(self, "_update_versions_list_slot", Qt.QueuedConnection)
            
        except Exception as e:
            self._error_msg = f"Ошибка загрузки версий: {str(e)}"
            QMetaObject.invokeMethod(self, "_show_error_slot", Qt.QueuedConnection)
    
    @Slot()
    def _update_versions_list_slot(self):
        if hasattr(self, '_versions_result'):
            self._update_versions_list(self._versions_result)
            
    @Slot()
    def _show_error_slot(self):
        if hasattr(self, '_error_msg'):
            self._show_error(self._error_msg)
            
    def _update_versions_list(self, versions):
        self.versions = versions
        self.filter_versions()
        
        self.versions_list.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.progress_bar.hide()
        self.status_label.setText(f"Найдено версий: {len(self.versions)}")
        
        if self.current_version:
            for i in range(self.versions_list.count()):
                item = self.versions_list.item(i)
                if item and item.text() == self.current_version:
                    self.versions_list.setCurrentItem(item)
                    self.select_btn.setEnabled(True)
                    break
    
    @Slot(str)
    def _show_error(self, error_msg):
        self.versions_list.clear()
        self.versions_list.addItem(error_msg)
        self.versions_list.setEnabled(True)
        self.refresh_btn.setEnabled(True)
        self.progress_bar.hide()
        self.status_label.setText("Ошибка загрузки")
        
        error_box = QMessageBox(self)
        error_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        error_box.setWindowTitle("")
        error_box.setText(error_msg)
        error_box.setStandardButtons(QMessageBox.Ok)
        ok_button = error_box.button(QMessageBox.Ok)
        if ok_button:
            ok_button.setText("OK")
        error_box.exec()
    
    def filter_versions(self):
        self.versions_list.clear()
        self.remove_delete_button()
        
        search_text = self.search_edit.text().lower()
        filter_type = self.type_combo.currentData()
        show_only_installed = self.installed_checkbox.isChecked()
        
        self.filtered_versions = []
        
        for version in self.versions:
            version_id = version["id"]
            version_type = version.get("type", "unknown")
            is_installed = version.get("installed", False)
            
            if show_only_installed and not is_installed:
                continue
            
            if filter_type != "all" and version_type != filter_type:
                continue
                
            if search_text and search_text not in version_id.lower():
                continue
            
            self.filtered_versions.append(version)
        
        def sort_key(v):
            type_order = {"release": 0, "snapshot": 1, "old_beta": 2, "old_alpha": 3}
            type_priority = type_order.get(v.get("type", "unknown"), 4)
            release_time = v.get("releaseTime", "")
            if release_time is None:
                release_time = ""
            return (type_priority, release_time)
        
        self.filtered_versions.sort(key=sort_key)
        self.filtered_versions.reverse()
        
        for version in self.filtered_versions:
            version_id = version["id"]
            version_type = version.get("type", "unknown")
            is_installed = version.get("installed", False)
            
            item = QListWidgetItem(version_id)
            
            if is_installed:
                item.setForeground(QColor("#88FF88"))
            elif version_type == "release":
                item.setForeground(QColor("#888"))
            elif version_type == "snapshot":
                item.setForeground(QColor("#aaa"))
            elif version_type == "old_beta":
                item.setForeground(QColor("#666"))
            elif version_type == "old_alpha":
                item.setForeground(QColor("#555"))
            
            item.setData(Qt.UserRole, version)
            
            self.versions_list.addItem(item)
        
        if self.versions_list.count() == 0:
            self.versions_list.addItem("Нет версий, соответствующих фильтрам")
            self.select_btn.setEnabled(False)
        else:
            self.select_btn.setEnabled(True)
        
        QTimer.singleShot(50, self.restore_selection)
    
    def restore_selection(self):
        if self.current_version:
            for i in range(self.versions_list.count()):
                item = self.versions_list.item(i)
                if item and item.text() == self.current_version:
                    self.versions_list.setCurrentItem(item)
                    break
    
    def get_selected_version(self):
        current_item = self.versions_list.currentItem()
        if current_item:
            version_data = current_item.data(Qt.UserRole)
            return version_data
        return None
    
    def delete_version(self, version_data):
        version_id = version_data.get("id")
        
        if not version_id:
            return
        
        msg_box = QMessageBox(self)
        msg_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
        msg_box.setWindowTitle("")
        msg_box.setText(f"Вы уверены, что хотите удалить версию {version_id}?\n\nЭто действие нельзя отменить.")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        
        yes_button = msg_box.button(QMessageBox.Yes)
        no_button = msg_box.button(QMessageBox.No)
        if yes_button:
            yes_button.setText("Да")
        if no_button:
            no_button.setText("Нет")
        
        reply = msg_box.exec()
        
        if reply != QMessageBox.Yes:
            return
        
        try:
            version_dir = self.parent.minecraft_dir / "versions" / version_id
            
            if version_dir.exists():
                shutil.rmtree(version_dir)
                print(f"Версия {version_id} удалена")
                
                version_data["installed"] = False
                
                if hasattr(self.parent, 'update_installed_versions'):
                    self.parent.update_installed_versions()
                
                self.status_label.setText(f"Версия {version_id} удалена")
                
                self.remove_delete_button()
                
                self.filter_versions()
                
                success_box = QMessageBox(self)
                success_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
                success_box.setWindowTitle("")
                success_box.setText(f"Версия {version_id} успешно удалена")
                success_box.setStandardButtons(QMessageBox.Ok)
                ok_button = success_box.button(QMessageBox.Ok)
                if ok_button:
                    ok_button.setText("OK")
                success_box.exec()
            else:
                error_box = QMessageBox(self)
                error_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
                error_box.setWindowTitle("")
                error_box.setText(f"Папка версии {version_id} не найдена")
                error_box.setStandardButtons(QMessageBox.Ok)
                ok_button = error_box.button(QMessageBox.Ok)
                if ok_button:
                    ok_button.setText("OK")
                error_box.exec()
                
        except Exception as e:
            error_box = QMessageBox(self)
            error_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            error_box.setWindowTitle("")
            error_box.setText(f"Не удалось удалить версию {version_id}:\n{str(e)}")
            error_box.setStandardButtons(QMessageBox.Ok)
            ok_button = error_box.button(QMessageBox.Ok)
            if ok_button:
                ok_button.setText("OK")
            error_box.exec()
            print(f"Ошибка удаления версии {version_id}: {e}")
    
    def accept(self):
        self.selected_version = self.get_selected_version()
        if self.selected_version:
            super().accept()
        else:
            warning_box = QMessageBox(self)
            warning_box.setWindowFlags(Qt.FramelessWindowHint | Qt.Dialog)
            warning_box.setWindowTitle("")
            warning_box.setText("Выберите версию")
            warning_box.setStandardButtons(QMessageBox.Ok)
            ok_button = warning_box.button(QMessageBox.Ok)
            if ok_button:
                ok_button.setText("OK")
            warning_box.exec()