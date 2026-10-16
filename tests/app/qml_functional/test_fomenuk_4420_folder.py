"""#4433: a Folder menü önálló, tiszta profilú bejárása."""

from __future__ import annotations

import pytest

from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _bejarja_menu,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


MENU = ('Folder', 'F&older')


@pytest.mark.parametrize("magassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_tiszta_profilbol_valodi_kattintassal_bejarja_a_menut(
    tiszta_menuproba, qt_app, scratch_jelentes, magassag_eltolas
):
    _bejarja_menu(
        tiszta_menuproba,
        qt_app,
        scratch_jelentes,
        *MENU,
        magassag_eltolas=magassag_eltolas,
    )
