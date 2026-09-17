"""#3214 — az adatbázis költözése a KÖVETKEZŐ induláskor történik meg.

## A mért séma

| lépés | az eredetiben (mérve) |
|---|---|
| a párbeszéd „Áthelyezés" gombja | csak **szándékot** rögzít (`Preferences\\AppLocalDataPathCopy`; író `0x007d1936`) |
| a tényleges költözés | a **következő induláskor**, haladásjelzővel (olvasó `0x00404d97`, burkoló `0x00404c30`) |
| utána | a program már az ÚJ helyről indult — nem kér külön újraindítást |

Nálunk eddig a párbeszéd bezárása után, futás közben költözött, és a
felület újraindítást kért. Ez a modul a mért sémát tartatja be.

## Saját döntés — kimondva

A szándék-kulcs sorsa sikertelen költözés után **nem** mérés kérdése: a
kutatás nem adta meg, hogy az eredeti újrapróbálja-e. Mi a szándékot
**mindkét** kimenetnél (siker és hiba) töröljük: különben egy elérhetetlen
célra mutató szándék MINDEN indulást megfogna, és a felhasználó a saját
gépén nem tudná megkerülni. A hibát a hívó jelzi ki.
"""

from __future__ import annotations

import pytest

from picasapy.app.data_location import (
    read_data_root,
    read_pending_root,
    write_pending_root,
)

from picasapy.app.relocate_controller import RelocateController
from picasapy.app.startup_relocate import fuggo_koltozes
from picasapy.index import open_index, sync_tree
from support.qt_wait import hangos_hurok


def _forras(tmp_path):
    """Valódi index + cache, mock nélkül (a `test_relocate_controller.py`
    mintája)."""
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
def forras(tmp_path):
    return _forras(tmp_path)


@pytest.fixture
def config_dir(tmp_path):
    return tmp_path / "config"


@pytest.fixture
def vezerlo(qt_app, forras, config_dir):
    index_db, cache_dir = forras
    return RelocateController(index_db, cache_dir, config_dir)


class TestASzandekRogzitese:
    """A gomb SZÁNDÉKOT ír, fájlt nem mozgat."""

    def test_a_szandek_a_beallitasba_kerul(self, vezerlo, config_dir, tmp_path):
        cel = tmp_path / "uj-hely"
        hurok = hangos_hurok(vezerlo.relocateScheduled, timeout_ms=5000)
        vezerlo.startRelocate(str(cel))
        hurok.exec()

        assert read_pending_root(config_dir) == cel

    def test_semmi_nem_mozdul_el(self, vezerlo, forras, config_dir, tmp_path):
        index_db, cache_dir = forras
        cel = tmp_path / "uj-hely"
        hurok = hangos_hurok(vezerlo.relocateScheduled, timeout_ms=5000)
        vezerlo.startRelocate(str(cel))
        hurok.exec()

        assert index_db.exists(), "a régi adatbázis a helyén marad"
        assert (cache_dir / "x.jpg").exists()
        assert not cel.exists(), "a cél még létre sem jön"
        # az ÉLŐ útvonal is változatlan — az csak a költözés után íródik
        assert read_data_root(config_dir) is None

    def test_az_ervenytelen_celt_tovabbra_is_elutasitja(
        self, vezerlo, config_dir, tmp_path
    ):
        cel = tmp_path / "foglalt"
        cel.mkdir()
        (cel / "valami.txt").write_text("nem üres", encoding="utf-8")

        hurok = hangos_hurok(vezerlo.relocateFailed, timeout_ms=5000)
        vezerlo.startRelocate(str(cel))
        hurok.exec()

        assert read_pending_root(config_dir) is None, (
            "elutasított célra NEM szabad szándékot rögzíteni"
        )


class TestAzIndulas:
    """A költözést az INDULÁS végzi el."""

    def test_szandek_nelkul_semmihez_nem_nyul(self, forras, config_dir, tmp_path):
        index_db, cache_dir = forras
        eredmeny = fuggo_koltozes(config_dir, index_db, cache_dir)

        assert eredmeny.uj_gyoker is None
        assert eredmeny.hiba is None
        assert index_db.exists()
        assert not config_dir.exists() or read_data_root(config_dir) is None

    def test_a_szandek_koltoztet_es_atirja_az_elo_utvonalat(
        self, forras, config_dir, tmp_path
    ):
        index_db, cache_dir = forras
        cel = tmp_path / "uj-hely"
        write_pending_root(config_dir, cel)

        eredmeny = fuggo_koltozes(config_dir, index_db, cache_dir)

        assert eredmeny.hiba is None
        assert eredmeny.uj_gyoker == cel
        assert (cel / "index.db").exists()
        assert (cel / "thumbs" / "x.jpg").exists()
        assert read_data_root(config_dir) == cel
        assert read_pending_root(config_dir) is None, "a szándék elfogy"

    def test_a_haladast_jelenti(self, forras, config_dir, tmp_path):
        index_db, cache_dir = forras
        cel = tmp_path / "uj-hely"
        write_pending_root(config_dir, cel)
        fazisok: list[str] = []

        fuggo_koltozes(
            config_dir,
            index_db,
            cache_dir,
            haladas=lambda p: fazisok.append(p.phase),
        )

        assert "database" in fazisok, f"a fázisok: {fazisok}"

    def test_hibas_cel_utan_a_REGI_helyrol_indulunk(
        self, forras, config_dir, tmp_path
    ):
        index_db, cache_dir = forras
        cel = tmp_path / "idokozben-megtelt"
        cel.mkdir()
        write_pending_root(config_dir, cel)
        (cel / "valami.txt").write_text("nem üres", encoding="utf-8")

        eredmeny = fuggo_koltozes(config_dir, index_db, cache_dir)

        assert eredmeny.uj_gyoker is None
        assert eredmeny.hiba, "a hibát a hívónak ki kell tudnia jelezni"
        assert index_db.exists(), "a régi adatbázis érintetlen"
        assert read_data_root(config_dir) is None
        # saját döntés (ld. a modul docstringjét): a szándék elfogy, hogy a
        # hibás cél ne fogja meg MINDEN következő indulást
        assert read_pending_root(config_dir) is None


class TestARegiPeldanyLomtarba:
    """#1402: a régi példány a Lomtárba megy, nem törlődik véglegesen.

    (A próbák a #3214 előtt a vezérlőt mérték; a takarító azzal együtt
    költözött ide, ahol a költözés maga fut.)"""

    def test_a_koltozes_a_lomtaras_takaritot_adja_at(self, tmp_path, monkeypatch):
        from picasapy.app import startup_relocate as modul
        from picasapy.index.relocate import RelocationResult

        atadott: dict = {}

        def hamis_relocate(*args, **kwargs):
            atadott.update(kwargs)
            kwargs["on_verified"](tmp_path / "uj")
            return RelocationResult(new_root=tmp_path / "uj", old_cleanup_error=None)

        monkeypatch.setattr(modul, "relocate_data_root", hamis_relocate)
        config_dir = tmp_path / "config"
        write_pending_root(config_dir, tmp_path / "uj")

        modul.fuggo_koltozes(
            config_dir, tmp_path / "regi" / "index.db", tmp_path / "regi" / "thumbs"
        )

        assert atadott.get("delete_old") is modul.lomtarba

    def test_lomtar_nelkul_a_regi_a_helyen_marad(self, tmp_path, monkeypatch):
        """Ha nincs elérhető lomtár, NEM törlünk véglegesen a felhasználó
        háta mögött — a takarító hibát jelez, a fájl a helyén marad."""
        from picasapy.app.startup_relocate import lomtarba
        from picasapy.fileops.trash import TrashUnavailableError

        fajl = tmp_path / "index.db"
        fajl.write_bytes(b"adat")

        def nincs_lomtar(_ut, **_kw):
            raise TrashUnavailableError("írásvédett kötet")

        monkeypatch.setattr("picasapy.fileops.trash.delete_to_trash", nincs_lomtar)

        with pytest.raises(OSError) as hiba:
            lomtarba(fajl)

        assert "Lomtárba" in str(hiba.value)
        assert fajl.exists(), "a fájl eltűnt, pedig nem volt hova tenni"


class TestAzIndulasiKoltozoSzal:
    """A költözés HÁTTÉRSZÁLON fut, nyilvántartva (#430/#438/#988).

    Az `app/` rétegben a nyers `threading.Thread` tiltott — a
    háttérszálról emitált Qt-jelzés SIGSEGV-t ad, ha a küldő közben
    megsemmisül. (Mérve: a CI szál-őre pontosan ezt fogta meg az első
    változatomon.)"""

    def test_a_szal_elvegzi_a_koltozest_es_jelez(
        self, qt_app, forras, config_dir, tmp_path
    ):
        from PySide6.QtCore import QEventLoop, Qt

        from picasapy.app.startup_relocate import IndulasiKoltozo, KoltozesHid

        index_db, cache_dir = forras
        cel = tmp_path / "uj-hely"
        write_pending_root(config_dir, cel)

        koltozo = IndulasiKoltozo(KoltozesHid(cel))
        hurok = QEventLoop()
        koltozo.kesz.connect(hurok.quit, Qt.ConnectionType.QueuedConnection)
        koltozo.inditsd(config_dir, index_db, cache_dir)
        hurok.exec()

        assert koltozo.waitForBackgroundWorkers(30.0), "a szál nem állt le"
        assert koltozo.eredmeny.uj_gyoker == cel
        assert (cel / "index.db").exists()
        assert read_data_root(config_dir) == cel
