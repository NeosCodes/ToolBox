# ToolBox

A modular local file converter toolkit built with Python + PyQt6.

## Features

- **Image Converter** — PNG, JPEG, WebP, BMP, TIFF + resize + quality control
- **Video Converter** — MP4, MKV, AVI, MOV, WebM via ffmpeg
- **PDF Tools** — Merge, split, extract pages
- **Doc Converter** — DOCX → TXT/HTML, XLSX → CSV/JSON, Markdown → HTML
- **Audio Converter** — MP3, FLAC, WAV, OGG, AAC via ffmpeg

All processing runs locally — no cloud, no tracking.

---

## Setup

### 1. Clone / unzip the project

### 2. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 3. Install ffmpeg (required for Video + Audio tools)

- **Windows**: Download from https://ffmpeg.org/download.html → extract → add `bin/` folder to PATH
- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`

### 4. Run

```bash
python main.py
```

---

## Build as .exe (Windows)

```bash
pip install pyinstaller
pyinstaller ToolBox.spec
```

The executable is created at `dist/ToolBox.exe`.

> **Note**: ffmpeg must still be installed separately on the target machine for Video and Audio tools.
> To bundle ffmpeg, download the static build, place `ffmpeg.exe` in the project root, and add it to `binaries` in the spec file:
> ```python
> binaries=[('ffmpeg.exe', '.')]
> ```
> Then in the plugin, find ffmpeg via `sys._MEIPASS` at runtime.

---

## Adding a new plugin

1. Create a folder `plugins/your_tool_name/`
2. Add `__init__.py` (empty)
3. Create `plugin.py` with a class that extends `PluginBase`
4. Implement `meta`, `build_ui()`, and `run()`

The plugin is auto-discovered on next launch — no registration needed.

```python
from core.plugin_base import PluginBase, PluginMeta

class MyToolPlugin(PluginBase):

    @property
    def meta(self):
        return PluginMeta(
            id="my_tool",
            name="My Tool",
            description="Does something useful",
            category="Images",   # existing category
            icon_char="🔧",
            accent_color="#FF6B6B",
            supported_inputs=["*.txt"],
            supported_outputs=["TXT"],
        )

    def build_ui(self, parent):
        from PyQt6.QtWidgets import QWidget, QHBoxLayout, QLabel
        widget = QWidget(parent)
        layout = QHBoxLayout(widget)
        layout.addWidget(QLabel("No options needed"))
        return widget

    def run(self, input_files, output_dir):
        for i, path in enumerate(input_files):
            self.emit_log(f"Processing {path}", "info")
            # ... do work ...
            self.emit_progress(int((i+1)/len(input_files)*100))
        self.emit_done(True, "Done!")
```

---

## Project structure

```
ToolBox/
├── main.py                     Entry point
├── requirements.txt
├── ToolBox.spec             PyInstaller build config
├── core/
│   ├── plugin_base.py          Abstract base class for all plugins
│   ├── registry.py             Auto-discovers plugins at startup
│   ├── worker.py               QThread wrapper for background processing
│   ├── styles.py               Global dark-mode stylesheet
│   └── window.py               Main PyQt6 window
└── plugins/
    ├── image_converter/
    ├── video_converter/
    ├── pdf_tools/
    ├── doc_converter/
    └── audio_converter/
        └── plugin.py           (each folder has this)
```