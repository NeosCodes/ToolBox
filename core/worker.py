from PyQt6.QtCore import QThread, pyqtSignal
from typing import List
from core.plugin_base import PluginBase


class WorkerThread(QThread):
    progress = pyqtSignal(int)
    log      = pyqtSignal(str, str)
    done     = pyqtSignal(bool, str)

    def __init__(self, plugin: PluginBase, input_files: List[str], output_dir: str):
        super().__init__()
        self.plugin = plugin
        self.input_files = input_files
        self.output_dir = output_dir

    def run(self):
        self.plugin._cancelled = False
        self.plugin.set_callbacks(
            progress_cb=lambda v: self.progress.emit(v),
            log_cb=lambda msg, lvl: self.log.emit(msg, lvl),
            done_cb=lambda ok, msg: self.done.emit(ok, msg),
        )
        try:
            self.plugin.run(self.input_files, self.output_dir)
        except Exception as e:
            self.done.emit(False, str(e))