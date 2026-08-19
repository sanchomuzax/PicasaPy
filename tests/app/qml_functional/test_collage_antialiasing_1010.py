"""Élsimítás a kollázs-előnézetben, KIRAJZOLVA — #1010.

A felhasználó a **0.8.1-en** jelezte: a vásznon a fehér keretek széle
szaggatott. A Képkupac a képeket 0…−5°-kal elforgatja, és a Qt Quickben a
forgatott `Rectangle` **alapértelmezésben nem élsimított**.

## Mit mér ez a fájl, és miért nem képpontot

Az élsimítás vizuális tulajdonság, de a képpontos ellenőrzés itt **nem
használható mércének**: fejnélküli környezetben (`QT_QPA_PLATFORM=offscreen`,
tehát a CI-ban is) a jelenetgráf a **szoftveres** háttérre esik vissza, az
pedig QPainterrel rajzol, és a forgatott téglalapot **élsimítás nélkül is
simán** rajzolja meg. Mérve, ugyanazon a jeleneten:

| háttér | `antialiasing: false` | `antialiasing: true` |
|---|---|---|
| szoftveres (offscreen, CI) | 467 köztes árnyalat | 467 |
| OpenGL (valódi kijelző) | **0** | **466** |

A CI-ban tehát a képpontszámlálás a HIBÁS kódon is zöld lenne — beégetett
képpont-kivonatról (#942) nem is beszélve. Ezért a mérce a **kirajzolt fa
property-je**: a valódi `QQuickView`-ban felépült elemeket járjuk be, és
azt őrizzük, hogy egy későbbi átírás ne vegye ki némán az élsimítást.

A tényleges képpontmérés is itt van (`TestAValodiKeppontok`), de csak akkor
fut le, ha van GPU-s háttér — különben magától kihagyja magát.

## A #1016 — ami a #1010-ből kimaradt

A #1010 a keret `Rectangle`-jét simította, és a felhasználó a 0.8.5-ön
MÉGIS szaggatottat látott. Két él maradt, amire az `antialiasing` nem hat:
a **textúrázott** `Image` külső éle (`noborder`), és a képen lévő
`clip: true` **stencil-alapú**, tehát kemény éle (a fehér keret BELSŐ éle).

A megoldás a rajz-tartó **simító rétege** (`CollageNode.qml`). Ugyanazon a
próbajeleneten, valódi OpenGL-en (V3D) mérve:

| él | réteg nélkül | réteggel |
|---|---|---|
| `noborder` külső (fotó) éle | **0** | 516 |
| `whiteborder` külső (keret) éle | 514 | 641 |
| `whiteborder` belső (fotó/keret) éle | **0** | 819 |

## ⚠️ A képpontmérés és a réteg — amitől a teszt BEFAGY

A `QTest.qWaitForWindowExposed` VALÓDI GPU-s háttéren, szálas rajzoló
hurokkal **holtpontra fut**, ha a jelenetben réteg (`layer.enabled`) van.
Mérve ezen a gépen: réteg nélkül lefut, réteggel soha nem tér vissza (a
`QSG_RENDER_LOOP=basic` és a `QEventLoop`-os várakozás viszont jó).
Offscreen (CI) háttéren nincs holtpont. A próbaablak ezért **eseményhurokkal
vár**, nem `qWaitForWindowExposed`-del — aki visszaírja, befagyasztja a
tesztet minden GPU-s gépen.

## Amit ez a fájl SZÁNDÉKOSAN nem állít

Nem állítja, hogy „mindenen legyen élsimítás". A rákent élsimítás fölösleges
rajzolási költség, 350 képes kollázsnál pedig már számít is. A `smooth`
(a kép MÉRETEZÉSE) és az `antialiasing` (a GEOMETRIA éle) két külön dolog,
és a lap egyszínű, tengelyre állított hátterének egyik sem kell.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QEventLoop, QRectF, QTimer, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty
from PySide6.QtQuick import QQuickView, QSGRendererInterface

from support.collage_canvas_harness import (
    _child,
    _csomopontok,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


def _kepek_szama(controller) -> int:
    return len(_csomopontok(controller))


# --------------------------------------------------------------------------
# 0. Előfeltétel — van-e egyáltalán forgatás
# --------------------------------------------------------------------------


def test_a_kepkupac_csomopontjai_tenyleg_forgatva_vannak(controller):
    """Ha a Képkupac nem forgatna, az egész jegy tárgytalan lenne.

    Ez az az állítás, ami a többit értelmessé teszi: élsimítást azért kell
    tenni a keretre, mert a keret EL VAN FORGATVA. Tengelyre állított
    téglalapnak nincs mit simítani."""
    szogek = [node.theta for node in _csomopontok(controller)]
    assert any(abs(szog) > 1e-6 for szog in szogek), (
        "egyetlen csomópont sincs elforgatva — a Képkupac elrendezése "
        f"megváltozott (szögek: {szogek})"
    )


# --------------------------------------------------------------------------
# 1. A forgatott elemek élsimítása
# --------------------------------------------------------------------------


class TestAForgatottElemek:
    def test_a_keret_lapja_elsimitott(self, controller):
        """A felhasználó bejelentésének pontos tárgya: a keret fehér lapja.

        A `Rectangle` élsimítása alapból KI van kapcsolva, és a Qt csak a
        lekerekített (`radius != 0`) téglalapoknál kapcsolja be magától —
        a keret pedig szögletes. Kézzel kell megadni, különben a −5°-kal
        elforgatott fehér él lépcsőzik."""
        panel = _panel(controller)
        for index in range(_kepek_szama(controller)):
            keret = _child(panel, f"collageNodeFrame{index}")
            assert keret.property("antialiasing") is True, (
                f"a(z) {index}. kép keretének nincs élsimítása — "
                "a forgatott fehér él lépcsőzni fog"
            )

    def test_a_kijelolesjelolo_elsimitott(self, controller):
        """A kijelölés 2 képpontos kerete UGYANÚGY forgatva van.

        A rácsos témáknál (ahol nincs gyűrű) ez az EGYETLEN kijelölés-jel;
        ha ez szaggat, az a kijelölésen mindig látszik."""
        panel = _panel(controller)
        for index in range(_kepek_szama(controller)):
            jelolo = _child(panel, f"collageNodeSelection{index}")
            assert jelolo.property("antialiasing") is True, (
                f"a(z) {index}. kép kijelölés-jelölőjének nincs élsimítása"
            )

    def test_a_kep_simitva_meretezodik(self, controller):
        """A `smooth` a kép MÉRETEZÉSÉRŐL szól, nem a geometria éléről.

        A miniatűr (spec 6.3 lépcsői: ≤99 → nagy, 100+ → 256/128/64)
        majdnem sosem pont akkora, mint a doboz, tehát mindig méreteződik.
        A `smooth` a Qt Quickben alapból be van kapcsolva; itt kimondjuk,
        hogy ez SZÁNDÉK — egy későbbi „optimalizálás" ne kapcsolhassa ki
        némán szemcsés képekre cserélve az előnézetet."""
        panel = _panel(controller)
        for index in range(_kepek_szama(controller)):
            kep = _child(panel, f"collageNodeImage{index}")
            assert kep.property("smooth") is True, (
                f"a(z) {index}. kép nem simítva méreteződik (nearest-neighbour)"
            )


# --------------------------------------------------------------------------
# 2. Ahol NEM kell élsimítás — a rákent élsimítás fölösleges költség
# --------------------------------------------------------------------------


class TestAholNemKell:
    def test_a_lap_hatterere_nem_kerul_elsimitas(self, controller):
        """A lap háttere tengelyre állított, szögletes, egyszínű téglalap.

        Nincs rajta ferde él, tehát nincs mit simítani — a beállítása
        tiszta ráfizetés lenne. Ez az őre annak, hogy a javítás CÉLZOTT
        maradjon, és ne váljon „tegyünk mindenre élsimítást" körré."""
        panel = _panel(controller)
        hatter = _child(panel, "collageSheetBackground")
        assert hatter.property("antialiasing") is False, (
            "a lap egyszínű, tengelyre állított háttere élsimítást kapott — "
            "ez rajzolási költség haszon nélkül"
        )

    def test_a_gyuru_korei_a_lekerekitestol_mar_elsimitottak(self, controller):
        """A gyűrűre azért nem kell kézzel tenni, mert a Qt megteszi.

        A `QQuickRectangle` a `radius != 0` esetén magától bekapcsolja az
        élsimítást (enélkül a kör széle fűrészfog lenne). Ezt az állítást
        azért írjuk le, hogy ha valaki a gyűrűt szögletesre cserélné vagy
        a `radius`-t kivenné, azonnal kiderüljön: onnantól kézzel kellene
        megadni."""
        panel = _panel(controller)
        controller.setCollageSelection([0])
        for nev in ("collageRingOuter0", "collageRingInner0"):
            kor = _child(panel, nev)
            assert kor.property("radius") > 0, f"a(z) {nev} már nem lekerekített"
            assert kor.property("antialiasing") is True, (
                f"a(z) {nev} elvesztette a lekerekítésből jövő élsimítást"
            )


# --------------------------------------------------------------------------
# 3. A tényleges képpontok — csak GPU-s háttéren
# --------------------------------------------------------------------------

#: FEKETE lap — a fehér keret éle csak ezen a kontraszton mérhető. (A valódi
#: vászon háttere fehér, a keret `#eeeeee`: ott nincs mit számolni.)
_PROBA_HATTER = b'import QtQuick\nRectangle { width: 300; height: 300; color: "black" }\n'

_KEEPALIVE: list[object] = []


def _kek_kep(tmp_path) -> str:
    """Egyszínű KÉK fotó — a keret belső éle csak így mérhető.

    A fehér keret (`#eeeeee`) és a fotó között akkor számolható átmeneti
    árnyalat, ha a fotó minden képpontja UGYANAZ a szín: különben a fotó
    saját részletei is „átmenetnek" látszanának."""
    ut = tmp_path / "kek.png"
    if not ut.exists():
        kep = QImage(200, 150, QImage.Format.Format_RGB32)
        kep.fill(0xFF0000FF)
        assert kep.save(str(ut))
    return str(ut)


def _proba_csomopont(szog_fok: float, keret: str = "whiteborder", kep: str = ""):
    """Egyetlen `CollageNode` KIRAJZOLÁS NÉLKÜL, csak a kötések miatt.

    A `CollageNode` NINCS kiajánlva a `qmldir`-ben (a panel belső eleme),
    ezért fájl-URL-lel töltjük be — a tesztért nem ajánljuk ki nyilvános
    típusnak.

    Ablak nélkül dolgozunk: a geometriát és a réteg beállításait a QML
    kötései adják, azokhoz nem kell jelenetgráf. Így az őrök a CI-ban is
    futnak, GPU nélkül."""
    import picasapy.app.application as app_module

    qml_dir = app_module._APP_DIR / "qml"
    motor = QQmlEngine()
    motor.addImportPath(str(qml_dir))
    forras = QQmlComponent(
        motor, QUrl.fromLocalFile(str(qml_dir / "PicasaPy" / "CollageNode.qml"))
    )
    assert [e.toString() for e in forras.errors()] == []
    csomopont = forras.create()
    assert csomopont is not None
    for nev, ertek in (
        ("unit", 1.0),
        ("centerX", 150.0),
        ("centerY", 150.0),
        ("nodeWidth", 160.0),
        ("nodeHeight", 120.0),
        ("theta", math.radians(szog_fok)),
        ("border", keret),
        ("path", kep),
    ):
        csomopont.setProperty(nev, ertek)
    _KEEPALIVE.extend((motor, forras, csomopont))
    return csomopont


def _proba_ablak(szog_fok: float, keret: str = "whiteborder", kep: str = "") -> QQuickView:
    """Egyetlen, elforgatott `CollageNode` fekete lapon, KIRAJZOLVA.

    ⚠️ A megjelenésre `QEventLoop`-pal várunk, NEM
    `QTest.qWaitForWindowExposed`-del: az valódi GPU-s háttéren, szálas
    rajzoló hurokkal holtpontra fut, ha a jelenetben réteg van (mérve,
    ld. a modul docstringjét)."""
    import picasapy.app.application as app_module

    qml_dir = app_module._APP_DIR / "qml"
    view = QQuickView()
    view.engine().addImportPath(str(qml_dir))

    hatter = QQmlComponent(view.engine())
    hatter.setData(_PROBA_HATTER, QUrl())
    assert [e.toString() for e in hatter.errors()] == []
    lap = hatter.create()
    assert lap is not None
    lap.setParentItem(view.contentItem())

    csomopont_forras = QQmlComponent(
        view.engine(), QUrl.fromLocalFile(str(qml_dir / "PicasaPy" / "CollageNode.qml"))
    )
    assert [e.toString() for e in csomopont_forras.errors()] == []
    csomopont = csomopont_forras.create()
    assert csomopont is not None
    csomopont.setParentItem(lap)
    for nev, ertek in (
        ("unit", 1.0),
        ("centerX", 150.0),
        ("centerY", 150.0),
        ("nodeWidth", 160.0),
        ("nodeHeight", 120.0),
        ("theta", math.radians(szog_fok)),
        ("border", keret),
        ("path", kep),
    ):
        csomopont.setProperty(nev, ertek)

    view.resize(300, 300)
    view.show()
    hurok = QEventLoop()
    QTimer.singleShot(2500, hurok.quit)
    hurok.exec()
    _KEEPALIVE.extend((view, lap, csomopont, hatter, csomopont_forras))
    return view


def _koztes_arnyalatok(view: QQuickView) -> int:
    """Hány képpont esik a fekete háttér és a fehér keret KÖZÉ.

    Ez az élsimítás közvetlen mérőszáma: sima élnél a kettő között
    átmeneti árnyalatok vannak, lépcsőzőnél nincs egy sem. A küszöb bőven
    tág (nem beégetett érték): a lényeg a nulla és a nem-nulla különbsége."""
    kep = view.grabWindow()
    if kep.isNull():
        return -1
    szam = 0
    for y in range(kep.height()):
        for x in range(kep.width()):
            szin = kep.pixelColor(x, y)
            if szin.blue() > 180 and szin.red() < 15:
                continue                       # tiszta kék fotó, nem átmenet
            if 20 < szin.red() < 220:
                szam += 1
    return szam


def _kek_szelen_atmenetek(view: QQuickView) -> tuple[int, int]:
    """(külső, belső) átmenetek egy KÉK fotós csomóponton.

    - **külső**: fekete háttér ↔ a csempe (fotó vagy fehér keret) keveréke;
    - **belső**: a fehér keret ↔ a kék fotó keveréke — ezt a `clip: true`
      kemény, stencil-alapú éle nullázta le a #1016 előtt.
    """
    kep = view.grabWindow()
    if kep.isNull():
        return (-1, -1)
    kulso = belso = 0
    for y in range(kep.height()):
        for x in range(kep.width()):
            szin = kep.pixelColor(x, y)
            r, g, b = szin.red(), szin.green(), szin.blue()
            tiszta = (
                (r < 10 and g < 10 and b < 10)          # háttér
                or (abs(r - 238) < 10 and abs(g - 238) < 10 and abs(b - 238) < 10)
                or (r < 10 and g < 10 and b > 245)      # fotó
            )
            if tiszta:
                continue
            if abs(r - g) < 12 and abs(g - b) < 12:
                kulso += 1                              # fekete ↔ fehér keret
            elif r < 40 and g < 40:
                kulso += 1                              # fekete ↔ kék fotó
            else:
                belso += 1                              # fehér keret ↔ kék fotó
    return kulso, belso


class TestAValodiKeppontok:
    def test_a_forgatott_keret_elen_vannak_atmeneti_arnyalatok(self, qt_app):
        """A tényleges rajz mérése — GPU-s háttér nélkül kihagyva.

        Miért kihagyható: a szoftveres háttér (offscreen, CI) a forgatott
        téglalapot élsimítás nélkül is simán rajzolja, tehát ott a mérés
        semmit nem bizonyítana. Valódi GPU-n viszont ez a különbség
        0 ↔ több száz képpont — ez a felhasználó által látott hiba."""
        view = _proba_ablak(5.0)
        felulet = view.rendererInterface()
        if (
            felulet is None
            or felulet.graphicsApi() == QSGRendererInterface.GraphicsApi.Software
        ):
            pytest.skip(
                "szoftveres jelenetgráf — a képpontmérés itt nem különböztet meg"
            )
        qt_app.processEvents()
        arnyalatok = _koztes_arnyalatok(view)
        assert arnyalatok >= 8, (
            "a forgatott keret élén nincsenek átmeneti árnyalatok "
            f"({arnyalatok} db) — az él lépcsőzik"
        )


# --------------------------------------------------------------------------
# 4. A SIMÍTÓ RÉTEG — #1016
# --------------------------------------------------------------------------
#
# ⚠️ A `layer` CSOPORTOSÍTOTT property: `item.property("layer")` nem
# használható rá, `QQmlProperty(item, "layer.enabled").read()` kell.


def _reteg(elem, nev: str):
    return QQmlProperty(elem, f"layer.{nev}").read()


def _gyerek(csomopont, nev_kezdet: str):
    for gy in csomopont.findChildren(object):
        if hasattr(gy, "objectName") and gy.objectName().startswith(nev_kezdet):
            return gy
    raise AssertionError(f"{nev_kezdet}* nem található a csomópontban")


class TestASimitoReteg:
    """A #1016 szerződése a kirajzolt fán — a CI-ban is fog.

    A képpontmérés (5. szakasz) GPU nélkül kihagyja magát; ezek az őrök
    viszont mindenhol futnak, és pontosan azt a három beállítást védik,
    amelyekből MÉRVE egyik sem elég önmagában."""

    def test_a_rajztarto_retege_be_van_kapcsolva(self):
        """A három beállítás EGYÜTT adja a sima élt.

        Mérve, `noborder` külső élén: csak `layer.enabled` → 0 átmeneti
        árnyalat (rosszabb a réteg nélkülinél); `+ layer.smooth`, perem
        nélkül → 0; perem, `smooth` nélkül → 0; mindhárom → 310."""
        csomopont = _proba_csomopont(5.0)
        tarto = _gyerek(csomopont, "collageNodeLayer")
        assert _reteg(tarto, "enabled") is True, (
            "a rajz-tartónak nincs rétege — a forgatott kép külső éle és a "
            "vágott belső él is lépcsőzni fog"
        )
        assert _reteg(tarto, "smooth") is True, (
            "a réteg textúrája szűrés nélkül kerül ki: a forgatott textúra "
            "legközelebbi szomszéddal mintázódik, azaz ugyanolyan lépcsős"
        )
        assert _reteg(tarto, "samples") >= 4, (
            "a rétegen nincs többmintavételezés — a tört képpont-koordinátán "
            "álló vágott él részleges fedettsége elvész"
        )

    def test_a_reteg_NEM_zsugoritja_a_csempet(self):
        """A `layer.sourceRect` kiterjesztése CSAPDA — mérve.

        A réteg geometriája a kirajzolt elem dobozához igazodik, tehát a
        nagyobb forrás-téglalap BELEZSUGORODIK: a 168 képpont széles csempe
        134-re ment össze, azaz minden kép 20%-kal kisebb lett volna. A
        peremet ezért a TARTÓ MÉRETE adja, nem a `sourceRect`."""
        csomopont = _proba_csomopont(5.0)
        tarto = _gyerek(csomopont, "collageNodeLayer")
        forras = _reteg(tarto, "sourceRect")
        assert forras is None or QRectF(forras).isEmpty(), (
            f"a réteg `sourceRect`-je meg van adva ({forras}) — ettől a "
            "csempe belezsugorodik a dobozába"
        )
        keret = _gyerek(csomopont, "collageNodeFrame")
        assert keret.width() == pytest.approx(csomopont.width())
        assert keret.height() == pytest.approx(csomopont.height())

    def test_a_tarto_atlatszo_peremet_hagy_a_doboz_korul(self):
        """Perem nélkül a textúra szélső képpontsora átlátszatlan.

        A Qt a textúra szélén `clamp`-el, tehát a szűrésnek nincs mibe
        átmennie — az él pontosan olyan kemény marad, mint réteg nélkül
        (mérve: 0 átmeneti árnyalat)."""
        csomopont = _proba_csomopont(5.0)
        tarto = _gyerek(csomopont, "collageNodeLayer")
        assert tarto.width() >= csomopont.width() + 4, (
            "a rajz-tartó nem nagyobb a doboznál — nincs átlátszó perem"
        )
        assert tarto.x() <= -2 and tarto.y() <= -2

    def test_a_tarto_BEFOGADJA_a_vetett_arnyekot(self):
        """A réteg levágná az árnyékot — ez az őre annak, hogy nem teszi.

        A #1021 árnyéka TÚLLÓG a dobozon (haló + eltolás). Ha a rajz-tartó
        csak a dobozt fedné, a javítás egy MÁSIK, azonnal látható hibát
        okozna: levágott árnyékot."""
        csomopont = _proba_csomopont(5.0)
        for nev, ertek in (
            ("shadowSource", "qrc:/nincs.png"),
            ("shadowSupport", 24),
            ("shadowBorder", 48),
            ("shadowOffsetX", 8.0),
            ("shadowOffsetY", 6.0),
        ):
            csomopont.setProperty(nev, ertek)
        tarto = _gyerek(csomopont, "collageNodeLayer")
        arnyek = _gyerek(csomopont, "collageNodeShadow")
        # a tartó SAJÁT koordinátáiban: az árnyék doboza teljesen belefér,
        # és marad legalább 2 képpont átlátszó sáv körülötte
        assert arnyek.x() >= 2, f"az árnyék balra kilóg a rajz-tartóból ({arnyek.x()})"
        assert arnyek.y() >= 2, f"az árnyék fölfelé kilóg a rajz-tartóból ({arnyek.y()})"
        assert arnyek.x() + arnyek.width() <= tarto.width() - 2, (
            "az árnyék jobbra kilóg a rajz-tartóból — a réteg levágná"
        )
        assert arnyek.y() + arnyek.height() <= tarto.height() - 2, (
            "az árnyék lefelé kilóg a rajz-tartóból — a réteg levágná"
        )

    def test_a_kuszob_folott_a_reteg_kikapcsol(self, qt_app):
        """Dokumentált küszöb, nem néma lemondás.

        Mérve ezen a gépen (V3D, függőleges szinkron nélkül, minden csomópont
        mozog képkockánként): 9 képnél 5,4 → 5,9 ms, 30-nál 5,7 → 6,0 ms,
        350-nél 16,3 → 21,4…24,5 ms. A küszöb tehát a NAGY kollázsra szól —
        ott a csempe már úgyis 60 képpont alatti, ahol az él simasága nem
        látszik."""
        import picasapy.app.application as app_module

        csomopont = _proba_csomopont(5.0)
        motor = QQmlEngine()
        motor.addImportPath(str(app_module._APP_DIR / "qml"))
        lap_forras = QQmlComponent(motor)
        lap_forras.setData(
            b"import QtQuick\nQtObject { property int nodeCount: 0 }\n", QUrl()
        )
        assert [e.toString() for e in lap_forras.errors()] == []
        lap = lap_forras.create()
        _KEEPALIVE.extend((motor, lap_forras, lap))

        hatar = csomopont.property("smoothLayerLimit")
        assert hatar >= 30, (
            f"a küszöb ({hatar}) a tipikus, 9–30 képes kollázst is elvágná"
        )
        csomopont.setProperty("sheet", lap)
        tarto = _gyerek(csomopont, "collageNodeLayer")

        lap.setProperty("nodeCount", hatar)
        assert _reteg(tarto, "enabled") is True, (
            "a küszöbön a réteg már kikapcsolt — a tipikus kollázs marad szaggatott"
        )
        lap.setProperty("nodeCount", hatar + 1)
        assert _reteg(tarto, "enabled") is False, (
            "a küszöb fölött sem kapcsol ki a réteg — a 350 képes kollázs "
            "csomópontonként külön textúrát tartana"
        )


# --------------------------------------------------------------------------
# 5. A #1016 tényleges képpontjai — csak GPU-s háttéren
# --------------------------------------------------------------------------


class TestA1016Keppontok:
    """A felhasználó által LÁTOTT két él, kirajzolva.

    GPU nélkül kihagyja magát: a szoftveres háttér (offscreen, CI) a
    forgatott, vágott élt élsimítás nélkül is simán rajzolja, tehát ott a
    mérés a hibás kódon is zöld lenne (#1010 mérése)."""

    @staticmethod
    def _gpu_vagy_kihagy(view):
        felulet = view.rendererInterface()
        if (
            felulet is None
            or felulet.graphicsApi() == QSGRendererInterface.GraphicsApi.Software
        ):
            pytest.skip("szoftveres jelenetgráf — a képpontmérés itt nem különböztet meg")

    def test_a_noborder_csempe_KULSO_ele_sima(self, qt_app, tmp_path):
        """`noborder`-nél a csempe külső éle MAGA A FOTÓ éle.

        Erre az `antialiasing` nem hat (textúrázott csomópont), tehát a
        #1010 után is nulla átmeneti árnyalat volt rajta — mérve."""
        view = _proba_ablak(5.0, keret="noborder", kep=_kek_kep(tmp_path))
        self._gpu_vagy_kihagy(view)
        kulso, _ = _kek_szelen_atmenetek(view)
        assert kulso >= 8, (
            f"a forgatott fotó külső élén {kulso} átmeneti árnyalat van — "
            "az él lépcsőzik"
        )

    def test_a_feher_keret_BELSO_ele_sima(self, qt_app, tmp_path):
        """A `clip: true` stencil-éle — a felhasználó „fehér szélének" az a
        határa, ahol a keret a fotóval találkozik.

        Ez a legnagyobb kontrasztú él a csempén, tehát ezen látszik a
        legjobban a lépcső. A #1016 előtt mérve: **0** átmeneti árnyalat."""
        view = _proba_ablak(5.0, keret="whiteborder", kep=_kek_kep(tmp_path))
        self._gpu_vagy_kihagy(view)
        kulso, belso = _kek_szelen_atmenetek(view)
        assert belso >= 8, (
            f"a fehér keret és a fotó határán {belso} átmeneti árnyalat van — "
            "a vágás kemény, stencil-alapú éle lépcsőzik"
        )
        assert kulso >= 8, (
            f"a fehér keret külső élén {kulso} átmeneti árnyalat van — "
            "a #1010 eredménye elveszett"
        )
