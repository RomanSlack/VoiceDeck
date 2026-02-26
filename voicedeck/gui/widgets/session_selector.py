"""Session pill selector for hot mic mode."""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from PySide6.QtWidgets import (
    QWidget,
    QHBoxLayout,
    QPushButton,
    QSizePolicy,
)


# Colors matching claude-grid PANE_COLORS order
SESSION_COLORS = [
    QColor(205, 0, 0),       # red (colour1)
    QColor(0, 0, 205),       # blue (colour4)
    QColor(0, 205, 0),       # green (colour2)
    QColor(205, 0, 205),     # magenta (colour5)
    QColor(205, 205, 0),     # yellow (colour3)
    QColor(0, 205, 205),     # cyan (colour6)
    QColor(255, 135, 0),     # orange (colour208)
    QColor(135, 95, 255),    # purple (colour99)
    QColor(0, 175, 135),     # teal (colour37)
    QColor(215, 95, 0),      # dark orange (colour166)
    QColor(175, 0, 135),     # pink (colour126)
    QColor(0, 135, 0),       # forest green (colour28)
    QColor(95, 95, 215),     # slate blue (colour62)
]


class SessionSelector(QWidget):
    """Displays colored pills for each claude-grid session.

    Clicking a pill manually targets that session. The active session
    gets a highlighted border.
    """

    session_clicked = Signal(str)  # emits session name

    def __init__(self, parent=None):
        super().__init__(parent)

        self._layout = QHBoxLayout(self)
        self._layout.setContentsMargins(0, 0, 0, 0)
        self._layout.setSpacing(6)
        self._layout.addStretch()

        self._pills: dict[str, QPushButton] = {}
        self._active_session: str = ""

    def set_sessions(self, session_names: list[str]) -> None:
        """Update the displayed sessions. Preserves active selection if still valid."""
        # Clear existing pills
        for pill in self._pills.values():
            self._layout.removeWidget(pill)
            pill.deleteLater()
        self._pills.clear()

        # Remove the trailing stretch
        while self._layout.count():
            item = self._layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # Create new pills
        for i, name in enumerate(session_names):
            color = SESSION_COLORS[i % len(SESSION_COLORS)]
            pill = self._create_pill(name, color)
            self._layout.addWidget(pill)
            self._pills[name] = pill

        self._layout.addStretch()

        # Restore active if still present, otherwise clear
        if self._active_session not in self._pills:
            self._active_session = ""

        self._update_pill_styles()

    def set_active(self, session_name: str) -> None:
        """Set the active (highlighted) session."""
        self._active_session = session_name
        self._update_pill_styles()

    def get_active(self) -> str:
        return self._active_session

    def _create_pill(self, name: str, color: QColor) -> QPushButton:
        pill = QPushButton(name)
        pill.setCursor(Qt.CursorShape.PointingHandCursor)
        pill.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Fixed)
        pill.setFixedHeight(26)
        pill.setProperty("session_name", name)
        pill.setProperty("pill_color", color)
        pill.clicked.connect(lambda checked=False, n=name: self._on_pill_clicked(n))
        return pill

    def _on_pill_clicked(self, name: str) -> None:
        self._active_session = name
        self._update_pill_styles()
        self.session_clicked.emit(name)

    def _update_pill_styles(self) -> None:
        for name, pill in self._pills.items():
            color: QColor = pill.property("pill_color")
            r, g, b = color.red(), color.green(), color.blue()
            is_active = (name == self._active_session)

            if is_active:
                pill.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba({r}, {g}, {b}, 60);
                        color: rgb({min(r+80, 255)}, {min(g+80, 255)}, {min(b+80, 255)});
                        border: 2px solid rgb({r}, {g}, {b});
                        border-radius: 13px;
                        padding: 2px 12px;
                        font-size: 11px;
                        font-weight: 600;
                        min-width: 0;
                    }}
                """)
            else:
                pill.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgba({r}, {g}, {b}, 30);
                        color: rgba({r}, {g}, {b}, 180);
                        border: 1px solid rgba({r}, {g}, {b}, 80);
                        border-radius: 13px;
                        padding: 2px 12px;
                        font-size: 11px;
                        font-weight: 500;
                        min-width: 0;
                    }}
                    QPushButton:hover {{
                        background-color: rgba({r}, {g}, {b}, 50);
                        border-color: rgba({r}, {g}, {b}, 140);
                    }}
                """)
