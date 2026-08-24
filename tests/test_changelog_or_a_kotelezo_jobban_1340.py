"""A CHANGELOG-őrnek a KÖTELEZŐ ellenőrzésben a helye (#1340).

Az első változat a `lint` jobba került — csakhogy a repó egyetlen kötelező
ellenőrzése a „Test (ubuntu-latest)". Egy piros `lint` az auto-merge-öt nem
állítja meg, tehát az őrnek ott nem lett volna foga: pontosan az a fajta
látszat-garancia, amiből a projektben már több is visszaütött.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

CI = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"

#: A `main` ág védelmében beállított kötelező státusz neve.
KOTELEZO_JOB_NEV = "Test (ubuntu-latest)"


@pytest.fixture(scope="module")
def ci() -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


def _job_neve_szerint(ci: dict, nev: str) -> dict:
    for job in ci["jobs"].values():
        if job.get("name") == nev:
            return job
    raise AssertionError(f"nincs `{nev}` nevű job")


def test_az_or_a_kotelezo_jobban_fut(ci: dict) -> None:
    job = _job_neve_szerint(ci, KOTELEZO_JOB_NEV)
    futasok = " ".join(str(lepes.get("run", "")) for lepes in job["steps"])
    assert "changelog_or.py" in futasok, (
        "a CHANGELOG-őr nem a kötelező ellenőrzésben van — nem tud blokkolni"
    )


def test_az_or_teljes_elozmenyt_kap(ci: dict) -> None:
    job = _job_neve_szerint(ci, KOTELEZO_JOB_NEV)
    checkout = next(
        lepes for lepes in job["steps"]
        if str(lepes.get("uses", "")).startswith("actions/checkout")
    )
    assert checkout.get("with", {}).get("fetch-depth") == 0


def test_az_or_csak_PR_en_fut(ci: dict) -> None:
    """Pusholt commitnak nincs „alapja", amihez a diffet mérni lehetne."""
    job = _job_neve_szerint(ci, KOTELEZO_JOB_NEV)
    lepes = next(
        lepes for lepes in job["steps"] if "changelog_or.py" in str(lepes.get("run", ""))
    )
    assert "pull_request" in str(lepes.get("if", ""))
