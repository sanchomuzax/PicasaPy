"""#6945: a megerősített kilépést a főablak bezárási kérése nem vonhatja vissza.

A `Qt.quit()` a Qt-tól bezárási kérést (`Close` esemény) küld a főablaknak. A
háttérmunka miatti kérdés „Kilépés most" gombja után az `onClosing` ezt futó
munka mellett újra visszavonta, és újra feltette a kérdést: a kilépés sosem
ért véget (a külön folyamatban futó, valódi kilépést a
`test_kilepes_most_6945.py` méri).

Itt a folyamaton belüli rész: a valódi gombnyomás után a vezérlő megjegyzi a
megerősítést, és az ezt követő bezárási kérést elfogadja.
"""

from __future__ import annotations

import threading
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.app.worker_thread import BackgroundWorkerMixin
from support.menubar_components_6016 import main_sources
from support.varakozas import var_feltetelre

_COMMANDS = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainWindowCommands.qml"
).read_text(encoding="utf-8")
_IMPORT_ACTIONS = (
    Path(__file__).resolve().parents[3]
    / "src/picasapy/app/qml/PicasaPy/MainWindowImportActions.qml"
).read_text(encoding="utf-8")
_MAIN = main_sources()


class _Tarto(BackgroundWorkerMixin):
    pass


class _KilepesFigyelo:
    """A `Qt.quit()` a motor `quit` jelzését adja; a próba processzében nincs futó
    eseményhurok, tehát ez a jelzés nem zár be semmit."""

    def __init__(self, engine):
        self.szam = 0
        engine.quit.connect(self._jelzes)

    def _jelzes(self) -> None:
        self.szam += 1


@pytest.fixture
def futo_munka():
    """Egy sosem végződő, nyilvántartott háttérszál: a kilépéskor kérdezni kell."""
    felenged = threading.Event()
    tarto = _Tarto()
    tarto._start_background(felenged.wait, name="picasapy-proba-export")
    yield tarto
    felenged.set()
    assert tarto.waitForBackgroundWorkers(30.0)


def _gyerek(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kerdes_nyitva(window, qt_app) -> bool:
    return var_feltetelre(
        qt_app,
        lambda: (
            (kerdes := window.findChild(QObject, "exitConfirm")) is not None
            and kerdes.property("opened") is True
        ),
        10.0,
    )


def _kattints(window, qt_app, nev: str) -> None:
    """Valódi egérkattintás a vezérlő közepére."""
    elem = _gyerek(window, nev)
    kozep = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    )
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


class TestAMegerositettKilepes:
    def test_a_kilepes_most_gomb_megjegyzi_a_megerositest(
        self, qml_app, qt_app, futo_munka
    ):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        QMetaObject.invokeMethod(window, "kilepes", Qt.ConnectionType.DirectConnection)
        assert _kerdes_nyitva(window, qt_app), "a háttérmunka miatti kérdés nem jelent meg"
        assert window.property("kilepesMegerositve") is False

        _kattints(window, qt_app, "exitYesButton")

        assert figyelo.szam == 1, "a „Kilépés most” nem hívta a Qt.quit()-et"
        assert window.property("kilepesMegerositve") is True

    def test_a_megerositest_kovetoen_a_bezarasi_kerest_elfogadja(
        self, qml_app, qt_app, futo_munka
    ):
        """A Qt a `Qt.quit()` után bezárási kérést küld a főablaknak. Ezt az
        ablak `close()`-a adja vissza: elfogadás esetén az ablak eltűnik."""
        window, _controller, _engine = qml_app
        QMetaObject.invokeMethod(window, "kilepes", Qt.ConnectionType.DirectConnection)
        assert _kerdes_nyitva(window, qt_app)
        _kattints(window, qt_app, "exitYesButton")
        assert window.property("kilepesMegerositve") is True

        window.close()
        qt_app.processEvents()

        assert not window.isVisible(), (
            "a megerősített kilépést a bezárási kérés újra visszavonta"
        )

    def test_megerosites_nelkul_a_futo_munka_visszavonja_a_bezarast(
        self, qml_app, qt_app, futo_munka
    ):
        """Az ablak „X”-e a megerősítés ELŐTT továbbra is kérdez."""
        window, _controller, _engine = qml_app

        window.close()
        qt_app.processEvents()

        assert window.isVisible()
        assert _kerdes_nyitva(window, qt_app)
        assert window.property("kilepesMegerositve") is False

    def test_a_kerdes_Folytatas_gombja_nem_erositi_meg_a_kilepest(
        self, qml_app, qt_app, futo_munka
    ):
        window, _controller, engine = qml_app
        figyelo = _KilepesFigyelo(engine)
        QMetaObject.invokeMethod(window, "kilepes", Qt.ConnectionType.DirectConnection)
        assert _kerdes_nyitva(window, qt_app)

        _kattints(window, qt_app, "exitNoButton")

        assert figyelo.szam == 0
        assert window.property("kilepesMegerositve") is False


class TestAForras:
    """A kötések helye: a megerősítés a `Qt.quit()` ELŐTT áll be, mindkét kilépési
    út (menü és ablak „X”-e) ugyanazt a jelzőt olvassa."""

    def test_a_megerosites_a_quit_elott_all(self):
        kezd = _COMMANDS.index("onConfirmed: {")
        blokk = _COMMANDS[kezd : kezd + 200]
        assert blokk.index("kilepesMegerositve = true") < blokk.index("Qt.quit()")

    def test_a_menu_es_az_ablak_x_e_ugyanazt_a_jelzot_olvassa(self):
        kilepes = _IMPORT_ACTIONS[
            _IMPORT_ACTIONS.index("function kilepes(") :
        ][:800]
        ablak = _MAIN[_MAIN.index("onClosing:") :][:500]
        assert "kilepesMegerositve" in kilepes
        assert "kilepesMegerositve" in ablak

    def test_a_visszavont_bezaras_torli_a_megerositest(self):
        """Ha az „aa” kapu a bezárást mégis visszavonja, a megerősítés nem maradhat
        érvényben egy későbbi, másik bezáráshoz."""
        ablak = _MAIN[_MAIN.index("onClosing:") :][:500]
        torles = ablak.index("window.kilepesMegerositve = false")
        visszavonas = ablak.index("close.accepted = false")
        assert torles < visszavonas
