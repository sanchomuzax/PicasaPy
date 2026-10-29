"""#6211: az arcfelismerés specifikációja külön, jóval 1 MB alatti lapokon él."""

from __future__ import annotations

from pathlib import Path

from scripts import nagy_fajl_or

GYOKER = Path(__file__).resolve().parents[2]
FODOKUMENTUM = GYOKER / "docs/specs/picasa-arcfelismeres.md"
NAPLO = GYOKER / "docs/specs/picasa-arcfelismeres-kutatasi-naplo.md"
NAPLO_2026_10 = GYOKER / "docs/specs/picasa-arcfelismeres-kutatasi-naplo-2026-10.md"
MAX_DARAB_MERET = 800_000


def test_a_mukodes_es_a_kutatasi_korok_kulon_lapokon_vannak():
    fo = FODOKUMENTUM.read_text(encoding="utf-8")
    naplo = NAPLO.read_text(encoding="utf-8")
    naplo_2026_10 = NAPLO_2026_10.read_text(encoding="utf-8")

    assert "## 18." in fo
    assert "## 19." not in fo
    assert "## 19." in naplo and "## 53." in naplo
    assert "## 54." not in naplo
    assert "## 54." in naplo_2026_10 and "## 60." in naplo_2026_10
    assert "## 53." not in naplo_2026_10


def test_minden_lap_joval_a_nagyfajl_kuszob_alatt_marad():
    lapok = (FODOKUMENTUM, NAPLO, NAPLO_2026_10)

    assert all(lap.stat().st_size < MAX_DARAB_MERET for lap in lapok)


def test_az_arcfelismeresi_spec_mar_nem_kivetel():
    assert "docs/specs/picasa-arcfelismeres.md" not in nagy_fajl_or.KIVETELEK


def test_az_index_hivatkozik_mindharom_lapra():
    index = (GYOKER / "docs/specs/00-index.md").read_text(encoding="utf-8")

    for nev in (
        "picasa-arcfelismeres.md",
        "picasa-arcfelismeres-kutatasi-naplo.md",
        "picasa-arcfelismeres-kutatasi-naplo-2026-10.md",
    ):
        assert f"[{nev}]({nev})" in index
    assert (
        "[kutatási napló 35.7–35.11 szakaszát]"
        "(picasa-arcfelismeres-kutatasi-naplo.md)"
    ) in index


def test_a_19_szakasz_kulso_hivatkozasa_a_kutatasi_naplot_nevezi_meg():
    hivatkozo = (GYOKER / "docs/specs/paritas-ellenorzes.md").read_text(
        encoding="utf-8"
    )

    assert "picasa-arcfelismeres-kutatasi-naplo.md" in hivatkozo
    assert "picasa-arcfelismeres.md:2346" not in hivatkozo
