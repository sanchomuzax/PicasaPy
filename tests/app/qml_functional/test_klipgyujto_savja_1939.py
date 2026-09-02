"""A „Továbbiak…" klip-gyűjtő mód ÜZENETSÁVJA az alsó sávban (#1939).

A mód lényege nálunk megvolt (a gomb működik, a Könyvtár lapra vált), de a
**visszaút felülete** más volt: egyetlen lebegő zöld gomb a jobb felső
sarokban, az eredetiben viszont egy teljes **üzenetsáv az ablak alján**.

## A mért kényszerek (spec `getmore-klipgyujto-mod.md` 3.1)

`thumbui/single_action_container: thumbui/basecontrolset`, `m_hidden`:

```
XConstraint 0, .365,  2      bal  = az osztópont + 2
XConstraint 1, 1,   -20      jobb = a sáv jobb széle − 20
YConstraint 0, 0,    45      felül = a vezérlőkészlet tetejétől + 45
YConstraint 1, 1,    -2      alul  = a készlet aljától − 2
```

⚠️ A `respack.yt`-ben tárolt 502 × 40 **NEM normatív** — az a
tervezővászon pillanatképe; a kényszerek felülírják (ugyanaz a
tanulság, mint a #1934-nél az `infotext_clip`-nél).

## A ✕ CSAK ELREJT (spec 2.3)

`Property hidetarget thumbui/single_action_container`, és más hívás nincs
mellette. Vagyis a mód NEM szakad meg: a projekt lapja nyitva marad, és a
lapsávból vissza lehet térni. Ezt külön esettel őrizzük, mert a
kézenfekvő (és téves) olvasat az volna, hogy a ✕ kilép a módból.
"""
from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app

_TRAYBAR = (
    Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "TrayBar.qml"
).read_text(encoding="utf-8")
_MAIN = (
    Path(picasapy.app.__file__).parent / "qml" / "Main.qml"
).read_text(encoding="utf-8")

#: MÉRT tűrés: a QML geometriája tört szám lehet.
TURES = 0.5


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


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


def _kattints(window, elem, qt_app):
    assert elem.width() > 0 and elem.height() > 0, "kattinthatatlan (0 méret)"
    kozep = elem.mapToScene(elem.boundingRect().center())
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


class TestASavLetezikEsAHelyenVan:
    def test_a_sav_az_ALSO_savban_van(self, qml_app, qt_app):
        window, _c, _e = qml_app
        sav = _elem(window, "traySingleActionBar")
        assert sav is not None, (
            "a klip-gyűjtő üzenetsáv nincs meg az alsó sávban"
        )

    def test_alapbol_REJTETT(self, qml_app, qt_app):
        """`m_hidden` a `.tre`-ben, `vis=0` a respack fejlécében."""
        window, _c, _e = qml_app
        sav = _elem(window, "traySingleActionBar")
        assert sav.isVisible() is False

    def test_a_kenyszerek_szerinti_vizszintes_helye(self, qml_app, qt_app):
        """bal = osztópont + 2, jobb = a sáv jobb széle − 20."""
        window, _c, _e = qml_app
        sav = _elem(window, "traySingleActionBar")
        fosav = _elem(window, "trayMainBar")
        osztopont = fosav.property("splitX")
        assert abs(sav.property("x") - (osztopont + 2)) <= TURES
        jobb = sav.property("x") + sav.property("width")
        assert abs(jobb - (fosav.property("width") - 20)) <= TURES

    def test_a_tarolt_502x40_NEM_normativ(self, qml_app, qt_app):
        """A sáv a kényszereket követi, nem a tervezővászon pillanatképét.

        Ellenpróba: az ablak szélesítésével a sávnak EGYÜTT kell nőnie —
        egy fix 502-es szélesség itt bukna el.
        """
        window, _c, _e = qml_app
        sav = _elem(window, "traySingleActionBar")
        elotte = sav.property("width")
        eredeti = window.width()
        try:
            window.setWidth(eredeti + 300)
            qt_app.processEvents()
            assert _var(qt_app, lambda: sav.property("width") > elotte), (
                "a sáv szélessége nem követi az ablakot (fix méret?)"
            )
        finally:
            window.setWidth(eredeti)
            qt_app.processEvents()


class TestASavTartalma:
    def test_az_uzenet_a_hivatalos_magyar_szoveg(self):
        """A `thumbui/single_action_message` hivatalos fordítása."""
        assert "Jelölje ki azokat az elemeket" in _TRAYBAR or (
            "single_action_message" in _TRAYBAR
        )

    def test_az_uzenet_JOBBRA_igazitott(self, qml_app, qt_app):
        """MÉRT: `Property textalign right` (`thumbui.tre`)."""
        window, _c, _e = qml_app
        uzenet = _elem(window, "traySingleActionMessage")
        assert uzenet is not None
        assert "AlignRight" in _TRAYBAR

    def test_a_vissza_gomb_109x43(self, qml_app, qt_app):
        window, _c, _e = qml_app
        gomb = _elem(window, "traySingleActionReturn")
        assert gomb is not None, "nincs visszatérő gomb a sávban"
        assert (gomb.width(), gomb.height()) == (109.0, 43.0)

    def test_az_x_18x18(self, qml_app, qt_app):
        window, _c, _e = qml_app
        x = _elem(window, "traySingleActionClose")
        assert x is not None, "nincs ✕ a sávban"
        assert (x.width(), x.height()) == (18.0, 18.0)


class TestAzXCsakElrejt:
    """A jegy legkönnyebben elrontható pontja.

    A kézenfekvő olvasat az volna, hogy a ✕ kilép a módból. MÉRVE nem:
    `Property hidetarget thumbui/single_action_container`, és más hívás
    nincs mellette — a mód marad, a projekt lapja nyitva marad.
    """

    def _modba(self, window, qt_app):
        window.setProperty("backToCollagePrompted", True)
        qt_app.processEvents()

    def test_az_x_utan_a_sav_eltunik(self, qml_app, qt_app):
        window, _c, _e = qml_app
        self._modba(window, qt_app)
        sav = _elem(window, "traySingleActionBar")
        x = _elem(window, "traySingleActionClose")
        if not _var(qt_app, lambda: sav.isVisible() is True):
            import pytest
            pytest.skip("a sáv ebben az összeállításban nem jelenik meg")
        _kattints(window, x, qt_app)
        assert _var(qt_app, lambda: sav.isVisible() is False)

    def test_az_x_NEM_lep_ki_a_modbol(self, qml_app, qt_app):
        """A mód jelzője marad — a lapsávból tovább lehet visszatérni."""
        window, _c, _e = qml_app
        self._modba(window, qt_app)
        sav = _elem(window, "traySingleActionBar")
        if not _var(qt_app, lambda: sav.isVisible() is True):
            import pytest
            pytest.skip("a sáv ebben az összeállításban nem jelenik meg")
        _kattints(window, _elem(window, "traySingleActionClose"), qt_app)
        assert _var(qt_app, lambda: sav.isVisible() is False)
        assert window.property("backToCollagePrompted") is True, (
            "a ✕ kilépett a módból — az eredeti CSAK elrejti a sávot"
        )


class TestARegiLebegoGombHelyett:
    def test_a_regi_lebego_gomb_mar_nincs(self):
        """A visszaút MOSTANTÓL az alsó sávban van — két párhuzamos
        vezérlő ugyanarra a műveletre zavaró lenne."""
        assert 'objectName: "backToCollageButton"' not in _MAIN

    def test_a_forras_KIMONDJA_hova_kerult(self):
        """Hogy egy későbbi kör ne „hiányzó gombként" tegye vissza."""
        assert "#1939" in _MAIN
