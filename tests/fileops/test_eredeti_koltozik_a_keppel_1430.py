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
from picasapy.fileops import (
    conflicting_names,
    move_folder,
    move_photo,
    move_photos,
    move_preserved_originals,
    originals_follow,
    originals_slot_free,
    plan_original_moves,
    rename_photo,
    undo_original_moves,
)
from picasapy.fileops.originals import OriginalMove, _reject_unsafe_targets


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

        with pytest.raises(OSError) as hiba:
            rename_photo(photo, "b.jpg")

        assert (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert not (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").exists()
        # a visszagörgetés sikerült, tehát nincs mit a felhasználó nyakába
        # varrni: az eredeti hibaüzenet marad, figyelmeztetés nélkül
        uzenet = str(hiba.value)
        assert "a lemez megtelt" in uzenet
        assert "ne mentse" not in uzenet.lower()


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

        with pytest.raises(OSError) as hiba:
            move_photo(photo, cel)

        assert photo.exists()
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert not (cel / ORIGINALS_DIR_NAME / "a.jpg").exists()
        uzenet = str(hiba.value)
        assert "a lemez megtelt" in uzenet
        assert "ne mentse" not in uzenet.lower()


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


class TestVisszagorgetesUzenete:
    """#1430 kódszemle, 2. blokkoló: ha a visszagörgetés IS elbukik, a
    megnyugtató mondat („a régi helyén továbbra is működik") HAMIS — az
    eredeti a célmappában ragadt, a `find_original_backup` a régi helyen
    `None`-t ad. A következmény nem kozmetikai: az `edit/save.py`
    `existing_backup is None` mellett a MÁR SZERKESZTETT bájtokat írja be új
    „eredetiként", tehát a megnyugtatott felhasználó egyetlen mentéssel
    végleg elveszíti az érintetlen eredetit."""

    @staticmethod
    def _csak_visszafele_bukik(monkeypatch):
        """`shutil.move` az ODAÚTON működik, a VISSZAÚTON bukik."""
        eredeti_move = shutil.move
        allapot = {"odaut_kesz": False}

        def _fake(src, dst, *args, **kwargs):  # noqa: ANN001
            if allapot["odaut_kesz"]:
                raise OSError("a forrásmappa időközben írásvédetté vált")
            allapot["odaut_kesz"] = True
            return eredeti_move(src, dst, *args, **kwargs)

        monkeypatch.setattr("picasapy.fileops.originals.shutil.move", _fake)

    def test_bukott_visszagorgetes_nem_allitja_hogy_minden_rendben(
        self, tmp_path, monkeypatch
    ):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        target = tmp_path / "b.jpg"
        self._csak_visszafele_bukik(monkeypatch)

        with pytest.raises(OSError) as hiba:  # noqa: PT012
            with originals_follow(photo, target):
                raise OSError("a kép átnevezése nem sikerült")

        uzenet = str(hiba.value)
        # a hamis megnyugtatás semmilyen alakban nem hangozhat el
        assert "továbbra is működik" not in uzenet
        assert "nem mozdult el" not in uzenet
        # ehelyett meg kell mondania, hol a fájl és hogy MIT NE tegyen
        assert str(tmp_path / ORIGINALS_DIR_NAME / "b.jpg") in uzenet
        assert "ne mentse" in uzenet.lower()

    def test_sikeres_visszagorgetes_utan_megnyugtat(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        with pytest.raises(OSError) as hiba:  # noqa: PT012
            with originals_follow(photo, tmp_path / "b.jpg"):
                raise OSError("a kép átnevezése nem sikerült")

        uzenet = str(hiba.value)
        assert "ne mentse" not in uzenet.lower()
        assert (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").exists()

    def test_a_kisero_bukasakor_sincs_hamis_megnyugtatas(
        self, tmp_path, monkeypatch
    ):
        """Ugyanez a `move_preserved_originals` saját hibaágán: az ELSŐ
        kísérő átment, a másodiknál bukunk, és a visszaút sem megy."""
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        self._csak_visszafele_bukik(monkeypatch)

        with pytest.raises(OSError) as hiba:
            move_preserved_originals(photo, tmp_path / "b.jpg")

        uzenet = str(hiba.value)
        assert "továbbra is működik" not in uzenet
        assert "ne mentse" in uzenet.lower()


class TestUtbanLevoFajlUzenete:
    """#1430 kódszemle, 3. pont: az „útban van" tanács nem lehet feltétlen.
    Az ütköző fájl lehet egy MÁSIK, élő kép saját megőrzött eredetije —
    annak a törlése a másik kép visszaútját semmisítené meg."""

    def test_arva_fajlnal_a_torles_javasolhato(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(tmp_path, ORIGINALS_DIR_NAME, "b.1.jpg", b"arva")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")

        with pytest.raises(FileExistsError) as hiba:
            rename_photo(photo, "b.jpg")

        uzenet = str(hiba.value)
        assert "árván maradt" in uzenet
        assert "törölje vagy nevezze át" in uzenet
        assert "NE törölje" not in uzenet

    def test_masik_kep_eredetijenel_a_torles_NEM_javasolhato(self, tmp_path):
        """`b.1.jpg` egy ÖNÁLLÓ, élő kép a mappában; a
        `.picasaoriginals/b.1.jpg` az Ő eredetije. Az `a.jpg` → `b.jpg`
        átnevezés a saját `a.1.jpg` pillanatképét pont oda vinné."""
        photo = _photo(tmp_path, "a.jpg")
        _photo(tmp_path, "b.1.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        _original(tmp_path, ORIGINALS_DIR_NAME, "b.1.jpg", b"masik-kep-eredetije")

        with pytest.raises(FileExistsError) as hiba:
            rename_photo(photo, "b.jpg")

        uzenet = str(hiba.value)
        assert "NE törölje" in uzenet
        assert "árván maradt" not in uzenet
        assert "b.1.jpg" in uzenet
        assert photo.exists()
        assert (
            tmp_path / ORIGINALS_DIR_NAME / "b.1.jpg"
        ).read_bytes() == b"masik-kep-eredetije"


class TestPillanatkepNevutkozes:
    """#1430 kódszemle, 4. pont: két pillanatkép ugyanarra a célnévre
    képződhetett (`a.1.jpg` és `a.01.jpg`), és a `shutil.move` POSIX-on
    NÉMÁN felülír — a modul saját „sosem írunk felül" szerződése ellenére."""

    def test_a_nullaval_kezdodo_sorszam_nem_nyeli_el_a_masikat(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"egyes")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.01.jpg", b"nullaegy")

        rename_photo(photo, "b.jpg")

        originals = tmp_path / ORIGINALS_DIR_NAME
        megmaradt = {
            path.read_bytes() for path in originals.iterdir() if path.is_file()
        }
        assert megmaradt == {b"egyes", b"nullaegy"}, "az egyik pillanatkép elveszett"

    def test_nem_tizes_szamjegy_nem_ejt_ki_hibat(self, tmp_path):
        """A `str.isdigit()` átengedi a `²`-t, amin az `int()` `ValueError`-t
        dob — az a felhasználó felé olvashatatlan angol hibaként bukna ki."""
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.².jpg", b"nem-sorszam")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        uj_ut = rename_photo(photo, "b.jpg")

        assert (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").read_bytes() == b"eredeti"
        assert (tmp_path / ORIGINALS_DIR_NAME / "a.².jpg").exists()
        assert uj_ut.exists()


class TestUresMappaNemMaradHatra:
    """#1430 kódszemle, 5. pont: ha MÁR AZ ELSŐ kísérő bukik, a célban ne
    maradjon ott egy üres — a legacy esetben LÁTHATÓ — `Originals/` mappa,
    miközben az üzenet azt mondja, hogy semmi nem történt."""

    def test_elso_kisero_bukasakor_nincs_uj_ures_mappa_a_celban(
        self, tmp_path, monkeypatch
    ):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg")
        _original(forras, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi-eredeti")

        def _mindig_bukik(src, dst, *args, **kwargs):  # noqa: ANN001
            raise OSError("a lemez megtelt")

        monkeypatch.setattr("picasapy.fileops.originals.shutil.move", _mindig_bukik)

        with pytest.raises(OSError):
            move_photo(photo, cel)

        assert photo.exists()
        assert not (cel / LEGACY_ORIGINALS_DIR_NAME).exists()


class TestPublikusFuggvenyek:
    """A modul négy exportált függvénye közvetlenül is le van mérve."""

    def test_plan_original_moves_ures_ha_nincs_eredeti(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        assert plan_original_moves(photo, tmp_path / "b.jpg") == ()

    def test_plan_original_moves_nem_nyul_a_lemezhez(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        eredeti = _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        terv = plan_original_moves(photo, tmp_path / "b.jpg")

        assert [(move.source, move.target) for move in terv] == [
            (eredeti, tmp_path / ORIGINALS_DIR_NAME / "b.jpg")
        ]
        assert eredeti.exists(), "a tervezés nem mozgathat semmit"

    def test_move_preserved_originals_visszaadja_a_megtett_lepeseket(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")

        megtett = move_preserved_originals(photo, tmp_path / "b.jpg")

        assert len(megtett) == 1
        assert megtett[0].target == tmp_path / ORIGINALS_DIR_NAME / "b.jpg"
        assert megtett[0].target.exists()

    def test_undo_original_moves_mindent_visszatesz(self, tmp_path):
        photo = _photo(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        megtett = move_preserved_originals(photo, tmp_path / "b.jpg")

        maradek = undo_original_moves(megtett)

        assert maradek == ()
        assert (tmp_path / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"eredeti"
        assert not (tmp_path / ORIGINALS_DIR_NAME / "b.jpg").exists()

    def test_originals_slot_free_az_eredetit_es_a_pillanatkepet_is_nezi(
        self, tmp_path
    ):
        assert originals_slot_free(tmp_path, "a.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        assert not originals_slot_free(tmp_path, "a.jpg")
        # a PILLANATKÉP helye is foglaltságot jelent
        assert originals_slot_free(tmp_path, "c.jpg")
        _original(tmp_path, ORIGINALS_DIR_NAME, "c.1.jpg", b"pillanatkep")
        assert not originals_slot_free(tmp_path, "c.jpg")

    def test_originals_slot_free_a_regi_mappanevet_is_nezi(self, tmp_path):
        _original(tmp_path, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi")
        assert not originals_slot_free(tmp_path, "a.jpg")


class TestKotegPotnevPillanatkeppel:
    """#1430 kódszemle, 6. pont: a pótnév-keresés a PILLANATKÉP helyét is
    nézze. Enélkül a köteg átnevezi a képet a forrásmappában, aztán a
    mozgatás elbukik — a kép a felhasználó háta mögött átnevezve marad."""

    def test_foglalt_pillanatkep_hely_nem_valaszthato_potnevnek(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        photo = _photo(forras, "a.jpg", b"koltozo")
        _photo(cel, "a.jpg", b"mar-ott-van")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        _original(cel, ORIGINALS_DIR_NAME, "a-1.1.jpg", b"arva-pillanatkep")

        result = move_photos([photo], cel)

        assert result.failed == ()
        assert not (forras / "a-1.jpg").exists(), (
            "a kép a forrásmappában maradt átnevezve"
        )
        (_, uj_ut), = result.done
        assert uj_ut.read_bytes() == b"koltozo"
        assert (cel / ORIGINALS_DIR_NAME / uj_ut.name).read_bytes() == b"eredeti"

    def test_a_foglalt_eredeti_hely_utkozesnek_szamit(self, tmp_path):
        """A célban NINCS azonos nevű kép, csak az eredeti helye foglalt.
        Ez ütközés: enélkül a köteg elkerülhető hibával állna meg."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _photo(forras, "a.jpg", b"koltozo")
        _original(forras, ORIGINALS_DIR_NAME, "a.jpg", b"eredeti")
        _original(cel, ORIGINALS_DIR_NAME, "a.jpg", b"arva")

        assert conflicting_names([photo], cel) == (photo,)

        result = move_photos([photo], cel)

        assert result.failed == ()
        (_, uj_ut), = result.done
        assert uj_ut.read_bytes() == b"koltozo"
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"arva"


class TestTervenBeluliDuplikatum:
    """#1430 kódszemle, 4. pont — a terven belüli ütközés őre.

    A `plan_original_moves` ma a sorszám SZÖVEGÉT viszi át, ezért két
    kísérőfájl nem képződhet ugyanarra a célnévre; az őr épp azért marad,
    hogy ha valaha visszakerülne az átszámozás, a `shutil.move` NE írja
    felül némán az egyiket. Mivel a bemenet a mai kóddal nem előállítható,
    a guardot közvetlenül, kézzel épített tervvel mérjük."""

    def test_ugyanarra_a_celnevre_kepzodo_terv_elutasitasa(self, tmp_path):
        cel = tmp_path / ORIGINALS_DIR_NAME / "b.1.jpg"
        terv = (
            OriginalMove(tmp_path / ORIGINALS_DIR_NAME / "a.1.jpg", cel),
            OriginalMove(tmp_path / ORIGINALS_DIR_NAME / "a.01.jpg", cel),
        )

        with pytest.raises(FileExistsError) as hiba:
            _reject_unsafe_targets(terv)

        uzenet = str(hiba.value)
        assert "a.1.jpg" in uzenet
        assert "a.01.jpg" in uzenet
        assert "Semmi nem változott" in uzenet
