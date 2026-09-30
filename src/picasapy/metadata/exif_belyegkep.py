"""Az export EXIF-bélyegképe, ahogy az eredeti Picasa készíti (#3998).

Spec: `docs/specs/picasa-metaadat-tulajdonsagok.md` 16. H) és I).

* **Mikor:** csak ha a kimenet szélessége ÉS magassága is > 300 (`kell_belyegkep`).
* **Méret:** `s = min(160,499/w, 160,499/h)`, `w′ = kerekít(float32(w·s + 1e-5))`
  (a `fistp` alapállása: legközelebbi, félre páros), `W = (w′ + 7) & ~7`
  (`belyegkep_meret`). A teljes kép nyújtva tölti ki a W × H-t.
* **Kicsinyítés:** 2×2-es előfelezés (`⌊(a+b+c+d)/4⌋`, a páratlan utolsó
  oszlop/sor eldobva), amíg a forrás mindkét oldala ≥ 2× a cél; utána egy
  Lanczos-3 menet (`resize_image(..., lanczos3=True)`).
* **JPEG:** q85 (IJG-táblák), 4:2:0, baseline, optimalizált Huffman, JFIF 1.01,
  sűrűségegység 0, 1:1. Ha az EXIF-blokk nem fér az APP1-be, a hívó a
  minőséget 15-tel csökkenti (`MINOSEGEK`: 85 → 10).
* Az ICC-átalakítás alapból ki van kapcsolva (`EnableColorManagement` = 0),
  nálunk sincs.

A bemenet a kimeneti kép képpontjai (a csatornasorrend közömbös: a menetek
csatornánként azonosak).
"""

from __future__ import annotations

import cv2
import numpy as np

from picasapy.render.glimmer_ops import resize_image

#: a küszöb: a szélesség és a magasság ennél NAGYOBB kell legyen
KUSZOB = 300
_HOSSZU_OLDAL = 160.499
_EPSZILON = 1e-5
#: az EXIF-író minőség-visszalépése: 85 → 70 → 55 → 40 → 25 → 10
MINOSEGEK = (85, 70, 55, 40, 25, 10)


def kell_belyegkep(meret: tuple[int, int]) -> bool:
    """`meret` = a kimenet `(szélesség, magasság)`-a."""
    return meret[0] > KUSZOB and meret[1] > KUSZOB


def belyegkep_meret(szelesseg: int, magassag: int) -> tuple[int, int]:
    """A bélyegkép `(W, H)`-ja: `0x009b4aa0`, `0x009ecef7`–`0x009ecf0e`."""
    s = min(_HOSSZU_OLDAL / szelesseg, _HOSSZU_OLDAL / magassag)

    def kerekit(oldal: int) -> int:
        return int(np.rint(np.float32(oldal * s + _EPSZILON)))

    def nyolcra(oldal: int) -> int:
        return (oldal + 7) & ~7

    return nyolcra(kerekit(szelesseg)), nyolcra(kerekit(magassag))


def felez(kep: np.ndarray) -> np.ndarray:
    """Egy 2×2-es doboz-átlag csatornánként: `⌊(a+b+c+d)/4⌋`; a páratlan
    utolsó sor/oszlop eldobódik (`0x00a43290`–`0x00a43337`, nincs `+2`)."""
    magas, szeles = kep.shape[0] // 2 * 2, kep.shape[1] // 2 * 2
    k = kep[:magas, :szeles].astype(np.uint16)
    osszeg = k[0::2, 0::2] + k[0::2, 1::2] + k[1::2, 0::2] + k[1::2, 1::2]
    return (osszeg >> 2).astype(np.uint8)


def elofelezett(kep: np.ndarray, cel_szeles: int, cel_magas: int) -> np.ndarray:
    """Felez, amíg `src.w ≥ 2·dst.w` ÉS `src.h ≥ 2·dst.h` (az egyenlőség is)."""
    while kep.shape[1] >= 2 * cel_szeles and kep.shape[0] >= 2 * cel_magas:
        kep = felez(kep)
    return kep


def kicsinyitett(kep: np.ndarray) -> np.ndarray:
    """A bélyegkép képpontjai: előfelezés, majd Lanczos-3 a W × H-ra."""
    szeles, magas = belyegkep_meret(kep.shape[1], kep.shape[0])
    forras = elofelezett(kep, szeles, magas)
    return resize_image(forras, szeles, magas, lanczos3=True)


def kodol(kicsi: np.ndarray, minoseg: int = MINOSEGEK[0]) -> bytes:
    """A kicsinyített kép JPEG-je (spec 16. H) 4.): baseline, 4:2:0,
    optimalizált Huffman; a JFIF 1.01/1:1/0-s egység a kódoló alapja."""
    ok, buf = cv2.imencode(
        ".jpg",
        np.ascontiguousarray(kicsi),
        [
            cv2.IMWRITE_JPEG_QUALITY,
            int(minoseg),
            cv2.IMWRITE_JPEG_OPTIMIZE,
            1,
            cv2.IMWRITE_JPEG_PROGRESSIVE,
            0,
            cv2.IMWRITE_JPEG_SAMPLING_FACTOR,
            cv2.IMWRITE_JPEG_SAMPLING_FACTOR_420,
        ],
    )
    if not ok:
        raise ValueError("a bélyegkép JPEG-kódolása nem sikerült")
    return buf.tobytes()


def belyegkep(kep: np.ndarray, minoseg: int = MINOSEGEK[0]) -> bytes:
    """A kép EXIF-bélyegképe JPEG-ként."""
    return kodol(kicsinyitett(kep), minoseg)
