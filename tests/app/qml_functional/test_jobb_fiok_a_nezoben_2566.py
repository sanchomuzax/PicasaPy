"""#2566: a jobb fiók négy lapja a NÉZŐBEN/SZERKESZTŐBEN is nyílik.

## Amit a felhasználó látott

A képtálca négy kapcsolója (Emberek / Helyek / Címkék / Tulajdonságok)
benyomódott a szerkesztőben, és **nem történt semmi**.

## A gyökérok — mérve

A négy panel a könyvtár `SplitView`-jének (`mainSplit`) KÖZVETLEN gyermeke
volt, azt pedig a néző elrejti (`visible: !viewerOpen && …`). A gomb tehát
helyesen állította az `activeDrawerTab`-ot, csak a panel a rejtett hasábban
ült. Kivétel a Tulajdonságok: annak a #192 óta VAN párja a nézőn belül —
ez a fájl ezt is méri, hogy a négyes együtt maradjon.

## Miért így oldottuk meg

`thumbui.tre:526`/`:533` szerint a `right_drawer` a `mainuipanel` gyereke,
és a szerkesztő-módot leíró `macros.tre:204` (`m_albumtoggle`) TÉTELESEN
sorolja fel, mit rejt el — a `right_drawer` és a `mainuipanel` nincs
köztük. Az eredetiben tehát a fiók a szerkesztőben is elérhető.

A megvalósítás a #192 mintáját folytatja: a néző a saját jobb hasábjában
hozza a panelt (`RowLayout`, a kép-terület mellett), nem a könyvtár
`SplitView`-jét kell életben tartani a néző alatt. Ezért ez a fájl
KÉT dolgot állít, egyenlő súllyal:

1. a fiók a nézőben nyílik és záródik (`TestANegyLapANezobenIsNyilik`,
   `TestANezoHelyetHagyAFioknak`, `TestANezettKepreHat`);
2. a KÖNYVTÁR viselkedése képpontra ugyanaz maradt
   (`TestAKonyvtarValtozatlan`) — a jegy súlypontja ez.
"""

import time

import pytest
from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

# (fiók-lap neve, a nézőbeli panel objectName-je, a könyvtárbeli párja,
#  a könyvtárbeli SplitView-szélesség)
#: #754: a negyedik érték a KÖNYVTÁRI panel kirajzolt szélessége. Eddig
#: négy különböző szám állt itt (200 · 320 · 190 · 210) — az a mi régi,
#: mérés nélküli állapotunk volt. Az eredetiben EGY fiók van, 280 képpont,
#: benne 276-os tartalom-vászon (`docs/specs/jobb-fiok-meretek.md`), és
#: mind a négy lap ugyanazt a vásznat kapja.
A_NEGY_LAP = [
    ("people", "viewerPeoplePanel", "peoplePanel", 276),
    ("places", "viewerPlacesPanel", "placesPanel", 276),
    ("tags", "viewerTagsPanel", "tagsPanel", 276),
    ("properties", "viewerPropertiesPanel", "propertiesPanel", 276),
]


# --------------------------------------------------------------------------
# Segédek
# --------------------------------------------------------------------------
def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _keres(window, nev: str):
    """A KIRAJZOLT jelenetből először, aztán a QObject-fából.

    A footer (képtálca) nem a `contentItem` gyereke, ezért kell a
    `findChild`-os ág is."""
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    return window.findChild(QObject, nev)


def _elem(window, nev: str):
    talalt = _keres(window, nev)
    assert talalt is not None, f"a(z) {nev} nincs a jelenetben"
    return talalt


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
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _ablakban(item: QQuickItem) -> tuple[float, float, float, float]:
    sarok = item.mapToScene(item.boundingRect().topLeft())
    return (sarok.x(), sarok.y(), item.width(), item.height())


def _kattints(window, item: QQuickItem, qt_app) -> None:
    """VALÓDI kattintás, STABIL geometria után (a #985/#1026 mintája)."""
    assert _var(qt_app, lambda: item.width() > 0 and item.height() > 0), (
        f"a(z) {item.objectName()} nem kapott méretet, nem lehet rákattintani"
    )
    kozep = item.mapToScene(item.boundingRect().center())
    elozo = (kozep.x(), kozep.y())
    _var(
        qt_app,
        lambda: (
            item.mapToScene(item.boundingRect().center()).x(),
            item.mapToScene(item.boundingRect().center()).y(),
        )
        == elozo,
        1.0,
    )
    kozep = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()
    QTest.qWait(30)
    qt_app.processEvents()


def _leszarmazottja(item: QQuickItem, os: QQuickItem) -> bool:
    """A `SplitView` a gyerekeit a saját contentItem-jébe teszi, tehát a
    közvetlen szülő nem a `mainSplit` — a LÁNCOT kell nézni."""
    szulo = item.parentItem()
    while szulo is not None:
        if szulo is os:
            return True
        szulo = szulo.parentItem()
    return False


def _talca_gomb(window, lap: str) -> QQuickItem:
    return _elem(window, "trayPanelToggle_" + lap)


def _nezot_nyit(window, qt_app, index: int = 0):
    window.setProperty("viewerOpen", True)
    viewer = _elem(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    assert _var(qt_app, viewer.isVisible), "a néző nem lett látható"
    return viewer


def _fiokot_urit(window, qt_app) -> None:
    window.setProperty("activeDrawerTab", "")
    qt_app.processEvents()


@pytest.fixture
def qml_app(qml_app_module):
    """#2851: az ablakot a MODUL építi EGYSZER, nem tesztenként.

    Ez a fájl nem ír tartós állapotot (se ini-t, se beállítást, se fájlt) —
    csak felületi kötéseket és geometriát mér. A tesztek közti felület-
    állapotot a `_tiszta_indulas` autouse fixture nullázza, ami eddig is
    futott: zárt néző, üres fiók, üres kijelölés, 1280 × 800.

    Mérve (#2851): 18 teszt × egy-egy ablaképítés 59,2 s volt; egyetlen
    ablakkal 9,3 s — a fájl ideje HATODÁRA esett. A kimondott feltétel az
    állapotmentesség: ha ide állapotot író teszt kerül, ezt az `override`-ot
    kell törölni, nem a nullázást bővíteni."""
    return qml_app_module


@pytest.fixture(autouse=True)
def _tiszta_indulas(qml_app, qt_app):
    """Minden teszt zárt fiókkal és zárt nézővel indul."""
    window = qml_app[0]
    window.resize(1280, 800)
    window.setProperty("viewerOpen", False)
    window.setProperty("activeDrawerTab", "")
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()
    yield


# --------------------------------------------------------------------------
# 1. A négy lap a NÉZŐBEN is nyílik — VALÓDI kattintással a tálca gombjára
# --------------------------------------------------------------------------
class TestANegyLapANezobenIsNyilik:
    @pytest.mark.parametrize("lap,nezo_panel,_konyvtari,_szel", A_NEGY_LAP)
    def test_a_talca_gombja_megnyitja_a_panelt(
        self, qml_app, qt_app, lap, nezo_panel, _konyvtari, _szel
    ):
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        gomb = _talca_gomb(window, lap)
        assert gomb.isVisible(), (
            f"a(z) „{lap}” kapcsoló nem látszik a nézőben — a képtálca a "
            "nézőben is ott van (`libraryFrameVisible`)"
        )
        _kattints(window, gomb, qt_app)
        assert window.property("activeDrawerTab") == lap
        panel = _keres(window, nezo_panel)
        assert panel is not None, (
            f"a(z) „{lap}” gombra nem jött létre a {nezo_panel} — ez a jegy "
            "hibája: a gomb benyomódik, és nem történik semmi"
        )
        assert _var(qt_app, panel.isVisible), (
            f"a {nezo_panel} létrejött, de nem látszik"
        )
        assert panel.width() > 0 and panel.height() > 0

    @pytest.mark.parametrize("lap,nezo_panel,_konyvtari,_szel", A_NEGY_LAP)
    def test_ugyanarra_a_gombra_ujra_kattintva_bezarul(
        self, qml_app, qt_app, lap, nezo_panel, _konyvtari, _szel
    ):
        """A mai `aktiv ? "" : nev` logika a nézőben is érvényes (#1773)."""
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        gomb = _talca_gomb(window, lap)
        _kattints(window, gomb, qt_app)
        assert window.property("activeDrawerTab") == lap
        _kattints(window, gomb, qt_app)
        assert window.property("activeDrawerTab") == "", (
            "az aktív gombra újra kattintva a fióknak ürülnie kell"
        )
        panel = _keres(window, nezo_panel)
        assert panel is None or not panel.isVisible()

    def test_egyszerre_csak_egy_lap_latszik_a_nezoben(self, qml_app, qt_app):
        """A fiók RÁDIÓ-csoport (#1773) — a nézőben is."""
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        for lap, nezo_panel, _k, _sz in A_NEGY_LAP:
            _kattints(window, _talca_gomb(window, lap), qt_app)
            lathato = [
                nev
                for _l, nev, _kk, _s in A_NEGY_LAP
                if (_keres(window, nev) is not None)
                and _keres(window, nev).isVisible()
            ]
            assert lathato == [nezo_panel], (
                f"a(z) „{lap}” lapon ez látszik: {lathato}"
            )

    def test_a_panel_sajat_bezaro_gombja_uriti_a_fiokot(self, qml_app, qt_app):
        """A panel `closeRequested` jele a nézőben is a közös kapcsolót viszi."""
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        panel = _elem(window, "viewerTagsPanel")
        panel.metaObject().invokeMethod(panel, "closeRequested")
        qt_app.processEvents()
        assert window.property("activeDrawerTab") == ""


# --------------------------------------------------------------------------
# 2. A néző HELYET HAGY a fióknak — a kép nem tűnik el alatta
# --------------------------------------------------------------------------
class TestANezoHelyetHagyAFioknak:
    @pytest.mark.parametrize("lap,nezo_panel,_konyvtari,_szel", A_NEGY_LAP)
    def test_a_panel_nem_fedi_a_kepteruletet(
        self, qml_app, qt_app, lap, nezo_panel, _konyvtari, _szel
    ):
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, lap), qt_app)
        panel = _elem(window, nezo_panel)
        kep = _elem(window, "viewerPhotoArea")
        assert _var(qt_app, lambda: panel.width() > 0 and kep.width() > 0)
        p_x, _p_y, p_w, _p_h = _ablakban(panel)
        k_x, _k_y, k_w, _k_h = _ablakban(kep)
        assert k_x + k_w <= p_x + 1, (
            f"a(z) „{lap}” panel ({p_x:.0f}…{p_x + p_w:.0f}) átfedi a "
            f"képterületet ({k_x:.0f}…{k_x + k_w:.0f})"
        )

    @pytest.mark.parametrize("lap,nezo_panel,_konyvtari,_szel", A_NEGY_LAP)
    def test_a_panel_az_ablakon_BELUL_van(
        self, qml_app, qt_app, lap, nezo_panel, _konyvtari, _szel
    ):
        """Nem elég nem fedni: a fiók nem lóghat ki az ablakból sem."""
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, lap), qt_app)
        panel = _elem(window, nezo_panel)
        assert _var(qt_app, lambda: panel.width() > 0)
        p_x, _p_y, p_w, _p_h = _ablakban(panel)
        assert p_x >= -1 and p_x + p_w <= window.width() + 1, (
            f"a(z) „{lap}” panel {p_x:.0f}…{p_x + p_w:.0f}, az ablak "
            f"0…{window.width()}"
        )

    def test_a_kepterulet_a_fiok_szelessegevel_szukul(self, qml_app, qt_app):
        """A MÉRT szám: a kép pont annyit veszít, amennyit a fiók elvesz."""
        window = qml_app[0]
        _nezot_nyit(window, qt_app)
        kep = _elem(window, "viewerPhotoArea")
        assert _var(qt_app, lambda: kep.width() > 0)
        elotte = kep.width()
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        panel = _elem(window, "viewerTagsPanel")
        assert _var(qt_app, lambda: panel.width() > 0 and kep.width() < elotte)
        assert abs((elotte - kep.width()) - panel.width()) <= 2, (
            f"a képterület {elotte:.0f} → {kep.width():.0f} px, a panel "
            f"{panel.width():.0f} px széles — nem egyezik"
        )
        _fiokot_urit(window, qt_app)
        assert _var(qt_app, lambda: abs(kep.width() - elotte) <= 1), (
            "a fiók bezárása után a kép nem kapta vissza a helyét"
        )


# --------------------------------------------------------------------------
# 3. A fiók a NÉZETT képre hat, nem a rács kijelölésére
# --------------------------------------------------------------------------
class TestANezettKepreHat:
    def test_a_cimkek_a_nezett_kepet_kovetik(self, qml_app, qt_app):
        """A néző léptetése csak a `selectedIndex`-et írja, a listát nem.

        Ha a panel a rács kijelölésére kötne, a 0. kép címkéit mutatná az
        1. képen állva is."""
        window, controller, _engine = qml_app
        controller.addKeywordToRows([1], "kutya")
        qt_app.processEvents()
        _nezot_nyit(window, qt_app, index=0)
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        panel = _elem(window, "viewerTagsPanel")
        assert list(panel.property("tags") or []) == []
        viewer = _elem(window, "photoViewer")
        viewer.setProperty("currentIndex", 1)
        assert _var(
            qt_app, lambda: list(panel.property("tags") or []) == ["kutya"]
        ), (
            "a Címkék-panel a nézőben nem a NÉZETT kép címkéit mutatja: "
            f"{list(panel.property('tags') or [])}"
        )

    def test_a_tulajdonsagok_is_a_nezett_kepet_kovetik(self, qml_app, qt_app):
        """A #192 útja változatlan — a négyes együtt mozog."""
        window = qml_app[0]
        viewer = _nezot_nyit(window, qt_app, index=0)
        _kattints(window, _talca_gomb(window, "properties"), qt_app)
        panel = _elem(window, "viewerPropertiesPanel")

        def _ut() -> str:
            ertek = panel.property("entries")
            if hasattr(ertek, "toVariant"):
                ertek = ertek.toVariant()
            return {e["label"]: e["value"] for e in (ertek or [])}.get(
                "File Path", ""
            )

        assert _var(qt_app, lambda: _ut().endswith("a.jpg"))
        viewer.setProperty("currentIndex", 1)
        assert _var(qt_app, lambda: _ut().endswith("b.jpg"))


# --------------------------------------------------------------------------
# 4. A KÖNYVTÁR viselkedése VÁLTOZATLAN — a jegy súlypontja
# --------------------------------------------------------------------------
class TestAKonyvtarValtozatlan:
    @pytest.mark.parametrize("lap,_nezo,konyvtari,szelesseg", A_NEGY_LAP)
    def test_a_panel_a_konyvtar_SplitView_jeben_nyilik(
        self, qml_app, qt_app, lap, _nezo, konyvtari, szelesseg
    ):
        """Ugyanott, ugyanolyan szélességgel, ugyanabban a hasábban."""
        window = qml_app[0]
        oszto = _elem(window, "mainSplit")
        _kattints(window, _talca_gomb(window, lap), qt_app)
        panel = _elem(window, konyvtari)
        assert _var(qt_app, lambda: panel.isVisible() and panel.width() > 0)
        assert _leszarmazottja(panel, oszto), (
            f"a(z) {konyvtari} kikerült a könyvtár SplitView-jéből"
        )
        #: A `SplitView` csatolt tulajdonságai Pythonból nem olvashatók
        #: (`property("SplitView.preferredWidth")` → None), ezért a
        #: KIRAJZOLT szélességet mérjük — az amúgy is erősebb állítás.
        assert abs(panel.width() - szelesseg) <= 1, (
            f"a(z) {konyvtari} {panel.width():.0f} px széles a könyvtárban, "
            f"a mért tartalom-vászon {szelesseg} (#754)"
        )
        #: #754: a panel a FIÓK vásznán ül, a fiók pedig a jobb szélen — a
        #: panel jobb éle ezért a fiók keretéig ér, nem az ablak széléig.
        fiok = _elem(window, "rightDrawer")
        f_x, _f_y, f_w, _f_h = _ablakban(fiok)
        assert abs((f_x + f_w) - window.width()) <= 1

    @pytest.mark.parametrize("lap,nezo_panel,_konyvtari,_szel", A_NEGY_LAP)
    def test_a_nezo_masodpeldanya_NEM_letezik_a_konyvtarban(
        self, qml_app, qt_app, lap, nezo_panel, _konyvtari, _szel
    ):
        """A nézőbeli példány csak nyitott néző mellett épülhet fel.

        Enélkül a `findChild` a KÖNYVTÁRI panel helyett a nézőbeli
        másodpéldányt találná meg (a komponensek a saját gyerekeikre égetik
        az objectName-et). A Tulajdonságok panel a #192 óta mohó — az
        kivétel, ezért csak a három új lapra állítunk."""
        if lap == "properties":
            pytest.skip("a #192 panelje szándékosan mohó — nem ez a jegy")
        window = qml_app[0]
        _kattints(window, _talca_gomb(window, lap), qt_app)
        assert window.property("activeDrawerTab") == lap
        assert _keres(window, nezo_panel) is None, (
            f"a nézőbeli {nezo_panel} csukott néző mellett is felépült"
        )

    def test_a_bal_hasab_szelessege_nem_valtozik(self, qml_app, qt_app):
        """A `folderPane` a néző és a fiók nyitogatásától sem mozdul.

        ⚠️ A `controller.folderPaneWidth`-hez hasonlítani NEM elég: a hasáb
        `onWidthChanged`-je 400 ms múlva VISSZAÍRJA a vezérlőbe a kirajzolt
        szélességet, tehát egy elrontott kötés magával rántaná az
        „elvárt" értéket is, és a mérés némán zöld maradna. Ezért a #587
        által mért ALAPÉRTÉKHEZ (240) mérünk."""
        window, controller, _engine = qml_app
        hasab = _elem(window, "folderPane")
        assert _var(qt_app, lambda: hasab.width() == 240), (
            f"a bal hasáb induláskor {hasab.width():.0f} px (#587: 240)"
        )
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        _nezot_nyit(window, qt_app)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert _var(qt_app, lambda: hasab.width() == 240), (
            f"a bal hasáb a néző-körút után {hasab.width():.0f} px"
        )
        assert controller.folderPaneWidth == 240, (
            f"a MENTETT szélesség is elmozdult: {controller.folderPaneWidth}"
        )

    def test_a_hasabelvalaszto_fogantyu_megvan(self, qml_app, qt_app):
        """A #322 fogható elválasztója a fiók mellett is ott van."""
        window = qml_app[0]
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        panel = _elem(window, "tagsPanel")
        assert _var(qt_app, panel.isVisible)
        fogantyuk = [
            item
            for item in _walk(window.contentItem())
            if item.objectName() == "folderPaneHandle" and item.isVisible()
        ]
        assert len(fogantyuk) == 2, (
            "nyitott fiók mellett KÉT látható fogantyú kell (bal hasáb és "
            f"a fiók), de {len(fogantyuk)} van"
        )
        #: ⚠️ A `visible: false` a fogantyún NEM mutációs próba: a
        #: `SplitView` maga állítja a fogantyú láthatóságát, tehát a kötést
        #: felülcsapja. A MÉRT szélesség és a szomszédosság viszont fog.
        for fogantyu in fogantyuk:
            assert fogantyu.width() == 6, (
                f"a fogantyú {fogantyu.width():.0f} px széles (#322: 6) — "
                "ennyivel nem lehet megfogni"
            )
        #: #754: a fogantyú a FIÓK bal éle mellett van, nem a panelé mellett
        #: — a panel a fiók 276-os vásznán ül, két képpont behúzással.
        fiok = _elem(window, "rightDrawer")
        f_x, _f_y, _f_w, _f_h = _ablakban(fiok)
        balra = [
            f
            for f in fogantyuk
            if abs((_ablakban(f)[0] + _ablakban(f)[2]) - f_x) <= 1
        ]
        assert balra, (
            "a fiók bal éle mellett nincs fogantyú — a fiók nem méretezhető"
        )

    def test_a_konyvtar_panelje_a_nezobol_visszaterve_ugyanaz(
        self, qml_app, qt_app
    ):
        """A néző nem semmisíti meg és nem is mozdítja el a könyvtár fiókját."""
        window = qml_app[0]
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        elotte = _elem(window, "tagsPanel")
        elotte_doboz = _ablakban(elotte)
        _nezot_nyit(window, qt_app)
        assert _var(qt_app, lambda: elotte.isVisible() is False), (
            "a könyvtár fiókja a nézőben is látszik — a `mainSplit` rejtve van"
        )
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        utana = _elem(window, "tagsPanel")
        assert utana is elotte, "a könyvtár fiókja újraépült"
        assert _var(qt_app, lambda: _ablakban(utana) == elotte_doboz), (
            f"a könyvtár fiókja elmozdult: {elotte_doboz} → {_ablakban(utana)}"
        )

    def test_a_mainSplit_lathatosaga_valtozatlan(self, qml_app, qt_app):
        """A könyvtár hasábja a nézőben rejtve, visszatérve látható."""
        window = qml_app[0]
        oszto = _elem(window, "mainSplit")
        assert _var(qt_app, oszto.isVisible)
        _nezot_nyit(window, qt_app)
        assert _var(qt_app, lambda: oszto.isVisible() is False)
        window.setProperty("viewerOpen", False)
        qt_app.processEvents()
        assert _var(qt_app, oszto.isVisible)


# --------------------------------------------------------------------------
# 5. A fiók KIFELÉ menő parancsai a nézőből
# --------------------------------------------------------------------------
class TestAFiokKifeleMenoParancsai:
    """Amit a panel nem hajthat végre maga, mert a néző eltakarná.

    A `TagsPanel` „ilyen címkéjű keresése" és a `PeoplePanel`
    személy-választása a KÖNYVTÁR rácsát cseréli le; a `PlacesPanel` két
    írási művelete pedig visszafordíthatatlan, tehát a gazda
    megerősítésén megy át. Mind a négy jelként hagyja el a nézőt."""

    def test_a_cimke_keresese_kivezet_a_nezobol(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        controller.addKeywordToRows([0], "kutya")
        qt_app.processEvents()
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, "tags"), qt_app)
        panel = _elem(window, "viewerTagsPanel")
        panel.findTaggedRequested.emit("kutya")
        qt_app.processEvents()
        assert window.property("viewerOpen") is False, (
            "a keresés a néző MÖGÖTT futott le — a találatokat nem látná senki"
        )
        assert _var(qt_app, lambda: controller.searchQuery == "kutya")

    def test_a_szemely_valasztasa_kivezet_a_nezobol(self, qml_app, qt_app):
        window, controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, "people"), qt_app)
        panel = _elem(window, "viewerPeoplePanel")
        panel.personChosen.emit("Anna")
        qt_app.processEvents()
        assert window.property("viewerOpen") is False
        assert _var(qt_app, lambda: controller.currentPersonName == "Anna")

    def test_a_hely_beallitasa_es_torlese_a_GAZDAHOZ_er(
        self, qml_app_friss, qt_app
    ):
        """A `PlacesPanel` két írási jele a nézőből is a gazdához megy.

        #2851: ez az EGYETLEN teszt a fájlban, ami tartós állapotot ír (a
        geocímkét a képre), ezért FRISS ablakot kap — a többi a modul közös
        ablakán fut.

        ⚠️ Az állítás a JEL ÚTJA, nem a megerősítés küszöbe: a
        `panelClearGeotagDialog.futtasd` küszöb alatt SZÁNDÉKOSAN nem
        kérdez (#2013, `cmp esi,5`), a próbakönyvtárban pedig két kép van.
        A küszöb-logikát a `test_hely_megerosites_2013.py` méri; itt az a
        kérdés, hogy a nézőből ugyanoda fut-e be a parancs, mint a
        könyvtárból."""
        qml_app = qml_app_friss
        window, controller, _engine = qml_app
        _nezot_nyit(window, qt_app)
        _kattints(window, _talca_gomb(window, "places"), qt_app)
        panel = _elem(window, "viewerPlacesPanel")
        assert len(controller.geoMarkers) == 0

        panel.setGeotagRequested.emit([0], 47.5, 19.0)
        assert _var(qt_app, lambda: len(controller.geoMarkers) == 1), (
            "a nézőből beállított hely nem került a képre — a jel nem ért "
            "el a gazdáig"
        )

        panel.clearGeotagRequested.emit([0])
        assert _var(qt_app, lambda: len(controller.geoMarkers) == 0), (
            "a nézőből indított geocímke-törlés nem futott le"
        )
