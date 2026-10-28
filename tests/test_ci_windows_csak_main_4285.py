"""A Windows tesztlábat PR-on kihagyjuk, mainen és éjjel megtartjuk (#6122)."""
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _blokk(nev: str) -> str:
    szoveg = CI.read_text(encoding="utf-8")
    eleje = szoveg.index(f"\n  {nev}:")
    vege = szoveg.find("\n  ", eleje + 1)
    while vege != -1 and szoveg[vege + 3] == " ":
        vege = szoveg.find("\n  ", vege + 1)
    return szoveg[eleje: vege if vege != -1 else None]


def test_a_windowsos_darabok_pr_on_kimaradnak():
    blokk = _blokk("darabok-windows")

    assert "if: ${{ github.event_name != 'pull_request' &&" in blokk
    assert "github.event_name != 'push'" not in blokk
    assert "github.event_name != 'schedule'" not in blokk


def test_a_windows_osszesito_pr_on_is_jelzi_a_darabok_bukasat():
    blokk = _blokk("test-windows")

    assert "github.event_name != 'pull_request'" not in blokk
    assert "needs.darabok-windows.result" in blokk


def test_a_windowsos_darabok_a_main_pushon_es_ejjel_futnak():
    """A main push és az ütemezett esemény továbbra is elindítja a Windows-lábat."""
    blokk = _blokk("darabok-windows")
    workflow = CI.read_text(encoding="utf-8")

    assert "github.event_name != 'push'" not in blokk
    assert "github.event_name != 'schedule'" not in blokk
    assert "\n  push:\n    branches: [main]\n" in workflow
    assert "\n  schedule:\n    - cron:" in workflow


def test_a_windows_pr_laba_a_windows_erzekeny_szurot_hivja():
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "teszt-darabok.yml"
    szoveg = workflow.read_text(encoding="utf-8")

    assert "--windows" in szoveg
    assert "inputs.os == 'windows-latest'" in szoveg
