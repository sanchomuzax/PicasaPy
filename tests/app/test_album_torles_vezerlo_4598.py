"""#4598 — egy album törlése minden érintett mappa ini-jéből."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QSettings

from picasapy.app.controller import AppController
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.ini.albums import parse_album_refs
from picasapy.ini.document import parse_document
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg

_TOKEN = "4598" * 8
_OTHER = "d" * 32


@pytest.fixture
def albumok(qt_app, tmp_path):
    """Két érintett és egy érintetlen mappa, albumonként több képpel."""
    root = tmp_path / "kepek"
    root.mkdir()
    mappak = {}
    for nev in ("elso", "masodik", "idegen"):
        mappa = root / nev
        mappa.mkdir()
        make_jpeg(mappa / f"{nev}.jpg")
        mappak[nev] = mappa

    (mappak["elso"] / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
        f"[.album:{_OTHER}]\ntoken={_OTHER}\nname=Másik album\n"
        f"[elso.jpg]\nalbums={_TOKEN},{_OTHER}\ncaption=maradjon\n",
        encoding="utf-8",
    )
    (mappak["masodik"] / ".picasa.ini").write_text(
        f"[.album:{_TOKEN}]\ntoken={_TOKEN}\nname=Nyaralás\n"
        f"[.album:{_OTHER}]\ntoken={_OTHER}\nname=Másik album\n"
        f"[masodik.jpg]\nalbums={_TOKEN},{_OTHER}\nstar=yes\n",
        encoding="utf-8",
    )
    (mappak["idegen"] / ".picasa.ini").write_text(
        "[idegen.jpg]\ncaption=ehhez ne nyúljon\n", encoding="utf-8"
    )
    idegen_ini = (mappak["idegen"] / ".picasa.ini").read_bytes()

    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, root)
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    controller = AppController(
        db,
        (str(root),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    controller._reload()
    return controller, mappak, idegen_ini


def test_torles_minden_erintett_mappaban_megorizve_a_tobbi_adatot(albumok):
    controller, mappak, idegen_ini = albumok

    assert controller.deleteAlbum(_TOKEN) is True

    for nev in ("elso", "masodik"):
        mappa = mappak[nev]
        document = parse_document(
            (mappa / ".picasa.ini").read_text(encoding="utf-8")
        )
        assert document.section(f".album:{_TOKEN}") is None
        assert document.section(f".album:{_OTHER}") is not None
        kep_szekcio = document.section(f"{nev}.jpg")
        assert kep_szekcio is not None
        assert _TOKEN not in parse_album_refs(kep_szekcio.get("albums") or "")
        assert _OTHER in parse_album_refs(kep_szekcio.get("albums") or "")

    elso_kep = parse_document(
        (mappak["elso"] / ".picasa.ini").read_text(encoding="utf-8")
    ).section("elso.jpg")
    masodik_kep = parse_document(
        (mappak["masodik"] / ".picasa.ini").read_text(encoding="utf-8")
    ).section("masodik.jpg")
    assert elso_kep.get("caption") == "maradjon"
    assert masodik_kep.get("star") == "yes"
    assert all((mappak[nev] / f"{nev}.jpg").is_file() for nev in mappak)
    assert (mappak["idegen"] / ".picasa.ini").read_bytes() == idegen_ini
    assert {album["token"] for album in controller.albums} == {_OTHER}


def test_ismeretlen_albumra_nem_ir(albumok):
    controller, mappak, idegen_ini = albumok
    elotte = {
        nev: (mappa / ".picasa.ini").read_bytes()
        for nev, mappa in mappak.items()
    }

    assert controller.deleteAlbum("f" * 32) is False

    assert {
        nev: (mappa / ".picasa.ini").read_bytes()
        for nev, mappa in mappak.items()
    } == elotte
    assert (mappak["idegen"] / ".picasa.ini").read_bytes() == idegen_ini
