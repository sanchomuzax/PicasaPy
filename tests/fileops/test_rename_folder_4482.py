"""#4482: mappanév-átírás biztonságos, kísérőfájlokat megőrző művelettel."""

from __future__ import annotations

import importlib

import pytest

from picasapy.fileops import FolderRenameError, rename_folder
from picasapy.ini import parse_document, save_document


def _mappa(root, name="nyaralas"):
    folder = root / name
    (folder / "alalbum").mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"kep")
    (folder / "alalbum" / "b.jpg").write_bytes(b"masik kep")
    document = parse_document("").with_value(
        "Picasa", "description", "Balatoni nyaralás"
    )
    save_document(document, folder / ".picasa.ini")
    return folder


def test_a_mappa_a_kepekkel_es_az_ini_vel_egyutt_atnevezheto(tmp_path):
    source = _mappa(tmp_path)

    target = rename_folder(source, "Balaton 2026")

    assert target == tmp_path / "Balaton 2026"
    assert (target / "a.jpg").read_bytes() == b"kep"
    assert (target / "alalbum" / "b.jpg").read_bytes() == b"masik kep"
    assert "Balatoni nyaralás" in (target / ".picasa.ini").read_text(
        encoding="utf-8"
    )
    assert not source.exists()


def test_lefoglalt_nevnel_sem_a_cel_sem_a_forras_nem_valtozik(tmp_path):
    source = _mappa(tmp_path)
    target = _mappa(tmp_path, "mar-foglalt")
    target_ini = (target / ".picasa.ini").read_bytes()

    with pytest.raises(FolderRenameError, match="már létezik"):
        rename_folder(source, "mar-foglalt")

    assert (source / "a.jpg").read_bytes() == b"kep"
    assert (target / ".picasa.ini").read_bytes() == target_ini


@pytest.mark.parametrize(
    "name",
    ["", "   ", ".", "..", "rossz/nev", "rossz\\nev", "rossz:nev", "vege."],
)
def test_ervenytelen_mappanevnel_nincs_atnevezes(tmp_path, name):
    source = _mappa(tmp_path)

    with pytest.raises(FolderRenameError):
        rename_folder(source, name)

    assert source.is_dir()
    assert (source / "a.jpg").read_bytes() == b"kep"


def test_lemezes_hiba_eseten_a_regi_mappa_marad(tmp_path, monkeypatch):
    source = _mappa(tmp_path)
    module = importlib.import_module("picasapy.fileops.rename_folder")

    def fail(_source, _target):
        raise OSError("nincs írási jogosultság")

    monkeypatch.setattr(module, "_rename", fail)

    with pytest.raises(FolderRenameError, match="nem sikerült"):
        rename_folder(source, "uj-nev")

    assert source.is_dir()
    assert (source / "a.jpg").exists()
    assert not (tmp_path / "uj-nev").exists()
