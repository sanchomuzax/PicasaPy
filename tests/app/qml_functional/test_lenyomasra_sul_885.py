"""#885: 49 vezérlő LENYOMÁSRA sül el az eredetiben, nem felengedésre.

## A mérés forrása

`Property mousedown 1` a `runtime/respack.yt` `.tre` leírásaiban — 49 elem,
és a csoportosításuk következetes: ami **nézetet vált vagy menüt nyit**,
az azonnal hat; ami **műveletet hajt végre** (Mentés, Mégse, Kollázs
létrehozása), az a szabványos felengedésre.

Ellenpélda ugyanabból a forrásból: a `Mégse` gombokon nincs `mousedown`,
viszont 11 helyen van `Property escapekey 1`.

## Amit ez a próba mér

A `PicasaButton` opt-in kapcsolóját (`lenyomasra`) és azt, hogy a
felsorolt vezérlőkön BE van kapcsolva, a művelet-gombokon pedig NINCS. A
kapcsoló nélkül a Qt alapértelmezése (felengedés) marad, és a felület
érezhetően lomhább ugyanazokon a helyeken.

⚠️ A próba a VISELKEDÉST méri: lenyomásra elsül-e a jelzés, és
felengedéskor nem sül-e el MÁSODSZOR. A puszta tulajdonság-olvasás azt
nem mutatná meg, hogy a gomb kétszer hat.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import Qt, QUrl
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QTest

_QML = Path(picasapy.app.__file__).parent / "qml"

#: a mért csoportok közül azok, amelyeknek MA van vezérlőjük nálunk
LENYOMASRA = [
    "viewerPrevButton",
    "viewerNextButton",
    "faceFilter",
    "movieFilter",
    "geoFilter",
    "dupeFilter",
    "toolbarFlatViewButton",
    "toolbarTreeViewButton",
]

#: a szerkesztő öt füle — `editpanel/tab1`…`tab5`
EDITOR_FULEK = ["editTab0", "editTab1", "editTab2"]

#: MŰVELET-gombok: ezeken NINCS `mousedown` az eredetiben sem — itt a
#: „lenyomtam, de elhúztam, mégsem" visszavonhatóság a fontos
FELENGEDESRE = [
    "toolbarImportButton",
    "toolbarNewAlbumButton",
]


def _lenyom(gomb, qt_app):
    """VALÓDI egér-lenyomás az ABLAKON, a gomb közepére.

    ⚠️ A `QCoreApplication.sendEvent(item, …)` nem elég: a Qt Quick az
    egéreseményeket az ABLAK-on át kézbesíti és ott dönt a megfogásról, egy
    elemre küldött szintetikus esemény pedig a `MouseArea`-ig el sem jut."""
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mousePress(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _felenged(gomb, qt_app):
    kozep = gomb.mapToScene(gomb.boundingRect().center())
    QTest.mouseRelease(
        gomb.window(), Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


@pytest.fixture
def gomb(qt_app):
    """Egyetlen `PicasaButton`, izoláltan — a kapcsoló a komponensé."""
    nezet = QQuickView()
    nezet.engine().addImportPath(str(_QML))
    nezet.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy" / "PicasaButton.qml")))
    assert nezet.status() == QQuickView.Status.Ready, [
        h.toString() for h in nezet.errors()
    ]
    elem = nezet.rootObject()
    elem.setProperty("width", 60)
    elem.setProperty("height", 24)
    nezet.show()
    qt_app.processEvents()
    yield elem, qt_app
    nezet.deleteLater()


class TestAKapcsolo:
    def test_alapbol_FELENGEDESRE_sul(self, gomb):
        """A többségnek ez a helyes: elhúzva vissza lehet vonni."""
        elem, qt_app = gomb
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        assert szamlalo == [], "lenyomásra elsült, pedig nem kértük"
        _felenged(elem, qt_app)
        assert szamlalo == [1]

    def test_bekapcsolva_LENYOMASRA_sul(self, gomb):
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == [1], "a gomb nem sült el lenyomásra"

    def test_felengedeskor_NEM_sul_el_masodszor(self, gomb):
        """A kétszeres hatás rosszabb a lomhaságnál: egy fülváltó kétszer
        váltana, egy léptető kettőt lépne."""
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        _felenged(elem, qt_app)

        assert szamlalo == [1], f"a gomb {len(szamlalo)}-szor sült el"

    def test_TILTOTT_gomb_nem_sul_el(self, gomb):
        elem, qt_app = gomb
        elem.setProperty("lenyomasra", True)
        elem.setProperty("enabled", False)
        qt_app.processEvents()
        szamlalo = []
        elem.clicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == []


class TestAHasznalatiHelyek:
    """A mért lista: melyik vezérlőn van bekapcsolva, és melyiken nincs."""

    @pytest.mark.parametrize("nev", LENYOMASRA)
    def test_a_nezetvaltok_es_leptetok_lenyomasra(self, qml_app, nev):
        from PySide6.QtCore import QObject

        window = qml_app[0]
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"{nev} nem található"
        assert elem.property("lenyomasra") is True, (
            f"a(z) {nev} felengedésre sül el, pedig az eredetiben "
            "`mousedown` van rajta (#885)"
        )

    @pytest.mark.parametrize("nev", FELENGEDESRE)
    def test_a_MUVELET_gombok_felengedesre(self, qml_app, nev):
        from PySide6.QtCore import QObject

        window = qml_app[0]
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"{nev} nem található"
        assert not elem.property("lenyomasra"), (
            f"a(z) {nev} lenyomásra sül el, pedig művelet-gomb — elhúzva "
            "vissza kell tudni vonni"
        )


class TestASzerkesztoFulek:
    """`editpanel/tab1`…`tab5`: a fülváltás NÉZETET vált, tehát azonnal hat.

    ⚠️ Ez FORRÁS-szintű állítás, nem viselkedési: a fülgomb `required
    property`-kkel épül (a gazda `EditorPanel`-t várja), tehát önmagában
    nem tölthető be, és így nem is nyomható meg. A viselkedési oldalt a
    `PicasaButton` próbái fedik — ott a kétszeres elsülés is mérve van."""

    def test_a_fulgomb_lenyomasra_valt(self):
        forras = (_QML / "PicasaPy" / "EditTabButton.qml").read_text(
            encoding="utf-8"
        )
        assert "onPressed: panel.activeTab" in forras, (
            "a fülgomb nem lenyomásra vált (#885)"
        )
        assert "onClicked: panel.activeTab" not in forras


#: `edittextpanel` — a szövegformázás hat gombja, MÉRT `mousedown`
#: (`bold`, `italic`, `underline`, `leftalign`, `centeralign`, `rightalign`).
#: Az `outline` kimarad: nálunk nem gomb, hanem szín + vastagság-csúszka.
SZOVEGFORMAZO = [
    "textBoldButton",
    "textItalicButton",
    "textUnderlineButton",
    "textAlign_left",
    "textAlign_center",
    "textAlign_right",
]


@pytest.fixture
def panelgomb(qt_app):
    """Egyetlen `PanelButton`, izoláltan — a kapcsoló a komponensé."""
    nezet = QQuickView()
    nezet.engine().addImportPath(str(_QML))
    nezet.setSource(QUrl.fromLocalFile(str(_QML / "PicasaPy" / "PanelButton.qml")))
    assert nezet.status() == QQuickView.Status.Ready, [
        h.toString() for h in nezet.errors()
    ]
    elem = nezet.rootObject()
    elem.setProperty("label", "B")
    elem.setProperty("width", 40)
    elem.setProperty("height", 24)
    nezet.show()
    qt_app.processEvents()
    yield elem, qt_app
    nezet.deleteLater()


class TestAPanelGombKapcsoloja:
    """A `PanelButton` ugyanazt az opt-in kapcsolót kapja, mint a
    `PicasaButton` — de itt nagyobb a tét: ez a komponens viszi az
    effekt-csempéket és az `Alkalmaz`/`Mégse` gombokat is, tehát az
    alapértelmezésnek FELENGEDÉSRE kell maradnia."""

    def test_alapbol_FELENGEDESRE_sul(self, panelgomb):
        elem, qt_app = panelgomb
        szamlalo = []
        elem.buttonClicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        assert szamlalo == [], "lenyomásra elsült, pedig nem kértük"
        _felenged(elem, qt_app)
        assert szamlalo == [1]

    def test_bekapcsolva_LENYOMASRA_sul(self, panelgomb):
        elem, qt_app = panelgomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.buttonClicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == [1], "a panel-gomb nem sült el lenyomásra"

    def test_felengedeskor_NEM_sul_el_masodszor(self, panelgomb):
        elem, qt_app = panelgomb
        elem.setProperty("lenyomasra", True)
        qt_app.processEvents()
        szamlalo = []
        elem.buttonClicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)
        _felenged(elem, qt_app)

        assert szamlalo == [1], f"a panel-gomb {len(szamlalo)}-szor sült el"

    def test_TILTOTT_gomb_nem_sul_el(self, panelgomb):
        elem, qt_app = panelgomb
        elem.setProperty("lenyomasra", True)
        elem.setProperty("buttonEnabled", False)
        qt_app.processEvents()
        szamlalo = []
        elem.buttonClicked.connect(lambda: szamlalo.append(1))

        _lenyom(elem, qt_app)

        assert szamlalo == []


class TestASzovegformazas:
    """FORRÁS-szintű állítás: a `edittextpanel` a szerkesztő szövegfülén
    él, amit a rácsból nem lehet állapotba hozni a próbán. A viselkedést a
    `TestAPanelGombKapcsoloja` méri, itt a BEKÖTÉS a kérdés."""

    @pytest.mark.parametrize("nev", SZOVEGFORMAZO)
    def test_a_formazo_gombok_lenyomasra(self, nev):
        forras = (_QML / "PicasaPy" / "EditorTextPanel.qml").read_text(
            encoding="utf-8"
        )
        # a gomb blokkja: az objectName sorától a következő objectName-ig
        kezd = forras.index(f'objectName: "{nev}"')
        kovetkezo = forras.find("objectName:", kezd + 10)
        blokk = forras[kezd : kovetkezo if kovetkezo > 0 else len(forras)]
        assert "lenyomasra: true" in blokk, (
            f"a(z) {nev} felengedésre sül el, pedig az eredetiben "
            "`mousedown` van rajta (#885)"
        )

    def test_az_ALKALMAZ_es_MEGSE_marad_felengedesre(self):
        """Ellenpróba ugyanabból a fájlból: a művelet-gombokon NINCS."""
        forras = (_QML / "PicasaPy" / "EditorTextPanel.qml").read_text(
            encoding="utf-8"
        )
        for nev in ("textApplyButton", "textCancelButton", "textRemoveAllButton"):
            kezd = forras.index(f'objectName: "{nev}"')
            kovetkezo = forras.find("objectName:", kezd + 10)
            blokk = forras[kezd : kovetkezo if kovetkezo > 0 else len(forras)]
            assert "lenyomasra" not in blokk, (
                f"a(z) {nev} művelet-gomb, elhúzva vissza kell tudni vonni"
            )


#: `headerpanel` — a mappa-fejléc mért `mousedown`-gombjai. ⚠️ FORRÁS-szintű
#: állítás: a `LightboxHeader` a rácsfejlécben él, és a próba
#: alap-állapotában (mappa nélkül) nem jön létre — a `findChild` `None`-t ad
#: rá. A viselkedést a `PicasaButton` saját próbái fedik.
FEJLEC_LENYOMASRA = [
    "headerSelectStarredButton",
    "headerCollageButton",
]


class TestAFejlecGombjai:
    @pytest.mark.parametrize("nev", FEJLEC_LENYOMASRA)
    def test_a_fejlec_gombjai_lenyomasra(self, nev):
        forras = (_QML / "PicasaPy" / "LightboxHeader.qml").read_text(
            encoding="utf-8"
        )
        kezd = forras.index(f'objectName: "{nev}"')
        kovetkezo = forras.find("objectName:", kezd + 10)
        blokk = forras[kezd : kovetkezo if kovetkezo > 0 else len(forras)]
        assert "lenyomasra: true" in blokk, (
            f"a(z) {nev} felengedésre sül el, pedig az eredetiben "
            "`mousedown` van rajta (#885)"
        )

    def test_a_MENTES_marad_felengedesre(self):
        """Ellenpróba ugyanabból a fájlból: a `save_edits` művelet-gomb."""
        forras = (_QML / "PicasaPy" / "LightboxHeader.qml").read_text(
            encoding="utf-8"
        )
        kezd = forras.index('objectName: "headerSaveEditsButton"')
        vege = forras.find("objectName:", kezd + 10)
        assert "lenyomasra" not in forras[kezd:vege], (
            "a mentés lenyomásra sül el, pedig művelet-gomb"
        )


class TestAMenutNyitoEsLejatszo:
    """`headerpanel/play` és `thumbui/folderviewpopup`: mindkettő
    `TapHandler`-rel épült, tehát nem a `lenyomasra` kapcsoló érvényes
    rájuk, hanem a kezelő MEGVÁLASZTÁSA."""

    def test_a_lejatszo_gomb_lenyomasra(self):
        forras = (_QML / "PicasaPy" / "LightboxHeader.qml").read_text(
            encoding="utf-8"
        )
        kezd = forras.index('objectName: "headerPlayButton"')
        blokk = forras[kezd : forras.index("PicasaButton {", kezd)]
        assert "onPressedChanged" in blokk and "playRequested" in blokk, (
            "a fejléc lejátszó gombja nem lenyomásra hat (#885)"
        )
        assert "onTapped" not in blokk, "felengedésre is elsül — kétszer hatna"

    def test_a_mappanezet_lenyilo_lenyomasra(self):
        forras = (_QML / "PicasaPy" / "MainToolbar.qml").read_text(
            encoding="utf-8"
        )
        kezd = forras.index('objectName: "toolbarFolderViewPopupButton"')
        vege = forras.find("objectName:", kezd + 10)
        blokk = forras[kezd:vege]
        assert "onPressedChanged" in blokk and "folderViewMenuRequested" in blokk, (
            "a mappanézet-lenyíló nem lenyomásra nyílik (#885)"
        )
        assert "onTapped" not in blokk


#: `Property normalcursor 1` — 16 elem, amely GOMB, de NEM vált kéz-kurzorra.
#: A mért lista (a jegy törzse): `headerpanel/create_movie`, `create_collage`,
#: `select_star`, `sync_options`, `websync0`, `websync1` ·
#: `faceheaderpanel/websync0` · `thumbui/folderviewpopup` · `throttle/pageup`,
#: `pagedown` · `bigslider/bigslider` · `acquirepanel/sync_options_button`,
#: `add_groups_button` · `compose_share/add_groups_button`, `composeclip`.
#:
#: Ezek közül nálunk ma ezeknek van vezérlőjük:
NORMALCURSOR_NALUNK = {
    "headerCollageButton": "PicasaPy/LightboxHeader.qml",
    "headerSelectStarredButton": "PicasaPy/LightboxHeader.qml",
    "headerPlayButton": "PicasaPy/LightboxHeader.qml",
    "toolbarFolderViewPopupButton": "PicasaPy/MainToolbar.qml",
}


class TestANyilKurzorMarad:
    """A mért `normalcursor` pont — MÉRVE már teljesül, de nem volt rá őr.

    ⚠️ Ez a lap azt rögzíti, ami MA igaz: ezeken a vezérlőkön nem állítunk
    kéz-kurzort. A kapu azért kell, mert a hiány NÉMA — ha valaki később
    „szebbnek" találja a kéz-kurzort és hozzáteszi, semmi nem szólna, pedig
    az eredeti mérése szerint ezek a gombok nyíl-kurzorral maradnak.

    A próba FORRÁS-szintű: a kurzor-alak a `HoverHandler`/`MouseArea`
    `cursorShape`-jén dől el, amit a futásidejű objektumfáról nem lehet
    megbízhatóan visszaolvasni (a `HoverHandler` nem `Item`, és a
    `cursorShape` csak lebegéskor hat)."""

    @pytest.mark.parametrize(("nev", "fajl"), sorted(NORMALCURSOR_NALUNK.items()))
    def test_nem_valt_kez_kurzorra(self, nev: str, fajl: str) -> None:
        forras = (_QML / fajl).read_text(encoding="utf-8")
        kezd = forras.index(f'objectName: "{nev}"')
        kovetkezo = forras.find("objectName:", kezd + 10)
        blokk = forras[kezd : kovetkezo if kovetkezo > 0 else len(forras)]
        assert "PointingHandCursor" not in blokk, (
            f"a(z) {nev} kéz-kurzorra vált, pedig az eredetiben "
            "`Property normalcursor 1` van rajta (#885)"
        )

    def test_a_proba_TALALNA_kez_kurzort(self) -> None:
        """A mérőt is mérjük: van a kódban ismert pozitív, amit a minta elkap.

        A verzió-címke (`MainToolbar.qml`) SZÁNDÉKOSAN kéz-kurzoros — az
        hivatkozás, nem gomb. Ha ezt sem találná meg a próba, a fenti négy
        állítás vakon menne át."""
        forras = (_QML / "PicasaPy" / "MainToolbar.qml").read_text(
            encoding="utf-8"
        )
        kezd = forras.index('objectName: "versionCursor"')
        kovetkezo = forras.find("objectName:", kezd + 10)
        assert "PointingHandCursor" in forras[kezd:kovetkezo]
