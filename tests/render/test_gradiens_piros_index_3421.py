"""#3421: a gradiens-LUT-ok indexe a PIROS csatorna, nem a luma.

A `GradientMap` építője (`0x00bb87b0`, a TwoTone-é is) és a `HSVGradientMap`
építője (`0x00bbc260`) a 256 elemű színtáblát a közös futószalag
(`0x00bcb2f0`) `+0x800` rekeszébe írja — ez a BGRA-képpont `src[2]` bájtja,
a piros —, a `+0x400` és `+0x000` rekeszt nullázza (`0x00bbc56a`–`0x00bbc588`).
A kimenet tehát CSAK a bemenet piros csatornájától függ.

A HeatMap leírója (`filterdesc.xml`) előtte `SimpleColorMatrix
Saturation="0"`-t ír, ami a mért viselkedés szerint NEM szürkít (a TwoTone
ugyanígy, #3433).
"""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters

from picasapy.render import glimmer_ops as g
from picasapy.render import glimmer_tone as t
from picasapy.render.chain import apply_filters


def _kep(*keppontok) -> np.ndarray:
    return np.array([list(keppontok)], dtype=np.uint8)


def test_a_gradient_map_csak_a_piros_csatornat_nezi():
    szinek = ((0, 0, 0), (255, 255, 255))
    ki = g.gradient_map(_kep((255, 0, 0), (0, 255, 255), (128, 7, 200)), szinek)
    assert tuple(int(v) for v in ki[0, 0]) == (255, 255, 255)
    assert tuple(int(v) for v in ki[0, 1]) == (0, 0, 0)
    assert tuple(int(v) for v in ki[0, 2]) == (128, 128, 128)


def test_a_hsv_gradient_map_csak_a_piros_csatornat_nezi():
    megallok = ((0.0, 240.0, 100.0, 100.0), (255.0, 0.0, 100.0, 100.0))
    ki = g.hsv_gradient_map(_kep((255, 0, 0), (0, 0, 255), (255, 255, 255)), megallok)
    # piros=255 → a felső megálló (tiszta vörös); kék (piros=0) → az alsó (kék)
    assert tuple(int(v) for v in ki[0, 0]) == (255, 0, 0)
    assert tuple(int(v) for v in ki[0, 1]) == (0, 0, 255)
    # a fehér piros csatornája is 255 → ugyanaz, mint a tiszta vörösé
    assert tuple(int(v) for v in ki[0, 2]) == tuple(int(v) for v in ki[0, 0])


def test_a_heatmap_nem_szurkit_a_gradiens_elott():
    """Egy tiszta vörös és egy tiszta kék képpont a luma szerint közel esne
    (76 vs 29), a piros csatorna szerint a skála két végére kerül."""
    ki = t.apply_heatmap(_kep((255, 0, 0), (0, 0, 255)))
    varhato_teteje = g.hsv_gradient_map(_kep((255, 0, 0)), t._HEATMAP_STOPS)[0, 0]
    varhato_alja = g.hsv_gradient_map(_kep((0, 0, 0)), t._HEATMAP_STOPS)[0, 0]
    np.testing.assert_array_equal(ki[0, 0], varhato_teteje)
    np.testing.assert_array_equal(ki[0, 1], varhato_alja)


# --- #3814: a HSV → RGB átalakítás lebegőpontos, float32, CSONKOLVA ---------
#
# Az eredeti (`0x00bbbe20`) nem az OpenCV 8 bites HSV-jén át alakít, hanem
# float32 köztes értékekkel, és a végén csonkol (`csonk(x · 255)`, nincs
# +0,5). Spec: `docs/specs/filterdesc-registry.md`,
# `HSVGradientMapImageOperation`, „A HSV → RGB átalakítás".
#
# rontás-kontroll (1): a `hsv_gradient_map` visszaállítva a régi, OpenCV 8
# bites HSV-s LUT-ra (`h/2`, `·2,55`, `rint`, `cv2.COLOR_HSV2RGB`) → 7 failed:
# a `test_a_heatmap_lut_kozepe_...` mind a 4 esete, az OpenCV-mentes teszt és
# a golden alap/min. A jegy három pontja (200°, 360°, −180) ÖNMAGÁBAN nem
# buktat: az OpenCV ezeken véletlenül ugyanazt adja — ezért a LUT-közép.
# rontás-kontroll (2): csonkolás helyett `np.rint` → 7 failed: a 200°-os, a
# −180-as, a V=50%-os, a 128-as LUT-közép, az OpenCV-mentes és a golden
# alap/min.


def _egyszinu(hue: float, sat: float, val: float, hue_offset: float = 0.0):
    """Két azonos megállóval a LUT minden bejegyzése ugyanaz a HSV-szín."""
    megallok = ((0.0, hue, sat, val), (255.0, hue, sat, val))
    ki = g.hsv_gradient_map(_kep((0, 0, 0), (255, 0, 0)), megallok, hue_offset=hue_offset)
    return tuple(int(v) for v in ki[0, 0])


def test_200_fok_csonkolva_169_nem_170():
    # 0,6666665 · 255 = 169,99996 → csonkolva 169 (kerekítve 170 volna)
    assert _egyszinu(200.0, 100.0, 100.0) == (0, 169, 255)


def test_360_fok_korbefordul_nullara():
    assert _egyszinu(360.0, 100.0, 100.0) == (255, 0, 0)


def test_a_hue_offset_minusz_180_nal_is_korbefordul():
    # 20° − 180° = −160° → +360 → 200°
    assert _egyszinu(20.0, 100.0, 100.0, hue_offset=-180.0) == (0, 169, 255)


def test_a_fel_ertek_csonkolodik():
    # V = 0,5 → 0,5 · 255 = 127,5 → 127 (a HeatMap alsó megállója, 240° 100% 50%)
    assert _egyszinu(240.0, 100.0, 50.0) == (0, 0, 127)



@pytest.mark.parametrize(
    ("piros", "hue_offset", "vart"),
    [
        # 240° − 40,31° = 199,69° → 3. szektor, f = 0,3281 → G = csonk(171,3)
        (64, 0.0, (0, 171, 255)),
        # 119,37° → 1. szektor, f = 0,9895 → R = csonk(2,68); az OpenCV 0-t adott
        (128, 0.0, (2, 255, 0)),
        # 29,02° → 0. szektor, f = 0,4837 → G = csonk(123,3); az OpenCV 127-et adott
        (200, 0.0, (255, 123, 0)),
        # 119,37° − 180° → 299,37° → 4. szektor, f = 0,9895 → R = csonk(252,3)
        (128, -180.0, (252, 0, 255)),
    ],
)
def test_a_heatmap_lut_kozepe_a_nativ_keplettel(piros, hue_offset, vart):
    """CI-biztos fog: ezeken a bejegyzéseken az OpenCV 8 bites HSV-je
    láthatóan eltér (a jegy pontjai önmagukban nem választják szét a kettőt)."""
    ki = g.hsv_gradient_map(_kep((piros, 0, 0)), t._HEATMAP_STOPS, hue_offset=hue_offset)
    assert tuple(int(v) for v in ki[0, 0]) == vart

def test_a_lut_opencv_nelkul_epul(monkeypatch):
    def _tilos(*_args, **_kwargs):
        raise AssertionError("a HSV → RGB LUT nem mehet az OpenCV-n át (#3814)")

    monkeypatch.setattr(g.cv2, "cvtColor", _tilos)
    assert _egyszinu(200.0, 100.0, 100.0) == (0, 169, 255)


_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: (változat, lánc, küszöb) — a küszöb a mért érték + 0,05, de legfeljebb
#: 0,6 (#3814). Mérve a javítás után: alap 0,548, min 0,558 (előtte 1,014 /
#: 1,130), max 0,121 (változatlan).
_HEATMAP_GOLDEN = [
    ("alap", "HeatMap=1,0.000000,0.000000;", 0.6),
    ("min", "HeatMap=1,-180.000000,0.000000;", 0.6),
    ("max", "HeatMap=1,180.000000,100.000000;", 0.121 + 0.05),
]


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(("valtozat", "lanc", "kuszob"), _HEATMAP_GOLDEN, ids=[e[0] for e in _HEATMAP_GOLDEN])
def test_heatmap_a_684_merokeszlettel(valtozat, lanc, kuszob):
    gyoker = Path(__file__).resolve().parents[2]
    if str(gyoker / "tools" / "golden") not in sys.path:
        sys.path.insert(0, str(gyoker / "tools" / "golden"))
    from compare_render import _read_rgb, delta_e_cie76

    nev = f"heatmap__{valtozat}.jpg"
    report = apply_filters(_read_rgb(_KIT / nev), parse_filters(lanc))
    de = float(delta_e_cie76(report.image, _read_rgb(_KIT / "export" / nev)).mean())
    assert de <= kuszob, f"HeatMap {valtozat}: ΔE {de:.3f} > {kuszob:.3f}"


def test_az_extrem_hue_egy_lepesben_fordul_korbe() -> None:
    """Kézzel szerkesztett ini-ből jöhet nagyon nagy `Hue`: a körbefordítás
    egyetlen vektoros lépés, nem ciklus (a #3835 átnézése: 1e7-nél 0,4 mp).
    A 14 400 200 még pontosan ábrázolható float32-ben (2^24 alatt)."""
    import time

    kezd = time.perf_counter()
    nagy = g._hsv_rgb_lut_f32(
        np.array([200.0 + 360.0 * 40000]), np.array([100.0]), np.array([100.0])
    )
    assert time.perf_counter() - kezd < 0.05
    kicsi = g._hsv_rgb_lut_f32(np.array([200.0]), np.array([100.0]), np.array([100.0]))
    np.testing.assert_array_equal(nagy, kicsi)
