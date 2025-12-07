"""LED-style status indicator with subtle glow."""

from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, Property
from PySide6.QtGui import QPainter, QColor, QRadialGradient, QPen
from PySide6.QtWidgets import QWidget, QSizePolicy


class LEDIndicator(QWidget):
    """A subtle LED indicator with customizable color and glow."""

    # Preset colors
    COLOR_OFF = QColor(60, 60, 65)
    COLOR_GREEN = QColor(80, 200, 100)
    COLOR_RED = QColor(220, 80, 80)
    COLOR_YELLOW = QColor(220, 200, 80)
    COLOR_BLUE = QColor(80, 160, 220)

    def __init__(self, parent=None, color: QColor = None):
        super().__init__(parent)

        self._color = color or self.COLOR_OFF
        self._on = False
        self._intensity = 0.0

        # Animation for smooth on/off transitions
        self._animation = QPropertyAnimation(self, b"intensity")
        self._animation.setDuration(150)
        self._animation.setEasingCurve(QEasingCurve.OutCubic)

        self.setFixedSize(12, 12)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

    def set_color(self, color: QColor):
        """Set the LED color."""
        self._color = color
        self.update()

    def set_on(self, on: bool):
        """Turn the LED on or off with animation."""
        if self._on != on:
            self._on = on
            self._animation.stop()
            self._animation.setStartValue(self._intensity)
            self._animation.setEndValue(1.0 if on else 0.0)
            self._animation.start()

    def is_on(self) -> bool:
        return self._on

    # Qt Property for animation
    def get_intensity(self) -> float:
        return self._intensity

    def set_intensity(self, value: float):
        self._intensity = value
        self.update()

    intensity = Property(float, get_intensity, set_intensity)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        cx = w // 2
        cy = h // 2
        radius = min(w, h) // 2 - 1

        # Interpolate between off and on color
        if self._intensity > 0:
            r = int(self.COLOR_OFF.red() + (self._color.red() - self.COLOR_OFF.red()) * self._intensity)
            g = int(self.COLOR_OFF.green() + (self._color.green() - self.COLOR_OFF.green()) * self._intensity)
            b = int(self.COLOR_OFF.blue() + (self._color.blue() - self.COLOR_OFF.blue()) * self._intensity)
            current_color = QColor(r, g, b)
        else:
            current_color = self.COLOR_OFF

        # Subtle outer glow when on
        if self._intensity > 0.3:
            glow_opacity = (self._intensity - 0.3) * 0.3
            glow = QRadialGradient(cx, cy, radius * 1.8)
            glow_color = QColor(current_color)
            glow_color.setAlphaF(glow_opacity)
            glow.setColorAt(0.3, glow_color)
            glow.setColorAt(1.0, QColor(current_color.red(), current_color.green(), current_color.blue(), 0))
            painter.setBrush(glow)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - radius * 1.5, cy - radius * 1.5,
                               radius * 3, radius * 3)

        # LED body gradient (3D effect)
        led_gradient = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 1.2)
        led_gradient.setColorAt(0.0, current_color.lighter(140))
        led_gradient.setColorAt(0.5, current_color)
        led_gradient.setColorAt(1.0, current_color.darker(140))

        # Border
        border_color = QColor(30, 30, 35)
        painter.setPen(QPen(border_color, 1))
        painter.setBrush(led_gradient)
        painter.drawEllipse(cx - radius, cy - radius, radius * 2, radius * 2)

        # Highlight spot
        if self._intensity > 0.2:
            highlight = QRadialGradient(cx - radius * 0.3, cy - radius * 0.3, radius * 0.5)
            highlight.setColorAt(0.0, QColor(255, 255, 255, int(60 * self._intensity)))
            highlight.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(highlight)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(cx - radius * 0.6, cy - radius * 0.6,
                               radius * 0.8, radius * 0.8)
