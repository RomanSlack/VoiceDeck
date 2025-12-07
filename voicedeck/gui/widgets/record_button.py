"""Custom animated record button with metallic 3D appearance."""

from PySide6.QtCore import (
    Qt, QPropertyAnimation, QEasingCurve, Property, QTimer, Signal
)
from PySide6.QtGui import (
    QPainter, QColor, QLinearGradient, QRadialGradient,
    QPen, QBrush, QPainterPath
)
from PySide6.QtWidgets import QAbstractButton, QSizePolicy


class RecordButton(QAbstractButton):
    """A sleek metallic record button with animated states."""

    # Custom signal for recording state
    recordingToggled = Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)

        self._recording = False
        self._hover = False
        self._pressed = False
        self._pulse_value = 0.0
        self._glow_opacity = 0.0

        # Animation for recording pulse
        self._pulse_animation = QPropertyAnimation(self, b"pulse_value")
        self._pulse_animation.setDuration(1200)
        self._pulse_animation.setStartValue(0.0)
        self._pulse_animation.setEndValue(1.0)
        self._pulse_animation.setEasingCurve(QEasingCurve.InOutSine)
        self._pulse_animation.setLoopCount(-1)  # Infinite loop

        # Animation for glow on hover/press
        self._glow_animation = QPropertyAnimation(self, b"glow_opacity")
        self._glow_animation.setDuration(150)
        self._glow_animation.setEasingCurve(QEasingCurve.OutCubic)

        # Size policy
        self.setMinimumSize(180, 50)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        # Connect click to toggle
        self.clicked.connect(self._on_clicked)

    def _on_clicked(self):
        self.set_recording(not self._recording)
        self.recordingToggled.emit(self._recording)

    def set_recording(self, recording: bool):
        """Set the recording state."""
        if self._recording != recording:
            self._recording = recording
            if recording:
                self._pulse_animation.start()
            else:
                self._pulse_animation.stop()
                self._pulse_value = 0.0
            self.update()

    def is_recording(self) -> bool:
        return self._recording

    # Qt Property for pulse animation
    def get_pulse_value(self) -> float:
        return self._pulse_value

    def set_pulse_value(self, value: float):
        self._pulse_value = value
        self.update()

    pulse_value = Property(float, get_pulse_value, set_pulse_value)

    # Qt Property for glow animation
    def get_glow_opacity(self) -> float:
        return self._glow_opacity

    def set_glow_opacity(self, value: float):
        self._glow_opacity = value
        self.update()

    glow_opacity = Property(float, get_glow_opacity, set_glow_opacity)

    def enterEvent(self, event):
        self._hover = True
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_opacity)
        self._glow_animation.setEndValue(0.3)
        self._glow_animation.start()
        super().enterEvent(event)

    def leaveEvent(self, event):
        self._hover = False
        self._glow_animation.stop()
        self._glow_animation.setStartValue(self._glow_opacity)
        self._glow_animation.setEndValue(0.0)
        self._glow_animation.start()
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        self._pressed = True
        self.update()
        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        self._pressed = False
        self.update()
        super().mouseReleaseEvent(event)

    def sizeHint(self):
        from PySide6.QtCore import QSize
        return QSize(180, 50)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()
        margin = 2

        # Colors based on state
        if self._recording:
            base_color = QColor(140, 45, 55)  # Deep red
            highlight_color = QColor(180, 60, 70)
            shadow_color = QColor(90, 30, 40)
            text_color = QColor(255, 220, 220)
            glow_color = QColor(255, 80, 80)
        else:
            base_color = QColor(45, 85, 45)  # Deep green
            highlight_color = QColor(60, 110, 60)
            shadow_color = QColor(30, 60, 30)
            text_color = QColor(220, 255, 220)
            glow_color = QColor(100, 200, 100)

        # Outer shadow/bevel
        outer_rect = QPainterPath()
        outer_rect.addRoundedRect(margin, margin, w - margin * 2, h - margin * 2, 8, 8)

        # Draw subtle outer glow when hovering or recording
        if self._glow_opacity > 0 or (self._recording and self._pulse_value > 0):
            glow_strength = self._glow_opacity
            if self._recording:
                # Subtle pulse glow
                pulse_glow = 0.15 + (self._pulse_value * 0.15)
                glow_strength = max(glow_strength, pulse_glow)

            glow_color.setAlphaF(glow_strength * 0.5)
            painter.setPen(QPen(glow_color, 3))
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawRoundedRect(margin - 1, margin - 1, w - margin * 2 + 2, h - margin * 2 + 2, 9, 9)

        # Main button gradient (metallic effect)
        button_gradient = QLinearGradient(0, margin, 0, h - margin)

        if self._pressed:
            # Pressed state - darker, inverted gradient
            button_gradient.setColorAt(0.0, shadow_color)
            button_gradient.setColorAt(0.5, base_color)
            button_gradient.setColorAt(1.0, highlight_color.darker(110))
        else:
            # Normal state - 3D bevel effect
            button_gradient.setColorAt(0.0, highlight_color)
            button_gradient.setColorAt(0.15, base_color)
            button_gradient.setColorAt(0.85, base_color.darker(105))
            button_gradient.setColorAt(1.0, shadow_color)

        painter.setPen(QPen(shadow_color.darker(130), 1))
        painter.setBrush(QBrush(button_gradient))
        painter.drawRoundedRect(margin, margin, w - margin * 2, h - margin * 2, 8, 8)

        # Inner highlight line (subtle top edge shine)
        if not self._pressed:
            highlight_pen = QPen(QColor(255, 255, 255, 30), 1)
            painter.setPen(highlight_pen)
            painter.drawLine(margin + 10, margin + 2, w - margin - 10, margin + 2)

        # Draw text
        text = "Stop Recording" if self._recording else "Start Recording"
        painter.setPen(text_color)
        font = painter.font()
        font.setPixelSize(14)
        font.setWeight(font.Weight.Medium)
        painter.setFont(font)

        # Offset text slightly when pressed
        text_offset = 1 if self._pressed else 0
        text_rect = self.rect().adjusted(0, text_offset, 0, text_offset)
        painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

        # Recording indicator dot
        dot_x = margin + 18
        dot_y = h // 2 + text_offset
        dot_radius = 5

        if self._recording:
            # Animated red dot
            dot_opacity = 0.7 + (self._pulse_value * 0.3)
            dot_color = QColor(255, 100, 100)
            dot_color.setAlphaF(dot_opacity)

            # Subtle glow behind dot
            glow = QRadialGradient(dot_x, dot_y, dot_radius * 2)
            glow.setColorAt(0, QColor(255, 100, 100, 60))
            glow.setColorAt(1, QColor(255, 100, 100, 0))
            painter.setBrush(QBrush(glow))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_x - dot_radius * 2, dot_y - dot_radius * 2,
                              dot_radius * 4, dot_radius * 4)

            painter.setBrush(dot_color)
            painter.drawEllipse(dot_x - dot_radius, dot_y - dot_radius,
                              dot_radius * 2, dot_radius * 2)
        else:
            # Subtle green dot
            dot_color = QColor(120, 180, 120, 180)
            painter.setBrush(dot_color)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(dot_x - dot_radius, dot_y - dot_radius,
                              dot_radius * 2, dot_radius * 2)
