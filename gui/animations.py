from PySide6.QtCore import QObject, QEvent, QPropertyAnimation, QEasingCurve, QRect, QTimer
from PySide6.QtWidgets import QGraphicsOpacityEffect

class PressBounceEffect(QObject):
    def __init__(self, dx=2, dy=2, parent=None):
        super().__init__(parent)
        self.dx = dx
        self.dy = dy
        
    def eventFilter(self, obj, event):
        if event.type() == QEvent.MouseButtonPress:
            if obj.isEnabled():
                g = obj.geometry()
                obj._orig_geo = g
                anim = QPropertyAnimation(obj, b"geometry", obj)
                anim.setDuration(50)
                anim.setStartValue(g)
                anim.setEndValue(g.adjusted(self.dx, self.dy, -self.dx, -self.dy))
                anim.setEasingCurve(QEasingCurve.InQuad)
                anim.start()
                obj._press_anim = anim
        elif event.type() == QEvent.MouseButtonRelease:
            if hasattr(obj, "_orig_geo"):
                anim = QPropertyAnimation(obj, b"geometry", obj)
                anim.setDuration(100)
                anim.setStartValue(obj.geometry())
                anim.setEndValue(obj._orig_geo)
                anim.setEasingCurve(QEasingCurve.OutQuad)
                anim.start()
                obj._release_anim = anim
        return super().eventFilter(obj, event)

class UIAnimations:
    @classmethod
    def apply_hover(cls, widget):
        """Эффекты при наведении реализованы через QSS (:hover), 
        чтобы не конфликтовать с QGraphicsOpacityEffect."""
        pass

    @classmethod
    def apply_press(cls, widget, dx=2, dy=2):
        """Легкое сжатие при нажатии"""
        filter_obj = PressBounceEffect(dx, dy, widget)
        widget.installEventFilter(filter_obj)

    @staticmethod
    def fade_in(widget, duration=400, delay=0):
        """Плавное появление элемента (Opacity)"""
        effect = QGraphicsOpacityEffect(widget)
        widget.setGraphicsEffect(effect)
        effect.setOpacity(0.0)
        
        anim = QPropertyAnimation(effect, b"opacity", widget)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        
        def on_finished():
            widget.setGraphicsEffect(None)
            
        anim.finished.connect(on_finished)
        
        if delay > 0:
            QTimer.singleShot(delay, anim.start)
        else:
            anim.start()
            
        if not hasattr(widget, '_fade_anims'):
            widget._fade_anims = []
        widget._fade_anims.append(anim)
        return anim

    @staticmethod
    def entrance_dialog(dialog, duration=300):
        """Плавное появление диалогового окна"""
        dialog.setWindowOpacity(0.0)
        anim = QPropertyAnimation(dialog, b"windowOpacity", dialog)
        anim.setDuration(duration)
        anim.setStartValue(0.0)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutQuad)
        anim.start()
        dialog._entrance_anim = anim
        return anim
