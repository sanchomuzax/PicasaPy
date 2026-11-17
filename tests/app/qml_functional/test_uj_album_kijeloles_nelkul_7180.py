"""#7180: a Fájl ▸ New Album... és a Ctrl+N kijelölt kép nélkül is él.

Az eredeti Fájl-menü állapotfrissítője (`0x0056e1c0`) a `0x9d67` (New Album...)
azonosítót sehol nem szürkíti, és a `0x005eb810` kezelő nem vizsgál kijelölést;
a Ctrl+N ugyanezt a parancsot váltja ki. Kijelölés nélkül is megnyílik az
`Untitled`, mai dátumos Album Properties ablak (#7164 óta üres albumot hoz
létre).

A próbák valódi felületi vezérlőn mennek végig: a menütételre VALÓDI
egérkattintás, a billentyűre VALÓDI `Ctrl+N` érkezik a főablakra. A jel vagy a
metódus közvetlen hívása itt nem elég: egy szürke tételen a `triggered`
közvetlen kiváltása akkor is „sikerülne", ha a felhasználó rá sem tud kattintani.

Nem változik: az Add to ▸ New Album... kijelölt képeket mentő útja és a tálca
New Album... sora (ld. `test_hozzaadas_albumhoz_almenu_7100.py`,
`test_tray_add_album_5846.py`).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _kattints
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre

_MAGASSAG_ELTERESEK = [-5, 0, 5]


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=91)
    make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=92)


@pytest.fixture
def qml_app(qt_app, tmp_path, request):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket_keszit,
        keep_modul=request.module,
    )


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 5.0)


def _elem(gyoker, nev: str) -> QObject:
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _ablakmagassag(window, qt_app, offset: int) -> None:
    vart = window.height() + offset
    window.setHeight(vart)
    assert _varj(qt_app, lambda: window.height() == vart), (
        f"a főablak magassága nem állt be {vart} px-re"
    )


def _betolt(window, qt_app, controller) -> None:
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2), (
        "a két tesztkép nem töltődött be"
    )


def _nincs_kijeloles(window, qt_app, controller) -> None:
    _betolt(window, qt_app, controller)
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    qt_app.processEvents()
    assert _kijeloles(window) == [], "a kijelölés nem ürült ki: a mérés nem érvényes"


def _kijelol_ket_kept(window, qt_app, controller) -> None:
    _betolt(window, qt_app, controller)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _kijeloles(window) -> list[int]:
    ertek = window.property("selectedIndexes")
    if hasattr(ertek, "toVariant"):
        ertek = ertek.toVariant()
    return [int(i) for i in (ertek or [])]


def _ini_bajtok(controller) -> bytes | None:
    ini = Path(controller.currentFolder) / ".picasa.ini"
    return ini.read_bytes() if ini.exists() else None


def _fajl_menu_uj_album(window, qt_app) -> QObject:
    """Fájl ▸ New Album... valódi kattintással; a megnyílt ablakkal tér vissza."""
    megnyit_fomenu(window, qt_app, "&File")
    tetel = _elem(window, "menuFileNewAlbum")
    assert tetel.property("visible") is True
    assert tetel.property("enabled") is True, (
        "kijelölés nélkül szürke a Fájl ▸ New Album... (#7180)"
    )
    _kattints(qt_app, tetel)
    return _megnyilt_ablak(window, qt_app)


def _ctrl_n(window, qt_app) -> QObject:
    """Valódi Ctrl+N a főablakra; a megnyílt ablakkal tér vissza."""
    QTest.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()
    return _megnyilt_ablak(window, qt_app)


def _megnyilt_ablak(window, qt_app) -> QObject:
    dialog = window.findChild(QObject, "toolbarNewAlbumPropertiesDialog")
    assert dialog is not None, "az Album Properties ablak nem jött létre"
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "kijelölés nélkül nem nyílt meg az Album Properties ablak (#7180)"
    )
    return dialog


def _ablak_tartalma_untitled_mai_datummal(dialog, elotte: str) -> None:
    assert dialog.property("title") == "Album Properties"
    assert _elem(dialog, "folderPropertiesNameField").property("text") == "Untitled"
    assert dialog.property("currentDate") in {elotte, date.today().isoformat()}, (
        "az ablak dátuma nem a létrehozás napja"
    )


def _ok(qt_app, dialog) -> None:
    _kattints(qt_app, _elem(dialog, "folderPropertiesOkButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False), (
        "az OK nem zárta be az Album Properties ablakot"
    )


def _megse(qt_app, dialog) -> None:
    _kattints(qt_app, _elem(dialog, "folderPropertiesCancelButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False), (
        "a Mégse nem zárta be az Album Properties ablakot"
    )


def _ures_album_nyilt_meg_ini_valtozatlan(
    qt_app, window, controller, ini_elotte: bytes | None
) -> None:
    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "az OK nem hozta létre az albumot"
    )
    album = controller.albums[0]
    assert album["name"] == "Untitled"
    assert album["count"] == 0
    token = album["token"]
    assert _varj(qt_app, lambda: controller.currentAlbumToken == token), (
        "az új üres album nem nyílt meg"
    )
    assert controller.viewModeName == "album"
    assert controller.photos.rowCount() == 0
    assert _ini_bajtok(controller) == ini_elotte, (
        "a képek mappájának .picasa.ini-je megváltozott"
    )


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_fajl_menu_uj_album_kijeloles_nelkul_engedelyezett_es_untitled_mai_datummal(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _nincs_kijeloles(window, qt_app, controller)
    ini_elotte = _ini_bajtok(controller)
    elotte = date.today().isoformat()

    dialog = _fajl_menu_uj_album(window, qt_app)

    _ablak_tartalma_untitled_mai_datummal(dialog, elotte)
    assert controller.albums == [], "az album az OK előtt jött létre"
    _ok(qt_app, dialog)
    _ures_album_nyilt_meg_ini_valtozatlan(qt_app, window, controller, ini_elotte)


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_ctrl_n_kijeloles_nelkul_untitled_mai_datummal_nyitja_az_ablakot(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _nincs_kijeloles(window, qt_app, controller)
    ini_elotte = _ini_bajtok(controller)
    elotte = date.today().isoformat()

    dialog = _ctrl_n(window, qt_app)

    _ablak_tartalma_untitled_mai_datummal(dialog, elotte)
    assert controller.albums == [], "az album az OK előtt jött létre"
    _ok(qt_app, dialog)
    _ures_album_nyilt_meg_ini_valtozatlan(qt_app, window, controller, ini_elotte)


@pytest.mark.parametrize("belepo", ["fajl_menu", "ctrl_n"])
@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_cancel_kijeloles_nelkul_nem_hoz_letre_albumot(
    qml_app, qt_app, belepo, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _nincs_kijeloles(window, qt_app, controller)
    ini_elotte = _ini_bajtok(controller)
    mappa = controller.currentFolder

    if belepo == "fajl_menu":
        dialog = _fajl_menu_uj_album(window, qt_app)
    else:
        dialog = _ctrl_n(window, qt_app)
    _megse(qt_app, dialog)

    assert controller.albums == []
    assert controller.currentAlbumToken == ""
    assert controller.viewModeName == "folder"
    assert controller.currentFolder == mappa
    assert controller.photos.rowCount() == 2
    assert _ini_bajtok(controller) == ini_elotte


@pytest.mark.parametrize("belepo", ["fajl_menu", "ctrl_n"])
@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_kijelolt_kepekkel_is_ures_albumot_hoz_letre_tagsag_nelkul(
    qml_app, qt_app, belepo, height_offset
):
    """A kijelölés a Fájl ▸ New Album... útján nem számít (#7164): a viselkedés
    a #7180 előtti marad."""
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)
    ini_elotte = _ini_bajtok(controller)
    elotte = date.today().isoformat()

    if belepo == "fajl_menu":
        dialog = _fajl_menu_uj_album(window, qt_app)
    else:
        dialog = _ctrl_n(window, qt_app)
    _ablak_tartalma_untitled_mai_datummal(dialog, elotte)
    _ok(qt_app, dialog)

    _ures_album_nyilt_meg_ini_valtozatlan(qt_app, window, controller, ini_elotte)
    assert "albums=" not in (ini_elotte or b"").decode("utf-8")


@pytest.mark.parametrize("height_offset", _MAGASSAG_ELTERESEK)
def test_ctrl_n_szovegmezo_fokuszban_kijeloles_nelkul_sem_nyit_ablakot(
    qml_app, qt_app, height_offset
):
    """A `textEntryHasFocus` miatti tiltás a #7180 után is marad: a keresőmezőben
    a Ctrl+N nem nyit ablakot."""
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _nincs_kijeloles(window, qt_app, controller)
    mezo = _elem(window, "searchField")
    mezo.setProperty("focus", True)
    qt_app.processEvents()
    assert mezo.property("activeFocus") is True, (
        "a keresőmező nem kapott fókuszt: a mérés nem érvényes"
    )
    shortcut = _elem(window, "shortcutNewAlbum")
    assert shortcut.property("enabled") is False

    QTest.keyClick(window, Qt.Key.Key_N, Qt.KeyboardModifier.ControlModifier)
    qt_app.processEvents()

    dialog = window.findChild(QObject, "toolbarNewAlbumPropertiesDialog")
    assert dialog is None or dialog.property("opened") is not True, (
        "a Ctrl+N szövegmező-fókuszban megnyitotta az ablakot"
    )
    assert controller.albums == []
