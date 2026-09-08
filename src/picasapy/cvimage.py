"""Közös OpenCV képsegédek (#151/7).

A bájt-alapú beolvasás (#65 tanulság: a cv2.imread Windowson ékezetes
útvonalon némán None-t ad) és a leghosszabb-oldal-korlátos kicsinyítés
korábban duplikálva élt a thumbnail-cache (`thumbs/cache.py`) és az
exporter (`export/exporter.py`) között — itt az egyetlen igazságforrás.

#294: a redukált JPEG-dekódolás döntése (`reduced_color_flag`) is ide
került — korábban a `thumbs/cache.py::_read_flag`-ben élt, most a
duplikátum-kereső dHash-e (`dedup/phash.py`) is ugyanezt hívja, hogy a
logika ne duplikálódjon.
"""

from __future__ import annotations

import io
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError


# Nagy forráskép redukált (fél/negyed/nyolcad méretű) JPEG-dekódolása kíméli
# a memóriát és nagyságrendet gyorsít; a legerősebb redukcióval kezdünk, és
# az első olyat választjuk, amely még elég pixelt hagy a célmérethez.
#
# #1611: a tábla FÜGGVÉNY, nem modulszintű konstans. Modulszinten a
# `cv2.IMREAD_*` olvasása a BETÖLTÉSKOR behozná az OpenCV-t, és ezzel
# elvenné a lusta import teljes nyereségét — a `cvimage` az indulási
# láncban van (`thumbs/__init__` → `thumbs/cache`).
def _reduced_color_flags() -> tuple[tuple[int, int], ...]:
    return (
        (8, cv2.IMREAD_REDUCED_COLOR_8),
        (4, cv2.IMREAD_REDUCED_COLOR_4),
        (2, cv2.IMREAD_REDUCED_COLOR_2),
    )

# Mintavételi tartalék: a dekódolt kép leghosszabb oldala legalább ennyiszer
# akkora legyen, mint a célméret — így az utána következő kicsinyítésnek
# marad miből átlagolnia (nem lépcsőzik).
_SAMPLING_HEADROOM = 2


def reduced_color_flag(payload: np.ndarray, goal: int) -> int:
    """Dekódolási flag a MÁR beolvasott JPEG-bájtokhoz, `goal` célmérethez.

    A PIL itt csak a fejlécet értelmezi (a fájlt nem nyitja meg újra), így
    a méret-próba olcsó. Ha a fejléc nem olvasható (nem kép, sérült fájl),
    a biztonságos `cv2.IMREAD_COLOR` a válasz — hogy a tartalom egyáltalán
    dekódolható-e, azt a hívó `imdecode`-ja dönti el.
    """
    try:
        with Image.open(io.BytesIO(payload)) as probe:
            longest = max(probe.size)
    except (
        OSError,
        UnidentifiedImageError,
        ValueError,
        Image.DecompressionBombError,
    ):
        return cv2.IMREAD_COLOR
    for factor, flag in _reduced_color_flags():
        if longest // factor >= goal * _SAMPLING_HEADROOM:
            return flag
    return cv2.IMREAD_COLOR


def read_image_bytes(source: Path) -> np.ndarray | None:
    """A forrásfájl bájtjai np.fromfile-lal; None, ha a fájl üres vagy
    nem olvasható (időközben törölt/elérhetetlen NAS-forrás)."""
    try:
        payload = np.fromfile(source, dtype=np.uint8)
    except OSError:
        return None
    if payload.size == 0:
        return None
    return payload


def scale_down(image: np.ndarray, max_dimension: int | None) -> np.ndarray:
    """A leghosszabb oldal korlátozása; felskálázás soha.

    ⚠️ **Ez az ÁLTALÁNOS út, és szándékosan `cv2.INTER_AREA` maradt.** A
    Picasa magja (`picasapy.resample.picasa_kicsinyites`) a
    **bélyegkép-úton** fut — ott mértük, és ott gyorsabb is. Az indoklás:

    A #871 mércéje a Picasa saját `bigthumbs` bélyegkép-tára (119 kép,
    288 képpont), és a mag ott mindhárom metrikán javít (ΔE 2,8247 →
    2,6245, SSIM 0,95484 → 0,96765, RMSE 6,7592 → 5,3889), **ráadásul
    gyorsabb** is: 4000 × 3000 → 288 esetén 23 ms az `INTER_AREA` 56
    ms-a helyett.

    Nagy kimenetnél viszont a 16 csapos mag ára meredeken nő: 4000 × 3000
    → **1600** (tipikus export) 300 ms a 18 ms helyett — **16×**. A
    minőségi nyereség ugyanaz a nagyságrend, az ár nem: egy 200 képes
    export 14 másodpercről 70-re nőne. Bizonyíték nélkül lassítani a
    felhasználó munkáját nem szabad, ezért az export-út a mag
    GYORSÍTÁSÁIG marad az `INTER_AREA`-n — #2669.

    `max_dimension=None` vagy már elég kicsi kép esetén a bemenet
    változatlanul (azonos objektumként) tér vissza."""
    # A gyorsítást a #2669 köre megpróbálta, és NEM sikerült (mérve
    # 2026-09-08, RPi5): nyolc irányból a legjobb 2,0×-t hozott a magon,
    # így a teljes út 16,1× helyett 7,9× — a 3×-os küszöb több mint
    # kétszerese. Már az elő-szűrés önmagában 1,6–1,9×, tehát a magra
    # ~1,2× jutna. A mért ok: a Pythonból hívható `cv2.sepFilter2D` nem
    # decimál és egy szálon fut; a gyors, decimáló OpenCV-utak magja
    # rögzített. Teljes tábla:
    # `docs/benchmarks/2026-09-08-2669-mag-gyorsitas.md`.
    if max_dimension is None:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_dimension:
        return image
    scale = max_dimension / longest
    return cv2.resize(
        image,
        (max(1, round(width * scale)), max(1, round(height * scale))),
        interpolation=cv2.INTER_AREA,
    )


def scale_down_picasa_mag(image: np.ndarray, max_dimension: int | None) -> np.ndarray:
    """Mint a `scale_down`, de a Picasa saját magjával (#871).

    Ezt a **bélyegkép-út** hívja. A mag Lanczos-4, a sugara `4 / lépték`
    szerint tágul (`0x00a3f745`), és a célméret kétszereséig területi
    átlagolás készíti elő — ez az eredeti piramisának a szerepe. A
    részletek és a 2× alatti sáv kivétele: `picasapy.resample`.

    Mérve a Picasa `bigthumbs` tárán (119 kép, 288 képpont): ΔE 2,8247 →
    **2,6245**, SSIM 0,95484 → **0,96765**, RMSE 6,7592 → **5,3889** —
    103/119 képen jobb ΔE-ben, 117/119-en SSIM-ben, romlás egyiken sincs.
    És gyorsabb is: 4000 × 3000 → 288 esetén 23 ms az `INTER_AREA` 56
    ms-a helyett.

    Nagy kimenetre (export) NE ezt hívd, amíg a mag nem gyorsul — ott az
    ár 16× (#2669); az általános út a `scale_down`."""
    from picasapy.resample import picasa_kicsinyites

    if max_dimension is None:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_dimension:
        return image
    scale = max_dimension / longest
    return picasa_kicsinyites(
        image, max(1, round(width * scale)), max(1, round(height * scale))
    )
