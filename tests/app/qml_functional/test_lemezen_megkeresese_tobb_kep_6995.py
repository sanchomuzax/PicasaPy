"""#6995: a Locate on Disk TÖBB kijelölt képnél mappánként egy fájlkezelő-ablakot nyit.

Az eredeti `0x005c85e0` a kijelölt képek szülőmappáit összegyűjti, mappánként
egyszer veszi (`0x005c8754`-`0x005c87b5`), majd a `0x005c8dc4`-`0x005c8dee`
ciklusban minden érintett mappához külön ablakot nyit az adott mappa ELSŐ
kijelölt elemére állva (`0x00981280`).

Mind a négy belépő valódi bemenettel indul: a Fájl menü tétele és a Ctrl+Enter
(`QTest.keyClick`), a kép helyi menüje és a tálca helyi menüje (`QTest.mouseClick`).
A fájlkezelő indítása a `picasapy.app.fileops_controller` modulszintű
`reveal_in_file_manager` fogantyúján át megy; a teszt azt cseréli, és a hívásait
számolja, valódi fájlkezelő nem indul. A mérés a hívások SZÁMÁT és sorrendjét
állítja, a fájlkezelő ablakának vizuális megjelenését nem méri.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.fileops_controller as fileops_modul
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    MAPPA,
    MASIK,
    app_epitese,
    keszits_ket_mappat,
)
from tests.app.qml_functional._menusor_maradek_5150_helpers import billentyu, tetel_kattintasa
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    jobbklikk_fotón,
    kijelol,
    varj,
)
from tests.app.qml_functional._racs_maradek_5150_helpers import kattint

_CTRL = Qt.KeyboardModifier.ControlModifier


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path, kepeket_keszit=keszits_ket_mappat)


@pytest.fixture
def megnyitva(monkeypatch) -> list[Path]:
    """A fájlkezelő-fogantyú helyettesítője: a kapott utakat gyűjti."""
    lista: list[Path] = []
    monkeypatch.setattr(
        fileops_modul, "reveal_in_file_manager", lambda ut: lista.append(Path(ut))
    )
    return lista


def _betolt(window, qt_app, controller) -> Path:
    """Megjeleníti az ablakot; a rácson MINDKÉT mappa képei látszanak."""
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.setFolderSort("name")
    assert varj(qt_app, lambda: len(controller.photos.photos) == 4), (
        "a két mappa képei nem töltődtek be a rácsra"
    )
    return Path(str(controller.watchedFolders[0]))


def _sor(controller, gyoker: Path, mappa: str, nev: str) -> int:
    sor = int(controller.photos.rowOfPath(str(gyoker / mappa / nev)))
    assert sor >= 0, f"a kép nincs a rácsban: {mappa}/{nev}"
    return sor


def _tobb_mappabol(window, qt_app, controller) -> tuple[list[int], list[Path]]:
    """Három kijelölt kép két mappából, FORDÍTOTT kattintási sorrendben.

    Visszaadja a kijelölt sorokat és a várt megnyitásokat: mappánként a rács
    szerinti ELSŐ kijelölt kép, a mappák a rács sorrendjében."""
    gyoker = _betolt(window, qt_app, controller)
    c = _sor(controller, gyoker, MAPPA, "c_kozepes.jpg")
    a = _sor(controller, gyoker, MAPPA, "a_nagy.jpg")
    d = _sor(controller, gyoker, MASIK, "d_nagy.jpg")
    sorok = [d, c, a]
    kijelol(window, qt_app, sorok)
    vart = sorted(
        [gyoker / MAPPA / "a_nagy.jpg", gyoker / MASIK / "d_nagy.jpg"],
        key=lambda ut: _sor(controller, gyoker, ut.parent.name, ut.name),
    )
    return sorok, vart


def _egy_mappabol(window, qt_app, controller) -> tuple[list[int], list[Path]]:
    """Három kijelölt kép EGY mappából, fordított kattintási sorrendben."""
    gyoker = _betolt(window, qt_app, controller)
    sorok = [
        _sor(controller, gyoker, MAPPA, "c_kozepes.jpg"),
        _sor(controller, gyoker, MAPPA, "b_kicsi.jpg"),
        _sor(controller, gyoker, MAPPA, "a_nagy.jpg"),
    ]
    kijelol(window, qt_app, sorok)
    return sorok, [gyoker / MAPPA / "a_nagy.jpg"]


class TestFajlMenu:
    def test_egy_mappabol_tobb_kep_egyetlen_ablakot_nyit_az_elso_kepre(
        self, app, qt_app, megnyitva
    ):
        window, controller, _motor = app
        _sorok, vart = _egy_mappabol(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "&File", "menuFileLocate")

        assert varj(qt_app, lambda: len(megnyitva) >= 1), (
            "a Fájl ▸ Locate on Disk nem indította a fájlkezelőt"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem egyetlen, az első képre álló ablak nyílt: {megnyitva}"

    def test_tobb_mappabol_mappankent_egy_ablak_nyilik(self, app, qt_app, megnyitva):
        window, controller, _motor = app
        _sorok, vart = _tobb_mappabol(window, qt_app, controller)

        tetel_kattintasa(window, qt_app, "&File", "menuFileLocate")

        assert varj(qt_app, lambda: len(megnyitva) >= 2), (
            f"a két mappa közül nem mindegyikhez nyílt ablak: {megnyitva}"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem mappánként egy ablak nyílt: {megnyitva}"


class TestCtrlEnter:
    def test_egy_mappabol_tobb_kep_egyetlen_ablakot_nyit_az_elso_kepre(
        self, app, qt_app, megnyitva
    ):
        window, controller, _motor = app
        _sorok, vart = _egy_mappabol(window, qt_app, controller)

        billentyu(window, qt_app, "shortcutLocateOnDisk", Qt.Key.Key_Return, _CTRL)

        assert varj(qt_app, lambda: len(megnyitva) >= 1), (
            "a Ctrl+Enter nem indította a fájlkezelőt"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem egyetlen, az első képre álló ablak nyílt: {megnyitva}"

    def test_tobb_mappabol_mappankent_egy_ablak_nyilik(self, app, qt_app, megnyitva):
        window, controller, _motor = app
        _sorok, vart = _tobb_mappabol(window, qt_app, controller)

        billentyu(window, qt_app, "shortcutLocateOnDisk", Qt.Key.Key_Return, _CTRL)

        assert varj(qt_app, lambda: len(megnyitva) >= 2), (
            f"a két mappa közül nem mindegyikhez nyílt ablak: {megnyitva}"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem mappánként egy ablak nyílt: {megnyitva}"


class TestKepHelyiMenu:
    def test_egy_mappabol_tobb_kep_egyetlen_ablakot_nyit_az_elso_kepre(
        self, app, qt_app, megnyitva
    ):
        window, controller, _motor = app
        sorok, vart = _egy_mappabol(window, qt_app, controller)

        jobbklikk_fotón(window, qt_app, sorok[0])
        kattint(window, qt_app, "contextMenuLocate")

        assert varj(qt_app, lambda: len(megnyitva) >= 1), (
            "a kép helyi menüjének Locate on Disk tétele nem indította a fájlkezelőt"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem egyetlen, az első képre álló ablak nyílt: {megnyitva}"

    def test_tobb_mappabol_mappankent_egy_ablak_nyilik(self, app, qt_app, megnyitva):
        window, controller, _motor = app
        sorok, vart = _tobb_mappabol(window, qt_app, controller)

        jobbklikk_fotón(window, qt_app, sorok[0])
        kattint(window, qt_app, "contextMenuLocate")

        assert varj(qt_app, lambda: len(megnyitva) >= 2), (
            f"a két mappa közül nem mindegyikhez nyílt ablak: {megnyitva}"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem mappánként egy ablak nyílt: {megnyitva}"


# --- a tálca helyi menüje -------------------------------------------------


def _gyerek(szulo, nev: str, tipus=QObject):
    elem = szulo.findChild(tipus, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints_az_ablakban(qt_app, elem, gomb=Qt.MouseButton.LeftButton) -> None:
    """Valódi egérkattintás az elem közepére, az elem SAJÁT ablakában."""
    assert elem.isVisible() and elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nem látszik, vagy nulla méretű, nem kattintható"
    )
    elem.ensurePolished()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _talca_locate(window, qt_app) -> None:
    """A tálca jobbklikkje, majd valódi bal kattintás a Locate on Disk tételen."""
    _kattints_az_ablakban(
        qt_app, _gyerek(window, "trayScratchStrip", QQuickItem), Qt.MouseButton.RightButton
    )
    menu = _gyerek(window, "trayContextMenu")
    assert varj(
        qt_app,
        lambda: menu.property("opened") is True or menu.property("visible") is True,
    ), "a tálca jobbklikkje nem nyitotta meg a helyi menüt"
    tetel = _gyerek(menu, "trayMenuLocate", QQuickItem)
    assert varj(qt_app, lambda: tetel.property("visible") is True), (
        "a Locate on Disk nem látszik a tálca helyi menüjében"
    )
    _kattints_az_ablakban(qt_app, tetel)


class TestTalcaHelyiMenu:
    def test_egy_mappabol_tobb_kep_egyetlen_ablakot_nyit_az_elso_kepre(
        self, app, qt_app, megnyitva
    ):
        window, controller, _motor = app
        _sorok, vart = _egy_mappabol(window, qt_app, controller)

        _talca_locate(window, qt_app)

        assert varj(qt_app, lambda: len(megnyitva) >= 1), (
            "a tálca Locate on Disk tétele nem indította a fájlkezelőt"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem egyetlen, az első képre álló ablak nyílt: {megnyitva}"

    def test_tobb_mappabol_mappankent_egy_ablak_nyilik(self, app, qt_app, megnyitva):
        window, controller, _motor = app
        _sorok, vart = _tobb_mappabol(window, qt_app, controller)

        _talca_locate(window, qt_app)

        assert varj(qt_app, lambda: len(megnyitva) >= 2), (
            f"a két mappa közül nem mindegyikhez nyílt ablak: {megnyitva}"
        )
        qt_app.processEvents()
        assert megnyitva == vart, f"nem mappánként egy ablak nyílt: {megnyitva}"

    def test_a_tartott_kepek_tobb_mappabol_mappankent_egy_ablakot_nyitnak(
        self, app, qt_app, megnyitva
    ):
        """A tálca SAJÁT kijelölése (#2039): a megtartott képek másik mappából is
        jöhetnek, a rács kijelölése közben üres."""
        window, controller, _motor = app
        gyoker = _betolt(window, qt_app, controller)
        b = _sor(controller, gyoker, MAPPA, "b_kicsi.jpg")
        d = _sor(controller, gyoker, MASIK, "d_nagy.jpg")
        controller.holdRows([b, d])
        kijelol(window, qt_app, [])
        assert varj(qt_app, lambda: len(controller.trayItems) == 2), (
            "a két megtartott kép nem került a tálcára"
        )
        controller.selectTrayIndex(0, False, False)
        controller.selectTrayIndex(1, True, False)
        assert list(controller.traySelectedIndexes) == [0, 1]
        elemek = [Path(str(elem["path"])) for elem in controller.trayItems]

        _talca_locate(window, qt_app)

        assert varj(qt_app, lambda: len(megnyitva) >= 2), (
            f"a tartott képek két mappájából nem mindegyikhez nyílt ablak: {megnyitva}"
        )
        qt_app.processEvents()
        assert sorted(megnyitva) == sorted(elemek), (
            f"nem mappánként egy ablak nyílt a tartott képekhez: {megnyitva}"
        )
        assert len(megnyitva) == 2

    def test_a_talca_sajat_kijelolese_elsobbseget_elvez_a_racs_kijelolesevel_szemben(
        self, app, qt_app, megnyitva
    ):
        window, controller, _motor = app
        gyoker = _betolt(window, qt_app, controller)
        a = _sor(controller, gyoker, MAPPA, "a_nagy.jpg")
        d = _sor(controller, gyoker, MASIK, "d_nagy.jpg")
        controller.holdRows([d])
        kijelol(window, qt_app, [a])
        assert varj(qt_app, lambda: len(controller.trayItems) == 2), (
            "a megtartott és a kijelölt kép nem került a tálcára"
        )
        index = next(
            i
            for i, elem in enumerate(controller.trayItems)
            if Path(str(elem["path"])) == gyoker / MASIK / "d_nagy.jpg"
        )
        controller.selectTrayIndex(index, False, False)

        _talca_locate(window, qt_app)

        assert varj(qt_app, lambda: len(megnyitva) >= 1), (
            "a tálca Locate on Disk tétele nem indította a fájlkezelőt"
        )
        qt_app.processEvents()
        assert megnyitva == [gyoker / MASIK / "d_nagy.jpg"], (
            f"a tálcán kijelölt képen kívül más is megnyílt: {megnyitva}"
        )
