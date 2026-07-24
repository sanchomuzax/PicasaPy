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

#294 — REDUKÁLT dekódolás: a hash célmérete 9x8 pixel, ehhez a teljes
felbontású dekódolás (egy 24 MP-es JPEG-nél ~70 MB pixeladat) tiszta
pazarlás volt; a bélyegkép-cache mintájára a közös
`picasapy.cvimage.reduced_color_flag` dönt a fél/negyed/nyolcad méretű
JPEG-beolvasásról. A hash értéke ettől a hasonlósági küszöb (10 bit)
szintjén NEM változik — ld. `tests/dedup/test_phash.py::TestReducedDecoding`.

Dokumentált korlát a redukcióhoz: a Nyquist-határ fölötti, szabályos
nagy-frekvenciás mintázatnál (szintetikus sakktábla, moaré-rács) a
kicsinyítés aliasol, és a hash a teljes felbontásúhoz képest elmozdulhat.
Ez nem a redukció hibája — a teljes felbontású út is aliasol, csak
másképp; ilyen képre a dHash maga sem ad értelmes lenyomatot. Valódi
fényképeken (alacsony frekvenciás fő struktúra) a két út egybeesik.
"""

from __future__ import annotations

from pathlib import Path

import cv2

from picasapy.cvimage import read_image_bytes, reduced_color_flag

_HASH_SIZE = 8  # 8x8 = 64 bites hash

# A redukált beolvasás célmérete. Bőven a 9x8-as hash-rács fölött van: a
# dekódolt kép így legalább ~64 px széles marad, ami az INTER_AREA
# kicsinyítésnek elég mintavételi tartalék, a nagy JPEG-eket viszont már a
# nyolcad méretű (leggyorsabb) úton olvassuk be.
_DECODE_GOAL = 32


def compute_dhash(path: Path, hash_size: int = _HASH_SIZE) -> int | None:
    """A kép dHash-e 64 bites egész számként; `None`, ha nem dekódolható.

    Lépések: (1) a kép REDUKÁLT (a hash-rácshoz mért) felbontású
    beolvasása, (2) szürkeárnyalatossá alakítás és `(hash_size+1) x
    hash_size` méretre kicsinyítés INTER_AREA-val (9x8 az alapértelmezett
    8-as hash-mérethez), (3) soronként a szomszédos pixelek összevetése
    (balról jobbra nagyobb-e) — ez adja a `hash_size * hash_size` bitet."""
    payload = read_image_bytes(path)
    if payload is None:
        return None
    image = cv2.imdecode(payload, reduced_color_flag(payload, _DECODE_GOAL))
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
