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
5. simítás háromszor, mindegyik kétirányú (vízszintes, majd függőleges),
   **helyben, nem rekurzívan** — a spec szó szerint: „az előző szomszédot a
   tárolás előtt olvassa", ugyanazzal a képlettel mindkét tengelyen:
   ```
   sorok 0…H−2,  x = 1…W−1:  p[y][x] = (3·p_bemenet[y][x] + p_bemenet[y][x−1]) >> 2
   oszlopok 0…W−2, y = 1…H−1: p[y][x] = (3·p_bemenet[y][x] + p_bemenet[y−1][x]) >> 2
   ```
   ahol `p_bemenet` az adott MENET (nem a háromszori ismétlés) eleji
   pillanatkép: a vízszintes menetnél az előző menet kimenete, a
   függőleges menetnél a VÍZSZINTES menet kimenete (nem a hívás eleji
   állapot). Mindkét menet teljes egészében vektorizálható, Python-ciklus
   nélkül. Az utolsó sort a vízszintes, az utolsó oszlopot a függőleges
   menet kihagyja;
6. friss zaj visszakeverése, képpontonként egy ÚJ MT-szóval (a folyam
   folytatásából, NEM a 127 felé húzva): `p' = friss + ((p − friss)·210) >> 8`;
7. szürkítés `w = 200`-zal: `Y = (28·B + 151·G + 77·R) >> 8`,
   `C = clamp(C + ((Y − C)·200) >> 8, 0, 255)`;
8. a képre, csatornánként: középtónus-súllyal
   `ki = clamp(c + (((160 − |128 − c|)·(n − 128)) >> 8), 0, 255)`.

Mérve (grain-kit, `grain__alap`, 8 mag átlaga): ΔE a Picasa-exporthoz
**2,674**, átlagos eltolás **−1,95**, tónussávonkénti szórás
**2,49 / 4,42 / 5,51 / 4,39 / 2,36**, vízszintes/függőleges
szomszéd-korreláció **0,283 / 0,283** — a spec táblázatának mind a négy
oszlopát visszaadja, ld. a fenti szakaszt a teljes táblázatért.
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
    """Egy (H, W) `uint32` zajmezőből R/G/B `int16` bájtsíkok (2./1./0. bájt).

    `int16` (nem `int32`): a 4. lépés (`_pull_127_fele`) és az 5. lépés
    háromszori kétirányú simítása (`_simit_haromszor`) — a legtöbbször
    futtatott, teljes képméretű numpy-hívások — matematikailag bizonyítottan
    a `[63, 191]` tartományban maradnak (a `_pull_127_fele` a bájtot a 127
    felé húzza, a simítás pedig konvex kombináció, tehát nem léphet ki a
    bemenet tartományából), így `int16`-ban felezett memóriasávszélességgel,
    hűen futnak. A `apply_native_grain` a visszakeverés (6. lépés) ELŐTT
    `int32`-re bővíti vissza — az ottani `·210` szorzás a mért tartományban
    (kb. −38 000…35 000) már `int16`-ban túlcsordulna."""
    bajtok = szavak.astype("<u4").view(np.uint8).reshape(*szavak.shape, 4).astype(np.int16)
    return bajtok[..., 2], bajtok[..., 1], bajtok[..., 0]


def _pull_127_fele(sik: np.ndarray, k: int) -> np.ndarray:
    """`bájt + ((127 − bájt)·k) >> 8` — a 4. lépés, csatornánként."""
    return sik + (((127 - sik) * k) >> 8)


def _vizszintes_pillanatkep(p_eredeti: np.ndarray, height: int, width: int) -> np.ndarray:
    """A vízszintes menet: pillanatkép-alapú, NEM rekurzív — mind az önmagát,
    mind a szomszédot adó tag a menet ELŐTTI (`p_eredeti`) állapotból jön
    (a spec 5. lépése: „az előző szomszédot a tárolás előtt olvassa"), tehát
    teljes egészében vektorizálható, soronkénti Python-ciklus nélkül."""
    utolso_sor = height - 1
    p = p_eredeti.copy()
    p[:utolso_sor, 1:] = (3 * p_eredeti[:utolso_sor, 1:] + p_eredeti[:utolso_sor, :-1]) >> 2
    return p


def _fuggoleges_pillanatkep(p_viz: np.ndarray, width: int) -> np.ndarray:
    """A függőleges menet: pillanatkép-alapú, NEM rekurzív — mind az önmagát,
    mind a szomszédot adó tag a vízszintes menet UTÁNI (a függőleges menet
    ELŐTTI) `p_viz` állapotból jön, ugyanazzal a képlettel, mint a
    vízszintes menet. Teljes egészében vektorizálható."""
    utolso_oszlop = width - 1
    p = p_viz.copy()
    p[1:, :utolso_oszlop] = (3 * p_viz[1:, :utolso_oszlop] + p_viz[:-1, :utolso_oszlop]) >> 2
    return p


def _simit_haromszor(sik: np.ndarray) -> np.ndarray:
    """Az 5. lépés: háromszor kétirányú simítás, mindkét irány pillanatkép-
    alapú (nem rekurzív), azonos képlettel — a spec szó szerint: „helyben,
    nem rekurzívan (az előző szomszédot a tárolás előtt olvassa)". A
    függőleges menet szomszédja a vízszintes menet UTÁNI (a függőleges menet
    ELŐTTI) állapot, nem a háromszori ismétlés eleji."""
    height, width = sik.shape
    p = sik
    for _ in range(3):
        p = _vizszintes_pillanatkep(p, height, width)
        p = _fuggoleges_pillanatkep(p, width)
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
    # int32-re bővítve: a `·210` szorzás túlcsordulna `int16`-ban (ld.
    # `_bajtok_rgb` docsztringje).
    r = friss_r.astype(np.int32) + (
        ((r.astype(np.int32) - friss_r) * _VISSZAKEVERES_SULY) >> 8
    )
    g = friss_g.astype(np.int32) + (
        ((g.astype(np.int32) - friss_g) * _VISSZAKEVERES_SULY) >> 8
    )
    b = friss_b.astype(np.int32) + (
        ((b.astype(np.int32) - friss_b) * _VISSZAKEVERES_SULY) >> 8
    )

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
