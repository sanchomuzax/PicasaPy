"""#2229: a Glimmer `AutoFix` vágás NÉLKÜLI min–max szinthúzás.

A `render/glimmer_ops.py` `autofix`-e eddig a natív „Jó napom van"
(`0x009db610`) megfejtett modelljét hívta, **0,30-as vágópont-keveréssel**
(#535, #721). A Glimmer `AutoFixImageOperation` viszont **másik kódút**, és
a munkavégzője (`0x00bc2d70`) mást csinál:

1. három **egyszerű** 256 rekeszes hisztogram (`0x00bc2e50`) — vágás,
   súlyozás, percentilis **nincs** benne;
2. csatornánként LUT (`0x00bc3170`):

```
lo = az első nem üres rekesz,  hi = az utolsó nem üres rekesz
lo == hi  ->  LUT[x] = 255
egyébként ->  LUT[x] = clamp(round((x − lo)/(hi − lo) · 255 + 0,5), 0, 255)
```

A `255,0` és a `0,5` konstans kiolvasva (`0x00cf39d0`, `0x00c72150`).

A két függvény az EREDETIBEN is különbözik — a #535/#721 a **natív**
parancsot mérte, ez a jegy a **Glimmer**-műveletet.

## #3797 — a hisztogram 1000 képpont fölött pontmintán számol

A fenti munkavégző 1000 képpont fölött NEM a teljes képből veszi a
hisztogramot, hanem egy kb. 1000 képpontos, legközelebbi szomszéd
pontmintából (`0x00bc2ea6`, `0x00bc2f40`): `s = sqrt(float32(1000/(w·h)))`,
`nW = max(1, trunc(w·s + 0,5))`, `nH = max(1, trunc(h·s + 0,5))`. A minta a
`diag(w/nW, h/nH)` mátrixszal, 16.16 fixpontban vetíti vissza a
mintaképpont közepét (`+0,5`) — ugyanaz a mintavevő, mint a
`QuantizePalette`-ben (`render/quantize_palette.py`, `pontminta_racs`). A
LUT-ot ezután a TELJES képre alkalmazza.

Mérve (684-merokeszlet, `analyze_validation_kit.mean_de`, CIE76 átlag-ΔE a
Picasa-exporthoz; a jegy táblázatának + 0,05-ös tűrésével):

| effekt · eset | ma (teljes kép) | 1000 képpontos pontminta |
|---|---:|---:|
| `PencilSketch` alap | 1,953 | **0,129** |
| `PencilSketch` min | 2,942 | **0,018** |
| `Cinemascope` alap | 1,367 | **1,097** |
| `Holga` alap / min | 0,890 / 0,678 | **0,750 / 0,500** |
| `Sixties` alap / min | 1,179 / 1,255 | **1,033 / 1,136** |
| `NightVision` alap / min | 4,626 / 3,673 | **4,595 / 3,663** |

Egyik eset sem romlik. A `NightVision`/`Holga`/`Cinemascope`/`Sixties`
frissített golden-értékei: `test_noise_mt19937_3736.py`.

Fejlesztés: #3797.
"""

# rontás-kontroll: a `_AUTOFIX_MINTA_KUSZOB` 100000-re írva (a pontminta
# gyakorlatilag soha nem fut) → 5 failed
# (`test_a_mintameret_a_kepletet_koveti`,
# `test_a_vekony_sotet_vonal_kimarad_a_mintabol` és a három golden eset
# lent: PencilSketch alap/min, Holga min); az `_autofix_mintameret` `+ 0,5`
# nélkül (csak `trunc(w·s)`) → 4 failed
# (`test_a_mintameret_a_kepletet_koveti` és ugyanaz a három golden eset).
# Ellenőrizve lefuttatva.

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.render.glimmer_ops import _autofix_mintameret, autofix


def _kep(ertekek: list[int]) -> np.ndarray:
    """Egysoros, szürke kép a megadott értékekből (mindhárom csatorna)."""
    sor = np.array(ertekek, dtype=np.uint8)
    return np.repeat(sor[np.newaxis, :, np.newaxis], 3, axis=2)


def test_a_teljes_min_max_tartomanyt_huzza_szet() -> None:
    """A legkisebb 0-ra, a legnagyobb 255-re megy — vágópont nélkül."""
    ki = autofix(_kep([64, 96, 128, 160, 192]))
    assert ki[0, 0, 0] == 0
    assert ki[0, -1, 0] == 255


def test_a_kozepso_ertek_a_kepletet_koveti() -> None:
    """`round((x − lo)/(hi − lo)·255 + 0,5)` — a 128 a 64…192 sávban
    pontosan félúton van, tehát 128."""
    ki = autofix(_kep([64, 96, 128, 160, 192]))
    assert int(ki[0, 2, 0]) == 128


def test_egyetlen_kiugro_keppont_is_szamit() -> None:
    """A VÁGÓPONTOS modell egy magányos szélső képpontot eldobna; a
    min–max szinthúzás NEM — ez a két modell szétválasztó esete."""
    ki = autofix(_kep([0] + [200] * 200 + [255]))
    # lo = 0, hi = 255 -> az azonosság-leképezés
    assert int(ki[0, 1, 0]) == 200
    assert int(ki[0, 0, 0]) == 0
    assert int(ki[0, -1, 0]) == 255


def test_egyszinu_kep_eseten_MINDEN_255() -> None:
    """`lo == hi` -> a natív ág fixen 255-öt ír a LUT minden rekeszébe."""
    ki = autofix(_kep([77] * 8))
    assert np.all(ki == 255)


def test_csatornankent_kulon_hisztogram() -> None:
    """A LUT csatornánként épül — az egyik csatorna szűk sávja nem
    befolyásolja a másikét."""
    kep = np.zeros((1, 3, 3), dtype=np.uint8)
    kep[0, :, 0] = [10, 20, 30]     # kék: szűk sáv
    kep[0, :, 1] = [0, 128, 255]    # zöld: teljes sáv
    kep[0, :, 2] = [100, 100, 100]  # vörös: egyszínű
    ki = autofix(kep)
    assert list(ki[0, :, 0]) == [0, 128, 255]
    assert list(ki[0, :, 1]) == [0, 128, 255]
    assert list(ki[0, :, 2]) == [255, 255, 255]


def test_a_felezopontok_LEFELE_csonkolnak_nem_paros_fele() -> None:
    """A natív út a `0x00c29990`-en megy, ami **`cvttsd2si`** — csonkol.

    A `+ 0,5` maga a felfelé kerekítés idiómája; `np.round`-dal kétszer
    kerekítenénk, és a numpy bankár-kerekítése a felezőpontokat PÁROS felé
    vinné. Ez a próba az a szétválasztó eset, ahol a kettő eltér.
    """
    # lo = 0, hi = 254 -> a 100-as bemenet nyers értéke 100,3937…,
    # a 101-esé 101,4015… ; a +0,5 után 100,89 és 101,90 -> 100 és 101.
    kep = _kep(list(range(0, 255)))
    ki = autofix(kep)
    varhato = [
        min(255, max(0, int((x - 0) / 254 * 255.0 + 0.5)))  # Python int() = csonkolás
        for x in range(0, 255)
    ]
    assert list(ki[0, :, 0]) == varhato


# ---------------------------------------------------------------------------
# #3797 — a hisztogram mintája
# ---------------------------------------------------------------------------


class TestAMintameret:
    def test_a_mintameret_a_kepletet_koveti(self) -> None:
        """960 × 640-nél 39 × 26 (a jegy példája)."""
        assert _autofix_mintameret(960, 640) == (39, 26)

    def test_1000_keppont_alatt_nincs_mintavetel(self) -> None:
        """`≤ 1000` képpontnál a teljes kép számít — ezt a
        `test_a_teljes_min_max_tartomanyt_huzza_szet` és a többi apró,
        5–255 képpontos próba fent már lefedi (nem sűrűsödnek pontmintára)."""
        kep = np.full((10, 100, 3), 100, dtype=np.uint8)  # 1000 képpont
        kep[0, 0] = 0
        kep[0, -1] = 255
        ki = autofix(kep)
        assert int(ki[0, 0, 0]) == 0
        assert int(ki[0, -1, 0]) == 255

    def test_a_legalabb_1_meret_also_hatara(self) -> None:
        """Extrém keskeny/lapos kép esetén `nW`/`nH` sosem 0."""
        nW, nH = _autofix_mintameret(100000, 1)
        assert nW >= 1 and nH >= 1


def test_a_vekony_sotet_vonal_kimarad_a_mintabol() -> None:
    """100×100-as (10 000 képpontos) kép: az alap 200-as, a 0. sor 50-es —
    a pontminta rácsa (`nW=nH=32`) a 0. sort NEM tartalmazza (ld. a jegy
    listáját: `test_glimmer_autofix_2229` rontás-kontrollja alatt). A
    hisztogram tehát csak a 200-as alapot látja: `lo == hi`, a natív ág a
    TELJES csatornát 255-re írja — a vonal is 255 lesz, NEM 0, holott a
    teljes képes hisztogram (lo=50, hi=200) a vonalat 0-ra húzná.
    """
    kep = np.full((100, 100, 3), 200, dtype=np.uint8)
    kep[0, :, :] = 50
    ki = autofix(kep)
    assert np.all(ki[1:] == 255), "az alap tartomány magára 255-re nyúlik (lo == hi)"
    assert np.all(ki[0] == 255), "a vonal kimaradt a mintából, tehát NEM 0-ra húz"


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal (684-
# merokeszlet), a `test_noise_mt19937_3736.py` mintájára.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: A jegy táblázatának + 0,05-ös tűrése.
_TURES = 0.05

#: (címke, fájlnév, lánc, a pontmintás mérés ΔE-je a jegyből)
_GOLDEN_ESETEK = [
    (
        "PencilSketch alap",
        "pencilsketch__alap.jpg",
        "PencilSketch=1,2.000000,100.000000,0.000000;",
        0.129,
    ),
    (
        "PencilSketch min",
        "pencilsketch__min.jpg",
        "PencilSketch=1,1.300000,0.000000,0.000000;",
        0.018,
    ),
    ("Holga min", "holga__min.jpg", "Holga=1,0.000000,0.000000,0.000000;", 0.500),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(
    ("cimke", "nev", "lanc", "vart_de"), _GOLDEN_ESETEK, ids=[e[0] for e in _GOLDEN_ESETEK]
)
def test_golden_a_684_merokeszlettel_a_hatarertek_alatt(cimke, nev, lanc, vart_de):
    load, mean_de = _golden_eszkozok()
    from picasapy.ini.filters import parse_filters
    from picasapy.render.chain import apply_filters

    forras = load(_KIT / nev)
    export = load(_KIT / "export" / nev)
    kep = apply_filters(forras, parse_filters(lanc)).image
    de = mean_de(kep, export)
    assert de <= vart_de + _TURES, f"{cimke}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"
