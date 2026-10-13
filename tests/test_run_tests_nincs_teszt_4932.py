"""#4932: a fájlonkénti futásnál az 5-ös kód (nem futott teszt) nem bukás."""
import importlib.util
import sys
from pathlib import Path

_UT = Path(__file__).resolve().parents[1] / "scripts" / "run_tests.py"
_spec = importlib.util.spec_from_file_location("run_tests_4932", _UT)
rt = importlib.util.module_from_spec(_spec)
sys.modules["run_tests_4932"] = rt
_spec.loader.exec_module(rt)


def test_az_otos_kod_nem_bukas():
    assert rt._nincs_teszt_nem_bukas(["tests/x.py"], 5) == 0


def test_a_valodi_bukas_megmarad():
    assert rt._nincs_teszt_nem_bukas(["tests/x.py"], 1) == 1
    assert rt._nincs_teszt_nem_bukas(["tests/x.py"], 124) == 124
