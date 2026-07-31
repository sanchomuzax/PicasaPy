"""#316: az effekt-alpanel vezérlő-oldala — élő előnézet és Alkalmaz.

A paraméteres effekt gombja csúszkás alpanelt nyit: húzás közben `previewEffect`
(csak előnézet, nincs ini-írás, nincs undo-lépés), az Alkalmaz gomb pedig
`applyEffectWithParams` (undo + mentés). A Mégse egyszerűen elveti az
előnézetet — a `discardEffectPreview` visszaállítja a mentett láncot.

A minta a `previewFinetune`/`setFinetune` páros (#20).
"""

from __future__ import annotations

import pytest

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


def _chain(controller) -> str:
    """A mentett (nem előnézeti) szűrőlánc szöveges alakja."""
    return controller._session.to_value()


@pytest.fixture
def editing(controller, photo):
    controller.beginEdit("1", str(photo))
    return controller


class TestParameterQuery:
    def test_effect_has_params_is_exposed_to_qml(self, editing):
        assert editing.effectHasParams("boost") is True
        assert editing.effectHasParams("sepia") is False
        assert editing.effectHasParams("nincs-ilyen") is False

    def test_effect_params_are_qml_friendly_dicts(self, editing):
        params = editing.effectParams("soften")
        assert isinstance(params, list), "a QML-ben a tuple NEM tömb (#232)"
        assert len(params) == 2
        first = params[0]
        assert set(first) >= {"key", "label", "minimum", "maximum", "default", "step"}
        assert first["default"] == pytest.approx(50.0)

    def test_unknown_effect_gives_empty_list(self, editing):
        assert editing.effectParams("nincs-ilyen") == []


class TestPreviewDoesNotCommit:
    def test_preview_does_not_touch_the_saved_chain(self, editing):
        before = _chain(editing)
        editing.previewEffect("boost", [80.0])
        assert _chain(editing) == before, "az előnézet nem írhat a láncba"

    def test_preview_bumps_the_revision(self, editing):
        before = editing.revision
        editing.previewEffect("boost", [80.0])
        assert editing.revision > before, "a nézőnek újra kell rajzolnia"

    def test_preview_of_an_unknown_effect_is_ignored(self, editing):
        before = (_chain(editing), editing.revision)
        editing.previewEffect("nincs-ilyen", [1.0])
        assert (_chain(editing), editing.revision) == before

    def test_discard_restores_the_saved_chain(self, editing):
        editing.previewEffect("boost", [80.0])
        editing.discardEffectPreview()
        assert _chain(editing) == ""


class TestApplyWritesTheChain:
    def test_apply_appends_with_the_given_values(self, editing):
        editing.applyEffectWithParams("boost", [80.0])
        assert _chain(editing) == "Boost=1,80.000000;"

    def test_apply_uses_the_picasa_spelling(self, editing):
        editing.applyEffectWithParams("polaroid", [12.0])
        assert _chain(editing).startswith("Polaroid=1,12.000000")

    def test_apply_without_values_falls_back_to_defaults(self, editing):
        editing.applyEffectWithParams("boost", [])
        assert _chain(editing) == "Boost=1,50.000000;"

    def test_apply_is_undoable(self, editing):
        editing.applyEffectWithParams("boost", [80.0])
        assert editing.canUndo is True
        editing.undo()
        assert _chain(editing) == ""

    def test_apply_of_an_unknown_effect_is_ignored(self, editing):
        editing.applyEffectWithParams("nincs-ilyen", [1.0])
        assert _chain(editing) == ""

    def test_parameterless_effect_still_works_through_the_same_slot(self, editing):
        editing.applyEffectWithParams("sepia", [])
        assert _chain(editing) == "sepia=1;"

    def test_too_many_values_are_truncated_to_the_catalogue(self, editing):
        # a felület sosem küld többet, de egy elrontott hívás se rontsa el a láncot
        editing.applyEffectWithParams("boost", [80.0, 999.0, 111.0])
        assert _chain(editing) == "Boost=1,80.000000;"
