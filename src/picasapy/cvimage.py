"""Közös OpenCV képsegédek (#151/7).

A bájt-alapú beolvasás (#65 tanulság: a cv2.imread Windowson ékezetes
útvonalon némán None-t ad) és a leghosszabb-oldal-korlátos kicsinyítés
korábban duplikálva élt a thumbnail-cache (`thumbs/cache.py`) és az
exporter (`export/exporter.py`) között — itt az egyetlen igazságforrás.
"""

from __future__ import annotations

from pathlib import Path

import cv2
import numpy as np


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
