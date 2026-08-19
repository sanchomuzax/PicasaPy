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

## Amit ez a fájl SZÁNDÉKOSAN nem állít

Nem állítja, hogy „mindenen legyen élsimítás". A rákent élsimítás fölösleges
rajzolási költség, 350 képes kollázsnál pedig már számít is. A `smooth`
(a kép MÉRETEZÉSE) és az `antialiasing` (a GEOMETRIA éle) két külön dolog,
és a lap egyszínű, tengelyre állított hátterének egyik sem kell.
"""

from __future__ import annotations

import math

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView, QSGRendererInterface
from PySide6.QtTest import QTest

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


def _proba_ablak(szog_fok: float) -> QQuickView:
    """Egyetlen, elforgatott `CollageNode` fekete lapon.

    A `CollageNode` NINCS kiajánlva a `qmldir`-ben (a panel belső eleme),
    ezért fájl-URL-lel töltjük be — a tesztért nem ajánljuk ki nyilvános
    típusnak."""
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
        ("border", "whiteborder"),
    ):
        csomopont.setProperty(nev, ertek)

    view.resize(300, 300)
    view.show()
    assert QTest.qWaitForWindowExposed(view, 5000), "a próbaablak nem jelent meg"
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
            ertek = kep.pixelColor(x, y).red()
            if 20 < ertek < 220:
                szam += 1
    return szam


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
