"""Az exportálás belső moduljai maradjanak 400 sor alatt (#6193)."""

from pathlib import Path


def test_minden_exportmodul_400_sor_alatt_marad() -> None:
    export = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "export"
    modulok = sorted(export.glob("*.py"))
    sorok = {
        modul.name: len(modul.read_text(encoding="utf-8").splitlines())
        for modul in modulok
    }

    assert modulok, "nem található exportmodul"
    tulhosszuak = {nev: sor for nev, sor in sorok.items() if sor >= 400}
    assert not tulhosszuak, f"a 400 soros plafont elérő exportmodulok: {tulhosszuak}"
