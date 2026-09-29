"""#3735: a `SimpleColorMatrix` (összekapcsolás nélkül) képpontra ható
sorrendje FÉNYERŐ → KONTRASZT, nem KONTRASZT → FÉNYERŐ.

A mag a részmátrixokat jobbról szorozza a gyűjtőhöz, a kész mátrix pedig
oszlopvektort szoroz (`docs/specs/filterdesc-registry.md`, „⛔ A
`SimpleColorMatrix` KÉPPONTRA ható sorrendje FORDÍTOTT"). Ebből a képpontra
(összekapcsolás nélkül, színárnyalat és telítettség nélkül) csatornánként:

    out = k·(x + b) + (1 − k)·63,5        (NEM: k·x + (1 − k)·63,5 + b)

ahol `k = 1 + kontraszt_gorbe(contrast)`, `b` a fényerő. A korábbi kód a
fényerőt a kontraszt UTÁN, skálázás nélkül adta hozzá — ez a `Boost`, a
`Lomo`, a `CrossProcess` és a `NightVision` kimenetét tévesztette el a
Picasa-exporthoz képest.

Mérve (684-merokeszlet, `analyze_validation_kit.py` módszerével, CIE76
átlag-ΔE a Picasa-exporthoz):

| eset | rossz sorrend (előtte) | helyes sorrend (#3735, itt) |
|---|---:|---:|
| `Boost` max (100) | 13,071 | **0,095** |
| `Boost` alap (50) | 2,686 | **0,143** |
| `Lomo` alap / min | 1,046 / 1,021 | **0,453 / 0,442** |
| `CrossProcess` alap | 0,883 | **0,807** |
| `NightVision` min (−50 / −50) | 10,813 | **5,436** |

A `TwoTone` (a `ContrastAndBrightnessLinked` ág, `linked=True`) NEM érintett:
ΔE alap/max/min = 0,546 / 0,121 / 0,670 — változatlan a javítás előtt/után.
"""

# rontás-kontroll: a kontraszt+fényerő összefűzése
# (`glimmer_ops._szinmatrix_osszefuzve`) visszaállítva a régi sorrendre (`k*image_f + t + b`, a fényerő a kontraszt UTÁN, skálázás
# nélkül) → 14 failed (a `TestAKepletSorrendjeCiBiztos` mind a 8 CI-biztos
# esete + a `test_a_684_merokeszlettel_a_hatarertek_alatt` mind a 6 golden
# esete; a `test_a_twotone_linked_ag_...` NEM buktat, mert a `linked=True`
# ágat a mutáció nem érinti). A meglévő `test_glimmer_ops.py` és
# `test_crossprocess_tint_3452.py` tesztek ezt NEM kapják el, mert azok
# kizárólag `contrast=0` VAGY `brightness=0` mellett mérnek.

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import glimmer_ops as g
from picasapy.render.chain import apply_filters

# ---------------------------------------------------------------------------
# 1. CI-BIZTOS rész: nincs képfájl-függősége, mindenhol lefut.
#
# A `k = 1 + kontraszt_gorbe(contrast)` táblát külön teszt fedi
# (`TestKontrasztGorbe`, `test_glimmer_ops.py`) — itt csak azt rögzítjük,
# hogy a `simple_color_matrix` a fényerőt és a kontrasztot a FENTI
# képlet szerint, ABBAN a sorrendben fűzi össze.
# ---------------------------------------------------------------------------


def _k(contrast: float) -> float:
    return 1.0 + g._kontraszt_gorbe(contrast)


def _vart_helyes_sorrend(x: float, contrast: float, brightness: float) -> float:
    """A #3735 utáni, helyes képlet: `out = k·(x+b) + (1-k)·63,5`."""
    k = _k(contrast)
    return float(np.clip(k * (x + brightness) + (1.0 - k) * 63.5, 0.0, 255.0))


def _vart_regi_hibas_sorrend(x: float, contrast: float, brightness: float) -> float:
    """A #3735 ELŐTTI, hibás képlet: `out = k·x + (1-k)·63,5 + b`."""
    k = _k(contrast)
    return float(np.clip(k * x + (1.0 - k) * 63.5 + brightness, 0.0, 255.0))


_REPREZENTATIV_ESETEK = [
    (100.0, 40.0, -20.0),
    (150.0, 20.0, 20.0),
    (60.0, -60.0, 30.0),
    (163.0, 50.0, -30.0),
]


class TestAKepletSorrendjeCiBiztos:
    """Kézzel levezetett képlet vs. a `simple_color_matrix` kimenete —
    képfájl nélkül, CI-n is fut."""

    @pytest.mark.parametrize(("x", "contrast", "brightness"), _REPREZENTATIV_ESETEK)
    def test_a_helyes_keplettel_egyezik(self, x, contrast, brightness):
        pixel = np.array([[[x, x, x]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=brightness, contrast=contrast)
        # #3951: a fixpontos alkalmazó (`+ 2`, `>> 2`) a felezőpontot FELFELÉ
        # kerekíti (`202,5 → 203`), a Python `round` páros felé (`→ 202`).
        vart = int(np.floor(_vart_helyes_sorrend(x, contrast, brightness) + 0.5))
        assert int(result[0, 0, 0]) == vart

    @pytest.mark.parametrize(("x", "contrast", "brightness"), _REPREZENTATIV_ESETEK)
    def test_a_regi_hibas_keplettel_ELTER(self, x, contrast, brightness):
        """Fog-ellenőrzés: ha valaki visszaállítja a régi sorrendet, ez a
        négy eset legalább egyike biztosan lebuktatja (a képletek itt
        legalább 1 egész szinttel eltérnek)."""
        pixel = np.array([[[x, x, x]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=brightness, contrast=contrast)
        regi = round(_vart_regi_hibas_sorrend(x, contrast, brightness))
        assert int(result[0, 0, 0]) != regi

    def test_linked_ag_valtozatlan(self):
        """A `ContrastAndBrightnessLinked` (`linked=True`) ág külön kódút —
        ezt a #3735 nem érinti, a forgáspontja marad 127,5."""
        pixel = np.array([[[227, 227, 227]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, contrast=50.0, brightness=0.0, linked=True)
        assert result[0, 0, 0] == 255  # 2*227 - 127.5 = 326.5 -> vágva (változatlan #904 óta)

    def test_csak_fenyero_valtozatlan(self):
        """`contrast=0` esetén `k=1`, a formula `out = x + b` — ugyanaz,
        mint a #3735 előtt."""
        pixel = np.array([[[100, 100, 100]]], dtype=np.uint8)
        result = g.simple_color_matrix(pixel, brightness=50.0, contrast=0.0)
        assert result[0, 0, 0] == 150


# ---------------------------------------------------------------------------
# 2. FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal (684-
# merokeszlet). A NAS-os mérőkészlet mintájára (`test_blur_nativ_3493.py`,
# `test_polaroid_keretmeret_1144.py`): ha a kit nincs a gépen, a teszt
# skip-pel lép ki — ez NEM hiba, csak ismert korlát (CI-n és felhős
# körben sosem érhető el).
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: (címke, forrásfájl, lánc, export-fájl, a helyes sorrenddel mért ΔE) — a
#: jegy táblázatából (#3735), `analyze_validation_kit.py`-vel mérve.
_GOLDEN_ESETEK = [
    ("Boost alap", "boost__alap.jpg", "Boost=1,50.000000;", "boost__alap.jpg", 0.143),
    ("Boost max", "boost__max.jpg", "Boost=1,100.000000;", "boost__max.jpg", 0.095),
    ("Lomo alap", "lomo__alap.jpg", "Lomo=1,50.000000,0.000000;", "lomo__alap.jpg", 0.453),
    ("Lomo min", "lomo__min.jpg", "Lomo=1,0.000000,0.000000;", "lomo__min.jpg", 0.442),
    (
        "CrossProcess alap",
        "crossprocess__alap.jpg",
        "CrossProcess=1,0.000000;",
        "crossprocess__alap.jpg",
        0.807,
    ),
    (
        "NightVision min",
        "nightvision__min.jpg",
        "NightVision=1,-50.000000,-50.000000,0.000000;",
        "nightvision__min.jpg",
        5.436,
    ),
]

#: A táblázat + 0,05-ös tűrése (a jegy „Kész, ha" listája szerint).
_TURES = 0.05


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(
    ("cimke", "forras_nev", "lanc", "export_nev", "vart_de"),
    _GOLDEN_ESETEK,
    ids=[eset[0] for eset in _GOLDEN_ESETEK],
)
def test_a_684_merokeszlettel_a_hatarertek_alatt(cimke, forras_nev, lanc, export_nev, vart_de):
    import sys

    gyoker = Path(__file__).resolve().parents[2]
    if str(gyoker / "tools" / "golden") not in sys.path:
        sys.path.insert(0, str(gyoker / "tools" / "golden"))
    from compare_render import _read_rgb, delta_e_cie76

    forras = _read_rgb(_KIT / forras_nev)
    export = _read_rgb(_KIT / "export" / export_nev)
    report = apply_filters(forras, parse_filters(lanc))
    de = float(delta_e_cie76(report.image, export).mean())
    assert de <= vart_de + _TURES, f"{cimke}: ΔE {de:.3f} > {vart_de + _TURES:.3f} (várt {vart_de})"


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
def test_a_twotone_linked_ag_a_684_merokeszlettel_nem_romlott():
    """A `TwoTone` (`linked=True`) a #3735 javítás UTÁN is a mért
    0,546/0,121/0,670 sávban marad (alap/max/min) — a rontás-kontroll
    része: ha a javítás véletlenül a linked ágat is módosítaná, ez itt
    kifutna."""
    import sys

    gyoker = Path(__file__).resolve().parents[2]
    if str(gyoker / "tools" / "golden") not in sys.path:
        sys.path.insert(0, str(gyoker / "tools" / "golden"))
    from compare_render import _read_rgb, delta_e_cie76

    esetek = [
        ("alap", "TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;", 0.546),
        ("max", "TwoTone=1,95.000000,100.000000,100.000000,00004488,00ffff00;", 0.121),
        ("min", "TwoTone=1,-95.000000,0.000000,0.000000,00004488,00ffff00;", 0.670),
    ]
    for variacio, lanc, vart_de in esetek:
        nev = f"twotone__{variacio}.jpg"
        forras = _read_rgb(_KIT / nev)
        export = _read_rgb(_KIT / "export" / nev)
        report = apply_filters(forras, parse_filters(lanc))
        de = float(delta_e_cie76(report.image, export).mean())
        assert de <= vart_de + _TURES, f"TwoTone {variacio}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"
