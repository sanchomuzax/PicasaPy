"""#4285: a windowsos tesztkészlet PR-on nem fut; 2026-10-09 óta main-pushon sem,
csak ütemezve (éjszaka) és kézi indításra."""
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
    assert "github.event_name != 'pull_request'" in _blokk("darabok-windows")


def test_a_windowsos_osszesito_pr_on_nem_buktat():
    assert "github.event_name != 'pull_request'" in _blokk("test-windows")


def test_a_windowsos_darabok_main_pushon_sem_futnak_csak_utemezve():
    blokk = _blokk("darabok-windows")
    assert "github.event_name != 'push'" in blokk
    assert "cron:" in CI.read_text(encoding="utf-8")
