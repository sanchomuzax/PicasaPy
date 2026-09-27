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

## Review-javítás (#3697 átnézése)

Az első változat mindössze KÉT képpel futott — ekkora tartalomnál a rács
belefér a nézetbe, tehát a görgetősáv (`PicasaScrollBar.barVisible`,
`policy === AsNeeded && size < 1.0`) valójában NEM feltétlenül látszik, és a
próba a pozícióját akkor is mérte, ha ő maga láthatatlan volt. A javítás:

1. külön fixture (`qml_app_sok_kep`), ami 160 képet tesz négy albumba — ekkora
   tartalom biztosan túlnyúlik egy képernyőn, tehát a sáv ténylegesen
   látszik (`sav.isVisible()` állítás minden próbában);
2. új próba a NYITOTT jobb fiók esetére: a fogóra kattintva a sáv jobb
   szélének a fiók bal széléhez (vagyis megint a fogó bal széléhez, hiszen a
   kettőt ugyanaz a `jobbFiok.visible ? jobbFiok.left : parent.right` képlet
   mozgatja együtt) kell simulnia — nem csak a csukott állapotban.
"""

from __future__ import annotations

import time

import pytest
from conftest import _build_qml_app
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg

#: a QML geometriája tört szám lehet (kerekített anchor-értékek)
TURES = 1.0

#: annyi album/kép, hogy a rács tartalma biztosan túlnyúljon egy képernyőn
#: (az átnézés méréssora 160 képpel dolgozott, ld. a review-javítás jegyzetét)
ALBUMOK = 4
KEPEK_ALBUMONKENT = 40


def _sok_kep(lib) -> None:
    for album in range(ALBUMOK):
        mappa = lib / f"album{album}"
        mappa.mkdir()
        for i in range(KEPEK_ALBUMONKENT):
            make_jpeg(mappa / f"k{i:02d}.jpg", size=(160, 120))


@pytest.fixture
def qml_app_sok_kep(qt_app, tmp_path):
    """Mint a `qml_app`, de 160 képpel — a rács TÉNYLEGESEN görgethető, tehát
    a `feedScrollBar` a review szerinti hiányzó `isVisible()` mellett is
    biztosan látszik."""
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_sok_kep)


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


def _katt(window, elem) -> None:
    """Valódi egérkattintás az elem közepére (MEMORY: a vezérlőre kattints,
    ne a kezelő metódusát hívd) — ugyanígy mért a #3697 átnézése is."""
    kp = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window, Qt.LeftButton, Qt.NoModifier, QPoint(int(kp.x()), int(kp.y()))
    )


def _fiok_animaciora_var(qt_app, masodperc: float = 0.6) -> None:
    """A jobb fiók 400 ms-os szélesség-animációjának kivárása (#3035,
    `RightDrawer.animacioMs`) — enélkül a fogó/sáv pozíciója még mozgás
    közben méretlen."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        time.sleep(0.01)


class TestARacsGorgetosavSzele:
    def test_a_sav_a_fogoig_er_ket_szelessegen(self, qml_app_sok_kep, qt_app):
        window, _controller, _engine = qml_app_sok_kep
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
                assert sav.isVisible(), (
                    f"{szelesseg} px: a görgetősáv nem látszik — 160 képpel "
                    "a rácsnak túl kellene nyúlnia a nézeten"
                )

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
        self, qml_app_sok_kep, qt_app
    ):
        window, controller, _engine = qml_app_sok_kep
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
            assert sav.isVisible(), "a görgetősáv csukott fióknál nem látszik"
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

    def test_nyitott_jobb_fioknal_is_a_fogoig_er(self, qml_app_sok_kep, qt_app):
        """Nyitott jobb fióknál a sáv jobb szélének ugyanúgy a fogó (vagyis a
        fiók) bal széléhez kell simulnia, mint csukott állapotban — a kettőt
        ugyanaz a képlet mozgatja együtt."""
        window, _controller, _engine = qml_app_sok_kep
        assert window.property("activeDrawerTab") == "", (
            "a próba csukott fiókból indul"
        )
        eredeti = window.width()
        try:
            window.setWidth(1920)
            assert _var(qt_app, lambda: abs(window.width() - 1920) < 1)
            qt_app.processEvents()

            fogo = _elem(window, "rightDrawerFogo")
            assert fogo is not None, "nincs rightDrawerFogo"
            _katt(window, fogo)
            assert _var(
                qt_app, lambda: window.property("activeDrawerTab") != "", 3.0
            ), "a fogóra kattintás nem nyitotta ki a jobb fiókot"
            _fiok_animaciora_var(qt_app)

            sav = _elem(window, "feedScrollBar")
            assert sav.isVisible(), "a görgetősáv nyitott fióknál sem tűnhet el"
            sav_jobb = _jobb_szel(sav)
            fogo_bal = fogo.mapToScene(QPointF(0, 0)).x()

            assert abs(sav_jobb - fogo_bal) <= TURES, (
                f"nyitott fióknál a sáv jobb széle {sav_jobb:.1f}, "
                f"a fogó bal széle {fogo_bal:.1f} — "
                f"{fogo_bal - sav_jobb:.1f} px rés"
            )

            # visszazárjuk — a teardown csukott fiókot vár
            _katt(window, fogo)
            assert _var(
                qt_app, lambda: window.property("activeDrawerTab") == "", 3.0
            ), "a fogóra kattintás nem zárta be a jobb fiókot"
            _fiok_animaciora_var(qt_app)
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()
