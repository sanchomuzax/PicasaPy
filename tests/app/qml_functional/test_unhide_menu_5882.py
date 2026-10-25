"""#5882: a Kép és a Mappa menü Unhide tétele csak rejtett elemre aktív."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Qt
from PySide6.QtTest import QTest
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _kattints,
    _nyisd_meg_felso_menut,
)
from tests.app.qml_functional.test_album_menu_mappa_elrejtes_4741 import (
    _nyisd_meg_menu_tetelt,
)
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app_minta_belyegkep(qt_app, tmp_path):
    """Két mintázott JPEG a valódi bélyegkép-szolgáltatóval (a kiadásképhez)."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=7)
        make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=8)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)
_BELYEGKEP_HATARIDO_MP = 3.0


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _menutetel(qt_app, window, menu_nev, item_nev):
    if menu_nev == "menuPicture":
        refs = _nyisd_meg_felso_menut(
            qt_app, window, "picture", item_nev
        )
    else:
        refs = _nyisd_meg_menu_tetelt(
            qt_app, window, item_nev
        )
    # A teljes hivatkozáscsomag maradjon a hívó hatókörében: a Qt/QML
    # menü-delegátumának élettartama a menüsáv- és fejlécreferenciákhoz kötött.
    return refs


def _zar_menut(qt_app, window, menu):
    if menu.property("opened") is True:
        QTest.keyClick(window, Qt.Key.Key_Escape)
        assert _varj(qt_app, lambda: menu.property("opened") is not True), (
            f"a {menu.objectName()} menü nem záródott be"
        )


def _kijelol(window, qt_app, sorok):
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _vizualis_bejaras(gyoker):
    yield gyoker
    for gyermek in gyoker.childItems():
        yield from _vizualis_bejaras(gyermek)


def _valodi_belyegkepek_keszek(window):
    """A kiadáskép előtt mindkét thumbnail képkérése legyen betöltve."""
    kepek = [
        elem
        for elem in _vizualis_bejaras(window.contentItem())
        if elem.objectName() == "thumbImage"
    ]
    return len(kepek) >= 2 and all(
        float(elem.property("implicitWidth")) > 1
        and float(elem.property("implicitHeight")) > 1
        for elem in kepek[:2]
    )


def _jelszoajanlat_kikapcsolasa(controller):
    from picasapy.app.confirm_settings import set_confirm_suppressed

    set_confirm_suppressed(controller._get_settings(), "DoNotConfirmHiddenPwd", True)


def _kiadas_kep(window, cel):
    kep = window.grabWindow()
    assert not kep.isNull(), "a megnyitott Mappa menü képe üres"
    cel = Path(cel)
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"


def test_unhide_menu_allapot_es_valodi_kattintasok(
    qml_app_minta_belyegkep, qt_app, tmp_path
):
    window, controller, _engine = qml_app_minta_belyegkep
    alapmagassag = int(window.height())
    controller.setShowHidden(True)
    _jelszoajanlat_kikapcsolasa(controller)

    # Az állapotot és a feliratot egyszer, az alap ablakmagasságon mérjük.
    kep = Path(controller.photos.filePathAt(0))
    sor = controller.photos.rowOfPath(str(kep))
    _kijelol(window, qt_app, [sor])
    eltérések = []
    _picture_bar, picture, _picture_header, picture_unhide = _menutetel(
        qt_app, window, "menuPicture", "menuPictureUnhide"
    )
    if picture_unhide.property("enabled") is not False:
        eltérések.append("a látható kijelölt képnél a Kép ▸ Unhide nem szürke")
    _zar_menut(qt_app, window, picture)

    _folder_bar, folder, _folder_header, folder_unhide = _menutetel(
        qt_app, window, "menuFolder", "menuFolderShow"
    )
    if folder_unhide.property("text") != "&Unhide":
        eltérések.append(
            f"a Mappa menü felirata {folder_unhide.property('text')!r}, nem '&Unhide'"
        )
    if folder_unhide.property("enabled") is not False:
        eltérések.append("a látható mappánál a Mappa ▸ Unhide nem szürke")
    output = os.environ.get("PICASAPY_5882_SCREENSHOT")
    assert _varj(
        qt_app, lambda: _valodi_belyegkepek_keszek(window), _BELYEGKEP_HATARIDO_MP
    ), (
        "a kiadáskép előtt a valós thumbnail-képek nem töltődtek be"
    )
    _kiadas_kep(window, output or (tmp_path / "5882-folder-menu.png"))
    _zar_menut(qt_app, window, folder)

    mappa = controller.currentFolder
    # A valós kattintásokat mindhárom ablakmagasságon végigjárjuk.
    for magassag_eltolas in _ABLAKMAGASSAG_ELTOLASOK:
        window.setHeight(alapmagassag + magassag_eltolas)
        assert _varj(
            qt_app,
            lambda eltolás=magassag_eltolas: int(window.height())
            == alapmagassag + eltolás,
        ), f"a főablak magassága nem állt be ({magassag_eltolas:+} px)"

        sor = controller.photos.rowOfPath(str(kep))
        _kijelol(window, qt_app, [sor])
        _picture_bar, picture, _picture_header, hide = _menutetel(
            qt_app, window, "menuPicture", "menuPictureHide"
        )
        _kattints(qt_app, hide)
        assert _varj(
            qt_app, lambda sor=sor: controller.photos.itemAt(sor)["hidden"] is True
        ), "a Kép ▸ Hide valódi kattintása nem rejtette el a képet"

        _kijelol(window, qt_app, [sor])
        _picture_bar, picture, _picture_header, unhide = _menutetel(
            qt_app, window, "menuPicture", "menuPictureUnhide"
        )
        if unhide.property("enabled") is not True:
            eltérések.append("rejtett képnél a Kép ▸ Unhide le van tiltva")
        _kattints(qt_app, unhide)
        assert _varj(
            qt_app, lambda sor=sor: controller.photos.itemAt(sor)["hidden"] is False
        ), "a Kép ▸ Unhide valódi kattintása nem hozta vissza a képet"

        mappa = controller.currentFolder
        _folder_bar, folder, _folder_header, hide_folder = _menutetel(
            qt_app, window, "menuFolder", "menuFolderHide"
        )
        _kattints(qt_app, hide_folder)
        assert _varj(
            qt_app, lambda mappa=mappa: controller.isFolderHidden(mappa) is True
        ), "a Mappa ▸ Hide valódi kattintása nem rejtette el a mappát"

        # A vezérlő a kiválasztott mappa útját megtartja a Hidden Folders
        # csoportba sorolás után is; a kiválasztást a valós mappa-lista friss
        # modellállapotára állítjuk vissza.
        controller.selectFolder(mappa)
        assert _varj(
            qt_app, lambda mappa=mappa: controller.currentFolder == mappa
        )
        _folder_bar, folder, _folder_header, unhide_folder = _menutetel(
            qt_app, window, "menuFolder", "menuFolderShow"
        )
        if unhide_folder.property("enabled") is not True:
            eltérések.append(
                "a Rejtett mappák közül kijelölt mappánál az Unhide szürke"
            )
        _kattints(qt_app, unhide_folder)
        assert _varj(
            qt_app, lambda mappa=mappa: controller.isFolderHidden(mappa) is False
        ), "a Mappa ▸ Unhide valódi kattintása nem hozta vissza a mappát"

    assert not eltérések, "\n".join(eltérések)
