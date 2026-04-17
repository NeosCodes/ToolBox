import os
import subprocess
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox,
)
from PyQt6.QtCore import Qt
from core.plugin_base import PluginBase, PluginMeta


class VideoConverterPlugin(PluginBase):

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            id="video_converter",
            name="Video Converter",
            description="Convert MP4, MKV, AVI, MOV and WebM using ffmpeg.",
            category="Video",
            icon_char="▶",
            icon_name="video",
            accent_color="#E24B4A",
            supported_inputs=["mp4", "mkv", "avi", "mov", "webm", "flv", "wmv"],
            supported_outputs=["mp4", "mkv", "avi", "mov", "webm"],
            requires=["ffmpeg (system install)"],
        )

    def build_ui(self, parent: QWidget) -> QWidget:
        w = QWidget(parent)
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Output format:"))
        self._fmt = QComboBox()
        self._fmt.addItems(["mp4", "mkv", "avi", "mov", "webm"])
        fmt_row.addWidget(self._fmt)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)

        codec_row = QHBoxLayout()
        codec_row.addWidget(QLabel("Video codec:"))
        self._codec = QComboBox()
        self._codec.addItems(["libx264", "libx265", "libvpx-vp9", "copy"])
        codec_row.addWidget(self._codec)
        codec_row.addStretch()
        layout.addLayout(codec_row)

        crf_row = QHBoxLayout()
        crf_row.addWidget(QLabel("Quality (CRF, lower = better):"))
        self._crf = QSlider(Qt.Orientation.Horizontal)
        self._crf.setRange(0, 51)
        self._crf.setValue(23)
        self._crf.setFixedWidth(160)
        self._crf_lbl = QLabel("23")
        self._crf.valueChanged.connect(lambda v: self._crf_lbl.setText(str(v)))
        crf_row.addWidget(self._crf)
        crf_row.addWidget(self._crf_lbl)
        crf_row.addStretch()
        layout.addLayout(crf_row)

        self._strip_audio = QCheckBox("Strip audio")
        layout.addWidget(self._strip_audio)

        layout.addStretch()
        return w

    def run(self, input_files: List[str], output_dir: str) -> None:
        fmt = self._fmt.currentText()
        codec = self._codec.currentText()
        crf = self._crf.value()
        strip_audio = self._strip_audio.isChecked()

        total = len(input_files)
        for i, path in enumerate(input_files):
            if self.is_cancelled:
                self.emit_done(False, "Abgebrochen.")
                return

            name = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(output_dir, f"{name}.{fmt}")

            cmd = ["ffmpeg", "-y", "-i", path]
            if codec != "copy":
                cmd += ["-vcodec", codec, "-crf", str(crf)]
            else:
                cmd += ["-vcodec", "copy"]
            if strip_audio:
                cmd += ["-an"]
            cmd.append(out_path)

            try:
                self.emit_log(f"Konvertiere {os.path.basename(path)}…", "info")
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=3600)
                if result.returncode == 0:
                    self.emit_log(f"✓  {os.path.basename(path)} → {fmt}", "ok")
                else:
                    self.emit_log(f"✗  {os.path.basename(path)}: {result.stderr[-200:]}", "error")
            except FileNotFoundError:
                self.emit_done(False, "ffmpeg nicht gefunden. Installiere ffmpeg und füge es zum PATH hinzu.")
                return
            except Exception as e:
                self.emit_log(f"✗  {os.path.basename(path)}: {e}", "error")

            self.emit_progress(int((i + 1) / total * 100))

        self.emit_done(True, f"{total} Video(s) konvertiert.")
