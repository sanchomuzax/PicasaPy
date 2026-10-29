"""Az alkalmazásindító részei maradjanak a Python-modulplafon alatt (#6155)."""

from pathlib import Path


_APP = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"


def test_application_modules_stay_under_the_size_limit():
    modules = sorted(_APP.glob("application*.py"))
    assert modules, "nem található application modul"

    oversized = {
        module.name: len(module.read_text(encoding="utf-8").splitlines())
        for module in modules
        if len(module.read_text(encoding="utf-8").splitlines()) > 700
    }
    assert not oversized, f"az application modulok túllépik a 700 soros plafont: {oversized}"
