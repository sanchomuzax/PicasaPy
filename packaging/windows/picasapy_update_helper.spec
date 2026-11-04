# -*- mode: python ; coding: utf-8 -*-
"""Egyfájlos Windows-frissítő segéd (#6340)."""

import sys
from pathlib import Path

GYOKER = Path(SPECPATH).resolve().parents[1]
sys.path.insert(0, str(Path(SPECPATH).resolve()))
from _windows_version_resource import write_version_info  # noqa: E402

sys.path.insert(0, str(GYOKER / "src"))

_VERZIO_EROFORRAS = Path(workpath) / "_picasapy_version_info.txt"
write_version_info(
    GYOKER / "pyproject.toml",
    _VERZIO_EROFORRAS,
    "PicasaPyUpdateHelper.exe",
)

a = Analysis(
    [str(Path(SPECPATH) / "picasapy_update_helper.py")],
    pathex=[str(GYOKER / "src")],
    binaries=[],
    datas=[],
    hiddenimports=[
        "tkinter",
        "tkinter.ttk",
        "picasapy.app.update_swap_helper",
        "picasapy.app.update_folyamatok",
        "picasapy.app.update_eredmeny",
        "picasapy.app.update_ablak",
    ],
    hookspath=[],
    runtime_hooks=[],
    excludes=["pytest"],
    noarchive=False,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name="PicasaPyUpdateHelper",
    debug=False,
    strip=False,
    upx=False,
    console=True,
    version=str(_VERZIO_EROFORRAS),
)
