"""Próbabetű: egy második betűcsalád a rendszerbetű-adatbázisba (#4546).

A betűtípus-választó próbái legalább KÉT telepített családot igényelnek.
Windowson az offscreen CI-futtató adatbázisában egy család látszik, ezért a
próbák (QML-es és vezérlős egyaránt) innen kapnak másodikat.
"""

from __future__ import annotations

import struct
from collections.abc import Callable, Iterable
from pathlib import Path

from picasapy.app import edit_preview as preview_module

BETU_FORRAS = (
    Path(preview_module.__file__).parent / "assets" / "fonts" / "OpenSans-Regular.ttf"
)


def atnevezett_betu(cel: Path) -> Path:
    """A csomagolt Open Sans egy másik CSALÁDNÉVEN („Open Sanz") futó másolata.

    Miért kell: a legördülő a telepített rendszerbetűket kínálja, a választást
    pedig csak legalább KÉT családnál lehet mérni. A windowsos CI offscreen
    futtatóján a rendszerbetű-adatbázis csak a csomagolt felület-betűt
    tartalmazza (hipotézis: a CI-bukás `target_index == -1` értéke ezt
    jelzi: legfeljebb egy család volt). A másolat azonos hosszú névcserével
    készül, így a táblaszerkezet érintetlen marad.
    """
    adat = bytearray(BETU_FORRAS.read_bytes())
    darab = struct.unpack(">H", adat[4:6])[0]
    for i in range(darab):
        cimke, _ellenorzo, eltolas, hossz = struct.unpack(
            ">4sIII", adat[12 + 16 * i:28 + 16 * i]
        )
        if cimke != b"name":
            continue
        blokk = bytes(adat[eltolas:eltolas + hossz])
        blokk = blokk.replace(
            "Open Sans".encode("utf-16-be"), "Open Sanz".encode("utf-16-be")
        )
        blokk = blokk.replace(b"Open Sans", b"Open Sanz")
        adat[eltolas:eltolas + hossz] = blokk
    cel.write_bytes(bytes(adat))
    return cel


#: Nem valódi rendszerbetű: az üres fontconfig-adatbázis általános álnevei és
#: a saját próbabetűink (`legalabb_ket_betucsalad`).
_NEM_VALODI_CSALADOK = frozenset(
    {"sans serif", "serif", "monospace", "open sans", "open sanz"}
)


def potlando_betufajlok(
    csaladok: Iterable[str],
    jeloltek: Iterable[Path | None],
) -> list[Path]:
    """A regisztrálandó betűfájlok, ha a Qt-adatbázis gyakorlatilag üres (#4506).

    A windowsos offscreen Qt (`QFreeTypeFontDatabase`) a rendszerbetűket nem
    látja, így a szövegrajzoló próbák Qt-útja betűkép nélkül fest. Ilyenkor —
    és CSAK ilyenkor, ha egyetlen VALÓDI család sincs (az általános álneveken és
    a saját próbabetűinken kívül) — a renderelő saját fájljelöltjeit
    (`render.text_fonts.font_path_for`) adjuk alkalmazás-betűként. Rendes
    adatbázisnál (Linux fontconfig) üres listát ad: ott nincs mit pótolni.
    """
    if any(c.casefold() not in _NEM_VALODI_CSALADOK for c in csaladok):
        return []
    egyedi: list[Path] = []
    for jelolt in jeloltek:
        if jelolt is not None and jelolt not in egyedi:
            egyedi.append(jelolt)
    return egyedi


def betufajlok_regisztralasa(
    fajlok: Iterable[Path], hozzaad: Callable[[str], int]
) -> dict[Path, int]:
    """A fájlok felvétele: `{fájl: azonosító}`, a sikertelen (-1) kimarad."""
    regisztralt: dict[Path, int] = {}
    for fajl in fajlok:
        azonosito = hozzaad(str(fajl))
        if azonosito >= 0:
            regisztralt[fajl] = azonosito
    return regisztralt
