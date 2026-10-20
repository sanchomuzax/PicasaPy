"""A tálca csillag- és forgatógombjainak lemezre írt eredménye (#5396)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from picasapy.ini import KeyValueLine, load_document
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


@pytest.fixture
def csillag_forgatas_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_kepeket,
    )


def _keszits_kepeket(mappa: Path) -> None:
    for sorszam in range(1, 8):
        make_jpeg(mappa / f"{sorszam}.jpg", size=(80, 60))


def _qml_bejaras(gyoker):
    for elem in gyoker.childItems():
        yield elem
        yield from _qml_bejaras(elem)


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _kattint(window, elem: QQuickItem, qt_app) -> None:
    assert elem.isVisible() and elem.isEnabled(), (
        f"a kattintandó elem nem látható vagy tiltott: {elem.objectName()}"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont.toPoint(),
    )
    qt_app.processEvents()


def _foto_kijelolese(window, controller, qt_app, fajlnev: str) -> int:
    sor = next(
        i for i, photo in enumerate(controller.photos.photos)
        if photo.name == fajlnev
    )
    mouse_areas = [
        item
        for item in _qml_bejaras(window.contentItem())
        if item.objectName() == "thumbMouseArea"
        and item.parentItem() is not None
        and item.parentItem().property("index") == sor
    ]
    assert len(mouse_areas) == 1, (
        f"a {fajlnev} kép rácsbeli kattintási területe nem egyértelmű"
    )
    _kattint(window, mouse_areas[0], qt_app)
    assert _var(qt_app, lambda: window.property("selectedIndex") == sor), (
        f"a valódi rácskattintás nem a {fajlnev} képet jelölte ki"
    )
    return sor


def _talca_gomb(window, object_name: str) -> QQuickItem:
    elem = window.findChild(QQuickItem, object_name)
    assert elem is not None, f"hiányzó tálcagomb: {object_name}"
    return elem


def _kattints_es_varj(window, controller, qt_app, gombnev: str) -> None:
    gomb = _talca_gomb(window, gombnev)
    wait_for_photo_op(
        controller,
        lambda: _kattint(window, gomb, qt_app),
        qt_app=qt_app,
    )


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_talca_csillag_es_forgatas_az_eredeti_ini_kimenetet_irja(
    csillag_forgatas_app, qt_app, magassag_eltolas, tmp_path
):
    window, controller, _engine = csillag_forgatas_app
    eredeti_magassag = window.height()
    celmagassag = eredeti_magassag + magassag_eltolas
    window.setHeight(celmagassag)
    assert _var(qt_app, lambda: window.height() == celmagassag), (
        f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
    )
    assert [photo.name for photo in controller.photos.photos] == [
        f"{sorszam}.jpg" for sorszam in range(1, 8)
    ]
    assert all(
        not photo.star and photo.rotate_steps == 0
        for photo in controller.photos.photos
    )

    _foto_kijelolese(window, controller, qt_app, "4.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: controller.photos.starAt(3))

    _foto_kijelolese(window, controller, qt_app, "7.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: controller.photos.starAt(6))
    _kattints_es_varj(window, controller, qt_app, "trayStarButton")
    assert _var(qt_app, lambda: not controller.photos.starAt(6))

    _foto_kijelolese(window, controller, qt_app, "5.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayRotateRight")
    assert _var(qt_app, lambda: controller.photos.rotateAt(4) == 1)

    _foto_kijelolese(window, controller, qt_app, "6.jpg")
    _kattints_es_varj(window, controller, qt_app, "trayRotateLeft")
    assert _var(qt_app, lambda: controller.photos.rotateAt(5) == 3)

    ini_path = Path(controller.photos.photos[0].folder_path) / ".picasa.ini"
    assert ini_path.is_file(), "a műveletek nem írtak .picasa.ini-t"
    document = load_document(ini_path)
    actual = [
        (
            section.name,
            {
                line.key: line.value
                for line in section.lines
                if isinstance(line, KeyValueLine)
            },
        )
        for section in document.file_sections()
    ]
    assert actual == [
        ("4.jpg", {"star": "yes"}),
        ("7.jpg", {}),
        ("5.jpg", {"rotate": "rotate(1)"}),
        ("6.jpg", {"rotate": "rotate(3)"}),
    ], f"a lemezre írt .picasa.ini eltér az eredeti viselkedésétől: {actual!r}"
    assert window.grabWindow().save(str(tmp_path / "csillag_forgatas_5396.png"))
