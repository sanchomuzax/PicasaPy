"""A #6340 frissítési súgója mindkét felhasználói nyelven elérhető."""

from pathlib import Path


ROOT = Path(__file__).resolve().parents[1] / "src" / "picasapy" / "help"


def test_frissitesi_sugo_leirja_az_ellenorzest_a_jelzest_es_a_platformokat():
    magyar = (ROOT / "features" / "beallitasok.md").read_text(encoding="utf-8")
    angol = (ROOT / "en" / "features" / "beallitasok.md").read_text(encoding="utf-8")

    assert "30 másodperccel" in magyar
    assert "GitHub" in magyar
    assert "SHA256SUMS" in magyar
    assert ".deb" in magyar and "pip" in magyar
    assert "30 seconds" in angol
    assert "GitHub" in angol
    assert "SHA256SUMS" in angol
    assert ".deb" in angol and "pip" in angol
