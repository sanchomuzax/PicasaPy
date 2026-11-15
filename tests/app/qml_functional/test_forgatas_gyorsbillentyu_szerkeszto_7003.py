"""A forgatás gyorsbillentyűi és a szerkesztő képforgatása (#7003).

Az eredeti Picasa 3.9 forgatási útja (`0x005e60d0` -> `0x005ee6e0`) a TELJES
kijelölést forgatja sorban, üres kijelölésnél pedig megszólal
(`IDS_MUST_SELECT_TO_ROT`). A szerkesztőben (`editpanel`, `editoneup`) külön
balra és jobbra képforgató gomb van, ami a FOTÓT forgatja.

Itt minden próba valódi Qt-billentyűleütéssel vagy valódi egérkattintással
fut a teljes főablakon; a forgatás eredménye a modell `rotate_steps` mezőjén
(a `.picasa.ini` `rotate=` kulcsának tükre) olvasható le.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_HIVATALOS_UZENET = "Must have selected images to rotate."


@pytest.fixture
def forgatas_app(qt_app, tmp_path):
    """Három képes mappa: kell egy többes kijelölés és egy kimaradó kép."""

    def harom_kep(mappa) -> None:
        for nev in ("a.jpg", "b.jpg", "c.jpg"):
            make_jpeg(mappa / nev, size=(320, 160))

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=harom_kep)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _objektum(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _aktivalj(window, qt_app) -> None:
    window.show()
    window.requestActivate()
    assert _varj(qt_app, lambda: window.isActive()), "a főablak nem aktiválódott"


def _kijelol(window, qt_app, sorok: list[int]) -> None:
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[-1] if sorok else -1)
    qt_app.processEvents()


def _lepesek(controller) -> list[int]:
    return [foto.rotate_steps for foto in controller.photos.photos]


def _billentyu(window, shift: bool) -> None:
    modosito = Qt.KeyboardModifier.ControlModifier
    if shift:
        modosito |= Qt.KeyboardModifier.ShiftModifier
    QTest.keyClick(window, Qt.Key.Key_R, modosito)


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


def _keszitsd_elo(window, controller, qt_app) -> None:
    _aktivalj(window, qt_app)
    assert _varj(qt_app, lambda: controller.photos.rowCount() >= 3), (
        "a három kép nem töltődött be"
    )
    assert _lepesek(controller)[:3] == [0, 0, 0]


def _nyisd_meg_a_szerkesztot(window, qt_app, sor: int) -> QObject:
    """A szerkesztő (NEM gyorsnéző) megnyitása a megadott soron."""
    window.setProperty("viewerOpen", True)
    nezo = _objektum(window, "photoViewer")
    nezo.setProperty("currentIndex", sor)
    assert _varj(
        qt_app,
        lambda: nezo.isVisible()
        and nezo.property("controllerReady")
        and nezo.property("quickViewerMode") is False,
    ), "a szerkesztő nézője nem nyílt meg"
    return nezo


class TestRacsGyorsbillentyu:
    def test_ctrl_r_a_TELJES_kijelolest_forgatja_jobbra(
        self, forgatas_app, qt_app
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [0, 1, 2])

        _billentyu(window, shift=False)

        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [1, 1, 1]), (
            "a Ctrl+R nem mindhárom kijelölt képet forgatta jobbra: "
            f"{_lepesek(controller)}"
        )

    def test_ctrl_shift_r_a_TELJES_kijelolest_forgatja_balra(
        self, forgatas_app, qt_app
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [0, 1, 2])

        _billentyu(window, shift=True)

        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [3, 3, 3]), (
            "a Ctrl+Shift+R nem mindhárom kijelölt képet forgatta balra: "
            f"{_lepesek(controller)}"
        )

    def test_a_kijelolesen_kivuli_kep_nem_forog(self, forgatas_app, qt_app):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [0, 1])

        _billentyu(window, shift=False)

        assert _varj(qt_app, lambda: _lepesek(controller)[:2] == [1, 1])
        qt_app.processEvents()
        assert _lepesek(controller)[2] == 0, "a nem kijelölt kép is elfordult"

    def test_egyetlen_kijeloles_tovabbra_is_egy_kepet_forgat(
        self, forgatas_app, qt_app
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [1])

        _billentyu(window, shift=False)

        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [0, 1, 0])


class TestUresKijeloles:
    @pytest.mark.parametrize("shift", [False, True])
    def test_ures_kijelolesnel_a_HIVATALOS_uzenet_jelenik_meg(
        self, forgatas_app, qt_app, shift
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [])
        sav = _objektum(window, "picasaNotifier")
        assert sav.property("cellCount") == 0
        jelzesek: list[int] = []
        controller.rotationNeedsSelection.connect(lambda: jelzesek.append(1))

        _billentyu(window, shift=shift)

        assert _varj(qt_app, lambda: sav.property("cellCount") == 1), (
            "üres kijelölésnél a forgatás billentyűje némán visszatért"
        )
        assert jelzesek == [1]
        assert sav.property("lastTitle") == _HIVATALOS_UZENET
        assert _lepesek(controller)[:3] == [0, 0, 0]


class TestNezo:
    def test_nezoben_csak_az_AKTUALIS_kep_forog(self, forgatas_app, qt_app):
        """A rács kijelölése a néző mögött megmarad, de nem a cél."""
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [0, 1])
        nezo = _nyisd_meg_a_szerkesztot(window, qt_app, 2)
        nezo.forceActiveFocus()
        assert _varj(qt_app, lambda: nezo.property("activeFocus") is True)

        _billentyu(window, shift=False)

        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [0, 0, 1]), (
            "nézőben a Ctrl+R nem csak az aktuális képet forgatta: "
            f"{_lepesek(controller)}"
        )
        _billentyu(window, shift=True)
        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [0, 0, 0])


class TestSzerkeszto:
    @pytest.mark.parametrize(
        ("gomb", "vart"),
        [("trayRotateRight", 1), ("trayRotateLeft", 3)],
    )
    def test_a_szerkesztoben_a_forgatogomb_a_FOTOT_forgatja(
        self, forgatas_app, qt_app, gomb, vart
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _kijelol(window, qt_app, [0])
        _nyisd_meg_a_szerkesztot(window, qt_app, 1)
        elem = _objektum(window, gomb)

        _kattint(window, elem, qt_app)

        assert _varj(qt_app, lambda: _lepesek(controller)[:3] == [0, vart, 0]), (
            f"a szerkesztő {gomb} gombja nem forgatta a fotót: "
            f"{_lepesek(controller)}"
        )

    def test_a_vagokeret_Rotate_gombja_nem_forgatja_a_fotot(
        self, forgatas_app, qt_app
    ):
        window, controller, _engine = forgatas_app
        _keszitsd_elo(window, controller, qt_app)
        _nyisd_meg_a_szerkesztot(window, qt_app, 1)
        panel = _objektum(window, "viewerEditorPanel")
        _kattint(window, _objektum(window, "editToolCrop"), qt_app)
        assert _varj(qt_app, lambda: panel.property("cropActive") is True), (
            "a vágó eszköz nem aktiválódott"
        )
        kert: list[int] = []
        panel.cropRotateRequested.connect(lambda: kert.append(1))

        _kattint(window, _objektum(window, "cropRotateButton"), qt_app)

        assert kert == [1], "a Rotate gomb kattintása nem jutott el a panelig"
        qt_app.processEvents()
        assert _lepesek(controller)[:3] == [0, 0, 0], (
            "a vágókeret Rotate gombja a fotót forgatta"
        )
