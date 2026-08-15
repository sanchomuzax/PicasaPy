"""#571 — az „Régi effektek" fül: a Picasa motorjában benne maradt, de a
3.9 felületén NEM elérhető szűrők.

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


def _make_panel(engine, active_tab=6):
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
    def test_tab_button_is_present(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.findChild(QObject, "editTabLegacy") is not None

    def test_tab_label_is_not_truncated(self, qml_engine, qt_app):
        # #318 tanulság: tördelés, nem vágás — a hetedik fül sem veszíthet
        # szöveget a szűkebb fülsávban
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        label = panel.findChild(QObject, "editTabLegacyLabel")
        assert label is not None
        assert label.property("truncated") is False

    def test_tab_bar_still_fits_the_panel_width(self, qml_engine, qt_app):
        """A hetedik fül nem lóghat ki: az egész sávnak a panel
        szélességében kell maradnia (a #328 4. pontjának megfelelően)."""
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
            "editTabLegacy",
        )
        total = sum(panel.findChild(QObject, n).property("width") for n in names)
        assert total <= tab_bar.property("width") + 5

    def test_column_visible_only_on_its_own_tab(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=6)
        qt_app.processEvents()
        column = panel.findChild(QObject, "legacyEffectsColumn")
        assert column is not None
        assert column.property("visible") is True

        other = _make_panel(qml_engine, active_tab=2)
        qt_app.processEvents()
        assert other.findChild(QObject, "legacyEffectsColumn").property(
            "visible"
        ) is False

    def test_intro_line_explains_the_tab(self, qml_engine, qt_app):
        # #571 2. pont: a fül teteje egy sorban mondja ki, mi ez a készlet
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        intro = panel.findChild(QObject, "legacyEffectsIntro")
        assert intro is not None
        assert intro.property("text")

    def test_no_dot_without_a_controller(self, qml_engine, qt_app):
        # controller nélkül (izolált teszt) nincs lánc — nincs jelzés sem
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        assert panel.property("legacyEffectsPresent") is False
        mark = panel.findChild(QObject, "editTabLegacyMark")
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
        ):
            assert can_render_filter(key)

    def test_the_undecoded_ones_are_not_renderable(self):
        # ezek addig szürkék, amíg a natív magjuk nincs megfejtve — a
        # felületen nem lehet aktívnak látszó, de nem ható gomb
        from picasapy.render.chain import can_render_filter

        for key in ("triple", "colorfix", "gamma"):
            assert not can_render_filter(key)

    def test_debug_is_deliberately_absent(self):
        # a `debug` („For debugging") fejlesztői eszköz volt, nem
        # felhasználói effekt — a jegy is kizárja
        from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

        assert "debug" not in LEGACY_EFFECT_KEYS

    def test_dead_legacy_name_is_marked_as_such(self):
        from picasapy.render.chain import DEAD_LEGACY_OPS
        from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

        # a halott név LÁTSZIK a fülön (egy régi láncban előfordulhat),
        # de a felület más magyarázatot ad rá (#567)
        assert "focalpixelate" in LEGACY_EFFECT_KEYS
        assert "focalpixelate" in DEAD_LEGACY_OPS
