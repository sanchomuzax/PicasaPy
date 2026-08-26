"""A színkeresés útja VÉGIG a FELÜLETEN: keresőmező → vezérlő → sáv (#1500).

## Miért a felületen

A #1500 előtt a `color:`/`szín:` keresés magja és lekérdezése is helyes
volt — a `photo_colors` gyorsítótárat viszont senki nem töltötte fel,
ezért a keresés MINDIG üres listát adott, minden visszajelzés nélkül. A
vezérlő-szintű teszt (`tests/app/test_szinkereses_feltoltes_1500.py`) a
jelzést méri; ez a fájl azt méri, hogy a jelzés a felhasználóig EL IS JUT.

A teszt ezért nem hívja a `controller.search()`-öt: a VALÓDI keresőmezőbe
ír, ahogy a felhasználó (MEMORY: „a vezérlőre kattints, ne a metódust
hívd") — így az is méréssé válik, hogy a `Main.qml` `Connections` blokkja
tényleg létező jelzésre köt.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QMetaObject, QObject, Qt


def _elem(root, nev):
    obj = root.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _lecsengetes(qt_app, masodperc: float = 0.5) -> None:
    """A gépelés utáni késleltetett munkák lefuttatása MÉG a lebontás előtt.

    A keresőmezőbe írás elindítja a `Main.qml` 150 ms-os javaslat-időzítőjét.
    Ha az a fixture lebontása közben sülne el, a `controller` context-
    property már null — a #1260 QML-hiba-őre (helyesen) elbuktatná a
    tesztet, ráadásul egy MÁSIK teszt nevén."""
    import time as _ido

    hatarido = _ido.monotonic() + masodperc
    while _ido.monotonic() < hatarido:
        qt_app.processEvents()
        _ido.sleep(0.02)


def _beir(mezo, szoveg, qt_app):
    """Gépelés a VALÓDI keresőmezőbe — a `textEdited` viszi tovább."""
    mezo.setProperty("text", szoveg)
    QMetaObject.invokeMethod(mezo, "textEdited", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


class TestSzinkeresesTajekoztatoSav:
    def test_hianyos_gyorsitotarnal_megjelenik_a_tajekoztato_sav(self, qml_app):
        """Friss indexen a `szín:kék` üres listát ad — de NEM némán."""
        window, controller, engine = qml_app
        from PySide6.QtGui import QGuiApplication

        qt_app = QGuiApplication.instance()
        mezo = _elem(window, "searchField")
        sav_szoveg = _elem(window, "errorBannerText")

        _beir(mezo, "szín:kék", qt_app)

        hatarido = time.monotonic() + 5.0
        while time.monotonic() < hatarido and not sav_szoveg.property("text"):
            qt_app.processEvents()
            time.sleep(0.02)

        szoveg = sav_szoveg.property("text")
        assert szoveg, (
            "a színkeresés némán, üres találati listával tért vissza — a "
            "felhasználó nem tudhatja, hogy a feltöltés még nem futott le"
        )
        assert "%" not in szoveg, "feloldatlan helykitöltő a szövegben"
        sav = _elem(window, "errorBanner")
        assert sav.property("notice") is True, (
            "TÁJÉKOZTATÁS, nem hiba — a piros hibasáv téves üzenetet adna"
        )
        controller.cancelColorIndex()
        assert controller.waitForBackgroundWorkers(30.0)
        _lecsengetes(qt_app)

    def test_szoveges_kereses_nem_hoz_fel_savot(self, qml_app):
        """Szín nélküli keresésnél semmilyen sáv nem villan fel."""
        window, controller, engine = qml_app
        from PySide6.QtGui import QGuiApplication

        qt_app = QGuiApplication.instance()
        mezo = _elem(window, "searchField")
        sav_szoveg = _elem(window, "errorBannerText")

        _beir(mezo, "nyaralás", qt_app)
        _lecsengetes(qt_app, 0.3)

        assert not sav_szoveg.property("text")
        assert not controller.colorIndexRunning()
        _lecsengetes(qt_app)
