"""#2512 — a mentésenkénti pillanatkép neve nem ütközhet egy ÖNÁLLÓ kép eredetijével.

A #444 óta minden mentés készít egy sorszámozott pillanatképet
(`<név>.<N><kiterjesztés>`), és ez a név KÉTÉRTELMŰ: az `a.jpg` második
mentésének pillanatképe (`a.2.jpg`) bitre ugyanúgy néz ki, mint egy önálló
`a.2.jpg` kép megőrzött, „szent" eredetije. Amíg a kettő UGYANABBAN a
mappában lakott, a `find_original_backup` nem tudta megkülönböztetni őket:
az önálló `a.2.jpg` szerkesztése után a „Vissza az eredetihez" egy IDEGEN
fénykép bájtjait tette a helyére, visszafordíthatatlanul.

A #1449 sorszám-átlépése ezt NEM oldotta meg: az csak a MÁR OTT ÁLLÓ fájl
felülírását akadályozta meg. A fordított irány — előbb `a.jpg`-t mentjük,
és az önálló `a.2.jpg` csak KÉSŐBB kerül szerkesztésre — nyitva maradt.

A megoldás (ADR-010): a „szent" eredeti útja marad
`.picasaoriginals/<név>` (teljes Picasa-kompatibilitás), a MI
pillanatképeink viszont külön alkönyvtárba mennek
(`.picasaoriginals/.picasapy-snapshots/`). A régi helyen álló példányok —
a Picasa írta pillanatképekkel együtt — továbbra is olvashatók.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest

from picasapy.edit import EditSession, ORIGINALS_DIR_NAME, revert, save_edited
from picasapy.edit.save import SNAPSHOT_DIR_NAME, find_original_backup, undo_save
from picasapy.scanner import PICASA_INI_NAME


def _kep(mappa: Path, nev: str, tartalom: bytes) -> Path:
    mappa.mkdir(parents=True, exist_ok=True)
    ini = mappa / PICASA_INI_NAME
    if not ini.exists():
        ini.write_text("", encoding="utf-8")
    path = mappa / nev
    path.write_bytes(tartalom)
    return path


def _png(szin: tuple[int, int, int]) -> np.ndarray:
    kep = np.zeros((4, 4, 3), dtype=np.uint8)
    kep[:, :] = szin
    return kep


class TestIdegenBajtokNemKerulnekVissza:
    """A jegy FŐ őre: a kár a „Vissza az eredetihez" kimenetén látszik."""

    def test_onallo_kep_visszaallitasa_a_sajat_bajtjait_adja(self, tmp_path):
        """`a.jpg` kétszeri mentése után `a.2.jpg` szerkesztése.

        A mai (hibás) elrendezésben a második mentés pillanatképe
        `.picasaoriginals/a.2.jpg`, amit a `find_original_backup` az önálló
        `a.2.jpg` kép eredetijének hisz — a `revert` ezért `a.jpg` egy régi
        állapotát írja bele.
        """
        kep = _kep(tmp_path, "a.png", b"a-kep-eredeti-bajtjai")
        session = EditSession().append_effect("bw", ("1",))
        save_edited(kep, _png((10, 10, 10)), session)
        save_edited(kep, _png((20, 20, 20)), session)

        # A MÁSIK, teljesen önálló kép — a neve véletlenül illik az `a.jpg`
        # pillanatkép-mintájára.
        onallo = _kep(tmp_path, "a.2.png", b"onallo-kep-eredeti-bajtjai")
        save_edited(onallo, _png((99, 99, 99)), EditSession())

        revert(onallo)

        assert onallo.read_bytes() == b"onallo-kep-eredeti-bajtjai"

    def test_a_mentes_nem_hisz_idegen_eredetit_a_sajatjanak(self, tmp_path):
        """A kár GYÖKERE: a mentés `existing_backup`-ot lát, ezért nem
        őrzi meg az önálló kép valódi eredetijét."""
        kep = _kep(tmp_path, "a.png", b"a-kep-eredeti-bajtjai")
        session = EditSession().append_effect("bw", ("1",))
        save_edited(kep, _png((10, 10, 10)), session)
        save_edited(kep, _png((20, 20, 20)), session)

        onallo = _kep(tmp_path, "a.2.png", b"onallo-kep-eredeti-bajtjai")
        eredmeny = save_edited(onallo, _png((99, 99, 99)), EditSession())

        assert eredmeny.backup_created_now, (
            "az önálló képnek MOST kellett volna megőrzött eredetit kapnia"
        )
        assert eredmeny.original_backup_path.read_bytes() == (
            b"onallo-kep-eredeti-bajtjai"
        )

    def test_a_pillanatkep_nem_all_a_szent_eredeti_utjaban(self, tmp_path):
        """A `find_original_backup` útja SOHA nem eshet egybe pillanatképpel."""
        kep = _kep(tmp_path, "a.png", b"eredeti")
        session = EditSession().append_effect("bw", ("1",))
        save_edited(kep, _png((10, 10, 10)), session)
        save_edited(kep, _png((20, 20, 20)), session)

        onallo = _kep(tmp_path, "a.2.png", b"onallo")

        assert find_original_backup(onallo) is None


class TestUjHelyreIr:
    def test_a_pillanatkep_a_sajat_alkonyvtarunkba_kerul(self, tmp_path):
        kep = _kep(tmp_path, "kep.png", b"eredeti")
        session = EditSession().append_effect("bw", ("1",))
        save_edited(kep, _png((1, 2, 3)), session)
        save_edited(kep, _png((4, 5, 6)), session)

        originals = tmp_path / ORIGINALS_DIR_NAME
        # A „szent" eredeti a Picasa által is ismert helyen marad…
        assert sorted(p.name for p in originals.iterdir() if p.is_file()) == [
            "kep.png"
        ]
        # …a pillanatképek viszont a mi alkönyvtárunkban.
        assert sorted(p.name for p in (originals / SNAPSHOT_DIR_NAME).iterdir()) == [
            "kep.1.png",
            "kep.2.png",
        ]

    def test_undo_save_az_uj_helyrol_dolgozik(self, tmp_path):
        kep = _kep(tmp_path, "kep.png", b"eredeti")
        session = EditSession().append_effect("bw", ("1",))
        save_edited(kep, _png((1, 2, 3)), session)
        elso_mentes_utan = kep.read_bytes()
        save_edited(kep, _png((4, 5, 6)), session)

        eredmeny = undo_save(kep)

        assert kep.read_bytes() == elso_mentes_utan
        assert eredmeny.restored_from.parent.name == SNAPSHOT_DIR_NAME
        assert not eredmeny.restored_from.exists()  # a felhasznált példány törlődik


class TestRegiSemaOlvasasaMegmarad:
    """A #444/#1449 óta lemezen álló példányokat nem hagyhatjuk el."""

    def test_a_regi_helyen_allo_sajat_pillanatkep_visszavonhato(self, tmp_path):
        kep = _kep(tmp_path, "a.png", b"mentett")
        directory = tmp_path / ORIGINALS_DIR_NAME
        directory.mkdir()
        (directory / "a.1.png").write_bytes(b"mentes-elotti")

        eredmeny = undo_save(kep)

        assert kep.read_bytes() == b"mentes-elotti"
        assert eredmeny.restored_from == directory / "a.1.png"

    def test_a_regi_es_az_uj_hely_egyutt_lathato(self, tmp_path):
        """Vegyes állapot: a régi helyen egy korábbi verziónk példánya,
        az újban a mostani mentésé — a visszavonás a LEGÚJABBAT viszi."""
        kep = _kep(tmp_path, "a.png", b"regi-mentes-utan")
        directory = tmp_path / ORIGINALS_DIR_NAME
        directory.mkdir()
        (directory / "a.1.png").write_bytes(b"legelso-allapot")

        save_edited(kep, _png((7, 7, 7)), EditSession())

        assert (directory / SNAPSHOT_DIR_NAME / "a.2.png").read_bytes() == (
            b"regi-mentes-utan"
        )

        undo_save(kep)
        assert kep.read_bytes() == b"regi-mentes-utan"

        undo_save(kep)
        assert kep.read_bytes() == b"legelso-allapot"

    def test_a_gazdas_regi_peldanyt_tovabbra_is_bekeh_hagyjuk(self, tmp_path):
        """A #1449 óvatossági szabálya a RÉGI helyen érvényben marad."""
        kep = _kep(tmp_path, "a.png", b"mentett")
        _kep(tmp_path, "a.1.png", b"onallo kep")
        directory = tmp_path / ORIGINALS_DIR_NAME
        directory.mkdir()
        idegen = directory / "a.1.png"
        idegen.write_bytes(b"az onallo kep eredetije")

        from picasapy.edit.save import SaveError

        with pytest.raises(SaveError):
            undo_save(kep)
        assert idegen.read_bytes() == b"az onallo kep eredetije"

    def test_a_picasa_irta_szent_eredetit_tovabbra_is_olvassuk(self, tmp_path):
        """A windowsos Picasa `.picasaoriginals/<név>`-je a mérce."""
        kep = _kep(tmp_path, "a.png", b"a picasa altal szerkesztett")
        directory = tmp_path / ORIGINALS_DIR_NAME
        directory.mkdir()
        (directory / "a.png").write_bytes(b"a picasa altal megorzott eredeti")

        revert(kep)

        assert kep.read_bytes() == b"a picasa altal megorzott eredeti"

    def test_az_uj_alkonyvtarban_nincs_gazda_szures(self, tmp_path):
        """Az ÚJ helyen a névminta nem kétértelmű: ott csak MI írunk.

        Ha a gazda-szűrést odaátra is alkalmaznánk, egy `a.1.png` nevű
        önálló kép puszta létezése elnémítaná a saját visszavonásunkat.
        """
        kep = _kep(tmp_path, "a.png", b"mentett")
        _kep(tmp_path, "a.1.png", b"onallo kep, veletlen egyezes")
        sajat = tmp_path / ORIGINALS_DIR_NAME / SNAPSHOT_DIR_NAME
        sajat.mkdir(parents=True)
        (sajat / "a.1.png").write_bytes(b"a mi mentes elotti allapotunk")

        eredmeny = undo_save(kep)

        assert kep.read_bytes() == b"a mi mentes elotti allapotunk"
        assert eredmeny.restored_from == sajat / "a.1.png"
