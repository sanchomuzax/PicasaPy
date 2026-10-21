"""#5435: a név-javaslatok leütésenként csak a memóriabeli cache-t olvassák."""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings, Signal

from support.jpeg_factory import make_jpeg

_RECT = "3f840000c3509f84"


class _HostFactory:
    @staticmethod
    def create(db_path):
        from picasapy.app.people_controller import PeopleMixin

        class _Host(PeopleMixin, QObject):
            syncFailed = Signal(str)

            def __init__(self):
                super().__init__()
                self._db_path = Path(db_path)
                self._view_mode = ("folder", "")
                self._filter_active = False
                self._filter_status = ""
                self._shown = ()
                self._people = ()
                self._init_people()

            def _get_settings(self):
                return QSettings(
                    str(self._db_path.parent / "settings.ini"),
                    QSettings.Format.IniFormat,
                )

            def _show(self, records):
                self._shown = records

            def _reload_after_sync(self):
                pass

        return _Host()


def _large_real_library(root: Path) -> Path:
    """1000 valódi fájlbejegyzés 30 mappában, SQLite-indexszel és ini-kkel."""
    from picasapy.index import open_index, sync_tree

    root.mkdir()
    image_source = root / "seed.jpg"
    make_jpeg(image_source)
    image_bytes = image_source.read_bytes()
    image_source.unlink()

    photo_total = 1000
    folder_total = 30
    with open_index(root / "index.db") as conn:
        for folder_index in range(folder_total):
            folder = root / f"folder-{folder_index:02d}"
            folder.mkdir()
            name = f"Person {folder_index:02d}"
            person_id = f"{folder_index + 1:016x}"
            photo_names = []
            for photo_index in range(folder_index, photo_total, folder_total):
                photo_name = f"photo-{photo_index:04d}.jpg"
                (folder / photo_name).write_bytes(image_bytes)
                photo_names.append(photo_name)
            ini_lines = ["[Contacts2]", f"{person_id}={name};;"]
            for photo_name in photo_names:
                ini_lines.extend(
                    [f"[{photo_name}]", f"faces=rect64({_RECT}),{person_id};"]
                )
            (folder / ".picasa.ini").write_text(
                "\n".join(ini_lines) + "\n", encoding="utf-8"
            )
            sync_tree(conn, folder)
        conn.commit()
    return root / "index.db"


@pytest.fixture
def large_host(tmp_path):
    db_path = _large_real_library(tmp_path / "library")
    return _HostFactory.create(db_path)


@pytest.fixture
def small_host(tmp_path):
    from picasapy.index import open_index, sync_tree

    folder = tmp_path / "kepek"
    folder.mkdir()
    make_jpeg(folder / "one.jpg")
    person_id = "b8e4117cf1d6615b"
    (folder / ".picasa.ini").write_text(
        f"[Contacts2]\n{person_id}=Roy Avery;;\n"
        f"[one.jpg]\nfaces=rect64({_RECT}),{person_id};\n",
        encoding="utf-8",
    )
    db_path = tmp_path / "index.db"
    with open_index(db_path) as conn:
        sync_tree(conn, folder)
    return _HostFactory.create(db_path)


def test_a_leutesenkenti_szures_valodi_nagy_tarolon_io_nelkul_20_ms_alatt(
    large_host,
):
    large_host.prepareNameSuggestions()

    audit_enabled = True
    io_events = []

    def audit(event, args):
        if audit_enabled and event in {
            "open",
            "sqlite3.connect",
            "os.listdir",
            "os.scandir",
        }:
            io_events.append((event, args))

    sys.addaudithook(audit)
    try:
        started = time.perf_counter()
        matches = large_host.nameSuggestions("Person 2")
        elapsed_ms = (time.perf_counter() - started) * 1000
    finally:
        audit_enabled = False

    assert len(matches) == 10
    assert [row["name"] for row in matches] == [
        f"Person {index:02d}" for index in range(20, 30)
    ]
    assert not io_events, f"a leütés alatti szűrés tároló-I/O-t végzett: {io_events}"
    assert elapsed_ms < 20, f"a szűrés {elapsed_ms:.2f} ms volt"


def test_a_nevjegy_letrehozasa_atnevezese_es_torlese_utan_friss_a_cache(
    small_host,
):
    small_host.prepareNameSuggestions()
    assert [row["name"] for row in small_host.nameSuggestions("Roy")] == [
        "Roy Avery"
    ]

    assert small_host.savePeopleManagerChanges(
        [{"action": "update", "oldName": "Roy Avery", "name": "Royal Avery"}]
    )
    assert [row["name"] for row in small_host.nameSuggestions("Royal")] == [
        "Royal Avery"
    ]
    assert small_host.savePeopleManagerChanges(
        [{"action": "delete", "oldName": "Royal Avery"}]
    )
    assert small_host.nameSuggestions("Royal") == []
    assert small_host.savePeopleManagerChanges(
        [{"action": "create", "name": "New Person"}]
    )
    assert [row["name"] for row in small_host.nameSuggestions("New")] == [
        "New Person"
    ]
