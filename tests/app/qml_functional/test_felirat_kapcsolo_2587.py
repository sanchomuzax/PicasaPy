"""#2587 — a felirat-kapcsoló KIKAPCSOLT feliratnál is látszik, és a sáv
a KRÓM színét viszi.

## A mérce: a tulajdonos NÉGY felvétele

`research/felirat-ki-bekapcsolva/` (1920 × 1080, 2026-09-06 22:32) — Picasa 3
és PicasaPy, felirat BE és KI állapotban, ugyanazon a képen.

| mérés | érték |
|---|---|
| a sáv sora | y **906…926** ⇒ **21 px** magas |
| a sáv színe | **`#c6c6c6`** — a KRÓM világosszürkéje |
| a kapcsoló doboza (MINDKÉT állapotban azonos) | x **287…303**, y **910…922** ⇒ **17 × 13** |
| a fotó-terület bal széle | x **286** ⇒ a gomb 1 képponttal beljebb |

A `.tre` ugyanezt mondja (`editpanel.tre:1262–1266`): a `captionbutton`
`hidetarget`-je a `caption` és a `captiontrash` — **magát a gombot nem**.
A `caption_icon` / `caption_yesicon` pár (`oneup.tre:112–124`) adja a két
állapotot: bekapcsolt feliratnál két vízszintes vonal a dobozban,
kikapcsoltnál ÜRES doboz.

## Amit a #2565 elrontott, és ez az őr megfog

- kikapcsolt feliratnál nem maradt LÁTHATÓ kapcsoló (a régi
  `captionRevealButton` a JOBB alsó sarokban ült, `opacity: 0.4`-gyel — a
  felvételen nem is látszott);
- a sáv SÖTÉT volt, világos módban idegen testként a világos króm alatt.
"""

from __future__ import annotations

import time
from pathlib import Path

import picasapy.app as app_csomag
from PySide6.QtCore import QObject

_QML_MAPPA = Path(app_csomag.__file__).parent / "qml" / "PicasaPy"
_NEZO = (_QML_MAPPA / "PhotoViewer.qml").read_text(encoding="utf-8")

#: MÉRT doboz-méret (`picasa3-felirat-*.jpg`)
GOMB_SZELES, GOMB_MAGAS = 17, 13
#: MÉRT sávmagasság
SAV_MAGAS = 21


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
    assert _var(qt_app, lambda: _elem(window, "captionToggleButton").isVisible())
    return nezo


def _kapcsold_ki(window, qt_app):
    """A feliratot a VEZÉRLŐN át kapcsoljuk, ahogy a gomb is tenné."""
    window.setProperty("viewerOpen", True)
    ctl = _elem(window, "photoViewer").property("editCtl")
    del ctl
    nezo = _elem(window, "photoViewer")
    nezo.metaObject().invokeMethod(nezo, "billentsdAFeliratot")
    qt_app.processEvents()


class TestAKapcsoloKIKAPCSOLVAisLATSZIK:
    def test_kikapcsolva_is_lathato(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        _kapcsold_ki(window, qt_app)
        assert _elem(window, "captionBar").isVisible() is False, (
            "a próba előfeltétele nem teljesült: a sáv nem kapcsolt ki"
        )
        gomb = _elem(window, "captionToggleButton")
        assert gomb.isVisible(), (
            "kikapcsolt feliratnál NINCS látható kapcsoló — az eredetiben a "
            "kis világos doboz ott marad a kép bal alsó sarkában"
        )
        assert gomb.opacity() > 0.9, (
            f"a kapcsoló csak {gomb.opacity():.2f} átlátszatlansággal látszik"
        )

    def test_a_BAL_also_sarokban_all(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        gomb = _elem(window, "captionToggleButton")
        terulet = _elem(window, "viewerPhotoArea")
        bal = gomb.mapToScene(gomb.boundingRect().topLeft()).x()
        terulet_bal = terulet.mapToScene(terulet.boundingRect().topLeft()).x()
        assert bal - terulet_bal < 6, (
            f"a kapcsoló {bal - terulet_bal:.0f} képpontra van a fotó-terület "
            "bal szélétől — az eredetiben 1"
        )

    def test_a_MERT_meret(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        gomb = _elem(window, "captionToggleButton")
        assert (gomb.width(), gomb.height()) == (GOMB_SZELES, GOMB_MAGAS)

    def test_a_kapcsolo_HELYE_nem_ugrik_a_ket_allapot_kozt(self, qml_app, qt_app):
        """A felvételeken a doboz MINDKÉT állapotban x 287…303, y 910…922."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        gomb = _elem(window, "captionToggleButton")
        be = gomb.mapToScene(gomb.boundingRect().center())
        _kapcsold_ki(window, qt_app)
        ki = gomb.mapToScene(gomb.boundingRect().center())
        assert abs(be.x() - ki.x()) < 1.5, "a kapcsoló vízszintesen elmozdult"
        assert abs(be.y() - ki.y()) < 6, (
            f"a kapcsoló {abs(be.y()-ki.y()):.0f} képpontot ugrott függőlegesen"
        )


class TestASavKINEZETE:
    def test_a_sav_MERT_magassaga(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        assert _elem(window, "captionBar").height() == SAV_MAGAS

    def test_a_sav_NEM_sotet_vilagos_temaban(self, qml_app, qt_app):
        """A #2565 `#d2000000`-t adott — a felvételen `#c6c6c6` áll."""
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        szin = _elem(window, "captionBarBackground").property("color")
        vilagossag = (szin.redF() + szin.greenF() + szin.blueF()) / 3
        assert szin.alphaF() > 0.95, "a sáv háttere áttetsző"
        assert vilagossag > 0.6, (
            f"a sáv világossága {vilagossag:.2f} — a mért `#c6c6c6` 0,78, "
            "a króm világosszürkéje"
        )

    def test_a_felirat_KONTRASZTOS_a_savon(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        hatter = _elem(window, "captionBarBackground").property("color")
        szoveg = _elem(window, "captionField").property("color")
        h = (hatter.redF() + hatter.greenF() + hatter.blueF()) / 3
        sz = (szoveg.redF() + szoveg.greenF() + szoveg.blueF()) / 3
        assert abs(h - sz) > 0.4, (
            f"a felirat és a sáv világossága túl közeli ({h:.2f} vs {sz:.2f})"
        )

    def test_a_felirat_FELKOVER(self, qml_app, qt_app):
        window, _c, _e = qml_app
        _nyisd_a_nezot(window, qt_app)
        betu = _elem(window, "captionField").property("font")
        assert betu.bold()


class TestAmiMEGSZUNT:
    def test_nincs_kulon_visszahozo_gomb_a_jobb_sarokban(self):
        """A `captionRevealButton` szerepét a mért helyű kapcsoló vette át."""
        assert "captionRevealButton" not in _NEZO
