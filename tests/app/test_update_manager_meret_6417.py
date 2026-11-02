from pathlib import Path


def test_update_manager_800_sor_alatt_marad():
    update_manager = (
        Path(__file__).resolve().parents[2]
        / "src"
        / "picasapy"
        / "app"
        / "update_manager.py"
    )

    line_count = len(update_manager.read_text(encoding="utf-8").splitlines())

    assert line_count < 800, f"update_manager.py: {line_count} sor (plafon: <800)"
