import os
from PyInstaller.utils.hooks import collect_all

block_cipher = None

# Alle PyQt6-Dateien (DLLs, Plugins, Daten) vollständig einsammeln
qt_binaries, qt_datas, qt_hidden = collect_all("PyQt6")

added_files = [
    ("assets",  "assets"),
    ("plugins", "plugins"),
]

a = Analysis(
    ["main.py"],
    pathex=["."],
    binaries=qt_binaries,
    datas=added_files + qt_datas,
    hiddenimports=qt_hidden + [
        "PIL",
        "PIL.Image",
        "pypdf",
        "docx",
        "openpyxl",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        "tkinter",
        "matplotlib",
        "numpy",
        "scipy",
        "pandas",
    ],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name="ToolBox",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,        # UPX aus — kann Qt-DLLs beschädigen
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon="assets/ToolBox.ico",
    version_file=None,
)
