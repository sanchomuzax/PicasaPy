"""#3663: a kettős nézet gombsorának helye, a „Kijelölve" jelvény és a
képre kattintásos fókuszváltás — KIRAJZOLT próbával.

## A mérés (`docs/specs/ui-audit-editor.md` 3/b, élő mérés a #3665-ből)

* A három kapcsoló (`A` · `AB` · `AA`) és a két segédgomb (fókuszváltó,
  elrendezés-váltó) a filmszalag és a ▶ **UTÁN** áll, nem előtte — a #3013
  fordítva tette.
* A „Kijelölve" jelvény **szürke** (`#666666`), fehér **félkövér**
  felirattal — a #3013 tévesen `Theme.selectionBlue` kéket adott neki.
* A jelvény a `photoArea` UTÁN, azzal egy szinten (nem előtte, nem a `photo`
  Image gyerekeként) áll, hogy garantáltan a kép fölött rajzolódjon — a
  #3013 a kép ELÉ tette, ezért a kép időnként rátakart.
* A bal/jobb (fent/lent) képre kattintás áthelyezi az aktív oldalt — a
  #3013-ban ezt csak a `swap_2up_focus` gomb tette.
* A jelvény pontos HELYE a kirajzolt kép széléhez képest mérve (nem a
  befoglaló doboz sarkában) — ld. lent a `TestAJelvenyHelye*` osztályokat.

## Miért kell a KIRAJZOLT próba a fenti property-alapú próbák mellé

A tulajdonos szava (#2494 kapcsán, de itt is érvényes): „A TESZTEDNEK LÁTNIA
KELLETT VOLNA, NEM CSAK KISZÁMOLNIA." A korábbi kör (#3013) a jelvényt a
`photoArea` SAROKÁBA, a kép ELÉ tette — ez a hiba egyetlen `objectName`/
`property`-alapú vagy deklarációs-sorrend próbán nem bukott volna el, mert
azok nem néznek KÉPERNYŐ-KOORDINÁTÁT. A `TestAGombsorSorrendjeKirajzolva` és
a `TestAJelvenyHelye*` osztályok ezért 1280×1024-es offscreen ablakban
TÉNYLEG kirajzolják az AB módot (vízszintes ÉS függőleges elrendezésben),
`QTest.mouseClick`-kel (nem `invokeMethod("kattints")`-szal) váltanak
módot/fókuszt, és a `mapToScene()`-nel mért jelenet-koordinátákat vetik
össze az eredeti Picasa élő felvételén mért résekkel (`Colab EN 33`–`35`).
A gombsor-sorrendet is `mapToScene().x()` szerint mérik, nem a QML
deklarációs (gyerek-)sorrendből — az utóbbi eltérhetne a kirajzolt helytől.

## A mért rések (mindkét elrendezésben UGYANAZ a két állandó adja vissza)

* a képek síkjával PÁRHUZAMOS tengelyen (vízszintesben az osztó felé,
  függőlegesben a bal margó felé): kb. **61 px** (mérve: 60/62/61);
* a MERŐLEGES tengelyen (vízszintesben fölfelé a margóba, függőlegesben az
  osztó felé): kb. **27 px** (mérve: 27/28/26).

A tűrés (`TURES_*`) bőven meghagyja a mi UI-nk (más eszköztár-magasság, más
`photoArea`-margó) és az eredeti Picasa abszolút képernyő-elrendezése
közötti eltérést — ami számít, hogy a jelvény a KIRAJZOLT képhez képest a
megfelelő OLDALON és nagyságrendileg a megfelelő TÁVOLSÁGRA áll, nem a
`photoArea` sarkában (a #3013 hibája) vagy a kép ALATT/MÖGÖTT.

A négyzetes (1:1) próbakép szándékos: a referencia-felvételek is négyzetes
(1024×1024) fotókat mutatnak, és a `PreserveAspectFit` letterboxolása a kép
SAJÁT arányától függ — egy 320×160-as alapértelmezett próbaképnél egészen
más helyre esne a kirajzolt kép széle, mint amit a referencián mértünk.

## Ami NEM ebben van

A jelvény pontos pixel-helyének KÉPLETE a binárisból nem olvasható ki
(`ui-audit-editor.md` 3/b, „Bizonyítottsági fok" megjegyzés) — a mérce az
élő összevetés a Colab kulcsképekkel; a fenti tűrés ezt a bizonytalanságot
fedi le, nem egzakt pixel-egyezést állít.
"""

from __future__ import annotations

from PySide6.QtCore import (
    QObject,
    QPoint,
    QPointF,
    Q_ARG,
    QMetaObject,
    Qt,
)
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

#: a mért rések (px, 1280×1024-es referencia) — ld. a modul docstringjét
PARHUZAMOS_RES = 61
MEROLEGES_RES = 27
#: a mi UI-nk más abszolút elrendezéséhez adott tűrés
TURES_PARHUZAMOS = 12
TURES_MEROLEGES = 10

#: a mért gombsor-sorrend (`ui-audit-editor.md` 3/b.1): a filmszalag és a
#: ▶ UTÁN, jobbra.
GOMBSOR_SORREND = (
    "viewerPlayButton",
    "viewerPrevButton",
    "viewerFilmstrip",
    "viewerNextButton",
    "viewerLayoutOnly1up",
    "viewerLayoutAb",
    "viewerLayoutAa",
    "viewerSwapFocus",
    "viewerSwapLayout",
)


def _gyerek(gyoker, nev: str):
    objektum = gyoker.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _bal_x(elem) -> float:
    return elem.mapToScene(QPointF(0, 0)).x()


def _jobb_x(elem) -> float:
    return elem.mapToScene(QPointF(0, 0)).x() + elem.property("width")


def _klikk(qt_app, window, elem, x=None, y=None):
    """Valódi egérkattintás a JELENET-koordinátán — `QTest.mouseClick`,
    NEM `invokeMethod("kattints")`: az utóbbi megkerülné a `TapHandler`
    tényleges célterületét, tehát nem venné észre, ha az rossz helyen áll.
    """
    x = elem.property("width") / 2 if x is None else x
    y = elem.property("height") / 2 if y is None else y
    pont = elem.mapToScene(QPointF(x, y))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(int(pont.x()), int(pont.y())),
    )
    for _ in range(20):
        qt_app.processEvents()
    QTest.qWait(150)


def _kep_teglalap(kep) -> dict[str, float]:
    """A KIRAJZOLT (letterboxolt) kép téglalapja jelenet-koordinátában —
    NEM a befoglaló `photoElotte`/`photo` doboz, ami csak a `photoArea`
    felét kapja."""
    szel = kep.property("width")
    mag = kep.property("height")
    pszel = kep.property("paintedWidth")
    pmag = kep.property("paintedHeight")
    bal_felso = kep.mapToScene(QPointF((szel - pszel) / 2, (mag - pmag) / 2))
    return {
        "bal": bal_felso.x(),
        "fent": bal_felso.y(),
        "jobb": bal_felso.x() + pszel,
        "lent": bal_felso.y() + pmag,
    }


def _elem_teglalap(elem) -> dict[str, float]:
    szel = elem.property("width")
    mag = elem.property("height")
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return {
        "bal": bal_felso.x(),
        "fent": bal_felso.y(),
        "jobb": bal_felso.x() + szel,
        "lent": bal_felso.y() + mag,
    }


def _nezot_nyit(window, qt_app, *, meret=(1280, 1024)):
    window.resize(*meret)
    window.show()
    for _ in range(20):
        qt_app.processEvents()
    window.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = _gyerek(window, "photoViewer")
    QMetaObject.invokeMethod(
        nezo, "show", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    QTest.qWait(300)
    return nezo


def _ab_modba(window, qt_app, *, meret=(1280, 1024)):
    nezo = _nezot_nyit(window, qt_app, meret=meret)
    _klikk(qt_app, window, _gyerek(window, "viewerLayoutAb"))
    QTest.qWait(200)
    assert nezo.property("layoutMode") == "ab"
    return nezo


class TestAGombsorSorrendjeKirajzolva:
    def test_a_mert_sorrend_a_kepernyon(self, qml_app, qt_app):
        """A gombsor-sorrendet a KIRAJZOLT `mapToScene().x()` alapján
        mérjük, nem a QML deklarációs (gyerek-)sorrendből."""
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        elemek = [(nev, _gyerek(window, nev)) for nev in GOMBSOR_SORREND]
        helyek = [(nev, _bal_x(e)) for nev, e in elemek]
        rendezett = [nev for nev, _x in sorted(helyek, key=lambda p: p[1])]
        assert rendezett == list(GOMBSOR_SORREND), (
            "a gombsor kirajzolt sorrendje eltér a mért eredetitől.\n"
            f"  mért:  {helyek}\n"
            f"  várt:  {list(GOMBSOR_SORREND)}"
        )


class TestANavigatorCsoportAbszolutHelye:
    """#3663 (átnézés, 2. kör): a tulajdonos kifogása — a Play …
    elrendezés-váltó csoport a SÁV JOBB SZÉLÉRE tolódott (a törölt
    `compareButtonA/AB/AA` placeholder ELŐTTI kitöltő `Item` a `RowLayout`
    egyetlen közös kitöltőjeként a teljes navigátor-csoportot a sáv jobb
    szélére nyomta). A helyes hely a FOTÓTERÜLET közepéhez igazodik — ez a
    próba ABSZOLÚT képernyő-koordinátán, a referenciához (`ui-audit-editor.md`
    3/b.1, 1280 px-en) mérve ellenőrzi a `▶` végét, a szegmenst és a két
    segédgombot, ±8 px tűréssel.

    Öt fotós mappa kell (`qml_app_5_negyzet_kep`): a filmszalag szélessége a
    mappa fotóinak számától függ (`Math.min(7, darab) * 44`), és a
    referencián mért ~215 px-es szalag csak ≥5 fotós mappával közelíthető —
    a 2 fotós próbaképpel (`qml_app_negyzet_kepek`, 88 px-es szalag) a
    navigátor-csoport hátsó fele éppen a hiányzó szalagszélesség felével
    tolódna el a referenciától.
    """

    #: (objectName, bal cél vagy None, jobb cél) — 1280 px-en, px
    ABSZOLUT_CELOK = (
        ("viewerNextButton", None, 917),  # a `▶` VÉGE a mérce (mérve #3663 3/b.1)
        ("viewerLayoutGroup", 933, 1047),
        ("viewerSwapFocus", 1057, 1091),
        ("viewerSwapLayout", 1096, 1130),
    )
    TURES = 8

    def test_1280_pixelen_a_mert_helyen_all(self, qml_app_5_negyzet_kep, qt_app):
        window, _controller, _engine = qml_app_5_negyzet_kep
        _ab_modba(window, qt_app, meret=(1280, 1024))

        hibak = []
        for nev, bal_cel, jobb_cel in self.ABSZOLUT_CELOK:
            elem = _gyerek(window, nev)
            jobb = _jobb_x(elem)
            if abs(jobb - jobb_cel) > self.TURES:
                hibak.append(
                    f"{nev}: jobb éle {jobb:.0f} px (mérce {jobb_cel} px, "
                    f"±{self.TURES})"
                )
            if bal_cel is not None:
                bal = _bal_x(elem)
                if abs(bal - bal_cel) > self.TURES:
                    hibak.append(
                        f"{nev}: bal éle {bal:.0f} px (mérce {bal_cel} px, "
                        f"±{self.TURES})"
                    )
        assert not hibak, "abszolút helyzet eltér a referenciától:\n" + "\n".join(hibak)

    def test_a_szegmens_es_a_segedgombok_merete(self, qml_app_5_negyzet_kep, qt_app):
        """Mérve (`ui-audit-editor.md` 3/b.1): a szegmens ~114×22, a két
        segédgomb ~34×22 — a korábbi 80×22/26×22 alig volt olvasható."""
        window, _controller, _engine = qml_app_5_negyzet_kep
        _ab_modba(window, qt_app, meret=(1280, 1024))

        szegmens = _gyerek(window, "viewerLayoutGroup")
        assert szegmens.property("width") == 114
        for nev in ("viewerSwapFocus", "viewerSwapLayout"):
            gomb = _gyerek(window, nev)
            assert gomb.property("width") == 34, f"{nev} szélessége nem 34"
            assert gomb.property("height") == 22, f"{nev} magassága nem 22"

    def test_szeles_ablakon_is_a_fototerulet_kozepere_igazodik(
        self, qml_app_5_negyzet_kep, qt_app
    ):
        """A csoport NEM egy fix pixelre, hanem a fotóterület KÖZEPÉHEZ
        igazodik — 1600 px-en a filmszalag középpontjának ugyanúgy egybe
        kell esnie a fotóterület középpontjával, mint 1280 px-en."""
        window, _controller, _engine = qml_app_5_negyzet_kep
        _ab_modba(window, qt_app, meret=(1600, 1024))

        filmszalag = _gyerek(window, "viewerFilmstrip")
        fototerulet = _gyerek(window, "viewerPhotoArea")
        filmszalag_kozepe = (_bal_x(filmszalag) + _jobb_x(filmszalag)) / 2
        fototerulet_kozepe = _bal_x(fototerulet) + fototerulet.property("width") / 2
        assert abs(filmszalag_kozepe - fototerulet_kozepe) <= 4, (
            f"a filmszalag közepe ({filmszalag_kozepe:.0f}) nem esik egybe "
            f"a fotóterület közepével ({fototerulet_kozepe:.0f}) 1600 px-en"
        )

    def test_nem_a_sav_jobb_szelere_tolva(self, qml_app_5_negyzet_kep, qt_app):
        """Ellenpróba a 2. átnézési kör kifogására: a csoport UTOLSÓ eleme
        (`viewerSwapLayout`) messze a sáv jobb szélétől kell álljon, nem
        közvetlenül mellette."""
        window, _controller, _engine = qml_app_5_negyzet_kep
        _ab_modba(window, qt_app, meret=(1280, 1024))

        sav = _gyerek(window, "viewerTopBar")
        utolso = _gyerek(window, "viewerSwapLayout")
        hezag = _jobb_x(sav) - _jobb_x(utolso)
        assert hezag > 100, (
            f"a csoport csak {hezag:.0f} px-re áll a sáv jobb szélétől — "
            "úgy tűnik, megint a szélre van tolva, nem a fotóterület közepére"
        )


class TestAJelvenySzine:
    def test_a_jelveny_SZURKE_nem_kek(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        szin = jelveny.property("color")
        # QColor.name() -> "#rrggbb"
        assert szin.name() == "#666666", (
            f"a jelvény háttere nem a mért szürke: {szin.name()}"
        )

    def test_a_felirat_FELKOVER_es_feher(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        # a felirat a jelvény egyetlen Text gyereke — kereséssel típus
        # szerint biztosabb, mint névvel (nincs objectName-je)
        szovegek = [
            gy for gy in jelveny.findChildren(QQuickItem)
            if gy.metaObject().className().startswith("QQuickText")
        ]
        assert szovegek, "a jelvénynek nincs Text gyereke"
        assert szovegek[0].property("font").bold(), (
            "a jelvény felirata nem félkövér"
        )
        assert szovegek[0].property("color").name() == "#ffffff"


class TestAJelvenyZSorrendje:
    def test_a_jelveny_a_photoArea_UTAN_all_a_fatban(self, qml_app, qt_app):
        """A #3013 a jelvényt a `photoArea` GYEREKÉNEK, a `photo` ELÉ
        tette — ez okozta, hogy a kép időnként a jelvény FÖLÉ rajzolt. A
        javításban a jelvény a `photoArea` TESTVÉRE, utána deklarálva."""
        window, _controller, _engine = qml_app
        _ab_modba(window, qt_app)

        jelveny = _gyerek(window, "viewerFocusBadge")
        terulet = _gyerek(window, "viewerPhotoArea")
        assert jelveny.parent() is terulet.parent(), (
            "a jelvény már nem a fotó-terület testvére"
        )


class TestAKattintasosFokuszvaltas:
    def test_a_BAL_kepre_kattintva_a_BAL_lesz_aktiv(self, qml_app, qt_app):
        """#3663.4: AB módban a bal képre kattintva a jelvény (és az
        aktív oldal) a bal képhez kerül — eddig ezt csak a
        `swap_2up_focus` gomb tudta."""
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        bal_kep = _gyerek(window, "viewerImageElotte")
        assert bal_kep.property("width") and bal_kep.property("height"), (
            "a bal kép mérete 0×0 — nincs mire kattintani"
        )

        _klikk(qt_app, window, bal_kep)

        assert nezo.property("aktivOldal") == "bal"

    def test_a_JOBB_kepre_kattintva_a_JOBB_lesz_aktiv(self, qml_app, qt_app):
        window, _controller, _engine = qml_app
        nezo = _ab_modba(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"

        jobb_kep = _gyerek(window, "viewerImage")
        assert jobb_kep.property("width") and jobb_kep.property("height"), (
            "a jobb kép mérete 0×0 — nincs mire kattintani"
        )

        _klikk(qt_app, window, jobb_kep)

        assert nezo.property("aktivOldal") == "jobb"

    def test_1up_modban_a_kepre_kattintas_NEM_valt_oldalt(self, qml_app, qt_app):
        """1up módban nincs második oldal — a kattintás ne írja át az
        `aktivOldal`-t (ami ilyenkor amúgy sem látszik, de a `photo`
        TapHandlere `layoutMode !== "1up"`-hoz kötött)."""
        window, _controller, _engine = qml_app
        nezo = _nezot_nyit(window, qt_app)
        assert nezo.property("layoutMode") == "1up"
        kezdeti = nezo.property("aktivOldal")

        jobb_kep = _gyerek(window, "viewerImage")
        _klikk(qt_app, window, jobb_kep)

        assert nezo.property("aktivOldal") == kezdeti


class TestAJelvenyHelyeVizszintesen:
    """#3663.1/.3: a jelvény helye a KIRAJZOLT képhez képest, vízszintes
    elrendezésben — négyzetes próbaképpel (ld. modul docstring)."""

    def test_jobb_fokusz_alapertelmezett(self, qml_app_negyzet_kepek, qt_app):
        """Az `aktivOldal` alapértéke „jobb" — a jelvénynek a JOBB kép bal
        széle mellett kell állnia, az osztó felől."""
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        kep = _kep_teglalap(_gyerek(window, "viewerImage"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        res_x = jelveny["bal"] - kep["bal"]
        res_y = kep["fent"] - jelveny["lent"]
        assert abs(res_x - PARHUZAMOS_RES) <= TURES_PARHUZAMOS, (
            f"a jelvény {res_x:.0f} px-re áll a jobb kép bal szélétől "
            f"(mérce: {PARHUZAMOS_RES} px, ±{TURES_PARHUZAMOS})"
        )
        assert abs(res_y - MEROLEGES_RES) <= TURES_MEROLEGES, (
            f"a jelvény {res_y:.0f} px-re áll a kép teteje fölött "
            f"(mérce: {MEROLEGES_RES} px, ±{TURES_MEROLEGES})"
        )
        # a jelvény ne kerüljön a kép ALÁ/MÖGÉ (a #3013 hibája)
        assert jelveny["lent"] <= kep["fent"]

    def test_bal_fokusz_kepre_kattintva(self, qml_app_negyzet_kepek, qt_app):
        """#3663.4: a képre kattintás is vált fókuszt — a bal/előtte kép
        kattintása a jelvényt a BAL kép jobb széle mellé viszi."""
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)

        _klikk(qt_app, window, _gyerek(window, "viewerImageElotte"))
        assert nezo.property("aktivOldal") == "bal"

        kep = _kep_teglalap(_gyerek(window, "viewerImageElotte"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        res_x = kep["jobb"] - jelveny["jobb"]
        res_y = kep["fent"] - jelveny["lent"]
        assert abs(res_x - PARHUZAMOS_RES) <= TURES_PARHUZAMOS, (
            f"a jelvény {res_x:.0f} px-re áll a bal kép jobb szélétől "
            f"(mérce: {PARHUZAMOS_RES} px, ±{TURES_PARHUZAMOS})"
        )
        assert abs(res_y - MEROLEGES_RES) <= TURES_MEROLEGES, (
            f"a jelvény {res_y:.0f} px-re áll a kép teteje fölött "
            f"(mérce: {MEROLEGES_RES} px, ±{TURES_MEROLEGES})"
        )

    def test_swapfocus_gomb_ugyanoda_viszi_mint_a_kattintas(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = _ab_modba(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        _klikk(qt_app, window, _gyerek(window, "viewerSwapFocus"))
        assert nezo.property("aktivOldal") == "bal"

        kep = _kep_teglalap(_gyerek(window, "viewerImageElotte"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))
        res_x = kep["jobb"] - jelveny["jobb"]
        assert abs(res_x - PARHUZAMOS_RES) <= TURES_PARHUZAMOS


class TestAJelvenyHelyeFuggolegesen:
    """#3663.1/.3 — `Colab EN 35`: a jelvény a fókuszban lévő kép BAL
    oldalán, az osztó (a másik kép) felőli végéhez közel."""

    def _fuggolegesre_valt(self, window, qt_app):
        nezo = _ab_modba(window, qt_app)
        _klikk(qt_app, window, _gyerek(window, "viewerSwapLayout"))
        assert nezo.property("fuggolegesElrendezes") is True
        return nezo

    def test_also_kep_fokuszalva(self, qml_app_negyzet_kepek, qt_app):
        """Alapértelmezett `aktivOldal == "jobb"` — az ALSÓ kép a fókusz,
        a jelvény a bal margóban, az osztó (a felső kép alja) felől."""
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = self._fuggolegesre_valt(window, qt_app)
        assert nezo.property("aktivOldal") == "jobb"

        kep = _kep_teglalap(_gyerek(window, "viewerImage"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        res_x = kep["bal"] - jelveny["jobb"]
        res_y = jelveny["fent"] - kep["fent"]
        assert abs(res_x - PARHUZAMOS_RES) <= TURES_PARHUZAMOS, (
            f"a jelvény {res_x:.0f} px-re áll a kép bal szélétől "
            f"(mérce: {PARHUZAMOS_RES} px, ±{TURES_PARHUZAMOS})"
        )
        assert abs(res_y - MEROLEGES_RES) <= TURES_MEROLEGES, (
            f"a jelvény {res_y:.0f} px-re áll az osztó (a felső kép alja) "
            f"alatt (mérce: {MEROLEGES_RES} px, ±{TURES_MEROLEGES})"
        )
        # a jelvény a képek BAL margójában áll, nem a kép fölött/alatt
        assert jelveny["jobb"] <= kep["bal"]

    def test_felso_kep_fokuszalva(self, qml_app_negyzet_kepek, qt_app):
        """A #3663 mércéje (`Colab EN 35`): a FELSŐ (fókuszban lévő) kép
        bal oldalán, az alsó (osztó felőli) végéhez közel."""
        window, _controller, _engine = qml_app_negyzet_kepek
        nezo = self._fuggolegesre_valt(window, qt_app)

        _klikk(qt_app, window, _gyerek(window, "viewerImageElotte"))
        assert nezo.property("aktivOldal") == "bal"

        kep = _kep_teglalap(_gyerek(window, "viewerImageElotte"))
        jelveny = _elem_teglalap(_gyerek(window, "viewerFocusBadge"))

        res_x = kep["bal"] - jelveny["jobb"]
        res_y = kep["lent"] - jelveny["lent"]
        assert abs(res_x - PARHUZAMOS_RES) <= TURES_PARHUZAMOS
        assert abs(res_y - MEROLEGES_RES) <= TURES_MEROLEGES
        assert jelveny["jobb"] <= kep["bal"]


class TestAJelvenyMerete:
    def test_86x26_es_enyhen_lekerekitett(self, qml_app_negyzet_kepek, qt_app):
        """Mérve (`Colab EN 33`, 1280×1024): 86×26, ~4 px sugár — NEM
        kapszula (a #3013 `height/2` sugara azt adott)."""
        window, _controller, _engine = qml_app_negyzet_kepek
        _ab_modba(window, qt_app)
        jelveny = _gyerek(window, "viewerFocusBadge")

        assert jelveny.property("width") == 86
        assert jelveny.property("height") == 26
        assert 2 <= jelveny.property("radius") <= 6
