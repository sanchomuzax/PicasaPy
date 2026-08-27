"""Az indexkép-nyomtatás geometriája (#1590) — Qt nélkül, determinisztikusan.

A várt értékek KIÍRT LITERÁLOK, nem a termék konstansaiból számolva: a
#1576-nál épp az nyelte el a hibát, hogy a teszt ugyanabból a forrásból
olvasott, amit mérni akart.
"""

from __future__ import annotations

import pytest

from picasapy.printing import PageGeometry
from picasapy.printing.contact_sheet import (
    header_rect,
    rows_per_page,
    sheet_pages,
)

#: A4 álló, 300 dpi-n, 5 mm margóval — a `print_controller` valós számai.
A4_300 = PageGeometry(width=2480, height=3508, margin=59)


class TestSorokEsLapok:
    def test_a4_allo_negy_oszlopnal_ot_sor(self) -> None:
        """A cél a legnégyzetesebb cella: a rács kövesse a lap alakját."""
        assert rows_per_page(A4_300, 4) == 5

    def test_fekvo_lapon_kevesebb_sor(self) -> None:
        fekvo = PageGeometry(width=3508, height=2480, margin=59)

        assert rows_per_page(fekvo, 4) == 3

    def test_legalabb_egy_sor_mindig_van(self) -> None:
        """Nagyon széles lapon a kerekítés nullát adna — az nem lap."""
        lapos = PageGeometry(width=4000, height=300, margin=10)

        assert rows_per_page(lapos, 4) == 1

    def test_husz_kep_egy_lapra_fer(self) -> None:
        lapok = sheet_pages(20, A4_300, 4)

        assert len(lapok) == 1
        assert lapok[0].first == 0
        assert lapok[0].count == 20

    def test_huszonegy_kep_MAR_ket_lap(self) -> None:
        lapok = sheet_pages(21, A4_300, 4)

        assert len(lapok) == 2
        assert (lapok[0].first, lapok[0].count) == (0, 20)
        assert (lapok[1].first, lapok[1].count) == (20, 1)

    def test_a_reszben_teli_lap_cellai_UGYANAKKORAK(self) -> None:
        """⚠️ Ez a lényeg. Ha az utolsó lap a saját képszámából számolna
        rácsot, az egyetlen maradék kép egy egész lapot töltene ki — a
        lapok nem lennének összehasonlíthatók, ami épp az indexkép célja."""
        lapok = sheet_pages(21, A4_300, 4)

        elso = lapok[0].placements[0]
        utolso = lapok[1].placements[0]
        assert (utolso.width, utolso.height) == (elso.width, elso.height)
        assert (utolso.x, utolso.y) == (elso.x, elso.y)

    def test_a_cellak_a_TELJES_kepet_mutatjak(self) -> None:
        """Indexképnél nincs vágás — ez választja el a rács-kollázstól."""
        lapok = sheet_pages(8, A4_300, 4)

        assert all(not cell.fill for cell in lapok[0].placements)

    def test_az_oszlopszam_valtoztatja_a_lapok_szamat(self) -> None:
        # 4 oszlop → 5 sor → 20 kép egy lapon; 2 oszlop → 3 sor → 6 egy
        # lapon, tehát 20 kép NÉGY lapra kerül
        assert len(sheet_pages(20, A4_300, 4)) == 1
        assert len(sheet_pages(20, A4_300, 2)) == 4


class TestFejlec:
    def test_a_fejlec_a_lap_tetejen_all_a_margon_belul(self) -> None:
        x, y, szelesseg, magassag = header_rect(A4_300)

        assert (x, y) == (59, 59)
        assert szelesseg == pytest.approx(2480 - 2 * 59)
        # a nyomtatható magasság 8 %-a (HEADER_RATIO) — kiírt literállal
        assert magassag == pytest.approx((3508 - 2 * 59) * 0.08)

    def test_a_belyegkepek_a_fejlec_ALATT_kezdodnek(self) -> None:
        _x, y, _sz, magassag = header_rect(A4_300)
        lapok = sheet_pages(4, A4_300, 4)

        assert lapok[0].placements[0].y >= y + magassag

    def test_a_cellak_nem_lognak_le_a_laprol(self) -> None:
        lapok = sheet_pages(20, A4_300, 4)

        for cell in lapok[0].placements:
            assert cell.x >= 59
            assert cell.y >= 59
            assert cell.x + cell.width <= 2480 - 59
            assert cell.y + cell.height <= 3508 - 59


class TestHibaagak:
    def test_nulla_kepnel_hibat_dob(self) -> None:
        with pytest.raises(ValueError):
            sheet_pages(0, A4_300, 4)

    def test_ervenytelen_oszlopszamnal_hibat_dob(self) -> None:
        with pytest.raises(ValueError):
            sheet_pages(4, A4_300, 0)
        with pytest.raises(ValueError):
            rows_per_page(A4_300, 0)
