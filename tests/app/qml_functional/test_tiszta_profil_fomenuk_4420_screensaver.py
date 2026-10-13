"""#4420: a screensaver párbeszéd után a Back Up Pictures elérhető."""

from __future__ import annotations

from tests.app.qml_functional import _fomenu_4420_akciok as _akciok
from tests.app.qml_functional._fomenu_bejaro_4420 import (
    _akcio,
    _megnyit,
    _parancsok,
)

pytest_plugins = ("tests.app.qml_functional._fomenu_4420_akciok",)


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
    # A napló helyben az objectName-et (screensaverDialog), a CI-n az
    # osztálynevet (ScreensaverDialog) írja — a kis-nagybetű nem számít.
    assert "screensaverdialog" in screensaver_eredmeny["eredmeny"].casefold()
    assert not backup_eredmeny["hiba"], (
        "a Configure Screensaver után a Back Up Pictures parancs nem nyílt meg: "
        f"{backup_eredmeny}"
    )
    assert "backupHost" in backup_eredmeny["eredmeny"]
