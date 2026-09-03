"""#1923: KÉT »Duplikátumok« sor a bal hasábban — mérés, nem feltevés.

A #1909 feltevése az volt, hogy az egyik sor egy régi, offline-jelölt
rekord, a másik a friss beolvasásé, és **ha a kettő ugyanarra az
útvonalra mutat, az önmagában is hiba**. Ez a fájl azt méri le, hogy ez
a helyzet **elő sem állhat** — és hogy a valódi ok más.

## A három mért tény

1. `folders.path` **UNIQUE** (`schema.py`): két sor ugyanarra az
   útvonalra be sem szúrható.
2. `sorted_folder_rows` `GROUP BY f.id`-vel dolgozik: mappánként PONTOSAN
   egy sor jön vissza.
3. A sor `name` mezője az útvonal **utolsó szakasza** (alapnév), nem a
   teljes út.

⇒ Két »Duplikátumok« feliratú sor **két KÜLÖNBÖZŐ mappa**. Ez nem hiba,
hanem a duplikátum-kereső természetes következménye: minden
forrásmappában SAJÁT `Duplikátumok` alkönyvtárat hoz létre
(`dedup_controller.DUPLICATES_SUBFOLDER_NAME`), tehát több ilyen nevű
mappa **várható**.

A megmaradó valódi gond — hogy a lapos listán a két sor
megkülönböztethetetlen — külön jegy, mert külön is megvalósítható.
"""

from __future__ import annotations

import sqlite3

import pytest

from picasapy.app.dedup_controller import DUPLICATES_SUBFOLDER_NAME
from picasapy.app.models import sorted_folder_rows
from picasapy.index import open_index


@pytest.fixture
def conn(tmp_path):
    with open_index(tmp_path / "index.db") as c:
        yield c


def _mappa(conn, ut: str, *, offline: int = 0) -> int:
    kurzor = conn.execute(
        "INSERT INTO folders (path, offline) VALUES (?, ?)", (ut, offline)
    )
    return int(kurzor.lastrowid)


class TestAzIndexNemEngedDuplikatumot:
    def test_ugyanarra_az_utvonalra_NEM_szurhato_be_ketto(self, conn):
        """Ez a #1909 feltevésének közvetlen cáfolata."""
        _mappa(conn, "/kepek/nyar/Duplikátumok")
        with pytest.raises(sqlite3.IntegrityError):
            _mappa(conn, "/kepek/nyar/Duplikátumok")

    def test_az_OFFLINE_jelolt_sem_kerulhet_be_masodszor(self, conn):
        """A feltevés szerint az egyik sor a régi, offline rekord volt —
        de az sem lehet KÜLÖN sor ugyanarra az útvonalra."""
        _mappa(conn, "/kepek/nyar/Duplikátumok", offline=1)
        with pytest.raises(sqlite3.IntegrityError):
            _mappa(conn, "/kepek/nyar/Duplikátumok", offline=0)


class TestAModellMappankentEgySort:
    def test_harom_mappa_harom_sor(self, conn):
        for ut in ("/kepek/a", "/kepek/b", "/kepek/c"):
            _mappa(conn, ut)
        assert len(sorted_folder_rows(conn)) == 3

    def test_ugyanaz_a_mappa_egyszer_szerepel(self, conn):
        _mappa(conn, "/kepek/nyar/Duplikátumok")
        utak = [sor[1] for sor in sorted_folder_rows(conn)]
        assert utak.count("/kepek/nyar/Duplikátumok") == 1


class TestKetAzonosNevuMappa:
    """A tulajdonos által látott jelenség REPRODUKCIÓJA — és a magyarázata."""

    def test_ket_kulonbozo_szulo_alatt_KET_sor_jon_azonos_nevvel(self, conn):
        nyar = f"/kepek/nyar/{DUPLICATES_SUBFOLDER_NAME}"
        tel = f"/kepek/tel/{DUPLICATES_SUBFOLDER_NAME}"
        _mappa(conn, nyar, offline=1)
        _mappa(conn, tel)

        sorok = sorted_folder_rows(conn)
        azonos_nevu = [s for s in sorok if s[0] == DUPLICATES_SUBFOLDER_NAME]

        assert len(azonos_nevu) == 2, (
            "nem jött létre a jelenség — a próba nem azt méri, amit kellene"
        )
        # A LÉNYEG: a két sor ÚTVONALA különbözik. Ha valaha egyeznének,
        # az volna a #1909 által gyanított valódi hiba.
        assert {s[1] for s in azonos_nevu} == {nyar, tel}
        # …és az egyik offline, a másik nem — pontosan az a kettősség,
        # amit a tulajdonos látott (dőlt + normál szedés).
        assert {s[6] for s in azonos_nevu} == {True, False}

    def test_a_NEV_az_utvonal_utolso_szakasza(self, conn):
        """Ezért látszik a két sor azonosnak: a felirat csak az alapnév."""
        _mappa(conn, "/kepek/nyar/Duplikátumok")
        nev, ut, *_ = sorted_folder_rows(conn)[0]
        assert nev == "Duplikátumok"
        assert ut.endswith("/kepek/nyar/Duplikátumok")
        assert nev != ut, "a felirat a teljes utat mutatja — akkor ez a jegy tárgytalan"
