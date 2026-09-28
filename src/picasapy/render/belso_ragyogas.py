"""A belső ragyogás (`GlowImageOperation`) natív lánca (#3827).

A `Vignette`, a `Matte`, a `Lomo`, a `Holga`, a `NightVision`, a
`MuseumMatte` és a `Comicize` ragyogása ezen fut. A lánc a rajzoló
(`0x00bb8f70`) két ága szerint épül (spec: `filterdesc-registry.md`, „A belső
ragyogás TELJES lánca a lekicsinyített ágon" és „A teljes felbontású ág és a
MuseumMatte"):

1. **Lépték** — a `0x00bb89b0` (`blur_atvalto`) tengelyenként `f`-et ad. Ha
   mindkettő pontosan 1,0 (`p < 33,33`), a **teljes felbontású** ág fut;
   különben a munkapuffer `csonk(f·W) × csonk(f·H)`, és a blur `f·p`.
2. **Maszk** (`0x00bcbbd0`) — tömör téglalap, a maszk `255 − α`: belül 0, a
   `min(255, csonk(⌈(b − 1)/2⌉·q + 1))` széles perem 255.
3. **Elmosás** (`0x00bcc7b0`) — tengelyenként `q` dobozmenet, előbb
   vízszintesen. A blurt a (peremmel bővített) méret felére vágja; a doboz
   paramétereit a `0x00bc5360` adja (`nativ_blur.sugar_egyutthatok`); a
   pótlás a puffer szélén 255; az osztás csonkol.
4. **Súly** — `a = min(255, (M · csonk(strength · 256)) >> 8)`.
5. **Kimenet** — a lekicsinyített ágon a súlyt a Mitchell-átméretező
   (`B = C = 0,4`, `resize_column_plane`) nagyítja vissza, a keverés
   `⌊(G·a + S·(255 − a)) / 255⌋`; a teljes felbontású ágon
   `((256 − a)·S + a·G) >> 8`.

A `glowalpha` a natív kódban holt paraméter; a MuseumMatte 0,7/0,6-os
áttetszősége a művelet `BlendAlpha`-ja, ezt a lánc keverője teszi rá:
`k′ = csonk(α·256) − 1`, `(be·(255 − k′) + ki·k′) >> 8`.

A render-effekt nem nyúl a lemezhez: képet kap, képet ad.
"""

from __future__ import annotations

import math

import numpy as np

from picasapy.lazy_cv2 import cv2
from picasapy.render.curves import validate_image
from picasapy.render.glimmer_ops import resize_column_plane
from picasapy.render.nativ_blur import sugar_egyutthatok

#: `0x00bb89b0`: a blur-átváltó korlátja (`0x00cf39d0` = 255,0).
_ATVALTO_KORLAT = 255.0
#: `0x00bc52c0`: a maszképítő a blurt `[0, 253]`-ra vágja (`0x00cf0b4c`).
BLUR_MAX = 253.0
#: A perem szélességének felső korlátja (`0x00bcc42c`, `esi = 0xff`).
_PEREM_MAX = 255
#: A `quality` alapértéke a `filterdesc.xml` minden Glow-hívásában.
MINOSEG = 3
#: A 8.8-as fixpont egysége (`0x00cf39d8` = 256,0).
_FIXPONT = 256
_TELJES = 255


def blur_atvalto(blur_px: float, meret: float) -> float:
    """A natív `0x00bb89b0` — a Glow MUNKAPUFFERÉNEK léptéke (#2159).

    ```
    p' = min(p, 255)
    k  = p' / p
    X  = ((100 + d) − d·k) / p'
    f  = (X > 3) ? k : k·X/3
    ```

    `p < 33,33` alatt `f = 1` (a teljes felbontású ág); fölötte a ragyogás
    lekicsinyített képen készül.
    """
    if blur_px <= 0:
        blur_px = 1e-05
    vagott = min(blur_px, _ATVALTO_KORLAT)
    k = vagott / blur_px
    x = ((100.0 + meret) - meret * k) / vagott
    return k if x > 3.0 else k * x / 3.0


def doboz_parameterek(blur: float) -> tuple[int, int, int, int]:
    """A `0x00bc5360` dobozparaméterei a blurból: `(s, a, r, div)`.

    `n = csonk(b)`, `s = 6`, amíg `n > 1`: `s −= 1`, `n >>= 1`;
    `v = csonk((b − 1)·2^(s−1))`, `a = v & (2^s − 1)`, `r = (v >> s) + 1`,
    `div = 2^s + 2v`. A menet: `(a·(be[x−r] + be[x+r]) + 2^s·Σ be[x−r+1 … x+r−1]) / div`.
    """
    s, r, a, div = sugar_egyutthatok(blur)
    return s, a, r, div


def peremsugar(blur: float, minoseg: int = MINOSEG) -> int:
    """A maszk peremének szélessége: `min(255, csonk(⌈(b − 1)/2⌉·q + 1))`."""
    return min(_PEREM_MAX, int(math.ceil((blur - 1.0) * 0.5) * minoseg + 1))


def _dobozmenetek(maszk: np.ndarray, tengely: int, blur: float, minoseg: int) -> np.ndarray:
    """`minoseg` dobozmenet egy tengely mentén, a puffer szélén 255-ös pótlással.

    A pótlás a lineáris szűrőn a kiegészítő maszkkal (`255 − M`, nullás
    peremmel) számolható pontosan: a súlyok összege `div`, tehát
    `Σw·M = 255·div − Σw·(255 − M)`, és a csonkoló osztás ezen fut. A
    részösszeg legfeljebb 64 515, a float32-es szűrő egészen pontos.
    """
    if not blur > 1.0:
        return maszk
    s, a, r, div = doboz_parameterek(blur)
    sulyok = np.full(2 * r + 1, float(1 << s), dtype=np.float32)
    sulyok[0] = sulyok[-1] = float(a)
    egyseg = np.ones(1, dtype=np.float32)
    kx, ky = (sulyok, egyseg) if tengely == 1 else (egyseg, sulyok)
    teljes = _TELJES * div
    for _ in range(minoseg):
        fedes = (_TELJES - maszk.astype(np.int32)).astype(np.float32)
        osszeg = cv2.sepFilter2D(
            fedes, cv2.CV_32F, kx, ky, borderType=cv2.BORDER_CONSTANT
        ).reshape(fedes.shape)
        maszk = ((teljes - np.rint(osszeg).astype(np.int64)) // div).astype(np.uint8)
    return maszk


def ragyogas_maszk(
    magas: int, szeles: int, xblur: float, yblur: float, minoseg: int = MINOSEG
) -> np.ndarray:
    """A tömör téglalap elmosott maszkja (`M`, `magas × szeles`, uint8)."""
    oszlopok, vissza = ragyogas_maszk_oszlopai(magas, szeles, xblur, yblur, minoseg)
    return oszlopok[:, vissza]


def ragyogas_maszk_oszlopai(
    magas: int, szeles: int, xblur: float, yblur: float, minoseg: int = MINOSEG
) -> tuple[np.ndarray, np.ndarray]:
    """A maszk tömör alakban: a különböző oszlopok (`magas × n`) és az
    oszlopindex (`szeles` hosszú); `M = oszlopok[:, vissza]`.

    A puffer a képnél tengelyenként `peremsugar` képponttal nagyobb, a perem
    255; a peremet is mossa, a puffer szélén túl a pótlás 255. A vízszintes
    menetek után minden belső sor ugyanaz (a perem-sorok 255-ök maradnak),
    ezért a függőleges menetek csak a sor KÜLÖNBÖZŐ értékeire futnak
    (legfeljebb 256 oszlop), és az eredmény oszloponként visszaindexelhető —
    bitre ugyanaz, mint a teljes puffer elmosása.
    """
    bx = min(max(float(xblur), 0.0), BLUR_MAX)
    by = min(max(float(yblur), 0.0), BLUR_MAX)
    rx, ry = peremsugar(bx, minoseg), peremsugar(by, minoseg)
    sor = np.full((1, szeles + 2 * rx), _TELJES, dtype=np.uint8)
    sor[0, rx:rx + szeles] = 0
    sor = _dobozmenetek(sor, 1, min(bx, sor.shape[1] * 0.5), minoseg)[0]
    ertekek, vissza = np.unique(sor[rx:rx + szeles], return_inverse=True)
    oszlopok = np.full((magas + 2 * ry, ertekek.size), _TELJES, dtype=np.uint8)
    oszlopok[ry:ry + magas] = ertekek
    oszlopok = _dobozmenetek(oszlopok, 0, min(by, oszlopok.shape[0] * 0.5), minoseg)
    return oszlopok[ry:ry + magas], vissza.reshape(-1)


def ragyogas_suly(maszk: np.ndarray, strength: float) -> np.ndarray:
    """`a = min(255, (M · csonk(strength · 256)) >> 8)` — 8.8-as fixpont."""
    ero = min(max(float(np.float32(strength)), 0.0), float(_TELJES))
    szorzo = int(math.trunc(ero * _FIXPONT))
    tabla = np.minimum(_TELJES, (np.arange(256, dtype=np.int64) * szorzo) >> 8)
    return tabla.astype(np.uint8)[maszk]


#: A két ág keverése: `(súly, forrás) → kimenet`, csatornánként.
_E = np.arange(256, dtype=np.int64)[:, np.newaxis]
_S = np.arange(256, dtype=np.int64)[np.newaxis, :]


def _teljes_felbontasu_tabla(szin: int) -> np.ndarray:
    """A `f = 1` ág: `((256 − e)·S + e·G) >> 8` (`0x00bcbd60`).

    ⚠️ Az `e·G` tag csak feketére MÉRT (ott 0); más színre a képlet
    folytatása, a Picasa-exporton nem kimérve.
    """
    return ((_FIXPONT - _E) * _S + _E * szin) >> 8


def _lekicsinyitett_tabla(szin: int) -> np.ndarray:
    """A `f < 1` ág keverése (`0x008f59d0`): `⌊(G·a + S·(255 − a)) / 255⌋`."""
    return (szin * _E + _S * (_TELJES - _E)) // _TELJES


def _blend_alpha_tabla(tabla: np.ndarray, alpha: float) -> np.ndarray:
    """A művelet `BlendAlpha`-ja (`0x009dc4b0`): `k′ = csonk(α·256) − 1`,
    `(be·(255 − k′) + ki·k′) >> 8`."""
    k = int(math.trunc(float(np.float32(alpha)) * _FIXPONT)) - 1
    return (_S * (_TELJES - k) + tabla * k) >> 8


def _kever(image: np.ndarray, suly: np.ndarray, tablak: list[np.ndarray]) -> np.ndarray:
    """A kimenet csatornánként egyetlen táblázatból: `T[súly, forrás]`.

    A keverés (és a `BlendAlpha`) csak a súlytól és a forrás bájtjától függ,
    ezért egy 256 × 256-os tábla bitre ugyanazt adja, mint a képlet.
    """
    if all(np.array_equal(t, tablak[0]) for t in tablak[1:]):
        lapos = tablak[0].astype(np.uint8).reshape(-1)
        return lapos[(suly.astype(np.uint16) << 8)[..., np.newaxis] | image]
    lapos = np.stack(tablak).astype(np.uint8).reshape(-1)
    csatorna = np.arange(len(tablak), dtype=np.uint32) << 16
    index = ((suly.astype(np.uint32) << 8)[..., np.newaxis] | csatorna) | image
    return lapos[index]


def _lekicsinyitett_suly(
    height: int, width: int, xblur: float, yblur: float,
    strength: float, minoseg: int, fx: np.float32, fy: np.float32,
) -> np.ndarray:
    """A `f < 1` ág súlya: a kis pufferben, Mitchell-nagyítással."""
    kis_w = max(1, int(np.float32(fx * np.float32(width))))
    kis_h = max(1, int(np.float32(fy * np.float32(height))))
    bx = float(np.float32(fx * np.float32(xblur)))
    by = float(np.float32(fy * np.float32(yblur)))
    oszlopok, vissza = ragyogas_maszk_oszlopai(kis_h, kis_w, bx, by, minoseg)
    return resize_column_plane(ragyogas_suly(oszlopok, strength), vissza, width, height)


def inner_glow(
    image: np.ndarray,
    color: tuple[int, int, int],
    xblur: float,
    yblur: float,
    strength: float,
    alpha: float = 1.0,
    quality: int = MINOSEG,
) -> np.ndarray:
    """`GlowImageOperation`: a kép széléről befelé ható ragyogás, natív lánccal.

    `xblur`/`yblur` a `filterdesc.xml` értéke képpontban (NEM Gauss-σ),
    `strength` a 8.8-as szorzó, `alpha` a művelet `BlendAlpha`-ja (1,0-nál
    nincs keverés). `color` csatornasorrendje **RGB**.
    """
    validate_image(image)
    if not alpha > 0.0:
        return image.copy()
    height, width = image.shape[:2]
    minoseg = min(max(int(quality), 1), 15)
    fx = np.float32(blur_atvalto(float(xblur), float(width)))
    fy = np.float32(blur_atvalto(float(yblur), float(height)))
    if fx == 1.0 and fy == 1.0:
        oszlopok, vissza = ragyogas_maszk_oszlopai(height, width, xblur, yblur, minoseg)
        suly = ragyogas_suly(oszlopok, strength)[:, vissza]
        tablak = [_teljes_felbontasu_tabla(int(c)) for c in color]
    else:
        suly = _lekicsinyitett_suly(height, width, xblur, yblur, strength, minoseg, fx, fy)
        tablak = [_lekicsinyitett_tabla(int(c)) for c in color]
    if alpha < 1.0:
        tablak = [_blend_alpha_tabla(t, alpha) for t in tablak]
    return _kever(image, suly, tablak)
