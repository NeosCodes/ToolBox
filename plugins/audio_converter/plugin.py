import os
import subprocess
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox,
)
from core.plugin_base import PluginBase, PluginMeta


class AudioConverterPlugin(PluginBase):

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            id="audio_converter",
            name="Audio Converter",
            description="Convert MP3, FLAC, WAV, OGG and AAC using ffmpeg.",
            category="Audio",
            icon_char="🎵",
            icon_name="audio",
            accent_color="#9B6FD4",
            supported_inputs=["mp3", "flac", "wav", "ogg", "aac", "m4a", "wma", "opus"],
            supported_outputs=["mp3", "flac", "wav", "ogg", "aac"],
            requires=["ffmpeg (system install)"],
        )

    def build_ui(self, parent: QWidget) -> QWidget:
        w = QWidget(parent)
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Output format:"))
        self._fmt = QComboBox()
        self._fmt.addItems(["mp3", "flac", "wav", "ogg", "aac"])
        fmt_row.addWidget(self._fmt)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)

        br_row = QHBoxLayout()
        br_row.addWidget(QLabel("Bitrate (kbps):"))
        self._bitrate = QComboBox()
        self._bitrate.addItems(["128", "192", "256", "320"])
        self._bitrate.setCurrentText("192")
        br_row.addWidget(self._bitrate)
        br_row.addStretch()
        layout.addLayout(br_row)

        sr_row = QHBoxLayout()
        sr_row.addWidget(QLabel("Sample rate (Hz):"))
        self._samplerate = QComboBox()
        self._samplerate.addItems(["44100", "48000", "22050", "16000"])
        sr_row.addWidget(self._samplerate)
        sr_row.addStretch()
        layout.addLayout(sr_row)

        self._normalize = QCheckBox("Normalize volume (-14 LUFS)")
        layout.addWidget(self._normalize)

        layout.addStretch()
        return w

    def run(self, input_files: List[str], output_dir: str) -> None:
        fmt = self._fmt.currentText()
        bitrate = self._bitrate.currentText()
        samplerate = self._samplerate.currentText()
        normalize = self._normalize.isChecked()

        total = len(input_files)
        for i, path in enumerate(input_files):
            if self.is_cancelled:
                self.emit_done(False, "Abgebrochen.")
                return

            name = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(output_dir, f"{name}.{fmt}")

            cmd = ["ffmpeg", "-y", "-i", path, "-ar", samplerate]

            if fmt == "flac":
                cmd += ["-c:a", "flac"]
            elif fmt == "wav":
                cmd += ["-c:a", "pcm_s16le"]
            elif fmt == "ogg":
                cmd += ["-c:a", "libvorbis", "-b:a", f"{bitrate}k"]
            elif fmt == "aac":
                cmd += ["-c:a", "aac", "-b:a", f"{bitrate}k"]
            else:  # mp3
                cmd += ["-c:a", "libmp3lame", "-b:a", f"{bitrate}k"]

            if normalize:
                cmd += ["-af", "loudnorm=I=-14:TP=-1:LRA=11"]

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

        self.emit_done(True, f"{total} Audio-Datei(en) konvertiert.")
