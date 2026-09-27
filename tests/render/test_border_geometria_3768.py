"""#3768: a `Border` feliratsávja és lekerekített sarka az eredeti szerint.

`docs/specs/filterdesc-registry.md`, „A `Border` sarka és feliratsávja —
MÉRVE”:

1. A dinamikus csúszka a tartomány két végét **float32-ben** tárolja
   (`0x00bbd40d`, `0x00bbd422`), és abból vetít:
   `érték = min + (f32(max) − f32(min)) · t/100`. A `captionheight`-et a
   `0x008eea90` **csonkítva** alakítja egésszé: 640-es képen
   `trunc(f32(640/6) · 0,6) = trunc(63,9999985) = 63`, nem 64.
2. A sarok koncentrikus: a kép sarka `R` sugarú (a kimaradó rész belső
   színű), a belső sáv külső éle `R + belső` sugarú (azon kívül külső
   szín), a vászon sarka szögletes. `R = 0` mellett a belső sáv is
   szögletes (a `border__alap` exportján mérve: a sáv sarokképpontja fehér).

Mérve (684-merokeszlet, CIE76 átlag-ΔE a Picasa-exporthoz):

| eset | előtte | utána |
|---|---:|---:|
| `border__max` | 3,584 (és 1104 sor 1103 helyett) | **0,097** |
| `border__alap` | 0,096 | 0,096 |
| `roundededges__alap` / `max` | 0,173 / 0,219 | **0,143 / 0,163** (élsimított ív) |
| `museummatte__alap` / `max` | 0,773 / 0,645 | változatlan |
| `sixties__alap` / `min` | 1,179 / 1,255 | változatlan |
"""

# rontás-kontroll: (1) a `draw_border` visszaállítva a régi rajzolásra (két
# szögletes gyűrű a kép köré, a teljes vászon sarka lekerekítve, a felirat
# kerekítve) → 9 failed: a `TestKoncentrikusSarok` három sarok-esete, a
# `TestFeliratsav` három méret-esete, a `border__max` és a két
# `roundededges` golden; (2) a `dinamikus_csuszka_ertek` f32-vetítése
# double-re visszaírva → 3 failed (a vetítés, az 1103 sor, a `border__max`
# golden); (3) a feliratsáv csonkítása kerekítésre cserélve → 3 failed
# (1104 ≠ 1103, 107 ≠ 106, a `border__max` golden). Ellenőrizve lefuttatva.

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters
from picasapy.render.chain_geometry import keret_geometria
from picasapy.render.dinamikus_csuszka import dinamikus_csuszka_ertek, felirat_maximum
from picasapy.render.glimmer_frame_ops import draw_border

_W, _H = 960, 640
_MAX_LANC = "Border=1,100,100,40,00000000,00ffffff,60;"

_KEP = (200, 30, 30)
_KULSO = (0, 0, 0)
_BELSO = (255, 255, 255)


@pytest.fixture
def kep() -> np.ndarray:
    out = np.empty((_H, _W, 3), dtype=np.uint8)
    out[:] = _KEP
    return out


class TestFeliratsav:
    def test_a_vetites_float32_vegpontokbol(self):
        vart = float(np.float32(_H / 6.0)) * 60.0 / 100.0
        assert dinamikus_csuszka_ertek(60.0, 0.0, felirat_maximum(_H)) == vart
        assert vart < 64.0

    def test_a_max_allas_kimenete_1103_sor(self, kep):
        kimenet, kihagyott = apply_filters(kep, parse_filters(_MAX_LANC))
        assert kihagyott == ()
        assert kimenet.shape == (_H + 400 + 63, _W + 400, 3)

    def test_a_teljes_feliratsav_csonkitva(self, kep):
        # 100 %: f32(640/6) = 106,666664 → 106 sor
        kimenet, _ = apply_filters(kep, parse_filters("Border=1,0,0,0,00000000,00ffffff,100;"))
        assert kimenet.shape[0] == _H + 106

    def test_a_geometria_a_renderrel_egyezik(self, kep):
        kimenet, _ = apply_filters(kep, parse_filters(_MAX_LANC))
        geo = keret_geometria(parse_filters(_MAX_LANC), _W, _H)
        assert (geo.magassag, geo.szelesseg) == kimenet.shape[:2]


class TestKoncentrikusSarok:
    """R = 128, belső = külső = 100: a közös középpont (328, 328)."""

    @pytest.fixture
    def kimenet(self, kep) -> np.ndarray:
        return draw_border(kep, _KULSO, _BELSO, 100, 100, 128, 63)

    def test_a_vaszon_es_a_sav_sarka_kulso_szinu(self, kimenet):
        # a sáv téglalapján belül, de az `R + belső = 228` ívén kívül
        assert tuple(kimenet[110, 110]) == _KULSO
        assert tuple(kimenet[0, 0]) == _KULSO
        assert tuple(kimenet[-1, 0]) == _KULSO

    def test_a_kep_sarka_belso_szinu(self, kimenet):
        # a kép téglalapján belül, de az `R = 128` ívén kívül
        assert tuple(kimenet[205, 205]) == _BELSO
        assert tuple(kimenet[200 + _H - 5, 200 + _W - 5]) == _BELSO

    def test_az_egyenes_szakaszok_es_a_kep(self, kimenet):
        assert tuple(kimenet[150, 680]) == _BELSO
        assert tuple(kimenet[50, 680]) == _KULSO
        assert tuple(kimenet[520, 680]) == _KEP
        # a belső sáv a feliratsáv fölött véget ér; a felirat külső színű
        assert tuple(kimenet[939, 680]) == _BELSO
        assert tuple(kimenet[940, 680]) == _KULSO
        assert tuple(kimenet[-30, 680]) == _KULSO

    def test_az_iv_elsimitott(self, kimenet):
        # a 235. sorban az ív (x ≈ 119) mentén átmeneti értéknek kell lennie
        sor = kimenet[235, 100:140, 0].astype(int)
        assert np.any((sor > 10) & (sor < 245))

    def test_nulla_sugarnal_a_sav_szogletes(self, kep):
        kimenet = draw_border(kep, _KULSO, _BELSO, 20, 5, 0, 0)
        assert tuple(kimenet[20, 20]) == _BELSO
        assert tuple(kimenet[25, 25]) == _KEP
        assert tuple(kimenet[19, 19]) == _KULSO

    def test_a_bemenet_nem_valtozik(self, kep):
        masolat = kep.copy()
        draw_border(kep, _KULSO, _BELSO, 100, 100, 128, 63)
        assert np.array_equal(kep, masolat)


def test_rounded_edges_merete_valtozatlan_es_a_sarok_kulso(kep):
    kimenet, _ = apply_filters(kep, parse_filters("RoundedEdges=1,30,00ffffff;"))
    assert kimenet.shape == kep.shape
    assert tuple(kimenet[0, 0]) == (255, 255, 255)
    assert tuple(kimenet[_H // 2, _W // 2]) == _KEP


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal. Ha a kit nincs
# a gépen, a teszt skip-pel lép ki (CI-n és felhős körben sosem érhető el).
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")

#: (név, lánc, a #3768 után mért ΔE) — a határ a mért érték + 0,01; a
#: `border__max`-é a jegy „Kész, ha” pontja szerint 0,15.
_GOLDEN = [
    ("border__max", _MAX_LANC, 0.14),
    ("border__alap", "Border=1,20,5,0,00000000,00ffffff,0;", 0.096),
    ("roundededges__alap", "RoundedEdges=1,30,00ffffff;", 0.143),
    ("roundededges__max", "RoundedEdges=1,60,00ffffff;", 0.163),
    ("museummatte__alap", "MuseumMatte=1,25,40,001a0e03,00f0eae4;", 0.773),
    ("museummatte__max", "MuseumMatte=1,100,100,001a0e03,00f0eae4;", 0.645),
    ("sixties__alap", "Sixties=1,20,00ffffff,0;", 1.179),
    ("sixties__min", "Sixties=1,0,00ffffff,0;", 1.255),
]


@pytest.mark.skipif(not _KIT.is_dir(), reason="a 684-merokeszlet NAS-os mérőkészlet nem elérhető")
@pytest.mark.parametrize(("nev", "lanc", "vart_de"), _GOLDEN, ids=[e[0] for e in _GOLDEN])
def test_a_684_merokeszlettel_nem_romlik(nev, lanc, vart_de):
    gyoker = Path(__file__).resolve().parents[2]
    if str(gyoker / "tools" / "golden") not in sys.path:
        sys.path.insert(0, str(gyoker / "tools" / "golden"))
    from compare_render import _read_rgb, delta_e_cie76

    forras = _read_rgb(_KIT / f"{nev}.jpg")
    export = _read_rgb(_KIT / "export" / f"{nev}.jpg")
    kimenet = apply_filters(forras, parse_filters(lanc)).image
    assert kimenet.shape == export.shape
    de = float(delta_e_cie76(kimenet, export).mean())
    assert de <= vart_de + 0.01, f"{nev}: ΔE {de:.3f} > {vart_de + 0.01:.3f}"
