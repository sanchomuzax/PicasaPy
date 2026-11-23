"""#7383: a Hangolás fül csúszkái alaphelyzetben indulnak, a látogatás EGY lépés.

Az eredeti Picasa felvételei (J2a/J2b, J3b, J3d, J4a, J6c):

- a csúszkák belépéskor, megnyitáskor és Undo/Redo után mindig a bal szélen
  állnak (a Színhőmérséklet a közepén), a kép viszont a láncot mutatja,
- hat húzás négy csúszkán után EGY Undo mindent visszaállít, az Undo tiltott,
  az Újra a lépés nevét viseli,
- a betöltött `finetune2` mellé az első húzás új réteget fűz (két sor).

A próbák a kirajzolt vezérlőt használják: valódi egéreseményt küldenek az
ablaknak (nem a kontroller metódusát hívják), a láncot, a csúszkák állását és
a Visszavonás/Újra gombok állapotát a kirajzolt elemekről olvassák vissza.

Rontás-kontroll: ha a `syncFinetuneSliders` ismét a mentett értékekre állítaná
a csúszkákat (a régi viselkedés), az alaphelyzetet ellenőrző próbák elbuknak.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QPointF, Qt, QTranslator
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.varakozas import var_feltetelre

_I18N_DIR = Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "i18n"
_LANC = "fill=1,0.5;finetune2=1,0.3,0,0,ffccc6b2,0.2;"


@pytest.fixture
def _magyar_forditas(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), "a hu .qm nem tölthető be"
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _kepek_betoltott_lanccal(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(600, 600))
    make_jpeg(lib / "b.jpg", size=(600, 600))
    (lib / ".picasa.ini").write_text(f"[a.jpg]\nfilters={_LANC}\n", encoding="utf-8")


@pytest.fixture
def app_betoltott_lanccal(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_betoltott_lanccal)


def _item(window, name: str):
    item = window.findChild(QObject, name)
    assert item is not None, f"{name} nem található a főablakban"
    return item


def _megnyit(app, qt_app):
    window, _controller, engine = app
    window.setProperty("width", 1280)
    window.setProperty("height", 1005)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    assert var_feltetelre(
        qt_app,
        lambda: _item(window, "viewerEditorPanel").property("visible") is True,
        10.0,
    ), "a szerkesztőpanel nem nyílt meg"
    assert not window.grabWindow().isNull(), "a főablak nem rajzolódott ki"
    edit = engine.rootContext().contextProperty("editController")
    return window, _item(window, "viewerEditorPanel"), edit


def _pont(item, arany: float) -> QPointF:
    return item.mapToScene(
        QPointF(float(item.property("width")) * arany, float(item.property("height")) / 2)
    )


def _huzas(window, slider, qt_app, honnan: float, hova: float) -> None:
    """Valódi egérhúzás: lenyomás, mozgatás, elengedés (az elengedés ment)."""
    assert slider.property("visible") is True, f"{slider.objectName()} nem látható"
    kezd = _pont(slider, honnan).toPoint()
    veg = _pont(slider, hova).toPoint()
    QTest.mousePress(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kezd)
    qt_app.processEvents()
    QTest.mouseMove(window, veg)
    qt_app.processEvents()
    QTest.mouseRelease(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, veg)
    qt_app.processEvents()


def _kattint(window, gomb, qt_app) -> None:
    pont = _pont(gomb, 0.5).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _ful(panel, qt_app, index: int) -> None:
    panel.setProperty("activeTab", index)
    qt_app.processEvents()


def _ertek(window, nev: str) -> float:
    return float(_item(window, nev).property("value"))


def _finetune_sorok(edit) -> list[list[str]]:
    return [
        elem.split("=", 1)[1].split(",")
        for elem in str(edit.property("chainValue")).split(";")
        if elem.startswith("finetune2=")
    ]


_HANGOLAS = (
    "finetuneFillSlider",
    "finetuneHighlightsSlider",
    "finetuneShadowsSlider",
    "finetuneTempSlider",
)


def _mind_alaphelyzetben(window) -> None:
    for nev in (*_HANGOLAS, "fixesFillSlider"):
        assert _ertek(window, nev) == pytest.approx(0.0, abs=1e-6), nev


class TestAlaphelyzet:
    def test_megnyitaskor_mindket_fulon_alaphelyzet_a_kep_a_lancot_mutatja(
        self, app_betoltott_lanccal, qt_app
    ):
        """J2a 28., 30. és J2b 14., 16. kép: `fill` és `finetune2` a láncban,
        a csúszkák mégis a bal szélen (a Színhőmérséklet a közepén)."""
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        lanc = str(edit.property("chainValue"))
        assert "fill=1,0.5" in lanc and "finetune2=1,0.3" in lanc, lanc

        _mind_alaphelyzetben(window)
        _ful(panel, qt_app, 1)
        _mind_alaphelyzetben(window)

    def test_a_fulvaltas_huzas_nelkul_alaphelyzetben_hagyja_a_csuszkakat(
        self, app_betoltott_lanccal, qt_app
    ):
        """J3b 5. kép: elhagyott és újra belépett Hangolás fül, a Kiemelések
        0-n áll, nem a mentett értéken."""
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.8)
        assert _ertek(window, "finetuneHighlightsSlider") > 0.1

        _ful(panel, qt_app, 0)
        _ful(panel, qt_app, 1)

        _mind_alaphelyzetben(window)
        assert len(_finetune_sorok(edit)) == 2, edit.property("chainValue")

    def test_a_masik_kepre_lapozva_alaphelyzet(self, app_betoltott_lanccal, qt_app):
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.8)

        _item(window, "photoViewer").setProperty("currentIndex", 1)
        qt_app.processEvents()
        _item(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()

        _mind_alaphelyzetben(window)


def _minta(window) -> str:
    """A kirajzolt alapszín-minta korongjának színe (`#rrggbb`)."""
    return _item(window, "finetuneNeutralSwatch").property("color").name()


class TestAlapszinMinta:
    def test_a_minta_betoltott_szin_mellett_is_alaphelyzetben_all(
        self, app_betoltott_lanccal, qt_app
    ):
        """J6c 16. kép: a betöltött `ffccc6b2` mellett a minta fekete; a
        látogatás Undo-ja után sem a betöltött réteg színét veszi fel."""
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)
        assert _minta(window) == "#000000"

        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.8)
        assert _minta(window) == "#000000"
        _kattint(window, _item(window, "editUndoButton"), qt_app)

        assert _finetune_sorok(edit)[0][4] == "ffccc6b2"
        assert _minta(window) == "#000000", "az Undo után a minta a betöltött színt mutatja"

    def test_a_pipetta_szine_a_ful_elhagyasaig_latszik(
        self, app_betoltott_lanccal, qt_app
    ):
        """A látogatás pipetta-színe a mintán látszik, a fül elhagyása és az
        újra-belépés után a minta is alaphelyzetben áll (mint a csúszkák)."""
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)
        edit.applyColorWand()
        qt_app.processEvents()
        assert _minta(window) != "#000000", "a pipetta színe nem látszik a mintán"

        _ful(panel, qt_app, 0)
        _ful(panel, qt_app, 1)

        assert _minta(window) == "#000000"


class TestEgyLepes:
    def test_hat_huzas_egy_undo_az_ujra_a_lepes_nevet_viseli(
        self, _magyar_forditas, qml_app_negyzet_kepek, qt_app
    ):
        """J3d 23., 25. kép: hat húzás négy csúszkán, egy Undo mindent
        visszaállít, az Undo tiltott, az Újra a lépés nevét viseli."""
        window, panel, edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _ful(panel, qt_app, 1)

        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.5, 0.8)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.8, 0.3)
        _huzas(window, _item(window, "finetuneFillSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneTempSlider"), qt_app, 0.5, 0.8)

        assert len(_finetune_sorok(edit)) == 1, edit.property("chainValue")
        assert str(_item(window, "editUndoButtonLabel").property("text")) == (
            "Visszavonás: Finomhangolás"
        )
        # a látogatásban a csúszkák ott maradnak, ahová húztuk (J3d 23. kép)
        assert _ertek(window, "finetuneHighlightsSlider") > 0.05
        assert _ertek(window, "finetuneTempSlider") > 0.2

        _kattint(window, _item(window, "editUndoButton"), qt_app)

        assert str(edit.property("chainValue")) == ""
        assert edit.property("canUndo") is False
        assert str(_item(window, "editRedoButtonLabel").property("text")) == (
            "Újra: Finomhangolás"
        )
        _mind_alaphelyzetben(window)

    def test_negy_huzas_undo_undo_redo(self, qml_app_negyzet_kepek, qt_app):
        """J4a 19., 21., 25. kép: a Redo után a kép szerkesztett, a csúszkák
        alaphelyzetben állnak."""
        window, panel, edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneFillSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.5)
        _huzas(window, _item(window, "finetuneTempSlider"), qt_app, 0.5, 0.8)
        szerkesztett = str(edit.property("chainValue"))

        undo = _item(window, "editUndoButton")
        _kattint(window, undo, qt_app)
        _kattint(window, undo, qt_app)
        _kattint(window, _item(window, "editRedoButton"), qt_app)

        assert str(edit.property("chainValue")) == szerkesztett
        assert len(_finetune_sorok(edit)) == 1
        _mind_alaphelyzetben(window)

    def test_az_undo_a_betoltott_reteget_nem_viszi_el(self, app_betoltott_lanccal, qt_app):
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.8)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.8, 0.4)

        _kattint(window, _item(window, "editUndoButton"), qt_app)

        sorok = _finetune_sorok(edit)
        assert len(sorok) == 1, edit.property("chainValue")
        assert sorok[0][4] == "ffccc6b2"
        _mind_alaphelyzetben(window)


class TestUjReteg:
    def test_betoltott_finetune2_mellett_egy_huzas_utan_ket_sor_all(
        self, app_betoltott_lanccal, qt_app
    ):
        """J6c: a második sor p4-je `00000000`, a betöltött sor érintetlen."""
        window, panel, edit = _megnyit(app_betoltott_lanccal, qt_app)
        _ful(panel, qt_app, 1)

        _huzas(window, _item(window, "finetuneTempSlider"), qt_app, 0.5, 0.9)

        sorok = _finetune_sorok(edit)
        assert len(sorok) == 2, edit.property("chainValue")
        assert sorok[0] == ["1", "0.3", "0", "0", "ffccc6b2", "0.2"]
        assert sorok[1][4] == "00000000"
        assert float(sorok[1][5]) > 0.2

    def test_a_ful_elhagyasa_utani_huzas_uj_reteget_ad(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, panel, edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneHighlightsSlider"), qt_app, 0.1, 0.6)
        _ful(panel, qt_app, 0)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneShadowsSlider"), qt_app, 0.1, 0.6)

        assert len(_finetune_sorok(edit)) == 2, edit.property("chainValue")

    def test_az_elso_ful_fill_csuszkaja_alaphelyzetbol_indul_uj_fill_reteg_jon(
        self, app_betoltott_lanccal, qt_app
    ):
        """E27 (job-906) és #7397: a betöltött `fill` mellett a húzás ÚJ réteget
        fűz a lánc végére, a betöltött `fill=1,0.5` érintetlen marad."""
        window, _panel, edit = _megnyit(app_betoltott_lanccal, qt_app)

        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.1, 0.9)

        lanc = str(edit.property("chainValue"))
        assert lanc.count("fill=1,") == 2, lanc
        assert lanc.startswith("fill=1,0.5;"), lanc
