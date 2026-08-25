"""#1430 — a megőrzött eredeti a képpel együtt költözik.

A #371 kutatása kizárta, hogy a Picasa a szerkesztést a fájlon kívül bárhol
tárolná: a retus/vörösszem a JPEG-be van beleégetve, tehát a visszaállítás
EGYETLEN útja az eredeti megőrzött másolata. Ha az elszakad a képtől — mert
a képet átneveztük vagy másik mappába vittük —, a szerkesztés véglegessé
válik: a felhasználó szempontjából adatvesztés.

Az őr ezért nem csak a fájlok új helyét nézi, hanem azt is, hogy a
felhasználó felé látszó funkció (`find_original_backup`, azaz a „Vissza az
eredetihez") az ÚJ helyen is talál eredetit.
"""

from __future__ import annotations

import shutil
from pathlib import Path

import pytest

from picasapy.edit import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    find_original_backup,
)
from picasapy.fileops import move_folder, move_photo, move_photos, rename_photo


def _photo(folder: Path, name: str, payload: bytes = b"szerkesztett") -> Path:
    """Egy „kép" a mappában — a tartalom bájtazonossága a bizonyíték."""
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / name
    path.write_bytes(payload)
    return path


def _original(folder: Path, dir_name: str, name: str, payload: bytes) -> Path:
    """Megőrzött eredeti (vagy sorszámozott pillanatkép) elhelyezése."""
    directory = folder / dir_name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / name
    path.write_bytes(payload)
    return path


class TestAtnevezes:
    def test_rejtett_eredeti_koveti_az_uj_nevet(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        new_path = rename_photo(photo, "b.jpg")

        assert not (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").exists()
        koltozott = tmp_path / ORIGINALS_DIR_NAME / "b.jpg"
        assert koltozott.read_bytes() == b"eredeti"
        assert find_original_backup(new_path) == koltozott

    def test_regi_originals_mappa_is_koveti(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi-eredeti")

        new_path = rename_photo(photo, "b.jpg")

        assert not (tmp_path / LEGACY_ORIGINALS_DIR_NAME / "a.jpg").exists()
        koltozott = tmp_path / LEGACY_ORIGINALS_DIR_NAME / "b.jpg"
        assert koltozott.read_bytes() == b"regi-eredeti"
        # a mappanév megmarad: a régi példány elsőbbsége (#1425) így marad meg
        assert find_original_backup(new_path) == koltozott

    def test_sorszamozott_pillanatkepek_is_koltoznek(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.2.jpg", b"masodik-mentes")

        rename_photo(photo, "b.jpg")

        originals = tmp_path / ORIGINALS_DIR_NAME
        assert (originals / "b.1.jpg").read_bytes() == b"elso-mentes"
        assert (originals / "b.2.jpg").read_bytes() == b"masodik-mentes"
        assert not (originals / "a.1.jpg").exists()
        assert not (originals / "a.2.jpg").exists()

    def test_mindket_mappa_egyszerre(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"ujabb")

        rename_photo(photo, "b.jpg")

        assert (tmp_path / LEGACY_ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == b"regi"
        assert (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == b"ujabb"

    def test_eredeti_nelkul_nem_keletkezik_uj_mappa(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")

        rename_photo(photo, "b.jpg")

        assert not (tmp_path / ORIGINALS_DIR_NAME).exists()
        assert not (tmp_path / LEGACY_ORIGINALS_DIR_NAME).exists()

    def test_masik_kep_eredetijet_nem_rangatja_el(self, tmp_path):
        """`a.jpg` mellett létezik egy KÜLÖN kép `a.2.jpg` néven — annak a
        megőrzött eredetije nem sorszámozott pillanatkép, nem költözhet."""
        photo = _photo(tmp_path, "a.jpg")
        _photo(tmp_path, "a.2.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.2.jpg", b"masik-kep-eredetije")

        rename_photo(photo, "b.jpg")

        maradt = tmp_path / ORIGINALS_DIR_NAME / "a.2.jpg"
        assert maradt.read_bytes() == b"masik-kep-eredetije"
        assert not (tmp_path / ORIGINALS_DIR_NAME / "b.2.jpg").exists()

    def test_foglalt_celhely_eseten_semmi_nem_mozdul(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(tmp_path, ORIGINALS_DIR_NAME, "b.jpg", b"arva-eredeti")

        with pytest.raises(FileExistsError) as hiba:
            rename_photo(photo, "b.jpg")

        assert photo.exists()
        assert (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == b"arva-eredeti"
        uzenet = str(hiba.value)
        assert "eredeti" in uzenet.lower()
        assert ORIGINALS_DIR_NAME in uzenet

    def test_bukott_atnevezes_utan_az_eredeti_visszakerul(self, tmp_path, monkeypatch):
        """Ha a KÉP átnevezése bukik el (verseny egy párhuzamos íróval), a már
        elmozdított eredeti nem maradhat az új néven — különben a kép a régi
        nevén elveszítené a visszaútját."""
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        def _bukik(self, target):  # noqa: ANN001
            raise OSError("a lemez megtelt")

        monkeypatch.setattr(Path, "rename", _bukik)

        with pytest.raises(OSError):
            rename_photo(photo, "b.jpg")

        assert (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert not (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").exists()


class TestMozgatas:
    def test_rejtett_eredeti_atkerul_a_celmappaba(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        new_path = move_photo(photo, cel)

        assert not (forras / ORIGINALS_DIR_NAME / "a.jpg").exists()
        koltozott = cel / ORIGINALS_DIR_NAME / "a.jpg"
        assert koltozott.read_bytes() == b"eredeti"
        assert find_original_backup(new_path) == koltozott

    def test_regi_originals_mappa_neve_megmarad_a_celban(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi-eredeti")

        new_path = move_photo(photo, cel)

        koltozott = cel / LEGACY_ORIGINALS_DIR_NAME / "a.jpg"
        assert koltozott.read_bytes() == b"regi-eredeti"
        assert find_original_backup(new_path) == koltozott

    def test_pillanatkepek_is_atkerulnek(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")

        move_photo(photo, cel)

        assert (cel / ORIGINALS_DIR_NAME / "a.1.jpg").read_bytes() == b"elso-mentes"
        assert not (forras / ORIGINALS_DIR_NAME / "a.1.jpg").exists()

    def test_ini_szekcio_es_eredeti_egyutt_koltozik(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        (forras / ".picasa.ini").write_text("[a.jpg]\nstar=yes\n", encoding="utf-8")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        move_photo(photo, cel)

        assert "[a.jpg]" in (cel / ".picasa.ini").read_text(encoding="utf-8")
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"

    def test_foglalt_celhely_eseten_a_kep_sem_mozdul(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(cel, ORIGINALS_DIR_NAME, "a.jpg", b"arva-eredeti-a-celban")

        with pytest.raises(FileExistsError) as hiba:
            move_photo(photo, cel)

        assert photo.exists()
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"arva-eredeti-a-celban"
        assert "eredeti" in str(hiba.value).lower()

    def test_bukott_mozgatas_utan_az_eredeti_visszakerul(self, tmp_path, monkeypatch):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        eredeti_move = shutil.move

        def _csak_a_kepnel_bukik(src, dst, *args, **kwargs):  # noqa: ANN001
            if Path(src).name == "a.jpg" and Path(src).parent == forras:
                raise OSError("a lemez megtelt")
            return eredeti_move(src, dst, *args, **kwargs)

        monkeypatch.setattr("picasapy.fileops.move.shutil.move", _csak_a_kepnel_bukik)

        with pytest.raises(OSError):
            move_photo(photo, cel)

        assert photo.exists()
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert not (cel / ORIGINALS_DIR_NAME / "a.jpg").exists()


class TestKotegeltMozgatas:
    def test_move_photos_viszi_az_eredetiket(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        elso = _photo(forras, "a.jpg")
        masodik = _photo(forras, "b.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"a-eredeti")
        _original(forras, LEGACY_ORIGINALS_DIR_NAME, "b.jpg", b"b-eredeti")

        result = move_photos([elso, masodik], cel)

        assert result.failed == ()
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"a-eredeti"
        assert (cel / LEGACY_ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == b"b-eredeti"

    def test_utkozeskor_a_potnev_az_eredetinek_is_szabad_helyet_keres(self, tmp_path):
        """Névütközésnél a köteg pótnevet ad (`a-1.jpg`). Ha azt a nevet a
        cél eredeti-mappájában egy árva fájl foglalja, a pótnév-keresésnek
        tovább kell lépnie — különben a köteg elkerülhető hibával állna meg."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        photo = _photo(forras, "a.jpg", b"koltozo")
        _photo(cel, "a.jpg", b"mar-ott-van")  # ez okozza az ütközést
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(cel, ORIGINALS_DIR_NAME, "a-1.jpg", b"arva")

        result = move_photos([photo], cel)

        assert result.failed == ()
        (_, uj_ut), = result.done
        assert uj_ut.name == "a-2.jpg"
        assert uj_ut.read_bytes() == b"koltozo"
        assert (cel / ORIGINALS_DIR_NAME / "a-2.jpg").read_bytes() == b"eredeti"
        assert (cel / ORIGINALS_DIR_NAME / "a-1.jpg").read_bytes() == b"arva"


class TestMappaMozgatas:
    def test_a_mappa_mozgatasa_viszi_az_eredetiket(self, tmp_path):
        """A `move_folder` a teljes könyvtárat viszi, tehát az eredeti-mappák
        maguktól vele mennek. Ez az őr azt rögzíti, hogy ez így is maradjon —
        egy „csak a képeket vigyük" átalakítás itt bukna el."""
        forras = tmp_path / "album"
        cel_szulo = tmp_path / "cel"
        cel_szulo.mkdir()
        _photo(forras, "a.jpg")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(forras, LEGACY_ORIGINALS_DIR_NAME, "b.jpg", b"regi-eredeti")

        uj_mappa = move_folder(forras, cel_szulo)

        assert (uj_mappa / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert (
            uj_mappa / LEGACY_ORIGINALS_DIR_NAME / "b.jpg"
        ).read_bytes() == b"regi-eredeti"
        assert find_original_backup(uj_mappa / "a.jpg") == (
            uj_mappa / ORIGINALS_DIR_NAME / "a.jpg"
        )
