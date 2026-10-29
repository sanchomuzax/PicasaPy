"""A render-lánc részei maradjanak a fájlméret-korlát alatt (#6185)."""

from pathlib import Path


def test_minden_lancmodul_800_sor_alatt_marad() -> None:
    render = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "render"
    modulok = sorted(render.glob("chain*.py"))
    sorok = {modul.name: len(modul.read_text(encoding="utf-8").splitlines()) for modul in modulok}

    assert modulok, "nem található render-lánc modul"
    tulhosszuak = {nev: sor for nev, sor in sorok.items() if sor >= 800}
    assert not tulhosszuak, f"a render-lánc moduljai elérték a 800 soros plafont: {tulhosszuak}"
