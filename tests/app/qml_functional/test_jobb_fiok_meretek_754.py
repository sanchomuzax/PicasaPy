"""#754: EGY jobb fiók, mért geometriával — nem négy különböző hasáb.

A normatív méretlap: `docs/specs/jobb-fiok-meretek.md`. Ami ebből mérhető
a felületen, azt ez a próba tartja fenn.

## Amit a javítás előtt MÉRTÜNK

| panel | nálunk volt | az eredetiben |
|---|---:|---:|
| `TagsPanel` | 190 | **280** |
| `PlacesPanel` | 320 | **280** |
| `PropertiesPanel` | 210 | **280** |
| `PeoplePanel` | 200 | **280** |

Se közös fejléc, se egységes szélesség, se kicsi/nagy váltás — a négy
panel négy külön `SplitView`-cellában ült.

## A fülsávról

A jegy címe fülsávot kér, a `respack.yt` szerint viszont a fülsáv és mind
a négy fül **`#`-kal ki van kommentezva** a kiadott csomagban (a jegy
2026-08-16-i helyesbítése). Ezért fülsáv NINCS, és ez a próba nem is kér:
a lapváltás a Nézet menüből megy, ahogy a #1773 óta.

## A két szélesség (#2529, kimérve)

| állapot | szélesség |
|---|---|
| alap | **280** |
| nagy | **min(az ablak 30 %-a, 392)** |
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt

#: menütétel → panel, a #1773 négy lapja
LAPOK = [
    ("menuViewProperties", "propertiesPanel"),
    ("menuViewTags", "tagsPanel"),
    ("menuViewPeople", "peoplePanel"),
    ("menuViewPlaces", "placesPanel"),
]

#: a mért alapszélesség (`RIGHTDRAWEROFFSET -280`)
ALAP_SZELESSEG = 280
#: a tartalom vászna a 280-as fiókban
TARTALOM_SZELESSEG = 276
#: a mért fejléc-magasság (`rightdrawerpanel/header`)
FEJLEC_MAGASSAG = 30
#: `size_toggle` és `close` — mindkettő 14 × 14
GOMB_MERET = 14
#: a nagy állapot plafonja (`0x00cf4e40` = 392,0)
NAGY_PLAFON = 392
#: a nagy állapot aránya (`0x00cf3ae0` = 0,3)
NAGY_ARANY = 0.3


def _gyerek(gyoker, nev):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _var_a_szelessegre(fiok, qt_app, vart, korok: int = 40) -> float:
    """Megvárja, amíg a fiók felveszi a kért szélességet.

    ⚠️ Egyetlen `processEvents` nem elég: a `SplitView` átméretezése egy
    POLISH körben történik, és a csökkentés MÉRVE néha csak a második
    körben ér el az elemig. Enélkül a próba a sorrend és a gép terhelése
    szerint bukott el (a #3037 első javítási kísérlete)."""
    for _ in range(korok):
        if abs(fiok.property("width") - vart) <= 1:
            break
        qt_app.processEvents()
    return fiok.property("width")


def _nyisd(window, qt_app, menu_nev):
    QMetaObject.invokeMethod(
        _gyerek(window, menu_nev), "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()


class TestEgyFiok:
    def test_a_negy_panel_UGYANABBAN_a_fiokban_ul(self, qml_app, qt_app):
        """A fő szerkezeti állítás: egy fiók, nem négy hasáb."""
        window, _controller, _engine = qml_app
        fiok = _gyerek(window, "rightDrawer")
        for _menu, panel in LAPOK:
            elem = _gyerek(window, panel)
            szulok = []
            p = elem.parent()
            while p is not None:
                szulok.append(p)
                p = p.parent()
            assert fiok in szulok, (
                f"a {panel} nem a fiókban van — külön hasábban ül"
            )

    @pytest.mark.parametrize("menu,panel", LAPOK)
    def test_MIND_a_negy_lapnal_280_a_fiok(self, qml_app, qt_app, menu, panel):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, menu)
        fiok = _gyerek(window, "rightDrawer")
        assert fiok.property("width") == ALAP_SZELESSEG, (
            f"a {panel} lapon a fiók {fiok.property('width')} széles, "
            f"nem {ALAP_SZELESSEG} — az eredetiben mind a négy azonos"
        )

    def test_mind_a_negy_panel_a_276_os_vasznon_ul(self, qml_app, qt_app):
        """A tartalom vászna 276 a 280-as fiókban — és MIND A NÉGY ugyanez.

        A régi állapotban a négy panel négy különböző szélességű volt; ez a
        próba azt tartja fenn, hogy egyetlen vászon maradt."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        tartalom = _gyerek(window, "rightDrawerContent")
        assert tartalom.property("width") == TARTALOM_SZELESSEG
        for menu, panel in LAPOK:
            _nyisd(window, qt_app, menu)
            elem = _gyerek(window, panel)
            assert elem.property("width") == TARTALOM_SZELESSEG, (
                f"a {panel} szélessége {elem.property('width')}, a vászon "
                f"{TARTALOM_SZELESSEG}"
            )


class TestAFejlec:
    def test_harminc_keppont_magas(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        fejlec = _gyerek(window, "rightDrawerHeader")
        assert fejlec.property("height") == FEJLEC_MAGASSAG

    def test_a_cim_KOZEPRE_igazodik(self, qml_app, qt_app):
        """`m_centerXY` — nem balra, ahogy nálunk a panelek fejlécében volt."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        fejlec = _gyerek(window, "rightDrawerHeader")
        cim = _gyerek(window, "rightDrawerTitle")
        kozep = cim.property("x") + cim.property("width") / 2
        assert abs(kozep - fejlec.property("width") / 2) <= 1, (
            f"a cím középpontja {kozep}, a fejléc közepe "
            f"{fejlec.property('width') / 2}"
        )

    def test_a_cim_a_MERT_felirat(self, qml_app, qt_app):
        """`rightdrawerpanel_text.tre:1` — a fiók neve, nem a panelé."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        assert _gyerek(window, "rightDrawerTitle").property("text") != ""

    @pytest.mark.parametrize("nev", ["rightDrawerSizeToggle", "rightDrawerClose"])
    def test_a_ket_gomb_14x14(self, qml_app, qt_app, nev):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        gomb = _gyerek(window, nev)
        assert (gomb.property("width"), gomb.property("height")) == (
            GOMB_MERET, GOMB_MERET
        )

    def test_a_bezaras_URITI_a_fiokot(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        assert window.property("activeDrawerTab") != ""

        QMetaObject.invokeMethod(
            _gyerek(window, "rightDrawerClose"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()

        assert window.property("activeDrawerTab") == "", (
            "a fejléc bezáró gombja nem ürítette a fiókot"
        )


class TestAKetSzelesseg:
    """#2529: a `size_toggle` a MÉRT két szélesség közt vált."""

    @staticmethod
    def _kicsire(window, qt_app):
        """Ismert állapotba visz: KATTINTÁSSAL, nem a tulajdonság írásával.

        ⚠️ A `nagy` tulajdonság közvetlen írása nem elég: a `SplitView` a
        kirajzolt szélességet csak akkor számolja újra, ha a kötés értéke
        MEGVÁLTOZIK. Ha ugyanarra az értékre írjuk, a fiók a régi
        szélességén marad — a CI-n ezért bukott el rendre a billentés
        próbája, miközben helyben átment (a próbák sorrendje döntötte el,
        mekkora fiókot örökölt)."""
        fiok = _gyerek(window, "rightDrawer")
        if fiok.property("nagy"):
            QMetaObject.invokeMethod(
                _gyerek(window, "rightDrawerSizeToggle"), "kattints",
                Qt.ConnectionType.DirectConnection,
            )
        _var_a_szelessegre(fiok, qt_app, ALAP_SZELESSEG)
        assert fiok.property("nagy") is False
        return fiok

    def test_a_nagy_allas_az_ablak_30_szazaleka(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        fiok = self._kicsire(window, qt_app)

        QMetaObject.invokeMethod(
            _gyerek(window, "rightDrawerSizeToggle"), "kattints",
            Qt.ConnectionType.DirectConnection,
        )
        vart = min(window.property("width") * NAGY_ARANY, NAGY_PLAFON)
        _var_a_szelessegre(fiok, qt_app, vart)
        assert abs(fiok.property("width") - vart) <= 1, (
            f"a nagy fiók {fiok.property('width')} széles, a mért képlet "
            f"szerint {vart} (az ablak 30 %-a, legfeljebb {NAGY_PLAFON})"
        )

    def test_visszavaltva_megint_280(self, qml_app, qt_app):
        """A fiók LÁTSZIK: csukott fiókot a `SplitView` nem méretez újra,
        tehát a szélessége a bezárás előtti maradna — az nem a billentés
        mérése volna."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, LAPOK[0][0])
        fiok = self._kicsire(window, qt_app)
        assert fiok.property("visible") is True
        assert fiok.property("width") == ALAP_SZELESSEG

        gomb = _gyerek(window, "rightDrawerSizeToggle")
        #: #3037: NÉGY kattintás, nem kettő. A hiba az volt, hogy a
        #: `SplitView` a növelést átvette, a csökkentést nem — a váltó
        #: egyszer működött, aztán beragadt a nagy fiók. Két kattintás ezt
        #: még elfedhetné, ha csak a végállapotot néznénk.
        nagy_vart = min(window.property("width") * NAGY_ARANY, NAGY_PLAFON)
        latott = []
        for kor in range(4):
            QMetaObject.invokeMethod(
                gomb, "kattints", Qt.ConnectionType.DirectConnection
            )
            vart = nagy_vart if kor % 2 == 0 else ALAP_SZELESSEG
            latott.append(_var_a_szelessegre(fiok, qt_app, vart))

        assert latott[1] == ALAP_SZELESSEG and latott[3] == ALAP_SZELESSEG, (
            f"a váltó nem vált vissza kicsire: a négy szélesség {latott}"
        )
        assert latott[0] > ALAP_SZELESSEG and latott[2] > ALAP_SZELESSEG, (
            f"a váltó nem nagyít: a négy szélesség {latott}"
        )


class TestAGyorscimkek:
    """A tíz gyorscímke-gomb MÉRT elrendezése: 2 · 3 · 2 · 3 (nem 5 · 5).

    A spec 3. szakasza: a kettes sorok gombjai 128–129 képpont szélesek, a
    hármas sorokéi 85, és az 1. meg a 2. sor közt 3 képpontos elválasztó
    áll. Előtte két ötös sor volt nálunk."""

    VART_SOROK = [2, 3, 2, 3]

    def test_negy_sorban_allnak(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, "menuViewTags")
        for index, darab in enumerate(self.VART_SOROK):
            sor = _gyerek(window, f"quickTagsRow{index}")
            gombok = [
                gy for gy in sor.children()
                if (gy.objectName() or "").startswith("quickTagButton")
            ]
            assert len(gombok) == darab, (
                f"a {index}. sorban {len(gombok)} gomb van, nem {darab}"
            )

    def test_van_elvalaszto_az_elso_ket_sor_kozt(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, "menuViewTags")
        elvalaszto = _gyerek(window, "quickTagsDivider")
        assert elvalaszto.property("height") == 3

    def test_a_ketes_sor_gombjai_SZELESEBBEK(self, qml_app, qt_app):
        """A mért 128–129 vs. 85 — a viszonyt mérjük, mert a vászon
        szélessége a fiók állapotától is függ."""
        window, _controller, _engine = qml_app
        _nyisd(window, qt_app, "menuViewTags")
        kettes = _gyerek(window, "quickTagButton0").property("width")
        harmas = _gyerek(window, "quickTagButton2").property("width")
        assert kettes > harmas, (
            f"a kettes sor gombja {kettes}, a hármasé {harmas} — a mért "
            "elrendezésben a kettes sor gombjai szélesebbek"
        )
