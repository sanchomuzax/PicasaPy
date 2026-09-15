"""RelocateController (#368) — a `picasapy.index.relocate` mag QML-hídja.

Valódi ideiglenes forrás- és cél-mappával, mock nélkül (a
`test_dedup_controller.py`/`test_import_source_controller.py` mintája)."""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.app.data_location import read_data_root
from picasapy.app.relocate_controller import RelocateController
from picasapy.index import open_index, sync_tree
from support.qt_wait import hangos_hurok


def _quit_on(signal, timeout_ms: int = 5000):
    """Eseményhurok, amit a `signal` érkezése zár le — HANGOS vészfékkel.

    ⚠️ #2313 óta a segéd `.lejart` mezőben JELEZTE az időtúllépést — de
    #1467-ben mérve **egyetlen hívó sem olvasta el** (hat várakozási hely,
    nulla ellenőrzés). A vészfék tehát a javítás után is néma maradt: az
    időtúllépés ugyanúgy egy későbbi, látszólag független állításon
    bukott. A közös segéd ezért nem MEZŐT ad, hanem az `exec()`-ben,
    ott helyben bukik — kihagyni nem lehet."""
    return hangos_hurok(signal, timeout_ms=timeout_ms)


def _make_source(tmp_path):
    old_data = tmp_path / "old-data"
    old_data.mkdir()
    old_cache = tmp_path / "old-cache" / "thumbs"
    old_cache.mkdir(parents=True)
    (old_cache / "x.jpg").write_bytes(b"thumb")

    photos = tmp_path / "fotok"
    photos.mkdir()
    (photos / "a.jpg").write_bytes(b"\xff\xd8\xff\xe0" + b"0" * 50)
    index_db = old_data / "index.db"
    with open_index(index_db) as conn:
        sync_tree(conn, photos)
    return index_db, old_cache


@pytest.fixture
def source(tmp_path):
    return _make_source(tmp_path)


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"


@pytest.fixture
def controller(qt_app, source, config_dir):
    """#438: a teszt végén BEVÁRJA a háttérszálat (a #430 SIGSEGV-osztály
    elkerülése), amíg a controller még él."""
    index_db, cache_dir = source
    ctl = RelocateController(index_db, cache_dir, config_dir)
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "az áthelyezés háttérszála nem állt le"


class TestCurrentLocation:
    def test_reports_index_database_folder(self, controller, source):
        index_db, _cache_dir = source
        assert controller.currentLocation == str(index_db.parent)


class TestStartRelocate:
    def test_missing_destination_emits_failure(self, controller):
        # üres cél esetén a hiba SZINKRON (a háttérszál elindítása előtt)
        # jön — nincs mire várni, az `_quit_on`-os loop csak feleslegesen
        # kivárná a saját időtúllépését
        seen = []
        controller.relocateFailed.connect(seen.append)
        controller.startRelocate("")
        assert seen

    def test_successful_relocation_emits_finished_and_writes_override(
        self, controller, source, config_dir, tmp_path
    ):
        index_db, cache_dir = source
        new_root = tmp_path / "uj-hely"

        finished = []
        controller.relocateFinished.connect(finished.append)
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(new_root))
        loop.exec()

        assert finished == [str(new_root)]
        assert not index_db.exists()
        assert not cache_dir.exists()
        assert (new_root / "index.db").exists()
        assert (new_root / "thumbs" / "x.jpg").exists()
        assert read_data_root(config_dir) == new_root

    def test_new_database_has_the_original_photo(
        self, controller, tmp_path
    ):
        new_root = tmp_path / "uj-hely"
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(new_root))
        loop.exec()

        conn = sqlite3.connect(str(new_root / "index.db"))
        try:
            count = conn.execute("SELECT COUNT(*) FROM photos").fetchone()[0]
        finally:
            conn.close()
        assert count == 1

    def test_progress_signal_reports_phases(self, controller, tmp_path, qt_app):
        """A haladás-jelzés a `done` fázissal zárul.

        ⚠️ #2313: a próba a `done` FÁZISRA vár, nem a `relocateFinished`-re.
        A kettő sorrendje a kódból egyértelmű (`relocate.py`: a `done`
        progress a `return` ELŐTT megy ki, a `relocateFinished` csak utána),
        de a szálak közti feldolgozás és a lassabb windows-fájlrendszer
        mellett az öt másodperces időkorlát előbb lépett be — és a hurok
        NÉMÁN kilépett. A `done`-ra várva ez nem fordulhat elő, az
        időtúllépést pedig külön mondjuk ki.
        """
        import time

        new_root = tmp_path / "uj-hely"
        phases = []
        controller.relocateProgress.connect(
            lambda phase, done, total: phases.append(phase)
        )
        controller.startRelocate(str(new_root))

        hatarido = time.monotonic() + 30.0
        while "done" not in phases and time.monotonic() < hatarido:
            qt_app.processEvents()
            time.sleep(0.01)

        assert "done" in phases, (
            f"a haladás-jelzés nem zárult `done` fázissal 30 másodpercen "
            f"belül (látott fázisok: {phases})"
        )

    def test_invalid_destination_inside_source_emits_failure_and_keeps_source(
        self, controller, source
    ):
        index_db, _cache_dir = source
        seen = []
        controller.relocateFailed.connect(seen.append)
        loop = _quit_on(controller.relocateFailed)
        controller.startRelocate(str(index_db.parent / "sub"))
        loop.exec()

        assert seen
        assert index_db.exists()

    def test_file_url_destination_is_accepted(self, controller, tmp_path):
        new_root = tmp_path / "uj-hely"
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(new_root.as_uri())
        loop.exec()

        assert (new_root / "index.db").exists()


class TestCancelRelocate:
    def test_cancel_before_completion_leaves_source_untouched(
        self, controller, source, tmp_path
    ):
        index_db, cache_dir = source
        new_root = tmp_path / "uj-hely"

        # a `relocateStarted` UGYANAZON a szálon, SZINKRON emit()-tel jön
        # (a `startRelocate` a háttérszál indítása ELŐTT bocsátja ki) — a
        # ide kötött `cancelRelocate` így garantáltan a worker első
        # ellenőrzési pontja ELŐTT állítja be a megszakítási jelzőt,
        # determinisztikussá téve a tesztet (nincs versenyhelyzet).
        controller.relocateStarted.connect(controller.cancelRelocate)
        cancelled = []
        controller.relocateCancelled.connect(lambda: cancelled.append(True))
        loop = _quit_on(controller.relocateCancelled)
        controller.startRelocate(str(new_root))
        loop.exec()

        assert cancelled == [True]
        assert index_db.exists()
        assert cache_dir.exists()
        assert not (new_root / "index.db").exists()

    def test_cancel_before_start_is_a_noop(self, controller):
        controller.cancelRelocate()  # nincs futó áthelyezés — nem hibázik


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): az áthelyezés háttérszála
    bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_worker_thread(self, controller, tmp_path):
        loop = _quit_on(controller.relocateFinished)
        controller.startRelocate(str(tmp_path / "uj-hely"))
        loop.exec()
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()


class TestRegiPeldanyLomtarba:
    """#1402: a régi adatbázis és gyorsítótár a LOMTÁRBA megy.

    A mért eredeti (`ID_MOVE_DATABASE` kilenc pontja) a régi példányt a
    Lomtárba teszi; nálunk `unlink`/`rmtree` futott, tehát egy elrontott
    áthelyezés után az adatbázis visszaállíthatatlanul eltűnt.
    """

    def test_a_vezerlo_a_lomtaras_takaritot_adja_at(self, tmp_path, monkeypatch):
        """A vezérlő NEM a mag alapértelmezett (végleges) törlését hagyja."""
        from picasapy.app import relocate_controller as modul

        atadott = {}

        def hamis_relocate(*args, **kwargs):
            atadott.update(kwargs)
            from picasapy.index.relocate import RelocationResult

            kwargs["on_verified"](tmp_path / "uj")
            return RelocationResult(new_root=tmp_path / "uj", old_cleanup_error=None)

        monkeypatch.setattr(modul, "relocate_data_root", hamis_relocate)
        vezerlo = modul.RelocateController(
            tmp_path / "regi" / "index.db",
            tmp_path / "regi" / "thumbs",
            tmp_path / "config",
        )
        vezerlo._run_relocate(tmp_path / "uj", __import__("threading").Event())
        assert atadott.get("delete_old") is modul._lomtarba

    def test_lomtar_nelkul_a_regi_a_helyen_marad(self, tmp_path, monkeypatch):
        """Ha nincs elérhető lomtár, NEM törlünk véglegesen a felhasználó
        háta mögött — a takarító hibát jelez, a fájl a helyén marad."""
        from picasapy.app import relocate_controller as modul
        from picasapy.fileops.trash import TrashUnavailableError

        fajl = tmp_path / "index.db"
        fajl.write_bytes(b"adat")

        def nincs_lomtar(_ut, **_kw):
            raise TrashUnavailableError("írásvédett kötet")

        monkeypatch.setattr(
            "picasapy.fileops.trash.delete_to_trash", nincs_lomtar
        )
        import pytest

        with pytest.raises(OSError) as hiba:
            modul._lomtarba(fajl)
        assert "Lomtárba" in str(hiba.value)
        assert fajl.exists(), "a fájl eltűnt, pedig nem volt hova tenni"


class TestEloEllenorzes:
    """#1402: a cél ellenőrzése MEGELŐZI a műveletet.

    A mért eredeti két feltételt ad: a cél **írható helyi merevlemez**
    (`MoveDatabase::LocalDriveOnly` — „No changes will be made"), és
    **üres** (`MoveDatabase::Failure` — „make sure the destination is
    empty"). Elutasításnál semmihez nem nyúlunk.
    """

    def _vezerlo(self, tmp_path):
        from picasapy.app.relocate_controller import RelocateController

        return RelocateController(
            tmp_path / "regi" / "index.db",
            tmp_path / "regi" / "thumbs",
            tmp_path / "config",
        )

    def test_nem_ures_celt_elutasit_es_NEM_indul(self, tmp_path, monkeypatch):
        from picasapy.app import relocate_controller as modul

        indult = []
        monkeypatch.setattr(
            modul.RelocateController,
            "_start_background",
            lambda self, *a, **k: indult.append(1),
        )
        cel = tmp_path / "cel"
        cel.mkdir()
        (cel / "valami.txt").write_text("nem üres")
        vezerlo = self._vezerlo(tmp_path)
        hibak = []
        vezerlo.relocateFailed.connect(hibak.append)
        vezerlo.startRelocate(str(cel))
        assert indult == [], "elindult a másolás, pedig a cél nem üres"
        assert len(hibak) == 1
        assert "empty" in hibak[0] or "üres" in hibak[0]

    def test_ures_celt_elfogad(self, tmp_path, monkeypatch):
        from picasapy.app import relocate_controller as modul

        indult = []
        monkeypatch.setattr(
            modul.RelocateController,
            "_start_background",
            lambda self, *a, **k: indult.append(1),
        )
        cel = tmp_path / "ures"
        cel.mkdir()
        vezerlo = self._vezerlo(tmp_path)
        hibak = []
        vezerlo.relocateFailed.connect(hibak.append)
        vezerlo.startRelocate(str(cel))
        assert hibak == []
        assert indult == [1]

    def test_halozati_celt_elutasit(self, tmp_path, monkeypatch):
        from picasapy.app import relocate_controller as modul
        from picasapy.perf import tesztuzem

        monkeypatch.setattr(
            tesztuzem, "tarolo_tipusa", lambda _ut: tesztuzem.TAROLO_HALOZATI
        )
        indult = []
        monkeypatch.setattr(
            modul.RelocateController,
            "_start_background",
            lambda self, *a, **k: indult.append(1),
        )
        cel = tmp_path / "halozat"
        cel.mkdir()
        vezerlo = self._vezerlo(tmp_path)
        hibak = []
        vezerlo.relocateFailed.connect(hibak.append)
        vezerlo.startRelocate(str(cel))
        assert indult == [], "hálózati célra is elindult a másolás"
        assert len(hibak) == 1
        assert "network" in hibak[0] or "hálózati" in hibak[0]

    def test_a_meg_nem_letezo_mappa_rendben_van(self, tmp_path, monkeypatch):
        """A mag létrehozza — a nem létező cél nem hiba."""
        from picasapy.app import relocate_controller as modul

        indult = []
        monkeypatch.setattr(
            modul.RelocateController,
            "_start_background",
            lambda self, *a, **k: indult.append(1),
        )
        vezerlo = self._vezerlo(tmp_path)
        hibak = []
        vezerlo.relocateFailed.connect(hibak.append)
        vezerlo.startRelocate(str(tmp_path / "meg" / "nincs"))
        assert hibak == []
        assert indult == [1]
