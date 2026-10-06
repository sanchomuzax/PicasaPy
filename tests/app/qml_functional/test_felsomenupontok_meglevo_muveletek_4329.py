"""#4329: a felső menüsor és a Ctrl+E/Ctrl+H a meglévő műveleteket hívja."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app.faces_helper import FacesHelper
from picasapy.ini import load_document


_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(qt_app, item) -> None:
    assert item is not None, "a kattintandó felületi elem hiányzik"
    assert item.isEnabled(), f"{item.objectName()}: a művelet le van tiltva"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()}: nincs kattintható mérete"
    )
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _objektum(window, nev):
    gyokerek = [window]
    menu_bar = window.property("menuBar")
    if menu_bar is not None:
        gyokerek.append(menu_bar)
    for gyoker in gyokerek:
        if hasattr(gyoker, "findChild"):
            elem = gyoker.findChild(QObject, nev)
            if elem is not None:
                return elem
    return None


def _nyisd_meg_felso_menut(qt_app, window, menu_nev, elem_nev):
    menu_feliratok = {
        "file": {"&File", "&Fájl"},
        "view": {"&View", "&Nézet"},
        "picture": {"&Picture", "&Kép"},
    }[menu_nev]
    menu_bar = window.property("menuBar")
    menu = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if item.property("title") in menu_feliratok
        ),
        None,
    )
    assert menu is not None, f"a felső {menu_nev} menü nem található"
    fejléc = next(
        (
            item
            for item in menu_bar.findChildren(QObject)
            if "MenuBarItem" in item.metaObject().className()
            and item.property("text") in menu_feliratok
        ),
        None,
    )
    assert fejléc is not None, f"a felső {menu_nev} menü fejléce nem található"
    _kattints(qt_app, fejléc)

    assert _varj(
        qt_app,
        lambda: menu.property("opened") is True
        and _objektum(window, elem_nev) is not None
        and _objektum(window, elem_nev).property("visible") is True,
    ), f"a {elem_nev} menüpont nem jelent meg a megnyitott menüben"
    # A menüpontot a teljes QML-fa tartja életben; a Menu.findChild a
    # QtQuick Controls popup-delegáltját adná vissza, ami a popup
    # bezárásakor megszűnik.
    item = _objektum(window, elem_nev)
    return menu_bar, menu, fejléc, item


def _magassag(window, offset: int) -> None:
    window.setHeight(window.height() + offset)


def _kijeloles(window, qt_app, rows) -> None:
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0] if rows else -1)
    qt_app.processEvents()


@pytest.fixture
def qml_app_small_pictures(qt_app, tmp_path, monkeypatch):
    from picasapy.app import small_picture_filter
    from support.jpeg_factory import make_jpeg

    # Ez a próba az eredeti alapértéket méri: a közös fixture kikapcsolását visszavonjuk.
    monkeypatch.setattr(small_picture_filter, "DEFAULT_SHOW_ONLY_BIG_IMAGES", True)
    from tests.app.qml_functional.conftest import _build_qml_app

    def keszits_kepeket(lib):
        make_jpeg(lib / "big.jpg", size=(400, 300))
        make_jpeg(lib / "small.jpg", size=(100, 100))

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=keszits_kepeket,
        show_only_big_images=None,
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_file_email_kattintas_a_meglevo_kuldesi_utvonalat_hivja(
    qml_app_email, qt_app, height_offset
):
    window, controller, engine = qml_app_email
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "file", "menuFileEmail"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "emailChoiceDialog") is not None
            and _objektum(window, "emailChoiceDialog").property("visible")
        ),
    ), "a Fájl ▸ E-Mail nem jutott el a meglévő e-mail választóig"
    dialog = _objektum(window, "emailChoiceDialog")
    attachments = list(dialog.property("attachmentPaths"))
    assert len(attachments) == 1
    assert Path(attachments[0]).name == Path(
        controller.photos.filePathAt(0)
    ).name


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_nezet_edit_view_kattintas_megnyitja_a_kijelolt_kepeket(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewEditView"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Nézet ▸ Edit View nem nyitotta meg a kijelölt képet"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_nezet_small_pictures_kattintas_szur_es_perzisztens(
    qml_app_small_pictures, qt_app, height_offset
):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController

    window, controller, _engine = qml_app_small_pictures
    _magassag(window, height_offset)

    def lathato_nevek():
        return {photo.name for photo in controller.photos.photos}

    assert controller.showOnlyBigImages is True
    assert lathato_nevek() == {"big.jpg"}

    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewThumbnailsOnly"
    )
    assert item.property("checkable") is True
    assert item.property("enabled") is True
    assert item.property("placeholder") is False
    assert item.property("checked") is False
    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.showOnlyBigImages is False)
    assert _varj(qt_app, lambda: lathato_nevek() == {"big.jpg", "small.jpg"})

    controller._get_settings().sync()
    uj_beallitas = QSettings(
        controller._get_settings().fileName(), QSettings.Format.IniFormat
    )
    uj_vezerlo = AppController(
        controller._db_path,
        tuple(controller._roots),
        controller._provider,
        settings=uj_beallitas,
    )
    assert uj_vezerlo.showOnlyBigImages is False
    uj_vezerlo.shutdown()
    assert uj_vezerlo.waitForBackgroundWorkers(30.0)
    uj_vezerlo.deleteLater()
    qt_app.processEvents()

    _menu_bar, _menu, _fejlec, item = _nyisd_meg_felso_menut(
        qt_app, window, "view", "menuViewThumbnailsOnly"
    )
    assert item.property("checked") is True
    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.showOnlyBigImages is True)
    assert _varj(qt_app, lambda: lathato_nevek() == {"big.jpg"})


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_view_and_edit_kattintas_megnyitja_a_kijelolt_kepeket(
    qml_app, qt_app, height_offset
):
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureViewAndEdit"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Kép ▸ View and Edit nem nyitotta meg a kijelölt képet"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_unhide_kattintas_csak_a_rejtett_kijelolteket_jeleniti_meg(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    controller.setShowHidden(True)
    controller.toggleHiddenRows([0])
    qt_app.processEvents()
    assert controller.photos.itemAt(0)["hidden"] is True
    assert controller.photos.itemAt(1)["hidden"] is False
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureUnhide"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0, 1])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    assert _varj(qt_app, lambda: controller.photos.itemAt(0)["hidden"] is False)
    assert controller.photos.itemAt(1)["hidden"] is False
    selected = window.property("selectedIndexes")
    if hasattr(selected, "toVariant"):
        selected = selected.toVariant()
    assert list(selected or []) == []


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_kep_reset_faces_kattintas_a_kijelolt_kepek_meglevo_kezelot_hivja(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    first = tmp_path / "kepek" / "a.jpg"
    other = tmp_path / "kepek" / "b.jpg"
    helper = FacesHelper()
    assert helper.addFace(str(first), 0.1, 0.2, 0.4, 0.6, "Ada")
    assert helper.addFace(str(other), 0.2, 0.3, 0.5, 0.7, "Bela")
    _menu_bar, _menu, _fejléc, item = _nyisd_meg_felso_menut(
        qt_app, window, "picture", "menuPictureResetFaces"
    )
    assert item.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: item.property("enabled") is True)

    _kattints(qt_app, item)

    first_section = load_document(first.parent / ".picasa.ini").section(first.name)
    other_section = load_document(other.parent / ".picasa.ini").section(other.name)
    assert first_section is None or first_section.get("faces") is None
    assert other_section is not None and other_section.get("faces")


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_ctrl_e_billentyu_a_meglevo_kuldesi_utvonalat_hivja(
    qml_app_email, qt_app, height_offset
):
    window, _controller, _engine = qml_app_email
    _magassag(window, height_offset)
    shortcut = _objektum(window, "emailShortcut")
    assert shortcut is not None
    assert shortcut.property("enabled") is False
    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: shortcut.property("enabled") is True)

    QTest.keyClick(window, Qt.Key.Key_E, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "emailChoiceDialog") is not None
            and _objektum(window, "emailChoiceDialog").property("visible")
        ),
    ), "a Ctrl+E nem jutott el a meglévő e-mail választóig"


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_ctrl_h_billentyu_a_talka_megtartasi_muveletet_hivja(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    shortcut = _objektum(window, "trayKeepSelectionShortcut")
    assert shortcut is not None
    assert shortcut.property("enabled") is False
    QTest.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    assert controller.heldCount == 0

    _kijeloles(window, qt_app, [0])
    assert _varj(qt_app, lambda: shortcut.property("enabled") is True)
    QTest.keyClick(window, Qt.Key.Key_H, Qt.KeyboardModifier.ControlModifier)

    assert _varj(qt_app, lambda: controller.heldCount == 1), (
        "a Ctrl+H nem rögzítette a kijelölt képet a képtálcán"
    )
    assert list(controller.heldPaths) == [controller.photos.filePathAt(0)]
