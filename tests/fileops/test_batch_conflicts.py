"""Kötegelt másolás/áthelyezés névütközéssel — #457, 2. pont.

Az eredeti Picasa ütközéskor MEGKÉRDEZTE a felhasználót („Másodpéldányok
átnevezése" / „Másodpéldányok kihagyása"), és ugyanezt a párbeszédet adta
másolásra és áthelyezésre is. Itt a döntés VÉGREHAJTÁSÁT ellenőrizzük.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.fileops.batch import (
    RENAME,
    SKIP,
    conflicting_names,
    copy_photos,
    move_photos,
)
from picasapy.scanner import PICASA_INI_NAME


def _photo(folder: Path, name: str, content: bytes = b"kep") -> Path:
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(content)
    return path


def test_conflicting_names_only_lists_collisions(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg")
    b = _photo(src, "b.jpg")
    _photo(dest, "a.jpg")

    assert conflicting_names([a, b], dest) == (a,)


def test_no_conflict_means_no_question(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg")
    dest.mkdir()

    assert conflicting_names([a], dest) == ()


def test_copy_rename_keeps_both_files(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    _photo(dest, "a.jpg", b"regi")

    result = copy_photos([a], dest, RENAME)

    assert (dest / "a.jpg").read_bytes() == b"regi"  # a meglévőt SOHA nem írjuk felül
    assert (dest / "a-1.jpg").read_bytes() == b"uj"
    assert result.done == ((a, dest / "a-1.jpg"),)
    assert result.skipped == () and result.failed == ()
    assert a.exists()  # a másolás forrása megmarad


def test_copy_skip_leaves_target_untouched(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    b = _photo(src, "b.jpg", b"uj-b")
    _photo(dest, "a.jpg", b"regi")

    result = copy_photos([a, b], dest, SKIP)

    assert (dest / "a.jpg").read_bytes() == b"regi"
    assert not (dest / "a-1.jpg").exists()
    assert (dest / "b.jpg").read_bytes() == b"uj-b"  # a nem ütköző átmegy
    assert result.skipped == (a,)
    assert result.done == ((b, dest / "b.jpg"),)


def test_move_rename_moves_source_away(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    _photo(dest, "a.jpg", b"regi")

    result = move_photos([a], dest, RENAME)

    assert not a.exists()  # az áthelyezés forrása eltűnik
    assert not (src / "a-1.jpg").exists()  # az átnevezés csak átmeneti volt
    assert (dest / "a.jpg").read_bytes() == b"regi"
    assert (dest / "a-1.jpg").read_bytes() == b"uj"
    assert result.done == ((a, dest / "a-1.jpg"),)


def test_move_rename_carries_the_ini_section(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    (src / PICASA_INI_NAME).write_text(
        "[a.jpg]\nstar=yes\ncaption=Nyar\n", encoding="utf-8"
    )
    _photo(dest, "a.jpg", b"regi")

    move_photos([a], dest, RENAME)

    dest_ini = (dest / PICASA_INI_NAME).read_text(encoding="utf-8")
    assert "[a-1.jpg]" in dest_ini  # a szekció a fájllal együtt új nevet kap
    assert "star=yes" in dest_ini and "caption=Nyar" in dest_ini
    assert "[a.jpg]" not in (src / PICASA_INI_NAME).read_text(encoding="utf-8")


def test_move_skip_keeps_the_source(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    _photo(dest, "a.jpg", b"regi")

    result = move_photos([a], dest, SKIP)

    assert a.read_bytes() == b"uj"  # kihagyva = érintetlenül a helyén marad
    assert (dest / "a.jpg").read_bytes() == b"regi"
    assert result.skipped == (a,) and result.done == ()


def test_rename_does_not_clobber_a_sibling_in_the_source(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    a = _photo(src, "a.jpg", b"uj")
    sibling = _photo(src, "a-1.jpg", b"testver")
    _photo(dest, "a.jpg", b"regi")

    move_photos([a], dest, RENAME)

    assert sibling.read_bytes() == b"testver"  # a testvért nem üthetjük el
    assert (dest / "a-2.jpg").read_bytes() == b"uj"


def test_one_bad_file_does_not_stop_the_batch(tmp_path):
    src, dest = tmp_path / "src", tmp_path / "dest"
    missing = src / "nincs.jpg"
    good = _photo(src, "b.jpg", b"jo")
    dest.mkdir()

    result = copy_photos([missing, good], dest, RENAME)

    assert result.done == ((good, dest / "b.jpg"),)
    assert [path for path, _ in result.failed] == [missing]
    assert result.failed[0][1]  # a hiba OKA is megmarad az összegzéshez


def test_unknown_policy_is_refused(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()

    with pytest.raises(ValueError):
        copy_photos([], dest, "overwrite")


def test_empty_selection_is_a_no_op(tmp_path):
    dest = tmp_path / "dest"
    dest.mkdir()

    assert copy_photos([], dest).done == ()
    assert move_photos([], dest).skipped == ()


class TestProgressReporting:
    """#457: az eredeti SZÁMLÁLÓT mutatott a hosszú műveletek alatt
    („Copying %1$d of %2$d files"), nem csak egy pörgő sávot."""

    def test_it_counts_every_file(self, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        paths = [_photo(src, name) for name in ("a.jpg", "b.jpg", "c.jpg")]
        dest.mkdir()
        seen = []

        copy_photos(paths, dest, RENAME, lambda d, t: seen.append((d, t)))

        assert seen == [(1, 3), (2, 3), (3, 3)]

    def test_a_skipped_file_still_advances_the_counter(self, tmp_path):
        """A felhasználó azt akarja tudni, hol tart a művelet — nem azt,
        hány fájl sikerült."""
        src, dest = tmp_path / "src", tmp_path / "dest"
        paths = [_photo(src, name) for name in ("a.jpg", "b.jpg")]
        _photo(dest, "a.jpg")
        seen = []

        result = copy_photos(paths, dest, SKIP, lambda d, t: seen.append((d, t)))

        assert len(result.skipped) == 1
        assert seen == [(1, 2), (2, 2)]

    def test_progress_is_optional(self, tmp_path):
        src, dest = tmp_path / "src", tmp_path / "dest"
        paths = [_photo(src, "a.jpg")]
        dest.mkdir()

        assert len(copy_photos(paths, dest, RENAME).done) == 1
