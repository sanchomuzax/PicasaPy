"""#7131: albumképek megerősítés nélküli képernyővédő-hozzáadása és tálcadátum."""

from pathlib import Path

import pytest
from PySide6.QtCore import QDate, QObject, Qt

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    almenu_megnyitasa,
    gyerek,
    jobbklikk_fotón,
    kattints,
    keres_vizualis_mindenablakban,
    varj,
)


def _ablakmagassag(window, qt_app, eltolás: int) -> None:
    cel = window.height() + eltolás
    window.setHeight(cel)
    assert varj(qt_app, lambda: window.height() == cel, 3.0)


def _album_nezet(window, controller, qt_app) -> tuple[str, list[int]]:
    rows = list(range(min(2, controller.photos.rowCount())))
    assert rows, "a funkcionális tesztnek legalább egy képre szüksége van"
    token = controller.createAlbum("7131 próbaalbum", rows)
    assert token
    controller.showAlbum(token)
    assert varj(qt_app, lambda: controller.currentAlbumToken == token, 5.0)
    assert varj(qt_app, lambda: controller.photos.rowCount() == len(rows), 5.0)
    window.setProperty("selectedIndexes", rows)
    window.setProperty("selectedIndex", rows[0])
    qt_app.processEvents()
    return token, rows


def _kepernyovedo_sor(window, qt_app, route: str):
    if route == "photo":
        menu = jobbklikk_fotón(window, qt_app, 0)
        almenu_megnyitasa(window, qt_app, menu, "contextMenuAddToAlbum")
        nev = "contextMenuAddToScreensaver"
    else:
        window.setProperty("viewerOpen", True)
        viewer = gyerek(window, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        assert varj(qt_app, lambda: viewer.isVisible(), 3.0)
        kattints(window, qt_app, viewer, Qt.MouseButton.RightButton)
        menu = gyerek(window, "viewerContextMenu")
        assert varj(qt_app, lambda: menu.property("opened") is True, 3.0)
        almenu_megnyitasa(window, qt_app, menu, "viewerMenuAddToAlbum")
        nev = "viewerMenuAddToScreensaver"
    return menu, keres_vizualis_mindenablakban(window, nev)


@pytest.mark.parametrize(
    ("route", "height_offset"),
    [
        ("photo", -5), ("photo", 0), ("photo", 5),
        ("viewer", -5), ("viewer", 0), ("viewer", 5),
    ],
)
def test_album_nezetben_a_kepmenuk_megerosites_nelkul_adnak_a_kepernyovedohoz(
    qml_app, qt_app, route, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _token, rows = _album_nezet(window, controller, qt_app)
    vart_utak = {
        Path(controller.photos.filePathAt(row))
        for row in (rows if route == "photo" else rows[:1])
    }
    elotte = {Path(path) for path in controller._screensaver_photo_paths()}

    menu, sor = _kepernyovedo_sor(window, qt_app, route)
    assert sor is not None, "a Screensaver menüsor nem látszik"
    kattints(window, qt_app, sor)

    confirm = window.findChild(QObject, "screensaverAlbumConfirmDialog")
    assert confirm is None or confirm.property("visible") is False, (
        "a fotó- vagy nézőmenü album-nézetben megerősítést nyitott"
    )
    assert varj(
        qt_app,
        lambda: vart_utak.issubset(
            {Path(path) for path in controller._screensaver_photo_paths()}
        ),
        5.0,
    ), "a kiválasztott/nézett képek nem kerültek a képernyővédő forrásai közé"
    hozzaadott = {Path(path) for path in controller._screensaver_photo_paths()} - elotte
    assert hozzaadott == vart_utak
    banner = gyerek(window, "errorBanner")
    assert banner.property("notice") is True, "a hozzáadás utáni értesítősáv eltűnt"
    if menu.property("opened") is True or menu.property("visible") is True:
        menu.close()
        qt_app.processEvents()


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_talca_uj_album_ma_datummal_nyilik_es_az_ini_be_is_azt_menti(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    assert controller.photos.rowCount() > 0
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    assert varj(qt_app, lambda: controller.heldCount == 1, 5.0)

    button = gyerek(window, "trayAddToButton")
    kattints(window, qt_app, button)
    menu = gyerek(window, "trayAddToMenu")
    assert varj(qt_app, lambda: menu.property("opened") is True, 3.0)
    kattints(
        window, qt_app,
        gyerek(window, "trayAddToNewAlbumItem"),
    )

    dialog = gyerek(window, "toolbarNewAlbumPropertiesDialog")
    assert varj(qt_app, lambda: dialog.property("opened") is True, 3.0)
    ma = QDate.currentDate().toString(Qt.DateFormat.ISODate)
    assert dialog.property("currentDate") == ma
    kattints(window, qt_app, gyerek(dialog, "folderPropertiesOkButton"))
    assert varj(qt_app, lambda: len(controller.albums) == 1, 5.0)

    token = controller.albums[0]["token"]
    ini = (Path(controller.currentFolder) / ".picasa.ini").read_text(
        encoding="utf-8"
    )
    sorok = ini.splitlines()
    kezdet = sorok.index(f"[.album:{token}]") + 1
    szakasz = []
    for sor in sorok[kezdet:]:
        if sor.startswith("["):
            break
        szakasz.append(sor)
    assert f"date={ma}" in szakasz, "az OK után nem a mai nap került az ini date= kulcsába"
