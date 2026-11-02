"""#4420: az Eszközök ▸ Language almenü utolsó parancsa kattintható."""

from __future__ import annotations

import pytest

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _NYELV_ALMENU_MIN_MAGASSAG,
    _akcio,
    _megnyit,
    _parancsok,
    _varj,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


@pytest.mark.parametrize("eltolas", (-5, 0, 5))
def test_a_nyelv_almenu_utolso_parancsa_is_kattinthato(
    tiszta_menuproba, qt_app, eltolas
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    nyelv_magassag = _NYELV_ALMENU_MIN_MAGASSAG + eltolas
    ablak.setHeight(nyelv_magassag)
    assert _varj(qt_app, lambda: ablak.height() == nyelv_magassag)
    menu_bar = ablak.property("menuBar")
    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    korean = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuLanguageko"
    )

    eredmeny = _akcio(
        ablak,
        vezerlo,
        tmp_path / "kepek",
        menu_bar,
        qt_app,
        "Tools",
        korean,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    assert not eredmeny["hiba"], (
        "a Language almenü utolsó parancsa nem jutott el a megerősítő "
        f"párbeszédig: {eredmeny}"
    )
    assert "menuLanguageConfirmDialog" in eredmeny["eredmeny"]
