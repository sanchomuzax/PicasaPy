"""QML-funkcionális teszt: a mappalista/albumlista HÁROM kék állapota
(#384, constants.ui) — hover (`alist_hicolor_win`, #83a7bd) ≠ valódi
kijelölés (`alist_selcolor_win`, #25648B).

A `FolderPane.qml`-t a #320-as bekötési teszt mintája szerint önálló
komponensként töltjük be (controller nélkül, VALÓS `FolderListModel`-lel).
A sor-delegate-ek `ListView`/`Repeater` termékek — a `findChild` NEM látja
őket (MEMORY 2026-07-31), ezért a vizuális fát járjuk be, és a színt
közvetlenül a Rectangle `color`/property-jén ellenőrizzük (nem a `visible`
öröklött állapotán, ami a MEMORY 2026-07-31 "Qt-csapda" szerint
megbízhatatlan). A hover-viselkedést (MouseArea.containsMouse, ami valódi
mozgás nélkül nem állítható elő headless tesztben) a `test_editor_look.py`
mintáját követve forráskód-vizsgálattal ellenőrizzük."""

from __future__ import annotations

from types import SimpleNamespace

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []
_SELECTION_ACTIVE = "#25648b"  # constants.ui alist_selcolor_win
_SELECTION_HOVER = "#83a7bd"  # constants.ui alist_hicolor_win (Theme.panelSelection)


@pytest.fixture
def qml_source():
    import picasapy.app.application as app_module

    return app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml"


@pytest.fixture
def pane(qt_app, qml_source):
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", None)
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(qml_source)))
    folders_model = FolderListModel()
    obj = component.createWithInitialProperties({"foldersModel": folders_model})
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    folders_model.setParent(obj)
    # a ListView csak a TÉNYLEGES viewport méretén belül példányosít
    # delegate-eket — 0x0 geometriánál a mappasorok sosem jönnének létre
    obj.setProperty("width", 300)
    obj.setProperty("height", 600)
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([engine, component, obj, folders_model])
    return obj, folders_model


def _walk_visual_tree(item):
    for child in item.childItems():
        yield child
        yield from _walk_visual_tree(child)


def _folder_row(pane_obj, path):
    folder_list = pane_obj.findChild(QObject, "folderListView")
    content = folder_list.property("contentItem")
    matches = [
        item
        for item in _walk_visual_tree(content)
        if item.property("kind") == "folder" and item.property("path") == path
    ]
    assert matches, f"nincs mappasor ehhez az útvonalhoz: {path}"
    return matches[0]


class TestFolderRowTrueSelectionColor:
    """A ténylegesen kijelölt mappasor a HITELES, sötétebb kéket kapja —
    nem a korábban (tévesen) erre használt hover-tónust."""

    def _feed_one_folder(self, folders_model, path="/kepek/balaton"):
        group = SimpleNamespace(
            folder_name="balaton", folder_path=path, photos=[object()]
        )
        folders_model.load_matches([group])

    def test_unselected_folder_row_is_transparent(self, pane, qt_app):
        pane_obj, model = pane
        self._feed_one_folder(model)
        qt_app.processEvents()
        row = _folder_row(pane_obj, "/kepek/balaton")
        assert row.property("color").name() == "#000000"

    def test_selected_folder_row_uses_the_dark_active_blue(self, pane, qt_app):
        pane_obj, model = pane
        self._feed_one_folder(model)
        pane_obj.setProperty("selectedPath", "/kepek/balaton")
        qt_app.processEvents()
        row = _folder_row(pane_obj, "/kepek/balaton")
        assert row.property("color").name() == _SELECTION_ACTIVE
        # a hitelesebb, sötétebb szín NEM ugyanaz, mint a hover-tónus —
        # ez a bug lényege, amit a #384 javít
        assert row.property("color").name() != _SELECTION_HOVER

    def test_selecting_an_album_clears_the_folder_row_highlight(self, pane, qt_app):
        # #9: album-nézetben a mappa-kijelölés szűnjön meg
        pane_obj, model = pane
        self._feed_one_folder(model)
        pane_obj.setProperty("selectedPath", "/kepek/balaton")
        pane_obj.setProperty("selectedAlbumToken", "album-1")
        qt_app.processEvents()
        row = _folder_row(pane_obj, "/kepek/balaton")
        assert row.property("color").name() == "#000000"


class TestStarredAndAlbumTrueSelectionColor:
    def test_starred_row_uses_the_dark_active_blue_when_active(self, pane, qt_app):
        pane_obj, _model = pane
        pane_obj.setProperty("starredActive", True)
        qt_app.processEvents()
        starred = pane_obj.findChild(QObject, "starredItem")
        assert starred.property("color").name() == _SELECTION_ACTIVE

    def test_starred_row_transparent_when_inactive(self, pane, qt_app):
        pane_obj, _model = pane
        pane_obj.setProperty("starredActive", False)
        qt_app.processEvents()
        starred = pane_obj.findChild(QObject, "starredItem")
        assert starred.property("color").name() == "#000000"

    def test_album_row_uses_the_dark_active_blue_when_selected(self, pane, qt_app):
        # az albumsor a Repeater terméke — findChild-dal NEM érhető el
        # (MEMORY 2026-07-31), a vizuális fát kell bejárni
        pane_obj, _model = pane
        pane_obj.setProperty(
            "albumsModel", [{"token": "album-1", "name": "Nyaralás", "count": 3}]
        )
        pane_obj.setProperty("selectedAlbumToken", "album-1")
        qt_app.processEvents()
        matches = [
            item
            for item in _walk_visual_tree(pane_obj)
            if item.objectName() == "albumItem_album-1"
        ]
        assert matches, "albumItem_album-1 nem található a fában"
        assert matches[0].property("color").name() == _SELECTION_ACTIVE


class TestHoverToneWiringInSource:
    """A hover-állapot (MouseArea.containsMouse) headless tesztben valódi
    egérmozgás nélkül nem állítható elő megbízhatóan — a `test_editor_
    look.py` mintáját követve a kötést forráskódon ellenőrizzük: a hover
    a régi (`Theme.panelSelection`) tónust kapja, a kijelölés viszont a
    hitelesebb, helyi `__selectionActiveColor`-t, a kettő SOSEM
    ugyanaz a kifejezés."""

    @pytest.fixture
    def source_text(self, qml_source):
        return qml_source.read_text(encoding="utf-8")

    def test_starred_row_hover_uses_panel_selection(self, source_text):
        assert "starredMouse.containsMouse ? Theme.panelSelection" in source_text

    def test_album_row_hover_uses_panel_selection(self, source_text):
        assert "albumMouse.containsMouse ? Theme.panelSelection" in source_text

    def test_folder_row_hover_uses_panel_selection(self, source_text):
        assert "folderRowMouse.containsMouse ? Theme.panelSelection" in source_text

    def test_all_three_mouse_areas_enable_hover_tracking(self, source_text):
        assert source_text.count("hoverEnabled: true") >= 3
