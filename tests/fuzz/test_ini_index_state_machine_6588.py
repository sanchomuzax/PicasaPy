"""Véletlen műveletsorok az ini és az SQLite index egyezésére (#6588)."""

from __future__ import annotations

import os
import tempfile
from collections import Counter
from dataclasses import fields
from pathlib import Path

import cv2
import numpy as np
import pytest
from hypothesis import HealthCheck, example, given, settings, strategies as st
from hypothesis.stateful import (
    RuleBasedStateMachine,
    invariant,
    precondition,
    rule,
    run_state_machine_as_test,
)

from picasapy.edit.edit_journal import (
    detect_lost_edits,
    load_journal,
    record_saved_chain,
    save_journal,
)
from picasapy.edit.session import EditSession
from picasapy.fileops import (
    copy_photo,
    copy_photos,
    create_folder_for_move,
    move_folder,
    move_photo,
    move_photos,
    rename_folder,
)
from picasapy.index import (
    album_photos,
    albums_in_index,
    all_photos,
    move_folder_tree,
    open_index,
    sync_folder,
    sync_tree,
)
from picasapy.ini import (
    load_document,
    parse_document,
    save_document,
    update_document,
)
from picasapy.ini.albums import ensure_album, with_album, without_album

_ALBUM_TOKEN = "state-machine-6588"
_NOT_REBUILT_PHOTO_FIELDS = {
    "id",
    "first_seen_mtime_ns",
    "face_count",
    "unnamed_face_count",
}
_PROFILE = os.environ.get("PICASAPY_FUZZ_PROFIL", "ci")


def _stateful_settings():
    """A közös fuzzprofilra épülő, a géphez mért futásméret."""
    ci_profile = _PROFILE == "ci"
    return settings(
        max_examples=8 if ci_profile else 24,
        stateful_step_count=10 if ci_profile else 30,
        deadline=None,
        # A gép saját TemporaryDirectory-t használ, nincs fixture, amit
        # Hypothesisnek el kellene némítania.
        suppress_health_check=[],
    )


def _photo_bytes(seed: int) -> bytes:
    image = np.full((3, 4, 3), seed % 256, dtype=np.uint8)
    ok, encoded = cv2.imencode(".png", image)
    assert ok
    return encoded.tobytes()


def _write_photo(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _media_files(root: Path) -> tuple[Path, ...]:
    return tuple(sorted(path for path in root.rglob("*.png") if path.is_file()))


def _section_header(line: bytes) -> str | None:
    content = line.rstrip(b"\r\n")
    if content.startswith(b"\xef\xbb\xbf"):
        content = content[3:]
    if content.startswith(b"[") and content.endswith(b"]"):
        return content[1:-1].decode("utf-8", errors="replace")
    return None


def _outside_section(raw: bytes, name: str) -> bytes:
    return _outside_sections(raw, {name})


def _outside_sections(raw: bytes, names: set[str]) -> bytes:
    """A megadott ini-szakaszokon kívüli sorokat bájtra pontosan adja vissza."""
    excluded = {name.casefold() for name in names}
    kept: list[bytes] = []
    keep = True
    for line in raw.splitlines(keepends=True):
        header = _section_header(line)
        if header is not None:
            keep = header.casefold() not in excluded
        if keep:
            kept.append(line)
    return b"".join(kept)


def _index_photo_state(connection) -> tuple[tuple[object, ...], ...]:
    """A friss szkennelésben nem rekonstruálható helyi/előzmény mezők nélkül."""
    return tuple(
        tuple(
            getattr(photo, field.name)
            for field in fields(photo)
            if field.name not in _NOT_REBUILT_PHOTO_FIELDS
        )
        for photo in all_photos(connection, include_hidden_folders=True)
    )


def _album_state(connection) -> tuple[tuple[object, ...], ...]:
    return tuple(
        (
            album.token,
            album.name,
            album.date,
            album.photo_count,
            tuple(
                (photo.folder_path, photo.name)
                for photo in album_photos(connection, album.token)
            ),
        )
        for album in albums_in_index(connection)
    )


class _IniIndexMachine(RuleBasedStateMachine):
    """A termék API-ját használja; a teszt és a gép nem ír ini-t közvetlenül."""

    def __init__(self):
        super().__init__()
        self._temporary_directory = tempfile.TemporaryDirectory(
            prefix="picasapy-state-machine-6588-"
        )
        self.root = Path(self._temporary_directory.name) / "library"
        self.root.mkdir()
        self.index_context = open_index(self.root / "index.sqlite")
        self.connection = self.index_context.__enter__()
        self.journal_path = self.root / "edit-journal.json"
        self.journal = {}
        self.sessions: dict[Path, EditSession] = {}
        self.undo_before: dict[Path, tuple[bytes, str | None]] = {}
        self.folder_number = 0
        self.photo_number = 0
        self.expected_payloads: Counter[bytes] = Counter()

        first = create_folder_for_move(self.root, "Album A")
        second = create_folder_for_move(self.root, "Album B")
        for folder, name, seed in (
            (first, "A-1.png", 31),
            (first, "A-2.png", 47),
            (second, "B-1.png", 83),
        ):
            payload = _photo_bytes(seed)
            _write_photo(folder / name, payload)
            self.expected_payloads[payload] += 1
        first_ini = parse_document(
            "[A-1.png]\r\nstar=no\r\ncaption=Alap A1\r\nunknown=keep-a1\r\n"
            "[A-2.png]\r\nstar=no\r\ncaption=Alap A2\r\nunknown=keep-a2\r\n"
        )
        first_ini = ensure_album(first_ini, _ALBUM_TOKEN, "Állapotgép")
        first_ini = with_album(first_ini, "A-1.png", _ALBUM_TOKEN)
        save_document(first_ini, first / ".picasa.ini")
        second_ini = parse_document(
            "[B-1.png]\r\nstar=no\r\ncaption=Alap B1\r\nunknown=keep-b1\r\n"
        )
        save_document(second_ini, second / ".picasa.ini")
        sync_tree(self.connection, self.root)

    def teardown(self) -> None:
        try:
            self.index_context.__exit__(None, None, None)
        finally:
            self._temporary_directory.cleanup()

    def _photos(self) -> tuple[Path, ...]:
        return _media_files(self.root)

    def _choose_photo(self, selection: int) -> Path | None:
        photos = self._photos()
        return photos[selection % len(photos)] if photos else None

    def _folders(self) -> tuple[Path, ...]:
        return tuple(sorted(path for path in self.root.rglob("*") if path.is_dir()))

    def _current_chain(self, photo: Path) -> str | None:
        ini_path = photo.parent / ".picasa.ini"
        if not ini_path.exists():
            return None
        section = load_document(ini_path).section(photo.name)
        return None if section is None else section.get("filters")

    def _persist_journal(self, photo: Path, chain: str) -> None:
        self.journal = record_saved_chain(
            self.journal, str(photo), chain, saved_at="2026-11-05T00:00:00"
        )
        save_journal(self.journal, self.journal_path)
        self.journal = load_journal(self.journal_path)

    def _relocate_journal(self, old_root: Path, new_root: Path) -> None:
        for entry in tuple(self.journal.values()):
            old_photo = Path(entry.path)
            if not old_photo.is_relative_to(old_root):
                continue
            new_photo = new_root / old_photo.relative_to(old_root)
            self.journal = record_saved_chain(
                self.journal, str(old_photo), "", saved_at="2026-11-05T00:00:00"
            )
            self.journal = record_saved_chain(
                self.journal,
                str(new_photo),
                entry.chain,
                saved_at="2026-11-05T00:00:00",
            )
        save_journal(self.journal, self.journal_path)
        self.journal = load_journal(self.journal_path)

    def _sync_folders(self, *folders: Path) -> None:
        for folder in dict.fromkeys(folders):
            sync_folder(self.connection, self.root, folder)

    def _assert_index_matches_rebuild(self) -> None:
        with open_index(":memory:") as rebuilt:
            sync_tree(rebuilt, self.root)
            actual_photos = _index_photo_state(self.connection)
            rebuilt_photos = _index_photo_state(rebuilt)
            assert actual_photos == rebuilt_photos, (
                "Az inkrementális index eltér a .picasa.ini-kből és a fájlokból "
                "újraépített indextől."
            )
            actual_folders = tuple(
                row[0]
                for row in self.connection.execute("SELECT path FROM folders ORDER BY path")
            )
            rebuilt_folders = tuple(
                row[0] for row in rebuilt.execute("SELECT path FROM folders ORDER BY path")
            )
            assert actual_folders == rebuilt_folders, (
                "Az inkrementális és az újraépített index mappái eltérnek."
            )
            assert _album_state(self.connection) == _album_state(rebuilt), (
                "Az inkrementális és az újraépített index albumai eltérnek."
            )

    def _assert_files_and_ini(self) -> None:
        photos = self._photos()
        actual_payloads = Counter(path.read_bytes() for path in photos)
        assert actual_payloads == self.expected_payloads, "A műveletsor képet veszített."

        for ini_path in self.root.rglob(".picasa.ini"):
            document = load_document(ini_path)
            present_names = {
                path.name for path in ini_path.parent.iterdir() if path.suffix.casefold() == ".png"
            }
            orphaned = [
                section.name
                for section in document.file_sections()
                if section.name not in present_names
            ]
            assert not orphaned, f"Árva ini-szakasz {ini_path}: {orphaned}"

    @invariant()
    def ini_index_and_files_remain_consistent(self) -> None:
        self._assert_files_and_ini()
        self._assert_index_matches_rebuild()

    @rule(selection=st.integers())
    def toggle_red_eye_filter_in_edit_session(self, selection: int) -> None:
        photo = self._choose_photo(selection)
        if photo is None:
            return
        session = self.sessions.get(photo)
        if session is None:
            session = EditSession.from_value(self._current_chain(photo))
        self.sessions[photo] = session.toggle("redeye")

    @rule(selection=st.integers())
    def save_filter_session_and_journal(self, selection: int) -> None:
        photo = self._choose_photo(selection)
        if photo is None:
            return
        session = self.sessions.get(photo, EditSession.from_value(self._current_chain(photo)))
        ini_path = photo.parent / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else b""
        previous = self._current_chain(photo)
        chain = session.to_value()

        def save_chain(document):
            if chain:
                return document.with_value(photo.name, "filters", chain)
            return document.with_removed(photo.name, "filters")

        update_document(ini_path, save_chain)
        after = ini_path.read_bytes()
        assert _outside_section(before, photo.name) == _outside_section(after, photo.name)
        self.undo_before[photo] = (before, previous)
        self._persist_journal(photo, chain)
        self.sessions[photo] = EditSession.from_value(chain)
        self._sync_folders(photo.parent)

    @precondition(lambda self: bool(self.undo_before))
    @rule(selection=st.integers())
    def undo_last_filter_save(self, selection: int) -> None:
        photos = tuple(self.undo_before)
        photo = photos[selection % len(photos)]
        before_bytes, previous_chain = self.undo_before.pop(photo)
        ini_path = photo.parent / ".picasa.ini"

        def restore_chain(document):
            if previous_chain:
                return document.with_value(
                    photo.name, "filters", previous_chain, carried=True
                )
            return document.with_removed(photo.name, "filters")

        update_document(ini_path, restore_chain)
        assert ini_path.read_bytes() == before_bytes
        self._persist_journal(photo, previous_chain or "")
        self.sessions[photo] = EditSession.from_value(previous_chain)
        self._sync_folders(photo.parent)

    @rule(selection=st.integers(), starred=st.booleans(), caption=st.sampled_from(
        ("Tópart", "Kék ég", "Őszi fény", "")))
    def edit_star_and_caption(self, selection: int, starred: bool, caption: str) -> None:
        photo = self._choose_photo(selection)
        if photo is None:
            return
        ini_path = photo.parent / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else b""

        def update_metadata(document):
            return document.with_value(photo.name, "star", "yes" if starred else "no").with_value(
                photo.name, "caption", caption
            )

        update_document(ini_path, update_metadata)
        assert _outside_section(before, photo.name) == _outside_section(
            ini_path.read_bytes(), photo.name
        )
        self.undo_before.pop(photo, None)
        self._sync_folders(photo.parent)

    @rule(selection=st.integers(), add=st.booleans())
    def change_album_membership(self, selection: int, add: bool) -> None:
        photo = self._choose_photo(selection)
        if photo is None:
            return
        ini_path = photo.parent / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else b""

        def update_membership(document):
            document = ensure_album(document, _ALBUM_TOKEN, "Állapotgép")
            if add:
                return with_album(document, photo.name, _ALBUM_TOKEN)
            return without_album(document, photo.name, _ALBUM_TOKEN)

        update_document(ini_path, update_membership)
        assert _outside_sections(
            before, {photo.name, f".album:{_ALBUM_TOKEN}"}
        ) == _outside_sections(
            ini_path.read_bytes(), {photo.name, f".album:{_ALBUM_TOKEN}"}
        )
        self.undo_before.pop(photo, None)
        self._sync_folders(photo.parent)

    @rule(selection=st.integers(), caption=st.sampled_from(
        ("Másik gépről", "Picasa módosítás", "Külső felirat", "")),
        drop_filters=st.booleans())
    def external_ini_edit(self, selection: int, caption: str, drop_filters: bool) -> None:
        photo = self._choose_photo(selection)
        if photo is None:
            return
        ini_path = photo.parent / ".picasa.ini"
        before = ini_path.read_bytes() if ini_path.exists() else b""

        def foreign_edit(document):
            document = document.with_value(photo.name, "caption", caption)
            if drop_filters:
                return document.with_removed(photo.name, "filters")
            return document

        update_document(ini_path, foreign_edit)
        assert _outside_section(before, photo.name) == _outside_section(
            ini_path.read_bytes(), photo.name
        )
        self.undo_before.pop(photo, None)
        self.sessions.pop(photo, None)
        self._sync_folders(photo.parent)

    @rule(selection=st.integers())
    def restore_lost_saved_filter_from_journal(self, selection: int) -> None:
        photos = tuple(
            Path(entry.path)
            for entry in self.journal.values()
            if Path(entry.path).is_file()
        )
        if not photos:
            return
        photo = photos[selection % len(photos)]
        current = self._current_chain(photo) or ""
        lost = detect_lost_edits(self.journal, {str(photo): current})
        if not lost:
            return
        entry = next(item for item in lost if item.path == str(photo))
        ini_path = photo.parent / ".picasa.ini"
        before = ini_path.read_bytes()
        update_document(
            ini_path,
            lambda document: document.with_value(
                photo.name, "filters", entry.chain, carried=True
            ),
        )
        assert _outside_section(before, photo.name) == _outside_section(
            ini_path.read_bytes(), photo.name
        )
        self._sync_folders(photo.parent)

    @rule(selection=st.integers())
    def copy_a_photo(self, selection: int) -> None:
        photos = self._photos()
        if not photos or len(photos) >= 16:
            return
        source = photos[selection % len(photos)]
        folders = tuple(folder for folder in self._folders() if folder != source.parent)
        if not folders:
            return
        destination = folders[selection % len(folders)]
        source_ini = source.parent / ".picasa.ini"
        source_bytes = source_ini.read_bytes() if source_ini.exists() else None
        destination_ini = destination / ".picasa.ini"
        destination_before = destination_ini.read_bytes() if destination_ini.exists() else b""
        new_photo = copy_photo(source, destination)
        self.expected_payloads[new_photo.read_bytes()] += 1
        if source_bytes is not None:
            assert source_ini.read_bytes() == source_bytes
        if destination_before:
            assert _outside_section(destination_before, new_photo.name) == _outside_section(
                destination_ini.read_bytes(), new_photo.name
            )
        chain = self._current_chain(new_photo)
        if chain:
            self._persist_journal(new_photo, chain)
        self.sessions.clear()
        self.undo_before.clear()
        self._sync_folders(source.parent, destination)

    @rule(selection=st.integers())
    def move_a_photo(self, selection: int) -> None:
        photos = self._photos()
        if len(photos) < 1:
            return
        candidates = [
            (source, destination)
            for source in photos
            for destination in self._folders()
            if destination != source.parent and not (destination / source.name).exists()
        ]
        if not candidates:
            return
        source, destination = candidates[selection % len(candidates)]
        source_ini = source.parent / ".picasa.ini"
        destination_ini = destination / ".picasa.ini"
        source_before = source_ini.read_bytes() if source_ini.exists() else b""
        destination_before = destination_ini.read_bytes() if destination_ini.exists() else b""
        chain = self._current_chain(source) or ""
        old_path = source
        new_path = move_photo(source, destination)
        assert not old_path.exists() and new_path.exists()
        if source_before:
            assert _outside_section(source_before, old_path.name) == _outside_section(
                source_ini.read_bytes(), old_path.name
            )
        if destination_before:
            assert _outside_section(destination_before, new_path.name) == _outside_section(
                destination_ini.read_bytes(), new_path.name
            )
        self._persist_journal(old_path, "")
        if chain:
            self._persist_journal(new_path, chain)
        self.sessions.clear()
        self.undo_before.clear()
        self._sync_folders(old_path.parent, new_path.parent)

    @rule(selection=st.integers(), move=st.booleans())
    def batch_copy_or_move_a_photo(self, selection: int, move: bool) -> None:
        photos = self._photos()
        if not photos or (not move and len(photos) >= 16):
            return
        source = photos[selection % len(photos)]
        destinations = tuple(folder for folder in self._folders() if folder != source.parent)
        if not destinations:
            return
        destination = destinations[selection % len(destinations)]
        if move and (destination / source.name).exists():
            return
        source_ini = source.parent / ".picasa.ini"
        destination_ini = destination / ".picasa.ini"
        source_before = source_ini.read_bytes() if source_ini.exists() else b""
        destination_before = destination_ini.read_bytes() if destination_ini.exists() else b""
        chain = self._current_chain(source) or ""
        result = (
            move_photos([source], destination)
            if move
            else copy_photos([source], destination)
        )
        if not result.done:
            return
        old_path, new_path = result.done[0]
        if move:
            assert not old_path.exists() and new_path.exists()
            self._persist_journal(old_path, "")
            if chain:
                self._persist_journal(new_path, chain)
        else:
            assert old_path.exists() and new_path.exists()
            self.expected_payloads[new_path.read_bytes()] += 1
            if chain:
                self._persist_journal(new_path, chain)
        if source_before:
            assert _outside_section(source_before, old_path.name) == _outside_section(
                source_ini.read_bytes(), old_path.name
            )
        if destination_before:
            assert _outside_section(destination_before, new_path.name) == _outside_section(
                destination_ini.read_bytes(), new_path.name
            )
        self.sessions.clear()
        self.undo_before.clear()
        self._sync_folders(old_path.parent, new_path.parent)

    @rule()
    def create_a_new_folder(self) -> None:
        self.folder_number += 1
        folder = create_folder_for_move(self.root, f"Új mappa {self.folder_number}")
        self._sync_folders(folder)

    @rule(selection=st.integers())
    def rename_a_folder(self, selection: int) -> None:
        folders = tuple(folder for folder in self._folders() if folder != self.root)
        if not folders:
            return
        source = folders[selection % len(folders)]
        destination_name = f"Átnevezett {self.folder_number + 1}"
        self.folder_number += 1
        old_files = {
            path.relative_to(source): path.read_bytes()
            for path in source.rglob("*")
            if path.is_file()
        }
        new_root = rename_folder(source, destination_name)
        move_folder_tree(self.connection, source, new_root)
        self._relocate_journal(source, new_root)
        self.sessions.clear()
        self.undo_before.clear()
        self._sync_folders(new_root.parent, new_root)
        assert {
            path.relative_to(new_root): path.read_bytes()
            for path in new_root.rglob("*")
            if path.is_file()
        } == old_files

    @rule(selection=st.integers())
    def move_a_folder(self, selection: int) -> None:
        nested = tuple(
            folder
            for folder in self._folders()
            if folder != self.root and folder.parent != self.root
        )
        if not nested:
            self.folder_number += 1
            container = create_folder_for_move(self.root, f"Konténer {self.folder_number}")
            nested = (
                create_folder_for_move(container, f"Belső {self.folder_number}"),
            )
        source = nested[selection % len(nested)]
        old_parent = source.parent
        old_files = {
            path.relative_to(source): path.read_bytes()
            for path in source.rglob("*")
            if path.is_file()
        }
        new_root = move_folder(source, self.root)
        move_folder_tree(self.connection, source, new_root)
        self._relocate_journal(source, new_root)
        self.sessions.clear()
        self.undo_before.clear()
        self._sync_folders(old_parent, new_root.parent, new_root)
        assert {
            path.relative_to(new_root): path.read_bytes()
            for path in new_root.rglob("*")
            if path.is_file()
        } == old_files

    @rule(selection=st.integers())
    def sync_one_folder(self, selection: int) -> None:
        folders = self._folders()
        if folders:
            sync_folder(self.connection, self.root, folders[selection % len(folders)])

    @rule()
    def sync_the_full_tree(self) -> None:
        sync_tree(self.connection, self.root)


def test_ini_index_state_machine_6588() -> None:
    run_state_machine_as_test(
        _IniIndexMachine,
        settings=_stateful_settings(),
    )


def test_album_copy_then_source_rename_regression_example() -> None:
    """A #6599 és #6608 minimalizált sorozata külön Hypothesis-példa."""

    @example(sequence="6599")
    @example(sequence="6608")
    @given(sequence=st.sampled_from(("6599", "6608")))
    @_stateful_settings()
    def run_regression_sequence(sequence: str) -> None:
        machine = _IniIndexMachine()
        try:
            if sequence == "6599":
                operations = (
                    (machine.copy_a_photo, 0),
                    (machine.rename_a_folder, 0),
                )
            else:
                operations = (
                    (machine.move_a_photo, 0),
                    (machine.move_a_photo, 0),
                    (machine.copy_a_photo, 0),
                )
            for operation, selection in operations:
                operation(selection)
                machine.ini_index_and_files_remain_consistent()
        finally:
            machine.teardown()

    run_regression_sequence()


def test_fuzz_profile_uses_picasapy_fuzz_profil() -> None:
    expected_profile = os.environ.get("PICASAPY_FUZZ_PROFIL", "ci")
    assert _PROFILE == expected_profile
    assert settings.default.max_examples == {"ci": 100, "ejszakai": 20_000}[
        expected_profile
    ]
    stateful_settings = _stateful_settings()
    assert stateful_settings.max_examples == {"ci": 8, "ejszakai": 24}[
        expected_profile
    ]
    assert stateful_settings.stateful_step_count == {"ci": 10, "ejszakai": 30}[
        expected_profile
    ]
    assert HealthCheck.function_scoped_fixture not in stateful_settings.suppress_health_check


def test_index_oracle_catches_a_missing_incremental_sync() -> None:
    machine = _IniIndexMachine()
    try:
        folder = next(folder for folder in machine._folders() if folder != machine.root)
        payload = _photo_bytes(229)
        _write_photo(folder / "unsynced.png", payload)
        machine.expected_payloads[payload] += 1

        with pytest.raises(AssertionError, match="inkrementális index eltér"):
            machine._assert_index_matches_rebuild()
    finally:
        machine.teardown()
