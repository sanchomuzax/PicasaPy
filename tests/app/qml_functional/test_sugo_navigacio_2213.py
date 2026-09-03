"""#2213 — a súgóban legyen Vissza és Kezdőlap.

A felhasználó jelentette: „ha a keresővel elnavigálok egy lapra, nem lehet
visszamenni sehová." A párbeszéd egyetlen `topic` értéket tartott,
előzmény nélkül.

⚠️ A próbák a **gomb `clicked` jelét** bocsátják ki — a valódi kattintás
útját —, nem a QML-függvényt hívják közvetlenül.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


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


def _nyisd_meg(window, qt_app):
    tetel = window.findChild(QObject, "menuHelpContents")
    assert tetel is not None
    QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    assert _var(qt_app, lambda: window.findChild(QObject, "helpDialog") is not None)
    return window.findChild(QObject, "helpDialog")


def _gomb(window, nev):
    g = window.findChild(QObject, nev)
    assert g is not None, f"nincs ilyen vezérlő: {nev}"
    return g


def _kattints(gomb, qt_app):
    QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestAVisszaGomb:
    def test_letezik_a_vissza_gomb(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_meg(window, qt_app)
        assert window.findChild(QObject, "helpBackButton") is not None

    def test_a_vissza_az_ELOZO_fejezetre_lep(self, qml_app, qt_app):
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg(window, qt_app)

        elso = controller.helpHomeTopic
        masodik = next(
            t["nev"] for t in controller.helpTopics if t["nev"] != elso
        )
        parbeszed.setProperty("topic", elso)
        qt_app.processEvents()
        parbeszed.setProperty("topic", masodik)
        qt_app.processEvents()

        vissza = _gomb(window, "helpBackButton")
        assert vissza.property("enabled") is True, (
            "két fejezet után is inaktív a Vissza"
        )
        _kattints(vissza, qt_app)
        assert _var(qt_app, lambda: parbeszed.property("topic") == elso), (
            f"a Vissza nem az előző fejezetre lépett "
            f"(most: {parbeszed.property('topic')!r}, várt: {elso!r})"
        )

    def test_a_vissza_HAROM_lepes_utan_is_sorban_halad(self, qml_app, qt_app):
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg(window, qt_app)
        nevek = [t["nev"] for t in controller.helpTopics][:3]
        assert len(nevek) == 3

        for nev in nevek:
            parbeszed.setProperty("topic", nev)
            qt_app.processEvents()

        vissza = _gomb(window, "helpBackButton")
        for vart in reversed(nevek[:-1]):
            _kattints(vissza, qt_app)
            assert _var(qt_app, lambda v=vart: parbeszed.property("topic") == v), (
                f"a visszalépés-sor elromlott: {parbeszed.property('topic')!r} "
                f"!= {vart!r}"
            )

    def test_a_vissza_kimeriti_az_elozmenyt_es_INAKTIV_lesz(
        self, qml_app, qt_app
    ):
        """Nem ragadhat be aktívként, ha már nincs hova lépni."""
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg(window, qt_app)
        elso = controller.helpHomeTopic
        masodik = next(
            t["nev"] for t in controller.helpTopics if t["nev"] != elso
        )
        parbeszed.setProperty("topic", elso)
        qt_app.processEvents()
        parbeszed.setProperty("topic", masodik)
        qt_app.processEvents()

        vissza = _gomb(window, "helpBackButton")
        _kattints(vissza, qt_app)
        assert _var(qt_app, lambda: vissza.property("enabled") is False)

    def test_a_VISSZALEPES_nem_kerul_be_az_elozmenybe(self, qml_app, qt_app):
        """Máskülönben a Vissza oda-vissza ugrálna két lap közt."""
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg(window, qt_app)
        nevek = [t["nev"] for t in controller.helpTopics][:2]
        for nev in nevek:
            parbeszed.setProperty("topic", nev)
            qt_app.processEvents()

        vissza = _gomb(window, "helpBackButton")
        _kattints(vissza, qt_app)
        qt_app.processEvents()
        assert parbeszed.property("topic") == nevek[0]
        # az előzmény kiürült — nincs hova tovább
        assert vissza.property("enabled") is False

    def test_a_vissza_kezdetben_INAKTIV(self, qml_app, qt_app):
        """Nem hazudik kattinthatóságot (#1895 tanulsága)."""
        window, _c, _e = qml_app
        _nyisd_meg(window, qt_app)
        vissza = _gomb(window, "helpBackButton")
        assert vissza.property("enabled") is False


class TestAKezdolapGomb:
    def test_letezik_a_kezdolap_gomb(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_meg(window, qt_app)
        assert window.findChild(QObject, "helpHomeButton") is not None

    def test_a_kezdolap_a_nyitolapra_visz_KERESES_kozben_is(
        self, qml_app, qt_app
    ):
        window, controller, _e = qml_app
        parbeszed = _nyisd_meg(window, qt_app)
        masik = next(
            t["nev"] for t in controller.helpTopics
            if t["nev"] != controller.helpHomeTopic
        )
        parbeszed.setProperty("topic", masik)
        mezo = window.findChild(QObject, "helpSearchField")
        mezo.setProperty("text", "effekt")   # a lista átvált a találatokra
        qt_app.processEvents()

        _kattints(_gomb(window, "helpHomeButton"), qt_app)
        assert _var(
            qt_app,
            lambda: parbeszed.property("topic") == controller.helpHomeTopic,
        )
