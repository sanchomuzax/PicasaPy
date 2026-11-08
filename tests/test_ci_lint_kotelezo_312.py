"""A lint bukása a kötelező „Test (ubuntu-latest)" ellenőrzést is pirosra viszi (picasapy-agent#312).

2026-11-08-án a #6718 piros `Lint (ruff)` mellett beolvadt auto-merge-dzsel, mert a repó
kötelező ellenőrzése egyedül a `test-ubuntu` job, a `lint` nem.
"""
from __future__ import annotations

from pathlib import Path

import yaml

CI = Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


def _job(nev: str) -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))["jobs"][nev]


def test_a_kotelezo_job_megvarja_a_lintet():
    job = _job("test-ubuntu")
    assert "lint" in job["needs"]
    assert job["if"] == "always()"


def test_a_kotelezo_job_elbukik_ha_a_lint_nem_zold():
    lepesek = [s for s in _job("test-ubuntu")["steps"] if "needs.lint.result" in s.get("run", "")]
    assert len(lepesek) == 1
    lepes = lepesek[0]
    assert "needs.valtozas.outputs.kod == 'true'" in lepes["if"]
    assert '!= "success"' in lepes["run"] and "exit 1" in lepes["run"]


def test_a_lint_job_feltetele_egyezik_a_lepesevel():
    # ha a lint csak kódváltozásnál fut, a kötelező lépés is csak akkor nézze
    assert "needs.valtozas.outputs.kod == 'true'" in _job("lint")["if"]
