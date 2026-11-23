"""#7410: a Ragyogás (Glow) effekt Radius csúszkája 3,0 alapértékkel nyíljon."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from support.qt_wait import varj_feltetelre

from picasapy.app.effect_params import effect_params


def _walk(item):
    if hasattr(item, "childItems"):
        for child in item.childItems():
            yield child
            yield from _walk(child)


def _child(root, name: str):
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _kattint(obj) -> None:
    assert obj is not None
    QMetaObject.invokeMethod(obj, "buttonClicked", Qt.ConnectionType.DirectConnection)


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_glow2_defaults_apply_cancel_reopen(
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
    panel.setProperty("activeTab", 2)  # 1. effektfül (Effects)
    qt_app.processEvents()

    def glow_values():
        return list(_lista(panel.property("paramEffectValues")) or [])

    def open_glow():
        gomb = panel.findChild(QObject, "effectGlow2")
        assert gomb is not None, "az effectGlow2 gomb nem található"
        _kattint(gomb)
        assert varj_feltetelre(
            qt_app,
            lambda: bool(panel.property("paramPanelActive"))
            and len(glow_values()) == 2,
            3.0,
        ), "a Glow panel nem nyílt meg két paraméterrel"
        assert panel.property("paramEffectName") == "glow2"
        # 1. Kritérium: A Ragyogás panel megnyitásakor a Radius csúszka a 3.0 értéken áll.
        assert glow_values() == pytest.approx([0.65, 3.0])
        slider1 = _child(panel, "effectParamSlider1")
        assert slider1 is not None, "a Radius csúszka nem található"
        assert float(slider1.property("value")) == pytest.approx(3.0)

    # 1. Nyitás: ellenőrizzük az alapértéket (3.0)
    open_glow()

    # 2. Mégse: zárjuk be a panelt
    cancel_btn = panel.findChild(QObject, "effectParamCancelButton")
    assert cancel_btn is not None
    _kattint(cancel_btn)
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "a Mégse nem zárta be a panelt"

    # 3. Kritérium: Mégse utáni újranyitáskor is a 3.0 érték áll be.
    open_glow()

    # 4. Kritérium: Változtatás nélküli Alkalmazáskor a mentett láncban glow2=1,0.650000,3.000000; jelenik meg.
    apply_btn = panel.findChild(QObject, "effectParamApplyButton")
    assert apply_btn is not None
    _kattint(apply_btn)
    assert varj_feltetelre(
        qt_app, lambda: not panel.property("paramPanelActive"), 3.0
    ), "az Alkalmaz nem zárta be a panelt"

    ini_path = tmp_path / "kepek" / ".picasa.ini"
    assert ini_path.exists(), "a .picasa.ini nem jött létre"
    ini = ini_path.read_text(encoding="utf-8")
    assert "glow2=1,0.650000,3.000000;" in ini


def test_glow_catalogue_defaults_parity():
    """A katalógusban a glow és glow2 Radius alapértéke 3.0."""
    g2 = {p.key: p for p in effect_params("glow2")}
    assert g2["radius"].default == pytest.approx(3.0)
    assert g2["radius"].minimum == pytest.approx(0.0)
    assert g2["radius"].maximum == pytest.approx(100.0)

    g = {p.key: p for p in effect_params("glow")}
    assert g["radius"].default == pytest.approx(3.0)
