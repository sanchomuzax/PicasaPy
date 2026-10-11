"""A windowsos offscreen Qt-platform betűmappája (#4506).

A windowsos `qoffscreen.dll` a `QFreeTypeFontDatabase`-t használja (a DLL a
konstruktorát importálja, a `QWindowsFontDatabase`-ét nem). Ez az adatbázis
csak a `QT_QPA_FONTDIR` mappát olvassa, ennek híján a `<Qt-lib>/fonts`-ot — a
PySide6-kerékből ez a mappa hiányzik, így a tesztfolyamat egyetlen
rendszerbetűt sem lát: a szöveg betűkép nélkül rajzolódik, a félkövér és a
dőlt nem különbözik, a betűlista üres.

A valódi alkalmazás Windowson a `windows` platformmal fut, amelynek saját
rendszerbetű-adatbázisa van; a beállítás a tesztkörnyezetet hozza ugyanarra
a betűkészletre. A `windows` platformot a `QT_QPA_FONTDIR` nem befolyásolja,
Linuxon pedig a fontconfig-adatbázis dolgozik, az sem nézi.
"""

from __future__ import annotations

import os
from collections.abc import Callable, Mapping
from pathlib import PureWindowsPath


def qt_betukonyvtar_kiegeszites(
    kornyezet: Mapping[str, str],
    platform: str,
    *,
    letezik: Callable[[str], bool] = os.path.isdir,
) -> dict[str, str]:
    """A környezet kiegészítése: `{"QT_QPA_FONTDIR": <Windows\\Fonts>}` vagy `{}`.

    Nem módosítja a kapott környezetet; a kézzel megadott `QT_QPA_FONTDIR`
    érintetlen marad, és nem létező mappát nem állít be.
    """
    if platform != "win32" or kornyezet.get("QT_QPA_FONTDIR"):
        return {}
    windows = kornyezet.get("WINDIR") or kornyezet.get("SystemRoot") or r"C:\Windows"
    betumappa = str(PureWindowsPath(windows) / "Fonts")
    if not letezik(betumappa):
        return {}
    return {"QT_QPA_FONTDIR": betumappa}


__all__ = ["qt_betukonyvtar_kiegeszites"]
