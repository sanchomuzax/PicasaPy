"""`picasapy.printing.grid_layout` — a nyomatméret mint CELLA, rácsba
rendezve a papíron, laptöréssel és tájolás-választással (#3647).

Élő referencia (`docs/specs/picasa-nyomtatas.md`, Colab EN 3.9.141,
PDF-nyomtató, A4, 300 dpi):

- 4×6, 1 példány → 1 lap, egy cella középen;
- 4×6, 5 példány → „1 of 3”: 2 + 2 + 1 cella (a rendszer a FEKVŐ A4-et
  választja, mert az kevesebb lapot ad);
- Tárcaméret, 5 példány → 1 lap, sorfolytonos rács: 3 + 2 (itt a két
  tájolás UGYANANNYI lapot adna, tehát a PORTRÉ marad — döntetlennél az
  eredeti)."""

from __future__ import annotations

import pytest

from picasapy.printing.grid_layout import (
    choose_page_orientation,
    grid_pages,
    page_capacity,
)
from picasapy.printing.layout import PageGeometry

_MM_PER_HUVELYK = 25.4


def _huvelyk_lap(szeles_mm: float, magas_mm: float, margo_mm: float = 5.0) -> PageGeometry:
    """Papírméret (mm) hüvelykes `PageGeometry`-ként — a modul mértékegység-
    független, csak a hívó legyen KÖVETKEZETES (itt: hüvelyk)."""
    return PageGeometry(
        width=szeles_mm / _MM_PER_HUVELYK,
        height=magas_mm / _MM_PER_HUVELYK,
        margin=margo_mm / _MM_PER_HUVELYK,
    )


#: Letter, portré (215,9 × 279,4 mm — 8,5 × 11 hüvelyk).
_LETTER_PORTRE = _huvelyk_lap(215.9, 279.4)

#: A4, portré és fekvő (210 × 297 mm) — a Colab élő méréséé.
_A4_PORTRE = _huvelyk_lap(210.0, 297.0)
_A4_FEKVO = _huvelyk_lap(297.0, 210.0)

# a hüvelykes nyomatméretek (`NyomatMeret`) — nem importáljuk az
# `app`-ot, hogy a próba Qt nélkül is fusson
_4X6 = (4.0, 6.0)
_TARCA = (2.5, 3.5)


class TestPageCapacity:
    def test_ket_4x6_letter_portren_ket_oszlop_egy_sor(self):
        columns, rows = page_capacity(_LETTER_PORTRE, *_4X6)
        assert (columns, rows) == (2, 1)

    def test_a_cella_semmilyen_iranyban_nem_fer_el(self):
        parany_lap = PageGeometry(width=1.0, height=1.0)
        columns, rows = page_capacity(parany_lap, *_4X6)
        assert (columns, rows) == (0, 0)


class TestGridPagesLapszamitas:
    def test_ket_4x6_letter_papiron_egy_lapot_ad_ket_cellaval(self):
        """Kész, ha #1: két 4×6-os kép Letter-papíron EGY lapot ad, KÉT
        cellával."""
        lapok = grid_pages(_LETTER_PORTRE, *_4X6, count=2)
        assert len(lapok) == 1
        assert lapok[0].first == 0
        assert lapok[0].count == 2

    def test_ot_4x6_letter_papiron_tulcsordul_a_2_lapra(self):
        """Kész, ha #2: öt 4×6-os kép a papír befogadóképességénél (2)
        több cellát kér, és a túlcsorduló a 2. lap ELSŐ cellája — a
        kép-/példányszámláló FOLYTATÓDIK, nem indul újra."""
        lapok = grid_pages(_LETTER_PORTRE, *_4X6, count=5)
        assert [lap.count for lap in lapok] == [2, 2, 1]
        assert [lap.first for lap in lapok] == [0, 2, 4]

    def test_pontosan_kitolto_cella_nem_esik_ki_a_tures_miatt(self):
        # rontás-kontroll: ha valaki a `FIT_TOLERANCE`-t eltávolítaná (vagy
        # `1.0`-ra állítaná), ez a próba buknia kell — egy lebegőpontosan
        # PONTOSAN kitöltő cella (itt: 2 × 4 hüvelyk egy 8 hüvelykes,
        # margó nélküli lapon) 1e-15 nagyságrendű kerekítési hiba miatt
        # kiesne a rácsból, és a lapszám hamisan megduplázódna.
        lap = PageGeometry(width=8.0, height=8.0, margin=0.0)
        # 8.0 / 4.0 lebegőpontosan nem mindig pontosan 2.0 — a `4.0` itt
        # tudatosan `2.0 + 2.0`-ból jön, hogy a tesztkörnyezet ne
        # rejtse el a hibát egy szerencsés kerekítéssel
        cella = 2.0 + 2.0
        columns, rows = page_capacity(lap, cella, cella)
        assert (columns, rows) == (2, 2)

    def test_ures_kijeloles_hibat_dob(self):
        with pytest.raises(ValueError):
            grid_pages(_LETTER_PORTRE, *_4X6, count=0)

    def test_tulnagy_cella_hibat_dob(self):
        with pytest.raises(ValueError):
            grid_pages(_LETTER_PORTRE, 20.0, 30.0, count=1)


class TestGridPagesTerkoz:
    def test_egyetlen_cella_kozepre_kerul(self):
        """„1 lap, egy cella középen” — a maradék hely egyenletesen a
        cella két oldalára oszlik, tehát a cella középen áll."""
        lapok = grid_pages(_LETTER_PORTRE, *_4X6, count=1)
        assert len(lapok) == 1
        (cella,) = lapok[0].cells
        vart_x = _LETTER_PORTRE.margin + (_LETTER_PORTRE.printable_width - 4.0) / 2
        assert cella.x == pytest.approx(vart_x)

    def test_reszben_teli_utolso_lap_nem_noveli_meg_a_cellat(self):
        """A `contact_sheet`-hez hasonlóan: a részben teli lap cellái nem
        nőnek nagyobbra, csak a térköz nő körülöttük."""
        egy_kepes = grid_pages(_LETTER_PORTRE, *_4X6, count=1)[0].cells[0]
        harom_lap_utolso = grid_pages(_LETTER_PORTRE, *_4X6, count=5)[-1].cells[0]
        assert harom_lap_utolso.width == pytest.approx(egy_kepes.width)
        assert harom_lap_utolso.height == pytest.approx(egy_kepes.height)


class TestChoosePageOrientation:
    def test_4x6_5_pelany_a4n_a_fekvot_valasztja_kevesebb_lapert(self):
        """Élő referencia (Colab „1 of 3”): 4×6, 5 példány A4-en a FEKVŐ
        lapállás 3 lapot ad (2+2+1), a PORTRÉ 5-öt adna — a fekvő nyer."""
        fekvo_e, lapok = choose_page_orientation(
            _A4_PORTRE, _A4_FEKVO, *_4X6, count=5
        )
        assert fekvo_e is True
        assert [lap.count for lap in lapok] == [2, 2, 1]

    def test_tarca_5_pelany_a4n_dontetlennel_a_portre_marad(self):
        """Élő referencia: Tárcaméret, 5 példány A4-en „3 + 2” sorfolytonos
        rács — mindkét lapállás 1 lapot ad (döntetlen), tehát az EREDETI
        (portré) marad, és a 3+2 sortörés jön ki."""
        fekvo_e, lapok = choose_page_orientation(
            _A4_PORTRE, _A4_FEKVO, *_TARCA, count=5
        )
        assert fekvo_e is False
        assert len(lapok) == 1
        elso_sor = lapok[0].cells[:3]
        masodik_sor = lapok[0].cells[3:]
        assert len(elso_sor) == 3
        assert len(masodik_sor) == 2
        # a második sor lejjebb van, mint az első (ugyanaz az y mindkét
        # cellának — sorfolytonos rács, nem szórt elhelyezés)
        assert masodik_sor[0].y > elso_sor[0].y
        assert masodik_sor[0].y == pytest.approx(masodik_sor[1].y)

    def test_egyik_tajolasba_sem_fer_bele_hibat_dob(self):
        with pytest.raises(ValueError):
            choose_page_orientation(_A4_PORTRE, _A4_FEKVO, 50.0, 50.0, count=1)

    def test_csak_az_egyik_tajolasba_fer_bele_azt_valasztja(self):
        # egy 4×20 hüvelykes keskeny lapon a 8×3-as cella PORTRÉBAN nem
        # fér el (a lap 4 hüvelyk széles, a cella 8), FEKVŐBEN viszont
        # igen (a lap ekkor 20 hüvelyk széles) — ez PONTOSAN azt az esetet
        # próbálja, amikor csak az egyik tájolás ad érvényes elrendezést
        keskeny_lap_portre = PageGeometry(width=4.0, height=20.0, margin=0.0)
        keskeny_lap_fekvo = PageGeometry(width=20.0, height=4.0, margin=0.0)
        fekvo_e, lapok = choose_page_orientation(
            keskeny_lap_portre, keskeny_lap_fekvo, 8.0, 3.0, count=1
        )
        assert fekvo_e is True
        assert len(lapok) == 1
