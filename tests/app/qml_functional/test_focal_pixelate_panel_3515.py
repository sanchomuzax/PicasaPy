"""#3515 — a Képpontnövelés (`PicnikFocalPixelate`) csúszkapanelt nyit.

A `Pixelate` csempe Shift-párja a #3315 óta renderel, de a katalógusban
(`effect_params._CATALOGUE`) nem volt bejegyzése, ezért az
`effectHasParams()` hamisat adott: a hatás a beégetett alapértékekkel
azonnal a képre került, panel nélkül.

A vezérlők forrása a `filterdesc.xml:865–869` (ld.
`docs/specs/filterdesc-registry.md` 4.1/c): puck (x, y), `Impact` 2–100
(20), `Radius` 10–min(W,H)/2 (a tartomány közepe), `Hardness` 0–100 (50),
`Fade` 0–100 (0), `Reverse` jelölő (ki). A feliratok a bináris szűrőnkénti
felülírásából (`docs/specs/picasa-effekt-feliratok.md`): `_sldrImpact` →
„Pixel Size", `_sldrRadius` → „Focal Size", `_sldrHardness` → „Edge
Hardness", `_chkReverse` → „Reverse".

A próbák a panel TÉNYLEGES megnyílását nézik (valódi QML-motor, Shift-állás,
csempe-kattintás), és azt, hogy a Megfordítás jelölő a képen is megfordítja
a hatást.
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from picasapy.app.effect_params import (
    effect_params,
    format_param_values,
    resolve_effect_params,
)
from picasapy.ini import parse_filters
from picasapy.render import apply_filters
from tests.app.qml_functional.test_editor_panel_rendered_651 import _child
from tests.app.qml_functional.test_effect_sliders import (
    _as_list,
    _click,
    _FakeEditController,
    _make_panel,
    qml_engine,  # noqa: F401 — pytest-fixture
)

KULCS = "picnikfocalpixelate"
#: a `EditorEffectsTab3.qml` a panel 4-es `activeTab`-ja
FUL = 4


def _shift_csempe(panel, qt_app):
    """Shift lenyomva → a `Pixelate` csempe a másodlagost adja."""
    panel.setProperty("shiftMasodlagos", True)
    qt_app.processEvents()
    csempe = panel.findChild(QObject, "effectPixelate")
    assert csempe is not None
    assert csempe.property("szuro") == KULCS
    return csempe


class TestAKatalogus:
    def test_a_vezerlok_a_merte_feliratokkal_es_sorrendben(self):
        vezerlok = effect_params(KULCS)
        assert [(p.key, p.label, p.kind) for p in vezerlok] == [
            ("x", "Center X", "slider"),
            ("y", "Center Y", "slider"),
            ("impact", "Impact", "slider"),
            ("radius", "Radius", "slider"),
            ("hardness", "Edge Hardness", "slider"),
            ("fade", "Fade", "slider"),
            ("reverse", "Reverse", "checkbox"),
        ]

    def test_a_tartomanyok_a_filterdescbol(self):
        # 320 × 160-as kép: a Radius 10 … 80, alapja a közép (45)
        p = {v.key: v for v in resolve_effect_params(KULCS, 320, 160)}
        assert (p["impact"].minimum, p["impact"].maximum, p["impact"].default) == (2, 100, 20)
        assert (p["radius"].minimum, p["radius"].maximum, p["radius"].default) == (10, 80, 45)
        assert (p["hardness"].minimum, p["hardness"].maximum, p["hardness"].default) == (0, 100, 50)
        assert (p["fade"].minimum, p["fade"].maximum, p["fade"].default) == (0, 100, 0)
        assert p["reverse"].default == 0.0


class TestAPanelMegnyilik:
    def test_shift_kattintas_panelt_nyit_elo_elonezettel(self, qml_engine, qt_app):  # noqa: F811
        vezerlo = _FakeEditController()
        panel = _make_panel(qml_engine, vezerlo, active_tab=FUL)
        qt_app.processEvents()
        keresett = []
        panel.effectRequested.connect(lambda nev: keresett.append(nev))

        _click(_shift_csempe(panel, qt_app))
        qt_app.processEvents()

        assert panel.property("paramPanelActive") is True, (
            "a Képpontnövelés panel nélkül került a képre"
        )
        assert keresett == [], "a hatás panel helyett azonnal alkalmazódott"
        assert panel.property("paramEffectName") == KULCS
        ismetlo = panel.findChild(QObject, "effectParamRepeater")
        assert ismetlo.property("count") == 7
        feliratok = [p["label"] for p in _as_list(panel.property("paramEffectParams"))]
        assert feliratok[2:] == [
            "Impact", "Radius", "Edge Hardness", "Fade", "Reverse",
        ]
        # élő előnézet: a megnyitás az alapértékekkel rögtön renderel
        assert vezerlo.preview_calls and vezerlo.preview_calls[-1][0] == KULCS


class TestALancig:
    def test_a_megforditas_jelolo_a_lancba_kerul(self, qml_app, qt_app, tmp_path):
        window, _controller, _engine = qml_app
        window.setProperty("viewerOpen", True)
        window.findChild(QObject, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", FUL)
        qt_app.processEvents()

        _click(_shift_csempe(panel, qt_app))
        qt_app.processEvents()
        assert panel.property("paramPanelActive") is True

        # a Megfordítás jelölőre KATTINTUNK, nem a metódust hívjuk
        jelolo = _child(panel, "effectParamCheckbox6")
        assert jelolo.isVisible(), "a Megfordítás jelölő nem látszik a panelen"
        # valódi egérkattintás a jelölő közepére (a CheckBox-nak nincs
        # `buttonClicked` metódusa, a `toggled` csak felhasználói kattintásra jön)
        kozep = jelolo.mapToScene(jelolo.boundingRect().center()).toPoint()
        QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, kozep)
        qt_app.processEvents()
        assert jelolo.property("checked") is True
        _click(panel.findChild(QObject, "effectParamApplyButton"))
        qt_app.processEvents()

        ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
        # a Radius a `.picasa.ini`-ben SZÁZALÉK (#3596): a közép = 50
        assert (
            "PicnikFocalPixelate=1,0.500000,0.500000,20.000000,50.000000,"
            "50.000000,0.000000,1;"
        ) in ini


def _minta():
    rng = np.random.default_rng(3515)
    return rng.integers(0, 256, size=(120, 160, 3), dtype=np.uint8)


def _render(kep, megforditva):
    vezerlok = resolve_effect_params(KULCS, kep.shape[1], kep.shape[0])
    ertekek = [v.default for v in vezerlok]
    ertekek[-1] = 1.0 if megforditva else 0.0
    lanc = f"PicnikFocalPixelate=1,{','.join(format_param_values(ertekek, vezerlok))};"
    return apply_filters(kep, parse_filters(lanc)).image


@pytest.mark.parametrize("megforditva", [False, True])
def test_a_megforditas_a_kepen_is_megfordit(megforditva):
    kep = _minta()
    kimenet = _render(kep, megforditva)
    kozep = (slice(55, 65), slice(75, 85))
    sarok = (slice(0, 10), slice(0, 10))
    kozep_ep = np.array_equal(kimenet[kozep], kep[kozep])
    sarok_ep = np.array_equal(kimenet[sarok], kep[sarok])
    # alaphelyzetben a kör KÖZEPE éles, a széle pixeles; fordítva épp fordítva
    assert (kozep_ep, sarok_ep) == ((False, True) if megforditva else (True, False))
