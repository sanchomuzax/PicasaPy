"""#7371: a Film Grain menüparancs (`grain2`) a nyitott szerkesztőben alkalmazható.

Az eredetiben a Kép ▸ Csoportos szerkesztés ▸ Film Grain a `grain2`-t hívja, az
Effektek fül 5. csempéje viszont a `PicnikGrain`, ezért a `grain2` a #2141 óta
nem tagja a csempék neveinek (`_EFFECT_NAMES`). A nyitott szerkesztő
`applyEffect`-je ezt `ValueError`-ral utasította volna el. A név külön,
csak-menüs halmazban él: a csempe-katalógus (és annak őrei) változatlan.
"""

from __future__ import annotations

import pytest
from support.jpeg_factory import make_jpeg

from picasapy.ini import load_document


@pytest.fixture
def controller(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditController(EditPreviewProvider())


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _filters(photo) -> str:
    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    section = load_document(ini).section("IMG_0001.jpg")
    return (section.get("filters") if section else None) or ""


class TestNevkeszlet:
    def test_a_grain2_alkalmazhato_de_nem_csempe_nev(self):
        from picasapy.app.edit_controller import _APPLICABLE_EFFECTS, _EFFECT_NAMES

        assert "grain2" in _APPLICABLE_EFFECTS
        assert "grain2" not in _EFFECT_NAMES, (
            "a csempe-katalógus nem bővülhet: az 1. fül 5. csempéje a picnikgrain"
        )

    def test_a_menu_only_halmaz_pontosan_a_grain2(self):
        from picasapy.app.edit_controller_shared import _MENU_ONLY_EFFECT_NAMES

        assert _MENU_ONLY_EFFECT_NAMES == ("grain2",)

    def test_a_grain2_visszavonas_felirata_film_grain(self):
        from picasapy.app.edit_action_names import ACTION_LABELS

        assert ACTION_LABELS["grain2"][0] == "Film Grain"


class TestAlkalmazas:
    def test_a_grain2_az_egykepes_kotegnek_megfelelo_lancot_ir(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))

        controller.applyEffect("grain2")

        assert _filters(photo) == "grain2=1;"
        assert controller.undoAction == "grain2"

    def test_a_grain2_visszavonhato(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.applyEffect("grain2")

        controller.undo()

        assert _filters(photo) == ""

    def test_ismeretlen_nev_tovabbra_is_hiba(self, controller, photo):
        controller.beginEdit("1", str(photo))
        with pytest.raises(ValueError):
            controller.applyEffect("nincs-ilyen-effekt")
