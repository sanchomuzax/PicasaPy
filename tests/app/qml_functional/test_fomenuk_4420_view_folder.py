"""#4433: a View ▸ Folder View csoport külön, rövid bejárása."""

from __future__ import annotations

import pytest

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _VIEW_UTVONAL_DARAB_CSOPORTONKENT,
    _bejarja_menu,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


MENU = ("View", "&View")


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_tiszta_profilbol_valodi_kattintassal_bejarja_a_mappanezetet(
    tiszta_menuproba, qt_app, scratch_jelentes, magassag_eltolas
):
    _bejarja_menu(
        tiszta_menuproba,
        qt_app,
        scratch_jelentes,
        *MENU,
        magassag_eltolas=magassag_eltolas,
        felirat_elso="Folder View",
        vart_darabszam=_VIEW_UTVONAL_DARAB_CSOPORTONKENT["mappanezet"],
    )
