"""Dark theme styles for VoiceDeck GUI."""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Segoe UI", "Ubuntu", "Cantarell", sans-serif;
    font-size: 14px;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel#statusLabel {
    color: #a0a0a0;
    font-size: 13px;
    padding: 4px;
}

QLabel#statusLabel[recording="true"] {
    color: #ff6b6b;
}

QLabel#statusLabel[transcribing="true"] {
    color: #4ecdc4;
}

QComboBox {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 8px 12px;
    min-width: 200px;
    color: #e0e0e0;
}

QComboBox:hover {
    border-color: #505050;
}

QComboBox:focus {
    border-color: #4a9eff;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox::down-arrow {
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 6px solid #808080;
    margin-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    selection-background-color: #404040;
    color: #e0e0e0;
}

QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 10px 20px;
    color: #e0e0e0;
    font-weight: 500;
}

QPushButton:hover {
    background-color: #383838;
    border-color: #505050;
}

QPushButton:pressed {
    background-color: #252525;
}

QPushButton:disabled {
    background-color: #252525;
    color: #606060;
    border-color: #353535;
}

QPushButton#recordButton {
    background-color: #2d5a2d;
    border-color: #3d7a3d;
    font-size: 16px;
    padding: 14px 28px;
    min-width: 180px;
}

QPushButton#recordButton:hover {
    background-color: #3d6a3d;
}

QPushButton#recordButton:pressed {
    background-color: #1d4a1d;
}

QPushButton#recordButton[recording="true"] {
    background-color: #8b2635;
    border-color: #ab3645;
}

QPushButton#recordButton[recording="true"]:hover {
    background-color: #9b3645;
}

QPushButton#copyButton, QPushButton#clearButton {
    padding: 8px 16px;
    font-size: 13px;
}

QTextEdit {
    background-color: #252525;
    border: 1px solid #404040;
    border-radius: 6px;
    padding: 12px;
    color: #e0e0e0;
    font-size: 14px;
    line-height: 1.5;
}

QTextEdit:focus {
    border-color: #4a9eff;
}

QScrollBar:vertical {
    background-color: #252525;
    width: 12px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    min-height: 30px;
    border-radius: 6px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background-color: #505050;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}
"""
