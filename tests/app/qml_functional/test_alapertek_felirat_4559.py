"""#4559 — a Színátmenet (`dir_tint`) Feather alapértéke 0,25 és a Fókuszos FF
(`radsat`) csúszkája „Méret" (Size) néven szerepel, az eredeti szerint.

Spec: `docs/specs/filterdesc-registry.md:160` — `dir_tint` `0=Feather [0..1]
d=0.25`, `1=Shade [0..1] d=0.25`; `radsat` `0=Size [-1..1]`. A magyar
feliratok a referencia-tábla szerint: `filter_dir_tint_label1` → „Lágy
perem", `filter_radsat_label1` → „Méret".

A próba VALÓDI egérkattintással nyitja meg az effekt csempéjét, a csúszkák
feliratát és alapértékét a kirajzolt panelből olvassa, és a kirajzolt
nézőképet is elmenti. Az ablakot −5 / 0 / +5 px magassággal ismétli.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_editor_panel_rendered_651 import _child
from tests.app.qml_functional.test_effect_sliders import _as_list

#: (effekt, csempe objectName, a csúszka indexe, felirat-index, várt alap,
#:  várt magyar felirat)
_ALAPERTEKEK = [
    pytest.param(
        "dir_tint", "effectDirTint", 2, 2, 0.25, "Lágy perem",
        id="dir_tint_feather",
    ),
    pytest.param(
        "radsat", "effectRadsat", 2, 2, 0.0, "Méret",
        id="radsat_meret",
    ),
]

_MAGASSAG_ELTERESEK = (-5, 0, 5)


@pytest.fixture
def hu_app(qt_app, tmp_path):
    """Teljes app a magyar fordítással — a feliratot a `.qm`-ből kérjük."""
    import picasapy.app.application as app_module
    from PySide6.QtCore import QTranslator

    translator = QTranslator(qt_app)
    assert translator.load(
        str(app_module._APP_DIR / "i18n" / "picasapy_hu.qm")
    ), "a picasapy_hu.qm nem tölthető be"
    qt_app.installTranslator(translator)
    try:
        yield from _build_qml_app(qt_app, tmp_path)
    finally:
        qt_app.removeTranslator(translator)


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 5.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(uzenet)


def _nyisd_meg_az_effektet(ablak, panel, qt_app, csempe: str, kulcs: str):
    ablak.setProperty("viewerOpen", True)
    nezo = ablak.findChild(QObject, "photoViewer")
    assert nezo is not None
    nezo.setProperty("currentIndex", 0)
    panel.setProperty("activeTab", 2)
    _varj(
        qt_app,
        lambda: panel.property("activeTab") == 2,
        "az effektfül nem váltott át",
    )
    gomb = ablak.findChild(QObject, csempe)
    assert gomb is not None, f"a {kulcs} effekt csempéje hiányzik"
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        gomb.mapToScene(gomb.boundingRect().center()).toPoint(),
    )
    _varj(
        qt_app,
        lambda: panel.property("paramPanelActive") is True,
        f"a {kulcs} paraméterpanelje nem nyílt meg",
    )
    assert panel.property("paramEffectName") == kulcs


@pytest.mark.parametrize("kulcs,csempe,csuszka,felirat,alap,felirat_szoveg", _ALAPERTEKEK)
def test_alapertek_es_felirat_az_eredeti_szerint(
    hu_app,
    qt_app,
    tmp_path,
    kulcs,
    csempe,
    csuszka,
    felirat,
    alap,
    felirat_szoveg,
):
    ablak, _vezerlo, _engine = hu_app
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    _nyisd_meg_az_effektet(ablak, panel, qt_app, csempe, kulcs)

    eredeti_magassag = ablak.height()
    for elteres in _MAGASSAG_ELTERESEK:
        ablak.resize(ablak.width(), eredeti_magassag + elteres)
        _varj(
            qt_app,
            lambda cel=eredeti_magassag + elteres: ablak.height() == cel,
            "az ablak nem vette fel a kért magasságot",
        )
        csuszka_elem = _child(panel, f"effectParamSlider{csuszka}")
        felirat_elem = _child(panel, f"effectParamLabel{felirat}")
        assert felirat_elem.property("text") == felirat_szoveg
        assert csuszka_elem.property("value") == pytest.approx(alap)
        assert _as_list(panel.property("paramEffectValues"))[csuszka] == pytest.approx(alap)

        kep = ablak.grabWindow()
        assert not kep.isNull(), "a néző képe nem rajzolódott ki"
        assert kep.save(str(tmp_path / f"alap-{kulcs}-{elteres}.png"))


@pytest.mark.parametrize("kulcs,csempe,csuszka,felirat,alap,felirat_szoveg", _ALAPERTEKEK)
def test_alapertek_kerul_a_lancba(
    hu_app,
    qt_app,
    tmp_path,
    kulcs,
    csempe,
    csuszka,
    felirat,
    alap,
    felirat_szoveg,
):
    """Az alapértékkel alkalmazott effekt a `.picasa.ini` láncába is az
    alapértéket írja (dir_tint: a Feather 0,25 a harmadik paraméter)."""
    ablak, _vezerlo, _engine = hu_app
    panel = ablak.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    _nyisd_meg_az_effektet(ablak, panel, qt_app, csempe, kulcs)

    gomb = _child(panel, "effectParamApplyButton")
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        gomb.mapToScene(gomb.boundingRect().center()).toPoint(),
    )
    qt_app.processEvents()
    ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
    if kulcs == "dir_tint":
        assert "filters=dir_tint=1,0.500000,0.500000,0.250000,0.250000,ffffffff;" in ini
    else:
        assert "radsat=1,0.500000,0.500000,0.000000,0.500000;" in ini
