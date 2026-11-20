"""#7116/#7244: a paritásspecifikáció fő lapja és archívumai méretkorlátosak."""

from __future__ import annotations

from pathlib import Path

from scripts import nagy_fajl_or

GYOKER = Path(__file__).resolve().parents[2]
FO = GYOKER / "docs/specs/paritas-ellenorzes.md"
ARCHIV = GYOKER / "docs/specs/paritas-ellenorzes-archiv-1.md"
ARCHIV_2 = GYOKER / "docs/specs/paritas-ellenorzes-archiv-2.md"


def test_minden_lap_a_nagyfajl_kuszob_alatt_marad():
    assert FO.stat().st_size < nagy_fajl_or.KUSZOB
    assert ARCHIV.stat().st_size < nagy_fajl_or.KUSZOB
    assert ARCHIV_2.stat().st_size < nagy_fajl_or.KUSZOB


def test_a_fo_lap_crlf_merete_is_boven_a_kuszob_alatt_marad():
    fo_crlf = FO.read_text(encoding="utf-8").replace("\n", "\r\n").encode("utf-8")
    assert len(fo_crlf) < 800_000


def test_a_paritas_lap_nem_kivetel():
    assert not nagy_fajl_or.kivetel("docs/specs/paritas-ellenorzes.md")


def test_a_lezart_szakaszok_az_archivban_a_nyitottak_a_fo_lapon():
    fo = FO.read_text(encoding="utf-8")
    archiv = ARCHIV.read_text(encoding="utf-8")
    archiv_2 = ARCHIV_2.read_text(encoding="utf-8")
    assert "\n## #6984:" in archiv and "\n## #6984:" not in fo
    assert "\n## #7012:" in fo and "\n## #7012:" not in archiv
    assert "\n## #7028:" in fo
    for jegy in ("#7031:", "#7032:", "#7059:", "#7069:", "#7083:", "#7084:"):
        assert f"\n## {jegy}" in archiv_2
        assert f"\n## {jegy}" not in fo
    assert "\n## #7033:" in fo and "\n## #7033:" not in archiv_2
    assert "paritas-ellenorzes-archiv-1.md" in fo
    assert "paritas-ellenorzes-archiv-2.md" in fo


def test_az_index_mindket_lapra_hivatkozik():
    index = (GYOKER / "docs/specs/00-index.md").read_text(encoding="utf-8")
    assert "(paritas-ellenorzes.md)" in index
    assert "(paritas-ellenorzes-archiv-1.md)" in index
    assert "(paritas-ellenorzes-archiv-2.md)" in index
