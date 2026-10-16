"""#5150 (5. rész, 2. fájl): a tálca többi gombja valódi egérkattintással.

- `trayAddToButton` - a gomb megnyitja az album-listát (ha van tálcás kép és
  album);
- `zoomFitButton`, `zoomActualButton` - a néző nagyítás-párja: az illesztés
  a nagyítást 0-ra, a valódi méret a `zoomDetent`-re (0,5) állítja;
- `trayUploadButton`, `trayOrderButton`, `trayShareButton`, `trayBlogButton` -
  LETILTVA, és nincs kezelőjük. A valódi kattintásnak nincs hatása, és a
  tiltottságot külön mérjük.

Már valódi kattintással fedett tételek (nem ismételjük):
- `trayEmailButton`, `trayExportButton`: test_talca_gombok_valodi_kattintas_5127.py:99, :123
- `trayMoreItem`: test_tulcsordulas_fuggoleges_4537.py:173
- `searchbutton`, `facesearch`, `dupesearch`: test_search_lefedettseg_4202.py:260
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from tests.app.qml_functional.test_talca_eszkoztar_valodi_5150 import (
    _gyerek,
    _kattints,
    _kijelol,
    _nyitott,
    _sor,
    _varj,
    _zar,
)


@pytest.fixture
def talca_app(qt_app, tmp_path, request):
    yield from _build_qml_app(qt_app, tmp_path, keep_modul=request.module)


def _allapot(window, controller) -> tuple:
    """Az állapot, amelyet egy valódi kattintásnak meg kellene változtatnia."""
    return (
        window.property("viewerOpen"),
        window.property("activeDrawerTab"),
        controller.heldCount,
        list(window.property("selectedIndexes")),
    )


def _varva_es_kattint(window, qt_app, nev: str) -> None:
    """Megvárja, hogy az elem kirajzolódjon, és arra valódi kattintást ad."""
    gomb = _gyerek(window, nev, QQuickItem)
    assert _varj(qt_app, lambda: gomb.isVisible() and gomb.width() > 0), (
        f"{nev} nem rajzolódott ki"
    )
    _kattints(qt_app, gomb)


def _nezo_nyitva(window, qt_app, controller) -> QObject:
    """A kijelölt képet a Ctrl+3 (Megjelenítés és szerkesztés) nyitja meg."""
    _kijelol(window, qt_app, [_sor(controller, "a.jpg")])
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    QTest.keyClick(window, Qt.Key.Key_3, Qt.KeyboardModifier.ControlModifier)
    assert _varj(qt_app, lambda: window.property("viewerOpen") is True), (
        "a Ctrl+3 nem nyitotta meg a nézőt"
    )
    return _gyerek(window, "photoViewer")


def test_az_add_to_gomb_megnyitja_az_album_listat(talca_app, qt_app):
    window, controller, _engine = talca_app
    controller.createAlbum("Proba", [_sor(controller, "b.jpg")])
    controller.holdRows([_sor(controller, "a.jpg")])
    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "a teszt albuma nem jött létre"
    )
    gomb = _gyerek(window, "trayAddToButton", QQuickItem)
    assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
        "az Add to gomb nem engedélyezett tálcás képpel és albummal"
    )

    _varva_es_kattint(window, qt_app, "trayAddToButton")

    menu = _gyerek(window, "trayAddToMenu")
    assert _varj(qt_app, lambda: _nyitott(menu)), (
        "az Add to gomb kattintása nem nyitotta meg az album-listát"
    )
    _zar(qt_app, menu)


def test_a_zoom_fit_gomb_illesztesre_allitja_a_nagyitast(talca_app, qt_app):
    window, controller, _engine = talca_app
    nezo = _nezo_nyitva(window, qt_app, controller)
    nezo.setProperty("zoomValue", 0.25)
    qt_app.processEvents()
    assert nezo.property("zoomValue") == pytest.approx(0.25)

    _varva_es_kattint(window, qt_app, "zoomFitButton")

    assert _varj(qt_app, lambda: nezo.property("zoomValue") == 0), (
        "a Fit gomb nem állította a nagyítást illesztésre"
    )


def test_a_zoom_actual_gomb_a_valodi_meretre_allitja_a_nagyitast(talca_app, qt_app):
    window, controller, _engine = talca_app
    nezo = _nezo_nyitva(window, qt_app, controller)
    assert nezo.property("zoomValue") == 0, "a nézet nem illesztve nyílt meg"

    _varva_es_kattint(window, qt_app, "zoomActualButton")

    detent = nezo.property("zoomDetent")
    assert _varj(qt_app, lambda: nezo.property("zoomValue") == pytest.approx(detent)), (
        "az 1:1 gomb nem a valódi méretre (zoomDetent) állította a nagyítást"
    )


@pytest.mark.parametrize(
    "nev",
    ["trayUploadButton", "trayOrderButton", "trayShareButton", "trayBlogButton"],
)
def test_a_letiltott_talcagomb_valodi_kattintasra_nem_valtoztat_semmit(
    talca_app, qt_app, nev
):
    """LETILTVA: nincs kezelője. A tiltottság a tesztelt állítás."""
    window, controller, _engine = talca_app
    _kijelol(window, qt_app, [_sor(controller, "a.jpg")])
    gomb = _gyerek(window, nev, QQuickItem)
    assert gomb.property("enabled") is False, f"{nev}: nincs letiltva"
    elotte = _allapot(window, controller)

    _varva_es_kattint(window, qt_app, nev)

    assert _allapot(window, controller) == elotte, (
        f"a letiltott {nev} valódi kattintása megváltoztatta az állapotot"
    )
