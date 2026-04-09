"""Modern dark theme QSS stylesheet."""

# Palette
# bg          #0b1020   window background
# panel       #141b2d   main content surface
# elevated    #1b2236   inputs, list items
# hover       #232c44
# border      #2a3350
# text        #e5e7eb
# muted       #94a3b8
# accent      #818cf8
# accent-hov  #a5b4fc
# danger      #f87171

STYLESHEET = """
* {
    font-family: "Segoe UI", "SF Pro Display", "Helvetica Neue", Arial, sans-serif;
    font-size: 13px;
    color: #e5e7eb;
}

QMainWindow, QWidget {
    background-color: #0b1020;
}

/* ---------- Sidebar ---------- */
QWidget#sidebar {
    background-color: #0e1426;
    border-right: 1px solid #1e2740;
}

QLabel#appTitle {
    color: #f1f5f9;
    font-size: 18px;
    font-weight: 700;
    padding: 18px 18px 2px 18px;
    background: transparent;
}
QLabel#appSubtitle {
    color: #64748b;
    font-size: 11px;
    font-weight: 500;
    padding: 0 18px 14px 18px;
    background: transparent;
    letter-spacing: 0.5px;
}
QLabel#sectionLabel {
    color: #64748b;
    font-size: 10px;
    font-weight: 700;
    padding: 10px 18px 6px 18px;
    background: transparent;
    letter-spacing: 1.2px;
}

QListWidget#navList {
    background: transparent;
    border: none;
    outline: 0;
    padding: 4px 8px;
}
QListWidget#navList::item {
    background: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 2px 4px;
    color: #94a3b8;
    font-weight: 500;
}
QListWidget#navList::item:hover {
    background: #1b2236;
    color: #e5e7eb;
}
QListWidget#navList::item:selected {
    background: #1e2a4d;
    color: #a5b4fc;
    font-weight: 600;
    border-left: 3px solid #818cf8;
    padding-left: 11px;
}

/* ---------- Main content ---------- */
QWidget#contentArea {
    background-color: #0b1020;
}

QLabel#pageTitle {
    color: #f1f5f9;
    font-size: 20px;
    font-weight: 700;
    background: transparent;
}
QLabel#pageSubtitle {
    color: #64748b;
    font-size: 12px;
    background: transparent;
}

/* ---------- Groups ---------- */
QGroupBox {
    background: #141b2d;
    border: 1px solid #1e2740;
    border-radius: 12px;
    margin-top: 16px;
    padding: 16px;
    font-weight: 600;
    color: #cbd5e1;
}
QGroupBox::title {
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 14px;
    padding: 0 8px;
    background: #141b2d;
    color: #a5b4fc;
    font-size: 12px;
    font-weight: 600;
}

QLabel {
    background: transparent;
    color: #cbd5e1;
}

/* ---------- Inputs ---------- */
QLineEdit, QSpinBox, QComboBox {
    background: #1b2236;
    border: 1px solid #2a3350;
    border-radius: 8px;
    padding: 8px 12px;
    color: #e5e7eb;
    selection-background-color: #818cf8;
    selection-color: #0b1020;
}
QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
    border: 1px solid #818cf8;
    background: #1e2640;
}
QLineEdit:hover, QSpinBox:hover, QComboBox:hover {
    border: 1px solid #3b456a;
}
QLineEdit::placeholder {
    color: #64748b;
}

QComboBox::drop-down {
    border: none;
    width: 26px;
}
QComboBox QAbstractItemView {
    background: #1b2236;
    border: 1px solid #2a3350;
    border-radius: 8px;
    selection-background-color: #1e2a4d;
    selection-color: #a5b4fc;
    color: #e5e7eb;
    padding: 4px;
    outline: 0;
}

QSpinBox::up-button, QSpinBox::down-button {
    background: transparent;
    border: none;
    width: 18px;
}

/* ---------- Buttons ---------- */
QPushButton {
    background: #1b2236;
    color: #cbd5e1;
    border: 1px solid #2a3350;
    border-radius: 8px;
    padding: 9px 18px;
    font-weight: 500;
}
QPushButton:hover {
    background: #232c44;
    border: 1px solid #3b456a;
    color: #f1f5f9;
}
QPushButton:pressed {
    background: #161d30;
}
QPushButton:disabled {
    color: #475569;
    background: #141b2d;
    border: 1px solid #1e2740;
}

QPushButton#primary {
    background: #6366f1;
    color: #ffffff;
    border: 1px solid #6366f1;
    font-weight: 600;
    padding: 10px 24px;
}
QPushButton#primary:hover {
    background: #818cf8;
    border: 1px solid #818cf8;
}
QPushButton#primary:pressed {
    background: #4f46e5;
}
QPushButton#primary:disabled {
    background: #312e81;
    border: 1px solid #312e81;
    color: #94a3b8;
}

QPushButton#danger {
    background: #1b2236;
    color: #f87171;
    border: 1px solid #3b1f2e;
}
QPushButton#danger:hover {
    background: #2a1620;
    border: 1px solid #7f1d1d;
    color: #fca5a5;
}

/* ---------- Checkbox ---------- */
QCheckBox {
    background: transparent;
    spacing: 8px;
    color: #cbd5e1;
}
QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #3b456a;
    background: #1b2236;
}
QCheckBox::indicator:hover {
    border: 1px solid #818cf8;
}
QCheckBox::indicator:checked {
    background: #6366f1;
    border: 1px solid #6366f1;
}

/* ---------- Slider ---------- */
QSlider::groove:horizontal {
    height: 6px;
    border-radius: 3px;
    background: #1b2236;
    border: 1px solid #2a3350;
}
QSlider::sub-page:horizontal {
    background: #6366f1;
    border-radius: 3px;
}
QSlider::handle:horizontal {
    background: #e5e7eb;
    border: 2px solid #818cf8;
    width: 16px;
    height: 16px;
    margin: -7px 0;
    border-radius: 10px;
}
QSlider::handle:horizontal:hover {
    background: #ffffff;
    border: 2px solid #a5b4fc;
}

/* ---------- Progress bar ---------- */
QProgressBar {
    background: #0f1a2e;
    border: 1px solid #1e3a2e;
    border-radius: 6px;
    height: 14px;
    text-align: center;
    color: #ecfdf5;
    font-size: 11px;
    font-weight: 600;
}
QProgressBar::chunk {
    background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
        stop:0 #10b981, stop:1 #34d399);
    border-radius: 5px;
}

/* ---------- Log / code panel ---------- */
QPlainTextEdit {
    background: #060a16;
    color: #94a3b8;
    border: 1px solid #1e2740;
    border-radius: 8px;
    padding: 8px 10px;
    font-family: "Consolas", "Menlo", "Courier New", monospace;
    font-size: 12px;
    selection-background-color: #6366f1;
    selection-color: #ffffff;
}

/* ---------- Drop zone list ---------- */
QListWidget#dropList {
    background: #0e1426;
    border: 2px dashed #2a3350;
    border-radius: 12px;
    padding: 8px;
    outline: 0;
    color: #cbd5e1;
}
QListWidget#dropList[dragging="true"] {
    border: 2px dashed #818cf8;
    background: #141d38;
}
QListWidget#dropList::item {
    background: transparent;
    border: none;
    padding: 0;
    margin: 3px 0;
}
QListWidget#dropList::item:selected {
    background: transparent;
}

QWidget#queueItem {
    background: #1b2236;
    border: 1px solid #2a3350;
    border-radius: 8px;
}
QWidget#queueItem:hover {
    background: #232c44;
    border: 1px solid #3b456a;
}

/* ---------- Status bar ---------- */
QStatusBar {
    background: #0e1426;
    color: #64748b;
    border-top: 1px solid #1e2740;
    padding: 4px 10px;
}

/* ---------- Scrollbars ---------- */
QScrollBar:vertical {
    background: transparent;
    width: 10px;
    margin: 0;
}
QScrollBar::handle:vertical {
    background: #2a3350;
    border-radius: 5px;
    min-height: 24px;
}
QScrollBar::handle:vertical:hover {
    background: #3b456a;
}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}
QScrollBar:horizontal {
    background: transparent;
    height: 10px;
}
QScrollBar::handle:horizontal {
    background: #2a3350;
    border-radius: 5px;
    min-width: 24px;
}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
    width: 0;
}

/* ---------- Dialogs ---------- */
QMessageBox {
    background: #141b2d;
}
QMessageBox QLabel {
    color: #e5e7eb;
}

QScrollArea {
    background: transparent;
    border: none;
}
QScrollArea > QWidget > QWidget {
    background: transparent;
}
QScrollArea > QWidget#qt_scrollarea_viewport {
    background: transparent;
}

QLabel#previewLabel {
    background: #060a16;
    border: 1px solid #1e2740;
    border-radius: 10px;
    color: #64748b;
    min-width: 420px;
    min-height: 280px;
    padding: 8px;
}

QToolTip {
    background: #1b2236;
    color: #e5e7eb;
    border: 1px solid #2a3350;
    padding: 5px 8px;
    border-radius: 6px;
}
"""
