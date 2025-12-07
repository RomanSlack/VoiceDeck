"""Sleek dark metallic theme for VoiceDeck GUI."""

DARK_STYLESHEET = """
/* ============================================
   VOICEDECK - Sleek Dark Metallic Theme
   ============================================ */

/* Main Window - Brushed metal dark background */
QMainWindow {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:0.3 #1e1e22,
        stop:0.7 #1c1c20,
        stop:1 #18181c
    );
}

QWidget {
    color: #d0d0d5;
    font-family: "Ubuntu", "Cantarell", "Segoe UI", sans-serif;
    font-size: 13px;
}

QWidget#centralWidget {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:0.3 #1e1e22,
        stop:0.7 #1c1c20,
        stop:1 #18181c
    );
}

/* Dialog windows */
QDialog {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:0.5 #1e1e22,
        stop:1 #18181c
    );
}

/* ============================================
   Labels
   ============================================ */

QLabel {
    color: #c5c5ca;
    background-color: transparent;
    padding: 2px;
}

QLabel#statusLabel {
    color: #808088;
    font-size: 12px;
    padding: 6px 12px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #151518,
        stop:1 #1a1a1e
    );
    border: 1px solid #2a2a30;
    border-radius: 4px;
}

QLabel#statusLabel[recording="true"] {
    color: #e87070;
    border-color: #4a2020;
}

QLabel#statusLabel[transcribing="true"] {
    color: #60c0b8;
    border-color: #204a48;
}

QLabel#sectionLabel {
    color: #909098;
    font-size: 11px;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 4px 0;
}

/* ============================================
   ComboBox - Metallic dropdown
   ============================================ */

QComboBox {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #2e2e34,
        stop:0.1 #28282e,
        stop:0.9 #242428,
        stop:1 #1e1e22
    );
    border: 1px solid #3a3a42;
    border-radius: 5px;
    padding: 8px 32px 8px 12px;
    min-width: 150px;
    min-height: 22px;
    color: #d0d0d5;
}

QComboBox:hover {
    border-color: #4a4a55;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #343438,
        stop:0.1 #2e2e34,
        stop:0.9 #28282e,
        stop:1 #222226
    );
}

QComboBox:focus {
    border-color: #5080a0;
}

QComboBox:disabled {
    background: #1e1e22;
    color: #505058;
    border-color: #2a2a30;
}

QComboBox::drop-down {
    subcontrol-origin: padding;
    subcontrol-position: center right;
    width: 28px;
    border-left: 1px solid #3a3a42;
    border-top-right-radius: 5px;
    border-bottom-right-radius: 5px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #38383e,
        stop:1 #2a2a30
    );
}

QComboBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid #808088;
}

QComboBox::down-arrow:hover {
    border-top-color: #a0a0a8;
}

QComboBox QAbstractItemView {
    background-color: #222228;
    border: 1px solid #3a3a42;
    border-radius: 4px;
    selection-background-color: #3a3a45;
    color: #d0d0d5;
    padding: 4px;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 8px 12px;
    min-height: 22px;
    border-radius: 3px;
}

QComboBox QAbstractItemView::item:hover {
    background-color: #32323a;
}

QComboBox QAbstractItemView::item:selected {
    background-color: #3a3a45;
}

/* ============================================
   Buttons - Metallic beveled
   ============================================ */

QPushButton {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a3a42,
        stop:0.1 #32323a,
        stop:0.9 #2a2a32,
        stop:1 #242428
    );
    border: 1px solid #444450;
    border-bottom-color: #1e1e22;
    border-radius: 5px;
    padding: 8px 18px;
    min-width: 70px;
    min-height: 20px;
    color: #d0d0d5;
    font-weight: 500;
}

QPushButton:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #424248,
        stop:0.1 #3a3a42,
        stop:0.9 #32323a,
        stop:1 #2a2a30
    );
    border-color: #505060;
}

QPushButton:pressed {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #28282e,
        stop:0.5 #2a2a32,
        stop:1 #32323a
    );
    border-color: #3a3a42;
    padding-top: 9px;
    padding-bottom: 7px;
}

QPushButton:disabled {
    background: #222228;
    color: #505058;
    border-color: #2a2a30;
}

QPushButton#settingsButton {
    padding: 7px 14px;
    min-width: 60px;
    font-size: 12px;
}

QPushButton#copyButton, QPushButton#clearButton {
    padding: 7px 16px;
    min-width: 55px;
}

/* ============================================
   TextEdit - Recessed screen look
   ============================================ */

QTextEdit {
    background-color: #18181c;
    border: 1px solid #2a2a32;
    border-top-color: #1a1a1e;
    border-radius: 5px;
    padding: 12px;
    color: #d5d5da;
    font-size: 13px;
    selection-background-color: #3a5060;
    selection-color: #ffffff;
}

QTextEdit:focus {
    border-color: #405060;
}

/* ============================================
   LineEdit - Input fields
   ============================================ */

QLineEdit {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:1 #222228
    );
    border: 1px solid #3a3a42;
    border-radius: 5px;
    padding: 8px 12px;
    min-height: 20px;
    color: #d0d0d5;
    selection-background-color: #3a5060;
}

QLineEdit:focus {
    border-color: #5080a0;
}

QLineEdit:disabled {
    background: #1a1a1e;
    color: #505058;
    border-color: #2a2a30;
}

/* ============================================
   SpinBox
   ============================================ */

QSpinBox {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:1 #222228
    );
    border: 1px solid #3a3a42;
    border-radius: 5px;
    padding: 6px 10px;
    min-height: 20px;
    color: #d0d0d5;
}

QSpinBox:focus {
    border-color: #5080a0;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #38383e,
        stop:1 #2a2a30
    );
    border: none;
    width: 22px;
    border-radius: 2px;
}

QSpinBox::up-button:hover, QSpinBox::down-button:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #424248,
        stop:1 #34343a
    );
}

QSpinBox::up-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-bottom: 4px solid #808088;
}

QSpinBox::down-arrow {
    width: 0;
    height: 0;
    border-left: 4px solid transparent;
    border-right: 4px solid transparent;
    border-top: 4px solid #808088;
}

/* ============================================
   CheckBox
   ============================================ */

QCheckBox {
    spacing: 10px;
    color: #c5c5ca;
}

QCheckBox::indicator {
    width: 18px;
    height: 18px;
    border: 1px solid #3a3a42;
    border-radius: 4px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:1 #222228
    );
}

QCheckBox::indicator:checked {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #4080a0,
        stop:1 #306080
    );
    border-color: #5090b0;
}

QCheckBox::indicator:hover {
    border-color: #505060;
}

/* ============================================
   TabWidget
   ============================================ */

QTabWidget::pane {
    border: 1px solid #2a2a32;
    border-radius: 5px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1c1c20,
        stop:1 #1a1a1e
    );
    top: -1px;
    padding: 10px;
}

QTabBar::tab {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #2a2a30,
        stop:1 #222228
    );
    border: 1px solid #2a2a32;
    border-bottom: none;
    border-top-left-radius: 5px;
    border-top-right-radius: 5px;
    padding: 10px 20px;
    margin-right: 2px;
    color: #808088;
    font-weight: 500;
}

QTabBar::tab:selected {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e22,
        stop:1 #1c1c20
    );
    color: #d0d0d5;
    border-bottom: 1px solid #1c1c20;
}

QTabBar::tab:hover:!selected {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #32323a,
        stop:1 #2a2a30
    );
    color: #b0b0b8;
}

/* ============================================
   GroupBox
   ============================================ */

QGroupBox {
    border: 1px solid #2a2a32;
    border-radius: 5px;
    margin-top: 14px;
    padding-top: 10px;
    color: #a0a0a8;
    font-weight: 500;
    background: transparent;
}

QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 12px;
    padding: 0 8px;
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e22,
        stop:1 #1a1a1e
    );
    color: #909098;
}

/* ============================================
   KeySequenceEdit
   ============================================ */

QKeySequenceEdit {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a1e,
        stop:1 #222228
    );
    border: 1px solid #3a3a42;
    border-radius: 5px;
    padding: 8px 12px;
    min-height: 20px;
    color: #d0d0d5;
}

QKeySequenceEdit:focus {
    border-color: #5080a0;
}

/* ============================================
   ScrollBars - Sleek minimal
   ============================================ */

QScrollBar:vertical {
    background-color: #18181c;
    width: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:vertical {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #3a3a42,
        stop:0.5 #444450,
        stop:1 #3a3a42
    );
    min-height: 30px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:vertical:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:1, y2:0,
        stop:0 #444450,
        stop:0.5 #505060,
        stop:1 #444450
    );
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
    background: none;
}

QScrollBar:horizontal {
    background-color: #18181c;
    height: 10px;
    margin: 0;
    border-radius: 5px;
}

QScrollBar::handle:horizontal {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #3a3a42,
        stop:0.5 #444450,
        stop:1 #3a3a42
    );
    min-width: 30px;
    border-radius: 5px;
    margin: 2px;
}

QScrollBar::handle:horizontal:hover {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #444450,
        stop:0.5 #505060,
        stop:1 #444450
    );
}

QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

QScrollBar::add-page:horizontal, QScrollBar::sub-page:horizontal {
    background: none;
}

/* ============================================
   Message Box
   ============================================ */

QMessageBox {
    background: qlineargradient(
        x1:0, y1:0, x2:0, y2:1,
        stop:0 #1e1e22,
        stop:1 #1a1a1e
    );
}

QMessageBox QLabel {
    color: #d0d0d5;
}

/* ============================================
   Tool Tips
   ============================================ */

QToolTip {
    background-color: #2a2a32;
    border: 1px solid #3a3a42;
    border-radius: 4px;
    padding: 6px 10px;
    color: #d0d0d5;
    font-size: 12px;
}
"""
