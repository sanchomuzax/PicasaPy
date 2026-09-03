"""#2039: a képtálcának SAJÁT kijelölése van — valódi kattintással mérve.

## A lelet

A tálca elemeire nem lehetett kattintani: a `trayPreviewThumb` csupasz
`Image` volt, az egyetlen mutató-kezelője a jobbklikkes helyi menü. A
„Kijelölés eltávolítása" ezért a RÁCS kijelöléséből vett ki elemeket —
azokból, amiket a felhasználó a tálcán ki sem tudott jelölni.

## Bizonyíték

Az eredetiben a tálca ugyanolyan `CSelectionNode`, mint a rács
(`docs/specs/picasa-keptalca.md` 13.), és a csomópont ELEMENKÉNTI
állapotot tárol; a tálca számlálója ezt a jelzőt olvassa. A kijelölés
tehát a tálca sajátja, nem a rács tükre.

## Miért kattintással

A vezérlő metódusát meghívni semmit nem bizonyít: a `selectTrayIndex`
zölden futhat úgy is, hogy a bélyegképhez soha nem ér el egérnyomás.
Ezek a próbák ezért a **képre kattintanak** (`QTest.mouseClick`), és a
módosítókat is az egérrel adják.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elemek(window, nev: str) -> list:
    return [it for it in _walk(window.contentItem()) if it.objectName() == nev]


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _harom_kep(qml_app, qt_app):
    """Három kép a tálcán, MEGTARTVA — a megtartás nélkül a tálca a rács
    kijelölését tükrözi, és a tartalma kattintás közben változna."""
    window, controller, _e = qml_app
    lib = Path(controller.watchedFolders[0])
    for i in range(3):
        make_jpeg(lib / f"k{i}.jpg", size=(60, 40))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()

    sorok = list(range(min(3, controller.photos.rowCount())))
    assert len(sorok) == 3, "a próbához három kép kell"
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()
    controller.holdRows(sorok)
    assert _var(qt_app, lambda: len(_elemek(window, "trayPreviewThumb")) == 3), (
        "nem lett három bélyegkép a tálcán"
    )
    return window, controller


def _belyegkepek(window) -> list:
    """A tálca bélyegképei a MEGJELENÉS sorrendjében (bal→jobb).

    A gyerek-sorrend nem garantáltan a modell sorrendje, a `trayItems`
    indexei viszont igen — ezért az x koordináta dönt."""
    return sorted(_elemek(window, "trayPreviewThumb"), key=lambda it: it.mapToScene(QPointF(0, 0)).x())


def _kattints(qt_app, window, item, modosito=Qt.KeyboardModifier.NoModifier) -> None:
    kozep = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    assert 0 <= kozep.x() <= window.width() and 0 <= kozep.y() <= window.height(), (
        f"a kattintási pont ({kozep.x():.0f};{kozep.y():.0f}) az ablakon kívülre "
        "esik — a próba így nem mérne semmit"
    )
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, modosito, kozep.toPoint())
    qt_app.processEvents()


class TestKattintasAKepre:
    def test_indulaskor_nincs_kijelolve_semmi(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        assert list(controller.traySelectedIndexes) == []

    def test_a_kepre_kattintva_kijelolodik(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        _kattints(qt_app, window, _belyegkepek(window)[1])
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == [1]), (
            f"a kattintás nem jelölte ki a képet "
            f"(kijelölt: {list(controller.traySelectedIndexes)})"
        )

    def test_masikra_kattintva_atvalt(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        kepek = _belyegkepek(window)
        _kattints(qt_app, window, kepek[0])
        _kattints(qt_app, window, kepek[2])
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == [2])

    def test_ctrl_kattintassal_hozzaad(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        kepek = _belyegkepek(window)
        _kattints(qt_app, window, kepek[0])
        _kattints(qt_app, window, kepek[2], Qt.KeyboardModifier.ControlModifier)
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == [0, 2])

    def test_shift_kattintassal_tartomanyt_jelol(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        kepek = _belyegkepek(window)
        _kattints(qt_app, window, kepek[0])
        _kattints(qt_app, window, kepek[2], Qt.KeyboardModifier.ShiftModifier)
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == [0, 1, 2])


class TestAKijelolesLATSZIK:
    def test_kattintas_elott_egyetlen_keret_sem_latszik(self, qml_app, qt_app):
        window, _controller = _harom_kep(qml_app, qt_app)
        latszo = [k for k in _elemek(window, "trayThumbSelectionOuter") if k.isVisible()]
        assert not latszo, "kijelölés nélkül is látszik kijelölés-keret"

    def test_a_kijelolt_kepen_megjelenik_a_keret(self, qml_app, qt_app):
        window, _controller = _harom_kep(qml_app, qt_app)
        _kattints(qt_app, window, _belyegkepek(window)[1])
        assert _var(
            qt_app,
            lambda: len(
                [k for k in _elemek(window, "trayThumbSelectionOuter") if k.isVisible()]
            )
            == 1,
        ), "a kijelölt képen nem jelent meg a keret"

    def test_a_keret_a_RACCSAL_AZONOS_szint_hasznalja(self):
        """Nem új stílus: ugyanaz a `Theme.thumbSelection`, mint a rácsban."""
        import picasapy.app

        qml = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
        racs = (qml / "ThumbDelegate.qml").read_text(encoding="utf-8")
        talca = (qml / "TrayBar.qml").read_text(encoding="utf-8")
        assert "Theme.thumbSelection" in racs
        assert "Theme.thumbSelection" in talca


def _gyerek(window, nev):
    """A `Menu` NEM a `contentItem` gyereke (felugró), ezért `findChild` kell."""
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


class TestAKijelolesEltavolitasa:
    """A `Tray::ID_REMOVE_SELECTION` a TÁLCA kijelölésére hasson."""

    def test_csak_a_talcan_kijelolt_kerul_le(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        _kattints(qt_app, window, _belyegkepek(window)[1])
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == [1])

        _gyerek(window, "trayContextMenu").removeSelectionRequested.emit()
        qt_app.processEvents()

        assert _var(qt_app, lambda: controller.heldCount == 2), (
            f"nem egy elem került le a tálcáról (megtartott: {controller.heldCount})"
        )

    def test_utana_nem_marad_kijeloles(self, qml_app, qt_app):
        window, controller = _harom_kep(qml_app, qt_app)
        _kattints(qt_app, window, _belyegkepek(window)[0])
        _gyerek(window, "trayContextMenu").removeSelectionRequested.emit()
        qt_app.processEvents()
        assert _var(qt_app, lambda: list(controller.traySelectedIndexes) == []), (
            "az eltávolítás után is maradt kijelölés — a megmaradt elemekre "
            "mutatna, tehát a következő parancs MÁST törölne"
        )
