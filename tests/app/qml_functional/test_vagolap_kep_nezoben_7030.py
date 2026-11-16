"""#7030: a nézőben a Másolás KÉPET tesz a vágólapra, a rácsban fájlokat.

Az eredeti Picasa 3.9 a szerkesztőben a szerkesztésekkel együtt kiszámolt
képet teszi a vágólapra, `CF_BITMAP`-ként (`0x00a706f0`, `0x00a70776`,
hívó: `0x0069b000`, #7028). A rácsban a Másolás változatlanul a fájlokat
adja (#1526).

Minden bemenet valódi: a Ctrl+C `QTest.keyClick`-kel érkezik az ablakra, a
Szerkesztés menü tétele valódi egérkattintással indul. A rendszervágólapot
a teszt nem olvassa (fej nélkül nincs tulajdonosa, és a Qt-vágólap ott
szegmenshibát okozott), hanem azt, AMIT a vezérlők feltennének.
"""

from __future__ import annotations

import time
from pathlib import Path

import numpy as np
import pytest
from PIL import Image
from PySide6.QtCore import QObject, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

from conftest import _build_qml_app
from tests.app.qml_functional._menusor_maradek_5150_helpers import tetel_kattintasa

# rontás-kontroll: a `MainLibrarySelectionState.qml` `copyActionToClipboard`
# nézős ága kikapcsolva (`if (false && hostWindow.viewerOpen)`) -> a két
# nézős teszt bukik (nem kerül kép a vágólapra, a fájl-vágólap viszont
# feltöltődik); a két rácsos teszt zöld marad


def _szines_kepek(lib: Path) -> None:
    y, x = np.indices((90, 120))
    for nev, eltolas in (("a.png", 0), ("b.png", 40)):
        rgb = np.stack(
            (
                (x * 2 + y + eltolas) % 256,
                (y * 3 + x + eltolas) % 256,
                (x + y * 2 + eltolas) % 256,
            ),
            axis=2,
        ).astype(np.uint8)
        Image.fromarray(rgb).save(lib / nev)


@pytest.fixture
def kep_app(qt_app, tmp_path, request):
    """Teljes app. A menüsor Python-burkát a fixture tartja a teszt végéig:
    a GC-je különben megsemmisítené az ablakot (ld. `app_epitese`)."""
    gen = _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_szines_kepek, keep_modul=request.module
    )
    window, controller, engine = next(gen)
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    yield window, controller, engine
    del menu_bar
    next(gen, None)


def _varj(qt_app, feltetel, leiras: str, timeout: float = 10.0) -> None:
    hatarido = time.monotonic() + timeout
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    pytest.fail(f"Határidőn belül nem teljesült: {leiras}")


def _tomb(kep: QImage) -> np.ndarray:
    rgb = kep.convertToFormat(QImage.Format.Format_RGB888)
    sorhossz = rgb.bytesPerLine()
    nyers = np.frombuffer(rgb.constBits(), dtype=np.uint8, count=sorhossz * rgb.height())
    return (
        nyers.reshape(rgb.height(), sorhossz)[:, : rgb.width() * 3]
        .reshape(rgb.height(), rgb.width(), 3)
        .copy()
    )


def _szerkeszto(engine):
    return engine.rootContext().contextProperty("editController")


def _fajlmuveletek(engine):
    return engine.rootContext().contextProperty("fileOpsController")


def _szerkesztett_nezo(window, engine, qt_app):
    """Megnyitott néző az első képen, fekete-fehér effekttel, kész előnézettel."""
    window.setProperty("viewerOpen", True)
    nezo = window.findChild(QObject, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    szerkeszto = _szerkeszto(engine)
    _varj(
        qt_app,
        lambda: szerkeszto.property("previewSource") != "",
        "a néző szerkesztési munkamenete megnyílik",
    )
    szerkeszto.applyEffect("bw")
    assert szerkeszto.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()
    return nezo, szerkeszto


def _azonos_a_megjelenitettel(szerkeszto) -> None:
    vagolapon = szerkeszto._vagolap_kepe()
    assert vagolapon is not None and not vagolapon.isNull(), "nem került kép a vágólapra"
    megjelenitett = szerkeszto._provider.requestImage(szerkeszto._kulcs, None, None)
    assert (vagolapon.width(), vagolapon.height()) == (
        megjelenitett.width(),
        megjelenitett.height(),
    ), "a vágólap-kép mérete eltér a megjelenített képétől"
    felvett, mutatott = _tomb(vagolapon), _tomb(megjelenitett)
    magassag, szelesseg = felvett.shape[:2]
    for sor, oszlop in (
        (0, 0),
        (0, szelesseg - 1),
        (magassag // 2, szelesseg // 2),
        (magassag - 1, 0),
        (magassag - 1, szelesseg - 1),
        (17, 63),
    ):
        assert felvett[sor, oszlop].tolist() == mutatott[sor, oszlop].tolist(), (
            f"a ({oszlop}, {sor}) képpont nem egyezik a megjelenített képpel"
        )
    # a szerkesztés (fekete-fehér) a vágólap-képen is ott van
    kulonbseg = np.abs(felvett[..., 0].astype(int) - felvett[..., 1].astype(int)).max()
    assert kulonbseg <= 2, f"a vágólap-kép nem a szerkesztett (fekete-fehér) kép: {kulonbseg}"


class TestNezoMasolas:
    def test_ctrl_c_a_szerkesztett_kepet_teszi_a_vagolapra(self, kep_app, qt_app):
        window, _controller, engine = kep_app
        _nezo, szerkeszto = _szerkesztett_nezo(window, engine, qt_app)

        QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        qt_app.processEvents()

        _azonos_a_megjelenitettel(szerkeszto)
        assert _fajlmuveletek(engine)._vagolap_adat is None, (
            "a nézőben a Ctrl+C nem tehet fájl-hivatkozást a vágólapra"
        )

    def test_a_szerkesztes_menu_masolasa_is_a_szerkesztett_kepet_teszi_fel(
        self, kep_app, qt_app
    ):
        window, _controller, engine = kep_app
        _nezo, szerkeszto = _szerkesztett_nezo(window, engine, qt_app)

        tetel_kattintasa(window, qt_app, "&Edit", "menuEditCopy")
        qt_app.processEvents()

        _azonos_a_megjelenitettel(szerkeszto)
        assert _fajlmuveletek(engine)._vagolap_adat is None, (
            "a nézőben a Szerkesztés ▸ Másolás nem tehet fájl-hivatkozást a vágólapra"
        )


class TestRacsMasolas:
    def test_a_racsban_a_ctrl_c_fajlokat_tesz_a_vagolapra(self, kep_app, qt_app):
        window, controller, engine = kep_app
        window.setProperty("selectedIndexes", [0])
        qt_app.processEvents()
        kijelolt = Path(controller.photos.filePathAt(0))

        QTest.keyClick(window, Qt.Key.Key_C, Qt.KeyboardModifier.ControlModifier)
        qt_app.processEvents()

        adat = _fajlmuveletek(engine)._vagolap_adat
        assert adat is not None and adat.hasUrls(), "a rácsban a Ctrl+C fájlokat másol"
        assert [Path(u.toLocalFile()) for u in adat.urls()] == [kijelolt]
        kep = _szerkeszto(engine)._vagolap_kepe()
        assert kep is None or kep.isNull(), "a rácsban nem kerülhet képadat a vágólapra"

    def test_a_racsban_a_menu_masolasa_fajlokat_tesz_a_vagolapra(self, kep_app, qt_app):
        window, controller, engine = kep_app
        window.setProperty("selectedIndexes", [0])
        qt_app.processEvents()
        kijelolt = Path(controller.photos.filePathAt(0))

        tetel_kattintasa(window, qt_app, "&Edit", "menuEditCopy")
        qt_app.processEvents()

        adat = _fajlmuveletek(engine)._vagolap_adat
        assert adat is not None and adat.hasUrls()
        assert [Path(u.toLocalFile()) for u in adat.urls()] == [kijelolt]
        kep = _szerkeszto(engine)._vagolap_kepe()
        assert kep is None or kep.isNull()
