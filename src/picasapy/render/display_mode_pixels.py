"""A megjelenítési módok pixelműveletei és előszámított táblái."""

from __future__ import annotations

from picasapy.lazy_cv2 import cv2
import numpy as np

from picasapy.render.display_modes import (
    _LINEAR_GAMMA_TABLE,
    LUMA_WEIGHTS_RGB,
    _MAC_GAMMA_TABLE,
    OVERFLOW_MARK_RGB,
    PIXEL_AFFECTING_MODES,
    SEPIA_BLEND_RGB,
    SEPIA_LIGHTEN_MULTIPLIER,
)

def _luma_tabla() -> np.ndarray:
    """Csatornánkénti `súly · érték` tábla uint16-ban (spec 5.7 1. fele).

    `cv2.LUT`-kész `(1, 256, 3)` alak. A **uint16** kimenet szándékos: a
    legnagyobb részszorzat `151 · 255 = 38505` nem férne 8 bitre, a három
    csatorna összege (`65280`) viszont még uint16-ban is elfér, tehát az
    összegzés túlcsordulás nélkül, **egészben** elvégezhető.
    """
    ertekek = np.arange(256, dtype=np.uint16)
    tabla = np.empty((1, 256, 3), dtype=np.uint16)
    for csatorna, suly in enumerate(LUMA_WEIGHTS_RGB):
        tabla[0, :, csatorna] = ertekek * np.uint16(suly)
    return tabla


def _szepia_tabla() -> np.ndarray:
    """A szépia 2–4. lépése `Y`-nal indexelt `(1, 256, 3)` uint8 táblává.

    A szépia teljes egészében a lumából származik (az 1. lépés mindhárom
    csatornára ugyanazt az `Y`-t teríti szét), ezért a maradék három lépés
    **egyetlen, 256 soros keresőtáblává** előszámolható — a képpontonkénti
    munka így egy `cv2.LUT` hívás.

    A számítás végig `int32`-n megy, de minden lépés a mért **egész**
    aritmetika: `>> 8` levágás, nem osztás és nem kerekítés.
    """
    y = np.arange(256, dtype=np.int32)
    # 2. lépés — világosítás: xor 0xFF → ·218 → >>8 → xor 0xFF.
    v1 = 255 - (((255 - y) * SEPIA_LIGHTEN_MULTIPLIER) >> 8)
    # 3. lépés — a mért `((v1 >> 7) & 0x010101) · 0xFF` csatornánkénti alakja:
    # 0xFF, ha az érték felső bitje áll (≥ 128), különben 0x00.
    maszk = ((v1 >> 7) & 1) * 0xFF
    # 4. lépés — a maszkkal tükrözött érték kétszerese.
    v2 = (v1 ^ maszk) * 2
    tabla = np.empty((1, 256, 3), dtype=np.uint8)
    for csatorna, keveroszin in enumerate(SEPIA_BLEND_RGB):
        # …szorzás a szintén tükrözött keverőszínnel, `>> 8`, majd vissza.
        tabla[0, :, csatorna] = (((v2 * (keveroszin ^ maszk)) >> 8) ^ maszk).astype(
            np.uint8
        )
    return tabla


#: A luma-súlytábla — egyszer épül fel, modulszinten.
_LUMA_TABLE: np.ndarray = _luma_tabla()

#: A szépia `Y → (R, G, B)` táblája — egyszer épül fel, modulszinten.
_SEPIA_TABLE: np.ndarray = _szepia_tabla()

def display_mode_changes_pixels(mode: str) -> bool:
    """Mozdít-e ez a mód képpontot? (Ismeretlen/üres módra `False`.)"""
    return mode in PIXEL_AFFECTING_MODES


def mark_overflow(rgb: np.ndarray) -> np.ndarray:
    """A tökéletesen fehér képpontok átfestése `#FF7F7F`-re (`ID_VIEW_OV`).

    A bemenet `(H, W, 3)` uint8 RGB-tömb. A visszaadott tömb **új**, ha volt
    mit jelölni — a bemenetet SOHA nem írjuk át helyben, mert a hívó
    (edit-előnézet) gyorsítótárazott köztes eredményt ad át, és annak
    megmérgezése a mód kikapcsolása után is festve hagyná a képet.

    Ha nincs jelölendő képpont, a bemenetet adja vissza változatlanul (a
    hívók nem mutálnak, tehát a másolat itt fölösleges munka volna).

    **Mérve** (RPi5, 4000×3000, `min` 5 futásból): kifehéredett folt nélkül
    34 ms, ~5 %-nyi folttal 58 ms, végig fehér képen 117 ms. A néző valódi
    előnézeti mérete (2560 px-es élhossz) mellett ~24 ms. A kézenfekvő
    alakok LASSABBAK: a `(r == 255) & (g == 255) & (b == 255)` maszk és a
    `kép[maszk] = szín` háromdimenziós szórás együtt 2–4-szeres idő
    (68/127/469 ms), a `min(axis=2)` pedig 5–10-szeres. Ezért készül a maszk
    bitenkénti ÉS-sel, és ezért csatornánként (kétdimenziós nézeten) írunk.
    """
    if rgb is None or rgb.ndim != 3 or rgb.shape[2] != 3:
        return rgb
    # `(r & g & b) == 255` pontosan akkor igaz, ha MINDHÁROM csatorna 255 —
    # ez maga a mért `and esi, 0xffffff` + `cmp esi, 0xffffff`, tűrés nélkül.
    mask = (rgb[:, :, 0] & rgb[:, :, 1] & rgb[:, :, 2]) == 255
    if not mask.any():
        return rgb
    marked = rgb.copy()
    for channel, value in enumerate(OVERFLOW_MARK_RGB):
        # `marked[:, :, channel]` NÉZET — a beírás a másolatba megy.
        plane = marked[:, :, channel]
        plane[mask] = value
    return marked


def _rgb_kep_e(rgb: np.ndarray) -> bool:
    """`(H, W, 3)` uint8 tömb-e? (A hívó bármit átadhat.)"""
    return (
        rgb is not None
        and getattr(rgb, "ndim", 0) == 3
        and rgb.shape[2] == 3
        and rgb.dtype == np.uint8
    )


def _tablat_alkalmaz(rgb: np.ndarray, table: np.ndarray) -> np.ndarray:
    """256 elemű tábla mindhárom csatornára, ÚJ tömbbe.

    A `cv2.LUT` nulla kiterjedésű képre `None`-t ad — az üres tömb így a
    másolatával tér vissza (a hívó mindig új, írható tömböt kap).
    """
    if rgb.size == 0:
        return rgb.copy()
    return cv2.LUT(rgb, table)


def darken(rgb: np.ndarray, multiplier: int) -> np.ndarray:
    """Egyenletes sötétítés `c' = (c · multiplier) >> 8` (spec 5.4/5.5).

    Mindhárom csatorna UGYANAZT a szorzót kapja, tehát **színeltolás nincs**
    — ez a mért viselkedés, nem hiányosság (ld. a modul-docstringet az „LCD
    fehérpont" félrevezető feliratáról).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**. A
    bemenetet SOHA nem írjuk át helyben: a hívó (edit-előnézet)
    gyorsítótárazott köztes eredményt ad át, és annak megmérgezése a mód
    kikapcsolása után is sötéten hagyná a képet.

    A számítás 256 elemű táblává előszámolva megy (`cv2.LUT`): a tábla maga
    az egész aritmetika, tehát a kerekítés bitre a mért `>> 8` levágása.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    # `arange` uint16-on: 255 · 246 = 62730 nem fér 8 bitre, a `>> 8` UTÁN
    # viszont már igen. Ez maga a mért egész aritmetika, lebegőpont nélkül.
    table = ((np.arange(256, dtype=np.uint16) * int(multiplier)) >> 8).astype(
        np.uint8
    )
    return _tablat_alkalmaz(rgb, table)


def apply_linear_gamma(rgb: np.ndarray) -> np.ndarray:
    """A lineáris gamma (2,2) keresőtáblája csatornánként (spec 12.4).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    🟡 A tábla (`LINEAR_GAMMA_LUT`) **SZÁMÍTOTT**, és ez a hű alak: az
    eredeti a `0x00d32cd0` táblát futásidőben tölti fel a
    `round(pow(i/255, 1/2,2) · 255)` képlettel. A binárisba beégetett
    `0x00d32bd0` tábla NEM ezé a módé, hanem a Mac gammáé (#3068).
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(rgb, _LINEAR_GAMMA_TABLE)


def apply_mac_gamma(rgb: np.ndarray) -> np.ndarray:
    """A `Mac gamma (1.6)` világosítása (#1730).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    🔴 A tábla (`MAC_GAMMA_LUT`) **MÉRT adat**: a binárisba beégetett
    `0x00d32bd0` 256 bájtja (spec 5.9). Képlettel helyettesíteni tilos —
    a legjobb illesztés (`p = 0,6945`) is 37 helyen téved.

    ⚠️ A MENÜFELIRAT („Mac gamma (1.6)") ÉS A TÁBLA NEM EGYEZIK: a tábla
    effektív gammája ≈1,44. Ez az EREDETI sajátossága, nem a mi hibánk, és
    a hűség a táblát követi. A #1580 képernyőkép-mérése (133,5 → 154,5)
    kereszt-ellenőrzés: az irány és a nagyságrend stimmel, a pontos érték
    a felvétel körülményeitől függ (#3068).

    A 0 és a 255 fixpont marad, tehát a fekete nem mosódik szürkévé, a
    fehér nem csordul ki.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(rgb, _MAC_GAMMA_TABLE)


def luma(rgb: np.ndarray) -> np.ndarray:
    """A mért egész luma `(H, W)` uint8 síkja: `(77·R + 151·G + 28·B) >> 8`.

    A számítás **végig egész**: a csatornánkénti szorzatokat egy uint16
    kimenetű `cv2.LUT` adja, az összegzés uint16-ban megy (a legnagyobb
    lehetséges összeg `65280`, tehát nem csordul túl), és a `>> 8` levágás
    — nem kerekítés. Lebegőpontos úton (`cv2.addWeighted`, `cv2.transform`
    float mátrixszal) a kerekítés miatt csatornánként ±1 eltérés keletkezne
    az eredetitől.

    ⚠️ **Előfeltétel:** a bemenet `(H, W, 3)` uint8, nem üres tömb — ez a
    függvény NEM ellenőriz. A védett belépési pont az `apply_display_bw`.
    Szándékosan nincs a `picasapy.render` csomagszintű névterében sem: ott
    a `luma` név összekeverhető volna a `glimmer_ops` LEBEGŐPONTOS,
    Rec.601-es `luma`-jával, ami egészen mást számol.
    """
    sulyozott = cv2.LUT(rgb, _LUMA_TABLE)
    osszeg = sulyozott[:, :, 0] + sulyozott[:, :, 1] + sulyozott[:, :, 2]
    return (osszeg >> 8).astype(np.uint8)


def apply_display_bw(rgb: np.ndarray) -> np.ndarray:
    """Fekete-fehér MEGJELENÍTÉSI mód: a luma mindhárom csatornára (spec 5.7).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**. A
    bemenetet SOHA nem írjuk át helyben: a hívó (edit-előnézet)
    gyorsítótárazott köztes eredményt ad át, és annak megmérgezése a mód
    kikapcsolása után is szürkén hagyná a képet.

    ⚠️ **Nem azonos a szerkesztő `bw` effektjével** (`render/color.py`):
    az a mentett képre ír és a `filters=` láncba kerül, ez csak a
    képernyőre hat. A képletük a #3613 óta ugyanaz, ld. a modul-docstringet.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    if rgb.size == 0:
        return rgb.copy()
    szurke = luma(rgb)
    return cv2.merge((szurke, szurke, szurke))


def apply_display_sepia(rgb: np.ndarray) -> np.ndarray:
    """Szépia MEGJELENÍTÉSI mód: a mért négylépéses műveletsor (spec 5.8).

    A bemenet `(H, W, 3)` uint8 RGB-tömb; a visszaadott tömb **új**.

    Az 1. lépés a fekete-fehér móddal azonos luma, a 2–4. lépés pedig
    `Y`-tól függ csak, ezért egyetlen előszámolt táblából (`_SEPIA_TABLE`)
    olvasható ki. A lépéssort ld. a modul-docstringben: **a nevét
    („overlay") nem valósítjuk meg, csak a mért műveleteket** — a szokásos
    overlay `/255`-tel normalizál, a mért kód `>> 8`-cal.

    ⚠️ **Nem azonos a szerkesztő `sepia` effektjével** (`render/color.py`):
    az a mentett képre ír, ez csak a képernyőre hat.
    """
    if not _rgb_kep_e(rgb):
        return rgb
    return _tablat_alkalmaz(apply_display_bw(rgb), _SEPIA_TABLE)
