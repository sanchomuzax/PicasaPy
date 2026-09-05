"""#2054: a súgó a felületről — F1 a főoldalra, Shift+F1 a mutató alatti elemre.

A menütétel eddig **helyfoglaló** volt (`placeholder: true`): a helye
megvolt, kattintásra nem történt semmi. A tartalom (28 fájl) készen állt
a `docs/help/` alatt, csak a program nem tudta megnyitni.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _gyerek(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


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


class TestAMenutetel:
    def test_a_tetel_MAR_NEM_helyfoglalo(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        tetel = _gyerek(window, "menuHelpContents")
        assert tetel.property("enabled") is True, (
            "a Súgó tartalom menütétel továbbra is tiltott"
        )

    def test_a_tetelre_kattintva_MEGNYILIK_a_sugo(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        tetel = _gyerek(window, "menuHelpContents")
        QMetaObject.invokeMethod(tetel, "triggered", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        assert _var(qt_app, lambda: window.findChild(QObject, "helpDialog") is not None)


class TestAVezerloAdja_A_Tartalmat:
    def test_a_fejezetlista_nem_ures(self, qml_app, qt_app):
        _window, controller, _e = qml_app
        fejezetek = controller.helpTopics
        assert len(fejezetek) >= 20, f"csak {len(fejezetek)} fejezet"
        assert all("nev" in f and "cim" in f for f in fejezetek)

    def test_a_FOOLDAL_all_elol(self, qml_app, qt_app):
        _window, controller, _e = qml_app
        assert controller.helpTopics[0]["nev"] == controller.helpHomeTopic

    def test_egy_fejezet_szovege_megjon(self, qml_app, qt_app):
        _window, controller, _e = qml_app
        assert len(controller.helpTopicText(controller.helpHomeTopic)) > 200

    def test_ismeretlen_fejezetre_URES_szoveg_nem_hiba(self, qml_app, qt_app):
        """A súgó megnyitása sosem buktathatja el a programot."""
        _window, controller, _e = qml_app
        assert controller.helpTopicText("nincs/ilyen.md") == ""

    def test_a_kereses_talal(self, qml_app, qt_app):
        _window, controller, _e = qml_app
        talalatok = controller.helpSearch("kollázs")
        assert talalatok and "reszlet" in talalatok[0]


class TestAGyorsbillentyuk:
    def test_az_F1_LETEZIK(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        rovidites = _gyerek(window, "helpShortcut")
        assert rovidites.property("sequence") == "F1"

    def test_a_ShiftF1_LETEZIK(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        rovidites = _gyerek(window, "helpContextShortcut")
        assert rovidites.property("sequence") == "Shift+F1"

    def test_az_F1_MEGNYITJA_a_sugot(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        rovidites = _gyerek(window, "helpShortcut")
        QMetaObject.invokeMethod(
            rovidites, "activated", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert _var(qt_app, lambda: window.findChild(QObject, "helpDialog") is not None)

    def test_a_ShiftF1_mutato_NELKUL_is_megnyilik(self, qml_app, qt_app):
        """Ha a mutató sehol nincs (vagy egyik ős sem deklarál
        `helpTopic`-ot), a FŐOLDAL nyílik — néma kudarc nincs."""
        window, _controller, _e = qml_app
        rovidites = _gyerek(window, "helpContextShortcut")
        QMetaObject.invokeMethod(
            rovidites, "activated", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert _var(qt_app, lambda: window.findChild(QObject, "helpDialog") is not None)
