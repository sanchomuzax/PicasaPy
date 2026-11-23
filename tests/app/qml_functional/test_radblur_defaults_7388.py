"""#7388: a Soft Focus csúszkái a natív középértéken nyíljanak meg."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from support.qt_wait import varj_feltetelre

from picasapy.app.effect_params import effect_params


def _kattint(obj) -> None:
    assert obj is not None
    QMetaObject.invokeMethod(obj, "buttonClicked", Qt.ConnectionType.DirectConnection)


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _kepernyokep(window, environment_key: str, height_delta: int) -> None:
    cel = os.environ.get(environment_key)
    if not cel or height_delta != 0:
        return
    fajl = Path(cel).resolve()
    tmp = Path(__file__).resolve().parents[3] / ".tmp"
    assert fajl.is_relative_to(tmp.resolve()), "a képernyőkép csak a munkafa .tmp mappájába írható"
    fajl.parent.mkdir(parents=True, exist_ok=True)
    kep = window.grabWindow()
    assert not kep.isNull(), "nem készült PicasaPy-képkocka"
    assert kep.save(str(fajl), "PNG"), f"nem menthető a képkocka: {fajl}"


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_soft_focus_defaults_apply_cancel_reopen_and_neighbor_positions(
    qml_app, qt_app, tmp_path, height_delta
):
    window, _controller, _engine = qml_app
    eredeti_magassag = int(window.height())
    cel_magassag = eredeti_magassag + height_delta
    window.setHeight(cel_magassag)
    assert varj_feltetelre(
        qt_app, lambda: int(window.height()) == cel_magassag, 3.0
    ), "az ablakmagasság nem állt be"

    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    assert viewer is not None
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    panel = window.findChild(QObject, "viewerEditorPanel")
    assert panel is not None
    panel.setProperty("activeTab", 2)
    qt_app.processEvents()

    def soft_focus_values():
        return list(_lista(panel.property("paramEffectValues")) or [])

    def open_soft_focus():
        _kattint(panel.findChild(QObject, "effectRadblur"))
        assert varj_feltetelre(
            qt_app,
            lambda: bool(panel.property("paramPanelActive"))
            and len(soft_focus_values()) == 4,
            3.0,
        ), "a Soft Focus panel nem nyílt meg négy paraméterrel"
        assert panel.property("paramEffectName") == "radblur"
        assert soft_focus_values() == pytest.approx([0.5, 0.5, 0.0, 0.0])

    open_soft_focus()
    _kepernyokep(window, "PICASAPY_7388_SOFTFOCUS_SCREENSHOT", height_delta)
    _kattint(panel.findChild(QObject, "effectParamCancelButton"))
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "a Mégse nem zárta be a panelt"

    # A Mégse után is az eredeti alapértékeknek kell újra megjelenniük.
    open_soft_focus()
    _kattint(panel.findChild(QObject, "effectParamApplyButton"))
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "az Alkalmaz nem zárta be a panelt"
    ini = (tmp_path / "kepek" / ".picasa.ini").read_text(encoding="utf-8")
    assert "radblur=1,0.500000,0.500000,0.000000,0.000000;" in ini

    open_soft_focus()
    _kattint(panel.findChild(QObject, "effectParamCancelButton"))
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "a panel nem zárult be"

    # #3826: a Focal B&W mérete továbbra is 0; a két korábban mért szomszéd
    # csúszka 20%-os helye (Sharpen 0,6/3; Film Grain 10/50) sem változik.
    radsat = {param.key: param for param in effect_params("radsat")}
    assert radsat["radius"].default == 0.0

    panel.setProperty("activeTab", 2)
    qt_app.processEvents()
    _kattint(panel.findChild(QObject, "effectUnsharp"))
    assert varj_feltetelre(
        qt_app, lambda: bool(panel.property("paramPanelActive")), 3.0
    ), "a Sharpen panel nem nyílt meg"
    assert panel.property("paramEffectName") == "unsharp2"
    assert _lista(panel.property("paramEffectValues")) == pytest.approx([0.6])
    _kepernyokep(window, "PICASAPY_7388_SHARPEN_SCREENSHOT", height_delta)
    _kattint(panel.findChild(QObject, "effectParamCancelButton"))
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "a Sharpen panel nem zárult be"

    panel.setProperty("activeTab", 4)
    qt_app.processEvents()
    _kattint(panel.findChild(QObject, "effectPicnikGrain"))
    assert varj_feltetelre(
        qt_app, lambda: bool(panel.property("paramPanelActive")), 3.0
    ), "a Film Grain panel nem nyílt meg"
    assert panel.property("paramEffectName") == "picnikgrain"
    assert _lista(panel.property("paramEffectValues")) == pytest.approx([10.0, 0.0])
    _kepernyokep(window, "PICASAPY_7388_GRAIN_SCREENSHOT", height_delta)
    _kattint(panel.findChild(QObject, "effectParamCancelButton"))

