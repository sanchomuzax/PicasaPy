"""A TIFF-blokk-szerkesztő részei maradjanak a fájlméret-korlát alatt (#6232)."""

from pathlib import Path


def test_minden_tiff_modul_400_sor_alatt_marad() -> None:
    metadata = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "metadata"
    modulok = sorted(metadata.glob("tiff_*.py"))
    sorok = {modul.name: len(modul.read_text(encoding="utf-8").splitlines()) for modul in modulok}

    assert "tiff_helyben.py" in sorok, "nem található a TIFF-blokk belépési modulja"
    tulhosszuak = {nev: sor for nev, sor in sorok.items() if sor >= 400}
    assert not tulhosszuak, f"a TIFF-modulok elérték a 400 soros plafont: {tulhosszuak}"
