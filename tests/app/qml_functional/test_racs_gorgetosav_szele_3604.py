"""A rács görgetősávja az ablak (rácsterület) jobb széléhez simul (#3604).

## A mérés (#3582 R2/R3-összevetése)

Az eredetiben a görgetősáv (`thumbui/throttlegroup`) az `albumsback` (a rács
háttere) GYEREKE, `XConstraint 1, 1, 0` — a jobb éle a rácsterület jobb
szélén. Csukott jobb fióknál ez maga az ablak széle.

Nálunk (mérve, teljes `Main.qml`, 800/1280/1920 px): a `feedScrollBar` a
`photoGrid` gyereke, és a jobb széle **26 px-re** áll az ablak szélétől
mindhárom szélességen — ez a „fehér kártya" (`Layout.margins: 12`) és a
belső `ColumnLayout` (`anchors.margins: 14`) EGYÜTTES, mindkét oldalon
egyenlő kerete. A legszélső 6 px a láthatatlan fiók-fogó (`rightDrawerFogo`,
#3035); a maradék 20 px fölösleges rés.

## A javítás

A kártya és a belső elrendezés JOBB oldali margója a fogó szélességére
csökken (`jobbFiokFogo.width`, ma 6) — a másik három oldal (a kártya
stílusa, nem Picasa-tárgy) változatlan marad. Így a rács görgetősávja pont a
fogóig ér: csukott fióknál az ablak széléig, nyitott fióknál a fiók bal
széléig — mindkét esetben ugyanaz a képlet adja mindkettőt
(`jobbFiok.visible ? jobbFiok.left : parent.right`), tehát a kettő mindig
egybeesik.

A próba KIRAJZOLT ablakban mér, két szélességen (1280 és 1920 px).
"""

from __future__ import annotations

import time

from PySide6.QtCore import QPointF
from PySide6.QtQuick import QQuickItem

#: a QML geometriája tört szám lehet (kerekített anchor-értékek)
TURES = 1.0


def _elem(window, nev: str):
    return window.findChild(QQuickItem, nev)


def _jobb_szel(elem) -> float:
    """A kirajzolt (jelenet-koordinátás) jobb szél."""
    bal = elem.mapToScene(QPointF(0, 0)).x()
    return bal + elem.width()


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


class TestARacsGorgetosavSzele:
    def test_a_sav_a_fogoig_er_ket_szelessegen(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        eredeti = window.width()
        try:
            for szelesseg in (1280, 1920):
                window.setWidth(szelesseg)
                assert _var(
                    qt_app,
                    lambda cel=szelesseg: abs(window.width() - cel) < 1,
                )
                qt_app.processEvents()

                sav = _elem(window, "feedScrollBar")
                fogo = _elem(window, "rightDrawerFogo")
                assert sav is not None, "nincs feedScrollBar"
                assert fogo is not None, "nincs rightDrawerFogo"

                sav_jobb = _jobb_szel(sav)
                fogo_bal = fogo.mapToScene(QPointF(0, 0)).x()

                assert abs(sav_jobb - fogo_bal) <= TURES, (
                    f"{szelesseg} px: a sáv jobb széle {sav_jobb:.1f}, "
                    f"a fogó bal széle {fogo_bal:.1f} — "
                    f"{fogo_bal - sav_jobb:.1f} px rés"
                )
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()

    def test_csukott_fioknal_az_ablak_szelehez_simul_a_fogot_leszamitva(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        assert window.property("activeDrawerTab") == "", (
            "ez a próba a CSUKOTT fiók állapotát méri"
        )
        eredeti = window.width()
        try:
            window.setWidth(1920)
            assert _var(qt_app, lambda: abs(window.width() - 1920) < 1)
            qt_app.processEvents()

            sav = _elem(window, "feedScrollBar")
            fogo = _elem(window, "rightDrawerFogo")
            sav_jobb = _jobb_szel(sav)
            res = window.width() - sav_jobb

            assert abs(res - fogo.width()) <= TURES, (
                f"a sáv {res:.1f} px-re áll az ablak szélétől, "
                f"a fogó szélessége {fogo.width():.1f} — nem simul a "
                "rácsterület jobb szélére"
            )
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()
