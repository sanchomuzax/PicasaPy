"""#1450 — a kép MÁSOLÁSA is viszi a megőrzött eredetit.

A `copy_photo` a képfájlt és az ini-szekciót másolta, a
`.picasaoriginals/` (vagy `Originals/`) alatti megőrzött eredetihez nem
nyúlt. A másolat az új helyen nem tudott visszaállni: a „Vissza az
eredetihez" nem talált semmit, a szerkesztés a példányon véglegesnek
látszott.

Az „After copying: delete" import-mód (`import_source_controller`) ugyanez
plusz forrástörlés — vagyis TÉNYLEGES mozgatás. Ott a hiány adatvesztéssé
vált: a forrás eredetije a törléssel elérhetetlenné lett.

Az őr a felhasználó felé látszó funkciót méri (`find_original_backup`), nem
csak a fájlok helyét.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit import (
    LEGACY_ORIGINALS_DIR_NAME,
    ORIGINALS_DIR_NAME,
    find_original_backup,
)
from picasapy.fileops import copy_photo
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME


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


class TestMasolas:
    def test_az_eredeti_a_masolattal_jon(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        target = copy_photo(photo, cel)

        backup = find_original_backup(target)
        assert backup is not None
        assert backup.read_bytes() == b"erintetlen"

    def test_a_forras_eredetije_a_helyen_marad(self, tmp_path):
        """A másolás NEM destruktív — a forrás visszaútja is megmarad."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        copy_photo(photo, cel)

        assert find_original_backup(photo) is not None

    def test_legacy_mappanev_marad_legacy(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, LEGACY_ORIGINALS_DIR_NAME, "a.jpg", b"regi")

        target = copy_photo(photo, cel)

        assert (cel / LEGACY_ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"regi"
        assert not (cel / ORIGINALS_DIR_NAME).exists()
        assert find_original_backup(target).read_bytes() == b"regi"

    def test_a_pillanatkepek_is_atjonnek(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.2.jpg", b"masodik-mentes")

        copy_photo(photo, cel)

        directory = cel / ORIGINALS_DIR_NAME
        assert (directory / "a.1.jpg").read_bytes() == b"elso-mentes"
        assert (directory / "a.2.jpg").read_bytes() == b"masodik-mentes"

    def test_utkozeskor_atnevezett_masolat_eredetije_is_atnevezodik(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        _kep(cel, "a.jpg", b"mar-ott-volt")
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"elso-mentes")

        target = copy_photo(photo, cel)

        assert target.name == "a-1.jpg"
        directory = cel / ORIGINALS_DIR_NAME
        assert (directory / "a-1.jpg").read_bytes() == b"erintetlen"
        assert (directory / "a-1.1.jpg").read_bytes() == b"elso-mentes"
        assert find_original_backup(target).read_bytes() == b"erintetlen"

    def test_az_ini_szekcio_is_atjon(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        (forras / ORIGINALS_DIR_NAME / PICASA_INI_NAME).write_text(
            "[a.jpg]\nfilters=redeye=1;\nrotate=rotate(1)\n", encoding="utf-8"
        )

        copy_photo(photo, cel)

        szekcio = load_or_empty(
            cel / ORIGINALS_DIR_NAME / PICASA_INI_NAME
        ).section("a.jpg")
        assert szekcio is not None
        assert szekcio.get("filters") == "redeye=1;"
        # A forrás szekciója megmarad (a másolás nem destruktív).
        assert (
            load_or_empty(forras / ORIGINALS_DIR_NAME / PICASA_INI_NAME).section("a.jpg")
            is not None
        )

    def test_eredeti_nelkuli_kep_masolasa_nem_hoz_letre_ures_mappat(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")

        copy_photo(photo, cel)

        assert not (cel / ORIGINALS_DIR_NAME).exists()
        assert not (cel / LEGACY_ORIGINALS_DIR_NAME).exists()


class TestBukas:
    def test_bukott_eredeti_masolas_utan_nem_marad_fel_masolat(
        self, tmp_path, monkeypatch
    ):
        """Fél másolat (kép igen, eredeti nem) NINCS: az a néma
        funkcióvesztés, amit ez a jegy megszüntet."""
        from picasapy.fileops import originals as originals_module

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        def _bukik(*args, **kwargs):
            raise OSError("tele a lemez")

        monkeypatch.setattr(originals_module, "_copy", _bukik)

        with pytest.raises(OSError):
            copy_photo(photo, cel)

        assert not (cel / "a.jpg").exists()
        assert not (cel / ORIGINALS_DIR_NAME).exists()
        # A forrás mindenestül érintetlen.
        assert photo.read_bytes() == b"szerkesztett"
        assert find_original_backup(photo).read_bytes() == b"erintetlen"


class TestArvaFajlACelban:
    def test_a_celnev_akkor_jo_ha_az_eredeti_helye_is_szabad(self, tmp_path):
        """Egy korábbi költöztetés árvája miatt ne bukjon el a másolás."""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        _eredeti(cel, ORIGINALS_DIR_NAME, "a.jpg", b"arva-idegen")
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")

        target = copy_photo(photo, cel)

        assert target.name == "a-1.jpg"
        assert find_original_backup(target).read_bytes() == b"erintetlen"
        # Az árva fájlhoz NEM nyúltunk: lehet, hogy egy élő kép eredetije.
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"arva-idegen"

    def test_eredeti_nelkuli_kep_sem_ULHET_az_arvara(self, tmp_path):
        """⚠️ #2569 — EZ A PRÓBA KORÁBBAN A HIBÁT RÖGZÍTETTE.

        A régi állítása („ha nincs mit megőrizni, a `.picasaoriginals`
        tartalma nem számít") azt szentesítette, hogy a kísérő nélküli kép
        ráülhet egy idegen árva eredetire. MÉRVE (2026-09-06): a másolatra
        hívott `find_original_backup` ilyenkor az IDEGEN árva bájtjait
        adta vissza — a felhasználó a saját képén egy vadidegen kép régi
        változatát kapta „megőrzött eredetiként", és a „Vissza az
        eredetihez" azt töltötte volna vissza.

        A helyes viselkedés: a másolat pótnevet kap, és az árvához nem
        nyúlunk. A „nem tolja el" kényelme nem éri meg az adatvesztést.

        (A gazdás — tehát NEM árva — példány továbbra sem foglal: azt a
        `TestGazdasFoglaltsag` és a #2510 őre méri.)"""
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        _eredeti(cel, ORIGINALS_DIR_NAME, "a.jpg", b"arva-idegen")
        photo = _kep(forras, "a.jpg")

        target = copy_photo(photo, cel)

        assert target.name == "a-1.jpg"
        eredeti = find_original_backup(target)
        assert eredeti is None or eredeti.read_bytes() != b"arva-idegen"
        assert (cel / ORIGINALS_DIR_NAME / "a.jpg").read_bytes() == b"arva-idegen"


class TestGazdasFoglaltsag:
    """A két őr UGYANAZT a halmazt nézze (#1450 átnézés, 4. lelet).

    Az `originals_slot_free` a `snapshot_numbers`-en át kihagyta az önálló
    kép megőrzött eredetijét (ezért „szabadnak" mondta a helyet), a
    `_reject_unsafe_targets` viszont BÁRMELY létező célfájlra dob. A
    `_unique_target` így nem lépett tovább a `-1`-es névre, és a másolás
    elbukott — visszalépés a #1450 ELŐTTI állapothoz képest, ahol a másolás
    még sikerült.
    """

    def test_gazdas_pillanatkep_nev_is_foglalt(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        # A célban `a.1.jpg` egy ÖNÁLLÓ kép, a saját megőrzött eredetijével.
        _kep(cel, "a.1.jpg", b"onallo kep")
        _eredeti(cel, ORIGINALS_DIR_NAME, "a.1.jpg", b"onallo kep eredetije")

        target = copy_photo(photo, cel)

        assert target.name == "a-1.jpg"
        assert find_original_backup(target).read_bytes() == b"erintetlen"
        # Az önálló kép és az eredetije érintetlen.
        assert (cel / "a.1.jpg").read_bytes() == b"onallo kep"
        assert (
            cel / ORIGINALS_DIR_NAME / "a.1.jpg"
        ).read_bytes() == b"onallo kep eredetije"

    def test_a_slot_free_gazdas_foglaltsagot_is_jelez(self, tmp_path):
        """A két őr közös igazsága, közvetlenül mérve."""
        from picasapy.fileops.originals import originals_slot_free

        _kep(tmp_path, "a.1.jpg", b"onallo kep")
        _eredeti(tmp_path, ORIGINALS_DIR_NAME, "a.1.jpg", b"onallo kep eredetije")

        assert not originals_slot_free(tmp_path, "a.jpg")


class TestFelbemaradtMasolas:
    def test_a_masodik_kiseronel_bukva_nem_marad_masolat(
        self, tmp_path, monkeypatch
    ):
        """A `_discard_copies` foga: a MÁR átmásolt kísérőket is takarítja.

        A korábbi próba csak a KÉP másolatát nézte, ezért a `_discard_copies`
        törzse `return`-nel kiütve is zöld maradt (7. lelet).
        """
        from picasapy.fileops import originals as originals_module

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")

        valodi_copy = originals_module._copy
        hivas = {"n": 0}

        def _masodiknal_bukik(source, target):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("tele a lemez")
            return valodi_copy(source, target)

        monkeypatch.setattr(originals_module, "_copy", _masodiknal_bukik)

        with pytest.raises(OSError):
            copy_photo(photo, cel)

        # Se kép, se ELSŐ kísérő, se üres eredeti-mappa nem marad.
        assert not (cel / "a.jpg").exists()
        assert not (cel / ORIGINALS_DIR_NAME).exists()

    def test_bukott_ini_masolas_nem_hagy_frissen_ultetett_arvat(
        self, tmp_path, monkeypatch
    ):
        """Az 5. lelet: a `_discard_copies` csak a FÁJLOKAT törli.

        Ha az ini-írás a MÁSODIK szekciónál dob, az első már benne van a cél
        `.picasa.ini`-jében — és ott is maradt. A következő, azonos nevű
        eredeti örökölte volna.
        """
        from picasapy.fileops import original_ini as original_ini_module

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        (forras / ORIGINALS_DIR_NAME / PICASA_INI_NAME).write_text(
            "[a.jpg]\nfilters=redeye=1;\n[a.1.jpg]\nfilters=crop64=1;\n",
            encoding="utf-8",
        )

        valodi = original_ini_module.update_document
        hivas = {"n": 0}

        def _masodiknal_bukik(*args, **kwargs):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("az ini nem írható")
            return valodi(*args, **kwargs)

        monkeypatch.setattr(original_ini_module, "update_document", _masodiknal_bukik)

        with pytest.raises(OSError):
            copy_photo(photo, cel)

        cel_ini = cel / ORIGINALS_DIR_NAME / PICASA_INI_NAME
        if cel_ini.exists():
            document = load_or_empty(cel_ini)
            assert document.section("a.jpg") is None
            assert document.section("a.1.jpg") is None

    def test_a_bukas_a_celban_allo_arvat_nem_semmisiti_meg(
        self, tmp_path, monkeypatch
    ):
        """A visszavétel a KORÁBBI tartalmat állítja vissza, nem törli."""
        from picasapy.fileops import originals as originals_module
        from picasapy.fileops.originals import copy_preserved_originals

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg", b"erintetlen")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.1.jpg", b"pillanatkep")
        (forras / ORIGINALS_DIR_NAME / PICASA_INI_NAME).write_text(
            "[a.jpg]\nfilters=redeye=1;\n[a.1.jpg]\nfilters=crop64=1;\n",
            encoding="utf-8",
        )
        _kep(cel, "b.jpg")
        cel_dir = cel / ORIGINALS_DIR_NAME
        cel_dir.mkdir(parents=True)
        (cel_dir / PICASA_INI_NAME).write_text(
            "[b.jpg]\nfilters=REGI-ARVA\n", encoding="utf-8"
        )

        from picasapy.fileops import original_ini as original_ini_module

        valodi = original_ini_module.update_document
        hivas = {"n": 0}

        def _masodiknal_bukik(*args, **kwargs):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("az ini nem írható")
            return valodi(*args, **kwargs)

        monkeypatch.setattr(original_ini_module, "update_document", _masodiknal_bukik)
        del originals_module  # csak az import-hurok kedvéért

        with pytest.raises(OSError):
            copy_preserved_originals(forras / "a.jpg", cel / "b.jpg")

        szekcio = load_or_empty(cel_dir / PICASA_INI_NAME).section("b.jpg")
        assert szekcio is not None
        assert szekcio.get("filters") == "REGI-ARVA"
