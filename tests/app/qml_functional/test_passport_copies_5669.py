"""#5669 — a Passport mód megtartja a nyomtatási munka példányszámát."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_utlevelkep_utvonal_1401 import (
    _HamisDetektor,
    _arc,
    _elem,
    _kattints,
    _menubol_inditja,
    _passport_vezerlo,
)
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

#: a kiadáskép csak kérésre készül, a hívó adja a mappát
KIADASKEP_MAPPA = "PICASAPY_5669_KIADASKEP_MAPPA"

try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen",
)


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Mintázatos képekkel: a kiadásképen valódi kép látszik (agent #225)."""

    def kepek(lib):
        make_minta_jpeg(lib / "a.jpg", size=(320, 240), seed=41)
        make_minta_jpeg(lib / "b.jpg", size=(320, 240), seed=42)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepek,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _parbeszedmagassag(nyomtatas: QObject, qt_app, elteres: int) -> None:
    """A nyomtatási ablakot a tartalmi átméretezés után állítja be."""
    assert var_feltetelre(
        qt_app,
        lambda: not nyomtatas.property("meretezesFuggoben"),
        5.0,
    ), "a nyomtatási ablak tartalmi átméretezése nem fejeződött be"
    celmagassag = int(nyomtatas.height()) + elteres
    nyomtatas.setHeight(celmagassag)
    qt_app.processEvents()
    assert int(nyomtatas.height()) == celmagassag


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_passport_megtartja_a_darabszamot_es_kilepeskor_visszaallitja(
    qml_app, qt_app, magassag_elteres
):
    """Valódi kattintásokkal vált a Passport és az általános mód között."""
    window, _controller, engine = qml_app

    # Egy új nyomtatási munka az eredeti szerint egy példánnyal indul.
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    window.metaObject().invokeMethod(window, "openPrint")
    assert var_feltetelre(
        qt_app,
        lambda: _elem(window, "printDialog").property("visible") is True,
        5.0,
    )
    nyomtatas = _elem(window, "printDialog")
    _parbeszedmagassag(nyomtatas, qt_app, magassag_elteres)
    assert nyomtatas.property("copies") == 1
    assert nyomtatas.property("fitMode") == "fill"  # #5681: Crop to Fit az induló mód

    # A felhasználó a normál módjában három példányt kér.
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCopiesPlusButton"))
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCopiesPlusButton"))
    assert nyomtatas.property("copies") == 3
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCloseButton"))
    assert var_feltetelre(
        qt_app, lambda: nyomtatas.property("visible") is False, 5.0
    )

    # A Tools ▸ Experimental ▸ Passport photo... menün valódi kattintásokkal lép be.
    passport = _passport_vezerlo(
        engine, _HamisDetektor([_arc(140, 40, 180, 90)])
    )
    _menubol_inditja(window, qt_app, passport)
    assert var_feltetelre(
        qt_app, lambda: nyomtatas.property("visible") is True, 5.0
    )
    _parbeszedmagassag(nyomtatas, qt_app, magassag_elteres)
    assert nyomtatas.property("passport") is True
    assert nyomtatas.property("fitMode") == "fill"
    assert nyomtatas.property("copies") == 3
    mappa = os.environ.get(KIADASKEP_MAPPA)
    if magassag_elteres == 0 and mappa:
        qt_app.processEvents()
        kep = nyomtatas.grabWindow()
        assert not kep.isNull(), "a kiadáskép üres"
        cel = Path(mappa) / "utlevel_peldanyszam_5669.png"
        assert kep.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"

    # Az útlevélmód alatt módosított érték sem írja át az általános módét.
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCopiesPlusButton"))
    assert nyomtatas.property("copies") == 4
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCloseButton"))
    assert var_feltetelre(
        qt_app, lambda: nyomtatas.property("visible") is False, 5.0
    )

    window.metaObject().invokeMethod(window, "openPrint")
    assert var_feltetelre(
        qt_app, lambda: nyomtatas.property("visible") is True, 5.0
    )
    _parbeszedmagassag(nyomtatas, qt_app, magassag_elteres)
    assert nyomtatas.property("passport") is False
    assert nyomtatas.property("fitMode") == "fill"
    assert nyomtatas.property("copies") == 3
    _kattints(nyomtatas, qt_app, _elem(nyomtatas, "printCloseButton"))
    assert var_feltetelre(
        qt_app, lambda: nyomtatas.property("visible") is False, 5.0
    )
