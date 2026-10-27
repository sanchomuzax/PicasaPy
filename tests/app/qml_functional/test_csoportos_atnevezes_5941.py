"""A Rename Files valódi kattintása foglalt cél esetén sorszámozott fájlt hoz létre (#5941)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    kijelolt,
    varj,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg


@pytest.fixture
def qml_app(qt_app, tmp_path):
    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "forras.jpg", size=(320, 240), seed=31)
        make_minta_jpeg(lib / "nyaralas.jpg", size=(320, 240), seed=32)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=128,
        valodi_belyegkep=True,
    )


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_rename_gomb_kattintasa_foglalt_celnel_001_nevvel_atnevez(
    qml_app, qt_app, magassag_elteres
):
    window, controller, _engine = qml_app
    window.show()
    window.setHeight(window.height() + magassag_elteres)
    window.requestActivate()
    assert varj(qt_app, lambda: window.property("active") is True), (
        "a főablak nem aktiválódott"
    )
    assert varj(qt_app, lambda: len(controller.photos.photos) == 2), (
        "a fixture két képe nem töltődött be"
    )

    source_index = next(
        i for i, photo in enumerate(controller.photos.photos)
        if photo.name == "forras.jpg"
    )
    source_path = Path(str(controller.photos.filePathAt(source_index)))
    occupied_path = source_path.with_name("nyaralas.jpg")
    occupied_bytes = occupied_path.read_bytes()

    kattints(window, qt_app, kep_cellaja(window, source_index))
    assert kijelolt(window) == [source_index], "a valódi bélyegképkattintás nem jelölt"
    QTest.keyClick(window, Qt.Key.Key_F2)
    assert varj(
        qt_app,
        lambda: (
            (dialog := window.findChild(QObject, "renameManyDialog")) is not None
            and dialog.property("visible") is True
        ),
    ), "az F2 nem a Rename Files párbeszédet nyitotta meg"

    dialog = _gyerek(window, "renameManyDialog")
    field = _gyerek(window, "renameManyField")
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    for character in "nyaralas":
        QTest.keyClick(window, character)
    qt_app.processEvents()
    assert field.property("text") == "nyaralas"

    rename_button = next(
        child for child in dialog.findChildren(QObject)
        if child.property("text") == "Rename"
    )
    kattints(window, qt_app, rename_button)

    result_path = source_path.with_name("nyaralas-001.jpg")
    assert varj(
        qt_app,
        lambda: (
            result_path.exists()
            and not source_path.exists()
            and dialog.property("visible") is False
        ),
    ), "a Rename gomb kattintása nem hozta létre a -001 célfájlt"
    assert occupied_path.read_bytes() == occupied_bytes, (
        "az átnevezés felülírta a korábban foglalt célfájlt"
    )
    kep_ut = os.environ.get("PICASAPY_5941_KIADASKEP")
    if kep_ut and magassag_elteres == 0:
        # Kiadáskép: az átnevezett képen újra megnyitott Rename Files
        # párbeszéd a -001-es új nevet mutatja.
        assert varj(qt_app, lambda: any(
            photo.name == "nyaralas-001.jpg" for photo in controller.photos.photos
        ))
        uj = next(
            i for i, photo in enumerate(controller.photos.photos)
            if photo.name == "nyaralas-001.jpg"
        )
        kattints(window, qt_app, kep_cellaja(window, 1 - uj))
        kattints(window, qt_app, kep_cellaja(window, uj))
        assert varj(qt_app, lambda: kijelolt(window) == [uj])
        QTest.keyClick(window, Qt.Key.Key_F2)
        assert varj(qt_app, lambda: dialog.property("visible") is True)
        assert varj(qt_app, lambda: field.property("text") == "nyaralas-001")
        QTest.qWait(300)
        window.grabWindow().save(kep_ut)
        QTest.keyClick(window, Qt.Key.Key_Escape)


# rontás-kontroll: a javítás nélküli kód a foglalt célon hibával áll meg, ezért
# a Rename Files párbeszéd valódi kattintásos próbája mindhárom ablakmagasságon piros.
