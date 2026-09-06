"""#2512 — az ÚJ helyen álló pillanatképek is a képpel mozognak.

A pillanatképek a `.picasaoriginals/.picasapy-snapshots/` alkönyvtárba
kerültek (ADR-010), hogy a nevük ne ütközzön egy önálló kép „szent"
eredetijével. A névtér-váltásnak azonban ára van, ha a KÍSÉRŐFÁJL-LOGIKA nem
követi: a kép átnevezésekor/mozgatásakor/törlésekor az új helyen álló
példányok hátramaradnának.

A kár ugyanaz, amit a #1430/#1450/#1451 megelőz: az árva pillanatképek
láthatatlanul gyűlnek, és a következő, azonos nevű kép a saját mentésénél
idegen sorszámokra futna. Ezért ez az őr a HÁROM úton külön mér.

A régi, közös helyen álló példányok költözését a #1430/#1450/#1451 őrei
mérik — azok változatlanul zöldek, és ez a lap szándékosan nem ismétli meg
őket.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit import ORIGINALS_DIR_NAME, SNAPSHOT_DIR_NAME
from picasapy.fileops import (
    copy_photo,
    delete_photo_permanently,
    delete_photo_to_trash,
    move_photo,
    originals_slot_free,
    rename_photo,
)
from picasapy.fileops.originals import companions_of


@pytest.fixture
def lomtar(tmp_path: Path) -> Path:
    return tmp_path / "lomtar"


def _kep(mappa: Path, nev: str, tartalom: bytes = b"szerkesztett") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _pillanatkep(mappa: Path, nev: str, tartalom: bytes) -> Path:
    """Pillanatkép az ÚJ helyen: `<mappa>/.picasaoriginals/.picasapy-snapshots/`."""
    directory = mappa / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(tartalom)
    return path


def _eredeti(mappa: Path, nev: str, tartalom: bytes) -> Path:
    directory = mappa / ORIGINALS_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(tartalom)
    return path


class TestAtnevezes:
    def test_az_uj_helyen_allo_pillanatkepek_is_koltoznek(self, tmp_path):
        kep = _kep(tmp_path, "a.jpg")
        _eredeti(tmp_path, "a.jpg", b"szent-eredeti")
        _pillanatkep(tmp_path, "a.1.jpg", b"elso-mentes")
        _pillanatkep(tmp_path, "a.2.jpg", b"masodik-mentes")

        rename_photo(kep, "b.jpg")

        sajat = tmp_path / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME
        assert (sajat / "b.1.jpg").read_bytes() == b"elso-mentes"
        assert (sajat / "b.2.jpg").read_bytes() == b"masodik-mentes"
        assert not (sajat / "a.1.jpg").exists()
        assert not (sajat / "a.2.jpg").exists()
        # a „szent" eredeti a saját, VÁLTOZATLAN helyén követi a nevet
        assert (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == (
            b"szent-eredeti"
        )

    def test_a_pillanatkep_nem_kerul_at_a_szent_eredeti_melle(self, tmp_path):
        """A szintek nem keveredhetnek: az alkönyvtárból alkönyvtárba megy."""
        kep = _kep(tmp_path, "a.jpg")
        _pillanatkep(tmp_path, "a.1.jpg", b"elso-mentes")

        rename_photo(kep, "b.jpg")

        assert not (tmp_path / ORIGINALS_DIR_NAME / "b.1.jpg").exists()


class TestMozgatas:
    def test_masik_mappaba_is_viszi(self, tmp_path):
        forras, cel = tmp_path / "forras", tmp_path / "cel"
        kep = _kep(forras, "a.jpg")
        cel.mkdir()
        _pillanatkep(forras, "a.1.jpg", b"elso-mentes")

        move_photo(kep, cel)

        assert (cel / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME / "a.1.jpg").read_bytes() == (
            b"elso-mentes"
        )
        assert not (
            forras / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME / "a.1.jpg"
        ).exists()


class TestMasolas:
    def test_a_masolat_is_megkapja_a_pillanatkepeit(self, tmp_path):
        forras, cel = tmp_path / "forras", tmp_path / "cel"
        kep = _kep(forras, "a.jpg")
        cel.mkdir()
        _pillanatkep(forras, "a.1.jpg", b"elso-mentes")

        copy_photo(kep, cel)

        assert (cel / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME / "a.1.jpg").read_bytes() == (
            b"elso-mentes"
        )
        # a forrás mindenestül a helyén marad
        assert (
            forras / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME / "a.1.jpg"
        ).read_bytes() == b"elso-mentes"


class TestTorles:
    def test_a_lomtarazas_viszi_az_uj_helyen_allokat(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        kep = _kep(mappa, "a.jpg")
        _eredeti(mappa, "a.jpg", b"szent-eredeti")
        pillanatkep = _pillanatkep(mappa, "a.1.jpg", b"elso-mentes")

        delete_photo_to_trash(kep, trash_dir=lomtar)

        assert not pillanatkep.exists()

    def test_a_vegleges_torles_is_viszi(self, tmp_path):
        mappa = tmp_path / "kepek"
        kep = _kep(mappa, "a.jpg")
        pillanatkep = _pillanatkep(mappa, "a.1.jpg", b"elso-mentes")

        delete_photo_permanently(kep)

        assert not pillanatkep.exists()

    def test_a_leltar_felsorolja_az_uj_helyen_allokat(self, tmp_path):
        kep = _kep(tmp_path, "a.jpg")
        eredeti = _eredeti(tmp_path, "a.jpg", b"szent-eredeti")
        pillanatkep = _pillanatkep(tmp_path, "a.1.jpg", b"elso-mentes")

        assert set(companions_of(kep)) == {eredeti, pillanatkep}


class TestFoglaltsag:
    def test_az_uj_helyen_allo_pillanatkep_is_foglal(self, tmp_path):
        """Különben a kísérők költöztetése `FileExistsError`-be futna —
        vagy ami rosszabb, a kép ÖRÖKBE FOGADNÁ az ott heverő példányt."""
        _kep(tmp_path, "b.jpg")  # a leendő gazda még nincs itt
        _pillanatkep(tmp_path, "a.1.jpg", b"arva")

        assert originals_slot_free(tmp_path, "a.jpg") is False

    def test_szabad_hely_szabadnak_latszik(self, tmp_path):
        assert originals_slot_free(tmp_path, "a.jpg") is True


class TestVisszagorgetesUtanTakaritas:
    """A bukott költöztetés ne hagyjon ÜRES eredeti-mappát a célban.

    A pillanatkép két szinttel lejjebb ül (`.picasaoriginals/`
    `.picasapy-snapshots/`), tehát a visszagörgetés után KÉT könyvtárat kell
    eltakarítani. Ha csak a belső tűnik el, a felhasználó célmappájában ott
    marad egy magyarázat nélküli `.picasaoriginals` — a legacy ágon egy
    LÁTHATÓ `Originals` —, miközben az üzenet azt mondja, semmi nem
    változott (#2511 gondolata a mélyebb szinten).
    """

    def test_a_bukott_masolas_nem_hagy_eredeti_mappat(self, tmp_path, monkeypatch):
        from picasapy.fileops import originals as originals_modul

        forras, cel = tmp_path / "A", tmp_path / "B"
        _kep(forras, "a.jpg")
        _pillanatkep(forras, "a.1.jpg", b"pillanatkep")
        _kep(cel, "mas.jpg")  # a célmappa nem üres, de eredeti-mappája nincs

        def _bukik(*args, **kwargs):
            raise OSError("a lemez tele van")

        monkeypatch.setattr(originals_modul, "_copy", _bukik)

        with pytest.raises(OSError):
            originals_modul.copy_preserved_originals(
                forras / "a.jpg", cel / "a.jpg"
            )

        assert not (cel / ORIGINALS_DIR_NAME).exists()
        assert (cel / "mas.jpg").exists()  # a célmappa maga megmarad


class TestUtbanLevoFajlUzenete:
    """Az alkönyvtárban álló fájl SOHA nem másik kép „szent" eredetije.

    A közös helyen a `<név>.<N>` alak kétértelmű, ezért ott az üzenet
    megkeresi a lehetséges gazdát, és óv a törlésétől (#1430). Az ÚJ
    alkönyvtárba viszont rajtunk kívül senki nem ír: ugyanaz a tanács ott
    egy vadidegen, ártatlan képre mutatna.
    """

    def test_az_arva_pillanatkep_torolhetonek_mondatik(self, tmp_path):
        forras, cel = tmp_path / "forras", tmp_path / "cel"
        kep = _kep(forras, "a.jpg")
        _pillanatkep(forras, "a.1.jpg", b"a mi pillanatkepunk")
        cel.mkdir()
        _kep(cel, "a.1.jpg", b"egy teljesen mas, onallo kep")  # a hamis „gazda”
        _pillanatkep(cel, "a.1.jpg", b"arva")

        with pytest.raises(FileExistsError) as hiba:
            move_photo(kep, cel)

        uzenet = str(hiba.value)
        assert "árván maradt pillanatképe" in uzenet
        assert "NE törölje" not in uzenet
        assert kep.exists()  # semmi nem mozdult el
