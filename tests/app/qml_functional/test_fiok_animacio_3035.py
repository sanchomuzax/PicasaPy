"""#3035: a jobb fiók nyitása ANIMÁLT, és nem látszó sáv is nyitja.

## A mérés

`thumbui.tre:700` — `Handler varbutton RIGHTDRAWEROFFSET -280 0 1 …`:

| érték | jelentés |
|---|---|
| `-280` | a fiók nyitva |
| `0` | a fiók zárva |
| `1` | **animált** |
| időtartam | **0,4 s** (`0x00cf4ce0`, az ág `0x009d7dc1`) |

A kapcsoló két elemet is értesít (`editpanel/previewimage`,
`…image2`), tehát a szerkesztő előnézete a fiókkal EGYÜTT méreteződik.

`thumbui.tre:696` — `m_fakehidden`: a fiókot egy **nem látszó**
kattintható terület is nyitja/zárja a fiók szélén.

## Amit ez a próba mér

A szélesség tényleges változását (nem a `visible` jelzőt), és azt, hogy a
nem látszó sáv ugyanazt a kaput hívja, mint a menü.
"""

from __future__ import annotations

from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

#: a mért animáció-hossz
ANIMACIO_MS = 400
ALAP_SZELESSEG = 280


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _var(qt_app, felteteles, korok: int = 40):
    """Megvárja a feltételt — VALÓDI idő múlásával.

    ⚠️ A puszta `processEvents` nem elég: az animáció órája nem lép
    tőle, tehát a 400 ms-os betolás közepén állva mérnénk."""
    for _ in range(korok):
        if felteteles():
            return True
        QTest.qWait(30)
    return felteteles()


def _nyisd(window, qt_app, menu_nev="menuViewTags"):
    QMetaObject.invokeMethod(
        _gyerek(window, menu_nev), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


class TestAzAnimacio:
    def test_a_szelesseg_ANIMALVA_valtozik(self, qml_app, qt_app):
        """A mért `1`-es jelző: a fiók nem ugrik, hanem betolódik."""
        window, _controller, _engine = qml_app
        fiok = _gyerek(window, "rightDrawer")

        assert fiok.property("animacioMs") == ANIMACIO_MS, (
            f"az animáció {fiok.property('animacioMs')} ms, a mért "
            f"{ANIMACIO_MS} helyett"
        )

    def test_nyitva_a_MERT_szelesseget_eri_el(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app)
        fiok = _gyerek(window, "rightDrawer")

        assert _var(qt_app, lambda: fiok.property("width") == ALAP_SZELESSEG), (
            f"a fiók {fiok.property('width')} széles maradt"
        )

    def test_zarva_NULLA_szeles(self, qml_app, qt_app):
        """A `0` a mért csukott állapot — a fiók nem foglal helyet."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app)
        fiok = _gyerek(window, "rightDrawer")
        assert _var(qt_app, lambda: fiok.property("width") > 0)

        QMetaObject.invokeMethod(
            window, "ureseidAFiokot", Qt.ConnectionType.DirectConnection
        )

        assert _var(qt_app, lambda: fiok.property("width") == 0), (
            f"a csukott fiók {fiok.property('width')} képpontot foglal"
        )


class TestANemLatszoSav:
    """`m_fakehidden`: kattintható, de nem látszó terület a fiók szélén."""

    def test_letezik_es_NEM_latszik(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        sav = _gyerek(window, "rightDrawerFogo")

        assert sav.property("opacity") == 0, (
            "a sávnak nem szabad látszania (`m_fakehidden`)"
        )

    def test_BILLENTI_a_fiokot(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app)
        assert window.property("activeDrawerTab") != ""

        QMetaObject.invokeMethod(
            _gyerek(window, "rightDrawerFogo"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert window.property("activeDrawerTab") == "", (
            "a nem látszó sáv nem zárta be a fiókot"
        )

    def test_UJRA_megnyitja_ugyanazt_a_lapot(self, qml_app, qt_app):
        """A billentés fele-útja adatvesztésnek látszana (#2163)."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, "menuViewPeople")
        fogo = _gyerek(window, "rightDrawerFogo")

        for _ in range(2):
            QMetaObject.invokeMethod(
                fogo, "kattints", Qt.ConnectionType.DirectConnection
            )
            qt_app.processEvents()

        assert window.property("activeDrawerTab") == "people"
