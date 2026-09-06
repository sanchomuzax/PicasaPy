"""#1451 — a törlés nem hagyja árván a megőrzött eredetit.

A lomtárba tett vagy véglegesen törölt képnél a `.picasaoriginals/` (vagy
`Originals/`) alatti példány a helyén maradt. Két baja volt:

1. **Láthatatlanul gyűlt** — teljes méretű JPEG-ek egy rejtett mappában.
2. **A következő, azonos nevű kép EGY IDEGEN kép eredetijét örökölte**: a
   „Vissza az eredetihez" egy teljesen más fénykép változatát adta vissza,
   ami a felhasználó saját képét írta volna felül.

Az őrök a felhasználó felé látszó funkciót mérik: a törlés után egy ÚJ,
azonos nevű kép mellett nem szabad eredetit találni.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    find_original_backup,
)
from picasapy.fileops import delete_photo_permanently, delete_photo_to_trash
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME


@pytest.fixture
def lomtar(tmp_path: Path) -> Path:
    return tmp_path / "lomtar"


def _kep(mappa: Path, nev: str, tartalom: bytes = b"szerkesztett") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _eredeti(mappa: Path, dir_name: str, nev: str, tartalom: bytes) -> Path:
    directory = mappa / dir_name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(tartalom)
    return path


class TestLomtar:
    def test_az_eredeti_sem_marad_a_helyen(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        assert not photo.exists()
        assert not eredeti.exists()

    def test_az_eredeti_visszaallithato_a_lomtarbol(self, tmp_path, lomtar):
        """Nem semmisítjük meg: saját lomtár-bejegyzést kap."""
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        lomtarazott = sorted(p.name for p in (lomtar / "files").iterdir())
        assert lomtarazott == ["a.jpg", "a_1.jpg"]
        infok = sorted(p.name for p in (lomtar / "info").iterdir())
        assert infok == ["a.jpg.trashinfo", "a_1.jpg.trashinfo"]
        tartalmak = {
            (lomtar / "files" / nev).read_bytes() for nev in lomtarazott
        }
        assert tartalmak == {b"szerkesztett", b"erintetlen"}

    def test_uj_azonos_nevu_kep_nem_orokol_idegen_eredetit(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"regi-kep-eredetije")

        delete_photo_to_trash(photo, trash_dir=lomtar)
        uj = _kep(mappa, "a.jpg", b"vadonatuj-kep")

        assert find_original_backup(uj) is None

    def test_a_pillanatkepek_is_mennek(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.2.jpg", b"masodik-mentes")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        assert not (mappa / ORIGINALS_DIR_NAME).exists()

    def test_masik_kep_eredetijehez_nem_nyul(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        masik = _kep(mappa, "b.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"a-eredetije")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "b.jpg", b"b-eredetije")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        assert find_original_backup(masik).read_bytes() == b"b-eredetije"

    def test_a_szamozott_nevu_masik_kep_eredetijet_sem_viszi_el(
        self, tmp_path, lomtar
    ):
        """`a.2.jpg` KÉP létezik → az azonos nevű fájl az Ő eredetije."""
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        masik = _kep(mappa, "a.2.jpg", b"masik-kep")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.2.jpg", b"masik-kep-eredetije")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        assert find_original_backup(masik).read_bytes() == b"masik-kep-eredetije"

    def test_legacy_mappabol_is(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi")

        delete_photo_to_trash(photo, trash_dir=lomtar)

        assert not eredeti.exists()

    def test_az_ini_szekcio_sem_marad_ott(self, tmp_path, lomtar):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "b.jpg", b"b-eredetije")
        _kep(mappa, "b.jpg")
        ini = mappa / ORIGINALS_DIR_NAME / PICASA_INI_NAME
        ini.write_text(
            "[a.jpg]\nfilters=redeye=1;\n\n[b.jpg]\nstar=yes\n", encoding="utf-8"
        )

        delete_photo_to_trash(photo, trash_dir=lomtar)

        document = load_or_empty(ini)
        assert document.section("a.jpg") is None
        assert document.section("b.jpg").get("star") == "yes"

    def test_a_kep_bukasakor_a_kiserok_visszakerulnek(
        self, tmp_path, lomtar, monkeypatch
    ):
        """Fél törlés nincs: ha a kép nem megy, az eredetije sem marad el."""
        from picasapy.fileops import trash as trash_module

        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        valodi_move = trash_module._move

        def _bukik_a_kepnel(source, target):
            if Path(source).name == "a.jpg" and Path(source).parent == mappa:
                raise OSError("a kép nem mozgatható")
            return valodi_move(source, target)

        monkeypatch.setattr(trash_module, "_move", _bukik_a_kepnel)

        with pytest.raises(OSError):
            delete_photo_to_trash(photo, trash_dir=lomtar)

        assert photo.exists()
        assert eredeti.exists()
        assert eredeti.read_bytes() == b"erintetlen"
        assert find_original_backup(photo) is not None
        assert list((lomtar / "info").iterdir()) == []


class TestVeglegesTorles:
    def test_nem_marad_arva_fajl(self, tmp_path):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")

        delete_photo_permanently(photo)

        assert not photo.exists()
        assert not eredeti.exists()
        assert not (mappa / ORIGINALS_DIR_NAME).exists()

    def test_uj_azonos_nevu_kep_nem_orokol(self, tmp_path):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"regi-kep-eredetije")

        delete_photo_permanently(photo)
        uj = _kep(mappa, "a.jpg", b"vadonatuj-kep")

        assert find_original_backup(uj) is None

    def test_masik_kep_eredetije_erintetlen(self, tmp_path):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        masik = _kep(mappa, "b.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"a-eredetije")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "b.jpg", b"b-eredetije")

        delete_photo_permanently(photo)

        assert find_original_backup(masik).read_bytes() == b"b-eredetije"
        assert (mappa / ORIGINALS_DIR_NAME).is_dir()

    def test_eredeti_nelkuli_kep_torolheto(self, tmp_path):
        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")

        delete_photo_permanently(photo)

        assert not photo.exists()


class TestFelTorlesNemNema:
    """#1451 átnézés, 2. lelet: a fél törlés némán ment ki.

    A kísérők ELŐBB mentek a lomtárba, a kép utána. Ha a kép lomtárazása
    bukott, a `_visszatesz` MINDEN hibát elnyelt és semmit nem adott
    vissza — a felhasználó azt látta, hogy a képe a helyén van, közben a
    megőrzött eredetije a lomtárban ült, és a „Vissza az eredetihez" némán
    elromlott. A modul docstringje eközben azt állította: „fél törlés
    nincs".
    """

    def test_a_visszatetel_bukasa_kimondva_jon_ki(self, tmp_path, lomtar, monkeypatch):
        from picasapy.fileops import photo_delete as photo_delete_module
        from picasapy.fileops import trash as trash_module

        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        valodi_move = trash_module._move

        def _bukik_a_kepnel(source, target):
            if Path(source) == photo:
                raise OSError("a kép nem mozgatható")
            return valodi_move(source, target)

        def _a_visszatetel_is_bukik(source, target):
            raise OSError("a visszatétel sem megy")

        monkeypatch.setattr(trash_module, "_move", _bukik_a_kepnel)
        monkeypatch.setattr(photo_delete_module, "_move", _a_visszatetel_is_bukik)

        with pytest.raises(OSError) as hiba:
            delete_photo_to_trash(photo, trash_dir=lomtar)

        uzenet = str(hiba.value)
        # A felhasználó megtudja, HOL vannak a fájljai, és mit ne tegyen.
        assert "lomtár" in uzenet.lower()
        assert "a.jpg" in uzenet
        assert photo.exists()

    def test_windowson_a_kep_megy_elobb(self, tmp_path, monkeypatch):
        """A `SHFileOperationW`-ág a bemeneti utat adja vissza, tehát a
        kísérőket onnan visszatenni ELVILEG lehetetlen — ezért ott a kép
        SIKERES lomtárazása UTÁN mennek."""
        from picasapy.fileops import trash as trash_module

        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        sorrend: list[str] = []

        def _fake_lomtar(p: Path) -> None:
            sorrend.append(str(p))
            Path(p).unlink()

        monkeypatch.setattr(trash_module, "_platform", lambda: "win32")
        monkeypatch.setattr(trash_module, "_windows_lomtarba", _fake_lomtar)

        delete_photo_to_trash(photo)

        assert sorrend == [str(photo), str(mappa / ORIGINALS_DIR_NAME / "a.jpg")]
        assert not photo.exists()
        assert not (mappa / ORIGINALS_DIR_NAME).exists()


class TestVeglegesTorlesHibaaga:
    """#1451 átnézés, 6. lelet: a `maradtak` ág teljesen tesztelettlen volt.

    Ez az az állapot, ahol a kép már VÉGLEGESEN, visszavonhatatlanul
    törlődött, de a kísérője nem — a legdrágább kimenet, amire a `#1451`
    négy meglévő próbája egyszer sem futott rá.
    """

    def test_a_felhasznalo_megtudja_mi_maradt_ott(self, tmp_path, monkeypatch):
        from picasapy.fileops import trash as trash_module

        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        valodi = trash_module.delete_permanently

        def _bukik_a_kiseronel(p):
            if Path(p) == eredeti:
                raise OSError("írásvédett")
            return valodi(p)

        monkeypatch.setattr(
            "picasapy.fileops.photo_delete.delete_permanently", _bukik_a_kiseronel
        )

        with pytest.raises(OSError) as hiba:
            delete_photo_permanently(photo)

        uzenet = str(hiba.value)
        assert str(eredeti) in uzenet
        assert "IDEGEN" in uzenet
        assert not photo.exists()
        assert eredeti.exists()

    def test_a_konyveles_csak_az_elment_kiserokre_fut(self, tmp_path, monkeypatch):
        """A helyben maradt kísérő szekciója MARAD — különben a fájl ott
        állna a beállításai nélkül."""
        from picasapy.fileops import trash as trash_module

        mappa = tmp_path / "kepek"
        photo = _kep(mappa, "a.jpg")
        eredeti = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        pillanatkep = _eredeti(mappa, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        (mappa / ORIGINALS_DIR_NAME / PICASA_INI_NAME).write_text(
            "[a.jpg]\nfilters=redeye=1;\n[a.1.jpg]\nfilters=crop64=1;\n",
            encoding="utf-8",
        )

        valodi = trash_module.delete_permanently

        def _bukik_a_pillanatkepnel(p):
            if Path(p) == pillanatkep:
                raise OSError("írásvédett")
            return valodi(p)

        monkeypatch.setattr(
            "picasapy.fileops.photo_delete.delete_permanently",
            _bukik_a_pillanatkepnel,
        )

        with pytest.raises(OSError):
            delete_photo_permanently(photo)

        document = load_or_empty(mappa / ORIGINALS_DIR_NAME / PICASA_INI_NAME)
        assert not eredeti.exists()
        assert document.section("a.jpg") is None  # elment, a könyvelése is
        assert pillanatkep.exists()
        assert document.section("a.1.jpg") is not None  # ott maradt, a sorai is
