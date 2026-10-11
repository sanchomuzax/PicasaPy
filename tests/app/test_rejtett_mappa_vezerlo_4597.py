"""#4597 — a rejtett mappa védelme a vezérlőben: gyűjtemény-átnevezés és
-törlés nem írhatja felül, ini-írási hiba és offline mappa kezelése."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.index import is_folder_hidden, open_index, sync_tree
from picasapy.ini import load_document, read_folder_category
from picasapy.scanner import PICASA_INI_NAME
from support.jpeg_factory import make_jpeg


def _kategoria(mappa) -> str | None:
    return read_folder_category(load_document(Path(mappa) / PICASA_INI_NAME))


@pytest.fixture
def ctrl(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "kepek"
    for nev in ("titkos", "masik"):
        mappa = library / nev
        mappa.mkdir(parents=True)
        make_jpeg(mappa / "a.jpg")
        (mappa / PICASA_INI_NAME).write_text(
            "[Picasa]\nP2category=tech\nname=Megtartott\n", encoding="utf-8"
        )
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    controller = AppController(
        tmp_path / "index.db",
        (str(library),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat),
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload_after_sync()
    controller.library = library
    return controller


def _rejtett(controller, mappa) -> bool:
    with open_index(controller._db_path) as conn:
        return is_folder_hidden(conn, str(mappa))


def _jelzesek(controller) -> list[tuple[str, str]]:
    lista: list[tuple[str, str]] = []
    controller.folderHideFailed.connect(lambda p, ok: lista.append((p, ok)))
    return lista


def test_atnevezes_nem_irja_felul_a_rejtett_mappat(ctrl, tmp_path):
    titkos = ctrl.library / "titkos"
    assert [c["name"] for c in ctrl.customCollections] == ["tech"]
    ctrl.toggleFolderHidden(str(titkos))
    assert _kategoria(titkos) == "Hidden Folders"
    ctrl.renameCollection("tech", "munka")
    assert _kategoria(titkos) == "Hidden Folders"
    assert _kategoria(ctrl.library / "masik") == "munka"
    with open_index(ctrl._db_path) as conn:
        sync_tree(conn, ctrl.library)
    assert _rejtett(ctrl, titkos) is True


def test_torles_nem_irja_felul_a_rejtett_mappat(ctrl):
    titkos = ctrl.library / "titkos"
    ctrl.toggleFolderHidden(str(titkos))
    ctrl.deleteCollection("tech")
    assert _kategoria(titkos) == "Hidden Folders"
    assert _kategoria(ctrl.library / "masik") == "Folders on Disk"
    with open_index(ctrl._db_path) as conn:
        sync_tree(conn, ctrl.library)
    assert _rejtett(ctrl, titkos) is True


def test_kifejezett_athelyezes_felulirhatja(ctrl):
    titkos = ctrl.library / "titkos"
    ctrl.toggleFolderHidden(str(titkos))
    ctrl.moveFolderToCollection(str(titkos), "tech")
    assert _kategoria(titkos) == "tech"


def test_elrejtes_ini_hibaja_eseten_a_mappa_azonnal_rejtett(ctrl, monkeypatch):
    titkos = ctrl.library / "titkos"

    def hiba(*_a, **_k):
        raise PermissionError("írásvédett")

    monkeypatch.setattr("picasapy.app.controller.set_folder_hidden_in_ini", hiba)
    ctrl.toggleFolderHidden(str(titkos))
    assert _rejtett(ctrl, titkos) is True
    with open_index(ctrl._db_path) as conn:
        assert conn.execute(
            "SELECT hidden FROM folders WHERE path = ?", (str(titkos),)
        ).fetchone()[0] == 2


def test_megjelenites_ini_hibaja_eseten_rejtett_marad_es_jelzes_megy(
    ctrl, monkeypatch
):
    titkos = ctrl.library / "titkos"
    ctrl.toggleFolderHidden(str(titkos))
    jelzesek = _jelzesek(ctrl)

    def hiba(*_a, **_k):
        raise PermissionError("írásvédett")

    monkeypatch.setattr("picasapy.app.controller.set_folder_hidden_in_ini", hiba)
    ctrl.toggleFolderHidden(str(titkos))
    assert _rejtett(ctrl, titkos) is True
    assert jelzesek == [(str(titkos), "write-failed-unhide")]


def test_offline_mappa_elrejtese_2_es_jelolest_ad(ctrl, tmp_path):
    utan = str(ctrl.library / "nincs-ilyen")
    with open_index(ctrl._db_path) as conn:
        conn.execute("INSERT INTO folders(path, has_ini) VALUES (?, 0)", (utan,))
        conn.commit()
    ctrl.toggleFolderHidden(utan)
    with open_index(ctrl._db_path) as conn:
        assert conn.execute(
            "SELECT hidden FROM folders WHERE path = ?", (utan,)
        ).fetchone()[0] == 2


def test_offline_mappa_megjelenitese_tiltott_es_jelzest_ad(ctrl):
    utan = str(ctrl.library / "nincs-ilyen")
    with open_index(ctrl._db_path) as conn:
        conn.execute(
            "INSERT INTO folders(path, has_ini, hidden) VALUES (?, 0, 2)", (utan,)
        )
        conn.commit()
    jelzesek = _jelzesek(ctrl)
    ctrl.toggleFolderHidden(utan)
    assert _rejtett(ctrl, utan) is True
    assert jelzesek == [(utan, "offline-unhide")]


def test_ini_iras_vedelem_a_gyorstar_nelkul_is_megvan(ctrl):
    """Ha a gyorstár elavult (a mappa még a gyűjteményben szerepel), akkor
    sem íródik felül a `Hidden Folders` átnevezés útján."""
    titkos = ctrl.library / "titkos"
    ini = titkos / PICASA_INI_NAME
    ini.write_text("[Picasa]\nP2category=Hidden Folders\n", encoding="utf-8")
    assert ctrl._write_folder_category(str(titkos), "munka") == "Hidden Folders"
    assert _kategoria(titkos) == "Hidden Folders"
    assert ctrl._write_folder_category(
        str(titkos), "munka", overwrite_hidden=True
    ) == "munka"
    assert _kategoria(titkos) == "munka"
