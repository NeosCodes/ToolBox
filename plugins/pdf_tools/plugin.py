import os
from typing import List
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QSpinBox, QCheckBox,
)
from core.plugin_base import PluginBase, PluginMeta


class PdfToolsPlugin(PluginBase):

    @property
    def meta(self) -> PluginMeta:
        return PluginMeta(
            id="pdf_tools",
            name="PDF Tools",
            description="Merge multiple PDFs, split by page count, or extract specific page ranges.",
            category="PDF",
            icon_char="📄",
            icon_name="pdf",
            accent_color="#E07A3A",
            supported_inputs=["pdf"],
            supported_outputs=["pdf"],
            requires=["pypdf>=4.0.0"],
        )

    def build_ui(self, parent: QWidget) -> QWidget:
        w = QWidget(parent)
        layout = QVBoxLayout(w)
        layout.setSpacing(12)

        mode_row = QHBoxLayout()
        mode_row.addWidget(QLabel("Operation:"))
        self._mode = QComboBox()
        self._mode.addItems(["Merge", "Split", "Extract pages"])
        self._mode.currentTextChanged.connect(self._on_mode_change)
        mode_row.addWidget(self._mode)
        mode_row.addStretch()
        layout.addLayout(mode_row)

        # Split options
        self._split_widget = QWidget()
        split_layout = QHBoxLayout(self._split_widget)
        split_layout.setContentsMargins(0, 0, 0, 0)
        split_layout.addWidget(QLabel("Pages per chunk:"))
        self._split_n = QSpinBox()
        self._split_n.setRange(1, 9999)
        self._split_n.setValue(1)
        split_layout.addWidget(self._split_n)
        split_layout.addStretch()
        layout.addWidget(self._split_widget)

        # Extract options
        self._extract_widget = QWidget()
        ext_layout = QHBoxLayout(self._extract_widget)
        ext_layout.setContentsMargins(0, 0, 0, 0)
        ext_layout.addWidget(QLabel("Page range (e.g. 1-3,5):"))
        from PyQt6.QtWidgets import QLineEdit
        self._page_range = QLineEdit()
        self._page_range.setPlaceholderText("1-3,5,7-9")
        ext_layout.addWidget(self._page_range)
        ext_layout.addStretch()
        layout.addWidget(self._extract_widget)

        self._extract_widget.setVisible(False)
        self._split_widget.setVisible(False)

        layout.addStretch()
        return w

    def _on_mode_change(self, mode: str):
        self._split_widget.setVisible(mode == "Split")
        self._extract_widget.setVisible(mode == "Extract pages")

    def run(self, input_files: List[str], output_dir: str) -> None:
        try:
            import pypdf
        except ImportError:
            self.emit_done(False, "pypdf nicht installiert. Führe: pip install pypdf")
            return

        mode = self._mode.currentText()

        if mode == "Merge":
            self._merge(input_files, output_dir, pypdf)
        elif mode == "Split":
            self._split(input_files, output_dir, pypdf)
        else:
            self._extract(input_files, output_dir, pypdf)

    def _merge(self, files, output_dir, pypdf):
        writer = pypdf.PdfWriter()
        for path in files:
            try:
                reader = pypdf.PdfReader(path)
                for page in reader.pages:
                    writer.add_page(page)
                self.emit_log(f"✓  {os.path.basename(path)} hinzugefügt", "ok")
            except Exception as e:
                self.emit_log(f"✗  {os.path.basename(path)}: {e}", "error")

        out_path = os.path.join(output_dir, "merged.pdf")
        with open(out_path, "wb") as f:
            writer.write(f)
        self.emit_done(True, f"Zusammengeführt → merged.pdf")

    def _split(self, files, output_dir, pypdf):
        n = self._split_n.value()
        total = len(files)
        for i, path in enumerate(files):
            if self.is_cancelled:
                self.emit_done(False, "Abgebrochen.")
                return
            try:
                reader = pypdf.PdfReader(path)
                base = os.path.splitext(os.path.basename(path))[0]
                chunk = 0
                for start in range(0, len(reader.pages), n):
                    writer = pypdf.PdfWriter()
                    for page in reader.pages[start:start + n]:
                        writer.add_page(page)
                    out = os.path.join(output_dir, f"{base}_part{chunk + 1}.pdf")
                    with open(out, "wb") as f:
                        writer.write(f)
                    chunk += 1
                self.emit_log(f"✓  {os.path.basename(path)} → {chunk} Teile", "ok")
            except Exception as e:
                self.emit_log(f"✗  {os.path.basename(path)}: {e}", "error")
            self.emit_progress(int((i + 1) / total * 100))
        self.emit_done(True, "Split abgeschlossen.")

    def _extract(self, files, output_dir, pypdf):
        page_range_str = self._page_range.text().strip()
        pages = self._parse_range(page_range_str)
        if not pages:
            self.emit_done(False, "Ungültiger Seitenbereich.")
            return

        total = len(files)
        for i, path in enumerate(files):
            if self.is_cancelled:
                self.emit_done(False, "Abgebrochen.")
                return
            try:
                reader = pypdf.PdfReader(path)
                writer = pypdf.PdfWriter()
                for p in pages:
                    if 1 <= p <= len(reader.pages):
                        writer.add_page(reader.pages[p - 1])
                base = os.path.splitext(os.path.basename(path))[0]
                out = os.path.join(output_dir, f"{base}_extract.pdf")
                with open(out, "wb") as f:
                    writer.write(f)
                self.emit_log(f"✓  {os.path.basename(path)} → {len(writer.pages)} Seiten", "ok")
            except Exception as e:
                self.emit_log(f"✗  {os.path.basename(path)}: {e}", "error")
            self.emit_progress(int((i + 1) / total * 100))
        self.emit_done(True, "Extraktion abgeschlossen.")

    @staticmethod
    def _parse_range(s: str) -> List[int]:
        pages = []
        for part in s.split(","):
            part = part.strip()
            if "-" in part:
                a, _, b = part.partition("-")
                try:
                    pages.extend(range(int(a), int(b) + 1))
                except ValueError:
                    pass
            elif part.isdigit():
                pages.append(int(part))
        return pages
