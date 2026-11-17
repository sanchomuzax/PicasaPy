"""#7123: a Sepia és a Fekete-fehér a nézőben az Effektek fület választja.

## Az eredeti (Picasa 3.9, `docs/specs/paritas-ellenorzes.md`, #7084)

A `0x00579330` igaz állapotában a `0x9d4a` (`"sepia"`) és a `0x9d4c`
(`"bw"`) a `0x9d4d` (`"warm"`), a `0x9d4b` (`"unsharp"`) és a `0x9d4e`
(`"grain2"`) ágával azonos hívásokat futtatja. A szerkesztőben nyitott
képnél a Kép ▸ Csoportos szerkesztés öt effekttétele tehát ugyanazt teszi.

## Nálunk a hiba

A `PhotoViewerGeometryActions.qml` `selectMenuEffect` listájából a `sepia`
és a `bw` hiányzott, ezért a `MainMenuBar.qml` egyképes
`applyEffectMany([row], name)` kötegre esett vissza, miközben a `warm`,
`unsharp` és `grain2` a 2. fület (Effektek) választotta ki.

## Mit mér ez a fájl

Minden bemenet valódi: a Kép menü fejlécére, a Csoportos szerkesztés
almenü sorára, majd a tételre érkezik `QTest.mouseClick`. A hatást a
renderelt panel `activeTab` állapotán (a fül, amit a felhasználó lát), a
lemezen maradt `filters=` láncon és a kötegelt visszavonás elérhetőségén
mérjük. A `0x005f8520` pontos hatása (kijelöl vagy alkalmaz is) örökölt
nyitott kérdés, ezért a teszt csak az ágak EGYSÉGESSÉGÉT rögzíti.

## A „Nem szabad” pontok

- a nézőben a tétel NEM módosítja a `filters=` láncot, és nem indít kötegelt
  műveletet (nincs visszavonható köteg);
- a könyvtárnézetben a kijelölt képekre a Sepia és a Fekete-fehér továbbra is
  lefut;
- az Alapvető javítások tételei (`autolight`, `autocolor`, `enhance`) a 0.
  fület választják, ezt a változtatás nem érinti.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    kijelol,
    szures,
    tetel_kattintasa,
    varj,
)

_BATCH = ("menuPictureBatchEdit",)

#: Effektek fül: a Picasa fülsorrendje szerint a 3. (index 2)
_EFFEKTEK_FUL = 2
#: Alapvető javítások fül: az 1. (index 0)
_ALAPVETO_FUL = 0

#: (menütétel, effektnév, a `filters=` kulcs, amit a könyvtári köteg ír)
_UJ_AGAK = (
    ("menuBatchSepia", "sepia", "sepia=1;"),
    ("menuBatchBlackWhite", "bw", "bw=1;"),
)
#: a már eddig is az Effektek fület választó testvérek (kontroll)
_TESTVEREK = (
    ("menuBatchWarmify", "warm"),
    ("menuBatchSharpen", "unsharp"),
    ("menuBatchFilmGrain", "grain2"),
)
_ALAPVETO = (
    ("menuBatchAutoContrast", "autolight"),
    ("menuBatchAutoColor", "autocolor"),
    ("menuBatchEnhance", "enhance"),
)


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezot_nyit(window, qt_app) -> QObject:
    """Megnyitja a nézőt az első képen, a panel az Alapvető javítások fülön."""
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", _ALAPVETO_FUL)
    qt_app.processEvents()
    assert panel.property("activeTab") == _ALAPVETO_FUL, (
        "a kiinduló fül nem az Alapvető javítások: a teszt nem bizonyít"
    )
    return panel


def _kozben_nincs_kotegmuvelet(controller) -> bool:
    return not controller.batchEditActive and not controller.canUndoBatchEdit


def _nezoben_kattint(kep_app, qt_app, tetel: str) -> tuple[QObject, object]:
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)
    panel = _nezot_nyit(window, qt_app)
    assert _kozben_nincs_kotegmuvelet(controller), (
        "a kiinduló állapotban már van kötegművelet: a teszt nem bizonyít"
    )
    tetel_kattintasa(window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH)
    qt_app.processEvents()
    return panel, controller


class TestNezoEffektekFul:
    @pytest.mark.parametrize(("tetel", "nev", "_kulcs"), _UJ_AGAK)
    def test_sepia_es_bw_az_effektek_fulet_valasztja(
        self, kep_app, qt_app, tetel, nev, _kulcs
    ):
        panel, _controller = _nezoben_kattint(kep_app, qt_app, tetel)

        assert varj(qt_app, lambda: panel.property("activeTab") == _EFFEKTEK_FUL), (
            f"a nézőben a {nev} nem az Effektek fület választotta "
            f"(activeTab={panel.property('activeTab')})"
        )

    @pytest.mark.parametrize(("tetel", "nev"), _TESTVEREK)
    def test_a_testverek_ugyanugy_az_effektek_fulet_valasztjak(
        self, kep_app, qt_app, tetel, nev
    ):
        panel, _controller = _nezoben_kattint(kep_app, qt_app, tetel)

        assert varj(qt_app, lambda: panel.property("activeTab") == _EFFEKTEK_FUL), (
            f"a nézőben a {nev} nem az Effektek fület választotta "
            f"(activeTab={panel.property('activeTab')})"
        )

    @pytest.mark.parametrize(("tetel", "nev", "kulcs"), _UJ_AGAK)
    def test_nem_modositja_a_lancot_es_nem_indit_koteget(
        self, kep_app, qt_app, tetel, nev, kulcs
    ):
        _window, controller, _engine = kep_app
        _nezoben_kattint(kep_app, qt_app, tetel)

        # a (hibás) háttérköteg is lefutott volna: kivárjuk a háttérmunkát
        assert controller.waitForBackgroundWorkers(10.0)
        qt_app.processEvents()

        for sor in range(len(controller.photos.photos)):
            assert kulcs not in szures(controller, sor), (
                f"a nézőben a {nev} a {sor}. kép láncát módosította"
            )
        assert _kozben_nincs_kotegmuvelet(controller), (
            f"a nézőben a {nev} kötegelt műveletet indított"
        )

    @pytest.mark.parametrize(("tetel", "nev"), _ALAPVETO)
    def test_az_alapveto_javitasok_tovabbra_is_a_0_fulet_valasztjak(
        self, kep_app, qt_app, tetel, nev
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        panel = _nezot_nyit(window, qt_app)
        panel.setProperty("activeTab", _EFFEKTEK_FUL)
        qt_app.processEvents()

        tetel_kattintasa(window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH)

        assert varj(qt_app, lambda: panel.property("activeTab") == _ALAPVETO_FUL), (
            f"a nézőben a {nev} nem az Alapvető javítások fület választotta"
        )


class TestKonyvtarnezetKotegelt:
    @pytest.mark.parametrize(("tetel", "nev", "kulcs"), _UJ_AGAK)
    def test_a_kijelolt_kepekre_tovabbra_is_lefut(
        self, kep_app, qt_app, tetel, nev, kulcs
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        sorok = [0, 1]
        kijelol(window, qt_app, sorok)
        assert window.property("viewerOpen") is not True, (
            "a könyvtárnézet helyett nyitott néző van: a teszt nem bizonyít"
        )
        assert all(kulcs not in szures(controller, sor) for sor in sorok), (
            f"a {kulcs} már a kiinduló láncban van: a teszt nem bizonyít"
        )

        wait_for_photo_op(
            controller,
            lambda: tetel_kattintasa(
                window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH
            ),
            qt_app=qt_app,
        )

        assert varj(
            qt_app,
            lambda: all(kulcs in szures(controller, sor) for sor in sorok),
        ), f"a könyvtárnézetben a {nev} nem került a kijelölt képekre"
        assert controller.photos.photos[2].name not in {
            controller.photos.photos[sor].name for sor in sorok
        }
        assert kulcs not in szures(controller, 2), (
            "a kijelöletlen képre is rákerült az effekt"
        )
