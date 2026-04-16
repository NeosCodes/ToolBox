import os
import sys
import json
import subprocess
from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QWidget, QStackedWidget, QProgressBar, QTextEdit,
    QCheckBox, QFileDialog, QFrame,
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QPixmap

from core.updater import APP_VERSION, AppUpdater
from core.assets import icon_label

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")

APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".toolbox")
PREFS_FILE   = os.path.join(APP_DATA_DIR, "prefs.json")
os.makedirs(APP_DATA_DIR, exist_ok=True)

def load_prefs() -> dict:
    if os.path.exists(PREFS_FILE):
        try:
            with open(PREFS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_prefs(prefs: dict):
    with open(PREFS_FILE, "w", encoding="utf-8") as f:
        json.dump(prefs, f, indent=2)

def is_first_run() -> bool:
    return not load_prefs().get("onboarding_done", False)

def mark_onboarding_done():
    p = load_prefs()
    p["onboarding_done"] = True
    save_prefs(p)

def _h(text: str, size: int = 22) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: {size}px; font-weight: 600; color: #e8e8e8; letter-spacing: -0.02em;")
    lbl.setWordWrap(True)
    return lbl

def _p(text: str, color: str = "#888") -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(f"font-size: 13px; color: {color}; line-height: 1.6;")
    lbl.setWordWrap(True)
    return lbl

def _sep() -> QFrame:
    f = QFrame()
    f.setFrameShape(QFrame.Shape.HLine)
    f.setStyleSheet("color: #2a2a2a; background: #2a2a2a; max-height: 1px; border: none;")
    return f

def _pill(text: str, color: str) -> QLabel:
    lbl = QLabel(text)
    lbl.setStyleSheet(
        f"font-size: 11px; font-weight: 600; color: {color}; "
        f"background: {color}22; border-radius: 4px; padding: 2px 8px;"
    )
    return lbl

class WelcomePage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(16)

        logo_row = QHBoxLayout()
        _logo_path = os.path.join(_ASSETS, "logo.png")
        if os.path.exists(_logo_path):
            logo = QLabel()
            logo.setPixmap(
                QPixmap(_logo_path).scaledToHeight(40, Qt.TransformationMode.SmoothTransformation)
            )
        else:
            logo = QLabel("Tool<span style='color:#7c6af7'>Box</span>")
            logo.setTextFormat(Qt.TextFormat.RichText)
            logo.setStyleSheet("font-size: 28px; font-weight: 700; letter-spacing: -0.03em;")
        logo_row.addWidget(logo)
        logo_row.addStretch()
        ver = QLabel(f"v{APP_VERSION}")
        ver.setStyleSheet("font-size: 12px; color: #555; margin-top: 6px;")
        logo_row.addWidget(ver)
        layout.addLayout(logo_row)

        layout.addWidget(_h("Welcome to ToolBox", 20))
        layout.addWidget(_p(
            "A modular, privacy-first file toolkit that runs entirely on your machine. "
            "No cloud. No telemetry. Just tools."
        ))

        layout.addWidget(_sep())

        features = [
            ("images", "🖼", "#4A8FE7", "Images", "Convert, resize, batch-rename"),
            ("video", "▶",  "#E24B4A", "Video", "Convert with ffmpeg"),
            ("pdf", "📄", "#E07A3A", "PDF", "Merge, split, extract"),
            ("documents", "📝", "#5BA85B", "Documents", "DOCX, XLSX, Markdown"),
            ("audio", "🎵", "#9B6FD4", "Audio", "MP3, FLAC, WAV and more"),
        ]
        grid = QWidget()
        grid_layout = QVBoxLayout(grid)
        grid_layout.setContentsMargins(0, 0, 0, 0)
        grid_layout.setSpacing(8)

        for asset, emoji, color, name, desc in features:
            row = QHBoxLayout()
            icon_lbl = icon_label(asset, emoji, 24)
            icon_lbl.setFixedSize(32, 32)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet(
                f"font-size: 16px; background: {color}22; "
                f"border-radius: 8px;"
            )
            row.addWidget(icon_lbl)
            text_col = QVBoxLayout()
            text_col.setSpacing(0)
            name_lbl = QLabel(name)
            name_lbl.setStyleSheet("font-size: 13px; font-weight: 500; color: #ddd;")
            desc_lbl = QLabel(desc)
            desc_lbl.setStyleSheet("font-size: 11px; color: #666;")
            text_col.addWidget(name_lbl)
            text_col.addWidget(desc_lbl)
            row.addLayout(text_col)
            row.addStretch()
            grid_layout.addLayout(row)

        layout.addWidget(grid)
        layout.addStretch()


class OutputPage(QWidget):
    def __init__(self):
        super().__init__()
        self._output_dir = os.path.join(os.path.expanduser("~"), "ToolBox_Output")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(_h("Where should output files go?"))
        layout.addWidget(_p(
            "Converted files are saved here by default. "
            "You can always change this per-session inside the app."
        ))
        layout.addWidget(_sep())

        dir_row = QHBoxLayout()
        self.dir_lbl = QLabel(self._output_dir)
        self.dir_lbl.setStyleSheet(
            "font-size: 12px; color: #888; background: #212121; "
            "border: 1px solid #2a2a2a; border-radius: 6px; padding: 8px 12px;"
        )
        self.dir_lbl.setWordWrap(True)
        dir_row.addWidget(self.dir_lbl, 1)

        browse_btn = QPushButton("Browse")
        browse_btn.setObjectName("secondary_btn")
        browse_btn.setFixedWidth(90)
        browse_btn.clicked.connect(self._browse)
        dir_row.addWidget(browse_btn)
        layout.addLayout(dir_row)

        self.create_lbl = QLabel("")
        self.create_lbl.setStyleSheet("font-size: 11px; color: #5fbc85;")
        layout.addWidget(self.create_lbl)
        layout.addStretch()

        os.makedirs(self._output_dir, exist_ok=True)
        self.create_lbl.setText(f"Folder ready")

    def _browse(self):
        path = QFileDialog.getExistingDirectory(self, "Choose output folder", self._output_dir)
        if path:
            self._output_dir = path
            self.dir_lbl.setText(path)
            os.makedirs(path, exist_ok=True)
            self.create_lbl.setText("Folder ready")

    @property
    def output_dir(self):
        return self._output_dir


class DependenciesPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(_h("Check dependencies"))
        layout.addWidget(_p(
            "ToolBox uses a few system tools and Python packages. "
            "Here's what was found on your machine."
        ))
        layout.addWidget(_sep())

        self.checks_layout = QVBoxLayout()
        self.checks_layout.setSpacing(8)
        layout.addLayout(self.checks_layout)
        layout.addStretch()

        QTimer.singleShot(100, self._run_checks)

    def _run_checks(self):
        checks = [
            ("Python", self._check_python()),
            ("Pillow (images)", self._check_import("PIL")),
            ("pypdf (PDF tools)", self._check_import("pypdf")),
            ("python-docx", self._check_import("docx")),
            ("openpyxl", self._check_import("openpyxl")),
            ("ffmpeg (video/audio)", self._check_ffmpeg()),
        ]
        for name, (ok, detail) in checks:
            self._add_row(name, ok, detail)

    def _add_row(self, name: str, ok: bool, detail: str):
        row = QHBoxLayout()
        status = icon_label("check" if ok else "error", "✓" if ok else "✗", 16)
        status.setFixedWidth(20)
        if not status.pixmap():
            status.setStyleSheet(f"font-size: 14px; color: {'#5fbc85' if ok else '#e05c5c'};")
        row.addWidget(status)

        name_lbl = QLabel(name)
        name_lbl.setStyleSheet("font-size: 13px; color: #ccc;")
        name_lbl.setFixedWidth(180)
        row.addWidget(name_lbl)

        detail_lbl = QLabel(detail)
        detail_lbl.setStyleSheet(f"font-size: 11px; color: {'#555' if ok else '#a05050'};")
        row.addWidget(detail_lbl)
        row.addStretch()
        self.checks_layout.addLayout(row)

    @staticmethod
    def _check_python():
        v = sys.version.split()[0]
        ok = tuple(int(x) for x in v.split(".")[:2]) >= (3, 10)
        return ok, f"Python {v}"

    @staticmethod
    def _check_import(mod: str):
        try:
            __import__(mod)
            import importlib.metadata
            try:
                ver = importlib.metadata.version(mod)
                return True, f"v{ver}"
            except Exception:
                return True, "installed"
        except ImportError:
            return False, f"not found — run: pip install {mod}"

    @staticmethod
    def _check_ffmpeg():
        try:
            r = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=5)
            if r.returncode == 0:
                line = r.stdout.splitlines()[0]
                ver = line.split("version ")[-1].split(" ")[0] if "version " in line else "found"
                return True, ver
        except Exception:
            pass
        return False, "not found - install from ffmpeg.org and add to PATH"


class UpdatesPage(QWidget):
    def __init__(self, update_version: str = "", release_notes: str = ""):
        super().__init__()
        self._update_version = update_version
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(16)

        if update_version:
            layout.addWidget(_h("Update available 🎉", 20))
            layout.addWidget(_p(
                f"ToolBox {update_version} is ready to download. "
                f"You're currently on v{APP_VERSION}."
            ))
            layout.addWidget(_sep())

            notes_lbl = QLabel("What's new:")
            notes_lbl.setStyleSheet("font-size: 12px; color: #666; font-weight: 500;")
            layout.addWidget(notes_lbl)

            notes = QTextEdit()
            notes.setReadOnly(True)
            notes.setPlainText(release_notes or "No release notes provided.")
            notes.setMaximumHeight(140)
            notes.setStyleSheet(
                "background: #141414; border: 1px solid #2a2a2a; "
                "border-radius: 8px; color: #888; font-size: 12px; padding: 8px;"
            )
            layout.addWidget(notes)

            self.remind_cb = QCheckBox("Remind me later (skip this update)")
            self.remind_cb.setStyleSheet("font-size: 12px; color: #666;")
            layout.addWidget(self.remind_cb)
        else:
            layout.addWidget(_h("You're up to date", 20))
            layout.addWidget(_p(
                f"ToolBox v{APP_VERSION} is the latest version."
            ))
            layout.addStretch()

        layout.addStretch()

    @property
    def skip_update(self) -> bool:
        return hasattr(self, "remind_cb") and self.remind_cb.isChecked()


class _ShopReadyPage(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 10, 0, 0)
        layout.setSpacing(16)

        layout.addWidget(_h("You're all set! 🎉", 20))
        layout.addWidget(_p(
            "ToolBox ships without any plugins — each tool is installed "
            "separately so you only get what you actually need."
        ))
        layout.addWidget(_sep())

        steps = [
            ("shop",     "🛒", "Open the Plugin Shop from the sidebar"),
            ("download", "⬇",  "Install any plugins you need — Image Converter, PDF Tools, etc."),
            ("play",     "▶",  "Drop your files and start converting"),
        ]
        for asset, emoji, text in steps:
            row = QHBoxLayout()
            icon_lbl = icon_label(asset, emoji, 24)
            icon_lbl.setFixedSize(32, 32)
            icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            icon_lbl.setStyleSheet(
                "font-size: 16px; background: #7c6af722; border-radius: 8px;"
            )
            row.addWidget(icon_lbl)
            text_lbl = QLabel(text)
            text_lbl.setStyleSheet("font-size: 13px; color: #aaa;")
            row.addWidget(text_lbl, 1)
            layout.addLayout(row)

        layout.addStretch()

class OnboardingDialog(QDialog):
    finished_setup = pyqtSignal(str)

    def __init__(self, update_version: str = "", download_url: str = "",
                 release_notes: str = "", parent=None):
        super().__init__(parent)
        self._update_version = update_version
        self._download_url   = download_url
        self._updater: AppUpdater | None = None

        self.setWindowTitle("ToolBox Setup")
        self.setFixedSize(520, 560)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QWidget { background: #1a1a1a; color: #e8e8e8; font-family: 'Segoe UI', system-ui, sans-serif; }
            QPushButton#run_btn { background-color:#7c6af7; color:#fff; border:none; border-radius:8px; padding:9px 22px; font-size:13px; font-weight:600; min-width:110px; }
            QPushButton#run_btn:hover { background-color:#8b7af8; }
            QPushButton#run_btn:disabled { background:#2a2a2a; color:#555; }
            QPushButton#secondary_btn { background:transparent; color:#888; border:1px solid #333; border-radius:8px; padding:9px 16px; font-size:12px; }
            QPushButton#secondary_btn:hover { background:#252525; color:#ccc; border-color:#444; }
            QScrollBar:vertical { background:transparent; width:6px; }
            QScrollBar::handle:vertical { background:#333; border-radius:3px; }
            QCheckBox { color:#888; spacing:8px; }
            QCheckBox::indicator { width:16px; height:16px; border-radius:4px; border:1px solid #444; background:#252525; }
            QCheckBox::indicator:checked { background:#7c6af7; border-color:#7c6af7; }
        """)

        self._build_pages(update_version, release_notes)
        self._build_chrome()

    def _build_pages(self, update_version, release_notes):
        self.page_welcome = WelcomePage()
        self.page_output = OutputPage()
        self.page_deps = DependenciesPage()
        self.page_updates = UpdatesPage(update_version, release_notes)
        self.page_shop = _ShopReadyPage()

        self._pages = [
            self.page_welcome,
            self.page_output,
            self.page_deps,
            self.page_updates,
            self.page_shop,
        ]
        self._titles = [
            "Welcome",
            "Output folder",
            "Dependencies",
            "Updates",
            "Get plugins",
        ]

    def _build_chrome(self):
        root = QVBoxLayout(self)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        dots_bar = QWidget()
        dots_bar.setFixedHeight(44)
        dots_bar.setStyleSheet("background: #141414; border-bottom: 1px solid #222;")
        dots_layout = QHBoxLayout(dots_bar)
        dots_layout.setContentsMargins(24, 0, 24, 0)

        self._dot_labels = []
        for i, title in enumerate(self._titles):
            col = QVBoxLayout()
            col.setSpacing(2)
            col.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot = QLabel("●")
            dot.setAlignment(Qt.AlignmentFlag.AlignCenter)
            dot.setStyleSheet("font-size: 8px; color: #333;")
            lbl = QLabel(title)
            lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
            lbl.setStyleSheet("font-size: 9px; color: #444; letter-spacing: 0.04em;")
            col.addWidget(dot)
            col.addWidget(lbl)
            self._dot_labels.append((dot, lbl))
            dots_layout.addLayout(col)
            if i < len(self._titles) - 1:
                line = QLabel("──")
                line.setStyleSheet("color: #2a2a2a; font-size: 10px;")
                line.setAlignment(Qt.AlignmentFlag.AlignCenter)
                dots_layout.addWidget(line, 1)

        root.addWidget(dots_bar)

        self.stack = QStackedWidget()
        for page in self._pages:
            self.stack.addWidget(page)
        content = QWidget()
        cl = QVBoxLayout(content)
        cl.setContentsMargins(32, 24, 32, 16)
        cl.addWidget(self.stack)
        root.addWidget(content, 1)

        bottom = QWidget()
        bottom.setFixedHeight(64)
        bottom.setStyleSheet("background: #141414; border-top: 1px solid #222;")
        bl = QHBoxLayout(bottom)
        bl.setContentsMargins(24, 0, 24, 0)

        self.back_btn = QPushButton("← Back")
        self.back_btn.setObjectName("secondary_btn")
        self.back_btn.clicked.connect(self._go_back)
        self.back_btn.setVisible(False)
        bl.addWidget(self.back_btn)
        bl.addStretch()

        self.skip_btn = QPushButton("Skip setup")
        self.skip_btn.setObjectName("secondary_btn")
        self.skip_btn.clicked.connect(self._skip)
        bl.addWidget(self.skip_btn)

        self.next_btn = QPushButton("Next →")
        self.next_btn.setObjectName("run_btn")
        self.next_btn.clicked.connect(self._go_next)
        bl.addWidget(self.next_btn)

        root.addWidget(bottom)

        self._current = 0
        self._refresh_nav()

    def _refresh_nav(self):
        i = self._current
        n = len(self._pages)

        self.stack.setCurrentIndex(i)
        self.back_btn.setVisible(i > 0)

        is_last = (i == n - 1)
        is_update_page = (self._pages[i] is self.page_updates)
        has_update = bool(self._update_version)

        if is_update_page and has_update and not self.page_updates.skip_update:
            self.next_btn.setText("Download update")
            self.next_btn.setStyleSheet(
                "QPushButton#run_btn { background-color: #3a8a5a; }"
                "QPushButton#run_btn:hover { background-color: #4aa06a; }"
            )
        elif is_last:
            self.next_btn.setText("Open Plugin Shop →")
            self.next_btn.setStyleSheet("")
            self.skip_btn.setVisible(False)
        else:
            self.next_btn.setText("Next →")
            self.next_btn.setStyleSheet("")
            self.skip_btn.setVisible(True)

        for j, (dot, lbl) in enumerate(self._dot_labels):
            if j < i:
                dot.setStyleSheet("font-size: 8px; color: #7c6af7;")
                lbl.setStyleSheet("font-size: 9px; color: #7c6af7;")
            elif j == i:
                dot.setStyleSheet("font-size: 10px; color: #7c6af7;")
                lbl.setStyleSheet("font-size: 9px; color: #ccc; font-weight: 600;")
            else:
                dot.setStyleSheet("font-size: 8px; color: #333;")
                lbl.setStyleSheet("font-size: 9px; color: #444;")

    def _go_next(self):
        is_last        = (self._current == len(self._pages) - 1)
        is_update_page = (self._pages[self._current] is self.page_updates)
        has_update     = bool(self._update_version)

        if is_update_page and has_update and not self.page_updates.skip_update:
            self._start_download()
            return

        if is_last:
            self._finish()
            return

        self._current += 1
        self._refresh_nav()

    def _go_back(self):
        if self._current > 0:
            self._current -= 1
            self._refresh_nav()

    def _skip(self):
        self._finish()

    def _finish(self):
        mark_onboarding_done()
        p = load_prefs()
        p["output_dir"] = self.page_output.output_dir
        save_prefs(p)
        self.finished_setup.emit(self.page_output.output_dir)
        self.accept()

    def _start_download(self):
        self.next_btn.setEnabled(False)
        self.next_btn.setText("Downloading…")
        self.back_btn.setEnabled(False)
        self.skip_btn.setEnabled(False)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setStyleSheet(
            "QProgressBar { background:#252525; border:none; border-radius:3px; }"
            "QProgressBar::chunk { background:#3a8a5a; border-radius:3px; }"
        )
        self._dl_lbl = QLabel("Preparing download…")
        self._dl_lbl.setStyleSheet("font-size: 12px; color: #888;")

        layout = self.page_updates.layout()
        layout.addWidget(self._dl_lbl)
        layout.addWidget(self._progress_bar)

        self._updater = AppUpdater(self._update_version, self._download_url)
        self._updater.progress.connect(self._progress_bar.setValue)
        self._updater.log.connect(lambda msg, _: self._dl_lbl.setText(msg))
        self._updater.done.connect(self._on_download_done)
        self._updater.start()

    def _on_download_done(self, success: bool, path_or_error: str):
        if success:
            self._dl_lbl.setText("✓  Download complete. Launching installer…")
            QTimer.singleShot(800, lambda: self._launch_and_finish(path_or_error))
        else:
            self._dl_lbl.setText(f"✗  {path_or_error}")
            self._dl_lbl.setStyleSheet("font-size: 12px; color: #e05c5c;")
            self.next_btn.setEnabled(True)
            self.next_btn.setText("Skip and continue")
            self.back_btn.setEnabled(True)
            self.skip_btn.setEnabled(True)

    def _launch_and_finish(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
        self._finish()

class UpdateNotificationDialog(QDialog):
    def __init__(self, version: str, download_url: str,
                 release_notes: str, parent=None):
        super().__init__(parent)
        self._version      = version
        self._download_url = download_url
        self._updater: AppUpdater | None = None

        self.setWindowTitle("Update available")
        self.setFixedSize(460, 360)
        self.setWindowFlags(Qt.WindowType.Dialog | Qt.WindowType.WindowCloseButtonHint)
        self.setStyleSheet("""
            QDialog { background: #1a1a1a; }
            QWidget { background: #1a1a1a; color: #e8e8e8; font-family: 'Segoe UI', system-ui, sans-serif; }
            QPushButton#run_btn { background-color:#7c6af7; color:#fff; border:none; border-radius:8px; padding:9px 22px; font-size:13px; font-weight:600; min-width:130px; }
            QPushButton#run_btn:hover { background-color:#8b7af8; }
            QPushButton#run_btn:disabled { background:#2a2a2a; color:#555; }
            QPushButton#secondary_btn { background:transparent; color:#888; border:1px solid #333; border-radius:8px; padding:9px 16px; font-size:12px; }
            QPushButton#secondary_btn:hover { background:#252525; color:#ccc; }
        """)

        root = QVBoxLayout(self)
        root.setContentsMargins(28, 24, 28, 20)
        root.setSpacing(14)

        hdr = QHBoxLayout()
        icon = QLabel("🚀")
        icon.setStyleSheet("font-size: 28px;")
        hdr.addWidget(icon)
        title_col = QVBoxLayout()
        title_col.setSpacing(2)
        title_lbl = QLabel(f"ToolBox {version} is available")
        title_lbl.setStyleSheet("font-size: 16px; font-weight: 600; color: #e8e8e8;")
        sub_lbl   = QLabel(f"You have v{APP_VERSION} installed")
        sub_lbl.setStyleSheet("font-size: 12px; color: #666;")
        title_col.addWidget(title_lbl)
        title_col.addWidget(sub_lbl)
        hdr.addLayout(title_col, 1)
        root.addLayout(hdr)

        sep = QFrame()
        sep.setFrameShape(QFrame.Shape.HLine)
        sep.setStyleSheet("color: #2a2a2a; background: #2a2a2a; max-height: 1px; border: none;")
        root.addWidget(sep)

        notes_lbl = QLabel("What's new:")
        notes_lbl.setStyleSheet("font-size: 12px; color: #666; font-weight: 500;")
        root.addWidget(notes_lbl)

        notes = QTextEdit()
        notes.setReadOnly(True)
        notes.setPlainText(release_notes or "No release notes provided.")
        notes.setStyleSheet(
            "background: #141414; border: 1px solid #2a2a2a; border-radius: 8px; "
            "color: #888; font-size: 12px; padding: 8px;"
        )
        root.addWidget(notes, 1)

        self._progress_bar = QProgressBar()
        self._progress_bar.setRange(0, 100)
        self._progress_bar.setFixedHeight(6)
        self._progress_bar.setVisible(False)
        self._progress_bar.setStyleSheet(
            "QProgressBar { background:#252525; border:none; border-radius:3px; }"
            "QProgressBar::chunk { background:#7c6af7; border-radius:3px; }"
        )
        self._progress_lbl = QLabel("")
        self._progress_lbl.setStyleSheet("font-size: 11px; color: #666;")
        self._progress_lbl.setVisible(False)
        root.addWidget(self._progress_bar)
        root.addWidget(self._progress_lbl)

        btn_row = QHBoxLayout()
        remind_btn = QPushButton("Remind me later")
        remind_btn.setObjectName("secondary_btn")
        remind_btn.clicked.connect(self.reject)
        btn_row.addWidget(remind_btn)
        btn_row.addStretch()

        self.skip_ver_cb = QCheckBox("Skip this version")
        self.skip_ver_cb.setStyleSheet("font-size: 12px; color: #555;")
        btn_row.addWidget(self.skip_ver_cb)

        self.download_btn = QPushButton("Download update")
        self.download_btn.setObjectName("run_btn")
        self.download_btn.clicked.connect(self._start_download)
        btn_row.addWidget(self.download_btn)

        root.addLayout(btn_row)

    def _start_download(self):
        self.download_btn.setEnabled(False)
        self.download_btn.setText("Downloading…")
        self._progress_bar.setVisible(True)
        self._progress_lbl.setVisible(True)
        self._progress_lbl.setText("Starting download…")

        self._updater = AppUpdater(self._version, self._download_url)
        self._updater.progress.connect(self._progress_bar.setValue)
        self._updater.log.connect(lambda msg, _: self._progress_lbl.setText(msg))
        self._updater.done.connect(self._on_done)
        self._updater.start()

    def _on_done(self, success: bool, path_or_error: str):
        if success:
            self._progress_lbl.setText("Launching installer…")
            if self.skip_ver_cb.isChecked():
                p = load_prefs()
                p["skip_version"] = self._version
                save_prefs(p)
            QTimer.singleShot(800, lambda: self._launch(path_or_error))
        else:
            self._progress_lbl.setText(f"{path_or_error}")
            self._progress_lbl.setStyleSheet("font-size: 11px; color: #e05c5c;")
            self.download_btn.setEnabled(True)
            self.download_btn.setText("Retry")

    def _launch(self, path: str):
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":
                subprocess.Popen(["open", path])
            else:
                subprocess.Popen(["xdg-open", path])
        except Exception:
            pass
        self.accept()