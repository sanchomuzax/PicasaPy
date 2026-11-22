"""A néző a szkennelés közbeni modell-beszúrás után is ugyanahhoz a képhez tér vissza (#7356)."""

from __future__ import annotations

from pathlib import Path
from threading import Event

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


def _bejark(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _bejark(child)


def _kattinthato_kep(window, row: int) -> QQuickItem:
    for item in _bejark(window.contentItem()):
        if item.objectName() != "thumbMouseArea" or not item.isVisible():
            continue
        cell = item.parentItem()
        if cell is not None and int(cell.property("index")) == row:
            return item
    raise AssertionError(f"a(z) {row}. képsor látható bélyegképe nem található")


def _duplakattint(window, qt_app, item: QQuickItem) -> None:
    kozep = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    pont = QPoint(round(kozep.x()), round(kozep.y()))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=pont)
    QTest.mouseDClick(window, Qt.MouseButton.LeftButton, pos=pont, delay=10)
    qt_app.processEvents()


def test_a_szkenneles_kozben_beszurt_kep_utan_azonos_kepre_ter_vissza(
    qml_app, qt_app, tmp_path, monkeypatch
):
    window, controller, _engine = qml_app
    window.show()
    assert var_feltetelre(qt_app, window.isExposed, 3.0), "a főablak nem jelent meg"

    target_row = 1
    target_path = Path(controller.photos.photos[target_row].folder_path) / controller.photos.photos[
        target_row
    ].name
    target_id = int(controller.photos.idAt(target_row))
    assert target_path.name == "b.jpg", "a próba két alapképet vár a mappában"

    original_sync = type(controller)._sync_tree
    scan_entered = Event()
    resume_scan = Event()

    def paused_sync(self, *args, **kwargs):
        scan_entered.set()
        if not resume_scan.wait(10.0):
            raise TimeoutError("a teszt nem engedte tovább a mappaszkennelést")
        return original_sync(self, *args, **kwargs)

    monkeypatch.setattr(type(controller), "_sync_tree", paused_sync)
    controller.rescan()

    try:
        assert var_feltetelre(qt_app, scan_entered.is_set, 5.0), (
            "a háttérszkenner nem jutott el a mappa beolvasásáig"
        )
        assert window.property("viewerOpen") is False
        _duplakattint(window, qt_app, _kattinthato_kep(window, target_row))

        assert var_feltetelre(
            qt_app, lambda: window.property("viewerOpen") is True, 3.0
        ), "a bélyegképre végzett valódi dupla kattintás nem nyitotta meg a nézőt"
        viewer = window.findChild(QQuickItem, "photoViewer")
        assert viewer is not None
        assert viewer.property("currentIndex") == target_row
        assert Path(controller.photos.photos[target_row].folder_path) / controller.photos.photos[
            target_row
        ].name == target_path

        # A scanner a feloldás után ezt a fájlt találja meg. Név szerinti
        # rendezésben az új sor a megnyitott b.jpg elé kerül, így a régi
        # sorszám már másik képet jelöl.
        make_jpeg(tmp_path / "kepek" / "0.jpg", size=(80, 60))
        resume_scan.set()

        assert var_feltetelre(
            qt_app,
            lambda: controller.photos.rowCount() == 3
            and any(
                (Path(photo.folder_path) / photo.name) == tmp_path / "kepek" / "0.jpg"
                for photo in controller.photos.photos
            ),
            10.0,
        ), "a szkennelés nem vette fel az újonnan érkezett képet"
        remapped_row = controller.photos.rowOfId(target_id)
        assert remapped_row == 2, "a reprodukcióban az új kép nem került a cél elé"
        assert viewer.property("currentIndex") == remapped_row, (
            "a néző sorindexe a modell frissítése után a régi képen maradt"
        )

        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert var_feltetelre(
            qt_app, lambda: window.property("viewerOpen") is False, 3.0
        ), "az Escape nem lépett vissza a bélyegképekhez"
        assert window.property("selectedIndex") == remapped_row, (
            "visszalépés után nem a nézőben utoljára mutatott kép van kijelölve"
        )
        assert window.property("selectedIndexes").toVariant() == [remapped_row]
        assert (
            Path(controller.photos.photos[window.property("selectedIndex")].folder_path)
            / controller.photos.photos[window.property("selectedIndex")].name
        ) == target_path, "visszalépés után másik kép lett kijelölve"
        target_cell = _kattinthato_kep(window, remapped_row)
        center = target_cell.mapToItem(
            window.findChild(QQuickItem, "photoGrid"),
            QPointF(target_cell.width() / 2, target_cell.height() / 2),
        )
        grid = window.findChild(QQuickItem, "photoGrid")
        assert target_cell.isVisible() and 0 <= center.y() <= grid.height(), (
            "a kijelölt kép bélyegképe nem látható a visszatérő rácson"
        )
        assert target_cell.parentItem().property("selected") is True, (
            "a visszatérő rácson a nézett kép bélyegképe nincs kijelölve"
        )
    finally:
        resume_scan.set()
