"""A README képernyőképe egyszer, a tetején szerepel (tulajdonosi kérés, 2026-10-13)."""

from pathlib import Path

README = Path(__file__).resolve().parents[1] / "README.md"


def test_a_kepernyokep_egyszer_es_a_nyelvi_reszek_elott_all():
    szoveg = README.read_text(encoding="utf-8")
    kepek = [sor for sor in szoveg.splitlines() if "<img" in sor and "screenshot" in sor]
    assert len(kepek) == 1, f"a képernyőkép {len(kepek)}-szer szerepel"
    assert szoveg.index(kepek[0]) < szoveg.index("# English")
    assert szoveg.index(kepek[0]) < szoveg.index("# Magyar")
