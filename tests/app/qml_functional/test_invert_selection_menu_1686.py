"""A „Kijelölés megfordítása" menütétel élő legyen — #1686.

A #1616 mérése közben derült ki, ugyanaz a hibaosztály, csak a MÁSIK
oldaláról: a `Ctrl+I` globális billentyű régóta működött, a menütétel
viszont helyfoglaló volt. A funkciót tehát csak az érte el, aki ismerte a
billentyűt.

⚠️ A #1616 söprő őre ezt NEM foghatta meg: az a helyfoglaló tételeket
szándékosan kizárja (ott a felirat nem ígéret, hanem hely). A két irány
külön mérést kíván.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest


def _tetel(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"nincs ilyen menütétel: {nev}"
    return elem


def _kijelol(window, qt_app, sorok):
    window.setProperty("selectedIndexes", list(sorok))
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()


def _sorok(window) -> list[int]:
    """A `selectedIndexes` QML-oldali listája Python-listaként."""
    ertek = window.property("selectedIndexes")
    return list(ertek.toVariant()) if hasattr(ertek, "toVariant") else list(ertek)


def _kattint(window, qt_app, nev):
    """A MENÜPONTRA kattintás — nem a mögöttes metódus hívása."""
    QMetaObject.invokeMethod(
        _tetel(window, nev), "triggered", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()


class TestAMenutetelElo:
    def test_a_tetel_nem_helyfoglalo_es_kattinthato(self, qml_app_module):
        window, _controller, _engine = qml_app_module
        elem = _tetel(window, "menuEditInvertSelection")
        assert elem.property("enabled") is True, "a menüpont letiltott maradt"
        assert not elem.property("placeholder"), "a menüpont helyfoglalónak jelölt"

    def test_a_felirat_a_MUKODO_billentyut_hirdeti(self, qml_app_module):
        """A felirat `Ctrl+I`-t ígér — és az tényleg él (Main.qml)."""
        window, _controller, _engine = qml_app_module
        elem = _tetel(window, "menuEditInvertSelection")
        assert "Ctrl+I" in str(elem.property("text"))
        rovidites = window.findChildren(QObject)
        talalt = [
            o for o in rovidites
            if o.metaObject().className().startswith("QQuickShortcut")
            and str(o.property("sequence")) == "Ctrl+I"
        ]
        assert talalt, "a felirat Ctrl+I-t hirdet, de nincs hozzá élő Shortcut"


class TestAMenupontUGYANAZTCsinalja:
    """A menüpont és a `Ctrl+I` ugyanarra a belépőre megy — MÉRVE."""

    def test_a_menupontra_KATTINTVA_megfordul_a_kijeloles(self, qml_app, qt_app):
        """⚠️ A projekt szabálya: a vezérlőre KATTINTS, ne a metódust hívd.

        A `window.invertSelection()` közvetlen hívása akkor is zöld lenne,
        ha a menüpont kattinthatatlan — épp ez volt a hiba (#1686).
        """
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        elotte = _sorok(window)
        assert elotte == [0]

        _kattint(window, qt_app, "menuEditInvertSelection")

        utana = _sorok(window)
        assert 0 not in utana, (
            f"a menüpontra kattintva a kijelölés nem fordult meg: "
            f"{elotte} → {utana}"
        )

    def test_a_billentyu_ugyanazt_adja(self, qml_app, qt_app):
        """Ellenpróba: a `Ctrl+I` és a menüpont eredménye AZONOS."""
        window, _controller, _engine = qml_app
        _kijelol(window, qt_app, [0])
        QTest.keyClick(window, Qt.Key.Key_I, Qt.KeyboardModifier.ControlModifier)
        qt_app.processEvents()
        billentyuvel = _sorok(window)

        _kijelol(window, qt_app, [0])
        _kattint(window, qt_app, "menuEditInvertSelection")
        menubol = _sorok(window)

        assert billentyuvel == menubol, (
            "a menüpont és a Ctrl+I MÁS eredményt ad — a menüpont nem "
            f"ugyanarra a belépőre megy: {menubol} vs {billentyuvel}"
        )
