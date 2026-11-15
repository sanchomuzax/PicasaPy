"""#6987: az E-mail parancs valódi kattintással, az eredeti Picasa 3.9 szerint.

- 21 kijelölt képnél megjelenik a kérdés (`CThumbUI::OutputBottleneck`,
  `0x00531550`), a Mégse nem készít elő semmit, az OK folytat; 20 vagy
  kevesebb képnél nincs kérdés;
- a saját levelező választásakor (`EmailPrepType = 3`, `0x00742a2c`) nincs
  belső szerkesztőpanel: a levelező közvetlenül nyílik a csatolmányokkal;
- a tárgy és a törzs a képszám szerint, a hivatalos magyar szöveggel
  töltődik, a reklámsor (`IDS_MAPITAGLINE`) nélkül.

A levelező indítása a `_which`/`_popen` modulszintű fogantyún át cserélt:
valódi levelező nem indul.
"""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, QTranslator, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg

_DARAB = 21


class _Folyamat:
    """A levelező-indítás hamis folyamata: azonnal, 0-s kóddal kilép."""

    def wait(self, timeout=None):
        return 0


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    """A valódi főablak 21 képpel, e-mail-vezérlővel és magyar fordítással."""
    import picasapy.app.application as app_module

    fordito = QTranslator(qt_app)
    assert fordito.load(str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm"))
    qt_app.installTranslator(fordito)

    def kepeket_keszit(mappa):
        for i in range(_DARAB):
            make_jpeg(mappa / f"k{i:02d}.jpg", size=(64, 48))

    try:
        yield from _build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=kepeket_keszit,
            email_vezerlo=True,
            keep_modul=request.module,
        )
    finally:
        qt_app.removeTranslator(fordito)


@pytest.fixture
def levelezo(monkeypatch, tmp_path):
    """Az előkészítés és a levelező-indítás nyilvántartása, valódi folyamat
    nélkül."""
    import picasapy.app.email_controller as email_module

    class Nyilvantartas:
        def __init__(self):
            self.elokeszitesek = []
            self.parancsok = []

    nyilvantartas = Nyilvantartas()

    def mkdtemp(prefix):
        mappa = tmp_path / f"csatolmanyok-{len(nyilvantartas.elokeszitesek)}"
        mappa.mkdir()
        nyilvantartas.elokeszitesek.append(mappa)
        return str(mappa)

    monkeypatch.setattr(email_module, "_mkdtemp", mkdtemp)
    monkeypatch.setattr(email_module, "_which", lambda _nev: "/usr/bin/xdg-email")
    monkeypatch.setattr(
        email_module,
        "_popen",
        lambda argv: nyilvantartas.parancsok.append(list(argv)) or _Folyamat(),
    )
    return nyilvantartas


def _var(window, nev, qt_app, *, ido=5.0):
    lejar = time.monotonic() + ido
    while time.monotonic() < lejar:
        qt_app.processEvents()
        elem = window.findChild(QObject, nev)
        if elem is not None and bool(elem.property("visible")):
            return elem
        QTest.qWait(10)
    pytest.fail(f"a várt QML-elem nem vált láthatóvá: {nev}")


def _elem(window, nev):
    elem = window.findChild(QQuickItem, nev)
    assert elem is not None, f"hiányzó, kirajzolt vezérlő: {nev}"
    return elem


def _kattint(window, elem, qt_app):
    assert elem.isEnabled(), f"a vezérlő le van tiltva: {elem.objectName()}"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    assert 0 <= pont.x() < window.width() and 0 <= pont.y() < window.height()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()
    QTest.qWait(30)
    qt_app.processEvents()


def _kijelol(window, darab, qt_app):
    window.setProperty("selectedIndexes", list(range(darab)))
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _vezerlo(engine):
    return engine.rootContext().contextProperty("emailController")


def _csatolmanyok(argv):
    return [argv[i + 1] for i, elem in enumerate(argv) if elem == "--attach"]


def test_a_21_kep_kerdezi_a_megse_nem_keszit_elo_az_ok_folytat(
    qml_app, qt_app, levelezo
):
    window, app_controller, engine = qml_app
    assert len(app_controller.photos.photos) == _DARAB
    _vezerlo(engine).setUseDefaultClient(True)
    _kijelol(window, _DARAB, qt_app)

    _kattint(window, _elem(window, "trayEmailButton"), qt_app)
    kerdes = _var(window, "emailCountConfirmDialog", qt_app)
    assert kerdes.property("title") == "Jóváhagyás"
    assert (
        _elem(kerdes, "emailCountConfirmMessageLabel").property("text")
        == "21 fájlt elküld e-mailben?"
    )
    assert _elem(kerdes, "emailCountConfirmYesButton").property("text") == "OK"
    assert (
        _elem(kerdes, "emailCountConfirmCancelButton").property("text") == "Mégse"
    )
    assert levelezo.elokeszitesek == [], "a kérdés előtt már készült előkészítés"

    # Mégse: semmi nem készül elő, a levelező nem indul
    _kattint(window, _elem(kerdes, "emailCountConfirmCancelButton"), qt_app)
    assert not bool(kerdes.property("visible"))
    assert levelezo.elokeszitesek == []
    assert levelezo.parancsok == []

    # újra, most OK: az előkészítés és a levelező indul
    _kattint(window, _elem(window, "trayEmailButton"), qt_app)
    kerdes = _var(window, "emailCountConfirmDialog", qt_app)
    _kattint(window, _elem(kerdes, "emailCountConfirmYesButton"), qt_app)
    assert not bool(kerdes.property("visible"))
    assert len(levelezo.elokeszitesek) == 1
    assert len(levelezo.parancsok) == 1
    assert len(_csatolmanyok(levelezo.parancsok[0])) == _DARAB


def test_a_20_kepnel_nincs_kerdes_es_megy_a_levelezo(qml_app, qt_app, levelezo):
    window, _app_controller, engine = qml_app
    _vezerlo(engine).setUseDefaultClient(True)
    _kijelol(window, 20, qt_app)

    _kattint(window, _elem(window, "trayEmailButton"), qt_app)

    assert window.findChild(QObject, "emailCountConfirmDialog") is None, (
        "20 képnél kérdés jelent meg"
    )
    assert len(levelezo.parancsok) == 1
    assert len(_csatolmanyok(levelezo.parancsok[0])) == 20


def test_a_sajat_levelezo_belso_panel_nelkul_nyilik_kepszam_szerinti_szoveggel(
    qml_app, qt_app, levelezo
):
    window, _app_controller, engine = qml_app
    _vezerlo(engine).setUseDefaultClient(True)
    _kijelol(window, 1, qt_app)

    _kattint(window, _elem(window, "trayEmailButton"), qt_app)

    assert window.findChild(QObject, "emailChoiceDialog") is None, (
        "a saját levelezős ág választó vagy szerkesztő párbeszédet nyitott"
    )
    assert len(levelezo.parancsok) == 1
    argv = levelezo.parancsok[0]
    assert len(_csatolmanyok(argv)) == 1
    assert argv[argv.index("--subject") + 1] == "Küldök egy képet"
    assert argv[argv.index("--body") + 1] == "Ön 1 képet kapott.\n\n"
    # a reklámsor (`IDS_MAPITAGLINE`) nincs a levélben; a melléklet útvonalát
    # nem vizsgáljuk, abban a munkafa neve szerepelhet
    levelszoveg = (
        argv[argv.index("--subject") + 1] + argv[argv.index("--body") + 1]
    ).lower()
    assert "picasa" not in levelszoveg and "google" not in levelszoveg


def test_tobb_kepnel_a_targy_es_a_torzs_a_kepszamot_mondja(
    qml_app, qt_app, levelezo
):
    window, _app_controller, engine = qml_app
    _vezerlo(engine).setUseDefaultClient(True)
    _kijelol(window, 3, qt_app)

    _kattint(window, _elem(window, "trayEmailButton"), qt_app)

    argv = levelezo.parancsok[0]
    assert argv[argv.index("--subject") + 1] == "Küldök 3 képet"
    assert argv[argv.index("--body") + 1] == "Ön 3 képet kapott.\n\n"


def test_a_kerdezz_mod_valasztasa_utan_is_kozvetlenul_nyilik_a_levelezo(
    qml_app, qt_app, levelezo
):
    window, _app_controller, engine = qml_app
    _vezerlo(engine).setUseDefaultClient(False)
    _kijelol(window, 2, qt_app)

    _kattint(window, _elem(window, "trayEmailButton"), qt_app)
    dialog = _var(window, "emailChoiceDialog", qt_app)
    assert levelezo.parancsok == [], "a választás előtt elindult a levelező"
    _kattint(window, _elem(dialog, "emailChoiceDefaultButton"), qt_app)

    assert not bool(dialog.property("visible"))
    assert len(levelezo.parancsok) == 1
    argv = levelezo.parancsok[0]
    assert "--to" not in argv
    assert argv[argv.index("--subject") + 1] == "Küldök 2 képet"
    assert len(_csatolmanyok(argv)) == 2
    assert Path(_csatolmanyok(argv)[0]).is_file()
