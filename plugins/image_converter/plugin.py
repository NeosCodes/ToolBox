import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSlider, QCheckBox, QSpinBox,
)
from PyQt6.QtCore import Qt
from core.plugin_base import PluginBase, PluginMeta


class ImageConverterPlugin(PluginBase):

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            id="image_converter",
            name="Image Converter",
            description="Convert between PNG, JPEG, WebP, BMP and TIFF. Supports batch resize and quality control.",
            category="Images",
            icon_char="🖼",
            icon_name="images",
            accent_color="#4A8FE7",
            supported_inputs=["png", "jpg", "jpeg", "webp", "bmp", "tiff", "tif"],
            supported_outputs=["png", "jpg", "webp", "bmp", "tiff"],
            requires=["Pillow>=10.0.0"],
        )

    def build_ui(self, parent: QWidget) -> QWidget:
        w = QWidget(parent)
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        # Output format
        fmt_row = QHBoxLayout()
        fmt_row.addWidget(QLabel("Output format:"))
        self._fmt = QComboBox()
        self._fmt.addItems(["PNG", "JPEG", "WebP", "BMP", "TIFF"])
        fmt_row.addWidget(self._fmt)
        fmt_row.addStretch()
        layout.addLayout(fmt_row)

        # Quality (JPEG / WebP)
        q_row = QHBoxLayout()
        q_row.addWidget(QLabel("Quality (JPEG/WebP):"))
        self._quality = QSlider(Qt.Orientation.Horizontal)
        self._quality.setRange(1, 100)
        self._quality.setValue(90)
        self._quality.setFixedWidth(160)
        self._quality_lbl = QLabel("90")
        self._quality.valueChanged.connect(lambda v: self._quality_lbl.setText(str(v)))
        q_row.addWidget(self._quality)
        q_row.addWidget(self._quality_lbl)
        q_row.addStretch()
        layout.addLayout(q_row)

        # Resize
        self._resize_cb = QCheckBox("Resize")
        layout.addWidget(self._resize_cb)

        resize_row = QHBoxLayout()
        resize_row.addWidget(QLabel("Width:"))
        self._width = QSpinBox()
        self._width.setRange(1, 99999)
        self._width.setValue(1920)
        resize_row.addWidget(self._width)
        resize_row.addWidget(QLabel("Height:"))
        self._height = QSpinBox()
        self._height.setRange(1, 99999)
        self._height.setValue(1080)
        resize_row.addWidget(self._height)
        self._keep_ratio = QCheckBox("Keep aspect ratio")
        self._keep_ratio.setChecked(True)
        resize_row.addWidget(self._keep_ratio)
        resize_row.addStretch()
        layout.addLayout(resize_row)

        self._resize_cb.toggled.connect(self._width.setEnabled)
        self._resize_cb.toggled.connect(self._height.setEnabled)
        self._resize_cb.toggled.connect(self._keep_ratio.setEnabled)
        self._resize_cb.setChecked(False)
        self._width.setEnabled(False)
        self._height.setEnabled(False)
        self._keep_ratio.setEnabled(False)

        layout.addStretch()
        return w

    def run(self, input_files: List[str], output_dir: str) -> None:
        try:
            from PIL import Image
        except ImportError:
            self.emit_done(False, "Pillow nicht installiert. Führe: pip install Pillow")
            return

        fmt = self._fmt.currentText()
        quality = self._quality.value()
        do_resize = self._resize_cb.isChecked()
        target_w = self._width.value()
        target_h = self._height.value()
        keep_ratio = self._keep_ratio.isChecked()

        ext_map = {"JPEG": "jpg", "PNG": "png", "WebP": "webp", "BMP": "bmp", "TIFF": "tiff"}
        ext = ext_map.get(fmt, fmt.lower())

        total = len(input_files)
        for i, path in enumerate(input_files):
            if self.is_cancelled:
                self.emit_done(False, "Abgebrochen.")
                return

            name = os.path.splitext(os.path.basename(path))[0]
            out_path = os.path.join(output_dir, f"{name}.{ext}")

            try:
                img = Image.open(path)

                if fmt == "JPEG" and img.mode in ("RGBA", "P"):
                    img = img.convert("RGB")

                if do_resize:
                    if keep_ratio:
                        img.thumbnail((target_w, target_h), Image.LANCZOS)
                    else:
                        img = img.resize((target_w, target_h), Image.LANCZOS)

                save_kwargs = {}
                if fmt in ("JPEG", "WebP"):
                    save_kwargs["quality"] = quality
                if fmt == "JPEG":
                    save_kwargs["optimize"] = True

                img.save(out_path, fmt, **save_kwargs)
                self.emit_log(f"✓  {os.path.basename(path)} → {ext}", "ok")

            except Exception as e:
                self.emit_log(f"✗  {os.path.basename(path)}: {e}", "error")

            self.emit_progress(int((i + 1) / total * 100))

        self.emit_done(True, f"{total} Bild(er) konvertiert.")
