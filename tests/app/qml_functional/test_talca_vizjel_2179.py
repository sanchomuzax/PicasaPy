"""#2179 — a tálca „Kijelölés" vízjele MINDIG látszik, a képek ALATT.

A tulajdonos hat felvétele ugyanabban a mappában, növekvő elemszámmal:

| felvétel | a tálca tartalma | a felirat |
|---|---|---|
| …214634 | **1** bélyegkép | **LÁTSZIK** |
| …214636 | **3** bélyegkép | **LÁTSZIK** |
| …214646 | 11 bélyegkép | eltakarva |
| …214851 | 6 bélyegkép | a vége (`…lés`) **kilóg a képek jobb oldalán** |

Az utolsó sor dönti el a rétegsorrendet: a felirat **bal része a képek
alatt** van, a jobb vége kilátszik ⇒ a bélyegképek a felirat FÖLÉ
rajzolódnak. Ugyanezt mondja a `thumbui.tre` szülő-gyerek viszonya is
(`scratchpadbase` — és rajta a `scratchlabel` — előbb deklarálva, mint a
`thumbui/scratch`).

Nálunk fordítva volt: a felirat csak ÜRES tálcánál látszott, és a képek
FÖLÉ rajzolódott — két hiba egy méréssel.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


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
    return False


def _elem(window, nev):
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"nincs ilyen elem: {nev}"
    return obj


class TestAVizjelMINDIG_latszik:
    """Az eredetiben ez nem üres-állapot felirat, hanem állandó vízjel."""

    def test_ures_talcan_latszik(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: _elem(window, "trayScratchLabel") is not None)
        assert _elem(window, "trayScratchLabel").property("visible") is True

    def test_a_visible_NINCS_a_talca_tartalmahoz_kotve(self, qml_app, qt_app):
        """A kötés törlésének gépi megfelelője: a `visible` nem függhet a
        tálca elemszámától. Ha valaki visszakötné, ez a próba elbukik —
        akkor is, ha a próba futásakor a tálca épp üres."""
        from pathlib import Path

        forras = (
            Path(__file__).resolve().parents[3]
            / "src" / "picasapy" / "app" / "qml" / "PicasaPy" / "TrayBar.qml"
        ).read_text(encoding="utf-8")
        kezdet = forras.index('objectName: "trayScratchLabel"')
        blokk = forras[kezdet : forras.index("}", kezdet)]
        assert "visible:" not in blokk, (
            "a vízjelnek megint van `visible` kötése — az eredetiben MINDIG "
            f"látszik. A blokk: {blokk!r}"
        )


class TestARetegsorrend:
    """A bélyegképek a felirat FÖLÉ rajzolódnak."""

    def test_a_felirat_a_belyegkepsor_ALATT_van(self, qml_app, qt_app):
        window, _c, _e = qml_app
        assert _var(qt_app, lambda: window.findChild(QObject, "trayScratchStrip"))
        felirat = _elem(window, "trayScratchLabel")
        sor = _elem(window, "trayScratchStrip")
        assert felirat.property("z") < sor.property("z"), (
            f"a felirat z-je ({felirat.property('z')}) nem kisebb a "
            f"bélyegképsorénál ({sor.property('z')}) — a felirat a képek "
            "fölé rajzolódna"
        )


class TestAMertMegjelenes:
    """A respackből mért szín és betűméret."""

    def test_a_szin_a_mert_C3C3C3(self, qml_app, qt_app):
        window, _c, _e = qml_app
        szin = _elem(window, "trayScratchLabel").property("color")
        assert szin.name().lower() == "#c3c3c3", (
            f"a vízjel színe {szin.name()}, a respack {'#C3C3C3'}-t mér"
        )

    def test_a_betumeret_a_mert_14(self, qml_app, qt_app):
        """`m_displayfont14` = 14 pt (`picasa-hisztogram.md`), és a
        felirat mért magassága 19 képpont — a kettő egybevág."""
        window, _c, _e = qml_app
        assert _elem(window, "trayScratchLabel").property("font").pixelSize() == 14
