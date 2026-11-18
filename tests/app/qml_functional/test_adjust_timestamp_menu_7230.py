"""#7230: az Eszközök dátummódosítója nézőben és mappán is elérhető."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_MAGASSAG_ELTOLASOK = (-5, 0, 5)
_CEL_MAPPANEVE = "cel"
_CEL_DATUMOK = (
    ("a_elso.jpg", "2020:01:02 08:15:00"),
    ("b_masodik.jpg", "2020:01:03 09:16:00"),
)


def _kepeket_keszit(lib: Path) -> None:
    cel = lib / _CEL_MAPPANEVE
    cel.mkdir()
    masik = lib / "masik"
    masik.mkdir()
    make_jpeg(lib / "gyoker.jpg", taken_at="2020:01:04 10:00:00")
    make_jpeg(masik / "masik.jpg", taken_at="2020:01:05 11:00:00")
    for nev, datum in _CEL_DATUMOK:
        make_jpeg(cel / nev, taken_at=datum, datetime_0th=datum)


@pytest.fixture
def timestamp_menu_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_kepeket_keszit
    )


def _var(qt_app, feltetel, leiras: str, ido: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, ido), f"időtúllépés: {leiras}"


def _elem(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nem található: {nev}"
    return elem


def _szoveges_menuelem(window, szoveg: str):
    elem = next(
        (
            jelolt
            for jelolt in window.findChildren(QObject)
            if jelolt.property("text") == szoveg
        ),
        None,
    )
    assert elem is not None, f"nem található a menüelem: {szoveg}"
    return elem


def _kattints(window, qt_app, elem) -> None:
    pont = elem.mapToScene(
        QPointF(float(elem.width()) / 2, float(elem.height()) / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _menu_megnyitasa(window, qt_app):
    menu = _elem(window, "menuTools")
    menu.open()
    _var(qt_app, lambda: menu.property("visible"), "az Eszközök menü")
    return menu


def _photo_rows(controller, folder: Path) -> list[int]:
    return [
        row
        for row in range(controller.photos.rowCount())
        if Path(controller.photos.filePathAt(row)).parent == folder
    ]


def _dialog_rows(dialog) -> list[int]:
    rows = dialog.property("photoRows")
    if hasattr(rows, "toVariant"):
        rows = rows.toVariant()
    return [int(row) for row in rows]


def _window_height(window, qt_app, offset: int) -> None:
    target = int(window.height()) + offset
    window.setHeight(target)
    _var(
        qt_app,
        lambda: int(window.height()) == target,
        f"ablakmagasság {offset:+} px eltéréssel",
    )


def _neighbor_states(window) -> tuple[bool, ...]:
    items = (
        _elem(window, "menuToolsFolderManager"),
        _szoveges_menuelem(window, "&Upload Manager..."),
        _elem(window, "menuToolsPhotoViewerSettings"),
        _elem(window, "menuToolsScreensaver"),
        _elem(window, "menuToolsBackup"),
        _szoveges_menuelem(window, "Batch Upload..."),
    )
    return tuple(bool(item.property("enabled")) for item in items)


@pytest.mark.parametrize("ablakmagassag_eltolas", _MAGASSAG_ELTOLASOK)
@pytest.mark.parametrize("allapot", ("viewer", "folder", "none"))
def test_datummodosito_menu_allapot_es_kattintas_7230(
    timestamp_menu_app,
    qt_app,
    allapot: str,
    ablakmagassag_eltolas: int,
) -> None:
    window, controller, _engine = timestamp_menu_app
    window.show()
    qt_app.processEvents()
    _window_height(window, qt_app, ablakmagassag_eltolas)

    cel_mappa = Path(controller.currentFolder) / _CEL_MAPPANEVE
    cel_sorok = _photo_rows(controller, cel_mappa)
    assert len(cel_sorok) == len(_CEL_DATUMOK)

    vart_sorok: list[int] = []
    if allapot == "folder":
        controller.selectFolder(str(cel_mappa))
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        _var(
            qt_app,
            lambda: controller.currentFolder == str(cel_mappa)
            and controller.viewModeName == "folder",
            "a célmappa kijelölése",
        )
        vart_sorok = cel_sorok
    elif allapot == "viewer":
        vart_sorok = [cel_sorok[0]]
        masik_sor = next(
            row for row in range(controller.photos.rowCount()) if row not in cel_sorok
        )
        window.setProperty("selectedIndexes", [masik_sor])
        window.setProperty("selectedIndex", masik_sor)
        window.openPhotoViewer(vart_sorok[0])
        _var(qt_app, lambda: window.property("viewerOpen"), "a néző megnyitása")
        viewer = window.ensurePhotoViewer()
        _var(
            qt_app,
            lambda: int(viewer.property("currentIndex")) == vart_sorok[0],
            "a célkép megjelenése a nézőben",
        )
    else:
        token = controller.createEmptyAlbum(
            "Üres tesztalbum", str(controller.currentFolder), "", "", "", False, ""
        )
        assert token, "az üres album létrehozása nem sikerült"
        controller.showAlbum(token)
        window.setProperty("selectedIndexes", [])
        window.setProperty("selectedIndex", -1)
        _var(
            qt_app,
            lambda: controller.currentAlbumToken == token
            and controller.viewModeName == "album",
            "a kijelölés nélküli album-nézet",
        )

    _menu_megnyitasa(window, qt_app)
    item = _elem(window, "menuToolsAdjustTimestamp")
    assert item.property("enabled") is True, (
        f"a dátummódosító menüpont letiltott ebben az állapotban: {allapot}"
    )

    szomszedok = _neighbor_states(window) if allapot == "viewer" else ()
    status_elotte = controller.statusText
    _kattints(window, qt_app, item)

    if allapot == "none":
        dialog = window.findChild(QObject, "adjustTimestampDialog")
        assert dialog is None or dialog.property("visible") is False, (
            "üres kijelölésnél nem nyílhat meg a dátummódosító"
        )
        assert controller.statusText == status_elotte, (
            "üres kijelölésnél nem jelenhet meg hibajelzés"
        )
        return

    _var(
        qt_app,
        lambda: window.findChild(QObject, "adjustTimestampDialog") is not None,
        "a dátummódosító ablak létrejötte",
    )
    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátummódosító ablak")
    assert _dialog_rows(dialog) == vart_sorok
    if allapot == "viewer":
        assert dialog.property("title") == "Adjust Photo Date"
        assert _elem(window, "adjustTimestampCurrentDateField").property(
            "text"
        ) == "2020-01-02"
        assert _neighbor_states(window) == szomszedok, (
            "a dátummódosító megváltoztatta egy szomszédos Eszközök-tétel állapotát"
        )
    else:
        assert dialog.property("title") == "Adjust Photo Date - 2 items"
        assert _elem(window, "adjustTimestampCurrentDateField").property(
            "text"
        ) == "2020-01-02"

