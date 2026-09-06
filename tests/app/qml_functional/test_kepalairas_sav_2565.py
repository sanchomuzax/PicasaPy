"""#2565 — a kép alatti KÉPALÁÍRÁS-SÁV és a kék infó-sáv tartalma.

## A mérés forrása: a tulajdonos ÖSSZEHASONLÍTÓ felvétele

`\\\\DS215j\\lemez\\My Pictures\\141421.jpg` (1920 × 1200, 2026-09-06 14:14) —
BAL oldalt a Picasa 3 szerkesztője, JOBB oldalt a mi programunk, UGYANAZON a
képen (`JonasBen_he_sits_…0a71328.png`, „Man on the cloud"). Vagyis nem
leírás és nem következtetés: **A/B felvétel ugyanarról a nézetről**.

### A kép alatti sáv (a felvétel bal oldala, kinagyítva)

| pozíció | az eredetiben | `.tre` kényszer (`editpanel.tre:1252–1266`) |
|---|---|---|
| bal szél | felirat-kapcsoló ikon (`captionbutton`) | `XConstraint 0, 0, 3` · `YConstraint 1, 1, -3` |
| közép | a kép felirata, **félkövér** (`caption`) | `XConstraint 0, 0, 25` … `1, 1, -24` |
| jobb szél | kuka (`captiontrash`) | `XConstraint 1, 1, -3` · `YConstraint 1, 1, -3` |

A `captionbase` / `captionbasetop` a sáv **háttere** (`predraw 1`), teljes
szélességben — a felvételen világosszürke csík a fotó alatt.

⚠️ Nálunk eddig a sor a fotó fölött LEBEGETT középre zárva, a kuka pedig a
felirat BAL oldalán állt.

### A kék infó-sáv (ugyanaz a felvétel, A/B)

| | Picasa 3 | PicasaPy (a felvételen) |
|---|---|---|
| fájlnév | `JonasBen_he_sits_…0a71328.png` | `AI > JonasBen_…_0291672e-…png` |
| **dátum** | **`2023. 05. 10. 16:30:05`** | — |
| méret | `896x1344 képpont` | `896x1344 képpont` |
| fájlméret | `807 KB` | `807 KB` |
| **címkék** | **`Címkék: AI image`** | — |
| számláló | — | `(427 / 82)` |

- a **dátum** forrása a #2486 óta megvan: EXIF felvételi idő híján a
  BEFAGYASZTOTT fájlidő (`PhotoRecord.sort_mtime_ns`) — ez volt a jegy
  nyitott kérdése („honnan veszi a Picasa a dátumot egy EXIF nélküli
  PNG-hez"), és a `docs/specs/pmp-database.md` 10.1/10.3–10.4 válaszolta meg:
  a Picasa a beolvasáskori fájlidőt tartja a katalógusában;
- a **címke-előtag** mért szöveg: `CThumbUI::GetTagInfo::format`
  (`referencia/stringres-en-hu.tsv:691`) — `Tags: ` → **`Címkék: `**;
- a **számláló** ebben a nézetben az eredetiben NINCS. A #1960 mérése (a
  fordított `(összes / aktuális)` sorrend) érvényes marad, csak nem ide
  való: az ő bizonyítéka egy ötképes mappa KIJELÖLÉSÉRŐL szólt.

### Ami SZÁNDÉKOSAN kimarad

A fájlnév alakja (az eredeti elhagyja a mappa-előtagot, és a nevet KÖZÉPEN
rövidíti `…`-tal). A rövidítés szabálya — karakterszám vagy képpontszélesség
— EGY mintából nem dönthető el, ezért nem találjuk ki: külön jegy.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QObject

_QML_MAPPA = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
_NEZO = (_QML_MAPPA / "PhotoViewer.qml").read_text(encoding="utf-8")
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AssertionError, AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.01)
    return False


def _walk(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _walk(gyerek)


def _elem(window, nev: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == nev:
            return item
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


def _nyisd_a_nezot(window, qt_app):
    window.setProperty("viewerOpen", True)
    nezo = _elem(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    assert _var(qt_app, lambda: _elem(window, "captionBar").isVisible())
    return nezo


def _kozep_x(elem) -> float:
    return elem.mapToScene(elem.boundingRect().center()).x()


class TestASavElrendezese:
    """bal: kapcsoló · közép: felirat · jobb: kuka — a felvétel szerint."""

    def test_a_kapcsolo_a_BAL_szelen(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        gomb = _elem(window, "captionToggleButton")
        bal = gomb.mapToScene(gomb.boundingRect().topLeft()).x()
        sav_bal = sav.mapToScene(sav.boundingRect().topLeft()).x()
        assert bal - sav_bal < 12, (
            f"a felirat-kapcsoló nem a sáv bal szélén ül ({bal - sav_bal:.0f} "
            "képpontra tőle) — mérve `XConstraint 0, 0, 3`"
        )

    def test_a_kuka_a_JOBB_szelen(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        kuka = _elem(window, "captionTrashButton")
        jobb = kuka.mapToScene(kuka.boundingRect().bottomRight()).x()
        sav_jobb = sav.mapToScene(sav.boundingRect().bottomRight()).x()
        assert sav_jobb - jobb < 12, (
            f"a kuka nem a sáv jobb szélén ül ({sav_jobb - jobb:.0f} képpontra "
            "tőle) — mérve `XConstraint 1, 1, -3`"
        )

    def test_a_felirat_KOZEPEN(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        mezo = _elem(window, "captionField")
        assert abs(_kozep_x(mezo) - _kozep_x(sav)) < 2, (
            "a felirat nem a sáv közepén áll"
        )

    def test_a_kuka_a_felirat_UTAN_all(self, qml_app, qt_app):
        """A régi sorrend (kuka · felirat) fordított volt."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        assert _kozep_x(_elem(window, "captionTrashButton")) > _kozep_x(
            _elem(window, "captionField")
        )
        assert _kozep_x(_elem(window, "captionToggleButton")) < _kozep_x(
            _elem(window, "captionField")
        )

    def test_a_sav_TELJES_szelessegu(self, qml_app, qt_app):
        """`captionbase`: `XConstraint 0,0,-2000` … `1,1,2000` — a sáv a
        fotó-terület teljes szélességét átéri, nem középre zárt csoport."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        terulet = _elem(window, "viewerPhotoArea")
        assert sav.width() >= terulet.width() - 1, (
            f"a felirat-sáv {sav.width():.0f} széles a {terulet.width():.0f} "
            "képpontos fotó-területen — az eredetiben végig ér"
        )

    def test_a_savnak_van_HATTERE(self, qml_app, qt_app):
        """`captionbase`/`captionbasetop` `predraw 1` — a felvételen
        világosszürke csík, nem áttetsző semmi a fotón."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        hatter = _elem(window, "captionBarBackground")
        assert hatter.isVisible()
        assert hatter.width() >= _elem(window, "captionBar").width() - 1


class TestAFeliratHelyorzoje:
    def test_ures_feliratnal_a_felszolitas_all_ott(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        mezo = _elem(window, "captionField")
        assert not mezo.property("text"), (
            "a próba előfeltétele nem teljesült: a képnek van felirata"
        )
        helyorzo = _elem(window, "captionPlaceholder")
        assert helyorzo.isVisible(), (
            "felirat nélküli képnél az eredeti „Készítsen képfeliratot!"
            "-t ír a sávba"
        )

    def test_a_helyorzo_a_SAVBAN_van(self, qml_app, qt_app):
        """A felvételen a felszólítás a sáv KÖZEPÉN áll, nem külön a fotón."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        helyorzo = _elem(window, "captionPlaceholder")
        assert abs(_kozep_x(helyorzo) - _kozep_x(sav)) < 2

    def test_a_hivatalos_magyar_alak(self):
        assert "<source>Make a caption!</source>" in _TS
        assert "<translation>Készítsen képfeliratot!</translation>" in _TS


class TestAForras:
    def test_a_sav_NEM_lebeg_kozepre_zartan(self):
        """A régi alak `anchors.horizontalCenter` volt — az eredetiben a sáv
        a fotó-terület két széléhez feszül."""
        blokk = _NEZO[_NEZO.index('objectName: "captionBar"'):]
        blokk = blokk[: blokk.index("captionToggleButton")]
        assert "anchors.left:" in blokk and "anchors.right:" in blokk, (
            "a felirat-sáv nem feszül a fotó-terület két széléhez"
        )


class TestSemmiNemTakarjaEL:
    """A lebegő arc-gombok doboza a sáv FÖLÖTT ül, nem rajta.

    ⚠️ Ez is megtörtént hiba őre: a kirajzolt képen (a `grabWindow`
    felvételén) a `viewerFacesBar` a felirat-sáv jobb szélére csúszott, és
    eltakarta a kukát. Geometria-SZÁMOLÁSBÓL nem derült volna ki — mindkét
    elem a saját helyén volt.
    """

    def test_az_arc_gombok_a_sav_FOLOTT_ulnek(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        sav = _elem(window, "captionBar")
        arcok = _elem(window, "viewerFacesBar")
        sav_teteje = sav.mapToScene(sav.boundingRect().topLeft()).y()
        arcok_alja = arcok.mapToScene(arcok.boundingRect().bottomLeft()).y()
        assert arcok_alja <= sav_teteje + 0.5, (
            f"az arc-gombok doboza belelóg a felirat-sávba "
            f"(alja {arcok_alja:.0f}, a sáv teteje {sav_teteje:.0f})"
        )

    def test_a_kuka_nincs_letakarva(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        kuka = _elem(window, "captionTrashButton")
        arcok = _elem(window, "viewerFacesBar")
        k = kuka.mapToScene(kuka.boundingRect().center())
        p = arcok.mapFromScene(k)
        assert not arcok.contains(p), (
            "az arc-gombok doboza a kuka fölött van"
        )
