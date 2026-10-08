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
    _CATALOGUE,
    LEGACY_COLORWHEEL_EFFECTS,
    PARAMETERLESS_EFFECTS,
    EffectParam,
    effect_params,
    format_param_values,
    has_params,
    resolve_effect_params,
)
from picasapy.app.edit_controller import _EFFECT_INI_NAMES, _EFFECT_NAMES
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
            "sixties", "crossprocess", "ir", "picnikgrain", "picniktint",
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
        "picniktint": (
            ("slider", 0.0, 100.0, 0.0),
            ("color", None, None, "#80cfff"),
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
        formatted = format_param_values(
            [20.0, "#ffffff", True], params, effect="sixties"
        )
        assert formatted[2] == "1"
        formatted_off = format_param_values(
            [20.0, "#ffffff", False], params, effect="sixties"
        )
        assert formatted_off[2] == "0"

    def test_color_values_use_the_00rrggbb_filters_hex(self):
        params = effect_params("vignette")
        formatted = format_param_values(
            [35.0, 1.4, 0.0, "#ff8800"], params, effect="vignette"
        )
        assert formatted[3] == "00ff8800"

    def test_color_without_an_effect_name_is_rejected(self):
        # #3908: az alfa az effekten múlik (`ff` a régi négyesnél, `00` a
        # többinél) — effektnév nélkül a szín alfája nem dönthető el, ezért
        # hangos hiba, nem csendes `00` (ami a `tint`-nél épp a rossz alfa).
        params = effect_params("tint")
        with pytest.raises(ValueError):
            format_param_values([0.5, "#336699"], params)

    def test_colorless_params_need_no_effect_name(self):
        # szín nélküli katalógusnál az alfa-kérdés föl sem merül
        params = effect_params("boost")
        assert format_param_values([50.0], params) == ("50.000000",)

    @pytest.mark.parametrize("effect", ["tint", "ansel", "dir_tint", "radtint"])
    def test_the_four_legacy_colorwheel_effects_use_ff_alpha(self, effect):
        # #3908: a Picasa a régi, színkerekes effektek színét `ff` alfával
        # írja (`%08x`), szemben a Picnik-generációs effektek `00`-jével.
        params = effect_params(effect)
        color_index = next(
            index for index, param in enumerate(params) if param.kind == "color"
        )
        values = [
            "#336699"
            if index == color_index
            else (param.color if param.kind == "color" else param.default)
            for index, param in enumerate(params)
        ]
        formatted = format_param_values(values, params, effect=effect)
        assert formatted[color_index] == "ff336699"

    @pytest.mark.parametrize(
        "effect", ["vignette", "border", "dropshadow", "neon", "sixties"]
    )
    def test_picnik_generation_effects_keep_00_alpha(self, effect):
        # #3908: ezek az effektek MARADNAK `00` alfásak — a katalógus-kulcs
        # átadása nem sodorja bele őket a régi négyes csoportba.
        params = effect_params(effect)
        color_index = next(
            index for index, param in enumerate(params) if param.kind == "color"
        )
        values = [
            "#336699"
            if index == color_index
            else (param.color if param.kind == "color" else param.default)
            for index, param in enumerate(params)
        ]
        formatted = format_param_values(values, params, effect=effect)
        assert formatted[color_index] == "00336699"

    def test_invalid_color_is_rejected(self):
        params = effect_params("vignette")
        with pytest.raises(ValueError):
            format_param_values([35.0, 1.4, 0.0, "nem szín"], params)


class TestColorAlphaGroupGuard:
    """#3908 őre: a színes katalógus-effektek két csoportra oszlanak — a
    régi, natív, színkerekes négyes (`LEGACY_COLORWHEEL_EFFECTS`, `ff` alfa,
    kisbetűs ini-név) és a Picnik-generáció (`00` alfa, CamelCase ini-név).
    Egy új, natív (kisbetűs ini-nevű) színes effekt csendben a `00` ágra
    esne — ez az őr kiszúrja, és a felvevőnek el kell döntenie, melyik
    csoportba tartozik."""

    @staticmethod
    def _colored_catalogue_keys() -> list[str]:
        return sorted(
            key
            for key, params in _CATALOGUE.items()
            if any(param.kind == "color" for param in params)
        )

    def test_every_colored_effect_belongs_to_a_known_alpha_group(self):
        orphans = [
            (key, _EFFECT_INI_NAMES.get(key, key))
            for key in self._colored_catalogue_keys()
            if key not in LEGACY_COLORWHEEL_EFFECTS
            and not _EFFECT_INI_NAMES.get(key, key)[:1].isupper()
        ]
        assert not orphans, (
            "natív (kisbetűs ini-nevű) színes effekt a régi négyesen kívül — "
            f"döntsd el, `ff` vagy `00` alfával ír-e a Picasa: {orphans}"
        )

    def test_the_legacy_group_is_the_lowercase_colored_natives(self):
        # a csoport tagjai valóban színesek és natív (kisbetűs) nevűek —
        # elavult vagy elírt tag nem ülhet benne
        colored = set(self._colored_catalogue_keys())
        for key in LEGACY_COLORWHEEL_EFFECTS:
            assert key in colored, key
            assert _EFFECT_INI_NAMES.get(key, key) == key, key


class TestReanimatedEyeColorAndFocalPixelate:
    """A Vámpírszem nem önálló effektpanel-bejegyzés; a másik négy effekt
    egész képre fut (#3541). A renderer nélküli `PicnikFocalPixelate` külön
    okból marad ki."""

    def test_reanimated_eye_color_has_no_ui_effect_name(self):
        assert "reanimatedeyecolor" not in _EFFECT_NAMES

    def test_picnik_tint_MOST_MAR_felületi_effekt(self):
        """#2141: a #516 kihagyása MEGDŐLT — de nem önkényesen.

        A #516 azért hagyta ki, mert nincs ecset-eszközünk. A #685
        mérőszettjének exportja viszont azt mutatja, hogy az EREDETI
        Picasa is a **teljes képre** futtatja befestés nélkül (#3541), tehát
        a mi viselkedésünk itt megegyezik az eredetivel. Az 1. effekt-fül 6.
        csempéje az eredeti csempe-táblája szerint a `PicnikTint`."""
        assert "picniktint" in _EFFECT_NAMES

    def test_picnik_tint_szine_a_fade_utan_kerul_a_lancba(self):
        """#4554: a Tint Color a Fade után, a handler által olvasott rekeszben áll."""
        params = effect_params("picniktint")
        assert [param.key for param in params] == ["fade", "color"]
        assert [param.label for param in params] == ["Fade", "Tint Color"]
        assert params[1].kind == "color"
        assert params[1].color.lower() == "#80cfff"

    def test_picnik_focal_pixelate_a_shift_par_miatt_szerepel(self):
        """#3315: a `pixelate` csempe Shift-párja — enélkül a Shiftes
        kattintás `ValueError`-t adna."""
        assert "picnikfocalpixelate" in _EFFECT_NAMES

    def test_soften_a_MERT_keszletet_hozza(self):
        """#723: `_sldrImpact` → Softness és `_sldrFade` → Fade.

        A korábbi `amount`/`radius` pár nem csak felirat-hiba volt: a lánc
        a MÁSODIK rekeszt fokozatnak olvassa, tehát a „Radius" feliratú
        csúszka a fokozatot állította."""
        params = effect_params("soften")
        assert [p.key for p in params] == ["impact", "fade"]
