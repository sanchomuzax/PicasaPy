"""A Rename Files csak megváltoztatott, nem üres névvel fogadható el (#5870)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    kijelolt,
    varj,
    vizualis_bejaras,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg

_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Két valódi JPEG-gel és a valódi bélyegkép-szolgáltatóval indul."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "tengerpart.jpg", size=(640, 480), seed=7)
        make_minta_jpeg(lib / "hegyek.jpg", size=(320, 240), seed=8)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _valodi_belyegkep_kesz(window) -> bool:
    for elem in vizualis_bejaras(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTOLASOK)
def test_f2_valtozatlan_es_ures_nevnel_letiltott_es_pelda_nelkul(
    qml_app, qt_app, tmp_path, magassag_elteres
):
    window, controller, _engine = qml_app
    window.show()
    window.setHeight(window.height() + magassag_elteres)
    window.requestActivate()
    assert varj(qt_app, lambda: window.property("active") is True), (
        "a főablak nem aktiválódott"
    )
    assert varj(qt_app, lambda: len(controller.photos.photos) == 2), (
        "a két tesztkép nem töltődött be"
    )

    kattints(window, qt_app, kep_cellaja(window, 0))
    assert kijelolt(window) == [0], "a valódi bélyegképkattintás nem jelölt ki képet"
    regi_ut = Path(str(controller.photos.filePathAt(0)))
    eredeti_nev = regi_ut.stem
    QTest.keyClick(window, Qt.Key.Key_F2)

    assert varj(
        qt_app,
        lambda: (
            (dialog := window.findChild(QObject, "renameManyDialog")) is not None
            and dialog.property("visible") is True
        ),
    ), "az F2 nem a Rename Files párbeszédet nyitotta meg"
    dialog = _gyerek(window, "renameManyDialog")
    mezo = _gyerek(window, "renameManyField")
    pelda = _gyerek(window, "renameManySampleLabel")
    rename_gomb = next(
        elem
        for elem in dialog.findChildren(QObject)
        if elem.property("text") == "Rename"
    )

    assert mezo.property("text") == eredeti_nev
    assert rename_gomb.property("enabled") is False, (
        "változatlan névnél a Rename gombnak letiltottnak kell lennie"
    )
    assert pelda.property("visible") is True
    assert pelda.property("text") == f"Example: {eredeti_nev}.jpg"

    if magassag_elteres == 0:
        assert varj(qt_app, lambda: _valodi_belyegkep_kesz(window)), (
            "a kiadásképhez nem töltődött be valódi bélyegkép"
        )
        kep_ut = Path(os.environ.get(
            "PICASA_5870_SCREENSHOT",
            str(tmp_path / "rename-files-5870.png"),
        ))
        kep_ut.parent.mkdir(parents=True, exist_ok=True)
        kep = window.grabWindow()
        assert not kep.isNull(), "a párbeszéd képernyőképe üres"
        assert kep.save(str(kep_ut)), f"nem menthető a kiadáskép: {kep_ut}"

    # Az előtöltött név végére gépelünk, így a mező megváltozott értéke
    # továbbra is az eredeti nevet tartalmazza.
    QTest.keyClick(window, Qt.Key.Key_End)
    QTest.keyClick(window, Qt.Key.Key_X)
    qt_app.processEvents()
    assert mezo.property("text") == f"{eredeti_nev}x"
    assert rename_gomb.property("enabled") is True
    assert pelda.property("visible") is True
    assert pelda.property("text") == f"Example: {eredeti_nev}x.jpg"

    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    QTest.keyClick(window, Qt.Key.Key_Backspace)
    qt_app.processEvents()
    assert mezo.property("text") == ""
    assert rename_gomb.property("enabled") is False
    assert pelda.property("visible") is False

    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()
    assert regi_ut.exists(), "Enter letiltott gomb mellett átnevezte a képet"
    assert dialog.property("visible") is True, (
        "Enter letiltott gomb mellett elfogadta a párbeszédet"
    )

