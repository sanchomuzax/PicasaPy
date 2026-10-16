"""#4433: a Edit menü önálló, tiszta profilú bejárása."""

from __future__ import annotations

import pytest

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _akcio,
    _bejarja_menu,
    _elero_menu,
    _megnyit,
    _parancsok,
    _varj,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


MENU = ('Edit', '&Edit')


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_tiszta_profilbol_valodi_kattintassal_bejarja_a_menut(
    tiszta_menuproba, qt_app, scratch_jelentes, magassag_eltolas
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu_bar = ablak.property("menuBar")
    picture_menu = _megnyit(menu_bar, qt_app, "&Picture")
    batch_effect = next(
        parancs
        for parancs in _parancsok(picture_menu, menu_bar)
        if parancs["nev"] == "menuBatchAutoContrast"
    )
    elokeszito = _akcio(
        ablak,
        vezerlo,
        tmp_path / "kepek",
        menu_bar,
        qt_app,
        "Picture",
        batch_effect,
        tmp_path / "kepernyokepek",
        kulsok,
    )
    assert not elokeszito["hiba"], (
        "a korábbi menüsorrend szükséges Batch Edit előfeltétele nem állt elő: "
        f"{elokeszito}"
    )
    assert vezerlo.waitForBackgroundWorkers(3.0), (
        "az Auto Contrast előfeltétel háttérmunkája nem fejeződött be"
    )
    edit_menu = _megnyit(menu_bar, qt_app, "&Edit")
    undo_batch = next(
        parancs
        for parancs in _parancsok(edit_menu, menu_bar)
        if parancs["nev"] == "menuEditUndoBatchEdit"
    )
    undo_item = _elero_menu(menu_bar, qt_app, "&Edit", undo_batch["utvonal"])
    assert _varj(qt_app, lambda: undo_item.property("enabled") is True), (
        "a Batch Edit előfeltétel háttérmunkája nem tette elérhetővé a visszavonást"
    )
    _bejarja_menu(
        tiszta_menuproba,
        qt_app,
        scratch_jelentes,
        *MENU,
        magassag_eltolas=magassag_eltolas,
    )
