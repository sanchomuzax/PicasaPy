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
    for nev, kategoria in (
        ("titkos", "tech"),
        ("masik", "tech"),
        ("proj", "Projects (internal)"),
    ):
        mappa = library / nev
        mappa.mkdir(parents=True)
        make_jpeg(mappa / "a.jpg")
        (mappa / PICASA_INI_NAME).write_text(
            f"[Picasa]\nP2category={kategoria}\nname=Megtartott\n", encoding="utf-8"
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


def _hiba(*_a, **_k):
    raise PermissionError("írásvédett")


def _gyujtemeny_mappai(ctrl) -> list[str]:
    return [m for c in ctrl.customCollections for m in c["folders"]]


def _projekt_mappak(ctrl) -> list[str]:
    return [p["path"] for p in ctrl.projectFolders]


def test_elrejtes_es_megjelenites_gyujtemeny_jelzest_kuld(ctrl):
    titkos = str(ctrl.library / "titkos")
    szamlalo: list[int] = []
    ctrl.customCollectionsChanged.connect(lambda: szamlalo.append(1))
    ctrl.toggleFolderHidden(titkos)
    assert szamlalo, "elrejtéskor nem ment customCollectionsChanged"
    szamlalo.clear()
    ctrl.toggleFolderHidden(titkos)
    assert szamlalo, "megjelenítéskor nem ment customCollectionsChanged"


def test_sikeresen_elrejtett_mappa_kikerul_a_gyujtemenybol(ctrl):
    """Az ini már `Hidden Folders` (mint a Picasában): a mappa a Rejtett
    mappák alá kerül, a gyűjteményben a megjelenítés után sem szerepel."""
    titkos = str(ctrl.library / "titkos")
    assert titkos in _gyujtemeny_mappai(ctrl)
    ctrl.toggleFolderHidden(titkos)
    assert titkos not in _gyujtemeny_mappai(ctrl)
    ctrl.setShowHidden(True)
    assert titkos not in _gyujtemeny_mappai(ctrl)


def test_2_es_jelolesnel_a_gyujtemenybol_is_kimarad(ctrl, monkeypatch):
    """Az ini P2category-je a gyűjtemény neve marad (az írás elbukott)."""
    titkos = str(ctrl.library / "titkos")
    monkeypatch.setattr("picasapy.app.controller.set_folder_hidden_in_ini", _hiba)
    ctrl.toggleFolderHidden(titkos)
    assert _kategoria(titkos) == "tech"
    assert titkos not in _gyujtemeny_mappai(ctrl)
    ctrl.setShowHidden(True)
    assert titkos in _gyujtemeny_mappai(ctrl)


def test_rejtett_projekt_mappa_nincs_a_projektek_kozott(ctrl):
    proj = str(ctrl.library / "proj")
    assert proj in _projekt_mappak(ctrl)
    ctrl.toggleFolderHidden(proj)
    assert proj not in _projekt_mappak(ctrl)
    ctrl.setShowHidden(True)
    assert proj in _projekt_mappak(ctrl)


def test_elrejtes_frissiti_a_gyorstarat(ctrl):
    titkos = str(ctrl.library / "titkos")
    assert titkos in ctrl._custom_collection_categories["tech"]
    ctrl.toggleFolderHidden(titkos)
    assert titkos not in ctrl._custom_collection_categories.get("tech", ())
    ctrl.toggleFolderHidden(titkos)
    assert titkos not in sum(ctrl._custom_collection_categories.values(), ())


def test_sikertelen_ini_iras_elrejtesnel_halk_jelzest_ad(ctrl, monkeypatch):
    titkos = str(ctrl.library / "titkos")
    jelzesek = _jelzesek(ctrl)
    monkeypatch.setattr("picasapy.app.controller.set_folder_hidden_in_ini", _hiba)
    ctrl.toggleFolderHidden(titkos)
    assert jelzesek == [(titkos, "write-failed-hide")]


def test_rejtett_mappa_nem_helyezheto_gyujtemenybe(ctrl):
    titkos = ctrl.library / "titkos"
    ctrl.toggleFolderHidden(str(titkos))
    jelzesek = _jelzesek(ctrl)
    ctrl.moveFolderToCollection(str(titkos), "tech")
    assert _kategoria(titkos) == "Hidden Folders"
    assert jelzesek == [(str(titkos), "hidden-move")]


def _athelyez_2_es(ctrl):
    import shutil

    regi = ctrl.library / "titkos"
    uj = ctrl.library / "athelyezett"
    with open_index(ctrl._db_path) as conn:
        conn.execute("UPDATE folders SET hidden = 2 WHERE path = ?", (str(regi),))
        conn.commit()
    shutil.move(str(regi), str(uj))
    return regi, uj


def test_2_es_mappa_athelyezeskor_a_rejtes_az_uj_utra_kerul(ctrl):
    regi, uj = _athelyez_2_es(ctrl)
    ctrl.resyncMovedFolder(str(regi), str(uj))
    assert _kategoria(uj) == "Hidden Folders"


def test_athelyezes_ini_hiba_eseten_az_uj_ut_2_es_jelolest_kap(ctrl, monkeypatch):
    regi, uj = _athelyez_2_es(ctrl)
    monkeypatch.setattr("picasapy.app.hidden_carry.set_folder_hidden_in_ini", _hiba)
    ctrl.resyncMovedFolder(str(regi), str(uj))
    with open_index(ctrl._db_path) as conn:
        assert conn.execute(
            "SELECT hidden FROM folders WHERE path = ?", (str(uj),)
        ).fetchone()[0] == 2
