"""RelocateController (#368, #3214) — a „Move Database" párbeszéd hídja.

⚠️ **A vezérlő 2026-09-17 óta NEM költöztet** (#3214): a mért eredetiben a
gomb csak SZÁNDÉKOT rögzít, a másolás a következő induláskor fut. A
költözés-oldali próbák ezért a
`test_adatbazis_koltozes_indulaskor_3214.py`-ban élnek; itt a cél
ELLENŐRZÉSE és a szándék rögzítése marad.

Valódi ideiglenes forrás- és cél-mappával, mock nélkül (a
`test_dedup_controller.py`/`test_import_source_controller.py` mintája)."""

from __future__ import annotations

import pytest

from picasapy.app.data_location import read_data_root, read_pending_root
from picasapy.app.relocate_controller import RelocateController
from picasapy.index import open_index, sync_tree


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
    index_db, cache_dir = source
    return RelocateController(index_db, cache_dir, config_dir)


class TestCurrentLocation:
    def test_reports_index_database_folder(self, controller, source):
        index_db, _cache_dir = source
        assert controller.currentLocation == str(index_db.parent)


class TestStartRelocate:
    """A gomb útja: ellenőrzés → szándék, fájlmozgás nélkül."""

    def test_missing_destination_emits_failure(self, controller, config_dir):
        hibak: list[str] = []
        controller.relocateFailed.connect(hibak.append)
        controller.startRelocate("")

        assert len(hibak) == 1
        assert read_pending_root(config_dir) is None

    def test_file_url_destination_is_accepted(
        self, controller, config_dir, tmp_path
    ):
        cel = tmp_path / "uj-hely"
        elojegyzett: list[str] = []
        controller.relocateScheduled.connect(elojegyzett.append)
        controller.startRelocate(cel.as_uri())

        assert elojegyzett == [str(cel)]
        assert read_pending_root(config_dir) == cel

    def test_invalid_destination_inside_source_is_rejected(
        self, controller, source, config_dir
    ):
        """A forráson BELÜLI cél a mag szerint sem érvényes — ezt már a
        szándék rögzítése előtt ki kell mondani."""
        index_db, _cache_dir = source
        hibak: list[str] = []
        controller.relocateFailed.connect(hibak.append)
        controller.startRelocate(str(index_db.parent / "beljebb"))

        assert len(hibak) == 1, f"nem jött hiba: {hibak}"
        assert read_pending_root(config_dir) is None

    def test_semmi_nem_koltozik_a_gombra(
        self, controller, source, config_dir, tmp_path
    ):
        index_db, cache_dir = source
        cel = tmp_path / "uj-hely"
        controller.startRelocate(str(cel))

        assert index_db.exists()
        assert (cache_dir / "x.jpg").exists()
        assert not cel.exists()
        assert read_data_root(config_dir) is None, (
            "az ÉLŐ útvonal csak a tényleges költözés után változhat"
        )


class TestElojegyzesVisszavonasa:
    def test_a_visszavonas_torli_a_szandekot(
        self, controller, config_dir, tmp_path
    ):
        cel = tmp_path / "uj-hely"
        controller.startRelocate(str(cel))
        assert read_pending_root(config_dir) == cel

        controller.cancelScheduledRelocate()
        assert read_pending_root(config_dir) is None

    def test_szandek_nelkul_is_biztonsagos(self, controller, config_dir):
        controller.cancelScheduledRelocate()
        assert read_pending_root(config_dir) is None


class TestEloEllenorzes:
    """#1402: a cél ellenőrzése MEGELŐZI a műveletet.

    A mért eredeti két feltételt ad: a cél **írható helyi merevlemez**
    (`MoveDatabase::LocalDriveOnly` — „No changes will be made"), és
    **üres** (`MoveDatabase::Failure` — „make sure the destination is
    empty"). Elutasításnál semmihez nem nyúlunk — #3214 óta ez azt is
    jelenti, hogy SZÁNDÉK sem marad hátra.
    """

    def _vezerlo(self, tmp_path):
        return RelocateController(
            tmp_path / "regi" / "index.db",
            tmp_path / "regi" / "thumbs",
            tmp_path / "config",
        )

    def test_nem_ures_celt_elutasit(self, tmp_path):
        cel = tmp_path / "cel"
        cel.mkdir()
        (cel / "valami.txt").write_text("nem üres", encoding="utf-8")
        vezerlo = self._vezerlo(tmp_path)
        hibak: list[str] = []
        vezerlo.relocateFailed.connect(hibak.append)

        vezerlo.startRelocate(str(cel))

        assert len(hibak) == 1
        assert "empty" in hibak[0] or "üres" in hibak[0]
        assert read_pending_root(tmp_path / "config") is None

    def test_ures_celt_elfogad(self, tmp_path):
        cel = tmp_path / "cel"
        cel.mkdir()
        vezerlo = self._vezerlo(tmp_path)
        elojegyzett: list[str] = []
        vezerlo.relocateScheduled.connect(elojegyzett.append)

        vezerlo.startRelocate(str(cel))

        assert elojegyzett == [str(cel)]

    def test_halozati_celt_elutasit(self, tmp_path, monkeypatch):
        from picasapy.perf.tesztuzem import TAROLO_HALOZATI

        monkeypatch.setattr(
            "picasapy.perf.tesztuzem.tarolo_tipusa",
            lambda _ut: TAROLO_HALOZATI,
        )
        cel = tmp_path / "cel"
        cel.mkdir()
        vezerlo = self._vezerlo(tmp_path)
        hibak: list[str] = []
        vezerlo.relocateFailed.connect(hibak.append)

        vezerlo.startRelocate(str(cel))

        assert len(hibak) == 1
        assert "network" in hibak[0] or "hálózati" in hibak[0]
        assert read_pending_root(tmp_path / "config") is None

    def test_a_meg_nem_letezo_mappa_rendben_van(self, tmp_path):
        vezerlo = self._vezerlo(tmp_path)
        elojegyzett: list[str] = []
        vezerlo.relocateScheduled.connect(elojegyzett.append)

        vezerlo.startRelocate(str(tmp_path / "meg-nincs"))

        assert elojegyzett == [str(tmp_path / "meg-nincs")]
