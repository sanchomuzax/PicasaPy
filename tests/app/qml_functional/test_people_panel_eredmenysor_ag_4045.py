"""Az Emberek-panel ágválasztása az eredménysorok számát követi (#4045)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_ANNA_ID = "1111111111111111"
_BELA_ID = "2222222222222222"
_INI = (
    "[Contacts2]\n"
    f"{_ANNA_ID}=Anna;;\n"
    f"{_BELA_ID}=Béla;;\n"
    "[a.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID}\n"
    "[b.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID}\n"
    "[c.jpg]\n"
    f"faces=rect64(1e00280045006e00),{_ANNA_ID};"
    f"rect64(5000280075006e00),{_BELA_ID}\n"
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _walk_items(item):
    for child in item.childItems():
        yield child
        yield from _walk_items(child)


def _prepare_library(controller, qt_app, tmp_path):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    lib = tmp_path / "kepek"
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(lib / name, size=(120, 90))
    (lib / ".picasa.ini").write_text(_INI, encoding="utf-8")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    controller._reload_after_sync()
    assert wait_for_all_background_workers(30.0)
    for _ in range(5):
        qt_app.processEvents()
    return lib


def _grid_cell(window, row):
    for item in _walk_items(window.contentItem()):
        if item.objectName() != "thumbMouseArea" or not item.isVisible():
            continue
        cell = item.parentItem()
        if cell is not None and cell.property("index") == row:
            return item
    raise AssertionError(f"a(z) {row}. sor cellája nincs a rácson")


def _select(window, controller, qt_app, lib, photo_names):
    """Valódi képkattintások a rácson, a Ctrl-kattintással bővített kijelölés."""
    for index, name in enumerate(photo_names):
        row = controller.photos.rowOfPath(str(lib / name))
        assert row >= 0, f"{name} nincs a rácson"
        item = _grid_cell(window, row)
        center = item.mapToScene(item.boundingRect().center())
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.ControlModifier
            if index
            else Qt.KeyboardModifier.NoModifier,
            QPoint(round(center.x()), round(center.y())),
        )
        for _ in range(5):
            qt_app.processEvents()
    assert _child(window, "peoplePanel").property("selectionCount") == len(
        photo_names
    )


def _visible_rows(panel):
    return sorted(
        item.objectName().removeprefix("peoplePanelRow_")
        for item in _walk_items(panel)
        if item.objectName().startswith("peoplePanelRow_") and item.isVisible()
    )


@pytest.mark.parametrize(
    "height_delta",
    [-5, 0, 5],
    ids=["magassag-minusz5", "alap", "magassag-plusz5"],
)
@pytest.mark.parametrize(
    ("photo_names", "expected_header", "expected_people"),
    [
        (("a.jpg",), "In this photo:", ["Anna"]),
        (("c.jpg",), "People in these photos:", ["Anna", "Béla"]),
        (("a.jpg", "b.jpg"), "In this photo:", ["Anna"]),
        (("a.jpg", "c.jpg"), "People in these photos:", ["Anna", "Béla"]),
    ],
    ids=[
        "egy-kep-egy-szemely",
        "egy-kep-ket-szemely",
        "ket-kep-egy-szemely",
        "ket-kep-ket-szemely",
    ],
)
def test_header_branch_uses_people_result_rows(
    qml_app, qt_app, tmp_path, photo_names, expected_header, expected_people,
    height_delta,
):
    from picasapy.app.worker_thread import wait_for_all_background_workers

    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    qt_app.processEvents()
    lib = _prepare_library(controller, qt_app, tmp_path)
    assert wait_for_all_background_workers(30.0)

    QMetaObject.invokeMethod(
        _child(window, "menuViewPeople"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()
    _select(window, controller, qt_app, lib, photo_names)

    header = _child(window, "peoplePanelHeader")
    assert header.property("visible") is True
    assert header.property("text") == expected_header
    assert _visible_rows(_child(window, "peoplePanel")) == expected_people
