"""A „Régi effektek" fül gombjai valóban működjenek — #582.

A #571-ben a fül csak megjelent: a gombjai a `LEGACY_EFFECTS` kulcsaival
hívták az `applyEffect`-et, az viszont csak a régi felület effektjeit
fogadta el, így MINDEN gomb `ValueError: Érvénytelen effekt: 'fill'`-be
futott. Az itteni tesztek a fül és a szerkesztő közötti szerződést őrzik:
amit a fül aktívként kínál, azt alkalmazni is lehet, és a renderelő is
elbírja.
"""

import numpy as np
import pytest

from picasapy.ini.filters import parse_filters
from picasapy.render.chain import apply_filters, can_render_filter
from picasapy.render.legacy_effects import LEGACY_EFFECTS
from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _filters(photo):
    from picasapy.ini import load_document

    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    section = load_document(ini).section("IMG_0001.jpg")
    return (section.get("filters") if section else None) or ""


ENABLED_KEYS = [
    effect.key for effect in LEGACY_EFFECTS if can_render_filter(effect.key)
]
DISABLED_KEYS = [
    effect.key for effect in LEGACY_EFFECTS if not can_render_filter(effect.key)
]


class TestEveryEnabledButtonWorks:
    @pytest.mark.parametrize("key", ENABLED_KEYS)
    def test_apply_does_not_raise_and_appends_a_layer(
        self, controller, photo, key
    ):
        controller.beginEdit("1", str(photo))
        controller.applyEffect(key)  # #582: ez dobott ValueError-t
        assert _filters(photo).startswith(f"{key}=1")

    @pytest.mark.parametrize("key", ENABLED_KEYS)
    def test_the_renderer_can_apply_what_we_wrote(self, controller, photo, key):
        # a láncba írt alak a RENDERELŐN is átmegy: a `fill` például
        # kötelező erősség-paramétert vár, paraméter nélkül kivételt dobna
        controller.beginEdit("1", str(photo))
        controller.applyEffect(key)
        ops = parse_filters(_filters(photo))
        image = np.full((6, 8, 3), 128, dtype=np.uint8)
        rendered, skipped = apply_filters(image, ops)
        assert rendered.shape == image.shape
        assert list(skipped) == []  # a lánc nem hagyta ki: tényleg hatott

    @pytest.mark.parametrize("key", ENABLED_KEYS)
    def test_apply_is_undoable(self, controller, photo, key):
        controller.beginEdit("1", str(photo))
        controller.applyEffect(key)
        assert controller.undoAction == key
        controller.undo()
        assert _filters(photo) == ""


class TestDisabledButtonsStayRefused:
    @pytest.mark.parametrize("key", DISABLED_KEYS)
    def test_a_filter_without_a_renderer_is_refused(
        self, controller, photo, key
    ):
        # ezek a fülön szürkén, kattinthatatlanul jelennek meg (#571) — ha
        # mégis idáig jutnának, a hibás lánc helyett hibát kell kapni
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.applyEffect(key)


class TestDefaultsComeFromTheOriginal:
    def test_fill_gets_the_native_25_percent(self, controller, photo):
        # #567: a natív `autobacklight` render callbackje ugyanazt a magot
        # hívja fix 0.25-tel — a `fill` alapértéke ezért 0.25, nem 0
        # (0-val a gomb láthatóan nem csinálna semmit)
        controller.beginEdit("1", str(photo))
        controller.applyEffect("fill")
        assert _filters(photo) == "fill=1,0.250000;"

    def test_radtint_gets_centre_and_the_filterdesc_feather(
        self, controller, photo
    ):
        # #565: `radtint=1,x,y,feather[,szín]` — középre tett fókuszpont és
        # a filterdesc.xml 0.25-ös Feather-alapértéke
        controller.beginEdit("1", str(photo))
        controller.applyEffect("radtint")
        assert _filters(photo) == "radtint=1,0.500000,0.500000,0.250000;"

    def test_autobacklight_is_a_one_click_filter(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("autobacklight")
        assert _filters(photo) == "autobacklight=1;"
