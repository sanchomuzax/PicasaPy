"""QML-funkcionális tesztek: a szerkesztő bal paneljének Picasa-hű
kinézete (#405) — a felhasználói screenshot-összevetés 6 pontja:

1. kép-előnézetes eszköz-csempék a "Gyakori javítások" fülön,
2. panel szélessége/aránya,
3. (fül-ikonok — már lefedve a test_editor_look.py `TestIconTabs`-jában),
4. a "Gyakori javítások" szöveges fejléc törlése,
5. Visszavonás/Újra egyenlő szélességű pár,
6. Derítőfény-csúszka elrendezése (címke a csúszka fölött).

Az `EditorPanel`-t önállóan, a `PicasaPy 1.0` modulon át töltjük be —
a `test_editor_look.py` / `test_qml_editor_panel.py` mintáját követve.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

_QML_SOURCE = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "EditorPanel.qml"
).read_text(encoding="utf-8")


class _FakeEditController(QObject):
    """Csak a bélyegkép-URL-hez szükséges felület: `previewSource`."""

    def __init__(self, preview_source="", parent=None):
        super().__init__(parent)
        self._preview_source = preview_source

    @Property(str)
    def previewSource(self):
        return self._preview_source


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


def _make_panel(engine, fake_controller=None, active_tab=0):
    if fake_controller is not None:
        engine.rootContext().setContextProperty("editController", fake_controller)
        _KEEPALIVE.append(fake_controller)
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


class TestToolTilesGetImagePreviews:
    """#405 1. pont (KIEMELT): a "Gyakori javítások" fül minden csempéje
    kép-előnézetes — effekt-előnézet, ahol van tényleges hatás
    (Vörösszem/Jó napom van/Automatikus kontraszt/Automatikus szín), sima
    fotó-miniatűr az interaktív eszközöknél (Vágás/Kiegyenesítés/
    Retusálás/Szöveg)."""

    EFFECT_PREVIEW_TILES = {
        "editToolRedeye": "redeye",
        "editToolEnhance": "enhance",
        "editToolAutolight": "autolight",
        "editToolAutocolor": "autocolor",
    }
    PLAIN_PREVIEW_TILES = ("editToolCrop", "editToolTilt", "editToolRetouch", "editToolText")

    def test_no_controller_means_empty_thumb_source(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        for name in (*self.EFFECT_PREVIEW_TILES, *self.PLAIN_PREVIEW_TILES):
            tile = panel.findChild(QObject, name)
            assert tile.property("thumbSource") == "", name

    def test_effect_tiles_get_effectthumb_url(self, qml_engine, qt_app):
        fake = _FakeEditController(preview_source="image://editpreview/7?rev=3")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=0)
        qt_app.processEvents()
        for object_name, effect in self.EFFECT_PREVIEW_TILES.items():
            tile = panel.findChild(QObject, object_name)
            assert tile.property("thumbSource") == f"image://effectthumb/7/{effect}", (
                object_name
            )

    def test_interactive_tool_tiles_get_plain_thumb_url(self, qml_engine, qt_app):
        fake = _FakeEditController(preview_source="image://editpreview/7?rev=3")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=0)
        qt_app.processEvents()
        for object_name in self.PLAIN_PREVIEW_TILES:
            tile = panel.findChild(QObject, object_name)
            assert tile.property("thumbSource") == "image://thumbs/7", object_name

    def test_tool_tile_thumb_image_child_exists(self, qml_engine, qt_app):
        """A csempe kép-előnézet-gyermeke (objectName + "Thumb") megvan —
        a PanelButton bélyegkép-mintáját követve."""
        fake = _FakeEditController(preview_source="image://editpreview/7?rev=3")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=0)
        qt_app.processEvents()
        thumb = panel.findChild(QObject, "editToolRedeyeThumb")
        assert thumb is not None


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
