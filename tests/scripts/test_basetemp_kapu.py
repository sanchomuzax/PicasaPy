"""A basetemp-kapu hook próbasora — #1649.

A kapu azt a hibaosztályt fogja meg, ami 2026-08-15-én **5,8 GB**-ot hagyott a
tmpfs-en: csupasz `pytest` közös `--basetemp` nélkül, öt párhuzamos körben.
A kár nem a vétkes körnél jelentkezik, hanem a párhuzamos munkameneteknél.

A vaklárma-osztályokat a `test_release_kapu.py` tanulságai alapján előre
őrizzük: a parancs SZÖVEGÉBEN előforduló említés (grep, fájlírás) nem
blokkolhat, és a projekt saját futtatója sem.
"""

import importlib.util
import io
import json
import pathlib

import pytest

_UT = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "hooks" / "basetemp_kapu.py"
_spec = importlib.util.spec_from_file_location("basetemp_kapu", _UT)
kapu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapu)


BLOKKOLANDO = [
    "pytest tests/app",
    "python -m pytest tests/ini",
    "python3 -m pytest tests/app/test_x.py -q",
    "cd /x && python3 -m pytest tests -q",
    "timeout 60 python3 -m pytest tests/app/test_y.py",
    "python3 -m pytest -q tests/app && echo kesz",
]

ATENGEDENDO = [
    # a projekt saját futtatója — maga adja a futásonként egyedi basetempet
    "python scripts/run_tests.py",
    "python3 scripts/run_tests.py --gyors",
    # explicit közös basetemp
    "python3 -m pytest tests/app --basetemp=/tmp/bt",
    "python3 -m pytest tests --basetemp /tmp/bt -q",
    "pytest tests/ini --basetemp=$SCRATCH/bt",
    # tmpdir-t nem hozó alakok
    "python3 -m pytest --help",
    "pytest -h",
    "pytest --version",
    "python3 -m pytest tests --collect-only",
    # puszta említés a parancs SZÖVEGÉBEN — a release_kapu élesben tanult osztálya
    "grep -rn 'python3 -m pytest' docs/",
    "echo 'ne hasznalj csupasz pytest-et' >> jegyzet.txt",
    "rg --files-with-matches 'pytest tests' .",
    # nem is pytest
    "git status",
    "python3 scripts/allapotlap.py",
]


@pytest.mark.parametrize("cmd", BLOKKOLANDO)
def test_csupasz_pytest_blokkolodik(cmd):
    assert kapu.blokkolando(cmd) is not None, cmd


@pytest.mark.parametrize("cmd", ATENGEDENDO)
def test_szabalyos_parancs_atmegy(cmd):
    assert kapu.blokkolando(cmd) is None, cmd


@pytest.mark.parametrize("bemenet", ["", "{", '{"tool_input": null}', "[]"])
def test_fail_open_rossz_bemenetre(bemenet, monkeypatch):
    monkeypatch.setattr("sys.stdin", io.StringIO(bemenet))
    assert kapu.main() == 0


def test_blokkolaskor_2_es_kilepokod_es_uzenet(monkeypatch, capsys):
    monkeypatch.setattr(
        "sys.stdin", io.StringIO(json.dumps({"tool_input": {"command": "pytest tests"}}))
    )
    assert kapu.main() == 2
    hiba = capsys.readouterr().err
    assert "basetemp" in hiba.lower()
    assert "run_tests.py" in hiba          # mondja meg, mit tegyen helyette


def test_szabalyos_parancsra_0(monkeypatch):
    monkeypatch.setattr(
        "sys.stdin",
        io.StringIO(json.dumps({"tool_input": {"command": "python scripts/run_tests.py"}})),
    )
    assert kapu.main() == 0
