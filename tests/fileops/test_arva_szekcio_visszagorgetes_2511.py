"""#2511 — a mozgatás visszagörgetése is MEGŐRZI a célban állt árva szekciót.

A másolás ága (#1450) már megjegyezte, mi állt a célnéven
(`IniSectionCopy.previous`), és a kör ezt kimondott elvként is rögzítette:

    „Az árva megtartása szándékos: nem a mi dolgunk eldönteni, hogy egy
    bukott másolás ürügyén a felhasználó régi adata is elvesszen."

A MOZGATÁS ágán ez az elv nem érvényesült: a `_placed` (fájlok között) és a
`_dropped_stale` (fájlon belül) elnyelte a célnéven állót, és teljes
visszagörgetés után a felhasználó korábbi, árva szekciója NYOMTALANUL
eltűnt. Mérve 2026-09-06, mind a három ágon:

* azonos fájlon belüli átnevezés (`source_ini == target_ini`):
  a `[b.jpg] filters=ARVA-DE-A-FELHASZNALOE` eltűnt;
* fájlok között: a cél ini `''` lett;
* `_HalfApplied` (a célba írás megtörtént, a forrásból törlés nem):
  ugyanúgy `''`.

A jegy második fele a célmappában maradó, CSAK `.picasa.ini`-t tartalmazó
eredeti-mappa — a legacy `Originals/` esetben ez LÁTHATÓ mappa. Ezt a
másolás visszavétele hagyta ott (mérve ugyanaznap), és a
`undo_copied_ini_sections` takarítja el; a `_remove_if_empty` szándékosan
NEM nyúl hozzá (ld. a docstringjét).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit import LEGACY_ORIGINALS_DIR_NAME, ORIGINALS_DIR_NAME
from picasapy.fileops import move_photo, rename_photo
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME

ARVA = "filters=ARVA-DE-A-FELHASZNALOE"
SAJAT = "filters=SAJAT"


def _kep(mappa: Path, nev: str) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    path = mappa / nev
    path.write_bytes(b"szerkesztett")
    return path


def _eredeti_mappa(mappa: Path, dir_name: str, ini: str | None) -> Path:
    directory = mappa / dir_name
    directory.mkdir(parents=True, exist_ok=True)
    if ini is not None:
        (directory / PICASA_INI_NAME).write_text(ini, encoding="utf-8")
    return directory


def _szekcio(directory: Path, nev: str):
    return load_or_empty(directory / PICASA_INI_NAME).section(nev)


def _buktat(monkeypatch, modul, nev: str) -> None:
    def _bumm(*args, **kwargs):
        raise OSError("a fájlrendszer nem engedte")

    monkeypatch.setattr(modul, nev, _bumm)


class TestArvaSzekcioTullel:
    """A három ág külön-külön — nem ugyanaz a kód fut bennük."""

    def test_azonos_fajlon_beluli_atnevezesnel(self, tmp_path, monkeypatch):
        """(a) `source_ini == target_ini`: a `_dropped_stale` ága."""
        from picasapy.fileops import rename as rename_modul

        photo = _kep(tmp_path, "a.jpg")
        directory = _eredeti_mappa(
            tmp_path,
            ORIGINALS_DIR_NAME,
            f"[a.jpg]\n{SAJAT}\n[b.jpg]\n{ARVA}\n",
        )
        (directory / "a.jpg").write_bytes(b"erintetlen")

        _buktat(monkeypatch, rename_modul, "_rename")
        with pytest.raises(OSError):
            rename_photo(photo, "b.jpg")

        maradt = _szekcio(directory, "b.jpg")
        assert maradt is not None, "az árva szekció nyomtalanul eltűnt"
        assert maradt.get("filters") == "ARVA-DE-A-FELHASZNALOE"
        # És a sajátunk is visszakapta a régi nevét.
        sajat = _szekcio(directory, "a.jpg")
        assert sajat is not None and sajat.get("filters") == "SAJAT"

    def test_kulonbozo_fajlok_kozott(self, tmp_path, monkeypatch):
        """(b) `source_ini != target_ini`: a `_placed` ága."""
        from picasapy.fileops import move as move_modul

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras, ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        cel_dir = _eredeti_mappa(cel, ORIGINALS_DIR_NAME, f"[a.jpg]\n{ARVA}\n")

        _buktat(monkeypatch, move_modul, "_move")
        with pytest.raises(OSError):
            move_photo(photo, cel)

        maradt = _szekcio(cel_dir, "a.jpg")
        assert maradt is not None, "az árva szekció nyomtalanul eltűnt"
        assert maradt.get("filters") == "ARVA-DE-A-FELHASZNALOE"
        sajat = _szekcio(forras_dir, "a.jpg")
        assert sajat is not None and sajat.get("filters") == "SAJAT"
        assert (forras_dir / "a.jpg").is_file()

    def test_felig_megtett_lepesnel(self, tmp_path, monkeypatch):
        """(c) `_HalfApplied`: a szekció MINDKÉT ini-ben ott van.

        A célba írás megtörtént, a forrásból törlés nem — a lépés a
        `done`-ba tartozik, és a `previous`-t is magával kell hoznia,
        különben a visszagörgetés a felhasználó árváját a frissen
        ültetettel EGYÜTT törli.
        """
        from picasapy.fileops import original_ini as ini_modul
        from picasapy.fileops.originals import move_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras, ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        cel_dir = _eredeti_mappa(cel, ORIGINALS_DIR_NAME, f"[a.jpg]\n{ARVA}\n")

        valodi = ini_modul.update_document
        hivas = {"n": 0}

        def _masodiknal_bukik(*args, **kwargs):
            hivas["n"] += 1
            if hivas["n"] == 2:  # a FORRÁSBÓL törlés — a célba írás már megvolt
                raise OSError("az ini nem írható")
            return valodi(*args, **kwargs)

        monkeypatch.setattr(ini_modul, "update_document", _masodiknal_bukik)
        with pytest.raises(OSError):
            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        maradt = _szekcio(cel_dir, "a.jpg")
        assert maradt is not None, "az árva szekció nyomtalanul eltűnt"
        assert maradt.get("filters") == "ARVA-DE-A-FELHASZNALOE"
        sajat = _szekcio(forras_dir, "a.jpg")
        assert sajat is not None and sajat.get("filters") == "SAJAT"


class TestALepesMegjegyzi:
    """A visszagörgetés EGYETLEN forrása a megtett lépés (#1448 átnézés, 1.
    lelet): a fájlállapotból nem következtethető ki, mi állt a célnéven.
    Ezért a `previous`-t magán a lépésen kell mérni — a végállapot ugyanis
    akkor is ép marad, ha a művelet el sem indult, és a fenti integrációs
    őrök ezt nem tudják megkülönböztetni."""

    def test_azonos_fajlon_belul_megjegyzi(self, tmp_path):
        from picasapy.fileops.original_ini import move_original_ini_sections

        directory = _eredeti_mappa(
            tmp_path,
            ORIGINALS_DIR_NAME,
            f"[a.jpg]\n{SAJAT}\n[b.jpg]\n{ARVA}\n",
        )
        (directory / "a.jpg").write_bytes(b"erintetlen")

        done = move_original_ini_sections(
            ((directory / "a.jpg", directory / "b.jpg"),)
        )

        assert len(done) == 1
        assert done[0].previous is not None, "a célnéven állt árva nincs megjegyezve"
        assert done[0].previous.get("filters") == "ARVA-DE-A-FELHASZNALOE"

    def test_fajlok_kozott_megjegyzi(self, tmp_path):
        from picasapy.fileops.original_ini import move_original_ini_sections

        forras_dir = _eredeti_mappa(
            tmp_path / "A", ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        cel_dir = _eredeti_mappa(
            tmp_path / "B", ORIGINALS_DIR_NAME, f"[a.jpg]\n{ARVA}\n"
        )

        done = move_original_ini_sections(
            ((forras_dir / "a.jpg", cel_dir / "a.jpg"),)
        )

        assert len(done) == 1
        assert done[0].previous is not None, "a célnéven állt árva nincs megjegyezve"
        assert done[0].previous.get("filters") == "ARVA-DE-A-FELHASZNALOE"

    def test_ures_celnevnel_nincs_previous(self, tmp_path):
        """A megjegyzés nem gyárthat magának előzményt: ahol semmi nem
        állt, ott a `previous` `None` marad — különben a visszagörgetés
        egy sosem volt szekciót ültetne a felhasználó mappájába."""
        from picasapy.fileops.original_ini import move_original_ini_sections

        forras_dir = _eredeti_mappa(
            tmp_path / "A", ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        cel_dir = _eredeti_mappa(tmp_path / "B", ORIGINALS_DIR_NAME, None)

        done = move_original_ini_sections(
            ((forras_dir / "a.jpg", cel_dir / "a.jpg"),)
        )

        assert len(done) == 1
        assert done[0].previous is None


class TestAmiNemVoltAzTUNJONEL:
    """A megőrzés nem jelenthet szemetelést: ha a célnéven SEMMI nem állt, a
    frissen ültetett szekciónak nyoma sem maradhat — és a MOST keletkezett,
    üresre fogyott ini (a `.bak` párjával) sem."""

    def test_a_frissen_ultetett_szekcio_es_az_ini_is_eltunik(
        self, tmp_path, monkeypatch
    ):
        from picasapy.fileops import move as move_modul

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras, LEGACY_ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")

        _buktat(monkeypatch, move_modul, "_move")
        with pytest.raises(OSError):
            move_photo(photo, cel)

        # A legacy `Originals/` LÁTHATÓ mappa — nem maradhat ott.
        assert not (cel / LEGACY_ORIGINALS_DIR_NAME).exists()
        assert sorted(p.name for p in cel.iterdir()) == []

    def test_a_visszaallitott_arva_inijet_nem_torli(self, tmp_path, monkeypatch):
        """A takarítás CSAK az üres inire vonatkozik: amibe visszakerült a
        felhasználó árvája, az nem üres, tehát marad."""
        from picasapy.fileops import move as move_modul

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras, LEGACY_ORIGINALS_DIR_NAME, f"[a.jpg]\n{SAJAT}\n"
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        cel_dir = _eredeti_mappa(
            cel, LEGACY_ORIGINALS_DIR_NAME, f"[a.jpg]\n{ARVA}\n"
        )

        _buktat(monkeypatch, move_modul, "_move")
        with pytest.raises(OSError):
            move_photo(photo, cel)

        assert (cel_dir / PICASA_INI_NAME).is_file()
        assert _szekcio(cel_dir, "a.jpg") is not None


class TestContentlessTakaritas:
    """A `_remove_if_contentless` szerződése közvetlenül — a fenti,
    integrációs eseteken kívül is ki kell mondani, mit töröl."""

    def test_ures_init_torol_a_bakkal_egyutt(self, tmp_path):
        from picasapy.fileops.original_ini import _remove_if_contentless

        ini = tmp_path / PICASA_INI_NAME
        ini.write_text("", encoding="utf-8")
        bak = tmp_path / (PICASA_INI_NAME + ".bak")
        bak.write_text("", encoding="utf-8")

        _remove_if_contentless(ini)

        assert not ini.exists()
        assert not bak.exists()

    def test_tartalmas_init_nem_torol(self, tmp_path):
        from picasapy.fileops.original_ini import _remove_if_contentless

        ini = tmp_path / PICASA_INI_NAME
        ini.write_text(f"[a.jpg]\n{ARVA}\n", encoding="utf-8")

        _remove_if_contentless(ini)

        assert ini.is_file()


class TestMasolasVisszavetele:
    """#2511 második fele: a bukott MÁSOLÁS se hagyjon a célmappában egy
    csak `.picasa.ini`-t tartalmazó eredeti-mappát.

    Mérve 2026-09-06: a `B/Originals/` ott maradt egy ÜRES `.picasa.ini`-vel
    és a `.bak` párjával, miközben a hibaüzenet azt mondta, „a forrás kép és
    a megőrzött változatai érintetlenek". A `_remove_if_empty` nem tudja
    eltakarítani (az `rmdir` csak ÜRES könyvtárat töröl).
    """

    def test_a_bukott_masolas_nem_hagy_eredeti_mappat(self, tmp_path, monkeypatch):
        from picasapy.fileops import original_ini as ini_modul
        from picasapy.fileops.originals import copy_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras,
            LEGACY_ORIGINALS_DIR_NAME,
            f"[a.jpg]\n{SAJAT}\n[a.1.jpg]\nfilters=PILLANAT\n",
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        (forras_dir / "a.1.jpg").write_bytes(b"pillanatkep")
        _kep(cel, "mas.jpg")  # a célmappa nem üres, de eredeti-mappája nincs

        valodi = ini_modul.update_document
        hivas = {"n": 0}

        def _masodiknal_bukik(*args, **kwargs):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("az ini nem írható")
            return valodi(*args, **kwargs)

        monkeypatch.setattr(ini_modul, "update_document", _masodiknal_bukik)
        with pytest.raises(OSError):
            copy_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        assert not (cel / LEGACY_ORIGINALS_DIR_NAME).exists()
        assert sorted(p.name for p in cel.iterdir()) == ["mas.jpg"]

    def test_a_celban_MAR_MEGVOLT_ini_nem_tunik_el(self, tmp_path, monkeypatch):
        """A takarítás csak a MI fájlunkra vonatkozik: a művelet előtt is
        létező ini (és a benne álló árva) marad."""
        from picasapy.fileops import original_ini as ini_modul
        from picasapy.fileops.originals import copy_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        forras_dir = _eredeti_mappa(
            forras,
            ORIGINALS_DIR_NAME,
            f"[a.jpg]\n{SAJAT}\n[a.1.jpg]\nfilters=PILLANAT\n",
        )
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        (forras_dir / "a.1.jpg").write_bytes(b"pillanatkep")
        cel_dir = _eredeti_mappa(cel, ORIGINALS_DIR_NAME, f"[a.jpg]\n{ARVA}\n")

        valodi = ini_modul.update_document
        hivas = {"n": 0}

        def _masodiknal_bukik(*args, **kwargs):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("az ini nem írható")
            return valodi(*args, **kwargs)

        monkeypatch.setattr(ini_modul, "update_document", _masodiknal_bukik)
        with pytest.raises(OSError):
            copy_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        maradt = _szekcio(cel_dir, "a.jpg")
        assert maradt is not None
        assert maradt.get("filters") == "ARVA-DE-A-FELHASZNALOE"
