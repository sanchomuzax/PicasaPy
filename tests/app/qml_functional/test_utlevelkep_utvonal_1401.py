"""#1401 — az Útlevélkép TELJES útja, valódi kattintásokkal.

Eszközök ▸ Kísérleti ▸ Útlevélkép… → `Main.qml` → `passportController`
(hamis arc-detektorral) → vagy a hibaablak, vagy a MEGLÉVŐ nyomtatási
nézet. Az élő mérés (picasa-colab-jobs #49/#50/#54) a mérce:

- nulla/több arcnál egy OK gombos ablak, címe „Try another picture?",
  a főablak FÖLÖTT, láthatóan;
- egy arcnál párbeszéd nélkül a nyomtatási nézet: Útlevél méret, Crop to
  Fit, 1 példány, előnézet „1 / 1", és egyik kész méret sincs kijelölve.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from picasapy.faces.detector import FaceDetection, FaceLandmarks

try:
    import PySide6.QtPrintSupport  # noqa: F401

    _QTPRINTSUPPORT_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    _QTPRINTSUPPORT_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTPRINTSUPPORT_VAN,
    reason="a PySide6.QtPrintSupport modul hiányzik ezen a gépen",
)

_LANDMARKS = FaceLandmarks(
    right_eye=(0.0, 0.0), left_eye=(0.0, 0.0), nose=(0.0, 0.0),
    mouth_right=(0.0, 0.0), mouth_left=(0.0, 0.0),
)


def _arc(left, top, right, bottom) -> FaceDetection:
    return FaceDetection(
        left=left, top=top, right=right, bottom=bottom, score=0.9,
        landmarks=_LANDMARKS,
    )


class _HamisDetektor:
    available = True

    def __init__(self, faces):
        self.faces = tuple(faces)

    def detect(self, image):
        return self.faces


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kattints(window, qt_app, elem) -> None:
    """Valódi bal kattintás a vezérlő KÖZEPÉRE."""
    assert _var(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: nincs mérete, nem kattintható"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    qt_app.processEvents()


def _vizualis(window, feltetel):
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and feltetel(elem):
            return elem
        sor.extend(elem.childItems())
    return None


def _passport_vezerlo(engine, detektor):
    ctl = engine.rootContext().contextProperty("passportController")
    assert ctl is not None, "a passportController nincs bekötve"
    ctl.use_detector(detektor)
    return ctl


def _menubol_inditja(window, qt_app, ctl) -> None:
    """Kijelölés + Eszközök ▸ Kísérleti ▸ Útlevélkép… — mind KATTINTÁS."""
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    eszkozok = _vizualis(
        window,
        lambda e: "MenuBarItem" in e.metaObject().className()
        and e.property("text") == "&Tools",
    )
    assert eszkozok is not None, "az Eszközök menü nincs a menüsávon"
    _kattints(window, qt_app, eszkozok)

    kiserleti = None

    def _kiserleti_tetel():
        nonlocal kiserleti
        kiserleti = _vizualis(
            window,
            lambda e: "MenuItem" in e.metaObject().className()
            and e.property("text") == "Experimental",
        )
        return kiserleti is not None

    assert _var(qt_app, _kiserleti_tetel), "nincs Kísérleti tétel"
    _kattints(window, qt_app, kiserleti)

    tetel = _elem(window, "menuToolsPassportPhoto")
    assert _var(qt_app, lambda: tetel.isVisible() and tetel.width() > 0), (
        "az Útlevélkép tétel nem jelent meg"
    )
    assert tetel.property("enabled") is True
    _kattints(window, qt_app, tetel)
    assert ctl.waitForBackgroundWorkers(20.0)
    qt_app.processEvents()


def _hibaablak(window):
    return window.findChild(QObject, "passportErrorDialog")


def _lathato_felso_ablakok():
    return [w for w in QGuiApplication.topLevelWindows() if w.isVisible()]


class TestAHibaablak:
    @pytest.mark.parametrize(
        ("arcok", "szoveg"),
        [
            ((), "Can't find any faces"),
            (
                (_arc(10, 10, 40, 50), _arc(100, 60, 140, 110)),
                "There appear to be multiple faces.",
            ),
        ],
        ids=["nulla-arc", "tobb-arc"],
    )
    def test_latszik_a_foablak_folott_es_OK_ra_bezar(
        self, qml_app, qt_app, arcok, szoveg
    ):
        window, _controller, engine = qml_app
        ctl = _passport_vezerlo(engine, _HamisDetektor(arcok))
        _menubol_inditja(window, qt_app, ctl)

        assert _var(
            qt_app,
            lambda: _hibaablak(window) is not None
            and _hibaablak(window).property("opened") is True,
        ), "a hibaablak nem nyílt meg"
        dialog = _hibaablak(window)
        assert dialog.property("visible") is True
        assert dialog.property("title") == "Try another picture?"
        assert _elem(window, "passportErrorMessage").property("text") == szoveg

        # a párbeszéd a LÁTHATÓ főablakban él, nem egy rejtett ablakban
        gomb = _elem(window, "passportErrorOkButton")
        assert gomb.window() is window
        assert window.isVisible()
        assert gomb.isVisible()
        # nincs más látható felső ablak — csak a főablak(ok)
        idegen = [
            w.title() for w in _lathato_felso_ablakok()
            if w.title() != window.title()
        ]
        assert idegen == []
        # a nyomtatási nézet NEM nyílt meg
        nyomtatas = window.findChild(QObject, "printDialog")
        assert nyomtatas is None or nyomtatas.property("visible") is False

        _kattints(window, qt_app, gomb)
        assert _var(qt_app, lambda: dialog.property("visible") is False), (
            "az OK gomb nem zárta be a hibaablakot"
        )


class TestANyomtatasiNezet:
    def test_egy_arcnal_a_meglevo_nyomtatasi_nezet_nyilik(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        ctl = _passport_vezerlo(engine, _HamisDetektor([_arc(140, 40, 180, 90)]))
        _menubol_inditja(window, qt_app, ctl)

        nezet = None

        def _nyitva():
            nonlocal nezet
            nezet = window.findChild(QObject, "printDialog")
            return nezet is not None and nezet.property("visible") is True

        assert _var(qt_app, _nyitva), "a nyomtatási nézet nem nyílt meg"
        hiba = _hibaablak(window)
        assert hiba is None or hiba.property("opened") is not True

        assert nezet.property("passport") is True
        assert nezet.property("printSize") == "PASSPORT"
        assert nezet.property("copies") == 1
        assert nezet.property("fitMode") == "fill"
        assert _elem(nezet, "printFillRadio").property("checked") is True

        meretvalaszto = _elem(nezet, "printSizeBox")
        assert meretvalaszto.property("currentIndex") == -1, (
            "egy kész méret ki van jelölve"
        )
        assert meretvalaszto.property("displayText") == "Passport"

        assert _var(
            qt_app, lambda: _elem(nezet, "printPreviewPageText").property("text")
            == "1 / 1"
        ), _elem(nezet, "printPreviewPageText").property("text")
        assert _elem(nezet, "printSelectionText").property("text").startswith(
            "Pictures to print: 1"
        )
        # az alkalmazás-modális nézet nyitva maradva a következő teszt
        # ablakát is elzárná
        _kattints(nezet, qt_app, _elem(nezet, "printCloseButton"))
        assert _var(qt_app, lambda: nezet.property("visible") is False)

    def test_a_kovetkezo_sima_nyomtatas_mar_nem_utlevel(self, qml_app, qt_app):
        window, _controller, engine = qml_app
        ctl = _passport_vezerlo(engine, _HamisDetektor([_arc(140, 40, 180, 90)]))
        _menubol_inditja(window, qt_app, ctl)
        nezet = _elem(window, "printDialog")
        assert _var(qt_app, lambda: nezet.property("visible") is True)
        _kattints(nezet, qt_app, _elem(nezet, "printCloseButton"))
        assert _var(qt_app, lambda: nezet.property("visible") is False)

        window.setProperty("selectedIndexes", [0, 1])
        qt_app.processEvents()
        window.metaObject().invokeMethod(window, "openPrint")
        qt_app.processEvents()
        assert nezet.property("passport") is False
        assert nezet.property("printSize") != "PASSPORT"
        assert nezet.property("fitMode") == "fit"
        assert _elem(nezet, "printSizeBox").property("currentIndex") >= 0
        assert _elem(nezet, "printSelectionText").property("text").startswith(
            "Pictures to print: 2"
        )
        _kattints(nezet, qt_app, _elem(nezet, "printCloseButton"))
        assert _var(qt_app, lambda: nezet.property("visible") is False)
