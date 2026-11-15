"""#7005: több kijelölt képnél a csillagozás képenként fordít (`0x005e81e0`).

Az eredeti `0x005e8260`-`0x005e82b2` ciklusa minden kijelölt képnél
lekérdezi a csillagot, és a negáltját írja vissza. Vegyes kijelölésnél a
csillagozott képről lekerül a csillag, a csillagozatlan megkapja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Q_ARG, QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index
from picasapy.ini import parse_document
from support.jpeg_factory import make_jpeg


def _child(root, name: str) -> QObject:
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _tray_star_button(window) -> QObject:
    button = _child(window, "trayStarButton")
    assert button is not None and button.property("targetRow") is not None
    return button


def _select(window, qt_app, index: int, modifiers: int = 0) -> None:
    QMetaObject.invokeMethod(
        window,
        "handleThumbClick",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", index),
        Q_ARG("QVariant", modifiers),
    )
    qt_app.processEvents()


def _index_star(controller, name: str) -> int:
    with open_index(controller._db_path) as conn:
        row = conn.execute(
            "SELECT star FROM photos WHERE name = ?", (name,)
        ).fetchone()
    assert row is not None, f"{name} nincs az indexben"
    return int(row[0])


def _selected_indexes(window) -> list[int]:
    val = window.property("selectedIndexes")
    if hasattr(val, "toVariant"):
        val = val.toVariant()
    return list(val or [])


def _ini_star(folder: Path, name: str) -> str | None:
    ini = folder / ".picasa.ini"
    if not ini.exists():
        return None
    doc = parse_document(ini.read_text(encoding="utf-8"))
    sec = doc.section(name)
    if sec is None:
        return None
    return sec.get("star")


@pytest.fixture
def qml_app_vegyes_csillag(qt_app, tmp_path, request):
    def kepek(lib: Path):
        make_jpeg(lib / "a.jpg", size=(320, 160))
        make_jpeg(lib / "b.jpg", size=(100, 100))
        (lib / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")

    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepek,
        keep_modul=request.module,
        nezetek_elore_epit=True,
    )


@pytest.mark.parametrize("magassag", (795, 800, 805))
def test_tobb_kijelolt_csillagozas_valodi_billentyu_es_kattintas_7005(
    qml_app_vegyes_csillag, qt_app, magassag
) -> None:
    """Két kijelölt képnél (egy csillagos, egy nem) az F4, a Ctrl+8 és a
    tálca Csillag gombja után az első csillagtalan, a második csillagos, a
    kijelölés nem változik (#7005)."""
    window, controller, _engine = qml_app_vegyes_csillag
    window.resize(1024, magassag)
    window.show()
    qt_app.processEvents()

    folder = Path(controller.photos.photos[0].folder_path)

    # kiindulás: az a.jpg (0. sor) csillagos, a b.jpg (1. sor) nem
    assert [p.star for p in controller.photos.photos] == [True, False]
    assert _index_star(controller, "a.jpg") == 1
    assert _index_star(controller, "b.jpg") == 0
    assert _ini_star(folder, "a.jpg") == "yes"
    assert _ini_star(folder, "b.jpg") is None

    # mindkét kép kijelölése
    ctrl = int(Qt.KeyboardModifier.ControlModifier.value)
    _select(window, qt_app, 0)
    _select(window, qt_app, 1, ctrl)
    assert _selected_indexes(window) == [0, 1]

    # 1. lépés: az F4 leütése megfordítja a két kép csillagát
    QTest.keyClick(window, Qt.Key.Key_F4)
    qt_app.processEvents()

    assert _selected_indexes(window) == [0, 1]
    assert [p.star for p in controller.photos.photos] == [False, True]
    assert _index_star(controller, "a.jpg") == 0
    assert _index_star(controller, "b.jpg") == 1
    assert _ini_star(folder, "a.jpg") is None
    assert _ini_star(folder, "b.jpg") == "yes"

    # 2. lépés: a Ctrl+8 leütése újra megfordítja
    QTest.keyClick(window, Qt.Key.Key_8, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    assert _selected_indexes(window) == [0, 1]
    assert [p.star for p in controller.photos.photos] == [True, False]
    assert _index_star(controller, "a.jpg") == 1
    assert _index_star(controller, "b.jpg") == 0
    assert _ini_star(folder, "a.jpg") == "yes"
    assert _ini_star(folder, "b.jpg") is None

    # 3. lépés: valódi kattintás a képtálca Csillag gombjára, újra megfordul
    button = _tray_star_button(window)
    assert button.property("multi") is True
    pont = button.mapToScene(QPointF(button.width() / 2, button.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()

    assert _selected_indexes(window) == [0, 1]
    assert [p.star for p in controller.photos.photos] == [False, True]
    assert _index_star(controller, "a.jpg") == 0
    assert _index_star(controller, "b.jpg") == 1
    assert _ini_star(folder, "a.jpg") is None
    assert _ini_star(folder, "b.jpg") == "yes"
