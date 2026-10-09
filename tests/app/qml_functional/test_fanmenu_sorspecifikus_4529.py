"""A fanézet jobbklikkje a sor típusának megfelelő menüt nyitja (#4529)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QPointF, Qt
from PySide6.QtTest import QTest

from test_folder_pane_tree_view_702 import (
    _child,
    _settle,
    _var,
    _walk,
)

pytest_plugins = ("test_folder_pane_tree_view_702",)


def _fasor(pane, path: str):
    object_name = "hierRow:" + path
    return next(
        (item for item in _walk(pane) if item.objectName() == object_name),
        None,
    )


def _jobbklikk_sor(view, row) -> None:
    assert row is not None and row.isVisible() and row.height() > 0
    center = row.mapToScene(QPointF(row.width() / 2, row.height() / 2))
    assert 0 <= center.x() <= view.width()
    assert 0 <= center.y() <= view.height()
    QTest.mouseClick(
        view,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        center.toPoint(),
    )


@pytest.mark.parametrize("height", [795, 800, 805])
def test_a_kepes_es_a_koztes_fasor_sajat_menut_nyit(qt_app, render_pane, height):
    view, pane, hierarchy = render_pane(tree=True, height=height)
    hierarchy.expandAll()
    _settle(qt_app, pane)

    kepes_ut = "/mnt/photo/Videok"
    koztes_ut = "/mnt/photo/Kepek"
    adatok = {sor["path"]: sor for sor in hierarchy.rows}
    assert adatok[kepes_ut]["own"] > 0
    assert adatok[koztes_ut]["own"] == 0

    teljes = _child(pane, "folderContextMenu")
    szukitett = _child(pane, "hierFolderContextMenu")

    _jobbklikk_sor(view, _fasor(pane, kepes_ut))
    assert _var(
        qt_app,
        lambda: teljes.property("visible") or szukitett.property("visible"),
    ), "a képes fasor jobbklikkjére egyik menü sem nyílt ki"
    assert teljes.property("visible") is True, (
        "a képes fasor a teljes Folder menü helyett a HierFolder menüt nyitotta"
    )
    assert szukitett.property("visible") is False
    for item_name in (
        "folderMenuEditDescription",
        "folderMenuDeleteFolder",
        "folderMenuExportAsHtml",
    ):
        assert _child(teljes, item_name) is not None

    assert QMetaObject.invokeMethod(
        teljes, "close", Qt.ConnectionType.DirectConnection
    )
    assert _var(qt_app, lambda: not teljes.property("visible"))

    _jobbklikk_sor(view, _fasor(pane, koztes_ut))
    assert _var(
        qt_app,
        lambda: teljes.property("visible") or szukitett.property("visible"),
    ), "a köztes fasor jobbklikkjére egyik menü sem nyílt ki"
    assert szukitett.property("visible") is True, (
        "a köztes fasor nem a rövid HierFolder menüt nyitotta"
    )
    assert teljes.property("visible") is False
