"""A szálközi futás-kapu próbái (picasapy-agent#308).

2026-11-08-án egy helyi teljes tesztfutás (`run_tests.py --nightly-random-seed`)
három Codex-szál, egy Claude-munkás és egy ütemezett kör mellett 15 fölé vitte
a négymagos gép terhelését. A kapu ezt az alakot állítja meg.
"""
from __future__ import annotations

import importlib.util
import io
import json
import sys
from pathlib import Path

import pytest

_UT = Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "szalkozi_futas_kapu.py"
_SPEC = importlib.util.spec_from_file_location("szalkozi_futas_kapu", _UT)
kapu = importlib.util.module_from_spec(_SPEC)
sys.modules["szalkozi_futas_kapu"] = kapu
_SPEC.loader.exec_module(kapu)

CODEX_PS = "120 codex exec --json -C /home/x/PicasaPy-wt-6690-codex brief\n"
CLAUDE_PS = "300 claude -p --model claude-sonnet-5-5 --permission-mode acceptEdits\n"
GEMINI_PS = "40 /usr/local/bin/agy -p --model gemini-3.8-flash-high\n"
CSENDES_PS = "10 bash\n20 python3 valami.py\n"


@pytest.mark.parametrize("cmd", [
    "python scripts/run_tests.py",
    "python3 scripts/run_tests.py --nightly-random-seed 1410318787",
    "cd ~/Documents/PicasaPy && timeout 3600 python3 scripts/run_tests.py --cov",
    "nice -n 10 python3 /home/x/PicasaPy/scripts/run_tests.py --shard 1/4",
    "systemd-run --user --scope -q -- python3 scripts/run_tests.py",
    "PICASAPY_TESZT_EGYIDEJU=1 python3 scripts/run_tests.py --mutmut",
])
def test_teljes_futas_felismerve(cmd):
    assert kapu.teljes_futas(cmd)


@pytest.mark.parametrize("cmd", [
    "python3 scripts/run_tests.py --fajllista lista.txt",
    "python3 scripts/run_tests.py --fajllista=lista.txt",
    "python3 scripts/run_tests.py --darabszam",
    "python3 scripts/run_tests.py --csak-takaritas",
    "python3 scripts/run_tests.py --help",
    "grep -n nightly scripts/run_tests.py",
    "sed -n 1,20p scripts/run_tests.py",
    "echo 'python3 scripts/run_tests.py' > jegyzet.txt",
    "python3 -m pytest tests/scripts/test_x.py -q --basetemp=$BT",
    "git log -- scripts/run_tests.py",
])
def test_nem_teljes_futas_atmegy(cmd):
    assert not kapu.teljes_futas(cmd)


@pytest.mark.parametrize("ps, varhato", [
    (CODEX_PS, {"codex": 1}),
    (CLAUDE_PS, {"claude": 1}),
    (GEMINI_PS, {"gemini": 1}),
    (CODEX_PS + CODEX_PS.replace("6690", "6713") + CLAUDE_PS, {"codex": 2, "claude": 1}),
    (CSENDES_PS, {}),
])
def test_futo_szalak(ps, varhato):
    assert kapu.futo_szalak(ps) == varhato


def test_futo_szalnal_blokkol():
    indok = kapu.blokkolando("python3 scripts/run_tests.py", ps=CODEX_PS, terheles=1.0, magok=4)
    assert indok is not None
    assert "codex" in indok


def test_magas_terhelesnel_blokkol_szal_nelkul_is():
    indok = kapu.blokkolando("python3 scripts/run_tests.py", ps=CSENDES_PS, terheles=6.5, magok=4)
    assert indok is not None
    assert "6.5" in indok


def test_csendes_gepen_atmegy():
    assert kapu.blokkolando("python3 scripts/run_tests.py", ps=CSENDES_PS, terheles=1.0, magok=4) is None


def test_fajlonkenti_futas_szal_mellett_is_atmegy():
    cmd = "python3 scripts/run_tests.py --fajllista lista.txt"
    assert kapu.blokkolando(cmd, ps=CODEX_PS, terheles=9.0, magok=4) is None


def test_main_blokkol_es_2_a_kilepokod(monkeypatch, capsys):
    monkeypatch.setattr(kapu, "_ps", lambda: CLAUDE_PS)
    monkeypatch.setattr(kapu, "_terheles", lambda: (0.5, 4))
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"tool_input": {"command": "python3 scripts/run_tests.py"}})))
    assert kapu.main() == 2
    assert "BLOKKOLVA" in capsys.readouterr().err


def test_main_rossz_bemenetnel_nem_blokkol(monkeypatch):
    monkeypatch.setattr(sys, "stdin", io.StringIO("nem json"))
    assert kapu.main() == 0


def test_main_elromlott_meresnel_nem_blokkol(monkeypatch):
    def hiba():
        raise OSError("nincs ps")
    monkeypatch.setattr(kapu, "_ps", hiba)
    monkeypatch.setattr(sys, "stdin", io.StringIO(json.dumps(
        {"tool_input": {"command": "python3 scripts/run_tests.py"}})))
    assert kapu.main() == 0


def test_be_van_kotve_a_projekt_horgai_koze():
    beallitas = json.loads((_UT.parents[2] / ".claude" / "settings.json").read_text(encoding="utf-8"))
    parancsok = [h.get("command", "")
                 for blokk in beallitas["hooks"]["PreToolUse"] if blokk.get("matcher") == "Bash"
                 for h in blokk.get("hooks", [])]
    assert any("szalkozi_futas_kapu.py" in p for p in parancsok)
