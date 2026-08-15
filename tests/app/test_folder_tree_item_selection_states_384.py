"""QML-teszt: a Mappakezelő fájának (`FolderTreeItem.qml`) hover ≠
kijelölés állapota (#384) — a `manager` property egy sima JS-objektum
(a komponens `property var`-ként fogadja, nincs QObject-kényszer), ezért
önálló komponens-betöltéssel, valódi fa/controller nélkül tesztelhető
(a `test_qml_edits_mark.py` mintája)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QUrl, Signal, Slot
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []
_SELECTION_ACTIVE = "#25648b"  # constants.ui alist_selcolor_win
_SELECTION_HOVER = "#83a7bd"  # constants.ui alist_hicolor_win (Theme.selectionBlue)


class _StubManager(QObject):
    """A FolderManagerDialog felszínének minimális tükre — a kijelöléshez
    (`selectedPath`) és az állapot-jelvényhez szükséges rész.

    #718: a `stateGlyph` egy RÉGI felszín; a `FolderTreeItem.qml` ma
    `stateFor()`-t és `facesExcludedFor()`-t hív (`FolderStateBadge`). Ezek
    hiánya miatt a QML minden sor kirajzolásakor „Property … is not a
    function" TypeError-t dobott — a teszt mégis zöld volt, mert a
    QML-szkripthiba-őr eddig nem futott a `tests/app/` alatt. A csonka
    stub tehát nem a valódi felszínt mérte. Az alapértékek a
    `FolderManagerDialog.qml` üres állapotát tükrözik: nincs figyelt
    mappa és nincs arc-kizárás."""

    selectedPathChanged = Signal()

    def __init__(self, selected_path=""):
        super().__init__()
        self._selected_path = selected_path

    def _get_selected_path(self):
        return self._selected_path

    def _set_selected_path(self, value):
        self._selected_path = value
        self.selectedPathChanged.emit()

    selectedPath = Property(str, _get_selected_path, _set_selected_path,
                             notify=selectedPathChanged)

    @Slot(str, result=str)
    def stateGlyph(self, _path):
        return ""

    @Slot(str, result=str)
    def stateFor(self, _path):
        """Nincs figyelt mappa — a valódi dialógus ilyenkor „none"-t ad."""
        return "none"

    @Slot(str, result=bool)
    def facesExcludedFor(self, _path):
        """Nincs arc-kizárás a próbában."""
        return False


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _make_row(qml_engine, path="/kepek/balaton", selected_path=""):
    import picasapy.app.application as app_module

    comp = QQmlComponent(
        qml_engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderTreeItem.qml")
        ),
    )
    row = comp.createWithInitialProperties(
        {"path": path, "name": "balaton", "hasChildren": False, "depth": 0}
    )
    assert comp.errors() == [], [e.toString() for e in comp.errors()]
    assert row is not None
    manager = _StubManager(selected_path)
    row.setProperty("manager", manager)
    QQmlEngine.setObjectOwnership(row, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(comp)
    _KEEPALIVE.append(row)
    _KEEPALIVE.append(manager)
    return row, manager


class TestFolderTreeRowTrueSelectionColor:
    def test_not_selected_row_is_transparent(self, qml_engine):
        row, _manager = _make_row(qml_engine, selected_path="/kepek/mas")
        rect = row.findChild(QObject, "folderTreeRow:/kepek/balaton")
        assert rect is not None
        assert rect.property("color").alpha() == 0

    def test_selected_row_uses_the_dark_active_blue(self, qml_engine):
        row, _manager = _make_row(qml_engine, selected_path="/kepek/balaton")
        rect = row.findChild(QObject, "folderTreeRow:/kepek/balaton")
        assert rect.property("color").name() == _SELECTION_ACTIVE
        # ez a #384 lényege: a régi kód a hover-tónust adta a
        # kijelölésre is — a kettő mostantól különbözik
        assert rect.property("color").name() != _SELECTION_HOVER

    def test_selection_follows_manager_property_change(self, qml_engine, qt_app):
        row, manager = _make_row(qml_engine, selected_path="")
        rect = row.findChild(QObject, "folderTreeRow:/kepek/balaton")
        assert rect.property("color").alpha() == 0
        manager.selectedPath = "/kepek/balaton"
        qt_app.processEvents()
        assert rect.property("color").name() == _SELECTION_ACTIVE


class TestFolderTreeIndent:
    def test_indent_step_is_17px_per_level(self, qml_engine):
        # constants.ui alist_indent = 17 (korábban 16 volt, mérés nélkül)
        import picasapy.app.application as app_module

        source = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "FolderTreeItem.qml"
        ).read_text(encoding="utf-8")
        assert "root.depth * 17" in source
        assert "root.depth * 16" not in source


class TestFolderTreeHoverToneWiringInSource:
    """A hover (MouseArea.containsMouse) headless tesztben valódi
    egérmozgás nélkül nem szimulálható megbízhatóan — forráskód-
    vizsgálattal ellenőrizzük, hogy a hover a régi (`Theme.selectionBlue`)
    tónust kapja, a kijelölés pedig a hitelesebb, helyi
    `__selectionActiveColor`-t (ld. `test_editor_look.py` mintája)."""

    def test_hover_uses_selection_blue_not_the_active_color(self, qml_engine):
        import picasapy.app.application as app_module

        source = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "FolderTreeItem.qml"
        ).read_text(encoding="utf-8")
        assert "rowMouse.containsMouse ? Theme.selectionBlue" in source
        assert "hoverEnabled: true" in source
