"""A Windows tesztlábat PR-on a kiválasztott fájlokra is futtatjuk (#4922)."""
from pathlib import Path

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _blokk(nev: str) -> str:
    szoveg = CI.read_text(encoding="utf-8")
    eleje = szoveg.index(f"\n  {nev}:")
    vege = szoveg.find("\n  ", eleje + 1)
    while vege != -1 and szoveg[vege + 3] == " ":
        vege = szoveg.find("\n  ", vege + 1)
    return szoveg[eleje: vege if vege != -1 else None]


def test_a_windowsos_darabok_pr_on_a_kivalasztott_fajllistat_futtatjak():
    blokk = _blokk("darabok-windows")

    assert (
        "github.event_name != 'pull_request' || "
        "needs.valtozas.outputs.windows_darabszam != '0'"
    ) in blokk
    assert "needs.valtozas.outputs.windows_darabok" in blokk
    assert "needs.valtozas.outputs.windows_darabszam" in blokk


def test_a_windows_osszesito_pr_on_is_jelzi_a_darabok_bukasat():
    blokk = _blokk("test-windows")

    assert "github.event_name != 'pull_request'" not in blokk
    assert "needs.darabok-windows.result" in blokk


def test_a_windowsos_darabok_a_main_pushon_futnak():
    """Az ütemezett futást a GitHub nem indította el (2026-10-10), így a
    futásidő-tábla windowsos mérés nélkül maradt — a main-pushon futnia kell."""
    blokk = _blokk("darabok-windows")
    assert "github.event_name != 'push'" not in blokk


def test_a_windows_pr_laba_a_windows_erzekeny_szurot_hivja():
    workflow = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "teszt-darabok.yml"
    szoveg = workflow.read_text(encoding="utf-8")

    assert "--windows" in szoveg
    assert "inputs.os == 'windows-latest'" in szoveg
