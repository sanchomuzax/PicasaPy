"""A fő vezérlő maradjon tematikus mixinekre bontva (#6022)."""

from pathlib import Path


_REPO = Path(__file__).resolve().parents[2]


def test_app_controller_modul_800_sor_alatt_marad() -> None:
    controller = _REPO / "src/picasapy/app/controller.py"
    sorok = len(controller.read_text(encoding="utf-8").splitlines())

    assert sorok < 800, f"a controller.py {sorok} soros (a plafon 800)"
