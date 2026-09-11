"""Indulás előtti platform-ellenőrzés (#3028).

A Qt a hiányzó platform-bővítményt angolul, a megoldás nélkül jelenti, és
utána megáll:

```
qt.qpa.plugin: Could not find the Qt platform plugin "wayland" in ""
This application failed to start because no Qt platform plugin could be
initialized.
```

A tulajdonos gépén (Raspberry Pi 5, wayland-asztal) pontosan ez történt: a
`qt6-wayland` csomag nem volt telepítve, a fent lévő `qtwayland5` pedig a
Qt 5-é. Ez a modul a `QGuiApplication` létrehozása ELŐTT fut — utána már
késő, mert a Qt addigra kilép.

⚠️ A modul csak **jelez**, nem választ helyette platformot. Egy néma
átterelés (például `QT_QPA_PLATFORM=xcb`) elrejtené a valódi hiányt, és a
felhasználó sosem tudná meg, mit kell telepítenie.
"""

from __future__ import annotations

import os
from pathlib import Path

#: a hiányzó bővítmény csomagneve Debian/Ubuntu alatt
_CSOMAG = "qt6-wayland"

_UZENET = (
    "PicasaPy: a program wayland-asztalon fut, de a Qt 6 wayland-bővítménye "
    "hiányzik, ezért nem indul el.\n"
    "  Megoldás — egyetlen parancs egy terminálban:\n"
    f"      sudo apt install {_CSOMAG}\n"
    "  (A gépen lévő qtwayland5 a Qt 5-é, ezt a program nem tudja "
    "használni.)"
)


def elerheto_platformok(plugin_dir: Path | None = None) -> tuple[str, ...]:
    """A telepített Qt platform-bővítmények nevei (`xcb`, `wayland`, …).

    A listát a Qt saját telepítéséből olvassuk, nem égetjük be: a PySide6
    kerék és a disztribúciós csomag más-más helyre teszi őket."""
    if plugin_dir is None:
        from PySide6.QtCore import QLibraryInfo

        plugin_dir = Path(
            QLibraryInfo.path(QLibraryInfo.LibraryPath.PluginsPath)
        ) / "platforms"
    if not plugin_dir.is_dir():
        return ()
    nevek = set()
    for fajl in plugin_dir.glob("libq*.so"):
        nevek.add(fajl.stem[4:])  # "libqwayland-egl" -> "wayland-egl"
    #: a wayland bővítmény több fájlból áll (`libqwayland-generic.so`,
    #: `libqwayland-egl.so`); bármelyik jelenléte elég
    if any(nev.startswith("wayland") for nev in nevek):
        nevek.add("wayland")
    return tuple(sorted(nevek))


def hianyzo_wayland_bovitmeny(
    kornyezet: dict[str, str] | None = None,
    *,
    bovitmenyek: tuple[str, ...] | None = None,
) -> str | None:
    """A figyelmeztetés szövege, vagy `None`, ha nincs miről szólni.

    Akkor és csak akkor szól, ha (1) a munkamenet wayland, (2) a
    felhasználó nem kért kifejezetten más platformot, és (3) tényleg
    nincs wayland-bővítmény. A téves riasztás elszoktat az olvasástól,
    ezért mindhárom feltétel kell."""
    kornyezet = os.environ if kornyezet is None else kornyezet
    if kornyezet.get("QT_QPA_PLATFORM"):
        return None
    wayland_munkamenet = (
        kornyezet.get("XDG_SESSION_TYPE") == "wayland"
        or bool(kornyezet.get("WAYLAND_DISPLAY"))
    )
    if not wayland_munkamenet:
        return None
    if bovitmenyek is None:
        bovitmenyek = elerheto_platformok()
    if any(nev.startswith("wayland") for nev in bovitmenyek):
        return None
    return _UZENET


__all__ = ["elerheto_platformok", "hianyzo_wayland_bovitmeny"]
