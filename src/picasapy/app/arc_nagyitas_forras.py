"""Az arc-nagyítás (#2187) forrásképe az EREDETI fájlból.

Kis arcnál a bélyegkép-tár egyik szintje sem elég nagy ahhoz, hogy a
kivágott négyzet elérje a cella méretét (`arc_nagyitas_url.
szukseges_hosszabb_el`). Ilyenkor az eredeti fájlt dekódoljuk a szükséges
méretre — ugyanazzal a redukált beolvasással és Picasa-maggal, mint a tár
(`thumbs.cache`), és ugyanazzal a nem-destruktív forgatással/tükrözéssel,
mint a szolgáltató `_render`-je, hogy a relatív arc-keret (ami a
MEGJELENÍTETT képre vonatkozik) ugyanarra a pontra essen.

A kimenet NEM kerül a lemez-gyorstárba: a Qt az URL szerint tartja a kész
képet, és a tár szintjei a rács méreteihez igazodnak, nem az arcokhoz.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PySide6.QtGui import QImage, QTransform

from picasapy.cvimage import read_image_bytes, reduced_color_flag, scale_down_picasa_mag
from picasapy.lazy_cv2 import cv2
from picasapy.rawdecode import nyers_utvonal
from picasapy.render.flip import FLIP_HORIZONTAL, FLIP_VERTICAL
from picasapy.scanner.filetypes import VIDEO_EXTENSIONS


def arc_eredetibol(
    ut: Path, hosszabb: int, rotate: int = 0, flip: int = 0
) -> QImage | None:
    """Az eredeti kép `hosszabb` élűre kicsinyítve (nagyítás soha), a
    megjelenítés forgatásával és tükrözésével; `None`, ha nem olvasható.

    Videó és nyers (RAW) fájl `None`: ott a tár képe a legjobb, amink van
    — a képkocka-kinyerés és a LibRaw egy csempéért túl drága."""
    if ut.suffix.lower() in VIDEO_EXTENSIONS or nyers_utvonal(ut):
        return None
    payload = read_image_bytes(ut)
    if payload is None:
        return None
    bgr = cv2.imdecode(payload, reduced_color_flag(payload, hosszabb))
    if bgr is None:
        return None
    rgb = np.ascontiguousarray(
        cv2.cvtColor(scale_down_picasa_mag(bgr, hosszabb), cv2.COLOR_BGR2RGB)
    )
    mag, szel = rgb.shape[:2]
    kep = QImage(
        rgb.data, szel, mag, rgb.strides[0], QImage.Format.Format_RGB888
    ).copy()
    if rotate:
        kep = kep.transformed(QTransform().rotate(90 * rotate))
    if flip:
        kep = kep.mirrored(
            bool(flip & FLIP_HORIZONTAL), bool(flip & FLIP_VERTICAL)
        )
    return kep


__all__ = ["arc_eredetibol"]
