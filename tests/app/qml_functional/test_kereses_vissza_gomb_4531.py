"""#4531: szöveges keresés után a zöld sávon látszik a „Vissza az összes
megtekintéséhez" gomb, és kattintásra visszaáll a teljes nézet.

Az eredeti Picasában a keresősávon ott a `searchoptions/viewallbutton`
(„Back to View All"), amely a keresésből a teljes nézetbe visz vissza
(ld. `docs/specs/picasa-kereses-modok.md` §2). Nálunk a keresés kikapcsolta
a zöld eredménysávot (`filterActive`), így a gomb sosem jelent meg.

A tesztek valódi egérkattintással és a keresőmezőn át (`textEdited`) dolgoznak,
−5/0/+5 px ablakmagassággal.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)
GOMB_NEV = "searchBackToViewAll"


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _magassag(window, offset: int) -> None:
    window.setHeight(window.height() + offset)


def _nevek(controller) -> list[str]:
    return [photo.name for photo in controller.photos.photos]


def _keress(window, qt_app, szoveg: str) -> None:
    """Keresés a KERESŐMEZŐN át (`textEdited` → `controller.search`)."""
    field = window.findChild(QObject, "searchField")
    assert field is not None, "a keresőmező nem található"
    field.setProperty("text", szoveg)
    QMetaObject.invokeMethod(
        field, "textEdited", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


def _gomb_kattintas(window, qt_app) -> None:
    """Valódi egérkattintás a gomb közepére — nem a Python-slot hívása."""
    gomb = window.findChild(QObject, GOMB_NEV)
    assert gomb is not None and gomb.isVisible(), (
        "a „Vissza az összes megtekintéséhez” gomb nem látszik keresés után"
    )
    assert gomb.width() > 0 and gomb.height() > 0, "a gombnak nincs mérete"
    kozep = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
    QTest.mouseClick(
        gomb.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_keresés_utan_a_gomb_latszik_es_visszaallitja_a_teljes_nezetet(
    qml_app, qt_app, height_offset
) -> None:
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    assert _nevek(controller) == ["a.jpg", "b.jpg"]

    _keress(window, qt_app, "a")
    assert _varj(qt_app, lambda: _nevek(controller) == ["a.jpg"]), (
        "a keresés nem talált egyetlen képet sem"
    )

    _gomb_kattintas(window, qt_app)

    assert _varj(qt_app, lambda: _nevek(controller) == ["a.jpg", "b.jpg"]), (
        "a gomb nem állította vissza a teljes nézetet: "
        f"{_nevek(controller)}"
    )
    assert controller.filterActive is False
    assert controller.viewModeName == "folder"
    mezo = window.findChild(QObject, "searchField")
    assert mezo.property("text") == "", "a keresőmezőben ottmaradt a szöveg"
    assert controller._folders_filtered is False, (
        "a bal hasáb a keresés találatos mappáira szűkítve maradt"
    )


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_gomb_csak_szoveges_kereses_utan_latszik(
    qml_app, qt_app, height_offset
) -> None:
    """Mappa-nézetben nincs keresés, így nincs visszalépő gomb sem."""
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    qt_app.processEvents()

    gomb = window.findChild(QObject, GOMB_NEV)
    assert gomb is None or not gomb.isVisible()
    assert controller.filterActive is False
