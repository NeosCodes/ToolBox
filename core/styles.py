STYLESHEET = """
QWidget {
    background-color: #1a1a1a;
    color: #e8e8e8;
    font-family: 'Segoe UI', 'SF Pro Display', 'Helvetica Neue', Arial, sans-serif;
    font-size: 13px;
}

/* ── Sidebar ──────────────────────────────────────────── */
#sidebar {
    background-color: #141414;
    border-right: 1px solid #2a2a2a;
    min-width: 200px;
    max-width: 200px;
}

#sidebar_title {
    font-size: 10px;
    font-weight: 600;
    color: #555;
    letter-spacing: 0.12em;
    text-transform: uppercase;
    padding: 20px 16px 8px;
}

#app_logo {
    font-size: 15px;
    font-weight: 700;
    color: #e8e8e8;
    padding: 18px 16px 6px;
    letter-spacing: -0.02em;
}

#app_logo span {
    color: #7c6af7;
}

QPushButton#nav_btn {
    background: transparent;
    border: none;
    border-radius: 6px;
    text-align: left;
    padding: 9px 14px;
    color: #888;
    font-size: 13px;
    font-weight: 400;
    margin: 1px 8px;
}

QPushButton#nav_btn:hover {
    background-color: #222;
    color: #ccc;
}

QPushButton#nav_btn[active="true"] {
    background-color: #252525;
    color: #e8e8e8;
    font-weight: 500;
}

/* ── Top Bar ──────────────────────────────────────────── */
#topbar {
    background-color: #1a1a1a;
    border-bottom: 1px solid #2a2a2a;
    padding: 14px 24px;
}

#topbar_title {
    font-size: 18px;
    font-weight: 600;
    color: #e8e8e8;
    letter-spacing: -0.02em;
}

#topbar_desc {
    font-size: 12px;
    color: #666;
    margin-top: 2px;
}

/* ── Tool Cards ───────────────────────────────────────── */
#tool_card {
    background-color: #212121;
    border: 1px solid #2a2a2a;
    border-radius: 10px;
    padding: 14px;
}

#tool_card:hover {
    background-color: #262626;
    border-color: #333;
}

#tool_card[selected="true"] {
    background-color: #1e1b3a;
    border-color: #7c6af7;
}

#card_name {
    font-size: 13px;
    font-weight: 500;
    color: #e0e0e0;
}

#card_desc {
    font-size: 11px;
    color: #666;
    margin-top: 2px;
}

#card_icon_bg {
    border-radius: 8px;
    padding: 6px;
    margin-bottom: 8px;
}

/* ── Workspace ────────────────────────────────────────── */
#workspace {
    background-color: #1a1a1a;
    border-top: 1px solid #2a2a2a;
    padding: 16px 24px;
}

#ws_label {
    font-size: 12px;
    color: #666;
    min-width: 80px;
}

/* Drop zone */
#drop_zone {
    background-color: #212121;
    border: 1.5px dashed #333;
    border-radius: 8px;
    color: #555;
    font-size: 12px;
    padding: 14px;
    min-height: 60px;
}

#drop_zone[dragover="true"] {
    border-color: #7c6af7;
    background-color: #1e1b3a;
    color: #9d8fff;
}

#drop_zone[has_files="true"] {
    border-color: #3a8a5a;
    background-color: #1a2820;
    color: #5fbc85;
}

/* ── Inputs / Selects ─────────────────────────────────── */
QComboBox {
    background-color: #252525;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ccc;
    min-height: 30px;
}

QComboBox:focus {
    border-color: #7c6af7;
}

QComboBox::drop-down {
    border: none;
    padding-right: 8px;
}

QComboBox QAbstractItemView {
    background-color: #252525;
    border: 1px solid #333;
    border-radius: 6px;
    color: #ccc;
    selection-background-color: #7c6af7;
    outline: none;
    padding: 4px;
}

QSpinBox, QDoubleSpinBox {
    background-color: #252525;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ccc;
    min-height: 30px;
}

QSpinBox:focus, QDoubleSpinBox:focus {
    border-color: #7c6af7;
}

QLineEdit {
    background-color: #252525;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px 10px;
    color: #ccc;
    min-height: 30px;
}

QLineEdit:focus {
    border-color: #7c6af7;
}

QCheckBox {
    color: #ccc;
    spacing: 8px;
}

QCheckBox::indicator {
    width: 16px;
    height: 16px;
    border-radius: 4px;
    border: 1px solid #444;
    background: #252525;
}

QCheckBox::indicator:checked {
    background-color: #7c6af7;
    border-color: #7c6af7;
}

/* ── Buttons ──────────────────────────────────────────── */
QPushButton#run_btn {
    background-color: #7c6af7;
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 9px 22px;
    font-size: 13px;
    font-weight: 600;
    min-width: 120px;
}

QPushButton#run_btn:hover {
    background-color: #8b7af8;
}

QPushButton#run_btn:pressed {
    background-color: #6a58e0;
}

QPushButton#run_btn:disabled {
    background-color: #2a2a2a;
    color: #555;
}

QPushButton#secondary_btn {
    background-color: transparent;
    color: #888;
    border: 1px solid #333;
    border-radius: 8px;
    padding: 9px 16px;
    font-size: 12px;
}

QPushButton#secondary_btn:hover {
    background-color: #252525;
    color: #ccc;
    border-color: #444;
}

/* ── Progress Bar ─────────────────────────────────────── */
QProgressBar {
    background-color: #252525;
    border: none;
    border-radius: 4px;
    height: 6px;
    text-align: center;
    color: transparent;
}

QProgressBar::chunk {
    background-color: #7c6af7;
    border-radius: 4px;
}

/* ── Log / Output ─────────────────────────────────────── */
QTextEdit#log_view {
    background-color: #141414;
    border: 1px solid #2a2a2a;
    border-radius: 8px;
    color: #666;
    font-family: 'Consolas', 'Fira Code', 'Courier New', monospace;
    font-size: 11px;
    padding: 10px;
}

/* ── Scrollbar ────────────────────────────────────────── */
QScrollBar:vertical {
    background: transparent;
    width: 8px;
    margin: 0;
}

QScrollBar::handle:vertical {
    background: #333;
    border-radius: 4px;
    min-height: 20px;
}

QScrollBar::handle:vertical:hover {
    background: #444;
}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {
    height: 0;
}

QScrollBar:horizontal {
    background: transparent;
    height: 8px;
}

QScrollBar::handle:horizontal {
    background: #333;
    border-radius: 4px;
    min-width: 20px;
}

/* ── Status Bar ───────────────────────────────────────── */
#status_bar {
    background-color: #141414;
    border-top: 1px solid #222;
    padding: 5px 20px;
    font-size: 11px;
    color: #555;
}

/* ── Separator ────────────────────────────────────────── */
QFrame[frameShape="4"],
QFrame[frameShape="HLine"] {
    color: #2a2a2a;
    background: #2a2a2a;
    max-height: 1px;
    border: none;
}

/* ── Tooltips ─────────────────────────────────────────── */
QToolTip {
    background-color: #2a2a2a;
    color: #ddd;
    border: 1px solid #333;
    border-radius: 6px;
    padding: 6px 10px;
    font-size: 12px;
}
"""