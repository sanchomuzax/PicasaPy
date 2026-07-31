"""#316: az effekt-paraméterek katalógusa a csúszkás alpanelhez.

Az eredeti Picasában a paraméteres effekt gombja nem azonnal alkalmaz, hanem
csúszkás alpanelt nyit (élő előnézet + Alkalmaz/Mégse). Ez a modul mondja
meg, MELYIK effektnek MILYEN csúszkái vannak — a tartományok és az
alapértékek a `docs/specs/filters-decoded.md` MÉRT ini-mintáiból és az
implementált render-szignatúrákból jönnek.
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import (
    PARAMETERLESS_EFFECTS,
    EffectParam,
    effect_params,
    format_param_values,
    has_params,
)
from picasapy.app.edit_controller import _EFFECT_NAMES
from picasapy.render.chain import _HANDLERS


class TestCatalogueShape:
    def test_every_described_effect_is_a_known_effect(self):
        for name in list(PARAMETERLESS_EFFECTS) + [
            n for n in _EFFECT_NAMES if effect_params(n)
        ]:
            assert name in _EFFECT_NAMES, f"ismeretlen effekt a katalógusban: {name}"
            assert name in _HANDLERS, f"nincs render-handler: {name}"

    def test_parameterless_effects_have_no_sliders(self):
        for name in PARAMETERLESS_EFFECTS:
            assert effect_params(name) == ()
            assert has_params(name) is False

    @pytest.mark.parametrize(
        "name", ["unsharp", "sat", "vignette", "glow2", "radblur", "boost", "polaroid"]
    )
    def test_known_parameterised_effects_have_sliders(self, name):
        params = effect_params(name)
        assert params, f"{name}: várt csúszkák, kaptunk semmit"
        assert has_params(name) is True
        for param in params:
            assert isinstance(param, EffectParam)
            assert param.minimum < param.maximum
            assert param.minimum <= param.default <= param.maximum
            assert param.step > 0
            assert param.label, "minden csúszkának van felirata"

    def test_unknown_effect_has_no_params(self):
        assert effect_params("nincs-ilyen") == ()
        assert has_params("nincs-ilyen") is False


class TestMeasuredDefaults:
    """Az alapértékek a mért ini-mintákat kövessék (filters-decoded.md)."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("boost", (50.0,)),                 # Boost=1,50.000000
            ("soften", (50.0, 50.0)),           # Soften=1,50.000000,50.000000
            ("pencilsketch", (2.0, 100.0, 0.0)),  # PencilSketch=1,2,100,0
            ("comicize", (20.0, 50.0, 50.0)),   # Comicize=1,20,50,50
            ("vignette", (35.0, 1.4)),          # Vignette=1,35.0,1.4
            ("unsharp", (0.6,)),                # unsharp=1 == unsharp2=1,0.6
        ],
    )
    def test_defaults_match_the_measured_samples(self, name, expected):
        actual = tuple(p.default for p in effect_params(name))
        assert actual == pytest.approx(expected)


class TestFormatting:
    """A láncba a Picasa `%.6f` alakja kerül (round-trip elv)."""

    def test_values_are_formatted_with_six_decimals(self):
        assert format_param_values([50.0, 1.25]) == ("50.000000", "1.250000")

    def test_empty_values(self):
        assert format_param_values([]) == ()

    def test_non_numeric_is_rejected(self):
        with pytest.raises((TypeError, ValueError)):
            format_param_values(["nem szám"])
