# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller-leírás a windowsos PicasaPy-hoz (#3021).

A tulajdonos szava: *„Egy felhasználó nem klónoz repót, nem keres batch
fájlt, és nincs Pythonja."* Ez a leírás a Python futtatókörnyezetet is a
csomagba teszi, tehát a gépen semmit nem kell előre telepíteni.

## Amit kézzel kell hozzátenni, és miért

A PyInstaller az IMPORTOKAT követi. A QML-fa, a fordítás (`.qm`) és az ikon
nem import, hanem adat — ezek nélkül a program elindul, de **ablak nélkül**
(a `Main.qml` nem található), vagy angolul. Ezért mennek a `datas` közé.

A Qt-bővítményeket (platform, képformátum, QML-modulok) a PySide6-hook
maga viszi; ezt NEM ismételjük meg kézzel, mert a kézi lista elavul. Hogy
a csomag tényleg teljes-e, azt a CI méri: a felépített `.exe`-t
`--onellenorzes` kapcsolóval elindítja.

## Használat

    pyinstaller --noconfirm packaging/windows/picasapy.spec

Kimenet: `dist/PicasaPy/PicasaPy.exe` (mappás csomag — Qt-programnál ez
indul gyorsabban, mint az egyfájlos, mert nincs kicsomagolás minden
indításkor).
"""

import sys
from pathlib import Path

from PyInstaller.utils.hooks import collect_data_files, collect_submodules

#: a repó gyökere — a spec a `packaging/windows/` alatt él
GYOKER = Path(SPECPATH).resolve().parents[1]
APP = GYOKER / "src" / "picasapy" / "app"

#: ⚠️ A `collect_*` segédek IMPORTÁLJÁK a csomagot; a `pathex` csak az
#: elemzésre hat. Enélkül a CI-n „'picasapy' … is not a package” mellett
#: üres listát adtak, és a csomagból modulok és adatfájlok maradtak ki.
sys.path.insert(0, str(GYOKER / "src"))

#: a QML-fa, a fordítás, az ikonok és a súgó: adatok, nem importok
adatok = [
    (str(APP / "qml"), "picasapy/app/qml"),
    (str(APP / "i18n"), "picasapy/app/i18n"),
    (str(APP / "assets"), "picasapy/app/assets"),
]
#: a `help/` és a többi csomagon belüli adat a saját hookok nélkül is kell
adatok += collect_data_files(
    "picasapy", includes=["**/*.md", "**/*.json", "**/*.onnx"]
)

#: ⚠️ NEM a `__main__.py`: azt a PyInstaller szkriptként futtatná, és a
#: relatív importja `ImportError`-ral esne el (mérve a windowsos CI-n). A
#: belépő egy külön, import-mentes indító.
a = Analysis(
    [str(Path(SPECPATH) / "picasapy_launcher.py")],
    pathex=[str(GYOKER / "src")],
    binaries=[],
    datas=adatok,
    #: ⚠️ A saját csomag MINDEN modulja: az indulást gyorsító lusta
    #: (függvényen belüli) importokat a PyInstaller nem látja, és a
    #: csomagból kimaradt modul csak a felület adott pontján, élesben
    #: derülne ki (#4913: `picasapy.app.edit_preview` hiányzott).
    hiddenimports=collect_submodules("picasapy"),
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
    strip=False,
    upx=False,
    #: ABLAKOS program: konzolos csomagolásnál minden indításnál fekete
    #: parancssor-ablak nyílna a felület mellé
    console=False,
    icon=str(APP / "assets" / "icon.ico"),
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    name="PicasaPy",
)
