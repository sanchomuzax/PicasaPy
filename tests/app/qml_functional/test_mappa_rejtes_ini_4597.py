"""#4597 — a Mappa ▸ Elrejtés / Megjelenítés VALÓDI kattintással az ini-be ír.

Elrejtés után a mappa `.picasa.ini`-jében `[Picasa] P2category=Hidden
Folders` áll, megjelenítés után `Folders on Disk`; a többi kulcs marad.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.ini import load_document, read_folder_category

from tests.app.qml_functional.test_album_menu_mappa_elrejtes_4741 import (
    _kattints,
    _nyisd_meg_menu_tetelt,
    _varj,
)


@pytest.fixture(autouse=True)
def _jelszoajanlat_nelkul(qml_app):
    """#5704: elrejtés után jelszóajánlat nyílna; ez a teszt az ini-írást méri."""
    from picasapy.app.confirm_settings import set_confirm_suppressed

    set_confirm_suppressed(qml_app[1]._get_settings(), "DoNotConfirmHiddenPwd", True)


def test_menu_kattintas_az_inibe_ir(qml_app, qt_app):
    window, controller, _engine = qml_app
    # Rejtett mappa nézete: a Megjelenítés tétel csak ott engedélyezett
    controller.setShowHidden(True)
    mappa = controller.currentFolder
    assert mappa, "a próba mappanézetből indul"
    ini = Path(mappa) / ".picasa.ini"

    _m, _menu, _f, hide = _nyisd_meg_menu_tetelt(qt_app, window, "menuFolderHide")
    _kattints(qt_app, hide)
    assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is True)
    assert read_folder_category(load_document(ini)) == "Hidden Folders"

    _m, _menu, _f, show = _nyisd_meg_menu_tetelt(qt_app, window, "menuFolderShow")
    _kattints(qt_app, show)
    assert _varj(qt_app, lambda: controller.isFolderHidden(mappa) is False)
    assert read_folder_category(load_document(ini)) == "Folders on Disk"
