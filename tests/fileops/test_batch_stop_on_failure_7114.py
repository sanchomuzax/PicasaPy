"""#7114: a vágólapos Beillesztés köteg az ELSŐ végleges fájlhibánál megáll.

Az eredeti `0x005350b0` fájlonként hívja a `0x00479870` segédet, és a
különleges `0xf4242` eredménynél kilép a további elemek ciklusából: a
korábbi sikeres másolatok megmaradnak, a későbbi képeket nem is kezdi el.

Ez a fájl a MAG (`fileops/batch.py`) képességét méri: a `stop_on_failure`
kapcsoló. A kapcsoló alapértéke KIKAPCSOLT, mert a fogd-és-vidd és a menüs
másolás/áthelyezés kötegei (#301/#459) továbbra is folytatják a hibás fájl
után: egy hibás kép nem állíthatja meg a többit. Az alapérték őre itt van.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops import batch as batch_module
from picasapy.fileops import copy as copy_module
from picasapy.fileops.batch import RENAME, copy_photos, move_photos


def _photo(folder: Path, name: str, content: bytes = b"kep") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(content)
    return path


@pytest.fixture
def harom_kep(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    kepek = [_photo(src, nev, nev.encode()) for nev in ("a.jpg", "b.jpg", "c.jpg")]
    dest.mkdir()
    return kepek, dest


@pytest.fixture
def masodik_iras_hibas(monkeypatch):
    """A MÁSODIK kép (`b.jpg`) másolása lemezhibára fut, a többié nem.

    A hibát a `batch` modul saját `copy_photo` fogantyúján injektáljuk, nem a
    globális `shutil.copy2`-n (az átszivárogna minden más modulba, #1375).
    """
    eredeti = batch_module.copy_photo

    def copy_photo(path, dest_folder):
        if Path(path).name == "b.jpg":
            raise OSError(28, "No space left on device")
        return eredeti(path, dest_folder)

    monkeypatch.setattr(batch_module, "copy_photo", copy_photo)


def test_masolasnal_a_masodik_hibajanal_megall_a_koteg(harom_kep, masodik_iras_hibas):
    (a, b, c), dest = harom_kep

    result = copy_photos([a, b, c], dest, RENAME, stop_on_failure=True)

    assert (dest / "a.jpg").read_bytes() == b"a.jpg", "az első másolat NEM maradt meg"
    assert not (dest / "b.jpg").exists(), "a hibás kép félkész példánya maradt"
    assert not (dest / "c.jpg").exists(), "a hiba után a harmadik kép is elindult"
    assert result.done == ((a, dest / "a.jpg"),)
    assert [path for path, _ in result.failed] == [b]
    assert "No space left" in result.failed[0][1]
    assert result.not_started == (c,), "a nem indított képet az eredmény nevezze meg"


def test_a_felig_megirt_masodik_masolat_visszavonva_a_harmadik_nem_indul(
    harom_kep, monkeypatch
):
    """A képfájl már lemezen van, de a megőrzött eredetije nem másolható:
    a `copy_photo` visszavonja a fél másolatot, a köteg pedig megáll."""
    (a, b, c), dest = harom_kep
    eredeti = copy_module.copy_preserved_originals

    def copy_preserved_originals(source, target):
        if Path(source).name == "b.jpg":
            raise OSError(5, "Input/output error")
        return eredeti(source, target)

    monkeypatch.setattr(copy_module, "copy_preserved_originals", copy_preserved_originals)

    result = copy_photos([a, b, c], dest, RENAME, stop_on_failure=True)

    assert (dest / "a.jpg").exists()
    assert not (dest / "b.jpg").exists(), "a fél másolat nem lett visszavonva"
    assert not (dest / "c.jpg").exists()
    assert "Input/output error" in result.failed[0][1]
    assert result.not_started == (c,)


def test_athelyezesnel_is_megall_az_elso_hibanal(harom_kep, monkeypatch):
    (a, b, c), dest = harom_kep

    eredeti = batch_module.move_photo

    def move_photo(path, dest_folder):
        if Path(path).name == "b.jpg":
            raise OSError(13, "Permission denied")
        return eredeti(path, dest_folder)

    monkeypatch.setattr(batch_module, "move_photo", move_photo)

    result = move_photos([a, b, c], dest, RENAME, stop_on_failure=True)

    assert (dest / "a.jpg").exists() and not a.exists()
    assert b.exists() and not (dest / "b.jpg").exists()
    assert c.exists() and not (dest / "c.jpg").exists(), "a harmadik kép elmozdult"
    assert [path for path, _ in result.failed] == [b]
    assert result.not_started == (c,)


def test_a_haladasjelzo_az_utolso_elindult_elemnel_all_meg(harom_kep, masodik_iras_hibas):
    (a, b, c), dest = harom_kep
    jelzesek: list[tuple[int, int]] = []

    copy_photos(
        [a, b, c], dest, RENAME, lambda kesz, osszes: jelzesek.append((kesz, osszes)),
        stop_on_failure=True,
    )

    assert jelzesek == [(1, 3), (2, 3)], "a nem indított elemre nem jelezhet haladást"


def test_ha_nincs_hiba_a_kapcsolo_nem_valtoztat_semmin(harom_kep):
    (a, b, c), dest = harom_kep

    result = copy_photos([a, b, c], dest, RENAME, stop_on_failure=True)

    assert len(result.done) == 3
    assert result.failed == () and result.not_started == ()


def test_a_kapcsolo_nelkul_a_koteg_folytatja_a_hiba_utan(harom_kep, masodik_iras_hibas):
    """NEM SZABAD: a #301/#459 kötegek (húzás, menü) folytatják."""
    (a, b, c), dest = harom_kep

    result = copy_photos([a, b, c], dest, RENAME)

    assert [path for path, _ in result.done] == [a, c]
    assert [path for path, _ in result.failed] == [b]
    assert result.not_started == ()
    assert (dest / "c.jpg").exists(), "a hibás kép után a köteg megállt"


def test_athelyezes_kapcsolo_nelkul_is_folytatja(harom_kep, monkeypatch):
    (a, b, c), dest = harom_kep

    eredeti = batch_module.move_photo

    def move_photo(path, dest_folder):
        if Path(path).name == "b.jpg":
            raise OSError(13, "Permission denied")
        return eredeti(path, dest_folder)

    monkeypatch.setattr(batch_module, "move_photo", move_photo)

    result = move_photos([a, b, c], dest, RENAME)

    assert [path for path, _ in result.done] == [a, c]
    assert (dest / "c.jpg").exists()
