"""A bal panel HIERARCHIKUS (fa) mappanézete KIRAJZOLVA — #702.

Miért kirajzolva: a fa lényege a VISELKEDÉS (mi látszik kinyitás előtt és
után), nem az, hogy egy property `true`-ra áll. A `visible` ráadásul
öröklődik — egy összecsukott ág gyermeksorára `visible === true` jöhet ki
akkor is, ha a szülője rejtett —, ezért itt a ténylegesen KIRAJZOLT sorok
halmazát nézzük. A `Repeater`/`ListView` delegáltjait a `findChild` nem
találja meg (nincs QObject-szülőjük, csak vizuális), így a vizuális fát
járjuk be, a `test_editor_panel_rendered_651.py` `_walk()` segédje szerint.

Bizonyíték a viselkedésre (docs/specs/ui-audit-mainwindow.md 1.4/1.7):
`Folder::ID_HIER_FOLDER_EXPAND` / `ID_HIER_FOLDER_COLLAPSE` — „Expand All"
/ „Collapse All" a `Picasa3i18n.dll` string-táblájából; a fa gyökere
`ViewRoot::All` = „My Computer".
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, QUrl
from PySide6.QtQuick import QQuickItem, QQuickView

from picasapy.app.folder_hierarchy_controller import FolderHierarchyController

_KEEPALIVE: list[object] = []

#: Több szintű mappakészlet — a lapos listából ez öt egyszintű sor, a
#: fából viszont szintenként bomlik ki.
_FOLDERS = [
    {"name": "space", "path": "/mnt/photo/Kepek/wallpapers/space", "count": 7},
    {"name": "LEGO", "path": "/mnt/photo/Kepek/wallpapers/LEGO", "count": 5},
    {"name": "wallpapers", "path": "/mnt/photo/Kepek/wallpapers", "count": 18},
    {"name": "AI", "path": "/mnt/photo/Kepek/AI", "count": 92},
    {"name": "Videok", "path": "/mnt/photo/Videok", "count": 3},
]

_QML = """
import QtQuick
import PicasaPy 1.0
Item {
    objectName: "hierRoot"
    FolderHierarchyView {
        id: hierView
        objectName: "folderHierarchyView"
        anchors.fill: parent
        hierarchy: folderHierarchyController
    }
}
"""


@pytest.fixture
def tree(qt_app):
    """(kirajzolt gyökér-elem, vezérlő) — a valós bekötés kicsinyített mása."""
    import picasapy.app.application as app_module
    from PySide6.QtQml import QQmlComponent

    controller = FolderHierarchyController()
    controller.setFolders(_FOLDERS)

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    view.engine().rootContext().setContextProperty(
        "folderHierarchyController", controller
    )
    view.setSource(QUrl())
    component = QQmlComponent(view.engine())
    component.setData(_QML.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(280, 600)
    root.setWidth(280)
    root.setHeight(600)
    _KEEPALIVE.extend((view, root, component, controller))
    view.show()
    qt_app.processEvents()
    yield root, controller
    view.hide()


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _rendered_paths(root: QQuickItem) -> set[str]:
    """A ténylegesen KIRAJZOLT mappasorok útvonalai.

    Nem a delegátum saját `visible` értékét nézzük (az öröklődik), hanem
    az `isVisible()`-t (a teljes szülőláncot figyelembe véve) és azt,
    hogy van-e valódi magassága.
    """
    prefix = "hierRow:"
    return {
        item.objectName()[len(prefix):]
        for item in _walk(root)
        if item.objectName().startswith(prefix)
        and item.isVisible()
        and item.height() > 0
    }


class TestATreeShowsOneLevelAtATime:
    """A fa nem a lapos lista más sorrendben: szinteket mutat."""

    def test_only_the_view_root_is_visible_at_first(self, tree, qt_app):
        root, _controller = tree

        assert _rendered_paths(root) == {""}, (
            "induláskor csak a nézet-gyökér (My Computer) sora látszik"
        )

    def test_expanding_the_root_reveals_only_its_direct_child(self, tree, qt_app):
        root, controller = tree

        controller.toggle("")
        qt_app.processEvents()

        paths = _rendered_paths(root)
        assert "/" in paths, f"a gyökér közvetlen gyermeke hiányzik: {sorted(paths)}"
        assert "/mnt" not in paths, (
            f"a fa az unokákat is kirajzolta — ez nem fa: {sorted(paths)}"
        )

    def test_each_expand_reveals_exactly_the_next_level(self, tree, qt_app):
        root, controller = tree

        for path in ("", "/", "/mnt", "/mnt/photo"):
            controller.toggle(path)
        qt_app.processEvents()

        paths = _rendered_paths(root)
        assert "/mnt/photo/Kepek" in paths
        assert "/mnt/photo/Videok" in paths
        assert "/mnt/photo/Kepek/AI" not in paths, (
            f"a Kepek ág csukva van, a gyermekei mégis látszanak: {sorted(paths)}"
        )


class TestTheTwoHierFolderCommands:
    """`Folder::ID_HIER_FOLDER_EXPAND` / `..._COLLAPSE` — a #702 két
    gazdátlan parancsa."""

    def test_expand_all_reveals_every_folder(self, tree, qt_app):
        root, controller = tree

        controller.expandAll()
        qt_app.processEvents()

        paths = _rendered_paths(root)
        for folder in _FOLDERS:
            assert folder["path"] in paths, (
                "az Expand All után hiányzik: " + folder["path"]
            )

    def test_collapse_all_leaves_only_the_view_root(self, tree, qt_app):
        root, controller = tree

        controller.expandAll()
        qt_app.processEvents()
        controller.collapseAll()
        qt_app.processEvents()

        assert _rendered_paths(root) == {""}


class TestTheSimplifiedTreeView:
    """`eMenuView::ID_VIEW_WATCHED` = „Simplified Tree View", a
    `SimplifiedHierarchy` beállításkulcs: az egygyermekes, fotó nélküli
    köztes szinteket összevonja."""

    def test_the_empty_chain_is_collapsed_into_one_row(self, tree, qt_app):
        root, controller = tree
        controller.setSimplified(True)

        controller.toggle("")
        qt_app.processEvents()

        paths = _rendered_paths(root)
        assert "/mnt/photo" in paths, (
            "egyszerűsített fában a gyökér alatt közvetlenül a legelső "
            f"elágazás áll: {sorted(paths)}"
        )
        assert "/mnt" not in paths, (
            f"a köztes, üres szintek nem lettek összevonva: {sorted(paths)}"
        )


class TestTheCountsAreAggregated:
    """A darabszám a fában az ÖSSZES leszármazott fotóját számolja
    (ui-audit 1.4: `Sajátgép (1 072)` = 227 + 842 + 3)."""

    def test_a_branch_counts_its_whole_subtree(self, tree, qt_app):
        _root, controller = tree

        controller.expandAll()
        rows = {row["path"]: row for row in controller.rows}

        assert rows["/mnt/photo/Kepek/wallpapers"]["count"] == 30
        assert rows["/mnt/photo/Kepek"]["count"] == 122
        assert rows[""]["count"] == 125


class TestSelection:
    """A sorra kattintás a mappát választja ki — ez a fa haszna."""

    def test_choosing_a_row_emits_the_path(self, tree, qt_app):
        root, controller = tree
        # `property("view")` itt nem járható: a QML-típusra nincs
        # Python-konverter — a névvel keresés viszont igen.
        view = root.findChild(QObject, "folderHierarchyView")
        assert view is not None
        seen: list[str] = []
        view.folderChosen.connect(seen.append)

        controller.expandAll()
        qt_app.processEvents()
        # QML-ben deklarált függvény — `QMetaObject.invokeMethod`-dal
        # hívható (a közvetlen Python-attribútumhívás nem oldja fel)
        QMetaObject.invokeMethod(
            view, "choose", Qt.ConnectionType.DirectConnection,
            Q_ARG("QVariant", "/mnt/photo/Kepek/AI"),
        )

        assert seen == ["/mnt/photo/Kepek/AI"]
