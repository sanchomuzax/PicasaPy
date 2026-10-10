"""A mérés nélküli tesztfájl konzervatív becslést kap, nem blokkol (#4825)."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

import run_tests  # noqa: E402

_TABLA = {f"tests/app/test_m{i}.py": float(i) for i in range(1, 11)}  # 1..10 mp


def test_az_uj_fajl_a_90_percentilist_kapja(monkeypatch):
    monkeypatch.setattr(run_tests, "_mert_idok", lambda: dict(_TABLA))
    egysegek = [*_TABLA, "tests/app/test_uj_4825.py"]

    idok = run_tests.becsult_idok(egysegek)

    assert idok["tests/app/test_uj_4825.py"] == 10.0, "a becslés nem konzervatív"
    assert idok["tests/app/test_m3.py"] == 3.0, "a mért időt nem szabad felülírni"


def test_a_becsult_egysegek_listaja_a_potlas_listaja(monkeypatch):
    monkeypatch.setattr(run_tests, "_mert_idok", lambda: dict(_TABLA))
    egysegek = [*_TABLA, "tests/app/test_uj_b.py", "tests/app/test_uj_a.py"]

    assert run_tests.becsult_egysegek(egysegek) == [
        "tests/app/test_uj_a.py",
        "tests/app/test_uj_b.py",
    ]


def test_az_uj_fajl_bekerul_egy_darabba(monkeypatch):
    monkeypatch.setattr(run_tests, "_mert_idok", lambda: dict(_TABLA))
    egysegek = [*_TABLA, "tests/app/test_uj_4825.py"]

    darabok = [run_tests._kiegyensulyozott_darab(egysegek, i, 4) for i in range(1, 5)]

    assert sum("tests/app/test_uj_4825.py" in d for d in darabok) == 1
    assert set().union(*darabok) == set(egysegek)


def test_ures_tablaval_is_mukodik(monkeypatch):
    monkeypatch.setattr(run_tests, "_mert_idok", dict)
    assert run_tests.becsult_idok(["tests/app/test_x.py"]) == {"tests/app/test_x.py": 1.0}
