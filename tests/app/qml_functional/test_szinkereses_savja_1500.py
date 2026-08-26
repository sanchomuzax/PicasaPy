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

import threading

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


def _kattint(gomb, qt_app, mit="a gomb"):
    """A VALÓDI vezérlő aktiválása — előbb megkövetelve, hogy látszódjon és
    engedélyezett legyen. Egy rejtett/letiltott gombon a `clicked`
    kibocsátása „sikerülne", miközben a felület néma és hatástalan (#1473)."""
    assert gomb.property("visible") is True, f"{mit} nem látszik"
    assert gomb.property("enabled") is True, f"{mit} le van tiltva"
    QMetaObject.invokeMethod(gomb, "clicked", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()


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
        assert not controller.color_index_fut()
        _lecsengetes(qt_app)


class TestLeallitasGomb:
    """#1476: a „megszakítható" a felhasználó felől csak akkor igaz, ha van
    mivel. A gomb LÉTE kevés — a mérés az, hogy a munka tényleg megáll."""

    def test_a_leallitas_gomb_tenyleg_megallitja_a_feldolgozast(
        self, qml_app, monkeypatch
    ):
        """A gombra kattintás után a HÁTRALÉVŐ képeket nem dolgozza fel.

        A mérés a KIMENETEN áll: hány kép kapott sort a `photo_colors`
        táblában, és hányszor hívódott a besorolás. A jelzés kimenetele
        önmagában semmit nem bizonyítana — a szál attól még végigfuthatna.
        """
        import picasapy.app.color_index_controller as cim
        import picasapy.index.colors as colors_modul
        from picasapy.index import color_index_progress, open_index

        window, controller, engine = qml_app
        from PySide6.QtGui import QGuiApplication

        qt_app = QGuiApplication.instance()

        # Képenként EGY köteg — így van hova beékelődni a megszakításnak.
        monkeypatch.setattr(cim, "_KOTEG_MERET", 1)
        elenged = threading.Event()
        hivasok: list[str] = []
        eredeti = colors_modul.compute_photo_color

        def lassu_besorolas(path):
            hivasok.append(str(path))
            elenged.wait(20.0)
            return eredeti(path)

        monkeypatch.setattr(colors_modul, "compute_photo_color", lassu_besorolas)

        with open_index(controller._db_path) as conn:
            _, osszes = color_index_progress(conn)
        assert osszes >= 2, "a méréshez legalább két fénykép kell"

        mezo = _elem(window, "searchField")
        _beir(mezo, "szín:kék", qt_app)

        # megvárjuk, hogy az ELSŐ kép feldolgozása tényleg elinduljon
        hatarido = time.monotonic() + 10.0
        while time.monotonic() < hatarido and not hivasok:
            qt_app.processEvents()
            time.sleep(0.02)
        assert hivasok, "a feltöltés el sem indult"

        _kattint(_elem(window, "errorBannerStopButton"), qt_app, "a Leállítás gomb")
        elenged.set()
        assert controller.waitForBackgroundWorkers(30.0)

        assert len(hivasok) == 1, (
            "a Leállítás után is tovább dolgozott a háttérszál "
            f"({len(hivasok)} kép) — a gomb hatástalan"
        )
        with open_index(controller._db_path) as conn:
            kesz, osszes_utana = color_index_progress(conn)
        assert kesz == 1, f"{kesz} kép készült el 1 helyett"
        assert kesz < osszes_utana, "a megszakítás után nem maradhat kész az egész"
        # a már kiszámolt kép munkája NEM veszett el (kötegenkénti commit)
        assert _elem(window, "errorBannerText").property("text") == ""
        _lecsengetes(qt_app)

    def test_a_gomb_csak_a_szinkereses_uzenetenel_latszik(self, qml_app):
        """Más üzeneteknek nincs mit leállítaniuk — a gomb ne zavarjon be."""
        window, controller, engine = qml_app
        from PySide6.QtGui import QGuiApplication

        qt_app = QGuiApplication.instance()
        gomb = _elem(window, "errorBannerStopButton")
        assert gomb.property("visible") is False

        controller.folderUnavailable.emit("/nincs/ilyen")
        qt_app.processEvents()
        assert _elem(window, "errorBannerText").property("text"), "nem jött üzenet"
        assert gomb.property("visible") is False, (
            "a Leállítás gomb egy nem-színkeresési üzeneten is megjelent"
        )
        _lecsengetes(qt_app, 0.2)
