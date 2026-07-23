"""Perceptual hash (dHash) számítás hasonló képek felderítéséhez (#31).

Döntés (dokumentált alapértelmezés, ld. `similar.py`): **dHash** (gradiens-
alapú), nem aHash — a dHash kevésbé érzékeny egyenletes fényerő-eltolásra
(pl. újratömörítés utáni finom világosodás/sötétedés), mert nem az átlaghoz,
hanem a szomszédos pixelekhez viszonyít.

A kép beolvasása a projekt közös, ékezetes-útvonal-tűrő rétegén
(`picasapy.cvimage.read_image_bytes` + `cv2.imdecode`) megy — ugyanaz az út,
amit a thumbnail-cache is használ. A `cv2.imdecode` alapból alkalmazza az
EXIF-orientációt (ld. `thumbs/cache.py` és `tests/thumbs/test_cache.py::
test_exif_orientation_applied`), ezért a hash a megjelenítési orientáció
szerint készül — egy 90°-kal elforgatott, de egyébként azonos kép hash-e
NEM fog egyezni a normál orientációjú társáéval (ez a réteg dokumentált
korlátja: nem forgatás-invariáns, csak EXIF-orientáció-helyes).
"""

from __future__ import annotations

from pathlib import Path

import cv2

from picasapy.cvimage import read_image_bytes

_HASH_SIZE = 8  # 8x8 = 64 bites hash


def compute_dhash(path: Path, hash_size: int = _HASH_SIZE) -> int | None:
    """A kép dHash-e 64 bites egész számként; `None`, ha nem dekódolható.

    Lépések: (1) a kép szürkeárnyalatos (2) `(hash_size+1) x hash_size`
    méretre kicsinyítése INTER_AREA-val (9x8 az alapértelmezett 8-as
    hash-mérethez), (3) soronként a szomszédos pixelek összevetése
    (balról jobbra nagyobb-e) — ez adja a `hash_size * hash_size` bitet."""
    payload = read_image_bytes(path)
    if payload is None:
        return None
    image = cv2.imdecode(payload, cv2.IMREAD_COLOR)
    if image is None:
        return None
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    resized = cv2.resize(
        gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA
    )
    diff = resized[:, 1:] > resized[:, :-1]
    value = 0
    for bit in diff.flatten():
        value = (value << 1) | int(bit)
    return value


def hamming_distance(a: int, b: int) -> int:
    """Két hash eltérő bitjeinek száma (0 = megegyező kép-lenyomat)."""
    return bin(a ^ b).count("1")
