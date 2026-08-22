"""#381: a Glimmer-effektek EGZAKT csővezetékei a teljes láncon (`chain.py`)
keresztül — round-trip a `docs/specs/filters-decoded.md`/`filterdesc-
registry.md`-ben rögzített, VALÓDI Picasa-exportokból mért `.picasa.ini`
`filters=` mintákkal: a lánc nem hagyja ki őket (`skipped == ()`), és a
kimenet érvényes kép.

`research/testdata/golden-kit3` a konténerben NEM érhető el (gitignore-olt,
csak a fejlesztő gépén él) — a `tools/golden/compare_render.py`-os pixel-
szintű összevetés ezért itt KIHAGYOTT (ld. a feladat zárójelentése).
"""

from __future__ import annotations

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import KNOWN_UNRENDERED_OPS, _HANDLERS, apply_filters
from picasapy.render.chain_glimmer_handlers import PAINTABLE_MASK_OPS

#: A `filters-decoded.md` 5. körében MÉRT, valódi Picasa-exportból származó
#: minták (5. fül) + a #381 issue-ban idézett, filterdesc.xml-lel egyeztetett
#: minták (4. fül) — mindegyiknek MOST már le kell futnia (nem KÖZELÍTŐ
#: modell, hanem a filterdesc.xml egzakt csővezetéke).
_REAL_SAMPLES = {
    "Vignette": "Vignette=1,35.000000,1.400000,0.000000,00000000;",
    "Matte": "Matte=1,40.000000,1.200000,0.000000,00ffffff;",
    "HDR": "HDR=1,20.000000,3.000000,0.000000;",
    "LocalContrast": "LocalContrast=1,15.000000,1.500000;",
    "Invert": "Invert=1;",
    "IR": "IR=1,0.000000;",
    "Lomo": "Lomo=1,50.000000,0.000000;",
    "Holga": "Holga=1,70.000000,30.000000,0.000000;",
    "Cinemascope": "Cinemascope=1,0;",
    "Orton": "Orton=1,25.000000,50.000000,0.000000;",
    "Sixties": "Sixties=1,20.000000,00ffffff,0;",
    "HeatMap": "HeatMap=1,0.000000,0.000000;",
    "NightVision": "NightVision=1,0.000000,0.000000,0.000000;",
    "CrossProcess": "CrossProcess=1,0.000000;",
    "QuantizePalette": "QuantizePalette=1,8.000000,80.000000,0.000000;",
    "TwoTone": "TwoTone=1,0.000000,20.000000,0.000000,00004488,00ffff00;",
    "Boost": "Boost=1,50.000000;",
    "Soften": "Soften=1,50.000000,50.000000;",
    "Pixelate": "Pixelate=1,20.000000,9.000000,0.000000;",
    "PicnikGrain": "PicnikGrain=1,10.000000,0;",
    "PencilSketch": "PencilSketch=1,2.000000,100.000000,0.000000;",
    "Neon": "Neon=1,0.000000,00ff0000;",
    "Border": "Border=1,20.000000,5.000000,0.000000,00000000,00ffffff,0.000000;",
    "RoundedEdges": "RoundedEdges=1,5.000000,00ffffff;",
    "DropShadow": "DropShadow=1,4.000000,90.000000,10.000000,00000000,00ffffff,30.000000;",
    "MuseumMatte": "MuseumMatte=1,25.000000,40.000000,001a0e03,00f0eae4;",
    "Polaroid": "Polaroid=1,5.000000,00e2e2e2;",
    "PicnikTint": "PicnikTint=1,0.000000,0080cfff;",
    "ReanimatedEyeColor": "ReanimatedEyeColor=1,6.000000,20.000000;",
}


@pytest.fixture
def sample() -> np.ndarray:
    rng = np.random.default_rng(13)
    image = rng.integers(30, 220, size=(64, 96, 3), dtype=np.uint8)
    image[:20, :, 0] = 210
    return image


class TestRealIniSamplesRoundTrip:
    @pytest.mark.parametrize("name,chain_text", list(_REAL_SAMPLES.items()))
    def test_a_lanc_nem_hagyja_ki(self, name, chain_text, sample):
        result, skipped = apply_filters(sample, parse_filters(chain_text))
        assert skipped == (), f"{name}: a lánc kihagyta ({skipped})"
        assert result.dtype == np.uint8 and result.shape[2] == 3

    @pytest.mark.parametrize("name,chain_text", list(_REAL_SAMPLES.items()))
    def test_a_kulcs_bekotott(self, name, chain_text):
        del chain_text
        key = name.casefold()
        assert key in _HANDLERS, f"{name}: nincs bekötve a láncba"
        assert key not in KNOWN_UNRENDERED_OPS, f"{name}: még mindig a kihagyott regiszterben"


class TestParamSweepIsPropagated:
    """A csúszkatartomány a regiszterből jön (#382) — az ini-értékek
    TÉNYLEG eljutnak a csővezetékhez, nem csak a nevet ismeri fel a lánc."""

    def test_vignette_szin_hat(self, sample):
        black, _ = apply_filters(sample, parse_filters("Vignette=1,35.0,1.4,0.0,00000000;"))
        white, _ = apply_filters(sample, parse_filters("Vignette=1,35.0,1.4,0.0,00ffffff;"))
        assert not np.array_equal(black, white)

    def test_boost_impact_hat(self, sample):
        low, _ = apply_filters(sample, parse_filters("Boost=1,5.0;"))
        high, _ = apply_filters(sample, parse_filters("Boost=1,95.0;"))
        assert not np.array_equal(low, high)

    def test_border_vastagsag_hat_a_meretre(self, sample):
        thin, _ = apply_filters(sample, parse_filters("Border=1,2.0,0.0,0.0,00000000,00ffffff,0.0;"))
        thick, _ = apply_filters(sample, parse_filters("Border=1,40.0,0.0,0.0,00000000,00ffffff,0.0;"))
        assert thick.shape[0] > thin.shape[0]


class TestPaintableMaskWarning:
    """#381 elfogadási feltétel: a festhető-maszkos effektek (PicnikTint,
    ReanimatedEyeColor) a TELJES KÉPRE futnak (nincs ecset-eszköz), és ezt a
    `ChainReport.range_warnings` jelzi."""

    @pytest.mark.parametrize("key", sorted(PAINTABLE_MASK_OPS))
    def test_figyelmeztetes_a_range_warnings_ban(self, key, sample):
        # #1141: a `PAINTABLE_MASK_OPS` kulcsai kisbetűsek (belső
        # regiszter), a LÁNC viszont a kanonikus alakot fogadja el — a
        # láncot ezért a kanonikus névvel építjük fel
        from picasapy.ini.filter_registry import canonicalize_filter_name

        kanonikus = canonicalize_filter_name(key)
        report = apply_filters(sample, parse_filters(f"{kanonikus}=1;"))
        assert any(
            key in warning.casefold() for warning in report.range_warnings
        ), report.range_warnings

    def test_nincs_figyelmeztetes_mas_effektnel(self, sample):
        report = apply_filters(sample, parse_filters("Invert=1;"))
        assert report.range_warnings == ()


class TestNewNamesRemovedFromUnrendered:
    """A `matte`/`nightvision`/`roundededges` #381 előtt a
    `KNOWN_UNRENDERED_OPS` tagjai voltak (#382/#347) — most egzakt
    csővezetékük van, ezért a listából kikerültek."""

    @pytest.mark.parametrize("key", ["Matte", "NightVision", "RoundedEdges"])
    def test_mar_nem_ismeretlen(self, key):
        assert key not in KNOWN_UNRENDERED_OPS
