from PySide6.QtWidgets import QWidget, QGraphicsOpacityEffect
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QTimer
from PySide6.QtGui import QPainter, QPixmap, QColor
from pathlib import Path
from core.config import get_asset_path

class BackgroundWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_StyledBackground, True)
        self.custom_background = None
        self.overlay_opacity = 70  # Увеличил затемнение для контраста
        self.setStyleSheet("""
            BackgroundWidget {
                margin: 0px;
                padding: 0px;
                border: 2px solid #444;
                border-radius: 15px;
            }
        """)
        self._fade_anim = None

    def paintEvent(self, event):
        painter = QPainter(self)
        
        # пользовательский фон если есть
        if self.custom_background and Path(self.custom_background).exists():
            pixmap = QPixmap(self.custom_background)
            if not pixmap.isNull():
                # Масштаб под размер виджета
                scaled_pixmap = pixmap.scaled(self.width(), self.height(), 
                                             Qt.KeepAspectRatioByExpanding, 
                                             Qt.SmoothTransformation)
                
                # Центрируем изображение
                x = (self.width() - scaled_pixmap.width()) // 2
                y = (self.height() - scaled_pixmap.height()) // 2
                painter.drawPixmap(x, y, scaled_pixmap)
        else:
            # Используем стандартный фон
            pixmap = QPixmap(get_asset_path("textures/background.png"))
            if not pixmap.isNull():
                painter.drawPixmap(0, 0, self.width(), self.height(), pixmap)
        
        # Темный слой:
        if self.overlay_opacity > 0:
            painter.fillRect(0, 0, self.width(), self.height(), 
                            QColor(0, 0, 0, int(self.overlay_opacity * 2.55)))
    
    def set_background_image(self, image_path):
        """Устанавливает пользовательское изображение для фона с плавной анимацией"""
        if self.custom_background == image_path:
            return
            
        # Плавная анимация смены фона
        effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(effect)
        
        anim_out = QPropertyAnimation(effect, b"opacity")
        anim_out.setDuration(300)
        anim_out.setStartValue(1.0)
        anim_out.setEndValue(0.4)
        
        anim_in = QPropertyAnimation(effect, b"opacity")
        anim_in.setDuration(500)
        anim_in.setStartValue(0.4)
        anim_in.setEndValue(1.0)
        
        def on_out_finished():
            self.custom_background = image_path
            self.update()
            anim_in.start()
            self._fade_anim = anim_in
            
        anim_out.finished.connect(on_out_finished)
        anim_out.start()
        self._fade_anim = anim_out
    
    def set_overlay_opacity(self, opacity):
        """Устанавливает прозрачность затемнения (0-100) с анимацией"""
        if hasattr(self, "_opacity_anim"):
            self._opacity_anim.stop()
            
        target_opacity = max(0, min(100, opacity))
        
        # Мы не можем анимировать overlay_opacity напрямую через QPropertyAnimation без pyqtProperty
        # Поэтому используем QTimer для плавности
        self._target_opacity = target_opacity
        self._opacity_timer = QTimer()
        self._opacity_timer.timeout.connect(self._animate_opacity_step)
        self._opacity_timer.start(16) # ~60 FPS

    def _animate_opacity_step(self):
        diff = self._target_opacity - self.overlay_opacity
        if abs(diff) < 1:
            self.overlay_opacity = self._target_opacity
            self._opacity_timer.stop()
        else:
            self.overlay_opacity += diff * 0.1
        self.update()
