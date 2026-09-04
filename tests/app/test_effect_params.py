"""#316/#516: az effekt-paraméterek katalógusa a vezérlős alpanelhez.

Az eredeti Picasában a paraméteres effekt gombja nem azonnal alkalmaz, hanem
egy alpanel nyílik (csúszkák/jelölőnégyzetek/színválasztók, élő előnézettel
+ Alkalmaz/Mégse). Ez a modul mondja meg, MELYIK effektnek MILYEN vezérlői
vannak — a #516 óta a `docs/specs/filterdesc-registry.md` 4.2 szakasza
("Vezérlők effektenként") a forrás, ÁTVEZETVE a `filters=` lánc tényleges
pozíció-sorrendjére (ld. `effect_params.py` modul-docsztringje).
"""

from __future__ import annotations

import pytest

from picasapy.app.effect_params import (
    PARAMETERLESS_EFFECTS,
    EffectParam,
    effect_params,
    format_param_values,
    has_params,
    resolve_effect_params,
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
        "name",
        [
            "unsharp", "sat", "vignette", "glow2", "radblur", "boost",
            "polaroid", "border", "dropshadow", "museummatte", "holga",
            "matte", "nightvision", "hdr", "orton", "quantizepalette",
            "pixelate", "lomo", "localcontrast", "heatmap", "roundededges",
            "sixties", "crossprocess", "ir", "picnikgrain",
        ],
    )
    def test_known_parameterised_effects_have_controls(self, name):
        params = effect_params(name)
        assert params, f"{name}: várt vezérlők, kaptunk semmit"
        assert has_params(name) is True
        for param in params:
            assert isinstance(param, EffectParam)
            assert param.label, "minden vezérlőnek van felirata"
            assert param.kind in ("slider", "checkbox", "color")
            if param.kind == "slider" and param.max_formula is None:
                assert param.minimum < param.maximum
                assert param.minimum <= param.default <= param.maximum
                assert param.step > 0

    def test_unknown_effect_has_no_params(self):
        assert effect_params("nincs-ilyen") == ()
        assert has_params("nincs-ilyen") is False


class TestFilterdescRegistry42Table:
    """A `docs/specs/filterdesc-registry.md` 4.2 táblázatának KÉZI
    transzkripciója, effektenként (kind, min, max, default) hármasokkal —
    ez fogja meg, ha valaki elgépel egy tartományt vagy alapértéket. A
    sorrend a `filters=` lánc POZÍCIÓ-sorrendje (ld. `chain_glimmer_
    handlers.py`), NEM a 4.2 táblázat deklarációs sorrendje."""

    # (key, kind, minimum, maximum, default) — a "color"/"checkbox" sorokban
    # csak a kind + (a színnél a `color`, a jelölőnél a `default` 0/1)
    # számít, min/max nem releváns.
    EXPECTED: dict[str, tuple[tuple, ...]] = {
        "border": (
            ("slider", 0.0, 100.0, 20.0),
            ("slider", 0.0, 100.0, 5.0),
            ("slider-image", None, None, None),  # CornerRadius, 0..min(W,H)/2 (0)
            ("color", None, None, "#000000"),
            ("color", None, None, "#ffffff"),
            ("slider-image", None, None, None),  # CaptionHeight, 0..H/6 (0)
        ),
        "dropshadow": (
            ("slider", 0.0, 30.0, 4.0),
            ("slider", 0.0, 360.0, 90.0),
            ("slider", 0.0, 100.0, 10.0),
            ("color", None, None, "#000000"),
            ("color", None, None, "#ffffff"),
            ("slider", 0.0, 100.0, 30.0),
        ),
        "museummatte": (
            ("slider", 0.0, 100.0, 25.0),
            ("slider", 0.0, 100.0, 40.0),
            ("color", None, None, "#1a0e03"),
            ("color", None, None, "#f0eae4"),
        ),
        "polaroid": (
            ("slider", -10.0, 10.0, 5.0),
            ("color", None, None, "#e2e2e2"),
        ),
        "pixelate": (
            ("slider", 2.0, 150.0, 20.0),
            ("slider", 0.0, 9.0, 9.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "vignette": (
            ("slider", 0.0, 50.0, 35.0),
            ("slider", 1.0, 2.0, 1.4),
            ("slider", 0.0, 100.0, 0.0),
            ("color", None, None, "#000000"),
        ),
        "matte": (
            ("slider", 0.0, 50.0, 40.0),
            ("slider", 1.0, 2.0, 1.2),
            ("slider", 0.0, 100.0, 0.0),
            ("color", None, None, "#ffffff"),
        ),
        "hdr": (
            ("slider", 1.3, 80.0, 20.0),
            ("slider", 1.0, 7.0, 3.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "localcontrast": (
            ("slider", 1.3, 40.0, 15.0),
            ("slider", 1.0, 3.0, 1.5),
        ),
        "orton": (
            ("slider", 0.0, 50.0, 25.0),
            ("slider", 0.0, 100.0, 50.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "holga": (
            ("slider", 0.0, 100.0, 70.0),
            ("slider", 0.0, 100.0, 30.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "lomo": (
            ("slider", 0.0, 100.0, 50.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "ir": (("slider", 0.0, 100.0, 0.0),),
        "crossprocess": (("slider", 0.0, 100.0, 0.0),),
        "nightvision": (
            ("slider", -50.0, 50.0, 0.0),
            ("slider", -50.0, 50.0, 0.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "heatmap": (
            ("slider", -180.0, 180.0, 0.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "quantizepalette": (
            ("slider", 2.0, 30.0, 8.0),
            ("slider", 0.0, 100.0, 80.0),
            ("slider", 0.0, 100.0, 0.0),
        ),
        "twotone": (
            ("slider", -95.0, 95.0, 0.0),
            ("slider", 0.0, 100.0, 20.0),
            ("slider", 0.0, 100.0, 0.0),
            ("color", None, None, "#004488"),
            ("color", None, None, "#ffff00"),
        ),
        "roundededges": (
            ("slider-image", None, None, None),  # CornerRadius 0..min(W,H)/2, alap min(W,H)/10
            ("color", None, None, "#ffffff"),
        ),
        "sixties": (
            ("slider", 0.0, 100.0, 20.0),
            ("color", None, None, "#ffffff"),
            ("checkbox", None, None, 1.0),
        ),
        "picnikgrain": (
            ("slider", 0.0, 50.0, 10.0),
            ("checkbox", None, None, 0.0),
        ),
    }

    @pytest.mark.parametrize("name", sorted(EXPECTED))
    def test_control_list_matches_the_spec_table(self, name):
        params = effect_params(name)
        expected = self.EXPECTED[name]
        assert len(params) == len(expected), (
            f"{name}: {len(params)} vezérlő van, a 4.2 tábla {len(expected)}-et ír"
        )
        for index, (param, exp) in enumerate(zip(params, expected, strict=True)):
            kind = exp[0]
            if kind == "slider-image":
                assert param.kind == "slider"
                assert param.max_formula is not None, (
                    f"{name}[{index}]: képfüggő tartományt vártunk"
                )
            elif kind == "slider":
                _, minimum, maximum, default = exp
                assert param.kind == "slider"
                assert param.minimum == pytest.approx(minimum)
                assert param.maximum == pytest.approx(maximum)
                assert param.default == pytest.approx(default)
            elif kind == "checkbox":
                assert param.kind == "checkbox"
                assert param.default == pytest.approx(exp[3])
            elif kind == "color":
                assert param.kind == "color"
                assert param.color.lower() == exp[3].lower()
            else:  # pragma: no cover - hibás teszt-tábla
                raise AssertionError(f"ismeretlen vezérlő-fajta: {kind}")


class TestImageDependentRanges:
    """A `docs/specs/filterdesc-registry.md` 4.2 szerinti képfüggő
    tartományok (`0..min(W,H)/2`, `0..H/6`, `min(W,H)/10` alapérték) a
    JELENLEGI kép méretéből számolódnak — nem beégetett szám."""

    def test_border_corner_radius_and_caption_height(self):
        params = resolve_effect_params("border", width=1000, height=600)
        corner_radius = params[2]
        caption_height = params[5]
        assert corner_radius.maximum == pytest.approx(min(1000, 600) / 2.0)
        assert corner_radius.default == pytest.approx(0.0)
        assert caption_height.maximum == pytest.approx(600 / 6.0)
        assert caption_height.default == pytest.approx(0.0)

    def test_border_corner_radius_uses_the_shorter_side(self):
        # portré kép: min(W,H) a SZÉLESSÉG, nem a magasság
        params = resolve_effect_params("border", width=400, height=1200)
        assert params[2].maximum == pytest.approx(400 / 2.0)

    def test_rounded_edges_default_is_a_tenth_of_the_shorter_side(self):
        params = resolve_effect_params("roundededges", width=2000, height=1000)
        corner_radius = params[0]
        assert corner_radius.maximum == pytest.approx(1000 / 2.0)
        assert corner_radius.default == pytest.approx(min(2000, 1000) / 10.0)

    def test_missing_image_size_falls_back_to_a_positive_range(self):
        # nincs betöltött kép (width/height None) — a katalógus akkor is
        # egy ÉRVÉNYES (nem 0..0) tartományt ad, csak a felhasználó elé ez
        # a helyzet valós szerkesztésnél sosem kerül (ld. `EditController.
        # beginEdit`, mindig van `_image_path`)
        params = resolve_effect_params("border", width=None, height=None)
        assert params[2].maximum > 0
        assert params[5].maximum > 0

    def test_non_image_dependent_params_are_unaffected(self):
        with_size = resolve_effect_params("border", width=1000, height=600)
        without_size = resolve_effect_params("border", width=None, height=None)
        assert with_size[0].maximum == without_size[0].maximum == 100.0


class TestMeasuredDefaults:
    """Az alapértékek a mért ini-mintákat kövessék (filters-decoded.md)."""

    @pytest.mark.parametrize(
        ("name", "expected"),
        [
            ("boost", (50.0,)),                 # Boost=1,50.000000
            ("soften", (50.0, 50.0)),           # Soften=1,50.000000,50.000000
            ("pencilsketch", (2.0, 100.0, 0.0)),  # PencilSketch=1,2,100,0
            ("comicize", (20.0, 50.0, 50.0)),   # Comicize=1,20,50,50
            ("unsharp", (0.6,)),                # unsharp=1 == unsharp2=1,0.6
        ],
    )
    def test_defaults_match_the_measured_samples(self, name, expected):
        actual = tuple(p.default for p in effect_params(name))
        assert actual == pytest.approx(expected)

    def test_vignette_blur_and_strength_defaults(self):
        params = effect_params("vignette")
        assert params[0].default == pytest.approx(35.0)  # Blur
        assert params[1].default == pytest.approx(1.4)   # Strength


class TestFormatting:
    """A láncba a Picasa `filters=` alakja kerül (round-trip elv)."""

    def test_values_are_formatted_with_six_decimals(self):
        assert format_param_values([50.0, 1.25]) == ("50.000000", "1.250000")

    def test_empty_values(self):
        assert format_param_values([]) == ()

    def test_non_numeric_is_rejected(self):
        with pytest.raises((TypeError, ValueError)):
            format_param_values(["nem szám"])

    def test_checkbox_values_are_plain_integers(self):
        params = effect_params("sixties")
        formatted = format_param_values([20.0, "#ffffff", True], params)
        assert formatted[2] == "1"
        formatted_off = format_param_values([20.0, "#ffffff", False], params)
        assert formatted_off[2] == "0"

    def test_color_values_use_the_00rrggbb_filters_hex(self):
        params = effect_params("vignette")
        formatted = format_param_values([35.0, 1.4, 0.0, "#ff8800"], params)
        assert formatted[3] == "00ff8800"

    def test_invalid_color_is_rejected(self):
        params = effect_params("vignette")
        with pytest.raises(ValueError):
            format_param_values([35.0, 1.4, 0.0, "nem szín"], params)


class TestPicnikFocalPixelateAndMaskEffectsAreDeliberatelySkipped:
    """#516 jelentés: a festhető maszkos effektek (ReanimatedEyeColor,
    Soften, PicnikTint) és a renderer nélküli `PicnikFocalPixelate` NEM
    kaptak vezérlőt — ez SZÁNDÉKOS, ld. a `effect_params.py` modul-
    docsztringjét."""

    def test_reanimated_eye_color_has_no_ui_effect_name(self):
        assert "reanimatedeyecolor" not in _EFFECT_NAMES

    def test_picnik_tint_MOST_MAR_felületi_effekt(self):
        """#2141: a #516 kihagyása MEGDŐLT — de nem önkényesen.

        A #516 azért hagyta ki, mert nincs ecset-eszközünk. A #685
        mérőszettjének exportja viszont azt mutatja, hogy az EREDETI
        Picasa is a **teljes képre** futtatja befestés nélkül
        (ΔE 36,9 — ld. `EMPTY_MASK_DEFAULT_OPS` kommentje), tehát a mi
        viselkedésünk itt megegyezik az eredetivel. Az 1. effekt-fül 6.
        csempéje az eredeti csempe-táblája szerint a `PicnikTint`."""
        assert "picniktint" in _EFFECT_NAMES

    def test_picnik_focal_pixelate_has_no_ui_effect_name(self):
        assert "picnikfocalpixelate" not in _EFFECT_NAMES

    def test_soften_keeps_its_pre_516_controls(self):
        # Soften MÁR volt vezérlős (#316); a #516 táblázat szerinti
        # Impact/Fade+maszk átnevezés a maszk-eszköz híján KIMARADT
        params = effect_params("soften")
        assert [p.key for p in params] == ["amount", "radius"]
