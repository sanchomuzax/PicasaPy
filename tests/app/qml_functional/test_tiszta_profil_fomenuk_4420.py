"""#4420/#4433: a főmenü-bejáró külön regressziós őrei."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, QTimer

from tests.app.qml_functional import _fomenu_4420_akciok as _akciok
from tests.app.qml_functional import _fomenu_4420_menu as _menu_segedek
from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _ABLAK_ALAPMAGASSAG,
    _ABLAKMAGASSAG_ELTOLASOK,
    _NYELV_ALMENU_MIN_MAGASSAG,
    _UTAK,
    _akcio,
    _megnyit,
    _menuk,
    _parancsok,
    _szoveg,
    _varj,
    _zarj_parbeszedeket,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


def test_parancsok_kihagyja_a_nem_qobject_menuelemet(monkeypatch):
    class Kifejezes:
        def evaluate(self):
            return QMetaObject(), None

    monkeypatch.setattr(
        _menu_segedek,
        "QQmlExpression",
        lambda *_args: Kifejezes(),
    )
    menu = QObject()
    menu.setProperty("count", 1)

    assert _menu_segedek._parancsok(menu, QObject()) == []


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
    eredmeny = _akcio(
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


def test_parbeszed_bezarasara_varakozik_a_lathato_allapot_vegeig(
    qt_app, monkeypatch
):
    """A lassabban bezáródó párbeszédet ne jelentse nyitva maradónak."""
    from PySide6.QtQuick import QQuickWindow

    ablak = QQuickWindow()
    ablak.show()
    qt_app.processEvents()
    dialogus = QObject()
    dialogus.setObjectName("kesleltetettDialog")
    dialogus.setProperty("visible", True)
    monkeypatch.setattr(
        _akciok,
        "_lathato_dialogusok",
        lambda _ablak: [dialogus] if dialogus.property("visible") else [],
    )
    # Az Escape után a QML bezárási átmenete csak később tünteti el az ablakot.
    QTimer.singleShot(1250, lambda: dialogus.setProperty("visible", False))
    naplo = []
    try:
        _zarj_parbeszedeket(ablak, qt_app, naplo)
    finally:
        ablak.close()

    assert dialogus.property("visible") is False
    assert not any("nyitva maradt" in sor for sor in naplo), naplo


def test_screensaver_utan_a_backup_parancs_is_elerheto(
    tiszta_menuproba, qt_app
):
    ablak, vezerlo, _motor, tmp_path, kulsok = tiszta_menuproba
    menu_bar = ablak.property("menuBar")
    minta = tmp_path / "kepek"

    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    screensaver = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsScreensaver"
    )
    screensaver_eredmeny = _akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        screensaver,
        tmp_path / "kepernyokepek",
        kulsok,
    )
    assert not _akciok._lathato_dialogusok(ablak), (
        "a Configure Screensaver párbeszédablaka nem záródott be a parancs után: "
        f"{screensaver_eredmeny}"
    )

    tools_menu = _megnyit(menu_bar, qt_app, "&Tools")
    backup = next(
        parancs
        for parancs in _parancsok(tools_menu, menu_bar)
        if parancs["nev"] == "menuToolsBackup"
    )
    backup_eredmeny = _akcio(
        ablak,
        vezerlo,
        minta,
        menu_bar,
        qt_app,
        "Tools",
        backup,
        tmp_path / "kepernyokepek",
        kulsok,
    )

    assert not screensaver_eredmeny["hiba"], (
        "a Configure Screensaver parancs hatását nem ismerte fel: "
        f"{screensaver_eredmeny}"
    )
    assert "screensaverDialog" in screensaver_eredmeny["eredmeny"]
    assert not backup_eredmeny["hiba"], (
        "a Configure Screensaver után a Back Up Pictures parancs nem nyílt meg: "
        f"{backup_eredmeny}"
    )
    assert "backupHost" in backup_eredmeny["eredmeny"]


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
