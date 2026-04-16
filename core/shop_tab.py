import os
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QLineEdit, QComboBox, QTextEdit,
    QStackedWidget, QProgressBar, QSizePolicy, QDialog,
    QDialogButtonBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor

from core.shop_manager import (
    RegistryFetcher, PluginInstaller,
    get_installed_versions, version_newer,
    save_review, get_my_review,
)

class StarRating(QWidget):
    def __init__(self, value: float = 0, max_stars: int = 5,
                 interactive: bool = False, parent=None):
        super().__init__(parent)
        self._value = value
        self._max = max_stars
        self._interactive = interactive
        self._hover = -1
        self._selected = int(round(value)) if interactive else 0
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(2)
        self._stars = []
        for i in range(max_stars):
            lbl = QLabel("★")
            lbl.setFixedSize(18, 18)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 14px;")
            layout.addWidget(lbl)
            self._stars.append(lbl)
        if interactive:
            self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._refresh()

    def _refresh(self, highlight: int = -1):
        active = highlight if highlight >= 0 else (self._selected if self._interactive else self._value)
        for i, lbl in enumerate(self._stars):
            filled = (i + 1) <= active
            lbl.setStyleSheet(
                f"font-size: 14px; color: {'#f5c518' if filled else '#444'};"
            )

    def mouseMoveEvent(self, e):
        if not self._interactive:
            return
        for i, lbl in enumerate(self._stars):
            if lbl.geometry().contains(e.pos()):
                self._hover = i + 1
                self._refresh(self._hover)
                return

    def leaveEvent(self, e):
        if self._interactive:
            self._hover = -1
            self._refresh()

    def mousePressEvent(self, e):
        if not self._interactive:
            return
        for i, lbl in enumerate(self._stars):
            if lbl.geometry().contains(e.pos()):
                self._selected = i + 1
                self._refresh()
                return

    @property
    def value(self) -> int:
        return self._selected

class ReviewDialog(QDialog):
    def __init__(self, plugin_id: str, plugin_name: str, parent=None):
        super().__init__(parent)
        self.plugin_id = plugin_id
        self.setWindowTitle(f"Review — {plugin_name}")
        self.setFixedSize(420, 280)
        self.setStyleSheet(parent.styleSheet() if parent else "")

        layout = QVBoxLayout(self)
        layout.setSpacing(14)
        layout.setContentsMargins(20, 20, 20, 20)

        layout.addWidget(QLabel(f"<b>{plugin_name}</b>"))

        stars_row = QHBoxLayout()
        stars_row.addWidget(QLabel("Rating"))
        self.stars = StarRating(0, interactive=True)
        stars_row.addWidget(self.stars)
        stars_row.addStretch()
        layout.addLayout(stars_row)

        layout.addWidget(QLabel("Comment (optional)"))
        self.comment = QTextEdit()
        self.comment.setMaximumHeight(90)
        self.comment.setPlaceholderText("What did you like or dislike?")
        layout.addWidget(self.comment)

        existing = get_my_review(plugin_id)
        if existing:
            self.stars._selected = existing["stars"]
            self.stars._refresh()
            self.comment.setPlainText(existing.get("comment", ""))

        btns = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        btns.accepted.connect(self._submit)
        btns.rejected.connect(self.reject)
        layout.addWidget(btns)

    def _submit(self):
        if self.stars.value == 0:
            return
        save_review(self.plugin_id, self.stars.value, self.comment.toPlainText())
        self.accept()

class ShopCard(QFrame):
    def __init__(self, data: dict, installed_version: str | None,
                 on_install, on_update, on_review, parent=None):
        super().__init__(parent)
        self.data = data
        self.setObjectName("tool_card")
        self.setMinimumHeight(140)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 14, 16, 14)
        layout.setSpacing(6)

        header = QHBoxLayout()

        icon_lbl = QLabel(data["icon_char"])
        icon_lbl.setStyleSheet(
            f"font-size: 20px; background: {data['accent_color']}22; "
            f"color: {data['accent_color']}; border-radius: 8px; padding: 4px 8px;"
        )
        header.addWidget(icon_lbl)

        title_col = QVBoxLayout()
        name_row = QHBoxLayout()
        name_lbl = QLabel(data["name"])
        name_lbl.setObjectName("card_name")
        name_row.addWidget(name_lbl)

        if data.get("official"):
            badge = QLabel("official")
            badge.setStyleSheet(
                "font-size: 10px; font-weight: 600; color: #7c6af7; "
                "background: #7c6af722; border-radius: 4px; padding: 1px 6px;"
            )
            name_row.addWidget(badge)
        name_row.addStretch()
        title_col.addLayout(name_row)

        author_lbl = QLabel(f"by {data['author']}  ·  v{data['version']}")
        author_lbl.setObjectName("card_desc")
        title_col.addWidget(author_lbl)
        header.addLayout(title_col, 1)

        layout.addLayout(header)

        desc_lbl = QLabel(data["description"])
        desc_lbl.setWordWrap(True)
        desc_lbl.setStyleSheet("font-size: 12px; color: #888; line-height: 1.5;")
        layout.addWidget(desc_lbl)

        tags_row = QHBoxLayout()
        tags_row.setSpacing(5)
        for tag in data.get("tags", [])[:4]:
            t = QLabel(tag)
            t.setStyleSheet(
                "font-size: 10px; color: #666; background: #252525; "
                "border-radius: 4px; padding: 2px 7px;"
            )
            tags_row.addWidget(t)
        tags_row.addStretch()
        layout.addLayout(tags_row)

        bottom = QHBoxLayout()

        star_widget = StarRating(data.get("rating_avg", 0))
        bottom.addWidget(star_widget)
        count_lbl = QLabel(f"{data.get('rating_count', 0)} reviews")
        count_lbl.setStyleSheet("font-size: 11px; color: #555;")
        bottom.addWidget(count_lbl)

        my_rev = get_my_review(data["id"])
        if my_rev:
            mine_lbl = QLabel(f"  My rating: {'★' * my_rev['stars']}")
            mine_lbl.setStyleSheet("font-size: 11px; color: #f5c518;")
            bottom.addWidget(mine_lbl)

        bottom.addStretch()

        size_kb = data.get("size_bytes", 0) // 1024
        if size_kb:
            sz = QLabel(f"{size_kb} KB")
            sz.setStyleSheet("font-size: 11px; color: #555;")
            bottom.addWidget(sz)

        review_btn = QPushButton("Review")
        review_btn.setObjectName("secondary_btn")
        review_btn.setFixedWidth(90)
        review_btn.clicked.connect(lambda: on_review(data))
        bottom.addWidget(review_btn)

        if installed_version is None:
            install_btn = QPushButton("⬇  Install")
            install_btn.setObjectName("run_btn")
            install_btn.setFixedWidth(100)
            install_btn.clicked.connect(lambda: on_install(data))
            bottom.addWidget(install_btn)

        elif version_newer(data["version"], installed_version):
            update_btn = QPushButton(f"↑  Update to {data['version']}")
            update_btn.setObjectName("run_btn")
            update_btn.setFixedWidth(140)
            update_btn.setStyleSheet(
                "QPushButton#run_btn { background-color: #3a8a5a; }"
                "QPushButton#run_btn:hover { background-color: #4aa06a; }"
            )
            update_btn.clicked.connect(lambda: on_update(data))
            bottom.addWidget(update_btn)

        else:
            ins_lbl = QLabel(f"✓  Installed {installed_version}")
            ins_lbl.setStyleSheet("font-size: 12px; color: #5fbc85; font-weight: 500;")
            bottom.addWidget(ins_lbl)

        layout.addLayout(bottom)

        changelog = data.get("changelog", {})
        if changelog:
            sep = QFrame()
            sep.setFrameShape(QFrame.Shape.HLine)
            sep.setStyleSheet("color: #2a2a2a; background: #2a2a2a; max-height: 1px; border: none;")
            layout.addWidget(sep)

            cl_toggle = QPushButton("▸  Changelog")
            cl_toggle.setObjectName("secondary_btn")
            cl_toggle.setCheckable(True)
            cl_toggle.setStyleSheet(
                "QPushButton { border: none; text-align: left; font-size: 11px; color: #555; padding: 0; background: transparent; }"
                "QPushButton:hover { color: #888; }"
            )

            cl_text = QLabel()
            cl_text.setWordWrap(True)
            cl_text.setVisible(False)
            cl_text.setStyleSheet("font-size: 11px; color: #666; font-family: monospace; padding: 4px 0;")
            lines = [f"<b>{v}</b>  {note}" for v, note in list(changelog.items())[:5]]
            cl_text.setText("<br>".join(lines))

            def toggle_cl(checked, btn=cl_toggle, txt=cl_text):
                txt.setVisible(checked)
                btn.setText(("▾" if checked else "▸") + "  Changelog")

            cl_toggle.toggled.connect(toggle_cl)
            layout.addWidget(cl_toggle)
            layout.addWidget(cl_text)

class ShopTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._registry: list = []
        self._filter_text = ""
        self._filter_cat = "All"
        self._installer: PluginInstaller | None = None
        self._fetcher: RegistryFetcher | None = None
        self._install_done_hook = None
        self._build_ui()

    def _build_ui(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        topbar = QWidget()
        topbar.setObjectName("topbar")
        topbar.setFixedHeight(66)
        tb_layout = QHBoxLayout(topbar)
        tb_layout.setContentsMargins(24, 10, 24, 10)

        title_col = QVBoxLayout()
        title_lbl = QLabel("Plugin Shop")
        title_lbl.setObjectName("topbar_title")
        self.subtitle_lbl = QLabel("Browse and install plugins")
        self.subtitle_lbl.setObjectName("topbar_desc")
        title_col.addWidget(title_lbl)
        title_col.addWidget(self.subtitle_lbl)
        tb_layout.addLayout(title_col)

        tb_layout.addStretch()

        refresh_btn = QPushButton("↺  Refresh")
        refresh_btn.setObjectName("secondary_btn")
        refresh_btn.clicked.connect(self.fetch_registry)
        tb_layout.addWidget(refresh_btn)

        root.addWidget(topbar)

        filter_bar = QWidget()
        filter_bar.setStyleSheet("background: #1a1a1a; border-bottom: 1px solid #2a2a2a;")
        fb_layout = QHBoxLayout(filter_bar)
        fb_layout.setContentsMargins(24, 10, 24, 10)
        fb_layout.setSpacing(12)

        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText("Search plugins…")
        self.search_box.setFixedWidth(220)
        self.search_box.textChanged.connect(self._on_filter_change)
        fb_layout.addWidget(self.search_box)

        self.cat_filter = QComboBox()
        self.cat_filter.addItems(["All", "Images", "Video", "PDF", "Documents", "Audio"])
        self.cat_filter.setFixedWidth(120)
        self.cat_filter.currentTextChanged.connect(self._on_filter_change)
        fb_layout.addWidget(self.cat_filter)

        fb_layout.addStretch()

        self.update_badge = QLabel("")
        self.update_badge.setStyleSheet(
            "background: #3a8a5a; color: #fff; font-size: 11px; font-weight: 600; "
            "border-radius: 10px; padding: 2px 10px;"
        )
        self.update_badge.setVisible(False)
        fb_layout.addWidget(self.update_badge)

        root.addWidget(filter_bar)

        self.stack = QStackedWidget()

        loading_page = QWidget()
        ll = QVBoxLayout(loading_page)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_lbl = QLabel("Fetching registry…")
        self._loading_lbl.setStyleSheet("color: #555; font-size: 13px;")
        self._loading_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._loading_bar = QProgressBar()
        self._loading_bar.setRange(0, 0)
        self._loading_bar.setFixedWidth(260)
        self._loading_bar.setFixedHeight(4)
        ll.addWidget(self._loading_lbl)
        ll.addWidget(self._loading_bar, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(loading_page)

        error_page = QWidget()
        el = QVBoxLayout(error_page)
        el.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._error_lbl = QLabel("Could not fetch registry.")
        self._error_lbl.setStyleSheet("color: #e05c5c; font-size: 13px;")
        self._error_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        retry_btn = QPushButton("Retry")
        retry_btn.setObjectName("secondary_btn")
        retry_btn.setFixedWidth(100)
        retry_btn.clicked.connect(self.fetch_registry)
        el.addWidget(self._error_lbl)
        el.addWidget(retry_btn, alignment=Qt.AlignmentFlag.AlignCenter)
        self.stack.addWidget(error_page)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        self._cards_widget = QWidget()
        self._cards_layout = QVBoxLayout(self._cards_widget)
        self._cards_layout.setContentsMargins(24, 16, 24, 16)
        self._cards_layout.setSpacing(10)
        self._cards_layout.addStretch()
        scroll.setWidget(self._cards_widget)
        self.stack.addWidget(scroll)

        root.addWidget(self.stack, 1)

        self.footer = QWidget()
        self.footer.setObjectName("workspace")
        self.footer.setFixedHeight(72)
        self.footer.setVisible(False)
        fl = QVBoxLayout(self.footer)
        fl.setContentsMargins(24, 10, 24, 10)
        fl.setSpacing(6)

        self._install_lbl = QLabel("Installing…")
        self._install_lbl.setStyleSheet("font-size: 12px; color: #888;")
        self._install_progress = QProgressBar()
        self._install_progress.setFixedHeight(6)
        self._install_progress.setRange(0, 100)

        fl.addWidget(self._install_lbl)
        fl.addWidget(self._install_progress)
        root.addWidget(self.footer)

    def fetch_registry(self):
        self.stack.setCurrentIndex(0)
        self._fetcher = RegistryFetcher()
        self._fetcher.done.connect(self._on_registry_loaded)
        self._fetcher.error.connect(self._on_registry_error)
        self._fetcher.start()

    def _on_registry_loaded(self, plugins: list):
        self._registry = plugins
        installed = get_installed_versions()

        updates = sum(
            1 for p in plugins
            if p["id"] in installed and version_newer(p["version"], installed[p["id"]])
        )
        if updates:
            self.update_badge.setText(f"  {updates} update{'s' if updates > 1 else ''} available  ")
            self.update_badge.setVisible(True)
        else:
            self.update_badge.setVisible(False)

        self.subtitle_lbl.setText(f"{len(plugins)} plugins available")
        self._render_cards()
        self.stack.setCurrentIndex(2)

    def _on_registry_error(self, msg: str):
        self._error_lbl.setText(f"Could not fetch registry: {msg}")
        self.stack.setCurrentIndex(1)

    def _on_filter_change(self):
        self._filter_text = self.search_box.text().lower()
        self._filter_cat  = self.cat_filter.currentText()
        self._render_cards()

    def _render_cards(self):
        installed = get_installed_versions()

        while self._cards_layout.count() > 1:
            item = self._cards_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        filtered = [
            p for p in self._registry
            if (self._filter_cat == "All" or p.get("category") == self._filter_cat)
            and (
                not self._filter_text
                or self._filter_text in p["name"].lower()
                or self._filter_text in p.get("description", "").lower()
                or any(self._filter_text in t for t in p.get("tags", []))
            )
        ]

        def sort_key(p):
            iv = installed.get(p["id"])
            if iv and version_newer(p["version"], iv):
                return 0
            if iv is None:
                return 1
            return 2

        filtered.sort(key=sort_key)

        for p in filtered:
            card = ShopCard(
                data=p,
                installed_version=installed.get(p["id"]),
                on_install=self._do_install,
                on_update=self._do_install,
                on_review=self._do_review,
                parent=self._cards_widget,
            )
            self._cards_layout.insertWidget(self._cards_layout.count() - 1, card)

    def _do_install(self, plugin_meta: dict):
        if self._installer and self._installer.isRunning():
            return
        self.footer.setVisible(True)
        self._install_progress.setValue(0)
        self._install_lbl.setText(f"Installing {plugin_meta['name']}…")

        self._installer = PluginInstaller(plugin_meta)
        self._installer.progress.connect(self._install_progress.setValue)
        self._installer.log.connect(lambda msg, lvl: self._install_lbl.setText(msg))
        self._installer.done.connect(self._on_install_done)
        self._installer.start()

    def _on_install_done(self, success: bool, message: str):
        self._install_lbl.setText(("✓  " if success else "X  ") + message)
        if success:
            QTimer.singleShot(2000, lambda: self.footer.setVisible(False))
            self._render_cards()
            if callable(self._install_done_hook):
                self._install_done_hook()

    def _do_review(self, plugin_meta: dict):
        dlg = ReviewDialog(plugin_meta["id"], plugin_meta["name"], parent=self)
        if dlg.exec():
            self._render_cards()