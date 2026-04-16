import os
from PyQt6.QtGui import QPixmap, QIcon
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QLabel

ASSETS_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "assets")
ICONS_DIR  = os.path.join(ASSETS_DIR, "icons")


def icon_pixmap(name: str, size: int = 24) -> QPixmap | None:

    path = os.path.join(ICONS_DIR, f"{name}.png")
    if os.path.exists(path):
        return QPixmap(path).scaled(
            size, size,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
    return None


def icon_qicon(name: str, size: int = 24) -> QIcon | None:
    px = icon_pixmap(name, size)
    return QIcon(px) if px else None


def icon_label(name: str, fallback: str, size: int = 24) -> QLabel:
    lbl = QLabel()
    px = icon_pixmap(name, size)
    if px:
        lbl.setPixmap(px)
        lbl.setFixedSize(size, size)
        lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
    else:
        lbl.setText(fallback)
    return lbl
