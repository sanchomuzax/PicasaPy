"""Recently Updated album QML-funkcionális és kattintásos tesztek (#6851)."""

from __future__ import annotations

import time
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg


def _varj(feltetel, qt_app, nev="feltétel", timeout_s=10.0):
    start = time.time()
    while time.time() - start < timeout_s:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"határidőn belül nem teljesült: {nev}")


def _katt(window, elem, gomb=Qt.LeftButton):
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        gomb,
        Qt.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def test_recently_updated_row_and_context_menu(qml_app, qt_app, tmp_path):
    window, controller, _ = qml_app
    root = tmp_path / "kepek"
    make_jpeg(root / "kep1.jpg")
    make_jpeg(root / "kep2.jpg")
    controller.resyncFolder(str(root))
    qt_app.processEvents()

    # 1. A sor létezik és látható
    row = window.findChild(QObject, "recentlyUpdatedItem")
    assert row is not None, "recentlyUpdatedItem nem található"
    assert row.property("visible") is True

    # 2. Ikon és felirat
    icon = window.findChild(QObject, "recentlyUpdatedRowIcon")
    assert icon is not None, "recentlyUpdatedRowIcon nem található"
    label = window.findChild(QObject, "recentlyUpdatedLabel")
    assert label is not None, "recentlyUpdatedLabel nem található"
    assert "Recently Updated" in label.property("text")

    # 3. Jobbklikk -> helyi menü és tételei
    _katt(window, row, Qt.RightButton)
    menu = window.findChild(QObject, "recentlyUpdatedContextMenu")
    _varj(lambda: menu is not None and menu.property("visible"), qt_app, "recentlyUpdatedContextMenu megjelenése")

    edit_item = window.findChild(QObject, "recentMenuEditDescription")
    assert edit_item is not None and edit_item.property("enabled") is True

    select_all = window.findChild(QObject, "recentMenuSelectAll")
    assert select_all is not None

    clear_sel = window.findChild(QObject, "recentMenuClearSelection")
    assert clear_sel is not None

    invert_sel = window.findChild(QObject, "recentMenuInvertSelection")
    assert invert_sel is not None

    refresh_thumb = window.findChild(QObject, "recentMenuRefreshThumbnails")
    assert refresh_thumb is not None

    sort_album = window.findChild(QObject, "recentMenuSortAlbumBy")
    assert sort_album is not None

    # Delete Album: szürke (letiltott)
    delete_item = window.findChild(QObject, "recentMenuDelete")
    assert delete_item is not None
    assert delete_item.property("enabled") is False

    upload_item = window.findChild(QObject, "recentMenuUploadToGooglePhotos")
    assert upload_item is not None

    export_html = window.findChild(QObject, "recentMenuExportAsHtml")
    assert export_html is not None

    add_tags = window.findChild(QObject, "recentMenuAddNameTags")
    assert add_tags is not None

    menu.close()
    qt_app.processEvents()


@pytest.mark.parametrize("delta_h", [-5, 0, 5])
def test_recently_updated_left_click_navigation(qml_app, qt_app, delta_h):
    window, controller, _ = qml_app
    orig_h = window.height()
    window.setHeight(orig_h + delta_h)
    qt_app.processEvents()

    row = window.findChild(QObject, "recentlyUpdatedItem")
    assert row is not None
    _katt(window, row, Qt.LeftButton)
    qt_app.processEvents()

    _varj(lambda: controller.viewModeName == "recent_album", qt_app, "átváltás recent_album nézetre")
    assert controller.currentAlbumToken == "]updated"
    assert len(controller.photos.photos) >= 2
    # Legújabb rekord áll elöl (b.jpg a.jpg után jött létre a fixture-ben)
    names = [p.name for p in controller.photos.photos]
    assert "b.jpg" in names
    assert "a.jpg" in names
    assert names.index("b.jpg") < names.index("a.jpg")
