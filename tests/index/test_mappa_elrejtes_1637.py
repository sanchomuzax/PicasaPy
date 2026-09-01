"""#1637 — a mappa elrejtése, index-oldalon.

## A lelet

A `FolderContextMenu` „Mappa elrejtése" tétele **látszott, kattintható
volt, és nem csinált semmit** (`placeholder: true`) — mappa-szintű
elrejtés a Pythonban sehol nem létezett.

## ⚠️ A jelölés SZÁNDÉKOSAN csak az indexben van

Az eredeti a `]hidden` tokennel és a „Rejtett mappák" gyűjteménnyel
dolgozik, de hogy a jelölés a `.picasa.ini`-be, az adatbázisba vagy
mindkettőbe kerül-e, **nincs mérve** — a jegy ezt hatókörön kívülinek
mondja.

Egy **találgatott kulcsot nem írunk** a felhasználó valódi ini-fájljaiba:
a kétirányú ini-kompatibilitás a projekt központi ígérete, és egy rossz
kulcs csendben rontaná el. Amíg a valódi tároló nincs megmérve, a jelölés
az indexben él.
"""

from __future__ import annotations

import pytest

from picasapy.index import (
    hidden_folders,
    is_folder_hidden,
    open_index,
    set_folder_hidden,
    sync_tree,
)
from picasapy.app.models import sorted_folder_rows


@pytest.fixture
def conn(tmp_path):
    gyoker = tmp_path / "kepek"
    (gyoker / "nyaralas").mkdir(parents=True)
    (gyoker / "titkos").mkdir()
    (gyoker / "nyaralas" / "a.jpg").write_bytes(b"1")
    (gyoker / "titkos" / "b.jpg").write_bytes(b"2")
    with open_index(tmp_path / "index.db") as kapcsolat:
        sync_tree(kapcsolat, gyoker)
        yield kapcsolat


def _titkos(tmp_path) -> str:
    return str(tmp_path / "kepek" / "titkos")


class TestAJeloles:
    def test_alapbol_egy_mappa_sem_rejtett(self, conn):
        assert hidden_folders(conn) == ()

    def test_elrejtes_es_visszahozas(self, conn, tmp_path):
        ut = _titkos(tmp_path)
        assert set_folder_hidden(conn, ut, True) is True
        assert is_folder_hidden(conn, ut) is True
        assert hidden_folders(conn) == (ut,)

        set_folder_hidden(conn, ut, False)
        assert is_folder_hidden(conn, ut) is False
        assert hidden_folders(conn) == ()

    def test_ismeretlen_utvonal_nem_kivetel(self, conn, tmp_path):
        """A felület a jelzésből tud üzenetet adni — ne szálljon el."""
        assert set_folder_hidden(conn, str(tmp_path / "nincs"), True) is False
        assert is_folder_hidden(conn, str(tmp_path / "nincs")) is False

    def test_a_lemezen_NEM_mozdul_semmi(self, conn, tmp_path):
        """A jegy külön feltétele: az elrejtés nem fájlművelet."""
        mappa = tmp_path / "kepek" / "titkos"
        set_folder_hidden(conn, str(mappa), True)
        assert mappa.is_dir()
        assert (mappa / "b.jpg").exists()


class TestAHasabListaja:
    def test_a_rejtett_mappa_kimarad(self, conn, tmp_path):
        set_folder_hidden(conn, _titkos(tmp_path), True)
        nevek = [sor[0] for sor in sorted_folder_rows(conn)]
        assert "titkos" not in nevek
        assert "nyaralas" in nevek

    def test_a_rejtett_kapcsoloval_visszajon(self, conn, tmp_path):
        """Ugyanaz a Nézet ▸ Rejtett képek kapcsoló, ami a fotókat is
        visszahozza — nem külön beállítás, és nem egyirányú elrejtés."""
        set_folder_hidden(conn, _titkos(tmp_path), True)
        nevek = [
            sor[0] for sor in sorted_folder_rows(conn, include_hidden=True)
        ]
        assert "titkos" in nevek

    def test_rejtett_nelkul_a_lista_valtozatlan(self, conn):
        alap = sorted_folder_rows(conn)
        assert sorted_folder_rows(conn, include_hidden=True) == alap
