"""Fókuszadás QML-vezérlőnek — MEGERŐSÍTÉSSEL (#1423).

## Miért kell ehhez külön segéd?

A `forceActiveFocus()` **némán nem csinál semmit**, ha a cél vezérlő a hívás
pillanatában nem látható (rejtett panel, csukott párbeszéd). A fókusz ott
marad, ahol volt, a hívás nem dob és nem naplóz. Egy negatív ág — „ebben a
mezőben állva az Enter NE nyisson képet" — ilyenkor **vakon zöld**: nem
azért nem történt semmi, mert a termék jól viselkedik, hanem mert a
billentyű oda ment, ahol amúgy sem csinált volna semmit.

A #1417 negatív ága pontosan így bukott meg: csukott párbeszéd mezőjére
erőltetett fókusz mellett zöld volt, a fókusz megerősítése után azonnal
elbukott.

Ez a segéd a fókuszadást és a megerősítést egy lépésbe köti, hogy a
megerősítést ne lehessen elfelejteni.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, Qt


def fokuszt_ad(elem, qt_app) -> None:
    """A `elem` QML-vezérlőre viszi a fókuszt, és ellenőrzi, hogy odaért.

    A `focus` property beállítása a fókuszhatókörön belüli szándékot jelzi,
    a `forceActiveFocus()` pedig a hatókörláncon végig érvényesíti — a kettő
    együtt a QML-ben bevett minta. A záró állítás a lényeg: enélkül a hívás
    némán hatástalan maradhat.

    Csak teszt-segéd: `assert`-tel jelez, mert a hívói tesztek.
    """
    assert elem is not None, "nem létező vezérlőre nem lehet fókuszt vinni"
    nev = elem.objectName() or elem.metaObject().className()
    lathato = elem.property("visible")
    assert lathato is not False, (
        f"a(z) {nev} nem látható, így nem kaphat fókuszt — a tesztnek előbb "
        "meg kell nyitnia a vezérlő konténerét (panelt, párbeszédet)"
    )
    elem.setProperty("focus", True)
    QMetaObject.invokeMethod(
        elem, "forceActiveFocus", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert elem.property("activeFocus") is True, (
        f"a fókusz nem ment át a(z) {nev} vezérlőre: a forceActiveFocus() "
        "némán hatástalan maradt, tehát az utána küldött billentyű nem oda "
        "megy, ahova a teszt hiszi (#1423)"
    )
