"""#571/#6443 — a régi effektek a Glimmer csempékkel közös fülre kerültek.

Ez TUDATOS eltérés az eredetitől — a fül léte maga is szerződés, ezért
teszttel őrizzük. A gombok a katalógusból generálódnak, és hogy melyik ÉL,
azt a renderelő dönti el: aktívnak látszó, de nem ható gomb nem lehet.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _make_panel(engine, active_tab=5):
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n'
        ).encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([component, obj])
    return obj


class TestLegacyTabExists:
    def test_combined_tab_is_present_and_old_separate_tab_is_gone(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "editTabEffects4") is not None
        assert panel.findChild(QObject, "editTabLegacy") is None

    def test_tab_label_is_not_truncated(self, qml_engine, qt_app):
        # #318 tanulság: tördelés, nem vágás — az összevont fül sem
        # veszíthet szöveget a szűkebb fülsávban.
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        label = panel.findChild(QObject, "editTabEffects4Label")
        assert label is not None
        assert label.property("truncated") is False
        tab = panel.findChild(QObject, "editTabEffects4")
        assert tab.property("description") == (
            "Forgotten or deprecated effects brought back to life"
        )

    def test_tab_bar_still_fits_the_panel_width(self, qml_engine, qt_app):
        """A hat fül hézag nélkül kitölti a sávot."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        tab_bar = panel.findChild(QObject, "editTabBar")
        names = (
            "editTabFixes",
            "editTabFinetune",
            "editTabEffects",
            "editTabEffects2",
            "editTabEffects3",
            "editTabEffects4",
        )
        total = sum(panel.findChild(QObject, n).property("width") for n in names)
        assert total <= tab_bar.property("width") + 5

    def test_combined_effect_column_is_visible_on_its_tab(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=5)
        qt_app.processEvents()
        column = panel.findChild(QObject, "effectsColumn4")
        assert column is not None
        assert column.property("visible") is True

        other = _make_panel(qml_engine, active_tab=2)
        qt_app.processEvents()
        assert other.findChild(QObject, "effectsColumn4").property(
            "visible"
        ) is False

    def test_no_gray_intro_header(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "legacyEffectsIntro") is None

    def test_no_dot_without_a_controller(self, qml_engine, qt_app):
        # controller nélkül (izolált teszt) nincs lánc — nincs jelzés sem
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.property("legacyEffectsPresent") is False
        mark = panel.findChild(QObject, "editTabEffects4Mark")
        assert mark is not None and mark.property("visible") is False


class TestLegacyCatalogue:
    """A katalógus a renderelőhöz van kötve — kézzel karbantartott
    engedélyezett-lista nincs, így nem lehet hazug gomb."""

    def test_enabled_flags_come_from_the_renderer(self):
        from picasapy.render.chain import can_render_filter
        from picasapy.render.legacy_effects import LEGACY_EFFECTS

        for effect in LEGACY_EFFECTS:
            assert isinstance(can_render_filter(effect.key), bool)

    def test_the_decoded_ones_are_renderable(self):
        # #565, #567 és #623 után ezeknek élniük KELL a fülön — az
        # irányított család MIND A NÉGY tagja renderel
        from picasapy.render.chain import can_render_filter

        for key in (
            "radtint",
            "autobacklight",
            "fill",
            "dir_sat",
            "dir_brite",
            "dir_sharp",
            "linblur",
            # #687: a natív tónus-/szín-szűrők
            "contrast",
            "gamma",
            "colortemp",
            "backlight",
            "triple",
            "triple2",
            "triple3",
            "autocontrast",
            "shadow",
            # #5304: a Rainbow kapott natív algoritmust és a lánc futtatja.
            "rainbow",
        ):
            assert can_render_filter(key)

    def test_colorfix_whitept_and_blur_are_rendered_and_offer_controls(self):
        from picasapy.render.chain import can_offer_filter_control, can_render_filter

        for key in ("colorfix", "whitept", "blur"):
            assert can_render_filter(key)
            assert can_offer_filter_control(key)

    def test_debug_is_deliberately_absent(self):
        # a `debug` („For debugging") fejlesztői eszköz volt, nem
        # felhasználói effekt — a jegy is kizárja
        from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

        assert "debug" not in LEGACY_EFFECT_KEYS

    def test_dead_legacy_name_is_marked_as_such(self):
        from picasapy.render.chain import DEAD_LEGACY_OPS
        from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

        # a halott név felismerhető marad a láncban, de a #6443 kivezette
        # a használhatatlan csempét a felületről.
        assert "focalpixelate" in LEGACY_EFFECT_KEYS
        assert "focalpixelate" in DEAD_LEGACY_OPS
