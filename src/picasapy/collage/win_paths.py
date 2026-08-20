r"""A `.cxf` útvonal-kódolása: `$My Pictures\…`, `$UNC…`, `[C]\…` (#1096).

## Miért kell

A tulajdonos megnyitotta a **Picasával készült** kollázsát PicasaPy-ben, és
**egyetlen kép sem töltődött be**. A napló (v0.8.23, Windows):

```
QML QQuickImage: Cannot open: file:$My Pictures/lake/sunny_lake-1366x768.jpg
```

Az eredeti Picasa a `.cxf`-be **nem nyers** útvonalat ír, hanem kódoltat, mi
pedig a `$My Pictures\…` szöveget szó szerint fájlnévként próbáltuk
megnyitni. A hiba **néma**: a konzolra megy, a felületen csak üres csempék
látszanak.

## A kódolás — a binárisból mérve

A változó-tábla a `WinSystemPaths` erőforrás (`0x00994a60`), a kódoló a
`0x00999170`. **Három alak van, nem egy:**

| eset | alak | példa | mérve? |
|---|---|---|---|
| ismert rendszermappa alatt | `$<Változó>\maradék` | `$My Pictures\AI\kep.png` | **igen** |
| hálózati megosztás | `$UNC…` | — | nem |
| egyszerű helyi útvonal | `[<betű>]\maradék` | `[C]\adat\kep.png` | nem |

A felismerés sorrendje kötött: előbb `$UNC`, aztán `$<név>\`, aztán
`[<betű>]\`; ami egyikbe sem illik, az nyers útvonal.

## ⚠️ Mit MÉRTÜNK, és mit nem

A kollázs-kutató kör **12 `.cxf`-et, 101 hivatkozást** nézett át (a
tulajdonos 11 páros mappája + az álló `lake.cxf`):

| alak | darab | arány |
|---|---:|---:|
| **`$My Pictures\…`** | **101** | **100,0%** |
| `$UNC…` | 0 | 0% |
| `[betű]\…` | 0 | 0% |
| nyers `C:\…` | 0 | 0% |

Egyetlen változónév fordul elő: **`My Pictures`**.

**Ezért a `$UNC`-ot FELISMERJÜK, de NEM oldjuk fel.** A formátum
`$UNC%s%s%s` — a literál után **három** behelyettesítés —, és hogy ezek
hogyan oszlanak meg (mappa / elválasztó / fájlnév, vagy más bontás),
**nincs igazolva**. Egy kitalált összerakás rosszabb volna, mint a
bevallott kudarc: így a hiányzó-kép ág lép működésbe, ami a felhasználónak
LÁTHATÓ (helykitöltő csempe), nem néma.

A `[<betű>]\` alakot feloldjuk — a meghajtóbetűnek egyetlen értelmes
olvasata van —, de **mérés nincs rá**, tehát feltételes.

⚠️ **A nulla előfordulás nem bizonyítja, hogy nem létezik**: a 12 minta
EGY felhasználótól, EGY gépről való, és a képek mind a Képek mappa alól.
(Pontosan ez a torzítás vitte félre a #1045-öt.)

## Miért a Qt szabványos mappái oldják fel

A `$My Pictures` a **shelltől** oldódik fel, tehát a tulajdonos gépén a
OneDrive-ra átirányított, honosított `Képek` mappára mutat — nem a
`C:\Users\<név>\Pictures`-re. A `QStandardPaths` ugyanezt a shell-értéket
kérdezi, és a #1088 óta amúgy is ezt használjuk a Kollázsok mappához.

## Ami feloldhatatlan, az MARAD, ahogy volt

Ha egy változó nem oldható fel (nincs ilyen mappa a rendszeren), a
függvény **az eredeti szöveget adja vissza**. Így a hiányzó-kép ág lép
működésbe — helykitöltő csempe, felsorolt hiány —, nem pedig egy néma
kivétel vagy egy kitalált útvonal. Az eredeti fájlt sosem írjuk át
mellékhatásként: a dekódolás csak a MEGJELENÍTÉS felé fordít.
"""

from __future__ import annotations

import re
from pathlib import Path, PureWindowsPath

from PySide6.QtCore import QStandardPaths

#: A `WinSystemPaths` tábla (`0x00994a60`) hét változója, a Qt szabványos
#: mappa-párjával. A `My Pictures` az egyetlen, amit `.cxf`-ekben eddig
#: láttunk, de a kódoló mind a hetet ismeri.
#:
#: ⚠️ **Két csapda** (a kollázs-kutató köre mérte ki):
#:
#: - az `Application Data` a **`GenericDataLocation`**, NEM az
#:   `AppDataLocation` — utóbbi hozzáfűzi az alkalmazás nevét, tehát más
#:   mappára mutatna, mint amit a Picasa értett alatta;
#: - a `Common Application Data`-nak **nincs Qt-párja** (gépszintű
#:   `ProgramData`). Szándékosan `None`: feloldani nem tudjuk, tehát az
#:   ilyen útvonal érintetlenül megy tovább, és a hiányzó-kép ág lép
#:   működésbe — kitalálni egy közelítő mappát rosszabb volna.
VALTOZOK: dict[str, QStandardPaths.StandardLocation | None] = {
    "My Pictures": QStandardPaths.StandardLocation.PicturesLocation,
    "My Music": QStandardPaths.StandardLocation.MusicLocation,
    "My Videos": QStandardPaths.StandardLocation.MoviesLocation,
    "My Documents": QStandardPaths.StandardLocation.DocumentsLocation,
    "Desktop": QStandardPaths.StandardLocation.DesktopLocation,
    "Application Data": QStandardPaths.StandardLocation.GenericDataLocation,
    "Common Application Data": None,
}

#: `$UNC\\szerver\megosztás\…` — a hálózati alak előtagja.
_UNC_ELOTAG = "$UNC"

#: `[C]\maradék` — meghajtóbetű szögletes zárójelben.
_MEGHAJTO = re.compile(r"^\[([A-Za-z])\][\\/]?(.*)$", re.DOTALL)

#: `$<Változónév>\maradék`
_VALTOZO = re.compile(r"^\$([^\\/]+)[\\/](.*)$", re.DOTALL)


def _mappa(location: QStandardPaths.StandardLocation) -> str:
    """A rendszermappa útvonala, vagy üres, ha nincs ilyen."""
    return QStandardPaths.writableLocation(location)


def _reszek(maradek: str) -> tuple[str, ...]:
    """A kódolt maradék szakaszai — a `.cxf` VISSZAPERJELLEL ír.

    Mindkét elválasztóra bontunk: a fájl windowsos, a futtató rendszer
    viszont lehet linux, és az eredményt a HELYI alakban kell visszaadni
    (különben egy `\\home\\…` alakú „útvonal" keletkezne, amit sehol nem
    lehet megnyitni)."""
    return tuple(resz for resz in re.split(r"[\\/]+", maradek) if resz)


def decode_cxf_path(src: str) -> str:
    """A `.cxf` `<src>` értéke → valódi, megnyitható útvonal (#1096).

    Feloldhatatlan változónál az EREDETI szöveget adja vissza — így a
    hiányzó-kép ág lép működésbe, nem egy kitalált útvonal.
    """
    szoveg = (src or "").strip()
    if not szoveg:
        return szoveg

    if szoveg.upper().startswith(_UNC_ELOTAG):
        # FELISMERJÜK, de nem oldjuk fel: a `$UNC%s%s%s` hármas bontása
        # nincs igazolva, és nincs rá valódi mintánk (0/101). Az eredeti
        # szöveg megy tovább → LÁTHATÓ hiányzó-kép csempe.
        return szoveg

    valtozo = _VALTOZO.match(szoveg)
    if valtozo is not None:
        nev, maradek = valtozo.group(1), valtozo.group(2)
        if nev not in VALTOZOK:
            return szoveg
        location = VALTOZOK[nev]
        if location is None:  # ismert név, de nincs Qt-párja (ProgramData)
            return szoveg
        gyoker = _mappa(location)
        if not gyoker:
            return szoveg
        return str(Path(gyoker).joinpath(*_reszek(maradek)))

    meghajto = _MEGHAJTO.match(szoveg)
    if meghajto is not None:
        betu, maradek = meghajto.group(1), meghajto.group(2)
        return str(PureWindowsPath(f"{betu.upper()}:\\").joinpath(*_reszek(maradek)))

    return szoveg


def encode_cxf_path(path: str) -> str:
    r"""Valódi útvonal → a `.cxf` kódolt alakja (#1096).

    A képmappa (és a többi ismert rendszermappa) alatt lévő fájl
    `$<Változó>\maradék` alakot kap — így a `.cxf` túléli a költöztetést és
    megosztható. Ami egyik mappa alá sem esik, az **változatlanul** megy ki:
    kitalált kódolás rosszabb volna, mint a nyers útvonal.
    """
    szoveg = (path or "").strip()
    if not szoveg:
        return szoveg
    jelolt = PureWindowsPath(szoveg)
    for nev, location in VALTOZOK.items():
        if location is None:
            continue
        gyoker = _mappa(location)
        if not gyoker:
            continue
        try:
            maradek = jelolt.relative_to(PureWindowsPath(gyoker))
        except ValueError:
            continue
        if str(maradek) in (".", ""):
            continue
        return f"${nev}\\{maradek}"
    return szoveg


__all__ = ["VALTOZOK", "decode_cxf_path", "encode_cxf_path"]
