"""A „Rács" (`regulargrid`) sor- és oszlopszáma (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.9.8 — zárt költségképlet,
nem a pakolófa.
"""

from __future__ import annotations

import pytest

from picasapy.collage.regular_grid import regular_grid_rects, regular_grid_shape


def test_hat_fekvo_kep_negy_harmad_lapon_harom_sor_ket_oszlop():
    """Kézzel végigszámolt eset: N=6, lap 1200×900, minden kép 3:2.

    A költségek: 1 sor 11,48 · 2 sor 2,87 · **3 sor 2,27** · 4 sor 5,02 ·
    5 sor 7,78 · 6 sor 9,07 — a 3 sor nyer."""
    assert regular_grid_shape([1.5] * 6, 1200, 900) == (3, 2)


def test_egy_kep_egy_cella():
    assert regular_grid_shape([1.5], 800, 600) == (1, 1)


def test_dontetlennel_a_NAGYOBB_sorszam_nyer():
    """Az eredeti összehasonlítása `<=`, nem `<`. Két négyzetes kép egy
    négyzetes lapon: 1 sor és 2 sor költsége is 3,4 — a 2 sor marad."""
    assert regular_grid_shape([1.0, 1.0], 100, 100) == (2, 1)


def test_az_ures_cellak_szama_is_koltseg():
    """Nyolc kép: a 3×3-as rács egy cellát üresen hagyna, ezért a képlet
    a hézagmentes osztásokat részesíti előnyben."""
    rows, columns = regular_grid_shape([1.5] * 8, 1200, 900)
    assert rows * columns >= 8
    assert rows * columns - 8 <= 1


def test_atlagos_oldalarany_szamit_nem_az_elso_kepe():
    """Álló képeknél más osztás nyer, mint fekvőknél — ugyanazon a lapon."""
    fekvo = regular_grid_shape([1.5] * 6, 1200, 900)
    allo = regular_grid_shape([1 / 1.5] * 6, 1200, 900)
    assert fekvo != allo


def test_rectek_hezagmentesen_lefedik_az_egysegnegyzetet():
    rects = regular_grid_rects(6, rows=3, columns=2)
    assert len(rects) == 6
    assert rects[0].x0 == 0.0 and rects[0].y0 == 0.0
    assert rects[-1].x1 == pytest.approx(1.0)
    assert rects[-1].y1 == pytest.approx(1.0)
    terulet = sum((r.x1 - r.x0) * (r.y1 - r.y0) for r in rects)
    assert terulet == pytest.approx(1.0)


def test_hianyos_utolso_sor_esetén_is_ervenyes_rectek():
    """Öt kép 3×2-es rácsban: az utolsó sorban egy cella marad üresen."""
    rects = regular_grid_rects(5, rows=3, columns=2)
    assert len(rects) == 5
    assert all(r.x1 > r.x0 and r.y1 > r.y0 for r in rects)


def test_ervenytelen_bemenet():
    with pytest.raises(ValueError):
        regular_grid_shape([], 800, 600)
    with pytest.raises(ValueError):
        regular_grid_shape([0.0], 800, 600)
    with pytest.raises(ValueError):
        regular_grid_rects(5, rows=2, columns=2)  # nem fér el
