"""Az egyképes átnevezés a közös Picasa-párbeszédet használja (#5804)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.app.qml_functional._fomenu_4420_menu import _megnyit
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    kijelolt,
    varj,
    vizualis_bejaras,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kep_cellaja
from tests.app.qml_functional.conftest import _build_qml_app
from support.jpeg_factory import make_minta_jpeg

_KEPNEV = "tengerpart.jpg"
_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Egy valódi, mintás JPEG-képen próbáljuk az egyképes útvonalat."""

    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / _KEPNEV, size=(640, 480), seed=7)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _valodi_belyegkep_kesz(window) -> bool:
    for elem in vizualis_bejaras(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(elem), elem, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


def _gyerek(window, nev: str):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _parbeszed_ellenorzese(window, qt_app, eredeti_stem: str):
    assert varj(
        qt_app,
        lambda: (
            (parbeszed := window.findChild(QObject, "renameManyDialog"))
            is not None
            and parbeszed.property("visible") is True
        ),
    ), "nem a Rename Files párbeszéd nyílt meg"
    parbeszed = _gyerek(window, "renameManyDialog")
    assert parbeszed.property("title") == "Rename Files"
    assert _gyerek(window, "renameManySelectionLabel").property("text") == (
        "1 file(s) selected for rename."
    )
    mezo = _gyerek(window, "renameManyField")
    assert mezo.property("text") == eredeti_stem, (
        "a névmezőnek a kijelölt fájl kiterjesztés nélküli nevét kell mutatnia"
    )
    assert mezo.property("selectionStart") == 0
    assert mezo.property("selectionEnd") == len(eredeti_stem), (
        "a fájlnév nem lett kijelölve a mezőben"
    )
    datum = _gyerek(window, "renameManyDateCheck")
    felbontas = _gyerek(window, "renameManySizeCheck")
    pelda = _gyerek(window, "renameManySampleLabel")
    assert datum.property("text") == "Date" and datum.property("visible") is True
    assert (
        felbontas.property("text") == "Image resolution"
        and felbontas.property("visible") is True
    )
    assert pelda.property("text").startswith("Example:")
    assert pelda.property("visible") is True
    return parbeszed, mezo


def _ablak_es_kijeloles(qml_app, qt_app, magassag_elteres: int):
    window, controller, _engine = qml_app
    window.show()
    window.setHeight(window.height() + magassag_elteres)
    window.requestActivate()
    assert varj(qt_app, lambda: window.property("active") is True), (
        "a főablak nem aktiválódott"
    )
    assert varj(qt_app, lambda: len(controller.photos.photos) == 1), (
        "a tesztképet nem töltötte be a könyvtár"
    )
    kattints(window, qt_app, kep_cellaja(window, 0))
    assert kijelolt(window) == [0], "a valódi bélyegképkattintás nem jelölt ki képet"
    return window, controller


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTOLASOK)
def test_f2_egy_keppel_a_nevmezot_kiterjesztes_nelkul_tolti_ki_es_atnevez(
    qml_app, qt_app, tmp_path, magassag_elteres
):
    window, controller = _ablak_es_kijeloles(qml_app, qt_app, magassag_elteres)
    regi_ut = Path(str(controller.photos.filePathAt(0)))

    QTest.keyClick(window, Qt.Key.Key_F2)
    parbeszed, mezo = _parbeszed_ellenorzese(window, qt_app, regi_ut.stem)

    if magassag_elteres == 0:
        cel_konyvtar = Path(
            os.environ.get("PICASA_5804_SCREENSHOT_DIR", str(tmp_path))
        )
        cel_konyvtar.mkdir(parents=True, exist_ok=True)
        assert varj(qt_app, lambda: _valodi_belyegkep_kesz(window)), (
            "a kiadásképhez nem töltődött be a valódi bélyegkép"
        )
        kep = window.grabWindow()
        assert not kep.isNull(), "a párbeszéd képernyőképe üres"
        assert kep.save(str(cel_konyvtar / "atnevezes-5804.png")), (
            "a párbeszéd kiadásképe nem menthető"
        )

    for karakter in "atnevezett":
        QTest.keyClick(window, karakter)
        qt_app.processEvents()
    assert mezo.property("text") == "atnevezett"
    rename_gomb = next(
        elem
        for elem in parbeszed.findChildren(QObject)
        if elem.property("text") == "Rename"
    )
    kattints(window, qt_app, rename_gomb)
    uj_ut = regi_ut.with_name("atnevezett" + regi_ut.suffix)
    assert varj(
        qt_app,
        lambda: uj_ut.exists()
        and not regi_ut.exists()
        and parbeszed.property("visible") is False,
    ), "a Rename gomb nem nevezte át a képet"


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTOLASOK)
def test_fajl_menu_egy_keppel_ugyanazt_a_kitoltott_parbeszedet_nyitja(
    qml_app, qt_app, magassag_elteres
):
    window, controller = _ablak_es_kijeloles(qml_app, qt_app, magassag_elteres)
    menubar = window.property("menuBar")
    _megnyit(menubar, qt_app, "&File")
    kattints(window, qt_app, _gyerek(window, "menuFileRename"))

    regi_ut = Path(str(controller.photos.filePathAt(0)))
    _parbeszed_ellenorzese(window, qt_app, regi_ut.stem)


# rontás-kontroll: renameManyField.text = "" → 6 failed before fix
