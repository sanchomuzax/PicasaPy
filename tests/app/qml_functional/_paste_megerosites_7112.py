"""#7112: a Beillesztés megerősítő ablaka, valódi kattintással jóváhagyva.

Eltérő forrás- és célmappánál a Ctrl+V és a Szerkesztés > Beillesztés már nem
indít azonnal: előbb a `pasteConfirmDialog` kérdez, és csak a „Copy Files” /
„Move Files” gomb (`pasteConfirmAcceptButton`) után indul a köteg. A régi
beillesztés-tesztek ezt a segéddel hagyják jóvá, majd az eredeti szándékuk
szerint ellenőriznek.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

_ELFOGADO_FELIRAT = {"copy": "Copy Files", "cut": "Move Files"}
_CIM = {"copy": "Confirm Copy", "cut": "Confirm Move"}


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(feltetel())


def _gyerek(window, nev: str) -> QObject:
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem épült fel"
    return elem


def _kattints(window, qt_app, nev: str) -> None:
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


def megerosito_ablak(window, qt_app) -> QObject:
    """Megvárja, hogy a Beillesztés megerősítő ablaka látható legyen."""

    def latszik() -> bool:
        ablak = window.findChild(QObject, "pasteConfirmDialog")
        return ablak is not None and ablak.property("visible") is True

    assert _varj(qt_app, latszik), (
        "az eltérő mappás Beillesztés nem kért megerősítést"
    )
    return _gyerek(window, "pasteConfirmDialog")


def megerosito_zarva(window) -> bool:
    """Igaz, ha a megerősítő ablak nincs (vagy már nincs) nyitva."""
    ablak = window.findChild(QObject, "pasteConfirmDialog")
    return ablak is None or ablak.property("visible") is False


def jovahagy_a_beillesztest(window, qt_app, muvelet: str = "copy") -> None:
    """A megerősítő ablak elfogadó gombját valódi egérkattintással megnyomja.

    A kattintás előtt azt is ellenőrzi, hogy a kérdés a várt műveletről szól
    (cím és gombfelirat), tehát nem egy másik kérdést hagy jóvá."""
    ablak = megerosito_ablak(window, qt_app)
    assert ablak.property("title") == _CIM[muvelet]
    elfogado = _gyerek(window, "pasteConfirmAcceptButton")
    assert elfogado.property("text") == _ELFOGADO_FELIRAT[muvelet]
    _kattints(window, qt_app, "pasteConfirmAcceptButton")
    assert _varj(qt_app, lambda: megerosito_zarva(window)), (
        "a jóváhagyás után a megerősítő ablak nem zárult be"
    )
