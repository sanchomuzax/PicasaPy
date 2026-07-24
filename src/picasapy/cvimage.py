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

import cv2
import numpy as np
from PIL import Image, UnidentifiedImageError

# Nagy forráskép redukált (fél/negyed/nyolcad méretű) JPEG-dekódolása kíméli
# a memóriát és nagyságrendet gyorsít; a legerősebb redukcióval kezdünk, és
# az első olyat választjuk, amely még elég pixelt hagy a célmérethez.
_REDUCED_COLOR_FLAGS = (
    (8, cv2.IMREAD_REDUCED_COLOR_8),
    (4, cv2.IMREAD_REDUCED_COLOR_4),
    (2, cv2.IMREAD_REDUCED_COLOR_2),
)

# Mintavételi tartalék: a dekódolt kép leghosszabb oldala legalább ennyiszer
# akkora legyen, mint a célméret — így az utána következő INTER_AREA
# kicsinyítésnek marad miből átlagolnia (nem lépcsőzik).
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
    for factor, flag in _REDUCED_COLOR_FLAGS:
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
    """A leghosszabb oldal korlátozása INTER_AREA-val; felskálázás soha.

    `max_dimension=None` vagy már elég kicsi kép esetén a bemenet
    változatlanul (azonos objektumként) tér vissza."""
    if max_dimension is None:
        return image
    height, width = image.shape[:2]
    longest = max(width, height)
    if longest <= max_dimension:
        return image
    scale = max_dimension / longest
    new_size = (max(1, round(width * scale)), max(1, round(height * scale)))
    return cv2.resize(image, new_size, interpolation=cv2.INTER_AREA)
