"""#3757 + #3444: a Filmszemcse (`PicnikGrain`) a leíró szerint számol.

A `filterdesc.xml` `PicnikGrain` blokkja (`filterdesc-registry.md`, 4. pont):

    NestedImageOperation BlendAlpha="1" BlendMode="{_radioLighten.selected?7:5}"
      NoiseImageOperation randomSeed="1" low=… high=… channelOptions="7" grayScale="true"

* **A mag rögzített: `randomSeed = 1`**, a zajt a `NoiseImageOperation`
  natív generátora adja (MT19937 a Picasa 1664525-ös magvetésével, #3736).
  A #907 „két alkalmazás független mintát ad" mérése a natív, kisbetűs
  `grain` szűrőre vonatkozott (`grain=1;`, `grain=1;grain=1;`), nem erre.
* **A keverési mód a natív módtábla sorszáma** (`0x00cf0e98`): 7 = Screen
  (világosító ág), 5 = Multiply (sötétítő ág) — nem Lighten/Darken.

Mérve (CIE76 átlag-ΔE a Picasa-exporthoz, `analyze_validation_kit.mean_de`):

| eset | előtte (véletlen mag, Darken) | utána (MT `randomSeed = 1`, Multiply) |
|---|---:|---:|
| 684 `picnikgrain__alap` (Grain 10) | 3,009 | **0,882** |
| 684 `picnikgrain__max` (Grain 50) | 12,21 | **1,380** |
| 684 `picnikgrain__min` (Grain 0) | 0,121 | 0,121 |
| merokit-2 `szemcse_04` (Grain 30) | 7,79 | **0,981** |

A világosító ág (Screen) Picasa-exportja egyik készletben sincs; a 7 = Screen
a binárisból jön, itt a bekötését a független referenciához mérjük.
"""

# rontás-kontroll: a `glimmer_artistic._PICNIK_GRAIN_SEED` 2-re átírva → 9
# failed (mind a hat referencia-próba és a golden `alap`/`max`/`szemcse_04`);
# a sötétítő ág módja `"darken"`-re visszaírva → 8 failed (a három Multiply-
# referencia, a három golden eset és mindkét statisztikai próba); a
# világosító ág `"lighten"`-re visszaírva → 3 failed (a Screen-referencia).

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render import glimmer_artistic as a
from picasapy.render.chain import apply_filters
from picasapy.render.nativ_noise import picasa_mt19937


@pytest.fixture
def kep():
    rng = np.random.default_rng(3757)
    return rng.integers(0, 256, size=(23, 31, 3), dtype=np.uint8)


def _referencia(kep: np.ndarray, grain: float, lighten: bool) -> np.ndarray:
    """Független referencia a leíróból: szürke MT-zaj `randomSeed = 1`-gyel,
    a Screen/Multiply a natív egész kernellel (#3442): Multiply
    `⌊b·t/255⌋`, Screen `⌊(65025 − (255−b)(255−t))/255⌋`."""
    h, w = kep.shape[:2]
    if lighten:
        also, felso = 0, min(int(2.55 * grain), 255)
    else:
        also, felso = min(int(255 - 2.55 * grain), 255), 255
    huzasok = picasa_mt19937(1, h * w).reshape(h, w).astype(np.int64)
    zaj = (huzasok % (felso - also + 1) + also)[..., np.newaxis]
    b = kep.astype(np.int64)
    if lighten:
        kimenet = (65025 - (255 - b) * (255 - zaj)) // 255
    else:
        kimenet = b * zaj // 255
    return kimenet.astype(np.uint8)


class TestALeiroSzerint:
    @pytest.mark.parametrize("grain", [10.0, 50.0, 33.0])
    def test_sotetito_ag_multiply_randomseed_1(self, kep, grain):
        np.testing.assert_array_equal(
            a.apply_picnik_grain(kep, grain=grain, lighten=False), _referencia(kep, grain, False)
        )

    @pytest.mark.parametrize("grain", [10.0, 50.0, 33.0])
    def test_vilagosito_ag_screen_randomseed_1(self, kep, grain):
        np.testing.assert_array_equal(
            a.apply_picnik_grain(kep, grain=grain, lighten=True), _referencia(kep, grain, True)
        )

    def test_ket_hivas_bajtazonos(self, kep):
        """A mag rögzített — két hívás ugyanazt adja (nincs véletlen mag)."""
        elso = a.apply_picnik_grain(kep, grain=20.0, lighten=True)
        masodik = a.apply_picnik_grain(kep, grain=20.0, lighten=True)
        np.testing.assert_array_equal(elso, masodik)

    def test_a_nulla_szemcse_no_op(self, kep):
        """`Grain 0`, sötétítő ág: a zaj a `[255, 255]` tartomány, és a
        Multiply 255-tel azonosság."""
        np.testing.assert_array_equal(a.apply_picnik_grain(kep, grain=0.0, lighten=False), kep)

    def test_a_bemenet_nem_mutalodik(self, kep):
        masolat = kep.copy()
        a.apply_picnik_grain(kep, grain=50.0, lighten=False)
        np.testing.assert_array_equal(kep, masolat)


# ---------------------------------------------------------------------------
# FEJLESZTŐI GÉPEN futó golden-mérés a valódi Picasa-exporttal; ha a készlet
# nincs a gépen, skip.
# ---------------------------------------------------------------------------

_KIT = Path("/mnt/nas/My Pictures/684-merokeszlet")
_MEROKIT2 = Path("/mnt/nas/My Pictures/PicasaPy merokit-2")

#: A jegy táblázatának + 0,05-ös tűrése.
_TURES = 0.05

#: (címke, forrás, Picasa-export, lánc, mért ΔE)
_GOLDEN_ESETEK = [
    (
        "684 alap",
        _KIT / "picnikgrain__alap.jpg",
        _KIT / "export" / "picnikgrain__alap.jpg",
        "PicnikGrain=1,10.000000,0;",
        0.882,
    ),
    (
        "684 max",
        _KIT / "picnikgrain__max.jpg",
        _KIT / "export" / "picnikgrain__max.jpg",
        "PicnikGrain=1,50.000000,0;",
        1.380,
    ),
    (
        "684 min",
        _KIT / "picnikgrain__min.jpg",
        _KIT / "export" / "picnikgrain__min.jpg",
        "PicnikGrain=1,0.000000,0;",
        0.121,
    ),
    (
        "merokit-2 szemcse_04",
        _MEROKIT2 / "szemcse_04.jpg",
        _MEROKIT2 / "export-202608151438" / "szemcse_04.jpg",
        "PicnikGrain=1,30.000000,0;",
        0.981,
    ),
]


def _golden_eszkozok():
    gyoker = Path(__file__).resolve().parents[2]
    utvonal = str(gyoker / "tools" / "golden")
    if utvonal not in sys.path:
        sys.path.insert(0, utvonal)
    from analyze_validation_kit import load, mean_de

    return load, mean_de


@pytest.mark.parametrize(
    ("cimke", "forras_ut", "export_ut", "lanc", "vart_de"),
    _GOLDEN_ESETEK,
    ids=[e[0] for e in _GOLDEN_ESETEK],
)
def test_golden_a_hatarertek_alatt(cimke, forras_ut, export_ut, lanc, vart_de):
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    load, mean_de = _golden_eszkozok()
    kep = apply_filters(load(forras_ut), parse_filters(lanc)).image
    de = mean_de(kep, load(export_ut))
    assert de <= vart_de + _TURES, f"{cimke}: ΔE {de:.3f} > {vart_de + _TURES:.3f}"


#: #3444 statisztikai próbája: a (kimenet − bemenet) különbség csatornánkénti
#: átlaga és szórása legfeljebb ennyivel térhet el a Picasáétól. Mérve a
#: javítás ELŐTT (#879): az átlag eltérése max-nál ~20,5, alapnál ~7,0; a
#: szórásé ~4,2, ill. ~5,0. Utána: átlag ≤ 0,03, szórás ≤ 0,30.
_STAT_TURES = 0.5


@pytest.mark.parametrize(
    ("nev", "grain"), [("picnikgrain__max.jpg", 50.0), ("picnikgrain__alap.jpg", 10.0)]
)
def test_statisztika_a_kulonbseg_atlaga_es_szorasa(nev, grain):
    export_ut = _KIT / "export" / nev
    if not export_ut.is_file():
        pytest.skip(f"a mérőkészlet nem elérhető: {export_ut}")
    load, _ = _golden_eszkozok()
    forras = load(_KIT / nev).astype(np.float64)
    picasa = load(export_ut).astype(np.float64) - forras
    mienk = a.apply_picnik_grain(load(_KIT / nev), grain=grain).astype(np.float64) - forras
    atlag_elteres = np.abs(mienk.mean(axis=(0, 1)) - picasa.mean(axis=(0, 1)))
    szoras_elteres = np.abs(mienk.std(axis=(0, 1)) - picasa.std(axis=(0, 1)))
    assert atlag_elteres.max() <= _STAT_TURES, f"átlag-eltérés: {atlag_elteres}"
    assert szoras_elteres.max() <= _STAT_TURES, f"szórás-eltérés: {szoras_elteres}"


def test_tartomanyon_kivuli_grain_a_szelso_ertekre_vagodik() -> None:
    """Kézzel szerkesztett ini-ből jöhet 100 fölötti érték: ne dobjon, hanem
    a 100-as állást adja (különben a lánc némán kihagyná a szűrőt)."""
    kep = np.full((8, 8, 3), 200, dtype=np.uint8)
    np.testing.assert_array_equal(
        a.apply_picnik_grain(kep, grain=120.0), a.apply_picnik_grain(kep, grain=100.0)
    )
