import os
import sys
import json
import urllib.request
import subprocess
import tempfile

from PyQt6.QtCore import QThread, pyqtSignal


APP_VERSION = "1.0.0"
GITHUB_REPO = "NeosCodes/ToolBox"

RELEASES_API = f"https://api.github.com/repos/{GITHUB_REPO}/releases/latest"

APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".toolbox")
os.makedirs(APP_DATA_DIR, exist_ok=True)


def _version_tuple(v: str):
    return tuple(int(x) for x in str(v).lstrip("v").split(".") if x.isdigit())

def is_newer(remote: str, local: str) -> bool:
    return _version_tuple(remote) > _version_tuple(local)

class AppUpdateChecker(QThread):
    update_available = pyqtSignal(str, str, str)
    up_to_date       = pyqtSignal(str)
    error            = pyqtSignal(str)

    def run(self):
        try:
            req = urllib.request.Request(
                RELEASES_API,
                headers={
                    "User-Agent": f"ToolBox/{APP_VERSION}",
                    "Accept": "application/vnd.github+json",
                },
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())

            latest_tag   = data.get("tag_name", "").lstrip("v")
            release_notes = data.get("body", "No release notes available.")
            assets        = data.get("assets", [])

            platform_keyword = {
                "win32":  ".exe",
                "darwin": ".dmg",
            }.get(sys.platform, ".tar.gz")

            download_url = ""
            for asset in assets:
                if asset["name"].endswith(platform_keyword):
                    download_url = asset["browser_download_url"]
                    break
            if not download_url:
                for asset in assets:
                    if asset["name"].endswith(".zip"):
                        download_url = asset["browser_download_url"]
                        break

            if latest_tag and is_newer(latest_tag, APP_VERSION):
                self.update_available.emit(latest_tag, download_url, release_notes)
            else:
                self.up_to_date.emit(APP_VERSION)

        except Exception as e:
            self.error.emit(str(e))

class AppUpdater(QThread):
    progress = pyqtSignal(int)
    log      = pyqtSignal(str, str)
    done     = pyqtSignal(bool, str)

    def __init__(self, version: str, download_url: str):
        super().__init__()
        self.version = version
        self.download_url = download_url

    def run(self):
        if not self.download_url:
            self.done.emit(False, "No download URL found for this platform.")
            return

        ext = os.path.splitext(self.download_url)[-1] or ".zip"
        dest = os.path.join(APP_DATA_DIR, f"ToolBox-{self.version}{ext}")

        self.log.emit(f"Downloading ToolBox {self.version}…", "info")
        try:
            req = urllib.request.Request(
                self.download_url,
                headers={"User-Agent": f"ToolBox/{APP_VERSION}"},
            )
            with urllib.request.urlopen(req, timeout=120) as resp:
                total = int(resp.headers.get("Content-Length", 0))
                downloaded = 0
                with open(dest, "wb") as f:
                    while True:
                        chunk = resp.read(8192)
                        if not chunk:
                            break
                        f.write(chunk)
                        downloaded += len(chunk)
                        if total:
                            self.progress.emit(int(downloaded / total * 100))
        except Exception as e:
            self.done.emit(False, f"Download failed: {e}")
            return

        self.progress.emit(100)
        self.log.emit("Download complete. Launching installer…", "ok")
        self.done.emit(True, dest)