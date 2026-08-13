"""A fülek tartalma SOSEM lóghat a Visszavonás/Újra sorra — #616.

Felhasználói hibajelentés (2026-08-13, képernyőképpel): az Effektek fülön a
gombsor a HARMADIK és a NEGYEDIK csempesor között lebegett, rálógva a
csempékre.

Az ok: a fülek közvetlenül a panelre voltak horgonyozva, vágás és görgetés
nélkül. Egy 12 csempés effekt-fül (3×4) a rövidebb ablakban magasabb, mint
a rendelkezésre álló hely — a rácsnak nem volt hova rövidülnie, ezért
túlnyúlt, és a panel alján ülő gombsor ráfeküdt.

Az eredeti Picasa ugyanezt a kettéválasztást használja: a csempék az
`editpanel/fxthumbs` (`gridtilecont`) konténerben élnek, a Visszavonás/Újra
pedig a sajátjában — `editpanel/filter_status_container`, benne
`filter_undo`/`filter_redo`.

A panelt ÖNÁLLÓAN töltjük be (a `test_editor_tabs.py` mintája), mert a
geometriát így tudjuk pontosan megadni: a hibát épp a SZŰK panel hozza elő.
"""

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


def _panel(engine, height, active_tab=2):
    """EditorPanel adott magassággal — a hiba a SZŰK panelen jelentkezik."""
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'EditorPanel {{ objectName: "panel"; width: 240; height: {height};'
            f" activeTab: {active_tab} }}\n"
        ).encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestTabsNeverOverlapTheUndoRow:
    def test_the_tab_area_is_clipped(self, qml_engine):
        panel = _panel(qml_engine, height=400)

        assert _child(panel, "editorTabScroll").property("clip") is True, (
            "vágás nélkül a fül tartalma kilóg a saját területéből"
        )

    @pytest.mark.parametrize("height", [320, 400, 560, 900])
    def test_the_tab_area_stops_above_the_undo_row(self, qml_engine, height):
        """A tényleges hiba: a fülterület alja SOSEM ér a gombsor alá —
        semmilyen panelmagasságnál."""
        panel = _panel(qml_engine, height=height)

        scroll = _child(panel, "editorTabScroll")
        undo_row = _child(panel, "editorGlobalUndoRow")

        scroll_bottom = scroll.property("y") + scroll.property("height")
        assert scroll_bottom <= undo_row.property("y") + 1, (
            f"{height} px magas panelen a fülterület belelóg a gombsorba"
        )

    def test_content_taller_than_the_area_becomes_scrollable(self, qml_engine):
        """Ha a fül tartalma magasabb a helynél, GÖRGETHETŐ — nem túlnyúlik.

        (A csempék bélyegkép nélkül alacsonyabbak, mint élesben, ezért a
        szűkösséget kis panelmagassággal állítjuk elő.)"""
        panel = _panel(qml_engine, height=160)

        scroll = _child(panel, "editorTabScroll")

        assert scroll.property("contentHeight") > scroll.property("height"), (
            "a szűk panelen a rácsnak görgethetőnek kell lennie"
        )
        # és a gombsor ilyenkor is a helyén marad
        undo_row = _child(panel, "editorGlobalUndoRow")
        assert (
            scroll.property("y") + scroll.property("height")
            <= undo_row.property("y") + 1
        )

    def test_a_tall_panel_needs_no_scrolling(self, qml_engine):
        """Bő helyen nincs görgetés — az eredetiben sem volt."""
        panel = _panel(qml_engine, height=900)

        scroll = _child(panel, "editorTabScroll")

        assert scroll.property("contentHeight") <= scroll.property("height")


class TestParamPanelStaysUsable:
    """#616 mellékhatás-őr: a csúszkás alpanel MAGA IS Flickable, és egy
    Flickable implicit magassága 0 — ha a fülek görgethető területébe
    csomagolnánk, nulla magasságot kapna, azaz eltűnne. Ezért kívül marad,
    saját horgonnyal a gombsorig."""

    def _with_param_panel(self, qml_engine):
        # a `paramPanelActive` futásidőben kapcsolódik (a panel a
        # létrehozáskori értéket felülírja), ezért UTÓLAG állítjuk
        panel = _panel(qml_engine, height=600)
        panel.setProperty("paramEffectName", "sepia")
        panel.setProperty("paramPanelActive", True)
        return panel

    def test_the_param_panel_has_a_real_height(self, qml_engine):
        panel = self._with_param_panel(qml_engine)

        param = _child(panel, "editorEffectParamScroll")

        assert param.property("height") > 0, "az alpanel eltűnt"
        assert param.property("clip") is True

    def test_the_param_panel_replaces_the_tabs(self, qml_engine):
        """Az alpanel a fülek HELYETT jelenik meg, nem föléjük."""
        panel = self._with_param_panel(qml_engine)

        assert _child(panel, "editorTabScroll").property("visible") is False

    def test_the_param_panel_stops_above_the_undo_row(self, qml_engine):
        panel = self._with_param_panel(qml_engine)

        param = _child(panel, "editorEffectParamScroll")
        undo_row = _child(panel, "editorGlobalUndoRow")

        assert (
            param.property("y") + param.property("height")
            <= undo_row.property("y") + 1
        )
