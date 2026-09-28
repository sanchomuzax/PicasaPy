"""A régi `grain` / `grain2` (Film Grain) natív munkafüggvénye (#3928).

A spec: `docs/specs/filters-decoded.md`, „⛳ `grain` / `grain2` — a munkafüggvény
kiolvasva" (#3927). A callback (`0x008f88e0`) mindig `a = 0,5`-tel hívja a
munkafüggvényt (`0x0090a2e0`) — a `grain` és a `grain2` paraméter nélküli, fix
erősségű oneclick pár (#347, #3927). A nyolc lépés, egész aritmetikával:

1. zajpuffer W×H×32 bit;
2. generátor: **helyi MT19937**, ugyanazzal a magvető-függvénnyel
   (`0x00aa28f0`, szorzó `0x19660D` = 1664525), mint a `NoiseImageOperation`
   (`nativ_noise.picasa_mt19937`) — csak a mag más (a Picasában három
   egymást követő CRT-`rand()`-ból; nálunk a hívó adja meg, mert a natív mag
   hívásonként változik, tehát úgysem reprodukálható bájtra, #3927 4. jegyzet);
3. erősség: `a = 0,5` ⇒ `k = trunc(256 − 256·a) = 128`;
4. első zajmező, képpontonként egy MT-szó, csatornánként (R = 2., G = 1.,
   B = 0. bájt, mint a `nativ_noise.noise_layer`-ben) a 127 felé húzva
   `k`-val: `bájt' = bájt + ((127 − bájt)·k) >> 8`;
5. simítás háromszor, mindegyik kétirányú (vízszintes, majd függőleges):
   ```
   sorok 0…H−2,  x = 1…W−1:  p[y][x] = (3·p[y][x]      + p[y][x−1])      >> 2
   oszlopok 0…W−2, y = 1…H−1: p[y][x] = (3·p_víz[y][x] + p_eredeti[y−1][x]) >> 2
   ```
   a vízszintes menet **kaszkádol** (balról jobbra haladva a MÁR frissített
   bal szomszédot olvassa — egyetlen soron belüli, sorfüggetlen futó szűrő);
   a függőleges menet viszont a HÍVÁS ELEJÉN vett pillanatképet
   (`p_eredeti`) olvassa szomszédként, a „3×" tag jön csak a vízszintes
   után frissített tömbből. Ez a kombináció (mérve, #3928) adja vissza a
   spec táblázatának mind a négy oszlopát ±0,05-ön belül; a tisztán
   kétirányú kaszkád és a tisztán kétirányú pillanatkép-alapú változat
   egyaránt eltér (ΔE 2,58, ill. 2,72 a célzott 2,67-hez képest).
   Az utolsó sort a vízszintes, az utolsó oszlopot a függőleges menet
   kihagyja;
6. friss zaj visszakeverése, képpontonként egy ÚJ MT-szóval (a folyam
   folytatásából, NEM a 127 felé húzva): `p' = friss + ((p − friss)·210) >> 8`;
7. szürkítés `w = 200`-zal: `Y = (28·B + 151·G + 77·R) >> 8`,
   `C = clamp(C + ((Y − C)·200) >> 8, 0, 255)`;
8. a képre, csatornánként: középtónus-súllyal
   `ki = clamp(c + (((160 − |128 − c|)·(n − 128)) >> 8), 0, 255)`.

Mérve (684-merokeszlet, `grain__alap`): ΔE a Picasa-exporthoz **2,67**
(korábban, egyenletes Gauss-zajjal: 3,23), a tónussávonkénti szórás és a
szomszéd-korreláció a spec „kiolvasott algoritmus" oszlopa szerinti, az
átlagos eltolás −1,96 körüli — ld. a fenti szakaszt a teljes táblázatért.
"""

from __future__ import annotations

import numpy as np

from picasapy.render.nativ_noise import picasa_mt19937

#: `a = 0,5` ⇒ `k = trunc(256 − 256·0,5)`.
_K_BEEGETETT = 128

#: A friss zaj visszakeverésének súlya (`0xd2`).
_VISSZAKEVERES_SULY = 210

#: A szürkítés súlya (`push 0xc8`).
_SZURKITES_SULY = 200

#: A szürkítés Rec.601-hez közeli, de attól eltérő, natívan mért súlyai
#: (`Y = (28·B + 151·G + 77·R) >> 8`, összegük pontosan 256).
_Y_R, _Y_G, _Y_B = 77, 151, 28

#: A középtónus-súlyozás csúcsa (`c = 128`-nál 160/256).
_KOZEPTONUS_CSUCS = 160
_KOZEPTONUS_KOZEP = 128


def _bajtok_rgb(szavak: np.ndarray) -> tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Egy (H, W) `uint32` zajmezőből R/G/B `int32` bájtsíkok (2./1./0. bájt)."""
    bajtok = szavak.astype("<u4").view(np.uint8).reshape(*szavak.shape, 4).astype(np.int32)
    return bajtok[..., 2], bajtok[..., 1], bajtok[..., 0]


def _pull_127_fele(sik: np.ndarray, k: int) -> np.ndarray:
    """`bájt + ((127 − bájt)·k) >> 8` — a 4. lépés, csatornánként."""
    return sik + (((127 - sik) * k) >> 8)


def _vizszintes_kaszkad(p0: np.ndarray, height: int, width: int) -> np.ndarray:
    """A vízszintes menet: soronként (sorfüggetlenül, tehát a H tengely
    marad vektorizált) balról jobbra kaszkádol — az `x`. oszlop a MÁR
    frissített `x−1`. oszlopot olvassa szomszédként. A `width` szerinti
    ciklus elkerülhetetlen (ez egy futó/rekurzív szűrő), de csatornánként
    és a 3 ismétlésen belül csak `width − 1` numpy-hívás, nem
    képpontonkénti Python-ciklus.
    """
    p = p0.copy()
    utolso_sor = height - 1
    for x in range(1, width):
        p[:utolso_sor, x] = (3 * p[:utolso_sor, x] + p[:utolso_sor, x - 1]) >> 2
    return p


def _fuggoleges_pillanatkep(p_viz: np.ndarray, p_eredeti: np.ndarray, width: int) -> np.ndarray:
    """A függőleges menet: a `3×` tag a vízszintes UTÁNI tömbből jön, a
    szomszéd viszont a hívás ELEJI (`p_eredeti`) pillanatképből — ez teljes
    egészében vektorizálható, ciklus nélkül."""
    utolso_oszlop = width - 1
    p = p_viz.copy()
    p[1:, :utolso_oszlop] = (
        3 * p_viz[1:, :utolso_oszlop] + p_eredeti[:-1, :utolso_oszlop]
    ) >> 2
    return p


def _simit_haromszor(sik: np.ndarray) -> np.ndarray:
    """Az 5. lépés: háromszor kétirányú simítás — vízszintesen kaszkádolva,
    függőlegesen a hívás eleji pillanatképet szomszédként olvasva (a két
    irány mérve, #3928, eltérő karakterű: ld. a modul docstringjét)."""
    height, width = sik.shape
    p = sik
    for _ in range(3):
        p_eredeti = p.copy()
        p_viz = _vizszintes_kaszkad(p_eredeti, height, width)
        p = _fuggoleges_pillanatkep(p_viz, p_eredeti, width)
    return p


def apply_native_grain(image: np.ndarray, seed: int) -> np.ndarray:
    """A `grain`/`grain2` munkafüggvénye, a natív nyolc lépés szerint.

    `image` RGB `uint8` (H, W, 3) — a hívó felel az alakellenőrzésért
    (`picasapy.render.curves.validate_image`). `seed` a helyi MT19937
    magja: a Picasában hívásonként más (nem reprodukálható), itt a hívó
    adja meg — rögzített maggal determinisztikus.
    """
    height, width = image.shape[:2]
    szavak = picasa_mt19937(seed, 2 * height * width).reshape(2, height, width)
    kezdeti_szavak, friss_szavak = szavak[0], szavak[1]

    r, g, b = _bajtok_rgb(kezdeti_szavak)
    r = _simit_haromszor(_pull_127_fele(r, _K_BEEGETETT))
    g = _simit_haromszor(_pull_127_fele(g, _K_BEEGETETT))
    b = _simit_haromszor(_pull_127_fele(b, _K_BEEGETETT))

    friss_r, friss_g, friss_b = _bajtok_rgb(friss_szavak)
    r = friss_r + (((r - friss_r) * _VISSZAKEVERES_SULY) >> 8)
    g = friss_g + (((g - friss_g) * _VISSZAKEVERES_SULY) >> 8)
    b = friss_b + (((b - friss_b) * _VISSZAKEVERES_SULY) >> 8)

    y = (_Y_B * b + _Y_G * g + _Y_R * r) >> 8
    r = np.clip(r + (((y - r) * _SZURKITES_SULY) >> 8), 0, 255)
    g = np.clip(g + (((y - g) * _SZURKITES_SULY) >> 8), 0, 255)
    b = np.clip(b + (((y - b) * _SZURKITES_SULY) >> 8), 0, 255)

    kep = image.astype(np.int32)
    kimenet = np.empty_like(kep)
    for csatorna, zaj in enumerate((r, g, b)):
        c = kep[..., csatorna]
        suly = _KOZEPTONUS_CSUCS - np.abs(_KOZEPTONUS_KOZEP - c)
        kimenet[..., csatorna] = np.clip(
            c + ((suly * (zaj - _KOZEPTONUS_KOZEP)) >> 8), 0, 255
        )
    return kimenet.astype(np.uint8)


__all__ = ["apply_native_grain"]
