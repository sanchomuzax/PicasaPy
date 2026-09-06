"""#1449 — a pillanatkép-keresés se jokert, se idegen eredetit ne fogadjon el.

A sorszámozott pillanatképek (`<név>.<N><kiterjesztés>`, #444) keresése az
`edit/save.py`-ban `glob()`-bal ment, a `fileops/originals.py`-ban viszont
`iterdir()`-rel. A két szabály KÜLÖNBÖZÖTT, és mindkét eltérésnek volt
felhasználói ára:

1. **Joker-szennyezés.** A `[`, `*`, `?` a `glob()` mintájában joker. Egy
   `IMG[1].jpg` nevű képnél az „Utolsó mentés visszavonása" némán rossz vagy
   nulla pillanatképet talált.
2. **Idegen eredeti.** A névminta kétértelmű: az `a.jpg` kép `a.2.jpg`
   pillanatképe pontosan úgy néz ki, mint egy önálló `a.2.jpg` kép megőrzött
   eredetije. Az `undo_save` a felhasznált pillanatképet TÖRLI — vagyis egy
   másik kép visszaútját semmisítette volna meg.

Az őr a felhasználó felé látszó műveletet (`undo_save`) méri, nem a belső
segédfüggvényt: ha valaha visszakerülne a `glob()`, ezek a próbák buknak.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.edit import ORIGINALS_DIR_NAME, undo_save
from picasapy.edit.save import SaveError, _existing_snapshots
from picasapy.scanner import PICASA_INI_NAME


def _kep(mappa: Path, nev: str, tartalom: bytes = b"szerkesztett") -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    # Az `undo_save` a mappa `.picasa.ini`-jéből olvassa vissza a `redo=`
    # láncot — mentés után az mindig ott van.
    ini = mappa / PICASA_INI_NAME
    if not ini.exists():
        ini.write_text("", encoding="utf-8")
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _pillanatkep(mappa: Path, nev: str, tartalom: bytes) -> Path:
    directory = mappa / ORIGINALS_DIR_NAME
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / nev
    path.write_bytes(tartalom)
    return path


#: #2541: a `*` és a `?` a Windows TILTOTT fájlnév-karakterei
#: (`* ? " < > | : \ /`), ezért az ilyen nevű fájl létrehozása már az
#: íráson elhasal (`OSError: [Errno 22] Invalid argument`) — a main
#: windows-lába emiatt lett piros a `76ad6e89`-en.
#:
#: ⚠️ A kihagyás indoka NEM az, hogy „Windowson nem működik", hanem hogy a
#: vizsgált HELYZET ott elő sem fordulhat: joker-karakteres nevű kép csak
#: POSIX-on létezik. A linuxos fedezet változatlan — ott mindkét próba fut.
#:
#: A szögletes zárójeles próba SZÁNDÉKOSAN nincs kihagyva: a `[` és a `]`
#: Windowson megengedett karakter, és a `glob()`-nak ugyanúgy jokere volt,
#: tehát ott is valódi fedezet.
_WINDOWSON_NEM_LETEZHET = pytest.mark.skipif(
    os.name == "nt",
    reason=(
        "a `*` és a `?` tiltott a Windows fájlneveiben, ezért joker-"
        "karakteres nevű kép ott elő sem fordulhat — a próba tárgya "
        "platformfüggő, nem a kód (#2541)"
    ),
)


class TestJokerKarakter:
    def test_szogletes_zarojeles_nev_pillanatkepe_megtalalhato(self, tmp_path):
        """`IMG[1].jpg`: a `[`/`]` a régi `glob()`-mintában joker volt."""
        kep = _kep(tmp_path, "IMG[1].jpg", b"mentett")
        _pillanatkep(tmp_path, "IMG[1].1.jpg", b"mentes-elotti")

        assert [p.name for _, p in _existing_snapshots(kep)] == ["IMG[1].1.jpg"]

        eredmeny = undo_save(kep)

        assert kep.read_bytes() == b"mentes-elotti"
        assert eredmeny.restored_from.name == "IMG[1].1.jpg"

    @_WINDOWSON_NEM_LETEZHET
    def test_csillagos_nev_nem_szed_ossze_idegen_pillanatkepeket(self, tmp_path):
        """A `*` a mintában MINDENT elfogadott volna: `b.1.jpg`-t is."""
        kep = _kep(tmp_path, "a*.jpg", b"mentett")
        _pillanatkep(tmp_path, "a*.1.jpg", b"sajat")
        _pillanatkep(tmp_path, "ab.1.jpg", b"idegen")

        talalatok = [p.name for _, p in _existing_snapshots(kep)]

        assert talalatok == ["a*.1.jpg"]

    @_WINDOWSON_NEM_LETEZHET
    def test_kerdojeles_nev(self, tmp_path):
        kep = _kep(tmp_path, "a?.jpg", b"mentett")
        _pillanatkep(tmp_path, "a?.1.jpg", b"sajat")
        _pillanatkep(tmp_path, "ax.1.jpg", b"idegen")

        assert [p.name for _, p in _existing_snapshots(kep)] == ["a?.1.jpg"]


class TestIdegenEredeti:
    def test_undo_save_nem_torli_masik_kep_eredetijet(self, tmp_path):
        """`a.2.jpg` KÉP létezik → az azonos nevű fájl az Ő eredetije."""
        kep = _kep(tmp_path, "a.jpg", b"mentett")
        masik = _kep(tmp_path, "a.2.jpg", b"masik-kep")
        idegen_eredeti = _pillanatkep(tmp_path, "a.2.jpg", b"masik-kep-eredetije")

        with pytest.raises(SaveError):
            undo_save(kep)

        assert idegen_eredeti.exists()
        assert idegen_eredeti.read_bytes() == b"masik-kep-eredetije"
        assert masik.read_bytes() == b"masik-kep"
        assert kep.read_bytes() == b"mentett"

    def test_sajat_pillanatkep_meg_akkor_is_hasznalhato_ha_van_idegen(self, tmp_path):
        kep = _kep(tmp_path, "a.jpg", b"mentett")
        _kep(tmp_path, "a.2.jpg", b"masik-kep")
        _pillanatkep(tmp_path, "a.2.jpg", b"masik-kep-eredetije")
        _pillanatkep(tmp_path, "a.1.jpg", b"sajat-mentes-elotti")

        eredmeny = undo_save(kep)

        assert kep.read_bytes() == b"sajat-mentes-elotti"
        assert eredmeny.restored_from.name == "a.1.jpg"
        assert (tmp_path / ORIGINALS_DIR_NAME / "a.2.jpg").exists()


class TestKozosSzabaly:
    def test_ugyanaz_a_kereses_mint_a_fileopsban(self, tmp_path):
        """A két hely KÖZÖS függvényből dolgozik — ne csússzanak szét újra."""
        from picasapy.fileops.originals import snapshot_numbers

        kep = _kep(tmp_path, "IMG[1].jpg")
        _pillanatkep(tmp_path, "IMG[1].1.jpg", b"egy")
        _pillanatkep(tmp_path, "IMG[1].2.jpg", b"ketto")
        directory = tmp_path / ORIGINALS_DIR_NAME

        fileops_talalat = sorted(
            (szam, path) for szam, _, path in snapshot_numbers(directory, kep)
        )

        assert _existing_snapshots(kep) == fileops_talalat

    def test_nem_decimalis_sorszam_kimarad(self, tmp_path):
        """`²` — az `isdigit()` átengedte, az `int()` viszont dobott rá."""
        kep = _kep(tmp_path, "a.jpg")
        _pillanatkep(tmp_path, "a.².jpg", b"nem-sorszam")

        assert _existing_snapshots(kep) == []


class TestSorszamKiosztas:
    def test_a_mentes_nem_irja_felul_masik_kep_eredetijet(self, tmp_path):
        """A kihagyott sorszám nem szabad hely: ott állhat idegen eredeti.

        `a.jpg` mentése az `a.1.jpg` pillanatkép-nevet kérné, de azon a
        néven a MÁSIK, önálló `a.1.jpg` kép megőrzött eredetije áll.

        #2512 óta a felülírás fizikailag kizárt (a pillanatkép külön
        alkönyvtárba megy), a sorszám-átlépés viszont MEGMARADT: ugyanaz a
        sorszám nem létezhet kétszer, két különböző helyen, mert az
        `undo_save` a legnagyobb sorszámot veszi, és egyenlőségnél nem
        tudná eldönteni, melyik a frissebb. Ezért lesz a pillanatkép
        sorszáma 2, nem 1.
        """
        import numpy as np

        from picasapy.edit import EditSession, save_edited
        from picasapy.edit.save import SNAPSHOT_DIR_NAME

        kep = _kep(tmp_path, "a.jpg", b"mentendo")
        _kep(tmp_path, "a.1.jpg", b"masik-kep")
        idegen = _pillanatkep(tmp_path, "a.1.jpg", b"masik-kep-eredetije")

        save_edited(kep, np.zeros((4, 4, 3), dtype=np.uint8), EditSession())

        assert idegen.read_bytes() == b"masik-kep-eredetije"
        sajat = tmp_path / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME / "a.2.jpg"
        assert sajat.read_bytes() == b"mentendo"


class TestKetertelmuNevUzenete:
    """#1449 átnézés, 3. lelet: az „üres vagy hiányzik" ilyenkor HAZUGSÁG.

    Az idegen-eredeti szűrő a `move`/`delete` úton helyes óvatosság, az
    `undo_save`-en viszont hamis negatív: a mappában VAN a képhez illő
    pillanatkép, csak ugyanazon a néven egy önálló kép is áll. Adat nem
    vész el, de a felhasználó elveszíti a visszavonást egy LÉTEZŐ
    pillanatképhez — és az üzenetből azt hiszi, a mappa üres.
    """

    def test_az_uzenet_megnevezi_a_ketertelmu_peldanyt(self, tmp_path):
        kep = _kep(tmp_path, "a.jpg", b"mentett")
        _kep(tmp_path, "a.1.jpg", b"onallo kep")
        _pillanatkep(tmp_path, "a.1.jpg", b"mentes-elotti")

        with pytest.raises(SaveError) as hiba:
            undo_save(kep)

        uzenet = str(hiba.value)
        assert "üres vagy hiányzik" not in uzenet
        assert "a.1.jpg" in uzenet

    def test_valoban_ures_mappanal_marad_a_regi_uzenet(self, tmp_path):
        kep = _kep(tmp_path, "a.jpg", b"mentett")

        with pytest.raises(SaveError) as hiba:
            undo_save(kep)

        assert "üres vagy hiányzik" in str(hiba.value)
