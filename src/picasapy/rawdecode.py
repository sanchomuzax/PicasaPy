"""Nyers (RAW) fájlok dekódolása — a nyers út egyetlen igazságforrása (#528).

## Miért van erre külön modul

A `scanner/filetypes.py` felismeri a nyers fájlokat (`media_kind_of` →
`"raw"`), a képbetöltés viszont mindenhol `cv2.imdecode` volt, aminek
**nincs nyers dekódere**: a nyers fájlok bekerültek az indexbe, de nem
jelent meg belőlük kép. Ez a modul a `rawpy`-t (a LibRaw kötése) adja a
dekódolási utakhoz, `cv2`-kompatibilis **BGR** képként — így a hívó oldalán
csak egy elágazás kell, nem külön képcsővezeték.

## Amit az eredeti Picasa csinált — mért tények

A `Picasa3.exe` a **`dcraw v9.19`**-et építette be (a sztring benne van a
binárisban), ami a LibRaw ELŐDJE: ugyanaz a Dave Coffin-féle kód, amit a
LibRaw átvett és továbbvitt. Tehát a `rawpy`/LibRaw nem „másik" dekóder,
hanem ugyanannak a családnak a mai tagja.

## A beágyazott előnézet GYORSÍTÁS, nem feltétel — mérve

A nyers fájlok egy részében ott a fényképezőgép beégetett JPEG-előnézete, és
azt kinyerni nagyságrenddel gyorsabb, mint demozaikolni. De **nem minden
nyers fájlban van**: a #528 Leica-mintáján
(`RAW_LEICA_DIGILUX2_SRGB.RAW`, 2568 × 1928) a `rawpy.extract_thumb()`
`LibRawNoThumbnailError: No thumbnail in file`-t adott, és a teljes
demozaikolás 0,39 s volt (RPi5, LibRaw 0.21.4). Ezért a gyors út
**opcionális ág**, a visszaesés a teljes dekódolásra kötelező.

## A hibát JELEZNI kell, nem elnyelni

Ha nincs `rawpy`, vagy a fájlt a LibRaw nem bírja, a válasz `None` — a hívók
ilyenkor helyőrző bélyegképet adnak —, és **a napló megnevezi az okot**. Néma
üres kép nem elfogadható kimenet (a jegy elfogadási feltétele).
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import numpy as np

from picasapy.scanner.filetypes import RAW_EXTENSIONS

_log = logging.getLogger(__name__)

#: A nyers kiterjesztések — a `filetypes` listája az igazságforrás, hogy a
#: felismert és a dekódolásra küldött halmaz ne csúszhasson el egymástól.
NYERS_KITERJESZTESEK = RAW_EXTENSIONS

#: A beágyazott előnézetet csak akkor használjuk, ha a leghosszabb oldala
#: legalább ennyiszerese a célméretnek — különben felskálázni kellene, ami
#: rosszabb, mint demozaikolni.
_ELONEZET_TARTALEK = 1


def _rawpy() -> Any | None:
    """A `rawpy` modul, vagy `None`, ha nincs telepítve.

    Lusta import: a `rawpy` behozza a LibRaw megosztott könyvtárat, ezt az
    indulási láncban nem akarjuk megfizetni (ugyanaz az elv, mint a
    `lazy_cv2`-nél)."""
    try:
        import rawpy
    except ImportError:
        return None
    return rawpy


def nyers_utvonal(source: Path | str) -> bool:
    """Nyers fájlra utal-e a kiterjesztés. A tartalmat NEM nyitja meg."""
    return Path(source).suffix.lower() in NYERS_KITERJESZTESEK


def beagyazott_elonezet(source: Path) -> bytes | None:
    """A fényképezőgép beégetett JPEG-előnézete, ha van; `None`, ha nincs.

    A `None` itt **nem hiba** — a nyers fájlok egy részében nincs előnézet
    (ld. a modul fejlécét), ilyenkor a teljes dekódolás jön."""
    rawpy = _rawpy()
    if rawpy is None:
        return None
    try:
        with rawpy.imread(str(source)) as nyers:
            elonezet = nyers.extract_thumb()
    except Exception:  # noqa: BLE001 — a LibRaw sokféle kivétellel jelez
        return None
    formatum = getattr(elonezet, "format", None)
    if formatum is None or getattr(formatum, "name", "") != "JPEG":
        # A bitmap-előnézet (ritka) nem JPEG-bájtfolyam: a hívó
        # `imdecode`-ja nem tudna vele mit kezdeni, essünk a teljes útra.
        return None
    return bytes(elonezet.data)


def nyers_hosszabb_el(source: Path) -> int | None:
    """A nyers fájl TELJES felbontású hosszabb éle képpontban, dekódolás
    nélkül (a LibRaw méret-mezőiből); `None`, ha nem olvasható (#3377).

    A forgatás (`flip`) a két élt felcserélheti, a hosszabbat nem."""
    rawpy = _rawpy()
    if rawpy is None:
        return None
    try:
        with rawpy.imread(str(source)) as nyers:
            meretek = nyers.sizes
            return max(int(meretek.width), int(meretek.height)) or None
    except Exception:  # noqa: BLE001 — a LibRaw sokféle kivétellel jelez
        return None


def dekodol_nyerset(source: Path, goal: int | None = None) -> np.ndarray | None:
    """Nyers fájl → **BGR** `uint8` kép; `None`, ha nem megy (és naplóz).

    `goal`: a hívó célmérete képpontban (bélyegkép-oldal). Ha meg van adva és
    a beágyazott előnézet elég nagy hozzá, a gyors út fut — különben teljes
    demozaikolás.
    """
    rawpy = _rawpy()
    if rawpy is None:
        _log.warning(
            "a nyers fájl nem dekódolható, mert a rawpy nincs telepítve: %s",
            source,
        )
        return None

    if goal is not None:
        kep = _elonezetbol(source, goal)
        if kep is not None:
            return kep

    from picasapy.lazy_cv2 import cv2

    try:
        with rawpy.imread(str(source)) as nyers:
            rgb = nyers.postprocess(output_bps=8, use_camera_wb=True)
    except Exception as hiba:  # noqa: BLE001 — a LibRaw sokféle kivétellel jelez
        _log.warning("a nyers fájl dekódolása nem sikerült (%s): %s", hiba, source)
        return None
    if rgb is None or rgb.size == 0:
        _log.warning("a nyers fájl dekódolása üres képet adott: %s", source)
        return None
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def _elonezetbol(source: Path, goal: int) -> np.ndarray | None:
    """A beágyazott előnézetből dekódolt BGR kép, ha elég nagy a célmérethez."""
    payload = beagyazott_elonezet(source)
    if payload is None:
        return None

    from picasapy.lazy_cv2 import cv2

    kep = cv2.imdecode(np.frombuffer(payload, np.uint8), cv2.IMREAD_COLOR)
    if kep is None:
        return None
    if max(kep.shape[:2]) < goal * _ELONEZET_TARTALEK:
        return None
    return kep


__all__ = [
    "NYERS_KITERJESZTESEK",
    "beagyazott_elonezet",
    "dekodol_nyerset",
    "nyers_utvonal",
]
