"""Dark theme styles for VoiceDeck GUI."""

DARK_STYLESHEET = """
QMainWindow {
    background-color: #1e1e1e;
}

QWidget {
    background-color: #1e1e1e;
    color: #e0e0e0;
    font-family: "Ubuntu", "Cantarell", "Segoe UI", sans-serif;
    font-size: 13px;
}

QDialog {
    background-color: #1e1e1e;
}

QLabel {
    color: #e0e0e0;
    background-color: transparent;
}

QLabel#statusLabel {
    color: #a0a0a0;
    font-size: 12px;
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
    border-radius: 4px;
    padding: 6px 30px 6px 10px;
    min-width: 150px;
    min-height: 20px;
    color: #e0e0e0;
}

QComboBox:hover {
    border-color: #505050;
}

QComboBox:focus {
    border-color: #4a9eff;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: top right;
    width: 24px;
    border-left: 1px solid #404040;
    border-top-right-radius: 4px;
    border-bottom-right-radius: 4px;
    background-color: #363636;
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #a0a0a0;
}

QComboBox::down-arrow:hover {
    border-top-color: #e0e0e0;
}

QComboBox QAbstractItemView {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    selection-background-color: #404040;
    color: #e0e0e0;
    padding: 4px;
}

QComboBox QAbstractItemView::item {
    padding: 6px 10px;
    min-height: 20px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #3a3a3a;
}

QPushButton {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 8px 16px;
    min-width: 70px;
    min-height: 20px;
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

QPushButton#settingsButton {
    padding: 6px 12px;
    min-width: 60px;
}

QPushButton#recordButton {
    background-color: #2d5a2d;
    border-color: #3d7a3d;
    font-size: 15px;
    padding: 12px 24px;
    min-width: 160px;
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
    padding: 6px 14px;
    min-width: 50px;
}

QTextEdit {
    background-color: #252525;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 10px;
    color: #e0e0e0;
    font-size: 13px;
}

QTextEdit:focus {
    border-color: #4a9eff;
}

QLineEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
    color: #e0e0e0;
}

QLineEdit:focus {
    border-color: #4a9eff;
}

QLineEdit:disabled {
    background-color: #252525;
    color: #606060;
}

QSpinBox {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 4px 8px;
    min-height: 20px;
    color: #e0e0e0;
}

QSpinBox:focus {
    border-color: #4a9eff;
}

QSpinBox::up-button, QSpinBox::down-button {
    background-color: #363636;
    border: none;
    width: 20px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background-color: #404040;
}

QSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #a0a0a0;
}

QSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #a0a0a0;
}

QCheckBox {
    spacing: 8px;
    color: #e0e0e0;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border: 1px solid #404040;
    border-radius: 3px;
    background-color: #2d2d2d;
}

QCheckBox::indicator:checked {
    background-color: #4a9eff;
    border-color: #4a9eff;
}

QCheckBox::indicator:hover {
    border-color: #505050;
}

QTabWidget::pane {
    border: 1px solid #404040;
    border-radius: 4px;
    background-color: #1e1e1e;
    top: -1px;
}

QTabBar::tab {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-bottom: none;
    border-top-left-radius: 4px;
    border-top-right-radius: 4px;
    padding: 8px 16px;
    margin-right: 2px;
    color: #a0a0a0;
}

QTabBar::tab:selected {
    background-color: #1e1e1e;
    color: #e0e0e0;
    border-bottom: 1px solid #1e1e1e;
}

QTabBar::tab:hover:!selected {
    background-color: #363636;
    color: #e0e0e0;
}

QGroupBox {
    border: 1px solid #404040;
    border-radius: 4px;
    margin-top: 12px;
    padding-top: 8px;
    color: #e0e0e0;
    font-weight: 500;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 10px;
    padding: 0 6px;
    background-color: #1e1e1e;
}

QKeySequenceEdit {
    background-color: #2d2d2d;
    border: 1px solid #404040;
    border-radius: 4px;
    padding: 6px 10px;
    min-height: 20px;
    color: #e0e0e0;
}

QKeySequenceEdit:focus {
    border-color: #4a9eff;
}

QScrollBar:vertical {
    background-color: #252525;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background-color: #404040;
    min-height: 30px;
    border-radius: 5px;
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

QScrollBar:horizontal {
    background-color: #252525;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background-color: #404040;
    min-width: 30px;
    border-radius: 5px;
}

QScrollBar::handle:horizontal:hover {
    background-color: #505050;
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}
"""
