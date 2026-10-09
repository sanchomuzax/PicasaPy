"""A Poszter készítése lapokra vágott képkimenete (#4268).

A mért 200%-os eset két sorba és két oszlopba osztja a forrás képpontjait.
Átfedéskor a szomszédos vágások a lap belső széle felé 10%-kal túlnyúlnak.
Más nagyításoknál a százalék százas értéke adja a sorok és oszlopok számát;
nem négyzetes képnél ugyanezt a rácsot alkalmazzuk mindkét tengelyen.
Ezek a kiterjesztések a mért négyzetes 200%-os példával összhangban álló,
egyszerű szabályok; a specifikáció nem mérte őket.

A papírméret a párbeszédben választható. A vágásra gyakorolt hatása nincs
megmérve, ezért jelenleg nem módosítja a pixelgeometriát.
"""

from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from picasapy.export.exporter import render_photo_pixels
from picasapy.ini import load_or_empty
from picasapy.ini.filters import parse_filters_prefix
from picasapy.lazy_cv2 import cv2
from picasapy.render.chain import normalize_crop_ops
from picasapy.render.flip import FLIP_MASK
from picasapy.scanner import PICASA_INI_NAME

# A 400 px-es mért lap belső élén 40 px-nyi, vagyis 10%-os túlnyúlás látszik.
OVERLAP_RATIO = 0.10
POSTER_MAGNIFICATIONS = tuple(range(200, 1001, 100))
_ROTATE_VALUE = re.compile(r"^rotate\((\d+)\)$")
_FLIPPED_VALUE = re.compile(r"^flipped\((\d+)\)$")


def _tile_bounds(length: int, count: int, index: int, overlap: bool) -> tuple[int, int]:
    """Egy rácscella vágási határa, a belső széleken kiterjesztve."""
    start = index * length // count
    end = (index + 1) * length // count
    if not overlap:
        return start, end

    extension = round((end - start) * OVERLAP_RATIO)
    if index > 0:
        start = max(0, start - extension)
    if index + 1 < count:
        end = min(length, end + extension)
    return start, end


def _render_edited_image(path: Path) -> np.ndarray:
    """A fájl EXIF-tájolású, `.picasa.ini`-ből szerkesztett képpontjai."""
    document = load_or_empty(path.parent / PICASA_INI_NAME)
    section = document.section(path.name)
    filters = section.get("filters") if section else None
    ops = parse_filters_prefix(filters or "")
    crop = section.get("crop") if section else None
    ops = normalize_crop_ops(ops, crop, warning_key=str(path))

    rotate_match = _ROTATE_VALUE.fullmatch(section.get("rotate") or "") if section else None
    rotate_steps = int(rotate_match.group(1)) % 4 if rotate_match else 0
    flip_match = _FLIPPED_VALUE.fullmatch(section.get("flipped") or "") if section else None
    flip_flags = int(flip_match.group(1)) & FLIP_MASK if flip_match else 0
    return render_photo_pixels(
        path,
        ops,
        rotate_steps=rotate_steps,
        flip_flags=flip_flags,
    )


def make_poster_tiles(
    source: str | Path,
    magnification_percent: int,
    paper_size: str,
    overlap: bool,
) -> tuple[Path, ...]:
    """A képet a forrásmappába írt, sorszámozott fájlokra vágja.

    A `paper_size` érték része a nyilvános API-nak, hogy a párbeszéd a
    kiválasztott méretet átadhassa. Mivel csak a 4x6-os eset vágása mért,
    más papírmérethez nem rendelünk kitalált képpontgeometriát.
    """
    path = Path(source)
    if magnification_percent not in POSTER_MAGNIFICATIONS:
        raise ValueError("A poszter nagyítása 200% és 1000% között választható.")
    if not paper_size.strip():
        raise ValueError("A papírméret nincs megadva.")
    if not path.is_file():
        raise FileNotFoundError(path)

    image = _render_edited_image(path)
    if image.size == 0:
        raise ValueError(f"A kép nem olvasható: {path.name}")

    height, width = image.shape[:2]
    count = magnification_percent // 100
    extension = path.suffix.lower() or ".jpg"
    if not cv2.haveImageWriter(extension):
        raise ValueError(f"Nem támogatott képfájl-kiterjesztés: {extension}")

    encoded_pages: list[tuple[Path, bytes]] = []
    for row in range(count):
        top, bottom = _tile_bounds(height, count, row, overlap)
        for column in range(count):
            left, right = _tile_bounds(width, count, column, overlap)
            tile = image[top:bottom, left:right]
            ok, encoded = cv2.imencode(extension, tile)
            if not ok:
                raise OSError(f"A poszterlap nem kódolható: {row}-{column}")
            target = path.with_name(f"{row}-{column}-{path.name}")
            encoded_pages.append((target, encoded.tobytes()))

    for target, data in encoded_pages:
        target.write_bytes(data)
    return tuple(target for target, _data in encoded_pages)


__all__ = ["OVERLAP_RATIO", "POSTER_MAGNIFICATIONS", "make_poster_tiles"]
