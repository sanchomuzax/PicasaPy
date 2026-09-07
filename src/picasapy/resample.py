"""A Picasa `ytResampler` Lanczos-4 magja (#871).

Az eredeti Picasa **minden** átméretezése ugyanezen a szűrőcsaládon megy
át; a tagot a `ResampleFilter2` beállítás választja ki, és az
**alapértéke 6 = Lanczos-4** (`0x00a3f51c`). A mag betű szerint
(`0xa3feed`, `docs/specs/filters-decoded.md`):

    w(x) = sinc(πx) · sinc(πx/4),   |x| ≥ 4 → 0

⚠️ **A `cv2.INTER_LANCZOS4` NEM ez.** Az OpenCV magja rögzített, 8 csapos,
és **nem tágul** kicsinyítéskor — így a nagy kicsinyítéseket aliasolja. A
Picasáé viszont igen: a mag szélessége `sugár / lépték`
(`0x00a3f745`–`0x00a3f74b`), vagyis kicsinyítéskor a mag a **forrásban**
szélesedik, és a magas frekvenciákat rendesen levágja. A különbség mérve
a tulajdonos valódi Picasa-bélyegképein — a részletek a #871-ben.

A Lanczos-lépés tisztán NumPy; az OpenCV-t csak az elő-szűréshez hívjuk,
és azt is a lusta proxyn át — a `cvimage` az indulási láncban van
(`thumbs/__init__` → `thumbs/cache`), ott a modulszintű `cv2` elvenné a
lusta import nyereségét (#1611).
"""

from __future__ import annotations

import numpy as np

from picasapy.lazy_cv2 import cv2

#: A 6-os mód tartósugara (`0xa40550` ugrótábla, `0x00a3f6c2`).
SUGAR = 4.0

#: A `0xc7d9c8` konstans: a második sinc `1/4`-es zsugorítása.
_MASODIK_LEBENY = 0.25


def lanczos4_suly(x: np.ndarray) -> np.ndarray:
    """A Lanczos-4 súlyfüggvény: `sinc(πx) · sinc(πx/4)`.

    A `0xa3feed` ág betű szerint: `fabs` → `x > 4,0` esetén 0 → `a = x·π`,
    `b = x·0,25·π` → `sin(a)/a · sin(b)/b` (a nullosztást mindkét helyen
    1-re váltva, ahogy az eredeti is).
    """
    tav = np.abs(np.asarray(x, dtype=np.float64))
    suly = np.zeros(tav.shape, dtype=np.float64)
    belul = tav < SUGAR
    if not belul.any():
        return suly
    a = tav[belul] * np.pi
    b = tav[belul] * (_MASODIK_LEBENY * np.pi)
    # A 0 helyen a sinc értéke 1 — az osztást előbb ártalmatlanná tesszük,
    # hogy ne fusson „0/0" figyelmeztetés.
    a_biztos = np.where(a == 0.0, 1.0, a)
    b_biztos = np.where(b == 0.0, 1.0, b)
    elso = np.where(a == 0.0, 1.0, np.sin(a_biztos) / a_biztos)
    masodik = np.where(b == 0.0, 1.0, np.sin(b_biztos) / b_biztos)
    suly[belul] = elso * masodik
    return suly


def _tengely_sulyok(be: int, ki: int) -> tuple[np.ndarray, np.ndarray]:
    """Egy tengely mintavételi indexei és súlyai — `(ki, csapok)` alakban.

    A mag szélessége `sugár / lépték` (`0x00a3f745`): kicsinyítéskor a
    mag a FORRÁSBAN tágul, nagyításnál (lépték ≥ 1) marad a 4-es sugár.
    A képen kívülre eső csapokat a szélső képpontra kötjük (szegély-
    ismétlés), a súlyokat pedig fázisonként 1-re normáljuk — az eredeti
    súlytáblája is így áll (a spec mérése: „a súlyok összege minden
    fázisban pontosan 1,0").
    """
    leptek = ki / be
    skala = min(leptek, 1.0)
    szelesseg = SUGAR / skala
    # A célképpont közepe a forrás koordinátáiban.
    kozep = (np.arange(ki, dtype=np.float64) + 0.5) / leptek - 0.5
    elso = np.floor(kozep - szelesseg + 0.5).astype(np.int64)
    csapok = int(np.ceil(2.0 * szelesseg)) + 2
    index = elso[:, None] + np.arange(csapok, dtype=np.int64)[None, :]
    suly = lanczos4_suly((index - kozep[:, None]) * skala)
    index = np.clip(index, 0, be - 1)
    osszeg = suly.sum(axis=1, keepdims=True)
    suly = np.divide(suly, np.where(osszeg == 0.0, 1.0, osszeg))
    return index, suly.astype(np.float32)


def _tengely_menten(kep: np.ndarray, index: np.ndarray, suly: np.ndarray) -> np.ndarray:
    """Súlyozott összegzés a 0. tengely mentén (a szeparábilis fél-lépés).

    A bemenetet **összefüggőnek** várja: a soronkénti gyűjtés nem
    összefüggő (transzponált nézeten képzett) tömbön nagyságrenddel
    lassabb, ezért a hívó másol, mielőtt a másik tengelyre fordul.
    """
    alak = (index.shape[0],) + kep.shape[1:]
    eredmeny = np.zeros(alak, dtype=np.float32)
    sulyalak = (-1,) + (1,) * (kep.ndim - 1)
    for csap in range(index.shape[1]):
        eredmeny += suly[:, csap].reshape(sulyalak) * kep[index[:, csap]]
    return eredmeny


def lanczos4_kicsinyites(
    kep: np.ndarray,
    cel_szelesseg: int,
    cel_magassag: int,
    *,
    vagas: bool = True,
) -> np.ndarray:
    """Átméretezés a Picasa Lanczos-4 magjával (szeparábilisan).

    Args:
        kep: 2D (szürkeárnyalatos) vagy 3D (csatornás) `uint8` kép.
        cel_szelesseg: a kimenet szélessége képpontban.
        cel_magassag: a kimenet magassága képpontban.
        vagas: ha hamis, a **nyers** (vágatlan, `float32`) jel jön vissza —
            ezen látszik a negatív lebenyek túllövése, amit a 8 bites
            vágás elrejt. Csak mérésre/őrzésre való.

    Returns:
        `uint8` kép (`vagas=True`), vagy `float32` nyers jel.
    """
    if cel_szelesseg < 1 or cel_magassag < 1:
        raise ValueError(
            f"A célméretnek pozitívnak kell lennie: "
            f"{cel_szelesseg}x{cel_magassag}"
        )
    magassag, szelesseg = kep.shape[:2]
    # A `uint8` bemenetet NEM alakítjuk előre `float32`-vé: a súlyozott
    # összegzés úgyis lebegőpontos eredményt ad, a teljes forrás
    # átalakítása viszont fölös memóriaforgalom (nagy képen ~20% idő).
    munka = kep
    if cel_magassag != magassag:
        index, suly = _tengely_sulyok(magassag, cel_magassag)
        munka = _tengely_menten(munka, index, suly)
    if cel_szelesseg != szelesseg:
        index, suly = _tengely_sulyok(szelesseg, cel_szelesseg)
        forgatott = np.ascontiguousarray(np.swapaxes(munka, 0, 1))
        munka = np.swapaxes(_tengely_menten(forgatott, index, suly), 0, 1)
    if not vagas:
        return np.asarray(munka, dtype=np.float32)
    return np.clip(np.rint(munka, dtype=np.float32), 0, 255).astype(np.uint8)


#: Az elő-szűrés célja: a Lanczos-lépés a célméret ennyiszereséről induljon.
#:
#: Az eredeti ugyanezt a szerepet **piramissal** tölti be (ismételt,
#: csonkoló 2 × 2 doboz-felezés ≥ 2× kicsinyítésnél, `0x00a42ec9`). Mi az
#: elő-szűrést **pontos arányú** területi átlagolásra cseréltük, mert a
#: tulajdonos valódi Picasa-bélyegképein (119 fotó, `bigthumbs`, 288 px)
#: az mérten JOBBAN egyezett, mint a felezés-lánc — a szerkezet (doboz
#: elő-szűrés + Lanczos-4 a maradékra) ugyanaz. A mért számok a #871-ben.
ELO_SZURES_SZORZO = 2


def felezo_mag() -> np.ndarray:
    """A **pontosan 2 : 1** lépés rögzített, 16 csapos Lanczos-4 magja.

    2 : 1 léptéknél a célképpont közepe a forrásban `2i + 0,5`, tehát
    minden célképpont ugyanazon a fázison áll — a súlytábla egyetlen
    sorra zsugorodik, és a lépés `cv2.sepFilter2D`-vel elvégezhető.
    Ez teszi a fő utat gyorssá; a mag ettől ugyanaz marad.
    """
    eltolas = np.arange(-7, 9, dtype=np.float64)
    suly = lanczos4_suly((eltolas - 0.5) * 0.5)
    return (suly / suly.sum()).astype(np.float32)


#: A 16 csapos mag horgonya (a `2i` forrásképponthoz tartozó rekesz).
_FELEZO_HORGONY = 7


def _gyors_felezes(kep: np.ndarray) -> np.ndarray:
    """Pontosan 2 : 1 kicsinyítés a rögzített maggal, OpenCV-vel."""
    mag = felezo_mag().reshape(-1, 1)
    szurt = cv2.sepFilter2D(
        kep,
        cv2.CV_32F,
        mag,
        mag,
        anchor=(_FELEZO_HORGONY, _FELEZO_HORGONY),
        borderType=cv2.BORDER_REPLICATE,
    )
    return np.clip(np.rint(szurt[0::2, 0::2]), 0, 255).astype(np.uint8)


def picasa_kicsinyites(
    kep: np.ndarray, cel_szelesseg: int, cel_magassag: int
) -> np.ndarray:
    """Kicsinyítés a Picasa útján: doboz elő-szűrés, majd Lanczos-4.

    Nagy kicsinyítésnél a mag `4 / lépték` sugara sok száz csapossá nőne,
    ami feleslegesen drága. Az elő-szűrés a célméret kétszereséig
    területi átlagolással visz le (ez a piramis szerepe az eredetiben),
    a záró Lanczos-4 pedig a maradék **pontosan 2 : 1** arányt méretezi —
    és épp ezen a rögzített arányon lesz a mag egyfázisú, tehát gyors.

    Ha a forrás nincs meg a célméret kétszeresében (enyhe, 2× alatti
    kicsinyítés), elő-szűrés nélkül, az általános — lassabb — úton megy.

    Args:
        kep: `uint8` kép (2D vagy csatornás).
        cel_szelesseg: a kimenet szélessége.
        cel_magassag: a kimenet magassága.
    """
    magassag, szelesseg = kep.shape[:2]
    elo_szelesseg = cel_szelesseg * ELO_SZURES_SZORZO
    elo_magassag = cel_magassag * ELO_SZURES_SZORZO
    if szelesseg < elo_szelesseg or magassag < elo_magassag:
        return lanczos4_kicsinyites(kep, cel_szelesseg, cel_magassag)
    if (szelesseg, magassag) != (elo_szelesseg, elo_magassag):
        kep = cv2.resize(
            kep, (elo_szelesseg, elo_magassag), interpolation=cv2.INTER_AREA
        )
    return _gyors_felezes(kep)
