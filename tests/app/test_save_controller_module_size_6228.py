"""A mentési vezérlő részei maradjanak a fájlméret-korlát alatt (#6228)."""

from pathlib import Path

_MENTES_MODULOK = (
    "save_controller.py",
    "save_as_copy.py",
    "save_errors.py",
    "save_feedback.py",
    "save_progress.py",
    "save_render.py",
    "save_restore.py",
    "save_rows.py",
)


def test_minden_mentesmodul_400_sor_alatt_marad() -> None:
    app = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"
    sorok = {
        nev: len((app / nev).read_text(encoding="utf-8").splitlines())
        for nev in _MENTES_MODULOK
    }

    tulhosszuak = {nev: sor for nev, sor in sorok.items() if sor >= 400}
    assert not tulhosszuak, f"a mentési modulok elérték a 400 soros plafont: {tulhosszuak}"
