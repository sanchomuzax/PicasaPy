"""#1919 — az összecsukott mappa-token megjelenik a VALÓDI tálcában.

## Miért kellett ez a fájl a `test_talca_mappa_token_1919.py` MELLETT

A meglévő őr a `TrayAlbumToken` komponenst ÖNMAGÁBAN példányosítja
(`QQmlComponent.setData`), és a rajzát méri. Ez a token KINÉZETÉT
bizonyítja — de azt nem, hogy a token a `TrayBar`-ban egyáltalán
megjelenik-e. A kettő között három olyan kötés van, amit önmagában
példányosított komponens NEM érint:

1. `trayScratchBack.albumTokens` ← `controller.trayAlbumTokens`
   (defenzív `!== undefined` kötés — ha a tulajdonság elnevezése
   elcsúszik, a kötés némán üres tömböt ad, és a token SOSEM látszik);
2. a `trayAlbumTokenRow` `visible`-je és a `Repeater` modellje;
3. a bélyegkép-sor (`trayScratchStrip`) elrejtése — a `scratch.tre`
   `m_scaleXY`-ja szerint a token a sáv HELYÉT foglalja el.

A `heldChanged` jelzésen múlik, hogy a nézet egyáltalán ÉRTESÜL a
változásról. Ezt a láncot csak a valódi ablakon, valódi vezérlővel lehet
mérni — ezért a `qml_app` fixture.

⛔ HATÓKÖR: ez a fájl azt méri, hogy a token KIRAJZOLÓDIK, ha a modellbe
bekerül. Azt NEM méri (és a #1919 nem is kéri), hogy melyik menüpont
vagy gesztus teszi oda: az eredetiben nem parancs kapcsolja, hanem egy
minden frissítéskor újraértékelt állapot-küldött, és az a bekötés külön
jegyre tartozik. A teszt ezért a vezérlő meglévő belépőjét
(`collapseFolderIntoTray`) hívja.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    """Vár egy feltételre, közben pumpálja az eseménysort."""
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


def _elem(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _walk(item):
    """A VIZUÁLIS fa bejárása (`childItems`).

    ⚠️ A `Repeater` delegáltjai a szülő VIZUÁLIS gyerekei, a QObject-fában
    viszont nem a sáv alatt ülnek — `findChild`-dal tehát NEM találhatók
    meg. (Ugyanezért definiál a `test_talca_vizjel_2179.py` is saját
    bejárót.) Ez a különbség egy körön át azt mutatta, hogy a `Repeater`
    nem hoz létre delegáltat, holott létrehozott.
    """
    for gyerek in item.childItems():
        yield gyerek
        yield from _walk(gyerek)


def _nev_szerint(window, nev: str) -> list:
    """A token-sáv alatti, `nev` objectName-ű VIZUÁLIS elemek."""
    return [
        elem
        for elem in _walk(_elem(window, "trayAlbumTokenRow"))
        if elem.objectName() == nev
    ]


def _tokenek(window) -> list:
    """A kirajzolt token-példányok feliratai (a `Repeater` delegáltjai)."""
    return _nev_szerint(window, "trayAlbumTokenLabel")


class TestAlapallapotbanNincsToken:
    """Token nélkül a tálca változatlanul a bélyegképeket mutatja."""

    def test_a_token_sav_NEM_latszik(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayAlbumTokenRow"))
        assert _elem(window, "trayAlbumTokenRow").property("visible") is False

    def test_a_belyegkep_sor_LATSZIK(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayScratchStrip"))
        assert _elem(window, "trayScratchStrip").property("visible") is True


class TestATokenMegjelenik:
    """A modellbe tett token a valódi tálcában kirajzolódik."""

    @staticmethod
    def _osszecsuk(qml_app, qt_app, tmp_path) -> None:
        _window, controller, _e = qml_app
        mappa = tmp_path / "kepek"
        assert controller.collapseFolderIntoTray(str(mappa)) is True, (
            "a vezérlő nem tette a tálcára a mappát — a próbakönyvtár "
            f"({mappa}) nincs az indexben?"
        )
        qt_app.processEvents()

    def test_a_token_sav_LATHATOVA_valik(self, qml_app, qt_app, tmp_path):
        window, _c, _e = qml_app
        self._osszecsuk(qml_app, qt_app, tmp_path)
        assert _var(
            qt_app,
            lambda: _elem(window, "trayAlbumTokenRow").property("visible")
            is True,
        ), (
            "a token sávja a mappa összecsukása után sem látszik — a "
            "`trayScratchBack.albumTokens` kötés nem ér el a vezérlőig"
        )

    def test_PONTOSAN_EGY_token_rajzolodik_ki(self, qml_app, qt_app, tmp_path):
        window, _c, _e = qml_app
        self._osszecsuk(qml_app, qt_app, tmp_path)
        assert _var(qt_app, lambda: len(_tokenek(window)) == 1), (
            f"{len(_tokenek(window))} token-felirat van a sávban, egy helyett"
        )

    def test_a_felirat_a_MAPPA_darabszamat_irja(
        self, qml_app, qt_app, tmp_path
    ):
        """A próbakönyvtárban KÉT kép van (`a.jpg`, `b.jpg`) — a feliratban
        ennek a számnak kell állnia, nem egy beégetett értéknek."""
        window, _c, _e = qml_app
        self._osszecsuk(qml_app, qt_app, tmp_path)
        assert _var(qt_app, lambda: len(_tokenek(window)) == 1)
        szoveg = str(_tokenek(window)[0].property("text"))
        assert "2" in szoveg, (
            f"a felirat ({szoveg!r}) nem a mappa két képét írja ki"
        )
        assert " - " in szoveg, (
            f"a felirat ({szoveg!r}) nem a `%1$s - %2$d %3$s` formátum"
        )

    def test_a_belyegkep_sor_ELREJTOZIK(self, qml_app, qt_app, tmp_path):
        """A `scratch.tre` `m_scaleXY`-ja szerint a token a bélyegkép-sáv
        HELYÉT foglalja el — a mért felvételen bélyegkép-rács nincs."""
        window, _c, _e = qml_app
        self._osszecsuk(qml_app, qt_app, tmp_path)
        assert _var(
            qt_app,
            lambda: _elem(window, "trayScratchStrip").property("visible")
            is False,
        ), "a token mellett a bélyegkép-sor is kirajzolódik"


class TestATokenGeometriaja:
    """A `.tre` kényszerei a VALÓDI tálcában is állnak."""

    @staticmethod
    def _kirajzolt_token(qml_app, qt_app, tmp_path):
        window, controller, _e = qml_app
        assert controller.collapseFolderIntoTray(
            str(tmp_path / "kepek")
        ) is True
        qt_app.processEvents()
        assert _var(qt_app, lambda: len(_tokenek(window)) == 1)
        felirat = _tokenek(window)[0]
        (pirula,) = _nev_szerint(window, "trayAlbumTokenHighlight")
        return window, felirat, pirula

    def test_a_pirula_a_felirattol_4_4_keppontal_szelesebb(
        self, qml_app, qt_app, tmp_path
    ):
        _w, felirat, pirula = self._kirajzolt_token(qml_app, qt_app, tmp_path)
        assert _var(qt_app, lambda: felirat.property("width") > 0)
        assert pirula.property("width") == felirat.property("width") + 8, (
            f"a pirula {pirula.property('width')} széles, a felirat "
            f"{felirat.property('width')} — a `.tre` ±4 képpontot ad"
        )

    def test_a_pirula_EGY_keppontal_magasabb(self, qml_app, qt_app, tmp_path):
        _w, felirat, pirula = self._kirajzolt_token(qml_app, qt_app, tmp_path)
        assert _var(qt_app, lambda: felirat.property("height") > 0)
        assert pirula.property("height") == felirat.property("height") + 1, (
            f"a pirula {pirula.property('height')} magas, a felirat "
            f"{felirat.property('height')} — a `.tre` +1 képpontot ad"
        )

    def test_a_felirat_a_tokenben_KOZEPEN_all(self, qml_app, qt_app, tmp_path):
        """`scratch/albumlabel`: `m_centerXY` — a felirat a token
        közepén ül, vízszintesen és függőlegesen is."""
        _w, felirat, _p = self._kirajzolt_token(qml_app, qt_app, tmp_path)
        assert _var(qt_app, lambda: felirat.property("width") > 0)
        token = felirat.parent()
        for tengely, meret in (("x", "width"), ("y", "height")):
            eltolas = felirat.property(tengely)
            szabad = token.property(meret) - felirat.property(meret)
            assert abs(eltolas - szabad / 2) <= 1, (
                f"a felirat {tengely}={eltolas}, a szabad hely {szabad} — "
                "nem középen ül"
            )


class TestATokenElvehetoAgain:
    """A token kivétele visszaadja a bélyegkép-sort."""

    def test_a_kibontas_utan_ujra_a_belyegkepek_latszanak(
        self, qml_app, qt_app, tmp_path
    ):
        window, controller, _e = qml_app
        mappa = str(tmp_path / "kepek")
        assert controller.collapseFolderIntoTray(mappa) is True
        qt_app.processEvents()
        assert _var(
            qt_app,
            lambda: _elem(window, "trayAlbumTokenRow").property("visible")
            is True,
        )
        assert controller.expandFolderInTray(mappa) is True
        qt_app.processEvents()
        assert _var(
            qt_app,
            lambda: _elem(window, "trayAlbumTokenRow").property("visible")
            is False,
        ), "a token kivétele után is látszik a token sávja"
        assert _elem(window, "trayScratchStrip").property("visible") is True, (
            "a bélyegkép-sor nem tért vissza a token kivétele után"
        )
