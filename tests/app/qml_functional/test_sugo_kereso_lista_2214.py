"""#2214 — a találatlista sorai megkülönböztethetők.

A felhasználó képernyőképén ugyanaz a cím ötször egymás alatt. Az őr azt
méri, amit a felhasználó LÁT: a sorok szövegét — nem a `kereses()`
visszatérési értékét (azt a `tests/test_help_kereses_2214.py` méri).
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _nevre(window, nev: str) -> list:
    gyoker = window.contentItem() if hasattr(window, "contentItem") else window
    return [e for e in _walk(gyoker) if e.objectName() == nev]


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


def _keress(window, qt_app, kifejezes: str):
    mezo = window.findChild(QObject, "helpSearchField")
    assert mezo is not None, "nincs keresőmező"
    mezo.setProperty("text", kifejezes)
    qt_app.processEvents()
    _var(qt_app, lambda: len(_nevre(window, "helpResultTitle")) > 0, 3.0)


class TestASorokMegkulonboztethetok:
    def test_nincs_ket_azonos_cimsor(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        _nyisd_meg(window, qt_app)
        _keress(window, qt_app, "effekt")

        cimek = [
            c.property("text")
            for c in _nevre(window, "helpResultTitle")
            if c.property("text")
        ]
        assert cimek, "a keresés egyetlen sort sem adott"
        assert len(cimek) == len(set(cimek)), (
            f"ismétlődő címsorok a találatlistában: {cimek}"
        )

    def test_a_reszlet_LATSZIK_a_soron(self, qml_app, qt_app):
        """Nem tooltipben — a listában."""
        window, _controller, _e = qml_app
        _nyisd_meg(window, qt_app)
        _keress(window, qt_app, "effekt")

        reszletek = [
            r
            for r in _nevre(window, "helpResultSnippet")
            if r.isVisible() and r.property("text")
        ]
        assert reszletek, "egyetlen találaton sem látszik a részlet"

    def test_a_reszletek_kulonboznek(self, qml_app, qt_app):
        window, _controller, _e = qml_app
        _nyisd_meg(window, qt_app)
        _keress(window, qt_app, "kép")
        szovegek = [
            r.property("text")
            for r in _nevre(window, "helpResultSnippet")
            if r.isVisible() and r.property("text")
        ]
        if len(szovegek) > 1:
            assert len(set(szovegek)) > 1, "minden részlet ugyanaz"


class TestATalalatraKattintvaMegnyilik:
    def test_az_elso_talalat_atvisz(self, qml_app, qt_app):
        window, controller, _e = qml_app
        _nyisd_meg(window, qt_app)
        parbeszed = window.findChild(QObject, "helpDialog")

        talalatok = controller.helpSearch("effekt")
        assert talalatok, "az »effekt« keresés nem ad találatot"
        vart = talalatok[0]["fejezet"]

        # ⚠️ A kiinduló fejezet NEM lehet a várt találat: az „effekt" első
        # találata épp a nyitólap, ezért a naiv „változott-e a topic"
        # állítás akkor is elbukna, ha a kötés hibátlan.
        masik = next(
            t["nev"] for t in controller.helpTopics if t["nev"] != vart
        )
        parbeszed.setProperty("topic", masik)
        qt_app.processEvents()
        eredeti = parbeszed.property("topic")
        assert eredeti == masik

        _keress(window, qt_app, "effekt")

        # a delegate `clicked` jele viszi tovább — ezt adja a valódi
        # kattintás is, tehát a kötés hiánya elbuktatja a próbát
        sorok = _nevre(window, "helpResultRow")
        assert sorok, "nincs kattintható találatsor"
        QMetaObject.invokeMethod(
            sorok[0], "clicked", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert _var(qt_app, lambda: parbeszed.property("topic") == vart), (
            f"a találatra kattintva nem a {vart!r} fejezet nyílt meg, hanem "
            f"{parbeszed.property('topic')!r}"
        )
