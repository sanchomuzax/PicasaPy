"""#6861: több kijelölt képnél a Copy All Effects Info ablakot mutat."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _kattints
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


_INFO = "Please select a single picture to copy the effects from."


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=83)
    make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=84)


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        belyegkep_meret=256,
        valodi_belyegkep=True,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 5.0)


def _elem(gyoker, nev: str):
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_edit_copy_all_effects_tobb_kepnel_infoval_nem_valtoztatja_a_vagolapot(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    vart = window.height() + height_offset
    window.setHeight(vart)
    assert _varj(qt_app, lambda: window.height() == vart), (
        f"a főablak magassága nem állt be {vart} px-re"
    )
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2), (
        "a két tesztkép nem töltődött be"
    )

    # Előzetes, egyképes másolat: az elutasított kattintásnak ezt kell megőriznie.
    controller.copyAllEffects([0])
    vagolap_elotte = controller._effect_clipboard_value
    assert controller.hasAllEffectsClipboard is True
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    megnyit_fomenu(window, qt_app, "&Edit")
    tetel = _elem(window, "menuEditCopyEffects")
    assert tetel.property("visible") is True
    _kattints(qt_app, tetel)

    dialog = _elem(window, "copyAllEffectsInfoDialog")
    assert _varj(qt_app, lambda: dialog.property("visible") is True), (
        "több kijelölt képnél nem jelent meg az Info ablak"
    )
    assert dialog.property("title") == "Info"
    assert _elem(dialog, "copyAllEffectsInfoText").property("text") == _INFO
    assert controller._effect_clipboard_value == vagolap_elotte, (
        "a többképes másolás megváltoztatta a vágólapot"
    )

    if height_offset == 0:
        output_dir = os.environ.get("PICASAPY_6861_SCREENSHOT_DIR")
        if output_dir:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
            kep = window.grabWindow()
            assert not kep.isNull(), "a kiadáskép üres"
            assert kep.save(str(Path(output_dir) / "picasapy-copy-all-effects.png"))

    QMetaObject.invokeMethod(dialog, "close")
    assert _varj(qt_app, lambda: dialog.property("visible") is False)
