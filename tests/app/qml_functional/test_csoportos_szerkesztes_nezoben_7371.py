"""#7371: a Kép ▸ Csoportos szerkesztés effektparancsai és a Ctrl+Shift+B a
szerkesztőben nyitott képre HATNAK, nem csak fület váltanak.

## Az eredeti (Picasa 3.9, `docs/specs/paritas-folyamat-7346.md`)

A Kép menü effektparancsai szerkesztőben nyitott képnél fület váltanak, majd
a csempekattintás végpontját (`0x005f8520`) hívják: a hatás azonnal a képre
kerül. A Ctrl+Shift+B (`0x005e6370` -> `0x005fe370(panel, "bw")`) a mért
Ctrl+Shift+E ikertestvére (`job-810`). A #7123 korábbi olvasata (csak fület
vált) téves volt.

## Mérce és mit NEM mér

Minden bemenet valódi: a menüsorra és a tételre `QTest.mouseClick`, a
gyorsbillentyű `QTest.keyClick`; parancsot, jelet nem hívunk közvetlenül. A
hatást a felhasználó felől mérjük: a megnyitott kép `.picasa.ini` `filters=`
lánca, az Undo felirat, a panel fülje és a valódi Visszavonás-gomb. A
mérce a CSEMPEKATTINTÁS, illetve (Film Grain: nincs csempéje) az egyképes
könyvtári köteg eredménye: a nézői lánc szövege egyezik velük.

A teszt a vizuális egyezést (az eredeti Picasa képe vs. a miénk) NEM méri;
az a jegy C1 felvételére vár. Itt a lánc és a visszavonás viselkedését
rögzítjük.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

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
from tests.app.qml_functional._szerkeszto_5150_helpers import item, kattint

_BATCH = ("menuPictureBatchEdit",)
CTRL_SHIFT = Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier

#: a Picasa fülsorrendje szerint: Alapvető javítások (0), Effektek (2)
_ALAPVETO_FUL = 0
_EFFEKTEK_FUL = 2

#: (menütétel, a tétel effektneve, a fül, a lánc kulcsa, az Undo felirat része,
#:  a csempe, amelyik a mérce - None: nincs csempéje)
_ALAPVETO = (
    ("menuBatchAutoContrast", "autolight", _ALAPVETO_FUL, "autolight=1;",
     "Auto Contrast", "editToolAutolight"),
    ("menuBatchAutoColor", "autocolor", _ALAPVETO_FUL, "autocolor=1;",
     "Auto Color", "editToolAutocolor"),
    ("menuBatchEnhance", "enhance", _ALAPVETO_FUL, "enhance=1;",
     "I'm Feeling Lucky", "editToolEnhance"),
)
_EFFEKTEK = (
    ("menuBatchSepia", "sepia", _EFFEKTEK_FUL, "sepia=1;", "Sepia", "effectSepia"),
    ("menuBatchBlackWhite", "bw", _EFFEKTEK_FUL, "bw=1;", "B&W", "effectBw"),
    ("menuBatchWarmify", "warm", _EFFEKTEK_FUL, "warm=1;", "Warmify", "effectWarm"),
    ("menuBatchFilmGrain", "grain2", _EFFEKTEK_FUL, "grain2=1;", "Film Grain", None),
)
_EGYGOMBOS = _ALAPVETO + _EFFEKTEK


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _nezot_nyit(window, qt_app, ful: int = _ALAPVETO_FUL):
    """Megnyitja a nézőt az első képen. Visszaad: néző, panel, szerkesztő."""
    window.setProperty("viewerOpen", True)
    nezo = gyerek(window, "photoViewer")
    nezo.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = gyerek(window, "viewerEditorPanel")
    panel.setProperty("activeTab", ful)
    qt_app.processEvents()
    assert panel.property("activeTab") == ful, (
        "a kiinduló fül nem a kért: a teszt nem bizonyít"
    )
    return nezo, panel, nezo.property("editCtl")


def _kezdo_allapot(kep_app, qt_app, ful: int = _ALAPVETO_FUL):
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)
    nezo, panel, szerk = _nezot_nyit(window, qt_app, ful)
    assert szures(controller, 0) == "", "a kiinduló lánc nem üres: nem bizonyít"
    assert not controller.canUndoBatchEdit, "van kötegelt undo: nem bizonyít"
    return window, controller, panel, szerk


def _menu(window, qt_app, tetel: str) -> None:
    tetel_kattintasa(window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH)
    qt_app.processEvents()


def _visszavon(window, qt_app) -> None:
    """A panel VALÓDI Visszavonás-gombja."""
    kattint(window, item(window, "editUndoButton"), qt_app)


def _billentyu(window, qt_app, kulcs: Qt.Key) -> None:
    window.requestActivate()
    QTest.keyClick(window, kulcs, CTRL_SHIFT)
    for _ in range(5):
        qt_app.processEvents()


class TestMenuparancsANyitottKepre:
    @pytest.mark.parametrize(
        ("tetel", "nev", "ful", "kulcs", "felirat", "_csempe"), _EGYGOMBOS
    )
    def test_a_parancs_a_megnyitott_kepre_hat(
        self, kep_app, qt_app, tetel, nev, ful, kulcs, felirat, _csempe
    ):
        window, controller, panel, szerk = _kezdo_allapot(kep_app, qt_app)

        _menu(window, qt_app, tetel)

        assert varj(qt_app, lambda: panel.property("activeTab") == ful), (
            f"a {nev} nem a {ful}. fület választotta"
        )
        assert varj(qt_app, lambda: szures(controller, 0).endswith(kulcs)), (
            f"a {nev} nem került a megnyitott kép láncára: {szures(controller, 0)!r}"
        )
        assert varj(qt_app, lambda: szerk.property("undoAction") == nev), (
            f"az Undo-sor nem a {nev} műveletet mutatja"
        )
        assert felirat in str(panel.property("undoLabel")), (
            f"az Undo felirat nem nevezi meg a(z) {felirat} műveletet: "
            f"{panel.property('undoLabel')!r}"
        )
        for sor in (1, 2):
            assert szures(controller, sor) == "", (
                f"a nem megnyitott {sor}. kép láncát is módosította a {nev}"
            )
        assert not controller.canUndoBatchEdit and not controller.batchEditActive, (
            f"a {nev} kötegelt műveletet indított a nézőben"
        )

    @pytest.mark.parametrize(
        ("tetel", "nev", "ful", "kulcs", "_felirat", "_csempe"), _EGYGOMBOS
    )
    def test_egy_visszavonas_visszaadja_az_elozo_allapotot(
        self, kep_app, qt_app, tetel, nev, ful, kulcs, _felirat, _csempe
    ):
        window, controller, panel, szerk = _kezdo_allapot(kep_app, qt_app)
        _menu(window, qt_app, tetel)
        assert varj(qt_app, lambda: szures(controller, 0).endswith(kulcs)), (
            f"a {nev} nem került a láncra: a teszt nem bizonyít"
        )

        _visszavon(window, qt_app)

        assert varj(qt_app, lambda: szures(controller, 0) == ""), (
            f"a Visszavonás nem vette le a {nev} réteget: {szures(controller, 0)!r}"
        )
        assert szerk.property("undoAction") != nev

    @pytest.mark.parametrize(
        ("tetel", "nev", "_ful", "kulcs", "_felirat", "csempe"),
        [t for t in _EGYGOMBOS if t[5] is not None],
    )
    def test_ugyanazt_adja_mint_a_csempekattintas(
        self, kep_app, qt_app, tetel, nev, _ful, kulcs, _felirat, csempe
    ):
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        # a MÉRCE: a csempe valódi kattintása a saját fülén
        panel.setProperty("activeTab", _ful)
        qt_app.processEvents()
        kattint(window, item(window, csempe), qt_app)
        assert varj(qt_app, lambda: szures(controller, 0).endswith(kulcs)), (
            f"a {csempe} csempe nem tette a láncra a {nev} réteget"
        )
        csempe_lanc = szures(controller, 0)
        _visszavon(window, qt_app)
        assert varj(qt_app, lambda: szures(controller, 0) == "")

        _menu(window, qt_app, tetel)

        assert varj(qt_app, lambda: szures(controller, 0) == csempe_lanc), (
            f"a menüparancs lánca ({szures(controller, 0)!r}) nem egyezik a "
            f"csempekattintáséval ({csempe_lanc!r})"
        )

    @pytest.mark.parametrize(
        ("tetel", "nev", "_ful", "kulcs", "_felirat", "_csempe"), _EGYGOMBOS
    )
    def test_ugyanazt_adja_mint_az_egykepes_konyvtari_koteg(
        self, kep_app, qt_app, tetel, nev, _ful, kulcs, _felirat, _csempe
    ):
        """A Film Grainnek nincs csempéje: a mérce az egyképes köteg."""
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [1])
        wait_for_photo_op(controller, lambda: _menu(window, qt_app, tetel),
                          qt_app=qt_app)
        assert varj(qt_app, lambda: szures(controller, 1).endswith(kulcs)), (
            f"a könyvtári köteg nem tette a láncra a {nev} réteget"
        )
        koteg_lanc = szures(controller, 1)
        kijelol(window, qt_app, [0])
        nezo, panel, _szerk = _nezot_nyit(window, qt_app)
        assert szures(controller, 0) == ""

        _menu(window, qt_app, tetel)

        assert varj(qt_app, lambda: szures(controller, 0) == koteg_lanc), (
            f"a nézői lánc ({szures(controller, 0)!r}) nem egyezik az egyképes "
            f"köteg láncával ({koteg_lanc!r})"
        )


class TestAlapvetoJavitasokNoopSzabalya:
    def test_a_lanc_veren_allo_jo_napom_van_ujra_nem_halmozodik(
        self, kep_app, qt_app
    ):
        """A láncvégi no-op szabály (`enhanceInViewer`) megmarad."""
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        _menu(window, qt_app, "menuBatchEnhance")
        assert varj(qt_app, lambda: szures(controller, 0) == "enhance=1;")

        _menu(window, qt_app, "menuBatchEnhance")

        assert szures(controller, 0).count("enhance=1;") == 1, (
            "a második Jó napom van újabb réteget tett a láncra"
        )


class TestSharpenParameterPanel:
    def _sharpen_nyitva(self, kep_app, qt_app):
        window, controller, panel, szerk = _kezdo_allapot(kep_app, qt_app)
        _menu(window, qt_app, "menuBatchSharpen")
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "a Sharpen nem nyitotta meg a paraméterpanelt"
        )
        return window, controller, panel, szerk

    def test_a_panel_nyilik_es_a_lanc_nem_valtozik(self, kep_app, qt_app):
        window, controller, panel, _szerk = self._sharpen_nyitva(kep_app, qt_app)

        assert panel.property("activeTab") == _EFFEKTEK_FUL
        assert panel.property("paramEffectName") == "unsharp2"
        assert szures(controller, 0) == "", (
            "a Sharpen a panel Alkalmazása nélkül a láncra került"
        )
        assert not controller.canUndoBatchEdit and not controller.batchEditActive

    def test_a_panel_cime_a_csempe_felirata(self, kep_app, qt_app):
        window, _controller, panel, _szerk = self._sharpen_nyitva(kep_app, qt_app)
        menu_cim = str(panel.property("paramEffectTitle"))
        kattint(window, item(window, "effectParamCancelButton"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)

        kattint(window, item(window, "effectUnsharp"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "a Sharpen csempe nem nyitotta meg a panelt: a teszt nem bizonyít"
        )

        assert menu_cim and menu_cim != "unsharp2", (
            f"a panel címe a belső kulcs vagy üres: {menu_cim!r}"
        )
        assert menu_cim == str(panel.property("paramEffectTitle")), (
            "a menüből nyitott panel címe eltér a csempéből nyitottétől"
        )

    def test_a_megse_visszaadja_az_allapotot(self, kep_app, qt_app):
        window, controller, panel, szerk = self._sharpen_nyitva(kep_app, qt_app)

        kattint(window, item(window, "effectParamCancelButton"), qt_app)

        assert varj(qt_app, lambda: panel.property("paramPanelActive") is False)
        assert szures(controller, 0) == ""
        assert szerk.property("undoAction") != "unsharp2"

    def test_az_alkalmaz_a_lancra_teszi_es_visszavonhato(self, kep_app, qt_app):
        window, controller, panel, szerk = self._sharpen_nyitva(kep_app, qt_app)

        kattint(window, item(window, "effectParamApplyButton"), qt_app)

        assert varj(qt_app, lambda: "unsharp2=" in szures(controller, 0)), (
            f"az Alkalmaz nem tette a láncra a Sharpent: {szures(controller, 0)!r}"
        )
        assert varj(qt_app, lambda: szerk.property("undoAction") == "unsharp2")
        assert "Sharpen" in str(panel.property("undoLabel"))
        _visszavon(window, qt_app)
        assert varj(qt_app, lambda: szures(controller, 0) == "")


class TestKapuk:
    """A kapuk azonosak a csempéjével: nyitott eszköz alatt a parancs no-op."""

    def test_nyitott_kiegyenesites_alatt_nem_alkalmaz(self, kep_app, qt_app):
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        kattint(window, item(window, "editToolTilt"), qt_app)
        assert varj(qt_app, lambda: panel.property("tiltActive") is True), (
            "a kiegyenesítés nem nyílt meg: a teszt nem bizonyít"
        )

        _menu(window, qt_app, "menuBatchSepia")

        assert szures(controller, 0) == "", (
            "a Sepia nyitott Kiegyenesítés alatt is a láncra került"
        )
        assert not controller.canUndoBatchEdit
        # pozitív kontroll: a kiegyenesítés nélkül ugyanez a parancs hat
        panel.setProperty("tiltActive", False)
        qt_app.processEvents()
        _menu(window, qt_app, "menuBatchSepia")
        assert varj(qt_app, lambda: szures(controller, 0).endswith("sepia=1;")), (
            "a kiegyenesítés nélkül sem hatott a Sepia: az előző állítás üres"
        )

    def test_nyitott_parameterpanel_alatt_nem_alkalmaz(self, kep_app, qt_app):
        window, controller, panel, _szerk = _kezdo_allapot(
            kep_app, qt_app, _EFFEKTEK_FUL
        )
        kattint(window, item(window, "effectUnsharp"), qt_app)
        assert varj(qt_app, lambda: panel.property("paramPanelActive") is True), (
            "a Sharpen csempe nem nyitotta meg a panelt: a teszt nem bizonyít"
        )

        _menu(window, qt_app, "menuBatchSepia")

        assert szures(controller, 0) == "", (
            "a Sepia nyitott paraméterpanel alatt is a láncra került"
        )
        # pozitív kontroll: a panel elvetése után ugyanez a parancs hat
        QMetaObject.invokeMethod(
            panel, "cancelParamPanel", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        assert panel.property("paramPanelActive") is False
        _menu(window, qt_app, "menuBatchSepia")
        assert varj(qt_app, lambda: szures(controller, 0).endswith("sepia=1;")), (
            "a panel nélkül sem hatott a Sepia: az előző állítás üres"
        )

    def test_a_kijelolt_konyvtari_kepekre_valtozatlanul_kotegel(
        self, kep_app, qt_app
    ):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [0, 1])
        assert window.property("viewerOpen") is not True

        wait_for_photo_op(controller, lambda: _menu(window, qt_app, "menuBatchSepia"),
                          qt_app=qt_app)

        assert varj(
            qt_app,
            lambda: all(szures(controller, s).endswith("sepia=1;") for s in (0, 1)),
        ), "a könyvtárban a Sepia nem került a kijelölt képekre"
        assert szures(controller, 2) == ""


class TestCtrlShiftB:
    def test_a_billentyu_feketefeheret_ad_a_megnyitott_kepre(self, kep_app, qt_app):
        window, controller, panel, szerk = _kezdo_allapot(kep_app, qt_app)

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;")), (
            "a Ctrl+Shift+B a szerkesztőben nem tette a láncra a B&W réteget: "
            f"{szures(controller, 0)!r}"
        )
        assert varj(qt_app, lambda: szerk.property("undoAction") == "bw")
        assert "B&W" in str(panel.property("undoLabel"))
        for sor in (1, 2):
            assert szures(controller, sor) == "", (
                f"a nem megnyitott {sor}. kép láncát is módosította"
            )
        assert not controller.canUndoBatchEdit and not controller.batchEditActive

    def test_egy_visszavonas_visszaadja_az_elozo_allapotot(self, kep_app, qt_app):
        window, controller, _panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        _billentyu(window, qt_app, Qt.Key.Key_B)
        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;"))

        _visszavon(window, qt_app)

        assert varj(qt_app, lambda: szures(controller, 0) == "")

    def test_ugyanazt_adja_mint_a_menuparancs(self, kep_app, qt_app):
        window, controller, _panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        _menu(window, qt_app, "menuBatchBlackWhite")
        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;"))
        menu_lanc = szures(controller, 0)
        _visszavon(window, qt_app)
        assert varj(qt_app, lambda: szures(controller, 0) == "")

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert varj(qt_app, lambda: szures(controller, 0) == menu_lanc)

    def test_nem_valtja_a_fulet(self, kep_app, qt_app):
        """Az eredeti `0x005fe370` a billentyűnél nem választ fület."""
        window, controller, panel, _szerk = _kezdo_allapot(
            kep_app, qt_app, _ALAPVETO_FUL
        )

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;")), (
            "a billentyű nem hatott: a fület nem váltó állítás nem bizonyít"
        )
        assert panel.property("activeTab") == _ALAPVETO_FUL

    def test_szovegmezoben_gepelve_nem_sul_el(self, kep_app, qt_app):
        window, controller, _panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        felirat: QObject = item(window, "captionField")
        QMetaObject.invokeMethod(
            felirat, "forceActiveFocus", Qt.ConnectionType.DirectConnection
        )
        qt_app.processEvents()
        fokusz = window.activeFocusItem()
        assert fokusz is not None and fokusz.property("selectedText") is not None, (
            "a próba feltétele: szövegmezőn áll a fókusz"
        )

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert szures(controller, 0) == "", (
            "szövegmezőben gépeléskor a Ctrl+Shift+B a láncra tett"
        )
        # pozitív kontroll: a fókusz elengedése után ugyanaz a billentyű hat
        QMetaObject.invokeMethod(
            item(window, "photoViewer"),
            "forceActiveFocus",
            Qt.ConnectionType.DirectConnection,
        )
        qt_app.processEvents()
        _billentyu(window, qt_app, Qt.Key.Key_B)
        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;")), (
            "szövegmező nélkül sem hatott a billentyű: az előző állítás üres"
        )

    def test_nyitott_kiegyenesites_alatt_nem_sul_el(self, kep_app, qt_app):
        window, controller, panel, _szerk = _kezdo_allapot(kep_app, qt_app)
        kattint(window, item(window, "editToolTilt"), qt_app)
        assert varj(qt_app, lambda: panel.property("tiltActive") is True)

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert szures(controller, 0) == ""
        # pozitív kontroll: a kiegyenesítés bezárása után ugyanaz a billentyű hat
        panel.setProperty("tiltActive", False)
        qt_app.processEvents()
        _billentyu(window, qt_app, Qt.Key.Key_B)
        assert varj(qt_app, lambda: szures(controller, 0).endswith("bw=1;")), (
            "a kiegyenesítés nélkül sem hatott a billentyű: az előző állítás üres"
        )

    def test_a_konyvtarban_valtozatlanul_a_kijeloltekre_kerul(self, kep_app, qt_app):
        window, controller, _engine = kep_app
        elokeszit(window, qt_app, controller)
        kijelol(window, qt_app, [0, 1])
        assert window.property("viewerOpen") is not True

        _billentyu(window, qt_app, Qt.Key.Key_B)

        assert varj(
            qt_app,
            lambda: all(szures(controller, s).endswith("bw=1;") for s in (0, 1)),
        ), "a könyvtári Ctrl+Shift+B nem írta a kijelölt képek láncába a B&W-t"
        assert szures(controller, 2) == ""
