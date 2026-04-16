from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import List
from PyQt6.QtWidgets import QWidget

@dataclass
class PluginMeta:
    id: str
    name: str
    description: str
    category: str
    icon_char: str
    accent_color: str
    supported_inputs: List[str]
    supported_outputs: List[str]
    requires: List[str] = field(default_factory=list)
    icon_name: str = ""


class PluginBase(ABC):
    def __init__(self):
        self._progress_cb = None
        self._log_cb = None
        self._done_cb = None
        self._cancelled = False

    def set_callbacks(self, progress_cb, log_cb, done_cb):
        self._progress_cb = progress_cb
        self._log_cb = log_cb
        self._done_cb = done_cb

    def emit_progress(self, value: int):
        if self._progress_cb:
            self._progress_cb(value)

    def emit_log(self, message: str, level: str = "info"):
        if self._log_cb:
            self._log_cb(message, level)

    def emit_done(self, success: bool, message: str = ""):
        if self._done_cb:
            self._done_cb(success, message)


    @property
    @abstractmethod
    def meta(self) -> PluginMeta: ...

    @abstractmethod
    def build_ui(self, parent: QWidget) -> QWidget: ...

    @abstractmethod
    def run(self, input_files: List[str], output_dir: str) -> None: ...


    def cancel(self):
        self._cancelled = True

    @property
    def is_cancelled(self) -> bool:
        return self._cancelled