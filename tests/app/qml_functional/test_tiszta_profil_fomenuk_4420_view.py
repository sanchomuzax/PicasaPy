"""#4420: a View parancs valódi kattintása ablakméret-eltéréssel."""

from __future__ import annotations

from pathlib import Path

import pytest

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _ABLAK_ALAPMAGASSAG,
    _ABLAKMAGASSAG_ELTOLASOK,
    _UTAK,
    _akcio,
    _megnyit,
    _parancsok,
    _varj,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


@pytest.mark.parametrize("eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_valodi_menukattintas_ablakmagassag_elteressel(
    tiszta_menuproba, qt_app, eltolas, scratch_jelentes
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    ablak.setHeight(_ABLAK_ALAPMAGASSAG + eltolas)
    assert _varj(
        qt_app, lambda: ablak.height() == _ABLAK_ALAPMAGASSAG + eltolas
    ), f"az ablak magassága nem állt be a kért {eltolas} px eltérésre"
    menu_bar = ablak.property("menuBar")
    assert menu_bar is not None, "a főablak felső menüsora hiányzik"
    menu = _megnyit(menu_bar, qt_app, "View")
    parancs = next(
        parancs
        for parancs in _parancsok(menu, menu_bar)
        if parancs["nev"] == "menuViewProperties"
    )
    eredmeny = _akcio(
        ablak,
        vezerlo,
        tmp_path / "kepek",
        menu_bar,
        qt_app,
        "View",
        parancs,
        tmp_path / "kepernyokepek",
        kulsok,
    )
    _UTAK.append(
        {"menu": "View", "magassag": eltolas, "eredmenyek": [eredmeny]}
    )
    assert not eredmeny["hiba"], (
        f"az ablakmagasság-eltolásos valódi kattintás hibázott: {eredmeny}"
    )
    assert Path(str(eredmeny["kep"])).is_file()
