"""#7091: A dátummódosító ablak címe egy képnél darabszám nélkül jelenik meg.

Eredeti: a 0x0077c7c0 inicializáló 0x0077c7fc-nél cmp [ebp+0xd8], 1 / jbe:
egy képnél az alapcím marad (Adjust Photo Date), csak 2 vagy több képnél
formáz (Adjust Photo Date - %d items).

Nálunk: rows.length <= 1 esetén qsTr("Adjust Photo Date"); különben
qsTr("Adjust Photo Date - %1 items").arg(photoRows.length).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

DATUMOK = (
    ("a.jpg", "2020:01:01 10:00:00"),
    ("b.jpg", "2020:01:03 12:00:00"),
    ("c.jpg", "2020:01:05 14:00:00"),
)


def _kepek(lib: Path) -> None:
    for nev, taken_at in DATUMOK:
        make_jpeg(lib / nev, taken_at=taken_at, datetime_0th=taken_at)


@pytest.fixture
def timestamp_app(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek)


def _var(qt_app, feltetel, leiras: str, ido: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, ido), f"időtúllépés: {leiras}"


def _elem(window, nev: str):
    from PySide6.QtCore import QObject

    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nem található: {nev}"
    return elem


def _kattints(elem, qt_app, window=None) -> None:
    pont = elem.mapToScene(
        QPointF(float(elem.property("width")) / 2, float(elem.property("height")) / 2)
    ).toPoint()
    ablak = window if window is not None else elem.window()
    assert ablak is not None, f"{elem.objectName()} nem látható ablakban"
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont.x(), pont.y()),
    )
    qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_datummodosito_cim_egy_es_harom_kepnel_7091(
    timestamp_app, qt_app, magassag_eltolas
) -> None:
    """1 kép kijelölésével megnyitva a cím 'Adjust Photo Date' (darabszám nélkül),
    3 kép kijelölésével pedig 'Adjust Photo Date - 3 items' (#7091)."""
    window, controller, _engine = timestamp_app
    window.setHeight(window.height() + magassag_eltolas)
    assert controller.sortFolderBy(controller.currentFolder, "date")
    window.show()
    qt_app.processEvents()

    # --- 1. ESET: 1 kép kijelölése (selectedIndexes = [0]) ---
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    eszkozok = _elem(window, "menuTools")
    eszkozok.open()
    _var(qt_app, lambda: eszkozok.property("visible"), "az Eszközök menü megnyitása")

    menu_item = _elem(window, "menuToolsAdjustTimestamp")
    assert menu_item.property("enabled"), "a menüpont engedélyezett kell legyen"
    _kattints(menu_item, qt_app, window)

    dialog = _elem(window, "adjustTimestampDialog")
    _var(qt_app, lambda: dialog.property("visible"), "a dátumállító ablak megnyílása")

    # Egyetlen képnél darabszám nélküli cím kell megjelenjen (#7091)
    assert dialog.property("title") == "Adjust Photo Date"
    photo_rows = dialog.property("photoRows")
    if hasattr(photo_rows, "toVariant"):
        photo_rows = photo_rows.toVariant()
    assert len(photo_rows) == 1

    cancel_btn = _elem(window, "adjustTimestampCancel")
    _kattints(cancel_btn, qt_app, window)
    _var(qt_app, lambda: not dialog.property("visible"), "a dialógus bezáródik")

    # --- 2. ESET: 3 kép kijelölése (selectedIndexes = [0, 1, 2]) ---
    window.setProperty("selectedIndexes", [0, 1, 2])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    eszkozok.open()
    _var(
        qt_app,
        lambda: eszkozok.property("visible"),
        "az Eszközök menü újbóli megnyitása",
    )

    _kattints(menu_item, qt_app, window)
    _var(
        qt_app,
        lambda: dialog.property("visible"),
        "a dátumállító ablak újbóli megnyílása",
    )

    # Három képnél a darabszámos formátum jelenik meg (#7091)
    assert dialog.property("title") == "Adjust Photo Date - 3 items"
    photo_rows = dialog.property("photoRows")
    if hasattr(photo_rows, "toVariant"):
        photo_rows = photo_rows.toVariant()
    assert len(photo_rows) == 3

    _kattints(cancel_btn, qt_app, window)
    _var(qt_app, lambda: not dialog.property("visible"), "a dialógus bezáródik")
