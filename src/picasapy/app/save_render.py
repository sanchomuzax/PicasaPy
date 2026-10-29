"""A mentéshez szükséges kép-renderelés: a szerkesztések beégetése egy képfájlba.

Ugyanaz a renderelő-út, mint az exportnál (`picasapy.render.chain`), így a
mentett fájl és a rácsban látott kép egyezik. A modul csak OLVAS a lemezről;
a kiírás a `picasapy.edit.save` dolga.
"""


from __future__ import annotations

from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.cvimage import read_image_bytes
from picasapy.edit.session import EditSession
from picasapy.ini import PhotoCropReader
from picasapy.render.chain import apply_filters, normalize_crop_ops
from picasapy.render.flip import apply_flip
from picasapy.scanner import PICASA_INI_NAME

from .paint_mask import maszk_vonasokbol, van_mentett_ecsetvonas

_CROP_READER = PhotoCropReader()


def _render_for_save(
    path: Path,
    rotate_steps: int,
    filters: str,
    flip_flags: int = 0,
    paint_strokes: tuple = (),
) -> np.ndarray:
    """A képfájl a szerkesztésekkel BEÉGETVE, OpenCV BGR-ben.

    A forgatás, a tükrözés (#2902) és a `filters=` lánc ugyanazon a
    renderelő-úton megy, mint az exportnál - a mentett fájl és a rácsban
    látott kép így egyezik.

    `paint_strokes`: a szerkesztő munkamenetében élő festés vonásai (#3462).
    A vonások a FORGATATLAN forrás terében vannak (az előnézet ott futtatja a
    láncot), ezért a maszk a forrás méretén épül, és a képpel azonos módon
    tükröződik és fordul.
    """
    # ⛔ #3120: ez az EGYETLEN képbetöltő hely, amit SZÁNDÉKOSAN nem
    # kötöttünk át a nyerset is ismerő `cvimage.dekodolj_forrast`-ra.
    #
    # A mentés a képet a SAJÁT HELYÉRE írja vissza (az eredetit a
    # `.picasaoriginals`-ba téve). Nyers fájlnál ez nem megy: DNG/CR2/NEF
    # írása nincs az OpenCV-ben, tehát az átkötés a legjobb esetben néma
    # hibát, a legrosszabban SÉRÜLT FÁJLT adna a felhasználó nyers képe
    # helyén. Ma ehelyett a dekódolás áll meg - a fájl érintetlen marad.
    #
    # Amit az eredeti tesz (a szerkesztést JPEG-ként a nyers MELLÉ menti),
    # az a jegy szerint MÉRENDŐ, nem kitalálandó. Amíg nincs mérve, a
    # biztonságos viselkedés a hibaüzenet.
    #
    # Őr: `tests/test_nyers_kozos_dekoder_3120.py::TestAMentesNEMIrRaNyerset`
    payload = read_image_bytes(path)
    if payload is None:
        raise ValueError(f"Üres vagy nem olvasható fájl: {path}")
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        raise ValueError(f"Nem dekódolható kép: {path}")
    # #3065: ELŐBB a tükrözés, UTÁNA a forgatás - a mért sorrend (ld. az
    # `export/exporter.py` azonos megjegyzését és a `render/flip.py`
    # modul-docstringjét).
    ops = EditSession.from_value(filters).ops
    maszk = (
        maszk_vonasokbol(
            paint_strokes,
            image.shape[0],
            image.shape[1],
            filters=ops,
        )
        if paint_strokes or van_mentett_ecsetvonas(ops)
        else None
    )
    image = apply_flip(image, flip_flags)
    steps = int(rotate_steps or 0) % 4
    for _ in range(steps):
        image = cv2.rotate(image, cv2.ROTATE_90_CLOCKWISE)
    crop, crop_ini_readable = _CROP_READER.read(
        path.parent / PICASA_INI_NAME, path.name
    )
    ops = normalize_crop_ops(
        ops,
        crop,
        crop_ini_readable=crop_ini_readable,
        warning_key=str(path),
    )
    if not ops:
        return image
    if maszk is not None:
        maszk = apply_flip(maszk, flip_flags)
        for _ in range(steps):
            maszk = cv2.rotate(maszk, cv2.ROTATE_90_CLOCKWISE)
    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
    rendered, _skipped = apply_filters(rgb, ops, paint_mask=maszk)
    return cv2.cvtColor(rendered, cv2.COLOR_RGB2BGR)
