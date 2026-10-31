"""A windowsos darab-futtató a választóval azonos teljes/szűkített döntést kap (#6324)."""
from pathlib import Path

WORKFLOWS = Path(__file__).resolve().parents[1] / ".github" / "workflows"


def _szoveg(nev: str) -> str:
    return (WORKFLOWS / nev).read_text(encoding="utf-8")


def test_a_ci_a_kodvaltozas_jelzot_adja_at_a_windowsos_daraboknak():
    ci = _szoveg("ci.yml")
    blokk = ci[ci.index("\n  darabok-windows:"):ci.index("\n  docs-orok:")]

    assert "teljes: ${{ needs.valtozas.outputs.kod == 'true' && '1' || '' }}" in blokk


def test_a_darab_futtato_a_teljes_bemenet_szerint_valaszt():
    darabok = _szoveg("teszt-darabok.yml")

    assert "github.event_name != 'pull_request' && '1' || ''" not in darabok
    assert darabok.count("inputs.teljes == '1' && '1' || ''") == 2
    assert "(github.event_name == 'pull_request' || inputs.teljes != '1') && '--windows'" in darabok


def test_a_teljes_bemenet_alapertelmezese_a_regi_viselkedes():
    darabok = _szoveg("teszt-darabok.yml")
    blokk = darabok[darabok.index("      teljes:"):darabok.index("      cov:")]

    assert 'default: "1"' in blokk
