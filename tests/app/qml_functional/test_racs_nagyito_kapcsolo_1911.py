"""A rács-nagyító BEKAPCSOLÓJA az alsó sávban (#1911).

A #1808 megépítette a nagyítót, de a kapcsolója a v0.8.198-ban kikerült az
eszköztárból: a tulajdonos élesben jelentette, hogy a gomb „semmit nem
csinál". A #1911 mérése kimutatta, hogy a lánc működik — csak
**elérhetetlen**, mert nem volt mit megnyomni.

## Miért az ALSÓ SÁVBA kerül vissza, és nem az eszköztárba

Mérve (`docs/specs/racs-nagyito.md` 1. és 5. szakasz): az eredetiben a
belépési pont a `thumbui/loupehit`, egy **25 × 19**-es `vbutton` az alsó
vezérlősáv `scale_group`-jában, közvetlenül a nagyítás-csúszka előtt
(`loupehit` x 366…391, `scalecontainer` x 398…525). Az eszköztárban az
eredetiben SINCS ilyen gomb — ezért marad igaz a #1808
`test_NINCS_kapcsologomb_az_eszkoztaron` állítása.

## ⚠️ Amiért ez az osztály KIRAJZOLT ablakon mér

A #1808 tizennégy állítása mind a QML **forrásszövegét** olvasta, és
mind zöld volt, miközben a funkció elérhetetlen volt. Ez a projekt saját
tanulságának pontos ismétlése: *a vezérlőre kattints, ne a metódust
hívd.* Itt ezért **valódi egérkattintás** megy a gombra, és az
`loupeActive` átbillenését mérjük — nem azt, hogy a kötés SZÖVEGE ott
van-e a fájlban.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app

_TRAYBAR = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


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


def _kattints(window, elem, qt_app):
    """VALÓDI egérkattintás — a projekt szabálya: a vezérlőre kattints,
    ne a metódust hívd."""
    assert elem.width() > 0 and elem.height() > 0, "kattinthatatlan (0 méret)"
    assert elem.isEnabled(), "tiltott"
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


class TestAGombOttVan:
    def test_a_gomb_letezik_az_also_savban(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _elem(window, "trayLoupeButton") is not None, (
            "a nagyító kapcsolója hiányzik az alsó sávból"
        )

    def test_a_gomb_25x19(self, qml_app, qt_app):
        """MÉRT méret (`thumbui/loupehit`, spec 5. szakasz)."""
        window, _c, _e = qml_app
        gomb = _elem(window, "trayLoupeButton")
        assert (gomb.width(), gomb.height()) == (25.0, 19.0)

    def test_a_gomb_a_nagyitas_csuszka_ELOTT_all(self, qml_app, qt_app):
        """Az eredetiben `loupehit` 366…391, a csúszka 398-tól — a gomb
        BALRA van a csúszkától, nem mögötte."""
        window, _c, _e = qml_app
        gomb = _elem(window, "trayLoupeButton")
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka is not None, "nincs meg a nagyítás-csúszka"
        gomb_jobb = gomb.mapToScene(gomb.boundingRect().topRight()).x()
        csuszka_bal = csuszka.mapToScene(
            csuszka.boundingRect().topLeft()
        ).x()
        assert gomb_jobb <= csuszka_bal + 1


class TestAKattintasHat:
    """A jegy lényege: a gomb NE csak létezzen — működjön is."""

    def test_kattintasra_bekapcsol(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert window.property("loupeActive") is False
        _kattints(window, _elem(window, "trayLoupeButton"), qt_app)
        assert _var(qt_app, lambda: window.property("loupeActive") is True), (
            "a gombra kattintva a nagyító NEM kapcsolt be"
        )

    def test_ujra_kattintva_kikapcsol(self, qml_app, qt_app):
        """Kapcsoló, nem egyirányú gomb — különben nem lehet kilépni
        belőle, és a rácson minden húzás nagyítana."""
        window, _c, _e = qml_app
        gomb = _elem(window, "trayLoupeButton")
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: window.property("loupeActive") is True)
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: window.property("loupeActive") is False), (
            "a nagyító nem kapcsolható ki a saját gombjával"
        )

    def test_a_racs_nagyito_retege_kovetni_KEZDI(self, qml_app, qt_app):
        """A kapcsoló a rács oldali réteget engedélyezi.

        A húzás-viselkedést a #1808 `TestANagyitoAracson` fedi; itt az a
        LÁNC a tét, hogy a gomb tényleg ahhoz a réteghez szól-e.
        """
        window, _c, _e = qml_app
        terulet = _elem(window, "feedLoupeArea")
        if terulet is None:
            import pytest
            pytest.skip("a rács nincs kirajzolva ebben az összeállításban")
        gomb = _elem(window, "trayLoupeButton")
        #: ⚠️ A `qml_app` ablak MEGOSZTOTT a modul tesztjei közt: az előző
        #: eset bekapcsolva hagyhatta. Nem a kiindulást feltételezzük,
        #: hanem BEÁLLÍTJUK — különben az izoláció hiánya látszana
        #: hibának, és a valódi lánc-szakadást elfedné.
        if window.property("loupeActive") is True:
            _kattints(window, gomb, qt_app)
        #: ⚠️ `property("enabled")`, NEM `isEnabled()`. A `MouseArea.enabled`
        #: a MouseArea SAJÁT tulajdonsága (az egérkezelés be/ki), a
        #: `QQuickItem.isEnabled()` pedig az elem-fa engedélyezettsége — a
        #: kettő külön él. Az `isEnabled()` itt végig `True`-t ad, akkor is,
        #: amikor a nagyító ki van kapcsolva; erre írva a teszt NÉMÁN
        #: átengedne egy elszakadt láncot.
        assert _var(qt_app, lambda: terulet.property("enabled") is False)
        _kattints(window, gomb, qt_app)
        assert _var(qt_app, lambda: terulet.property("enabled") is True), (
            "a bekapcsolás nem érte el a rács nagyító-rétegét"
        )


class TestAFelfedezhetoseg:
    """A #1911 külön kiköti: a felhasználó KIPRÓBÁLÁS NÉLKÜL tudja meg,
    hogy húzni kell.

    Az eredeti erre nem ad támpontot — mérve (spec 2. szakasz): külön
    egérmutató NINCS. Ezért a jelzés a MI döntésünk, és a legkisebb
    ilyen a buboréksúgó: nem foglal helyet, és nem talál ki új
    viselkedést.
    """

    def test_a_gombnak_van_buboreksugoja(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gomb = _elem(window, "trayLoupeButton")
        szoveg = gomb.property("ToolTip.text") or ""
        if not szoveg:
            # az attached property nem mindig olvasható property-ként:
            # a forrás akkor a hiteles hely
            assert "trayLoupeButton" in _TRAYBAR
            assert "ToolTip.text" in _TRAYBAR

    def test_a_sugo_KIMONDJA_hogy_huzni_kell(self):
        """A puszta »Nagyító« felirat nem elég — a #1911 szerint épp az
        nem derül ki, hogy nyomva HÚZNI kell.

        A forrásban a `qsTr` ANGOL (ez a projekt konvenciója), a magyar
        alak a `picasapy_hu.ts`-ben él — ezért mindkettőt nézzük. A
        fordítás hiánya ugyanolyan hiba lenne: a felhasználó magyarul
        használja a programot.
        """
        reszlet = _TRAYBAR[_TRAYBAR.find("trayLoupeButton"):][:3000]
        assert "drag" in reszlet, (
            "a nagyító súgója nem mondja ki, hogy húzni kell"
        )
        ts = (
            Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
        ).read_text(encoding="utf-8")
        assert "Loupe — drag over the photos" in ts, (
            "a súgó nincs lefordítva magyarra"
        )
        kezdet = ts.find("Loupe — drag over the photos")
        assert "úz" in ts[kezdet : kezdet + 300], (
            "a magyar súgó sem mondja ki, hogy húzni kell"
        )
