"""#6845: A Keresés a lemezen és Áthelyezés gyűjteménybe folyamatai valódi kattintással.

A #6845 jegy táblázatának két hiányzó PicasaPy-oldali vizsgálata:
1. „Keresés a lemezen":
   - Kép helyi menüje (1 és 2 kijelölt képpel)
   - Mappa helyi menüje (1 és 2 kijelölt képpel)
   - Fájl menü (1 és 2 kijelölt képpel, valamint kijelölés nélkül)
2. „Áthelyezés gyűjteménybe":
   - Mappa helyi menüje: Új gyűjtemény létrehozása (1 és 2 kijelölt képpel)
   - Mappa helyi menüje: Meglévő gyűjteménybe mozgatás (1 és 2 kijelölt képpel)
   - Kép helyi menüje és Fájl menü (igazolás, hogy ezekről a helyekről nem érhető el)
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtTest import QTest

import picasapy.app.fileops_controller as fileops_module
from picasapy.ini import load_document
from picasapy.ini.folder_category import CATEGORY_KEY, FOLDER_SECTION
from picasapy.scanner import PICASA_INI_NAME

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    tetel_kattintasa,
    varj,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    almenu_megnyitasa,
    gyerek,
    jobbklikk_fotón,
    jobbklikk_mappan,
    kattints,
    keres_vizualis,
    kijelol,
    kijelolt,
    nyitott,
    zar,
)


_ABLAKMAGASSAGOK = (-5, 0, 5)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def _ini_kategoria(mappa: Path) -> str:
    ini = mappa / PICASA_INI_NAME
    if not ini.exists():
        return ""
    szakasz = load_document(ini).section(FOLDER_SECTION)
    if szakasz is None:
        return ""
    return (szakasz.get(CATEGORY_KEY) or szakasz.get("category") or "")


@pytest.mark.parametrize("darab", [1, 2])
def test_kereses_a_lemezen_kep_helyi_menubol(app, qt_app, monkeypatch, darab):
    """Keresés a lemezen a kép helyi menüjéből 1 és 2 kijelölt képpel."""
    window, controller, _engine = app
    source = elokeszit(window, qt_app, controller)
    alapmagassag = window.height()

    mutatott_kepek: list[Path] = []
    mutatott_mappak: list[Path] = []
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: mutatott_kepek.append(Path(path)),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: mutatott_mappak.append(Path(path)),
    )

    vart_utvonalak = [
        Path(controller.photos.filePathAt(i)) for i in range(darab)
    ]
    cel_kep = vart_utvonalak[0]

    for elteres in _ABLAKMAGASSAGOK:
        window.resize(window.width(), alapmagassag + elteres)
        qt_app.processEvents()

        mutatott_kepek.clear()
        mutatott_mappak.clear()

        # Kijelöljük az 1 vagy 2 képet
        kijelol(window, qt_app, range(darab))
        assert kijelolt(window) == list(range(darab))

        # Jobbklikk a 0. képen
        menu = jobbklikk_fotón(window, qt_app, 0)
        assert varj(qt_app, lambda m=menu: m.property("visible") is True)

        locate_item = gyerek(window, "contextMenuLocate")
        assert locate_item.property("visible") is True
        assert locate_item.property("enabled") is True

        kattints(window, qt_app, locate_item)
        qt_app.processEvents()

        # Rögzített hatások:
        # 1. Ablak: nem nyílik belső párbeszédablak
        assert not nyitott(window.findChild(QObject, "moveToNewFolderDialog"))
        assert not nyitott(window.findChild(QObject, "newCollectionDialog"))

        # 2. Lemez: a képfájlok és az ini nem változnak
        assert all(p.is_file() for p in vart_utvonalak)
        assert _ini_kategoria(source) == ""

        # 3. Index: a fotók száma nem változik
        assert controller.photos.rowCount() == 3

        # 4. Bal hasáb: az aktuális mappa marad kijelölve
        assert Path(controller.currentFolder) == source

        # 5. Rács: a kijelölés megmarad
        assert kijelolt(window) == list(range(darab))

        # 6. Hívás: a fájlkezelő megnyitása a célzott képre történt
        assert mutatott_kepek == [cel_kep], f"eltérés: {elteres}px"
        assert mutatott_mappak == []

        zar(qt_app, menu)


@pytest.mark.parametrize("darab", [1, 2])
def test_kereses_a_lemezen_mappa_helyi_menubol(app, qt_app, monkeypatch, darab):
    """Keresés a lemezen a mappa helyi menüjéből 1 és 2 kijelölt képpel."""
    window, controller, _engine = app
    source = elokeszit(window, qt_app, controller)
    alapmagassag = window.height()

    mutatott_kepek: list[Path] = []
    mutatott_mappak: list[Path] = []
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: mutatott_kepek.append(Path(path)),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: mutatott_mappak.append(Path(path)),
    )

    for elteres in _ABLAKMAGASSAGOK:
        window.resize(window.width(), alapmagassag + elteres)
        qt_app.processEvents()

        mutatott_kepek.clear()
        mutatott_mappak.clear()

        kijelol(window, qt_app, range(darab))
        assert kijelolt(window) == list(range(darab))

        # Jobbklikk a bal oldali mappán
        menu = jobbklikk_mappan(window, qt_app, source)
        assert varj(qt_app, lambda m=menu: m.property("visible") is True)

        locate_item = gyerek(window, "folderMenuLocate")
        assert locate_item.property("visible") is True
        assert locate_item.property("enabled") is True

        kattints(window, qt_app, locate_item)
        qt_app.processEvents()

        # Rögzített hatások:
        # 1. Ablak: nem nyílik belső párbeszédablak
        assert not nyitott(window.findChild(QObject, "newCollectionDialog"))

        # 2. Lemez: lemezállapot érintetlen
        assert _ini_kategoria(source) == ""

        # 3. Index: fotók és mappák változatlanok
        assert controller.photos.rowCount() == 3

        # 4. Bal hasáb: a mappa marad
        assert Path(controller.currentFolder) == source

        # 5. Rács: a kijelölés megmarad
        assert kijelolt(window) == list(range(darab))

        # 6. Hívás: a mappa megnyitása történt a fájlkezelőben
        assert mutatott_kepek == []
        assert mutatott_mappak == [source], f"eltérés: {elteres}px"

        zar(qt_app, menu)


@pytest.mark.parametrize("darab", [1, 2])
def test_kereses_a_lemezen_fajl_menubol(app, qt_app, monkeypatch, darab):
    """Keresés a lemezen a felső Fájl menüből 1 és 2 kijelölt képpel."""
    window, controller, _engine = app
    source = elokeszit(window, qt_app, controller)
    alapmagassag = window.height()

    mutatott_kepek: list[Path] = []
    mutatott_mappak: list[Path] = []
    monkeypatch.setattr(
        fileops_module,
        "reveal_in_file_manager",
        lambda path: mutatott_kepek.append(Path(path)),
    )
    monkeypatch.setattr(
        fileops_module,
        "open_folder_in_file_manager",
        lambda path: mutatott_mappak.append(Path(path)),
    )

    cel_kep = Path(controller.photos.filePathAt(0))

    for elteres in _ABLAKMAGASSAGOK:
        window.resize(window.width(), alapmagassag + elteres)
        qt_app.processEvents()

        mutatott_kepek.clear()
        mutatott_mappak.clear()

        kijelol(window, qt_app, range(darab))
        assert kijelolt(window) == list(range(darab))

        # Fájl menü megnyitása és rákattintás a Locate on Disk tételre
        locate_item = gyerek(window, "menuFileLocate")
        assert locate_item.property("enabled") is True

        tetel_kattintasa(window, qt_app, "&File", "menuFileLocate")
        qt_app.processEvents()

        # Rögzített hatások:
        # 1. Ablak: nem nyílik belső ablak
        assert not nyitott(window.findChild(QObject, "newCollectionDialog"))

        # 2. Lemez: változatlan
        assert _ini_kategoria(source) == ""

        # 3. Index: változatlan
        assert controller.photos.rowCount() == 3

        # 4. Bal hasáb: változatlan
        assert Path(controller.currentFolder) == source

        # 5. Rács: kijelölés megmarad
        assert kijelolt(window) == list(range(darab))

        # 6. Hívás: az első kijelölt kép útvonalával fut le
        assert mutatott_kepek == [cel_kep], f"eltérés: {elteres}px"
        assert mutatott_mappak == []


def test_kereses_a_lemezen_fajl_menubol_kijeloles_nelkul_tiltott(app, qt_app):
    """Keresés a lemezen a Fájl menüből kijelölés nélkül tiltott."""
    window, controller, _engine = app
    elokeszit(window, qt_app, controller)

    # Kijelölés megszüntetése
    kijelol(window, qt_app, [])
    assert kijelolt(window) == []

    locate_item = gyerek(window, "menuFileLocate")
    assert locate_item.property("enabled") is False, (
        "kijelölés nélkül a Fájl ▸ Locate on Disk tételnek tiltottnak kell lennie"
    )


@pytest.mark.parametrize("darab", [1, 2])
def test_athelyezes_uj_gyujtemenybe_mappa_helyi_menubol(app, qt_app, darab):
    """Áthelyezés új gyűjteménybe a mappa helyi menüjéből 1 és 2 kijelölt képpel."""
    window, controller, _engine = app
    source = elokeszit(window, qt_app, controller)
    gyujtemeny_nev = f"UjGyujt_{darab}"

    kijelol(window, qt_app, range(darab))
    assert kijelolt(window) == list(range(darab))

    menu = jobbklikk_mappan(window, qt_app, source)
    assert varj(qt_app, lambda m=menu: m.property("visible") is True)

    almenu_megnyitasa(window, qt_app, menu, "folderContextMenuMoveToCollection")
    new_col_item = gyerek(window, "folderContextMenuNewCollection")
    assert new_col_item.property("visible") is True

    kattints(window, qt_app, new_col_item)

    dialog = gyerek(window, "newCollectionDialog")
    assert varj(qt_app, lambda: dialog.property("opened") is True), (
        "az Új gyűjtemény nem nyitotta meg a newCollectionDialog ablakot"
    )
    assert dialog.property("title") == "New Collection"

    # Név beírása a mezőbe, majd Enter leütése az elfogadáshoz
    name_field = gyerek(dialog, "newCollectionNameField")
    name_field.setProperty("text", gyujtemeny_nev)
    qt_app.processEvents()

    QTest.keyClick(window, Qt.Key.Key_Return)
    qt_app.processEvents()

    assert varj(qt_app, lambda: dialog.property("opened") is False), (
        "az elfogadás után a newCollectionDialog nem záródott be"
    )

    # Rögzített hatások:
    # 1. Lemez: a .picasa.ini [Picasa] szakaszában megjelenik a category (P2category)
    assert varj(qt_app, lambda: _ini_kategoria(source) == gyujtemeny_nev), (
        f"a lemezen az ini-ben nem jelent meg a P2category = {gyujtemeny_nev}"
    )

    # 2. Index: a customCollections-ben szerepel az új gyűjtemény
    assert varj(
        qt_app,
        lambda: any(c["name"] == gyujtemeny_nev for c in controller.customCollections),
    ), "az új gyűjtemény nem jelent meg a controller.customCollections-ben"

    # 3. Bal hasáb: megjelenik a gyűjtemény fejléc és a mappa alatta
    repeater = gyerek(window, "customCollectionsRepeater")
    assert varj(qt_app, lambda: repeater.property("count") >= 1)

    # 4. Rács: a mappa képei és a kijelölés megmarad
    assert controller.photos.rowCount() == 3
    assert kijelolt(window) == list(range(darab))

    zar(qt_app, menu)


def test_athelyezes_meglevo_gyujtemenybe_mappa_helyi_menubol(app, qt_app):
    """Áthelyezés meglévő gyűjteménybe a mappa helyi menüjéből."""
    window, controller, _engine = app
    source = elokeszit(window, qt_app, controller)
    cel_gyujtemeny = "LetezoGyujt"

    controller.createCollection(cel_gyujtemeny)
    pane = gyerek(window, "folderPane")
    QMetaObject.invokeMethod(
        pane, "refreshCustomCollections", Qt.ConnectionType.DirectConnection
    )
    qt_app.processEvents()
    assert any(c["name"] == cel_gyujtemeny for c in controller.customCollections)

    kijelol(window, qt_app, [0, 1])
    assert kijelolt(window) == [0, 1]

    menu = jobbklikk_mappan(window, qt_app, source)
    assert varj(qt_app, lambda m=menu: m.property("visible") is True)

    almenu_megnyitasa(window, qt_app, menu, "folderContextMenuMoveToCollection")

    item_nev = f"folderContextMenuMoveToCollectionItem_{cel_gyujtemeny}"
    target_item = keres_vizualis(window, item_nev)
    assert target_item is not None, f"a(z) {item_nev} nem jelent meg a menüben"
    assert target_item.isVisible() is True

    kattints(window, qt_app, target_item)
    qt_app.processEvents()

    # Rögzített hatások:
    # 1. Ablak: nem nyílik párbeszéd (közvetlen áthelyezés)
    assert not nyitott(window.findChild(QObject, "newCollectionDialog"))

    # 2. Lemez: az ini category-ja a megadott gyűjtemény
    assert varj(qt_app, lambda: _ini_kategoria(source) == cel_gyujtemeny)

    # 3. Index: a mappa a gyűjtemény része
    assert varj(
        qt_app,
        lambda: any(
            c["name"] == cel_gyujtemeny and str(source) in c["folders"]
            for c in controller.customCollections
        ),
    )

    # 4. Bal hasáb: a mappa átkerült
    assert Path(controller.currentFolder) == source

    # 5. Rács: a kijelölés megmarad
    assert kijelolt(window) == [0, 1]

    zar(qt_app, menu)


def test_athelyezes_gyujtemenybe_hianyzik_kep_helyi_es_fajl_menubol(app, qt_app):
    """Az Áthelyezés gyűjteménybe parancs hiányzik a kép helyi és a Fájl menüből."""
    window, controller, _engine = app
    elokeszit(window, qt_app, controller)

    # 1. Kép helyi menüjében:
    menu = jobbklikk_fotón(window, qt_app, 0)
    assert varj(qt_app, lambda m=menu: m.property("visible") is True)
    assert window.findChild(QObject, "folderContextMenuMoveToCollection") is None or not any(
        "Move to Collection" in str(getattr(c, "property", lambda _: "")("text"))
        for c in menu.findChildren(QObject)
    )
    # A képre csak új mappába helyezés van (fájlművelet)
    assert gyerek(window, "contextMenuMove") is not None
    zar(qt_app, menu)

    # 2. Fájl menüben:
    # A menüben csak Move Picture to Folder / Move to New Folder van
    assert window.findChild(QObject, "menuFileMoveToCollection") is None
