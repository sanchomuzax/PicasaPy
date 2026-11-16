r"""A hét ismert felhasználói mappa a Qt szabványos útvonalaiból (#7108).

Az eredeti Picasa a `0x00995c90` táblában hét mappát nevez meg: My Pictures,
Desktop, My Music, My Videos, My Documents, Application Data és Common
Application Data. A mappa mozgatása ezeken szürke, és a végrehajtó is
megáll rajtuk (`Unable to Move a System Path`). A tábla PONTOS egyezést
vizsgál: a mappák ALATTI könyvtárak mozgathatók.

A feloldás a `QStandardPaths`-ból megy (a `collage/win_paths.py` ugyanezt a
hetes táblát oldja fel `.cxf`-útvonalakhoz, ugyanezzel a leképezéssel):

| eredeti | Qt-hely |
|---|---|
| My Pictures | `PicturesLocation` |
| Desktop | `DesktopLocation` |
| My Music | `MusicLocation` |
| My Videos | `MoviesLocation` |
| My Documents | `DocumentsLocation` |
| Application Data | `GenericDataLocation` (írható) és az `AppDataLocation` gyökere |
| Common Application Data | a `GenericDataLocation` NEM írható bejegyzései |

⚠️ Az `AppDataLocation` hozzáfűzi a szervezet és az alkalmazás nevét
(`…/Roaming/<szervezet>/<alkalmazás>`). Az eredeti `Application Data`
(Windowson a `Roaming`) a gyökér maga, ezért a két név levágása után
használjuk. A Windowson a gépszintű `ProgramData`-t a `GenericDataLocation`
nem írható bejegyzése adja (a Qt viselkedéséről szóló ismeret, NEM mért);
linuxon ugyanez a hely a `/usr/local/share`, `/usr/share` és társai.

⚠️ A Windows-ág itt nem mérhető (nincs windowsos futtató ezen a gépen), és a
Qt dokumentációját sem tudtuk ellenőrizni. Ha a windowsos futtatón a közös
alkalmazásadat nem védett, a hiba itt keresendő; a `C:\ProgramData` a
`move_folder._SYSTEM_PATHS` rögzített listájában amúgy is benne van.

Ami nem oldható fel (üres szöveg), az NEM védett mappa: az üres szövegből
képzett `Path("")` a munkakönyvtárra oldódna fel, és azt tiltaná le.
"""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths

#: A `QStandardPaths` és az útvonal-normalizálás MODULSZINTŰ fogantyúi: a
#: teszt ezeket cseréli, ne a globális modulok tagjait (#1217, #1375).
_writable_location = QStandardPaths.writableLocation
_standard_locations = QStandardPaths.standardLocations
_normcase = os.path.normcase

_HELY = QStandardPaths.StandardLocation

#: Az írható Qt-hely az eredeti hét mappa közül ötnek egy-egy párja.
_EGYSZERU_HELYEK = (
    _HELY.PicturesLocation,
    _HELY.DesktopLocation,
    _HELY.MusicLocation,
    _HELY.MoviesLocation,
    _HELY.DocumentsLocation,
)


def _alkalmazas_nevek() -> tuple[str, str]:
    """A Qt által az `AppDataLocation`-hoz fűzött szervezet- és alkalmazásnév."""
    return (
        QCoreApplication.organizationName(),
        QCoreApplication.applicationName(),
    )


def _utak(szovegek) -> list[Path]:
    """A nem üres szövegekből útvonalak (az üres NEM a munkakönyvtár)."""
    return [Path(szoveg) for szoveg in szovegek if szoveg and szoveg.strip()]


def _alkalmazasadat_gyoker() -> list[Path]:
    """Az `AppDataLocation` a szervezet/alkalmazás név nélkül (Windowson `Roaming`)."""
    gyoker = _utak([_writable_location(_HELY.AppDataLocation)])
    if not gyoker:
        return []
    ut = gyoker[0]
    for nev in reversed([resz for resz in _alkalmazas_nevek() if resz]):
        if ut.name == nev:
            ut = ut.parent
    return [ut]


def _kozos_alkalmazasadat() -> list[Path]:
    """A `GenericDataLocation` nem írható bejegyzései (Windowson `ProgramData`)."""
    irhato = _writable_location(_HELY.GenericDataLocation)
    return _utak(
        ut for ut in _standard_locations(_HELY.GenericDataLocation) if ut != irhato
    )


def known_folder_paths() -> tuple[Path, ...]:
    """Az ismert mappák feloldott útvonalai (a fel nem oldhatók kimaradnak)."""
    jeloltek: list[Path] = []
    for hely in _EGYSZERU_HELYEK:
        jeloltek += _utak([_writable_location(hely)])
    jeloltek += _utak([_writable_location(_HELY.GenericDataLocation)])
    jeloltek += _alkalmazasadat_gyoker()
    jeloltek += _kozos_alkalmazasadat()
    # sorrendtartó ismétlés-szűrés (linuxon a két alkalmazásadat-hely egybeesik)
    return tuple(dict.fromkeys(jeloltek))


def _kulcs(ut: Path) -> str:
    """Az összevetés alakja: feloldott, a platform kis/nagybetű-szabályával."""
    return _normcase(str(ut.resolve())).rstrip("\\/")


def is_known_user_folder(folder: str | Path) -> bool:
    """Igaz, ha a mappa PONTOSAN az egyik ismert mappa (az alatta állók nem)."""
    keresett = _kulcs(Path(folder))
    return any(keresett == _kulcs(ismert) for ismert in known_folder_paths())


__all__ = ["is_known_user_folder", "known_folder_paths"]
