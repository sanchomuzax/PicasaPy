"""#1448 — a megőrzött eredeti ini-szekciója is a képpel költözik.

A #1430 óta a megőrzött eredeti FÁJLJA követi a képet, a hozzá tartozó
`.picasaoriginals/.picasa.ini` szekció viszont a forrásban maradt. A
tulajdonos valódi gyűjteményében 52 ilyen ini van, és nem üresek
(`filters=`, `rotate=`, `crop=`, `width/height`, `moddate`).

Két ára van:

1. A párhuzamosan futó windowsos Picasa (a projekt élő kétirányú
   kompatibilitási próbája) ezt az ini-t olvassa — a beállítások elvesznek.
2. Ha később másik, azonos nevű eredeti kerül a forrás eredeti-mappájába,
   **örökli az elárvult beállításokat** — idegen kép adatait kapja meg.

Az őr a szekció TARTALMÁT is nézi, nem csak a létét: a round-trip elv
szerint az ismeretlen kulcsoknak is át kell jönniük.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.edit import LEGACY_ORIGINALS_DIR_NAME, ORIGINALS_DIR_NAME
from picasapy.fileops import move_photo, rename_photo
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME

_SZEKCIO = (
    "[{nev}]\n"
    "filters=redeye=1;\n"
    "rotate=rotate(1)\n"
    "width=2592\n"
    "height=1944\n"
    "sajat-ismeretlen-kulcs=marad\n"
)


def _kep(mappa: Path, nev: str, tartalom: bytes = b"szerkesztett") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _eredeti(
    mappa: Path, dir_name: str, nev: str, *, ini_nev: str | None = None
) -> Path:
    """Megőrzött eredeti + a hozzá tartozó, NEM üres ini-szekció."""
    directory = mappa / dir_name
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(b"erintetlen")
    ini = directory / PICASA_INI_NAME
    ini.write_text(_SZEKCIO.format(nev=ini_nev or nev), encoding="utf-8")
    return path


def _szekcio(directory: Path, nev: str):
    return load_or_empty(directory / PICASA_INI_NAME).section(nev)


class TestAtnevezes:
    def test_a_szekcio_az_uj_nevre_all(self, tmp_path):
        photo = _kep(tmp_path, "a.jpg")
        _eredeti(tmp_path, ORIGINALS_DIR_NAME, "a.jpg")
        directory = tmp_path / ORIGINALS_DIR_NAME

        rename_photo(photo, "b.jpg")

        assert _szekcio(directory, "a.jpg") is None
        uj = _szekcio(directory, "b.jpg")
        assert uj is not None
        assert uj.get("filters") == "redeye=1;"
        assert uj.get("rotate") == "rotate(1)"
        assert uj.get("sajat-ismeretlen-kulcs") == "marad"

    def test_legacy_mappaban_is(self, tmp_path):
        photo = _kep(tmp_path, "a.jpg")
        _eredeti(tmp_path, LEGACY_ORIGINALS_DIR_NAME, "a.jpg")
        directory = tmp_path / LEGACY_ORIGINALS_DIR_NAME

        rename_photo(photo, "b.jpg")

        assert _szekcio(directory, "a.jpg") is None
        assert _szekcio(directory, "b.jpg") is not None


class TestMozgatas:
    def test_a_szekcio_a_celmappa_inijebe_kerul(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")

        move_photo(photo, cel)

        assert _szekcio(forras / ORIGINALS_DIR_NAME, "a.jpg") is None
        uj = _szekcio(cel / ORIGINALS_DIR_NAME, "a.jpg")
        assert uj is not None
        assert uj.get("width") == "2592"
        assert uj.get("sajat-ismeretlen-kulcs") == "marad"

    def test_a_pillanatkep_szekcioja_is_atszamozodik(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        directory = forras / ORIGINALS_DIR_NAME
        directory.mkdir(parents=True, exist_ok=True)
        (directory / "a.1.jpg").write_bytes(b"pillanatkep")
        (directory / PICASA_INI_NAME).write_text(
            _SZEKCIO.format(nev="a.1.jpg"), encoding="utf-8"
        )

        move_photo(photo, cel)

        assert _szekcio(directory, "a.1.jpg") is None
        assert _szekcio(cel / ORIGINALS_DIR_NAME, "a.1.jpg") is not None

    def test_a_celmappa_tobbi_szekcioja_erintetlen(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel_dir = cel / ORIGINALS_DIR_NAME
        cel_dir.mkdir(parents=True)
        (cel_dir / PICASA_INI_NAME).write_text(
            "[mas.jpg]\nstar=yes\n", encoding="utf-8"
        )
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")

        move_photo(photo, cel)

        assert _szekcio(cel_dir, "mas.jpg").get("star") == "yes"
        assert _szekcio(cel_dir, "a.jpg") is not None

    def test_a_forras_tobbi_szekcioja_erintetlen(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _kep(forras, "mas.jpg")
        directory = forras / ORIGINALS_DIR_NAME
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")
        (directory / "mas.jpg").write_bytes(b"mas-eredeti")
        (directory / PICASA_INI_NAME).write_text(
            _SZEKCIO.format(nev="a.jpg") + "\n[mas.jpg]\nstar=yes\n",
            encoding="utf-8",
        )

        move_photo(photo, cel)

        assert _szekcio(directory, "mas.jpg").get("star") == "yes"
        assert _szekcio(directory, "a.jpg") is None


class TestNincsMitVinni:
    def test_ini_nelkuli_eredeti_nem_hoz_letre_ures_init(self, tmp_path):
        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        directory = forras / ORIGINALS_DIR_NAME
        directory.mkdir(parents=True)
        (directory / "a.jpg").write_bytes(b"erintetlen")

        move_photo(photo, cel)

        assert not (cel / ORIGINALS_DIR_NAME / PICASA_INI_NAME).exists()


class TestVisszagorgetes:
    def test_a_kep_mozgatasanak_bukasakor_a_szekcio_is_visszajon(self, tmp_path):
        """Fél költözés (fájl az új helyen, szekció a régiben) nincs."""
        from picasapy.fileops import originals_follow

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")

        try:
            with originals_follow(photo, cel / "a.jpg"):
                raise OSError("a kép mozgatása elbukott")
        except OSError:
            pass

        assert _szekcio(forras / ORIGINALS_DIR_NAME, "a.jpg") is not None
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").exists()
        assert not (cel / ORIGINALS_DIR_NAME / "a.jpg").exists()

    def test_ini_hiba_eseten_a_fajlok_is_visszaallnak(self, tmp_path, monkeypatch):
        """Ha a szekció-átvitel bukik, a FÁJL sem marad az új helyen."""
        from picasapy.fileops import move_preserved_originals
        from picasapy.fileops import original_ini

        forras = tmp_path / "forras"
        cel = tmp_path / "cel"
        cel.mkdir()
        _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")

        def _bukik(*args, **kwargs):
            raise OSError("az ini nem írható")

        monkeypatch.setattr(original_ini, "move_original_ini_sections", _bukik)

        try:
            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")
        except OSError as error:
            assert "megőrzött eredeti" in str(error)
        else:  # pragma: no cover — az őr épp ezt zárja ki
            raise AssertionError("a hibának ki kellett volna jönnie")

        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").exists()
        assert not (cel / ORIGINALS_DIR_NAME / "a.jpg").exists()
        assert _szekcio(forras / ORIGINALS_DIR_NAME, "a.jpg") is not None

    def test_a_visszagorgetes_nem_rant_be_idegen_szekciot(
        self, tmp_path, monkeypatch
    ):
        """A forrásban SOSEM VOLT szekció → a visszagörgetés se vigyen oda egyet.

        A visszagörgetés korábban a FÁJLÁLLAPOTBÓL következtetett: „ha a
        szekció már nincs a forrásban, akkor elment, hozzuk vissza". A
        gyakori eset viszont az, hogy soha nem is volt ott — ilyenkor az őr
        átengedett, és a CÉL inijéből rántott át egy azonos nevű, ÁRVA
        szekciót. Pontosan az az öröklés, amit ez a jegy megszüntet, csak
        most a javítás hozta volna be.
        """
        from picasapy.fileops import move_preserved_originals
        from picasapy.fileops import originals as originals_module

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        forras_dir = forras / ORIGINALS_DIR_NAME
        forras_dir.mkdir(parents=True)
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        (forras_dir / "a.1.jpg").write_bytes(b"pillanatkep")
        # A forrás eredeti-mappájában NINCS ini — ez a gyakori eset.
        cel_dir = cel / ORIGINALS_DIR_NAME
        cel_dir.mkdir(parents=True)
        (cel_dir / PICASA_INI_NAME).write_text(
            "[b.jpg]\nfilters=IDEGEN\ncrop=rect64(1111)\n", encoding="utf-8"
        )

        valodi_move = originals_module._move
        hivas = {"n": 0}

        def _masodiknal_bukik(source, target):
            hivas["n"] += 1
            if hivas["n"] == 2:
                raise OSError("a fájlrendszer nem engedte")
            return valodi_move(source, target)

        monkeypatch.setattr(originals_module, "_move", _masodiknal_bukik)

        with pytest.raises(OSError):
            move_preserved_originals(forras / "a.jpg", cel / "b.jpg")

        # A forrás inije NEM keletkezhetett meg egy idegen szekcióból.
        assert _szekcio(forras_dir, "a.jpg") is None
        # És a cél árva szekcióját sem loptuk el.
        assert _szekcio(cel_dir, "b.jpg") is not None


def _update_document_bukik_a(hivas_sorszamok: set[int], monkeypatch):
    """A `original_ini.update_document` MEGADOTT SORSZÁMÚ hívásait buktatja.

    A szekció-költözés fájlok KÖZÖTT kétfázisú (előbb a cél ini-je, utána a
    forrásé), és a két fázis közti bukás a #1448 saját hibaosztálya: a
    célban FRISSEN ÜLTETETT árva marad. A hívás sorszámára kell tudni
    célozni, mert épp az a kérdés, MELYIK fázisban buktunk el.
    """
    from picasapy.fileops import original_ini

    valodi = original_ini.update_document
    szamlalo = {"n": 0}

    def _burkolo(*args, **kwargs):
        szamlalo["n"] += 1
        if szamlalo["n"] in hivas_sorszamok:
            raise OSError(f"az ini nem írható ({szamlalo['n']}. hívás)")
        return valodi(*args, **kwargs)

    monkeypatch.setattr(original_ini, "update_document", _burkolo)
    return szamlalo


class TestFelbemaradtSzekcioKoltozes:
    """#1448 2. átnézés, 3. lelet: a KÉTFÁZISÚ lépés is a `done`-ba tartozik.

    A fájlok közti szekció-költözés két `update_document`-ből áll: előbb a
    CÉL inijébe írunk, utána a forráséból törlünk. Ha a második bukik el, a
    lépés se nem történt meg, se nem maradt el — de a `done`-ból kimaradt,
    így a visszagörgetés nem tudott róla, és a célban FRISSEN ÜLTETETT árva
    szekció maradt. Pontosan az az öröklés, amit ez a jegy megszüntet.
    """

    def test_a_felig_megtett_lepes_bekerul_a_done_ba(self, tmp_path, monkeypatch):
        from picasapy.fileops.original_ini import (
            IniSectionsFailed,
            move_original_ini_sections,
        )

        forras_dir = tmp_path / "A" / ORIGINALS_DIR_NAME
        cel_dir = tmp_path / "B" / ORIGINALS_DIR_NAME
        forras_dir.mkdir(parents=True)
        cel_dir.mkdir(parents=True)
        (forras_dir / "a.jpg").write_bytes(b"erintetlen")
        (forras_dir / PICASA_INI_NAME).write_text(
            _SZEKCIO.format(nev="a.jpg"), encoding="utf-8"
        )
        _update_document_bukik_a({2}, monkeypatch)  # a forrásból törlés bukik

        with pytest.raises(IniSectionsFailed) as elkapva:
            move_original_ini_sections(
                ((forras_dir / "a.jpg", cel_dir / "a.jpg"),)
            )

        assert elkapva.value.done, (
            "a célba írás MEGTÖRTÉNT, tehát a visszagörgetésnek tudnia kell róla"
        )

    def test_a_celban_nem_marad_frissen_ultetett_arva(self, tmp_path, monkeypatch):
        """A teljes mozgatási úton mérve: a megnyugtató mondat IGAZ legyen."""
        from picasapy.fileops import move_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")
        _update_document_bukik_a({2}, monkeypatch)

        with pytest.raises(OSError) as elkapva:
            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        assert _szekcio(cel / ORIGINALS_DIR_NAME, "a.jpg") is None, (
            "a célban árva szekció maradt — ezt örökölné a következő eredeti"
        )
        assert _szekcio(forras / ORIGINALS_DIR_NAME, "a.jpg") is not None
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").exists()
        assert not (cel / ORIGINALS_DIR_NAME).exists(), (
            "üres eredeti-mappa maradt a célban, miközben „semmi nem változott”"
        )
        assert "A kép nem mozdult el" in str(elkapva.value)

    def test_ha_a_visszagorgetes_is_bukik_azt_kimondjuk(self, tmp_path, monkeypatch):
        """A `_undo_ini_sections` eredménye NEM eshet a padlóra.

        Ha a szekciót nem sikerül visszatenni, a „minden a helyén maradt”
        mondat hazugság: a beállítások a célban ragadtak.
        """
        from picasapy.fileops import move_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")
        # 2.: a forrásból törlés bukik → félig megtett lépés;
        # 3.: a visszagörgetés első fázisa is bukik → a szekció ott ragad.
        _update_document_bukik_a({2, 3}, monkeypatch)

        with pytest.raises(OSError) as elkapva:
            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        uzenet = str(elkapva.value)
        assert "A kép nem mozdult el" not in uzenet, (
            "a megnyugtatás HAMIS, amíg a beállítások a célban ragadtak"
        )
        assert "beállítás" in uzenet.lower()
        assert str(cel / ORIGINALS_DIR_NAME / PICASA_INI_NAME) in uzenet


class TestTobbKiseroVisszagorgetese:
    """#1448 2. átnézés, 6. lelet: a KRITIKUS javítás mozgatási ágának foga.

    Az `originals.py` a kivétel `done` mezőjéből görgeti vissza a MÁR
    átvitt szekciókat. Erre eddig nem volt próba: az `error.done` helyére
    üres sorozatot írva 440 teszt maradt zöld.
    """

    def test_az_elso_kisero_szekcioja_visszakerul(self, tmp_path, monkeypatch):
        from picasapy.fileops import move_preserved_originals

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        _kep(forras, "a.jpg")
        directory = forras / ORIGINALS_DIR_NAME
        directory.mkdir(parents=True)
        (directory / "a.jpg").write_bytes(b"erintetlen")
        (directory / "a.1.jpg").write_bytes(b"pillanatkep")
        (directory / PICASA_INI_NAME).write_text(
            _SZEKCIO.format(nev="a.jpg") + "\n" + _SZEKCIO.format(nev="a.1.jpg"),
            encoding="utf-8",
        )
        # 1–2.: az ELSŐ kísérő szekciója rendben átmegy;
        # 3.: a másodiké a cél inijébe íráskor bukik.
        _update_document_bukik_a({3}, monkeypatch)

        with pytest.raises(OSError):
            move_preserved_originals(forras / "a.jpg", cel / "a.jpg")

        assert _szekcio(directory, "a.jpg") is not None, (
            "a már átvitt szekciót nem hoztuk vissza a forrásba"
        )
        assert _szekcio(directory, "a.1.jpg") is not None
        assert _szekcio(cel / ORIGINALS_DIR_NAME, "a.jpg") is None, (
            "a már átvitt szekció a célban maradt — árva lett"
        )

    def test_a_kep_bukasakor_is_kimondjuk_a_bennragadt_szekciot(
        self, tmp_path, monkeypatch
    ):
        """Ugyanez az `originals_follow` úton: a KÉP mozgatása bukik el.

        A kísérők és a szekcióik már átmentek; a visszagörgetés a fájlokkal
        elkészül, a szekcióval nem. A felhasználó a KÉP hibaüzenetét kapja —
        abban kell megjelennie annak is, hogy a beállítás a célban ragadt.
        """
        from picasapy.fileops import originals_follow

        forras = tmp_path / "A"
        cel = tmp_path / "B"
        cel.mkdir()
        photo = _kep(forras, "a.jpg")
        _eredeti(forras, ORIGINALS_DIR_NAME, "a.jpg")
        # 1–2.: a szekció rendben átmegy; 3.: a visszavitele bukik.
        _update_document_bukik_a({3}, monkeypatch)

        with pytest.raises(OSError) as elkapva:
            with originals_follow(photo, cel / "a.jpg"):
                raise OSError("a képet nem sikerült átmozgatni")

        uzenet = str(elkapva.value)
        assert "a képet nem sikerült átmozgatni" in uzenet
        assert str(cel / ORIGINALS_DIR_NAME / PICASA_INI_NAME) in uzenet, (
            "a célban ragadt beállításról a felhasználó nem tud"
        )
        assert (forras / ORIGINALS_DIR_NAME / "a.jpg").exists()
