"""#4420: keresési parancs után visszaáll a tiszta profil állapota."""

from __future__ import annotations

from PySide6.QtCore import QObject

from tests.app.qml_functional import _fomenu_4420_akciok as _akciok
from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _megnyit,
    _menuk,
    _parancsok,
    _szoveg,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


def test_keresesi_parancs_utan_torolje_a_keresot_es_allitsa_vissza_a_mintamappat(
    tiszta_menuproba, qt_app
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    minta = tmp_path / "kepek"
    vezerlo.selectFolder(str(minta))
    ablak.setProperty("selectedIndexes", [0])
    ablak.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    menu_bar = ablak.property("menuBar")
    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    keresesi_parancs = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsSearchRed"
    )
    eredmeny = _akciok._akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        keresesi_parancs,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    hibasav = ablak.findChild(QObject, "errorBannerText")
    assert hibasav is not None
    assert _szoveg(hibasav, "text") == "", (
        "a színkeresés tájékoztató sávja nyitva maradt a parancs utáni "
        f"visszaállításkor: {eredmeny}"
    )
    assert vezerlo.color_index_fut() is False, (
        "a színkeresés háttérmunkája átnyúlt a következő menüparancsra"
    )
    toolbar = ablak.findChild(QObject, "mainToolbar")
    assert _szoveg(toolbar, "searchText") == "", (
        f"a keresőmező nem ürült ki a parancs után: {eredmeny}"
    )
    assert vezerlo.property("searchActive") is False
    assert vezerlo.property("currentFolder") == str(minta)
    assert not any(menu.property("opened") is True for menu in _menuk(menu_bar))
