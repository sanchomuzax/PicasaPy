"""#6861: a Fájl-menü és a fotó helyi menüje az Album Properties ablakot nyitja."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _objektum
from tests.app.qml_functional._fomenu_4420_menu import _kattints
from tests.app.qml_functional._teszt_menu_6861 import megnyit_fomenu
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


def _kepeket_keszit(mappa: Path) -> None:
    make_minta_jpeg(mappa / "a.jpg", size=(640, 400), seed=81)
    make_minta_jpeg(mappa / "b.jpg", size=(500, 500), seed=82)


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


def _elem(gyoker, nev: str):
    elem = _objektum(gyoker, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _ablakmagassag(window, qt_app, offset: int) -> None:
    kezdeti = window.height()
    vart = kezdeti + offset
    window.setHeight(vart)
    assert _varj(qt_app, lambda: window.height() == vart), (
        f"a főablak magassága nem állt be {vart} px-re"
    )


def _kijelol_ket_kept(window, qt_app, controller) -> None:
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2), (
        "a két tesztkép nem töltődött be"
    )
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _fomenu_tetel(window, qt_app, cim: str, nev: str):
    megnyit_fomenu(window, qt_app, cim)
    tetel = _elem(window, nev)
    assert tetel.property("visible") is True, f"{nev} nem látszik a menüben"
    _kattints(qt_app, tetel)
    return tetel


def _kiadasi_kep(window, nev: str) -> None:
    mappa = os.environ.get("PICASAPY_6861_SCREENSHOT_DIR")
    if not mappa:
        return
    cel = Path(mappa)
    cel.mkdir(parents=True, exist_ok=True)
    kep = window.grabWindow()
    assert not kep.isNull(), "a kiadáskép üres"
    assert kep.save(str(cel / nev), "PNG"), f"a kiadáskép nem menthető: {nev}"


def _vizualis_bejaras(item):
    for gyerek in item.childItems():
        yield gyerek
        yield from _vizualis_bejaras(gyerek)


def _vizualis_elem(window, nev: str):
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() == nev:
            return item
    raise AssertionError(f"{nev} vizuális elem nem található")


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_file_menu_new_album_ok_utan_a_kijelolt_ket_keppel_letrejon(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    assert _varj(qt_app, lambda: controller.photos.rowCount() == 2)
    megnyit_fomenu(window, qt_app, "&File")
    _kijelol_ket_kept(window, qt_app, controller)
    tetel = _elem(window, "menuFileNewAlbum")
    assert tetel.property("visible") is True
    _kattints(qt_app, tetel)

    dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a Fájl ▸ New Album... nem nyitotta meg az Album Properties ablakot"
    )
    assert dialog.property("title") == "Album Properties"
    assert controller.albums == [], "az album az OK előtt jött létre"
    assert _elem(dialog, "folderPropertiesNameField").property("text") == "Untitled"
    if height_offset == 0:
        _kiadasi_kep(window, "picasapy-uj-album.png")

    _kattints(qt_app, _elem(dialog, "folderPropertiesOkButton"))
    assert _varj(qt_app, lambda: len(controller.albums) == 1), (
        "az OK nem hozta létre az albumot"
    )
    album = controller.albums[0]
    assert album["name"] == "Untitled"
    assert album["count"] == 2, "az albumnak mindkét kijelölt képet tartalmaznia kell"

    ini = (Path(controller.currentFolder) / ".picasa.ini").read_text(encoding="utf-8")
    assert f"[.album:{album['token']}]" in ini
    assert ini.count(f"albums={album['token']}") == 2

    pane = _elem(window, "folderPane")
    model = pane.property("albumsModel")
    if hasattr(model, "toVariant"):
        model = model.toVariant()
    assert any(
        sor["token"] == album["token"] and sor["count"] == 2 for sor in model
    ), "az új album nem jelent meg a bal hasábban két képpel"


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_photo_context_new_album_cancel_utan_nincs_valtozas(
    qml_app, qt_app, tmp_path, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)
    _kijelol_ket_kept(window, qt_app, controller)
    ini = Path(controller.currentFolder) / ".picasa.ini"
    ini_elotte = ini.read_bytes() if ini.exists() else None

    thumb = _vizualis_elem(window, "thumbMouseArea")
    pont = thumb.mapToScene(QPointF(thumb.width() / 2, thumb.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.RightButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    assert _varj(qt_app, lambda: _elem(window, "photoContextMenu").property("visible")), (
        "a jobb kattintás nem nyitotta meg a fotó helyi menüjét"
    )

    menu = _elem(window, "photoContextMenu")
    submenu = _elem(window, "contextMenuAddToAlbum")
    submenu_title = str(submenu.property("title"))
    content = menu.property("contentItem")
    pending = list(content.childItems())
    add_to_album_row = None
    while pending:
        elem = pending.pop()
        if (
            "MenuItem" in elem.metaObject().className()
            and elem.property("text") == submenu_title
        ):
            add_to_album_row = elem
            break
        pending.extend(elem.childItems())
    assert add_to_album_row is not None, "az Add to Album almenüsor nem található"
    _kattints(qt_app, add_to_album_row)
    assert _varj(qt_app, lambda: submenu.property("opened") is True), (
        "az Add to Album kattintás nem nyitotta meg az almenüt"
    )

    new_album = _elem(window, "contextMenuNewAlbum")
    assert new_album.property("visible") is True
    _kattints(qt_app, new_album)
    dialog = _elem(window, "toolbarNewAlbumPropertiesDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a kép helyi menüjének New Album... sora nem nyitott Album Properties ablakot"
    )
    assert dialog.property("title") == "Album Properties"
    assert controller.albums == [], "a párbeszéd az OK előtt létrehozta az albumot"
    if height_offset == 0:
        _kiadasi_kep(window, "picasapy-uj-album-helyi-menu.png")

    _kattints(qt_app, _elem(dialog, "folderPropertiesCancelButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False)
    assert controller.albums == []
    assert (ini.read_bytes() if ini.exists() else None) == ini_elotte


@pytest.mark.parametrize("height_offset", [-5, 0, 5])
def test_folder_menu_remove_from_picasa_megerositoje_megnevezi_a_mappat(
    qml_app, qt_app, height_offset
):
    window, controller, _engine = qml_app
    _ablakmagassag(window, qt_app, height_offset)

    _fomenu_tetel(
        window,
        qt_app,
        "F&older",
        "menuFolderRemoveFromPicasa",
    )

    dialog = _elem(window, "removeFolderConfirmDialog")
    assert _varj(qt_app, lambda: dialog.property("opened") is True), (
        "a Folder ▸ Remove from Picasa nem nyitotta meg a megerősítést"
    )
    assert dialog.property("title") == "Confirm"
    assert dialog.property("message") == (
        f'Do you want to remove the folder "{controller.currentFolder}" '
        "and its subfolders?"
    )
    if height_offset == 0:
        _kiadasi_kep(window, "picasapy-remove-from-picasa.png")
    _kattints(qt_app, _elem(dialog, "removeFolderConfirmCancelButton"))
    assert _varj(qt_app, lambda: dialog.property("opened") is False)
