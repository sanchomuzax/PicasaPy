"""#4697 — az F5 a látható mappát és a keresési eredményeket frissíti."""

from __future__ import annotations

import shutil
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest


def _wait_until(qt_app, predicate, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if predicate():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(predicate())


def _search(field: QObject, query: str, qt_app) -> None:
    field.setProperty("text", query)
    QMetaObject.invokeMethod(
        field, "textEdited", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _photo_names(controller) -> set[str]:
    return {photo.name for photo in controller.photos.photos}


def _focus_library_view(window, qt_app) -> None:
    folder_list = window.findChild(QObject, "folderListView")
    assert folder_list is not None and folder_list.isVisible()
    folder_list.forceActiveFocus()
    qt_app.processEvents()
    assert window.property("_szovegmezoneVanFokusz") is False


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_f5_refreshes_the_visible_folder_and_search_state(
    qml_app, qt_app, height_delta
):
    window, controller, _engine = qml_app
    window.setHeight(window.height() + height_delta)
    window.show()
    window.requestActivate()

    field = window.findChild(QObject, "searchField")
    assert field is not None
    folder = Path(controller.photos.photos[0].folder_path)
    removed_path = folder / "b.jpg"

    _search(field, "b", qt_app)
    assert controller.searchResultCount == 1
    assert "b.jpg" in _photo_names(controller)
    _focus_library_view(window, qt_app)
    shortcut = window.findChild(QObject, "refreshCurrentFolderShortcut")
    assert shortcut is not None and shortcut.property("enabled") is True

    # A lemezről eltűnt fájl és a kereső eredményszáma is az F5 után
    # frissüljön; a vezérlő csak a látható mappát olvassa újra.
    removed_path.unlink()
    QTest.keyClick(window, Qt.Key.Key_F5)
    qt_app.processEvents()
    assert _wait_until(qt_app, lambda: controller.searchResultCount == 0), (
        "az F5 nem frissítette a keresést a lemezről törölt fájl után"
    )
    assert "b.jpg" not in _photo_names(controller)

    source_path = folder / "a.jpg"
    new_path = folder / "f5probe.jpg"
    shutil.copyfile(source_path, new_path)
    _search(field, "f5probe", qt_app)
    assert controller.searchResultCount == 0
    _focus_library_view(window, qt_app)

    # Valódi billentyűleütés, nem a Shortcut.activated jelének kibocsátása.
    QTest.keyClick(window, Qt.Key.Key_F5)
    qt_app.processEvents()
    assert _wait_until(
        qt_app,
        lambda: controller.searchResultCount == 1
        and "f5probe.jpg" in _photo_names(controller),
    ), "az F5 nem vette fel a lemezről megjelent fájlt és frissítette a keresést"
