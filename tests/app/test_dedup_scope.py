"""#294: a duplikátum-kereső hatóköre, haladás-jelzése, megszakítása és
dHash-gyorsítótára — valódi ideiglenes könyvtárfán/indexen, mock nélkül."""

from __future__ import annotations

import os
import threading

import pytest
from PySide6.QtCore import Qt, QEventLoop, QTimer

from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache

from support.jpeg_factory import make_jpeg


def _quit_on(signal):
    loop = QEventLoop()
    signal.connect(loop.quit)
    QTimer.singleShot(5000, loop.quit)
    return loop


def _cancel_on_progress(dedup):
    """A megszakítás kiváltása a haladás-jelzésre — KÖZVETLEN kapcsolattal.

    Alapértelmezett (Auto) kapcsolattal ez a teszt versenyhelyzetes: a
    `scanProgress` a worker-szálról jön, a fogadó kontextus viszont a
    GUI-szálon élő controller, tehát a Qt SORBA ÁLLÍTJA a hívást. A
    `cancelScan()` így csak a `loop.exec()` alatt fut le — addigra a
    hat képes próbakönyvtáron a keresés már be is fejeződött, és
    `scanFinished` érkezik `scanCancelled` helyett. (A `_PROGRESS_STEP`
    = 25 ritkítás miatt egyébként is csak a fázis-záró jelzések
    mennek ki, épp a leállási ellenőrzési pontok mellett.)

    KÖZVETLEN kapcsolattal a kérés ott és akkor kerül a jelzőre, ahol a
    valóságban is hat: a worker következő ellenőrzési pontja előtt —
    ez a TERMÉK szerződése, a sorbaállítás csak a tesztkörnyezeté.

    Bizonyíték: 2026-09-01, PR #1902 CI (ubuntu 2/4) — a
    `test_cancelled_scan_emits_no_results` elbukott, miközben ugyanaz a
    kód helyben ötször zölden futott.
    """
    dedup.scanProgress.connect(
        lambda *_args: dedup.cancelScan(), Qt.DirectConnection
    )


def _duplicate_pair(folder, stem, size=(40, 20)):
    """Bitre azonos pár a mappában — biztos találat a pontos rétegben."""
    folder.mkdir(parents=True, exist_ok=True)
    original = make_jpeg(folder / f"{stem}.jpg", size=size)
    copy = folder / f"{stem}-masolat.jpg"
    copy.write_bytes(original.read_bytes())
    return original, copy


@pytest.fixture
def provider(tmp_path):
    from picasapy.app.thumbnail_provider import ThumbnailProvider

    return ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))


@pytest.fixture
def library(tmp_path):
    """Két külön ág, mindkettőben egy-egy bitre azonos pár:
    `kepek/nyar/` (+ almappa `kepek/nyar/tenger/`) és `kepek/tel/`."""
    lib = tmp_path / "kepek"
    _duplicate_pair(lib / "nyar", "nyar", size=(40, 20))
    _duplicate_pair(lib / "nyar" / "tenger", "tenger", size=(41, 21))
    _duplicate_pair(lib / "tel", "tel", size=(42, 22))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)
    return lib, db


@pytest.fixture
def dedup(qt_app, library, provider):
    """#438: a teszt végén BEVÁRJA a keresés háttérszálát (a #430 SIGSEGV-
    osztály elkerülése), amíg a controller még él."""
    from picasapy.app.dedup_controller import DedupController

    _lib, db = library
    dedup = DedupController(db, provider)
    yield dedup
    assert dedup.waitForBackgroundWorkers(30.0), "a dedup háttérszála nem állt le"


def _scan(dedup, call):
    """Egy keresés lefuttatása és a csoportok visszaadása."""
    results = []
    dedup.scanFinished.connect(results.append)
    loop = _quit_on(dedup.scanFinished)
    call()
    loop.exec()
    assert results, "scanFinished nem érkezett meg"
    return results[0]


def _paths(groups):
    return {item["path"] for group in groups for item in group["items"]}


class TestScope:
    def test_folder_scope_includes_subfolders(self, dedup, library):
        lib, _db = library
        groups = _scan(dedup, lambda: dedup.scanFolder(str(lib / "nyar")))

        found = _paths(groups)
        assert str(lib / "nyar" / "nyar-masolat.jpg") in found
        assert str(lib / "nyar" / "tenger" / "tenger-masolat.jpg") in found
        # a másik ág NEM kerülhet bele
        assert not any(path.startswith(str(lib / "tel")) for path in found)

    def test_folder_scope_excludes_other_branches(self, dedup, library):
        lib, _db = library
        groups = _scan(dedup, lambda: dedup.scanFolder(str(lib / "tel")))

        found = _paths(groups)
        assert found == {
            str(lib / "tel" / "tel.jpg"),
            str(lib / "tel" / "tel-masolat.jpg"),
        }

    def test_folder_scope_accepts_file_url(self, dedup, library):
        lib, _db = library
        groups = _scan(
            dedup, lambda: dedup.scanFolder((lib / "tel").as_uri())
        )
        assert len(_paths(groups)) == 2

    def test_empty_folder_argument_reports_a_human_error(self, dedup):
        failures = []
        dedup.scanFailed.connect(failures.append)
        dedup.scanFolder("")
        assert failures and failures[0]

    def test_library_scope_covers_every_branch(self, dedup, library):
        lib, _db = library
        groups = _scan(dedup, dedup.scanForDuplicates)

        found = _paths(groups)
        assert str(lib / "nyar" / "nyar.jpg") in found
        assert str(lib / "tel" / "tel.jpg") in found

    def test_selection_scope_only_looks_at_given_paths(self, dedup, library):
        lib, _db = library
        selection = [
            str(lib / "tel" / "tel.jpg"),
            str(lib / "tel" / "tel-masolat.jpg"),
            str(lib / "nyar" / "nyar.jpg"),
        ]
        groups = _scan(dedup, lambda: dedup.scanSelection(selection))

        found = _paths(groups)
        # a kijelölésen KÍVÜLI kép nem kerülhet találatba (a hasonlósági
        # réteg az egyszínű teszt-JPEG-eket egymáshoz közelinek látja, ezért
        # a kijelölt harmadik kép megjelenhet — a hatókört az garantálja,
        # hogy a kijelölésen kívüli képek egyike sem szerepel)
        assert found <= set(selection)
        assert {selection[0], selection[1]} <= found

    def test_selection_below_two_items_finishes_immediately(self, dedup, library):
        lib, _db = library
        groups = _scan(
            dedup, lambda: dedup.scanSelection([str(lib / "tel" / "tel.jpg")])
        )
        assert groups == []


class TestProgress:
    def test_progress_is_reported_with_a_total(self, dedup, library):
        events = []
        dedup.scanProgress.connect(
            lambda phase, done, total: events.append((phase, done, total))
        )
        _scan(dedup, dedup.scanForDuplicates)

        assert events, "haladás-jelzés nem érkezett"
        assert all(total == 6 for _phase, _done, total in events)
        assert max(done for _phase, done, _total in events) == 6

    def test_started_precedes_progress_and_finish(self, dedup, library):
        order = []
        dedup.scanStarted.connect(lambda: order.append("started"))
        dedup.scanProgress.connect(
            lambda *_args: order.append("progress")
        )
        dedup.scanFinished.connect(lambda *_args: order.append("finished"))
        _scan(dedup, dedup.scanForDuplicates)

        assert order[0] == "started"
        assert order[-1] == "finished"
        assert "progress" in order


class TestCancellation:
    def test_cancel_stops_the_scan_and_emits_cancelled(self, dedup, library):
        cancelled = threading.Event()
        dedup.scanCancelled.connect(cancelled.set)
        # a legelső haladás-jelzésre azonnal megszakítjuk
        _cancel_on_progress(dedup)

        loop = _quit_on(dedup.scanCancelled)
        dedup.scanForDuplicates()
        loop.exec()

        assert cancelled.is_set()

    def test_cancelled_scan_emits_no_results(self, dedup, library):
        finished = []
        dedup.scanFinished.connect(finished.append)
        _cancel_on_progress(dedup)

        loop = _quit_on(dedup.scanCancelled)
        dedup.scanForDuplicates()
        loop.exec()

        assert finished == []

    def test_a_new_scan_runs_after_a_cancelled_one(self, dedup, library):
        _cancel_on_progress(dedup)
        loop = _quit_on(dedup.scanCancelled)
        dedup.scanForDuplicates()
        loop.exec()

        dedup.scanProgress.disconnect()
        groups = _scan(dedup, dedup.scanForDuplicates)
        assert groups  # a megszakítás nem hagyott maradandó állapotot


class TestHashCache:
    def test_second_scan_reuses_stored_hashes(self, dedup, library, monkeypatch):
        """Ismételt keresésnél egyetlen képet sem szabad újra dekódolni —
        a lenyomatok az indexből jönnek (#294 DoD)."""
        _scan(dedup, dedup.scanForDuplicates)

        import picasapy.app.dedup_controller as module

        calls = []
        monkeypatch.setattr(
            module, "compute_dhash", lambda path: calls.append(path) or 0
        )
        _scan(dedup, dedup.scanForDuplicates)

        assert calls == []

    def test_hashes_are_persisted_in_the_index(self, dedup, library):
        lib, db = library
        _scan(dedup, dedup.scanForDuplicates)

        with open_index(db) as conn:
            stored = conn.execute("SELECT COUNT(*) FROM photo_hashes").fetchone()[0]
        assert stored == 6

    def test_changed_file_invalidates_its_cached_hash(
        self, dedup, library, monkeypatch
    ):
        lib, db = library
        _scan(dedup, dedup.scanForDuplicates)

        changed = lib / "tel" / "tel.jpg"
        make_jpeg(changed, size=(60, 30))
        # #519: a hash-gyorsítótár kulcsa (útvonal, mtime_ns, méret) — ha az
        # újraírt fájl VÉLETLENÜL ugyanakkora, és a fájlrendszer időbélyege
        # sem mozdul (Windowson a runner alatt ez előfordul), a kulcs
        # azonos maradna, és a teszt a saját környezetén bukna el, nem a
        # vizsgált viselkedésen. Az időbélyeget ezért kézzel léptetjük.
        stamp = changed.stat().st_mtime + 10
        os.utime(changed, (stamp, stamp))
        with open_index(db) as conn:
            sync_tree(conn, lib)

        import picasapy.app.dedup_controller as module

        calls = []
        real = module.compute_dhash

        def spy(path):
            calls.append(str(path))
            return real(path)

        monkeypatch.setattr(module, "compute_dhash", spy)
        _scan(dedup, dedup.scanForDuplicates)

        assert calls == [str(changed)]
