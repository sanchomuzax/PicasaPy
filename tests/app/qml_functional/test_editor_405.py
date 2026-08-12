"""QML-funkcionális tesztek: a szerkesztő bal paneljének Picasa-hű
kinézete (#405) — a felhasználói screenshot-összevetés 6 pontja:

1. (kép-előnézetes eszköz-csempék a "Gyakori javítások" fülön — a #411
   VISSZAVONTA: ld. test_editor_411.py, ott ikonos csempékre vált),
2. panel szélessége/aránya (a #411 a FIX 280px-re javította — ld.
   test_editor_411.py),
3. (fül-ikonok — már lefedve a test_editor_look.py `TestIconTabs`-jában),
4. a "Gyakori javítások" szöveges fejléc törlése,
5. Visszavonás/Újra egyenlő szélességű pár,
6. Derítőfény-csúszka elrendezése (címke a csúszka fölött).

Az `EditorPanel`-t önállóan, a `PicasaPy 1.0` modulon át töltjük be —
a `test_editor_look.py` / `test_qml_editor_panel.py` mintáját követve.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

# #496: az 1. fül tartalma az `EditorPanel.qml`-ből az
# `EditorTabCommonFixes.qml`-be került (a fájl a 800 soros korlát fölé nőtt).
# A forrás-szöveges ellenőrzések ezért MINDKÉT fájlt nézik — a szerződés
# (sorrend, feliratok, hiányzó csempék) változatlan, csak a hely más.
_QML_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
)
_QML_SOURCE = "\n".join(
    (_QML_DIR / name).read_text(encoding="utf-8")
    for name in ("EditorPanel.qml", "EditorTabCommonFixes.qml")
)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _make_panel(engine, active_tab=0):
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )


class TestCommonFixesHeaderRemoved:
    """#405 4. pont: az eredetiben a fül alatt NINCS "Gyakori javítások"
    szöveges fejléc — a csempék rögtön kezdődnek."""

    def test_no_common_fixes_header_text_in_tools_column(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=0)
        qt_app.processEvents()
        tools = panel.findChild(QObject, "toolsColumn")
        assert tools is not None
        # a korábbi fejléc egy külön Rectangle+Text volt "Common Fixes"
        # szöveggel — az eltűnését a forrásban ellenőrizzük (a fordított
        # szöveg futásidőben angolul jelenne meg, forrás-szinten stabilabb)
        assert 'text: qsTr("Common Fixes")' not in _QML_SOURCE


class TestUndoRedoEqualWidth:
    """#405 5. pont: a Visszavonás/Újra egymás mellett, EGYENLŐ
    szélességű párként (nem egy kitöltő + egy keskeny gomb)."""

    def test_undo_and_redo_share_the_row_equally(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, active_tab=0)
        qt_app.processEvents()
        undo = panel.findChild(QObject, "editUndoButton")
        redo = panel.findChild(QObject, "editRedoButton")
        assert undo is not None and redo is not None
        assert undo.property("width") == pytest.approx(redo.property("width"), abs=1)


class TestFillLightLabelAboveSlider:
    """#405 6. pont: a Derítőfény ("Fill Light") címke a csúszka FÖLÖTT,
    kompakt — a forrássorrend (Label majd PicasaSlider) adja ezt."""

    def test_fill_light_label_precedes_slider_in_source(self):
        label_pos = _QML_SOURCE.index('text: qsTr("Fill Light")')
        slider_pos = _QML_SOURCE.index('id: fixesFillSlider')
        assert label_pos < slider_pos
