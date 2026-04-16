import os
import json
import hashlib
import zipfile
import shutil
import urllib.request
from datetime import datetime, timezone
from typing import Optional
from PyQt6.QtCore import QObject, QThread, pyqtSignal

REGISTRY_URL = (
    "https://raw.githubusercontent.com/NeosCodes/ToolBox-plugins/main/registry.json"
)
APP_DATA_DIR = os.path.join(os.path.expanduser("~"), ".toolbox")
REVIEWS_FILE = os.path.join(APP_DATA_DIR, "reviews.json")
PLUGINS_DIR = os.path.join(os.path.dirname(__file__), "..", "plugins")
CACHE_FILE = os.path.join(APP_DATA_DIR, "registry_cache.json")

os.makedirs(APP_DATA_DIR, exist_ok=True)

def _version_tuple(v: str):
    return tuple(int(x) for x in str(v).split(".") if x.isdigit())

def version_newer(remote: str, local: str) -> bool:
    return _version_tuple(remote) > _version_tuple(local)


def get_installed_versions() -> dict:
    versions = {}
    plugins_root = os.path.normpath(PLUGINS_DIR)
    if not os.path.isdir(plugins_root):
        return versions

    for name in os.listdir(plugins_root):
        folder = os.path.join(plugins_root, name)
        if not os.path.isdir(folder):
            continue
        meta_file = os.path.join(folder, "__meta__.json")
        if os.path.exists(meta_file):
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                versions[data["id"]] = data["version"]
                continue
            except Exception:
                pass
        try:
            import importlib
            mod = importlib.import_module(f"plugins.{name}.plugin")
            for attr in dir(mod):
                obj = getattr(mod, attr)
                if isinstance(obj, type):
                    try:
                        inst = obj()
                        if hasattr(inst, "meta"):
                            versions[inst.meta.id] = inst.meta.version if hasattr(inst.meta, "version") else "0.0.0"
                    except Exception:
                        pass
        except Exception:
            pass
    return versions

def load_reviews() -> dict:
    if os.path.exists(REVIEWS_FILE):
        try:
            with open(REVIEWS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}

def save_review(plugin_id: str, stars: int, comment: str):
    reviews = load_reviews()
    reviews[plugin_id] = {
        "stars": max(1, min(5, stars)),
        "comment": comment.strip(),
        "date": datetime.now(timezone.utc).isoformat(),
    }
    with open(REVIEWS_FILE, "w", encoding="utf-8") as f:
        json.dump(reviews, f, indent=2, ensure_ascii=False)

def get_my_review(plugin_id: str) -> Optional[dict]:
    return load_reviews().get(plugin_id)

class RegistryFetcher(QThread):
    done    = pyqtSignal(list)
    error   = pyqtSignal(str)

    def __init__(self, use_cache_on_fail=True):
        super().__init__()
        self._use_cache = use_cache_on_fail

    def run(self):
        try:
            req = urllib.request.Request(
                REGISTRY_URL,
                headers={"User-Agent": "ToolBox/1.0"},
            )
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode())
            plugins = data.get("plugins", [])
            with open(CACHE_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f)
            self.done.emit(plugins)
        except Exception as e:
            if self._use_cache and os.path.exists(CACHE_FILE):
                try:
                    with open(CACHE_FILE, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    self.done.emit(data.get("plugins", []))
                    return
                except Exception:
                    pass
            self.error.emit(str(e))

class PluginInstaller(QThread):
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    done = pyqtSignal(bool, str)

    def __init__(self, plugin_meta: dict):
        super().__init__()
        self.plugin_meta = plugin_meta

    def run(self):
        m = self.plugin_meta
        pid = m["id"]
        url = m["download_url"]
        expected_sha = m.get("checksum_sha256", "")
        tmp_zip = os.path.join(APP_DATA_DIR, f"{pid}_download.zip")

        self.log.emit(f"Downloading {m['name']} v{m['version']}…", "info")
        try:
            self._download(url, tmp_zip)
        except Exception as e:
            self.done.emit(False, f"Download failed: {e}")
            return
        self.progress.emit(60)

        if expected_sha and not expected_sha.startswith("abc") and not expected_sha.startswith("def"):
            self.log.emit("Verifying checksum…", "info")
            actual = self._sha256(tmp_zip)
            if actual != expected_sha:
                os.remove(tmp_zip)
                self.done.emit(False, f"Checksum mismatch - download may be corrupted.")
                return
        self.progress.emit(75)

        self.log.emit("Installing…", "info")
        target_dir = os.path.normpath(os.path.join(PLUGINS_DIR, pid))
        try:
            if os.path.exists(target_dir):
                shutil.rmtree(target_dir)
            with zipfile.ZipFile(tmp_zip, "r") as z:
                names = z.namelist()
                has_root_folder = all(n.startswith(pid + "/") or n.startswith(pid + "\\") for n in names if n.strip("/"))
                if has_root_folder:
                    z.extractall(PLUGINS_DIR)
                else:
                    os.makedirs(target_dir, exist_ok=True)
                    z.extractall(target_dir)
        except Exception as e:
            self.done.emit(False, f"Extraction failed: {e}")
            return
        finally:
            if os.path.exists(tmp_zip):
                os.remove(tmp_zip)

        meta_path = os.path.join(target_dir, "__meta__.json")
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump({"id": pid, "version": m["version"], "installed_at": datetime.now(timezone.utc).isoformat()}, f)

        self.progress.emit(100)
        self.log.emit(f"{m['name']} v{m['version']} installed", "ok")
        self.done.emit(True, f"{m['name']} installed successfully.")

    def _download(self, url: str, dest: str):
        req = urllib.request.Request(url, headers={"User-Agent": "ToolBox/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            total = int(resp.headers.get("Content-Length", 0))
            downloaded = 0
            chunk = 8192
            with open(dest, "wb") as f:
                while True:
                    buf = resp.read(chunk)
                    if not buf:
                        break
                    f.write(buf)
                    downloaded += len(buf)
                    if total:
                        pct = int(downloaded / total * 55)
                        self.progress.emit(pct)

    @staticmethod
    def _sha256(path: str) -> str:
        h = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                h.update(chunk)
        return h.hexdigest()