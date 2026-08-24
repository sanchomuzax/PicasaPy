"""A gyűrű HOVERRE jön elő és elhalványul — #1000.

Spec: `docs/specs/picasa-kollazs-felulet.md` **5.1/b**
(`RingNodeFadeHandler`, `0x007e6220`; a zár: `RingNodeFadeLockHandler`,
`0x007e6390`).

## Mit mérünk, és mit NEM

A gyűrű **léte** és a **láthatósága** két külön dolog, és a tesztek is
külön mérik őket:

* a **lét** a kijelöléshez kötött — ezt a `visible` mutatja, és a #947
  tesztjei már őrzik. Ez a fájl nem nyúl hozzá;
* a **láthatóság** az egérmutatótól függ — ezt az `opacity` mutatja. Az
  eredeti az eltűnéskor is csak **alfa 1**-ig (a 256-ból) halványít, tehát
  a gyűrű a felhasználó szeme elől eltűnik, de a fogantyúi ÉLNEK.

## Az időzítés mérése — miért nem `sleep`

Három konstans van (0,5 s késleltetés, 0,25 s beúszás, 0,5 s kiúszás), és
mindhármat **kétféleképpen** lehetne mérni: megvárni, vagy megnézni, mire
van BEÁLLÍTVA. A valós idejű mérés a CI-n ingadozó — egy terhelt futó
gépen a 0,5 s könnyen 0,7 lesz, és a teszt hamis riasztást ad.

Ez a fájl ezért:

1. a **beállított** értékeket olvassa ki a felület property-jeiből, és
   külön ellenőrzi, hogy a `Behavior` tényleg AZOKAT használja
   (`TestABeallitottIdok`) — itt nulla időfüggés van;
2. az **állapotgépet** a `Timer` állapotán át lépteti
   (`TestAzAllapotgep`): a lejáratot mi váltjuk ki (`stop()`), hogy a
   mérés ne fél másodperces alvástól függjön;
3. a **teljes láncot** egyszer, valós időben is végigviszi
   (`TestATeljesLanc`) — de VÁRAKOZÁSSAL, nem időméréssel: a feltétel
   teljesülésére várunk bőséges határidővel. Ez akkor sem ingadozó, ha a
   gép lassú; csak akkor bukik, ha a lánc SOHA nem fut le.

## Miért közvetlen `QHoverEvent`

Fejnélküli (offscreen) környezetben a `QTest.mouseMove` NEM szül
hover-eseményt (#706 tanulsága, két kört vitt el). A mutatót ezért
közvetlenül küldött `QHoverEvent`-tel visszük a helyére, és a mérés
KÖZVETLENÜL a hover után történik.
"""

from __future__ import annotations

import math
import time

import pytest
from PySide6.QtCore import QEvent, QObject, QPoint, QPointF
from PySide6.QtGui import QGuiApplication, QHoverEvent

from support.collage_canvas_harness import (
    _child,
    _csomopontok,
    _eger_fel,
    _eger_le,
    _eger_mozog,
    _egyseg,
    _kozeppont,
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


# --------------------------------------------------------------------------
# Segédek
# --------------------------------------------------------------------------


def _lap(panel):
    return _child(panel, "collageSheet")


def _hover(view, pont: QPointF) -> None:
    """Az egérmutatót a pontra visszük — közvetlen `QHoverEvent`-tel.

    ⚠️ ELŐBB egy távoli pontra: a jelenet hover-állapota pozíció-alapú, és
    ha a mutató „már ott van", az újabb, azonos pozíciójú esemény nem vált
    ki állapotváltozást (#706)."""
    app = QGuiApplication.instance()
    for cel in (QPointF(-100.0, -100.0), pont):
        app.sendEvent(
            view, QHoverEvent(QEvent.Type.HoverMove, cel, cel, QPointF(-1, -1))
        )
        app.processEvents()


def _hover_el(view) -> None:
    """A mutató elhagyja az ablakot."""
    app = QGuiApplication.instance()
    app.sendEvent(
        view,
        QHoverEvent(
            QEvent.Type.HoverLeave,
            QPointF(-1000, -1000),
            QPointF(-1000, -1000),
            QPointF(-1, -1),
        ),
    )
    app.processEvents()


def _lap_pontra(panel, u: float, v: float) -> QPointF:
    """Lapegység-koordináta → ABLAK-koordináta, kerekítés nélkül.

    A 12 képpontos tűrés mérésénél 2 képponton múlik a verdikt: a harness
    egész pontra kerekítő `_lap_pont`-ja itt elvinné a mérést."""
    e = _egyseg(panel)
    return _lap(panel).mapToScene(QPointF(u * e, v * e))


def _kep_szelen_tul(panel, index: int, tavolsag_px: float) -> QPointF:
    """A csomópont jobb szélétől `tavolsag_px`-re, a KÉP saját tengelyén.

    A csomópont EL VAN FORGATVA, ezért a „szélétől 11 képpontra" pont a
    saját rendszerében értendő, és onnan forgatjuk vissza az ablakba —
    különben ferde képnél nem azt mérnénk, amit mondunk."""
    csomopont = _csomopontok(panel.property("controller"))[index]
    e = _egyseg(panel)
    lx = csomopont.width * e / 2.0 + tavolsag_px
    th = csomopont.theta
    dx = lx * math.cos(th)
    dy = lx * math.sin(th)
    return _lap_pontra(
        panel, csomopont.center_x + dx / e, csomopont.center_y + dy / e
    )


def _kep_kozepe(panel, index: int) -> QPointF:
    csomopont = _csomopontok(panel.property("controller"))[index]
    return _lap_pontra(panel, csomopont.center_x, csomopont.center_y)


def _tavoli_pont(panel) -> QPointF:
    """A lap egy sarka — biztosan egyetlen képen sincs rajta."""
    lap = _lap(panel)
    return lap.mapToScene(QPointF(2.0, 2.0))


def _gyuru(panel, index: int = 0):
    return _child(panel, f"collageRing{index}")


def _idozito(gyuru, index: int = 0):
    talalt = gyuru.findChild(QObject, f"collageRingFadeDelay{index}")
    assert talalt is not None, "a gyűrűnek nincs elhalványítási időzítője"
    return talalt


def _var(feltetel, masodperc: float = 8.0) -> bool:
    """Esemény-pörgetés, amíg a feltétel teljesül (vagy lejár az idő).

    ⚠️ Ez VÁRAKOZÁS, nem időmérés: a határidő csak felső korlát, a teszt
    verdiktje nem függ attól, mennyi idő telt el."""
    app = QGuiApplication.instance()
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        app.processEvents()
        time.sleep(0.005)
    return bool(feltetel())


def _kijelolve(controller, index: int = 0):
    controller.setCollageSelection([index])
    QGuiApplication.instance().processEvents()


# --------------------------------------------------------------------------
# 1. A beállított idők és a 12 képpontos tűrés — nulla időfüggéssel
# --------------------------------------------------------------------------
class TestABeallitottIdok:
    """A négy konstans a `0x007e6220` diszasszemblátumából (spec 5.1/b)."""

    def test_a_negy_konstans_a_feluleten_olvashato(self, controller):
        panel = _panel(controller)
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        assert gyuru.property("hoverTolerancePx") == 12, "a tűrés 12 képpont"
        assert gyuru.property("fadeDelayMs") == 500, (
            "a kurzor távozása után 0,5 s-ig még látszik"
        )
        assert gyuru.property("fadeInMs") == 250, "a beúszás 0,25 s"
        assert gyuru.property("fadeOutMs") == 500, "a kiúszás 0,5 s"

    def test_az_idozito_a_beallitott_kesleltetest_hasznalja(self, controller):
        """A property önmagában díszlet lenne — az időzítőnek is ez kell."""
        panel = _panel(controller)
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        assert _idozito(gyuru).property("interval") == gyuru.property("fadeDelayMs")

    def test_a_beuszas_es_a_kiuszas_hossza_kulonbozik(self, controller):
        """0,25 s be, 0,5 s ki — a `Behavior` a MENETIRÁNYTÓL függ."""
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        anim = gyuru.findChild(QObject, "collageRingFadeAnim0")
        assert anim is not None, "a gyűrűnek nincs elhalványítási animációja"

        _hover(view, _kep_kozepe(panel, 0))
        assert gyuru.property("shown") is True
        assert anim.property("duration") == 250, "megjelenéskor 0,25 s"

        _hover(view, _tavoli_pont(panel))
        _idozito(gyuru).stop()
        QGuiApplication.instance().processEvents()
        assert gyuru.property("shown") is False
        assert anim.property("duration") == 500, "eltűnéskor 0,5 s"


class TestATizenketKeppontosTures:
    """A tűrés KÜLÖN állítás: 11 képpontra még látszik, 13-ra már nem."""

    def test_tizenegy_keppontra_a_keptol_meg_latszik(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        _hover(view, _kep_szelen_tul(panel, 0, 11.0))

        assert gyuru.property("hovered") is True, (
            "a kép szélétől 11 képpontra a gyűrűnek még elő kell jönnie "
            "(a tűrés 12 képpont)"
        )

    def test_tizenharom_keppontra_mar_nem(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        _hover(view, _kep_szelen_tul(panel, 0, 13.0))

        assert gyuru.property("hovered") is False, (
            "a kép szélétől 13 képpontra a tűrésen KÍVÜL vagyunk"
        )


# --------------------------------------------------------------------------
# 2. Az állapotgép — a `Timer` állapotán át léptetve
# --------------------------------------------------------------------------
class TestAzAllapotgep:
    def test_kijeloles_utan_hover_NELKUL_a_gyuru_halvany(self, controller):
        """Ez a jegy lelete: ma a gyűrű a kijelöléstől azonnal látszik."""
        panel = _panel(controller)
        view = panel.property("_view")
        _hover(view, _tavoli_pont(panel))
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        assert gyuru.isVisible(), "a gyűrű LÉTE a kijelöléshez kötött — az marad"
        assert gyuru.property("shown") is False, (
            "a kijelölés önmagában nem hozza elő a gyűrűt: az eredetiben a "
            "láthatóság az egérmutatótól függ (spec 5.1/b)"
        )
        assert gyuru.opacity() < 0.5, (
            "hover nélkül a gyűrűnek halványnak kell lennie"
        )

    def test_hoverre_elojon(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        _hover(view, _kep_kozepe(panel, 0))

        assert gyuru.property("hovered") is True
        assert gyuru.property("shown") is True
        assert _idozito(gyuru).property("running") is False, (
            "amíg a kurzor a képen van, az időzítő nem futhat"
        )

    def test_a_kurzor_tavozasakor_indul_a_kesleltetes(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))

        _hover(view, _tavoli_pont(panel))

        assert gyuru.property("hovered") is False
        assert _idozito(gyuru).property("running") is True, (
            "a kurzor távozása után a 0,5 s-os késleltetésnek el kell indulnia"
        )
        assert gyuru.property("shown") is True, (
            "a késleltetés ALATT a gyűrű még látszik"
        )

    def test_a_kesleltetes_lejartaval_elhalvanyul(self, controller):
        """A lejáratot MI váltjuk ki — így a mérés nem alvástól függ."""
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))
        _hover(view, _tavoli_pont(panel))

        _idozito(gyuru).stop()
        QGuiApplication.instance().processEvents()

        assert gyuru.property("shown") is False
        assert gyuru.isVisible(), (
            "az elhalványult gyűrű LÉTEZIK — az eredeti is csak alfa 1-ig megy"
        )

    def test_a_visszatero_kurzor_leallitja_a_kesleltetest(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))
        _hover(view, _tavoli_pont(panel))
        assert _idozito(gyuru).property("running") is True

        _hover(view, _kep_kozepe(panel, 0))

        assert _idozito(gyuru).property("running") is False
        assert gyuru.property("shown") is True

    def test_az_ablakot_elhagyva_is_indul_a_kesleltetes(self, controller):
        """`HoverLeave`: a mutató kimegy az ablakból, nem csak a képről."""
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))

        _hover_el(view)

        assert gyuru.property("hovered") is False
        assert _idozito(gyuru).property("running") is True


# --------------------------------------------------------------------------
# 3. A ZÁR — húzás közben a gyűrű látható marad
# --------------------------------------------------------------------------
class TestAZar:
    """`RingNodeFadeLockHandler` (`0x007e6390`) — a jegy kiemelt feltétele.

    Zár nélkül a gyűrű húzás közben eltűnne, ami ROSSZABB a mainál: a
    felhasználó a saját fogantyúját veszítené szem elől."""

    def test_huzas_kozben_a_gyuru_nem_halvanyul_el(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))
        assert gyuru.property("shown") is True

        kozep_x, kozep_y = _kozeppont(gyuru)
        kezdo = QPoint(round(kozep_x), round(kozep_y))
        _eger_le(view, kezdo)
        # a kurzor MESSZE kifut a képből — hover nélkül ez elhalványítaná
        tavol = QPoint(kezdo.x() + 300, kezdo.y() + 220)
        _eger_mozog(view, tavol)
        _hover(view, _tavoli_pont(panel))

        assert gyuru.property("fadeLocked") is True, "húzás közben zár van"
        assert _idozito(gyuru).property("running") is False, (
            "a zár FELFÜGGESZTI az időzítőt (spec 5.1/b)"
        )
        assert gyuru.property("shown") is True, (
            "húzás közben a gyűrűnek végig látszania kell"
        )

        _eger_fel(view, tavol)

    def test_a_huzas_vegen_a_zar_felold_es_indul_a_kesleltetes(self, controller):
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)
        _hover(view, _kep_kozepe(panel, 0))

        kozep_x, kozep_y = _kozeppont(gyuru)
        kezdo = QPoint(round(kozep_x), round(kozep_y))
        _eger_le(view, kezdo)
        # a képet a kurzor ALATT visszük, majd a kurzort a lap sarkába —
        # felengedéskor a mutató biztosan nincs a csomóponton
        cel = QPoint(kezdo.x() + 5, kezdo.y() + 5)
        _eger_mozog(view, cel)
        _eger_fel(view, cel)
        _hover(view, _tavoli_pont(panel))

        assert gyuru.property("fadeLocked") is False, "felengedve nincs zár"
        assert _idozito(gyuru).property("running") is True, (
            "a zár feloldása után a késleltetésnek el kell indulnia"
        )


# --------------------------------------------------------------------------
# 4. A teljes lánc, valós időben — VÁRAKOZÁSSAL, nem időméréssel
# --------------------------------------------------------------------------
class TestATeljesLanc:
    def test_hoverre_beuszik_majd_maga_el_is_halvanyul(self, controller):
        """Egyetlen eset, ami tényleg végigfuttatja az időzítőt.

        Nem azt állítja, hogy 0,5 s alatt történik — azt, hogy MEGTÖRTÉNIK.
        A határidő csak felső korlát, a verdikt nem függ az eltelt időtől."""
        panel = _panel(controller)
        view = panel.property("_view")
        _kijelolve(controller, 0)
        gyuru = _gyuru(panel)

        _hover(view, _kep_kozepe(panel, 0))
        assert _var(lambda: gyuru.opacity() > 0.99), (
            "hoverre a gyűrűnek teljesen elő kell úsznia"
        )

        # ⚠️ A VÉGÁLLAPOTRA várunk, nem egy „elég halvány" küszöbre: az
        # animáció közben bármikor átlépnénk egy laza küszöböt, és a
        # következő állítás egy félbehagyott átmenetet mérne.
        halvany = 1.0 / 256.0
        _hover(view, _tavoli_pont(panel))
        assert _var(lambda: gyuru.opacity() <= halvany + 1e-6), (
            "a kurzor távozása után a gyűrűnek magától el kell halványulnia "
            "(0,5 s várakozás + 0,5 s animáció)"
        )
        assert gyuru.isVisible(), "a gyűrű LÉTE közben végig megmarad"
        assert gyuru.opacity() == pytest.approx(halvany, abs=1e-6), (
            "az eredeti alfa 1-ig halványít a 256-ból, nem 0-ig"
        )
