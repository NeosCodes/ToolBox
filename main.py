import sys
import os
from PyQt6.QtWidgets import QApplication, QSplashScreen
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QPixmap, QColor, QPainter, QFont, QIcon

_ASSETS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets")


def _asset(name: str) -> str:
    return os.path.join(_ASSETS, name)

from core.updater import AppUpdateChecker, APP_VERSION
from core.onboarding import (
    OnboardingDialog, UpdateNotificationDialog,
    is_first_run, load_prefs,
)
from core.window import MainWindow


def make_splash() -> QSplashScreen:
    splash_path = _asset("splash.png")
    if os.path.exists(splash_path):
        px = QPixmap(splash_path)
        return QSplashScreen(px, Qt.WindowType.WindowStaysOnTopHint)

    px = QPixmap(420, 180)
    px.fill(QColor("#1a1a1a"))
    painter = QPainter(px)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)
    painter.setPen(QColor("#2a2a2a"))
    painter.setBrush(QColor("#1a1a1a"))
    painter.drawRoundedRect(0, 0, 420, 180, 12, 12)
    font = QFont("Segoe UI", 26, QFont.Weight.Bold)
    painter.setFont(font)
    painter.setPen(QColor("#e8e8e8"))
    painter.drawText(32, 96, "Neo")
    painter.setPen(QColor("#7c6af7"))
    painter.drawText(110, 96, "Toolbox")
    font2 = QFont("Segoe UI", 11)
    painter.setFont(font2)
    painter.setPen(QColor("#555"))
    painter.drawText(32, 126, f"v{APP_VERSION}  ·  Loading…")
    painter.end()
    return QSplashScreen(px, Qt.WindowType.WindowStaysOnTopHint)


def main():
    os.makedirs(os.path.join(os.path.expanduser("~"), "ToolBox_Output"), exist_ok=True)

    app = QApplication(sys.argv)
    app.setApplicationName("ToolBox")
    app.setApplicationVersion(APP_VERSION)

    for icon_file in ("icon.ico", "icon.png"):
        p = _asset(icon_file)
        if os.path.exists(p):
            app.setWindowIcon(QIcon(p))
            break

    splash = make_splash()
    splash.show()
    app.processEvents()

    window = MainWindow()

    def launch_window(output_dir: str = ""):
        if output_dir:
            window.output_dir = output_dir
        splash.finish(window)
        window.show()

    def run_onboarding(update_version="", url="", notes=""):
        dlg = OnboardingDialog(update_version=update_version,
                               download_url=url, release_notes=notes)
        dlg.finished_setup.connect(launch_window)
        splash.hide()
        if not dlg.exec():
            launch_window(load_prefs().get("output_dir", ""))

    def on_update_available(version, url, notes):
        if is_first_run():
            run_onboarding(version, url, notes)
        else:
            prefs = load_prefs()
            if prefs.get("skip_version") == version:
                launch_window(prefs.get("output_dir", ""))
                return
            dlg = UpdateNotificationDialog(version, url, notes)
            dlg.finished.connect(lambda: (
                launch_window(prefs.get("output_dir", ""))
                if not window.isVisible() else None
            ))
            splash.hide()
            dlg.exec()
            if not window.isVisible():
                launch_window(prefs.get("output_dir", ""))

    def on_no_update(_=""):
        if is_first_run():
            run_onboarding()
        else:
            launch_window(load_prefs().get("output_dir", ""))

    checker = AppUpdateChecker()
    checker.update_available.connect(on_update_available)
    checker.up_to_date.connect(on_no_update)
    checker.error.connect(on_no_update)
    checker.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()