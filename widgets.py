from PyQt5.QtCore import Qt, QPropertyAnimation, QEasingCurve, pyqtProperty
from PyQt5.QtGui import QColor, QLinearGradient, QPainter, QPen
from PyQt5.QtWidgets import QWidget


class GlowLine(QWidget):
    def __init__(self, color="#00ff88", parent=None):
        super().__init__(parent)
        self.color = QColor(color)
        self.setFixedHeight(2)

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        g = QLinearGradient(0, 0, self.width(), 0)
        c = self.color
        g.setColorAt(0,   QColor(c.red(), c.green(), c.blue(), 0))
        g.setColorAt(0.3, c)
        g.setColorAt(0.7, c)
        g.setColorAt(1,   QColor(c.red(), c.green(), c.blue(), 0))
        p.fillRect(self.rect(), g)


class StatusDot(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(10, 10)
        self._color = QColor("#00ff88")
        self._alpha = 255

        self._anim = QPropertyAnimation(self, b"dot_alpha")
        self._anim.setDuration(1200)
        self._anim.setStartValue(60)
        self._anim.setEndValue(255)
        self._anim.setEasingCurve(QEasingCurve.InOutSine)
        self._anim.setLoopCount(-1)
        self._anim.start()

    def get_alpha(self):
        return self._alpha

    def set_alpha(self, v):
        self._alpha = v
        self.update()

    dot_alpha = pyqtProperty(int, get_alpha, set_alpha)

    def set_color(self, hex_color):
        self._color = QColor(hex_color)
        self.update()

    def paintEvent(self, _):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        c    = self._color
        glow = QColor(c.red(), c.green(), c.blue(), self._alpha // 3)
        p.setPen(Qt.NoPen)
        p.setBrush(glow)
        p.drawEllipse(0, 0, 10, 10)
        p.setBrush(QColor(c.red(), c.green(), c.blue(), self._alpha))
        p.drawEllipse(2, 2, 6, 6)
