import os
from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QLabel, QPushButton, QScrollArea, QGridLayout,
    QProgressBar, QTextEdit, QFileDialog, QFrame,
    QSizePolicy, QComboBox, QSplitter, QStackedWidget
)
from PyQt6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QSize
from PyQt6.QtGui import QColor, QPalette, QIcon

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

from core.assets import icon_label, icon_qicon

from core.styles import STYLESHEET
from core.registry import PluginRegistry
from core.plugin_base import PluginBase
from core.worker import WorkerThread
from core.shop_tab import ShopTab

OUTPUT_DIR = os.path.join(os.path.expanduser("~"), "ToolBox_Output")

CATEGORY_ORDER = ["Images", "Video", "PDF", "Documents", "Audio"]
CATEGORY_ICONS = {
    "Images": "🖼",
    "Video": "▶",
    "PDF": "📄",
    "Documents": "📝",
    "Audio": "🎵",
}


class DropZone(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._files = []
        self.setText("Drop files here  ·  or click to browse")
        self.setObjectName("drop_zone")
        self.setAcceptDrops(True)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setMinimumHeight(70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

    def mousePressEvent(self, event):
        files, _ = QFileDialog.getOpenFileNames(self, "Select files")
        if files:
            self._set_files(files)

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.setProperty("dragover", "true")
            self.style().polish(self)

    def dragLeaveEvent(self, event):
        self.setProperty("dragover", "false")
        self.style().polish(self)

    def dropEvent(self, event):
        self.setProperty("dragover", "false")
        files = [u.toLocalFile() for u in event.mimeData().urls() if u.isLocalFile()]
        if files:
            self._set_files(files)

    def _set_files(self, files):
        self._files = files
        if len(files) == 1:
            self.setText(f"✓  {os.path.basename(files[0])}")
        else:
            self.setText(f"✓  {len(files)} files selected")
        self.setProperty("has_files", "true")
        self.style().polish(self)

    def clear_files(self):
        self._files = []
        self.setText("Drop files here  ·  or click to browse")
        self.setProperty("has_files", "false")
        self.style().polish(self)

    @property
    def files(self):
        return self._files


class ToolCard(QFrame):
    def __init__(self, plugin: PluginBase, parent=None):
        super().__init__(parent)
        self.plugin = plugin
        self.setObjectName("tool_card")
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self.setFixedHeight(100)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.setSpacing(2)

        icon_row = QHBoxLayout()
        icon_lbl = icon_label(plugin.meta.icon_name, plugin.meta.icon_char, 24)
        icon_lbl.setObjectName("card_icon_bg")
        icon_lbl.setStyleSheet(
            f"background-color: {plugin.meta.accent_color}22; "
            f"color: {plugin.meta.accent_color}; font-size: 18px; "
            "border-radius: 8px; padding: 4px 8px;"
        )
        icon_row.addWidget(icon_lbl)
        icon_row.addStretch()
        layout.addLayout(icon_row)

        name_lbl = QLabel(plugin.meta.name)
        name_lbl.setObjectName("card_name")
        layout.addWidget(name_lbl)

        desc_lbl = QLabel(plugin.meta.description)
        desc_lbl.setObjectName("card_desc")
        desc_lbl.setWordWrap(True)
        layout.addWidget(desc_lbl)

    def mousePressEvent(self, event):
        self.parent().parent().parent().select_plugin(self.plugin)

    def set_selected(self, selected: bool):
        self.setProperty("selected", "true" if selected else "false")
        self.style().polish(self)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("ToolBox")
        self.resize(1100, 700)
        self.setMinimumSize(900, 580)
        self.setStyleSheet(STYLESHEET)

        for _icon_file in ("ToolBox.ico", "icon.ico", "icon.png"):
            _p = os.path.join(_ASSETS, _icon_file)
            if os.path.exists(_p):
                self.setWindowIcon(QIcon(_p))
                break

        self.registry = PluginRegistry()
        self.active_plugin: PluginBase | None = None
        self.active_card: ToolCard | None = None
        self.worker: WorkerThread | None = None
        self._plugin_ui_widget: QWidget | None = None

        self._build_ui()
        self._populate_sidebar()
        self._load_initial_view()

    def _build_ui(self):
        root = QWidget()
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)
        self.setCentralWidget(root)

        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(200)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)

        logo = QLabel("Tool<span style='color:#7c6af7'>Box</span>")
        logo.setObjectName("app_logo")
        logo.setTextFormat(Qt.TextFormat.RichText)
        logo.setStyleSheet("font-size: 15px; font-weight: 700; padding: 18px 16px 6px;")
        sidebar_layout.addWidget(logo)

        sep_lbl = QLabel("CATEGORIES")
        sep_lbl.setObjectName("sidebar_title")
        sidebar_layout.addWidget(sep_lbl)

        self.nav_buttons = {}
        categories = self.registry.by_category()

        if categories:
            for cat in CATEGORY_ORDER:
                if cat not in categories:
                    continue
                btn = self._make_nav_btn(cat)
                sidebar_layout.addWidget(btn)
                self.nav_buttons[cat] = btn
        else:
            hint = QLabel("  No plugins installed")
            hint.setStyleSheet("font-size: 11px; color: #444; padding: 6px 16px;")
            sidebar_layout.addWidget(hint)

        sidebar_layout.addStretch()

        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #444; font-size: 10px; padding: 0 16px 14px;")
        sidebar_layout.addWidget(ver)

        sidebar_layout.addStretch()

        shop_sep = QLabel("STORE")
        shop_sep.setObjectName("sidebar_title")
        sidebar_layout.addWidget(shop_sep)

        self.shop_nav_btn = QPushButton("  🛒  Plugin Shop")
        self.shop_nav_btn.setObjectName("nav_btn")
        self.shop_nav_btn.clicked.connect(self._show_shop)
        sidebar_layout.addWidget(self.shop_nav_btn)

        ver = QLabel("v1.0.0")
        ver.setStyleSheet("color: #444; font-size: 10px; padding: 8px 16px 14px;")
        sidebar_layout.addWidget(ver)

        root_layout.addWidget(self.sidebar)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)

        self.right_stack = QStackedWidget()
        right_layout.addWidget(self.right_stack, 1)

        tools_page = QWidget()
        tools_layout = QVBoxLayout(tools_page)
        tools_layout.setContentsMargins(0, 0, 0, 0)
        tools_layout.setSpacing(0)

        self.topbar = QWidget()
        self.topbar.setObjectName("topbar")
        self.topbar.setFixedHeight(66)
        topbar_layout = QVBoxLayout(self.topbar)
        topbar_layout.setContentsMargins(24, 10, 24, 10)
        self.topbar_title = QLabel("Select a category")
        self.topbar_title.setObjectName("topbar_title")
        self.topbar_desc = QLabel("")
        self.topbar_desc.setObjectName("topbar_desc")
        topbar_layout.addWidget(self.topbar_title)
        topbar_layout.addWidget(self.topbar_desc)
        tools_layout.addWidget(self.topbar)

        splitter = QSplitter(Qt.Orientation.Vertical)
        splitter.setChildrenCollapsible(False)
        splitter.setStyleSheet("QSplitter::handle { background: #2a2a2a; height: 1px; }")

        grid_scroll = QScrollArea()
        grid_scroll.setWidgetResizable(True)
        grid_scroll.setFrameShape(QFrame.Shape.NoFrame)
        grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(20, 16, 20, 16)
        self.grid_layout.setSpacing(10)
        grid_scroll.setWidget(self.grid_container)
        splitter.addWidget(grid_scroll)

        workspace_outer = QWidget()
        workspace_outer.setObjectName("workspace")
        workspace_outer.setMinimumHeight(280)
        ws_layout = QVBoxLayout(workspace_outer)
        ws_layout.setContentsMargins(24, 16, 24, 16)
        ws_layout.setSpacing(10)

        drop_row = QHBoxLayout()
        ws_lbl = QLabel("Input")
        ws_lbl.setObjectName("ws_label")
        drop_row.addWidget(ws_lbl)
        self.drop_zone = DropZone()
        drop_row.addWidget(self.drop_zone)

        output_btn = QPushButton("📁  Output folder")
        output_btn.setObjectName("secondary_btn")
        output_btn.setFixedWidth(130)
        output_btn.setToolTip(OUTPUT_DIR)
        output_btn.clicked.connect(self._choose_output_dir)
        drop_row.addWidget(output_btn)
        ws_layout.addLayout(drop_row)

        self.options_area = QWidget()
        self.options_area.setMinimumHeight(60)
        self.options_layout = QVBoxLayout(self.options_area)
        self.options_layout.setContentsMargins(0, 0, 0, 0)
        ws_layout.addWidget(self.options_area)

        bottom_row = QHBoxLayout()
        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(6)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)

        self.run_btn = QPushButton("Run")
        self.run_btn.setObjectName("run_btn")
        self.run_btn.setEnabled(False)
        self.run_btn.clicked.connect(self._run_or_cancel)

        bottom_row.addWidget(self.progress_bar, 1)
        bottom_row.addWidget(self.run_btn)
        ws_layout.addLayout(bottom_row)

        self.log_view = QTextEdit()
        self.log_view.setObjectName("log_view")
        self.log_view.setReadOnly(True)
        self.log_view.setMaximumHeight(100)
        self.log_view.setPlaceholderText("Output log will appear here…")
        ws_layout.addWidget(self.log_view)

        splitter.addWidget(workspace_outer)
        splitter.setSizes([260, 340])
        tools_layout.addWidget(splitter)

        self.status_lbl = QLabel("Ready")
        self.status_lbl.setObjectName("status_bar")
        self.status_lbl.setFixedHeight(24)
        tools_layout.addWidget(self.status_lbl)

        self.right_stack.addWidget(tools_page)

        self.shop_tab = ShopTab()
        self.right_stack.addWidget(self.shop_tab)

        empty_page = QWidget()
        empty_layout = QVBoxLayout(empty_page)
        empty_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_layout.setSpacing(16)

        empty_icon = icon_label("shop", "📦", 48)
        empty_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        if not empty_icon.pixmap():
            empty_icon.setStyleSheet("font-size: 48px;")

        empty_title = QLabel("No plugins installed")
        empty_title.setStyleSheet(
            "font-size: 18px; font-weight: 600; color: #e8e8e8; letter-spacing: -0.02em;"
        )
        empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_desc = QLabel(
            "ToolBox is plugin-based — each tool is installed separately.\n"
            "Head to the Plugin Shop to get started."
        )
        empty_desc.setStyleSheet("font-size: 13px; color: #666; line-height: 1.6;")
        empty_desc.setAlignment(Qt.AlignmentFlag.AlignCenter)
        empty_desc.setWordWrap(True)

        open_shop_btn = QPushButton("  🛒  Open Plugin Shop")
        open_shop_btn.setObjectName("run_btn")
        open_shop_btn.setFixedWidth(200)
        open_shop_btn.clicked.connect(self._show_shop)

        empty_layout.addStretch()
        empty_layout.addWidget(empty_icon)
        empty_layout.addWidget(empty_title)
        empty_layout.addWidget(empty_desc)
        empty_layout.addSpacing(8)
        empty_layout.addWidget(open_shop_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        empty_layout.addStretch()

        self.right_stack.addWidget(empty_page)

        root_layout.addWidget(right, 1)


    def _make_nav_btn(self, cat: str) -> QPushButton:
        ico = icon_qicon(cat.lower(), 16)
        if ico:
            btn = QPushButton(f"  {cat}")
            btn.setIcon(ico)
            btn.setIconSize(QSize(16, 16))
        else:
            btn = QPushButton(f"  {CATEGORY_ICONS.get(cat, '•')}  {cat}")
        btn.setObjectName("nav_btn")
        btn.clicked.connect(lambda _, c=cat: self._show_category(c))
        return btn

    def _populate_sidebar(self):
        pass

    def _load_initial_view(self):
        if not self.registry.all():
            self._show_shop(auto=True)
        else:
            cats = self.registry.by_category()
            for cat in CATEGORY_ORDER:
                if cat in cats:
                    self._show_category(cat)
                    return

    def _show_category(self, category: str):
        self.right_stack.setCurrentIndex(0)

        for cat, btn in self.nav_buttons.items():
            btn.setProperty("active", "true" if cat == category else "false")
            btn.style().polish(btn)
        self.shop_nav_btn.setProperty("active", "false")
        self.shop_nav_btn.style().polish(self.shop_nav_btn)

        plugins = self.registry.by_category().get(category, [])
        self.topbar_title.setText(category)
        self.topbar_desc.setText(f"{len(plugins)} tool{'s' if len(plugins) != 1 else ''} available")

        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        self.active_card = None
        cols = 3
        for i, plugin in enumerate(plugins):
            card = ToolCard(plugin, self.grid_container)
            self.grid_layout.addWidget(card, i // cols, i % cols)

        self.grid_layout.setRowStretch(max(1, (len(plugins) // cols) + 1), 1)

        if plugins:
            self.select_plugin(plugins[0])

    def _show_shop(self, auto: bool = False):
        for btn in self.nav_buttons.values():
            btn.setProperty("active", "false")
            btn.style().polish(btn)
        self.shop_nav_btn.setProperty("active", "true")
        self.shop_nav_btn.style().polish(self.shop_nav_btn)

        self.right_stack.setCurrentIndex(1)

        if not self.shop_tab._registry:
            self.shop_tab.fetch_registry()

        if not hasattr(self, "_shop_install_connected"):
            self.shop_tab._install_done_hook = self._on_plugin_installed
            self._shop_install_connected = True

    def _on_plugin_installed(self):
        self.registry = PluginRegistry()

        sidebar_layout = self.sidebar.layout()

        for btn in list(self.nav_buttons.values()):
            sidebar_layout.removeWidget(btn)
            btn.deleteLater()
        self.nav_buttons.clear()

        for i in range(sidebar_layout.count()):
            item = sidebar_layout.itemAt(i)
            if item and item.widget():
                w = item.widget()
                if isinstance(w, QLabel) and "No plugins" in w.text():
                    sidebar_layout.removeWidget(w)
                    w.deleteLater()
                    break

        categories = self.registry.by_category()
        insert_after = None
        for i in range(sidebar_layout.count()):
            item = sidebar_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QLabel):
                if item.widget().objectName() == "sidebar_title":
                    insert_after = i
                    break

        pos = (insert_after + 1) if insert_after is not None else 2
        for cat in CATEGORY_ORDER:
            if cat not in categories:
                continue
            btn = self._make_nav_btn(cat)
            sidebar_layout.insertWidget(pos, btn)
            self.nav_buttons[cat] = btn
            pos += 1

        self.status_lbl.setText("Plugin installed — sidebar updated")

    

    def select_plugin(self, plugin: PluginBase):
        self.active_plugin = plugin

        for i in range(self.grid_layout.count()):
            w = self.grid_layout.itemAt(i).widget()
            if isinstance(w, ToolCard):
                w.set_selected(w.plugin is plugin)
                if w.plugin is plugin:
                    self.active_card = w

        if self._plugin_ui_widget:
            self._plugin_ui_widget.setParent(None)
            self._plugin_ui_widget = None

        try:
            ui = plugin.build_ui(self.options_area)
            self.options_layout.addWidget(ui)
            self._plugin_ui_widget = ui
        except Exception as e:
            self._log(f"Failed to build plugin UI: {e}", "error")

        self.run_btn.setEnabled(True)
        self.run_btn.setText(f"Run  {plugin.meta.name}")
        self.drop_zone.clear_files()
        self.progress_bar.setValue(0)
        self.progress_bar.setVisible(False)
        self.log_view.clear()
        self.status_lbl.setText(f"Selected: {plugin.meta.name}")


    def _run_or_cancel(self):
        if self.worker and self.worker.isRunning():
            self.active_plugin.cancel()
            self.run_btn.setEnabled(False)
            self.status_lbl.setText("Cancelling…")
            return

        if not self.active_plugin:
            return

        files = self.drop_zone.files
        if not files:
            self._log("No input files selected.", "warn")
            return

        self.log_view.clear()
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.run_btn.setText("Cancel")

        self.worker = WorkerThread(self.active_plugin, files, self.output_dir)
        self.worker.progress.connect(self._on_progress)
        self.worker.log.connect(self._on_log)
        self.worker.done.connect(self._on_done)
        self.worker.start()

    def _on_progress(self, value: int):
        self.progress_bar.setValue(value)
        self.status_lbl.setText(f"Processing… {value}%")

    def _on_log(self, message: str, level: str):
        self._log(message, level)

    def _on_done(self, success: bool, message: str):
        self.progress_bar.setValue(100 if success else self.progress_bar.value())
        if self.active_plugin:
            self.run_btn.setText(f"Run  {self.active_plugin.meta.name}")
        self.run_btn.setEnabled(True)
        if success:
            self._log(message or "Done!", "ok")
            self.status_lbl.setText(f"Finished · Output: {self.output_dir}")
        else:
            self._log(message or "Failed.", "error")
            self.status_lbl.setText("Error — see log")

    def _log(self, message: str, level: str = "info"):
        colors = {
            "info":  "#888",
            "ok": "#5fbc85",
            "warn": "#d4a017",
            "error": "#e05c5c",
        }
        color = colors.get(level, "#888")
        self.log_view.append(f'<span style="color:{color};">{message}</span>')

    def _choose_output_dir(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output folder", self.output_dir)
        if path:
            self.output_dir = path
            self.status_lbl.setText(f"Output folder: {path}")

    @property
    def output_dir(self):
        return getattr(self, "_output_dir", OUTPUT_DIR)

    @output_dir.setter
    def output_dir(self, val):
        self._output_dir = val