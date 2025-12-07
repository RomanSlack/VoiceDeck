"""VU-style audio level meter with smooth animation."""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QTimer
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QPen, QBrush
)
from PySide6.QtWidgets import QWidget, QSizePolicy


class LevelMeter(QWidget):
    """A sleek VU-style level meter with smooth falloff."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self._level = 0.0  # 0.0 to 1.0
        self._peak_level = 0.0
        self._display_level = 0.0

        # Smooth animation for level changes
        self._level_animation = QPropertyAnimation(self, b"display_level")
        self._level_animation.setDuration(80)
        self._level_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Peak hold timer
        self._peak_timer = QTimer(self)
        self._peak_timer.timeout.connect(self._decay_peak)
        self._peak_timer.setInterval(50)

        # Falloff timer for smooth decay
        self._falloff_timer = QTimer(self)
        self._falloff_timer.timeout.connect(self._decay_level)
        self._falloff_timer.setInterval(30)

        self.setMinimumSize(200, 24)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)

    def set_level(self, level: float):
        """Set the current level (0.0 to 1.0)."""
        level = max(0.0, min(1.0, level))

        if level > self._display_level:
            # Rising - animate quickly
            self._level_animation.stop()
            self._level_animation.setStartValue(self._display_level)
            self._level_animation.setEndValue(level)
            self._level_animation.setDuration(50)
            self._level_animation.start()

            # Update peak
            if level > self._peak_level:
                self._peak_level = level

            # Start falloff timer
            if not self._falloff_timer.isActive():
                self._falloff_timer.start()
            if not self._peak_timer.isActive():
                self._peak_timer.start()

        self._level = level

    def _decay_level(self):
        """Smooth decay when input level drops."""
        if self._display_level > self._level:
            new_level = self._display_level - 0.03
            if new_level <= self._level:
                self._display_level = self._level
                if self._level == 0:
                    self._falloff_timer.stop()
            else:
                self._display_level = new_level
            self.update()

    def _decay_peak(self):
        """Decay the peak indicator."""
        if self._peak_level > 0:
            self._peak_level = max(0, self._peak_level - 0.015)
            self.update()
        else:
            self._peak_timer.stop()

    def reset(self):
        """Reset the meter to zero."""
        self._level = 0.0
        self._peak_level = 0.0
        self._display_level = 0.0
        self._falloff_timer.stop()
        self._peak_timer.stop()
        self.update()

    # Qt Property for animation
    def get_display_level(self) -> float:
        return self._display_level

    def set_display_level(self, value: float):
        self._display_level = value
        self.update()

    display_level = Property(float, get_display_level, set_display_level)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 2
        bar_height = h - margin * 2
        bar_width = w - margin * 2

        # Background - recessed look
        bg_gradient = QLinearGradient(0, margin, 0, h - margin)
        bg_gradient.setColorAt(0.0, QColor(20, 20, 22))
        bg_gradient.setColorAt(0.3, QColor(28, 28, 32))
        bg_gradient.setColorAt(1.0, QColor(35, 35, 40))

        painter.setPen(QPen(QColor(15, 15, 18), 1))
        painter.setBrush(QBrush(bg_gradient))
        painter.drawRoundedRect(margin, margin, bar_width, bar_height, 4, 4)

        # Inner shadow effect
        painter.setPen(QPen(QColor(0, 0, 0, 40), 1))
        painter.drawLine(margin + 2, margin + 1, margin + bar_width - 2, margin + 1)

        # Calculate level width
        level_width = int(self._display_level * (bar_width - 4))

        if level_width > 2:
            # Level gradient - green to yellow to red
            level_gradient = QLinearGradient(margin + 2, 0, margin + bar_width - 2, 0)

            # Green zone (0-60%)
            level_gradient.setColorAt(0.0, QColor(60, 180, 80))
            level_gradient.setColorAt(0.4, QColor(80, 190, 70))

            # Yellow zone (60-80%)
            level_gradient.setColorAt(0.6, QColor(200, 200, 60))
            level_gradient.setColorAt(0.75, QColor(230, 180, 50))

            # Red zone (80-100%)
            level_gradient.setColorAt(0.85, QColor(230, 120, 50))
            level_gradient.setColorAt(1.0, QColor(220, 70, 60))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(QBrush(level_gradient))
            painter.drawRoundedRect(margin + 2, margin + 2,
                                   level_width, bar_height - 4, 2, 2)

            # Subtle shine on top of level bar
            shine_gradient = QLinearGradient(0, margin + 2, 0, margin + bar_height // 2)
            shine_gradient.setColorAt(0.0, QColor(255, 255, 255, 40))
            shine_gradient.setColorAt(1.0, QColor(255, 255, 255, 0))
            painter.setBrush(QBrush(shine_gradient))
            painter.drawRoundedRect(margin + 2, margin + 2,
                                   level_width, (bar_height - 4) // 2, 2, 2)

        # Peak indicator
        if self._peak_level > 0.02:
            peak_x = margin + 2 + int(self._peak_level * (bar_width - 6))

            # Peak line color based on level
            if self._peak_level > 0.85:
                peak_color = QColor(255, 80, 80, 200)
            elif self._peak_level > 0.6:
                peak_color = QColor(255, 220, 80, 200)
            else:
                peak_color = QColor(120, 220, 120, 200)

            painter.setPen(QPen(peak_color, 2))
            painter.drawLine(peak_x, margin + 3, peak_x, h - margin - 3)

        # Segment lines (subtle tick marks)
        painter.setPen(QPen(QColor(0, 0, 0, 60), 1))
        for i in range(1, 10):
            x = margin + 2 + int((i / 10) * (bar_width - 4))
            painter.drawLine(x, margin + 2, x, margin + 5)
            painter.drawLine(x, h - margin - 5, x, h - margin - 2)
