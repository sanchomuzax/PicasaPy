# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller specification for macOS PicasaPy application bundle (.app).

Builds:
    dist/PicasaPy.app
"""

import json
import os
import sys
import tomllib
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

# Root directory of the repository
GYOKER = Path(SPECPATH).resolve().parents[1]
APP = GYOKER / "src" / "picasapy" / "app"
sys.path.insert(0, str(GYOKER / "src"))

# Read version from pyproject.toml
_VERZIO = tomllib.loads((GYOKER / "pyproject.toml").read_text(encoding="utf-8"))[
    "project"
]["version"]
_VERZIO_FAJL = Path(workpath) / "_csomag_verzio.txt"
_VERZIO_FAJL.parent.mkdir(parents=True, exist_ok=True)
_VERZIO_FAJL.write_text(_VERZIO + "\n", encoding="utf-8")

# Required data files (QML, translations, assets, templates, version file)
adatok = [
    (str(APP / "qml"), "picasapy/app/qml"),
    (str(APP / "i18n"), "picasapy/app/i18n"),
    (str(APP / "assets"), "picasapy/app/assets"),
    (
        str(GYOKER / "src" / "picasapy" / "webexport" / "templates"),
        "picasapy/webexport/templates",
    ),
    (str(_VERZIO_FAJL), "picasapy"),
]

# Embed built-in Google OAuth client secrets if provided in the environment
_GOOGLE_CLIENT_ID = os.environ.get("PICASAPY_GOOGLE_CLIENT_ID", "").strip()
_GOOGLE_CLIENT_SECRET = os.environ.get("PICASAPY_GOOGLE_CLIENT_SECRET", "").strip()
_GOOGLE_CREDENTIALS_FILE = Path(workpath) / "_google_oauth.json"
if _GOOGLE_CLIENT_ID and _GOOGLE_CLIENT_SECRET:
    _GOOGLE_CREDENTIALS_FILE.parent.mkdir(parents=True, exist_ok=True)
    _GOOGLE_CREDENTIALS_FILE.write_text(
        json.dumps(
            {
                "client_id": _GOOGLE_CLIENT_ID,
                "client_secret": _GOOGLE_CLIENT_SECRET,
            }
        ),
        encoding="utf-8",
    )
    adatok.append((str(_GOOGLE_CREDENTIALS_FILE), "picasapy"))
else:
    _GOOGLE_CREDENTIALS_FILE.unlink(missing_ok=True)

# Collect help documentation and bundled ONNX models (e.g. YuNet face detector)
adatok += collect_data_files(
    "picasapy", includes=["**/*.md", "**/*.json", "**/*.onnx"]
)

a = Analysis(
    [str(Path(SPECPATH) / "picasapy_launcher.py")],
    pathex=[str(GYOKER / "src")],
    binaries=[],
    datas=adatok,
    hiddenimports=[
        "picasapy.app",
        "picasapy.printing.poster_worker",
        "picasapy.thumbs.cache",
        "picasapy.thumbs.video_decode_worker",
    ]
    + collect_submodules("picasapy"),
    hookspath=[],
    runtime_hooks=[],
    excludes=["tkinter", "pytest"],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="PicasaPy",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    icon=str(APP / "assets" / "icon.icns"),
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PicasaPy",
)

app = BUNDLE(
    coll,
    name="PicasaPy.app",
    icon=str(APP / "assets" / "icon.icns"),
    bundle_identifier="org.picasapy.picasapy",
    info_plist={
        "CFBundleDisplayName": "PicasaPy",
        "CFBundleName": "PicasaPy",
        "CFBundlePackageType": "APPL",
        "CFBundleShortVersionString": _VERZIO,
        "CFBundleVersion": _VERZIO,
        "NSHighResolutionCapable": True,
        "NSRequiresAquaSystemAppearance": False,
        "LSMinimumSystemVersion": "12.0",
        "NSHumanReadableCopyright": "Copyright © 2026 PicasaPy Contributors. GPL-3.0-or-later",
    },
)
