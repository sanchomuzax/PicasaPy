"""#4433: a Tools menü bejárása a rövidebb ablakváltozattal."""

from __future__ import annotations

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _TOOLS_UTVONAL_DARAB_CSOPORTONKENT,
    _bejarja_menu,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


MENU = ("Tools", "&Tools")


def test_tiszta_profilbol_valodi_kattintassal_bejarja_a_menut(
    tiszta_menuproba, qt_app, scratch_jelentes
):
    _bejarja_menu(
        tiszta_menuproba,
        qt_app,
        scratch_jelentes,
        *MENU,
        magassag_eltolas=-5,
        parancsnev_kizaro_prefix="menuLanguage",
        vart_darabszam=_TOOLS_UTVONAL_DARAB_CSOPORTONKENT["egyeb"],
    )
