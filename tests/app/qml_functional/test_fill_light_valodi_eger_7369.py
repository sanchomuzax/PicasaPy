"""#7369: a két Derítőfény-csúszka VALÓDI egérrel, két különálló rétegen.

Az eredeti Picasa az 1. fülre lépéskor a `fill`, a 2. fülre (Hangolás)
lépéskor a `finetune2` szűrőt aktiválja (`0x005d7780`). A Gyakori javítások
csúszkája ezért a `fill=1,<érték>` réteget szerkeszti, a Hangolás csúszkája a
`finetune2` 1. paraméterét; a két csúszka NEM osztozik állapoton.

A próbák a ténylegesen kirajzolt vezérlőt használják: egéreseményt küldenek az
ablaknak (nem a kontroller metódusát hívják), és a láncot, a másik fül
csúszkáját meg a Visszavonás-gomb kirajzolt szövegét olvassák vissza.

Rontás-kontroll: ha a Gyakori javítások csúszka vissza kerül a `finetune2`
rétegre (`panel.emitFinetuneCommit()`), a `fill=` sor eltűnik a láncból, és az
első két próba elbukik.
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


@pytest.fixture
def _magyar_forditas(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), "a hu .qm nem tölthető be"
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _kepek_fill_sorral(lib: Path) -> None:
    """Két négyzetes kép; az `a.jpg`-hoz eredeti Picasa-szerű `fill` sor tartozik."""
    make_jpeg(lib / "a.jpg", size=(600, 600))
    make_jpeg(lib / "b.jpg", size=(600, 600))
    (lib / ".picasa.ini").write_text(
        "[a.jpg]\nfilters=fill=1,0.5;\n", encoding="utf-8"
    )


@pytest.fixture
def app_fill_sorral(qt_app, tmp_path):
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_fill_sorral)


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


def _pont(slider, arany: float) -> QPointF:
    return slider.mapToScene(
        QPointF(
            float(slider.property("width")) * arany,
            float(slider.property("height")) / 2,
        )
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


def _ful(panel, qt_app, index: int) -> None:
    panel.setProperty("activeTab", index)
    qt_app.processEvents()


def _visszavonas_felirat(window) -> str:
    return str(_item(window, "editUndoButtonLabel").property("text"))


def _ertek(slider) -> float:
    return float(slider.property("value"))


class TestGyakoriJavitasokCsuszka:
    def test_a_huzas_fill_reteget_ir_finetune2_nelkul(self, qml_app_negyzet_kepek, qt_app):
        window, panel, edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        fixes = _item(window, "fixesFillSlider")

        _huzas(window, fixes, qt_app, 0.2, 0.8)

        lanc = str(edit.property("chainValue"))
        assert _ertek(fixes) > 0.5, "a valódi húzás nem mozgatta a csúszkát"
        assert "fill=1," in lanc, lanc
        assert "finetune2" not in lanc, lanc
        assert float(lanc.split("fill=1,")[1].split(";")[0]) == pytest.approx(
            _ertek(fixes), abs=1e-5
        )

    def test_a_hangolas_csuszka_0_marad(self, qml_app_negyzet_kepek, qt_app):
        window, panel, _edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.2, 0.8)

        _ful(panel, qt_app, 1)

        assert _ertek(_item(window, "finetuneFillSlider")) == pytest.approx(0.0)

    def test_a_visszavonas_felirat_derítofeny(
        self, _magyar_forditas, qml_app_negyzet_kepek, qt_app
    ):
        window, _panel, _edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _huzas(window, _item(window, "fixesFillSlider"), qt_app, 0.2, 0.8)
        assert _visszavonas_felirat(window) == "Visszavonás: Derítőfény"

    def test_a_ketszeri_huzas_egyetlen_fill_reteg(self, qml_app_negyzet_kepek, qt_app):
        window, _panel, edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        fixes = _item(window, "fixesFillSlider")
        _huzas(window, fixes, qt_app, 0.2, 0.8)
        _huzas(window, fixes, qt_app, 0.8, 0.4)
        assert str(edit.property("chainValue")).count("fill=") == 1


class TestHangolasCsuszka:
    def test_a_huzas_finetune2_reteget_ir_a_fill_valtozatlan(
        self, app_fill_sorral, qt_app
    ):
        window, panel, edit = _megnyit(app_fill_sorral, qt_app)
        elotte = str(edit.property("chainValue"))
        assert "fill=1,0.5" in elotte, elotte

        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneFillSlider"), qt_app, 0.2, 0.7)

        lanc = str(edit.property("chainValue"))
        assert "finetune2=1," in lanc, lanc
        assert "fill=1,0.5" in lanc, lanc
        assert lanc.count("fill=1,") == 1, lanc

    def test_a_visszavonas_felirat_finomhangolas(
        self, _magyar_forditas, qml_app_negyzet_kepek, qt_app
    ):
        window, panel, _edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneFillSlider"), qt_app, 0.2, 0.7)
        assert _visszavonas_felirat(window) == "Visszavonás: Finomhangolás"

    def test_a_gyakori_javitasok_csuszka_nem_koveti_a_hangolast(
        self, qml_app_negyzet_kepek, qt_app
    ):
        window, panel, _edit = _megnyit(qml_app_negyzet_kepek, qt_app)
        _ful(panel, qt_app, 1)
        _huzas(window, _item(window, "finetuneFillSlider"), qt_app, 0.2, 0.7)

        _ful(panel, qt_app, 0)

        assert _ertek(_item(window, "fixesFillSlider")) == pytest.approx(0.0)


class TestMeglevoFillSor:
    def test_a_megnyitaskor_a_csuszka_alaphelyzetben_all_a_kep_korrigalt(
        self, app_fill_sorral, qt_app
    ):
        """#7383 (J2b): `fill=1,0.5` mellett a kép a láncot mutatja, a csúszka
        mindkét fülön a bal szélen áll."""
        window, panel, edit = _megnyit(app_fill_sorral, qt_app)
        assert "fill=1,0.5" in str(edit.property("chainValue"))
        assert _ertek(_item(window, "fixesFillSlider")) == pytest.approx(0.0)
        _ful(panel, qt_app, 1)
        assert _ertek(_item(window, "finetuneFillSlider")) == pytest.approx(0.0)
