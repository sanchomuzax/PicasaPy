"""A CI-kör ne pörögjön feleslegesen (#1127).

## Miért van erre őr

Egy jegy végigvitele ~1 óra CI-időt vitt, és a tulajdonos ezt közvetlenül
érzi: *„Az 1-2 órája futó szarjaid miatt miért nekem kell szólni?"* és
*„Tilos 2-3 órás teszt köröket futni!"*

Két beállítás ebből sokat levesz, és mindkettő NÉMÁN tűnhet el egy későbbi
szerkesztésnél — a workflow-fájlt nem futtatja teszt, tehát csak ez az őr
szól, ha kikerül.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

CI = pathlib.Path(__file__).resolve().parents[1] / ".github" / "workflows" / "ci.yml"


@pytest.fixture(scope="module")
def ci() -> dict:
    return yaml.safe_load(CI.read_text(encoding="utf-8"))


def test_a_PR_uj_commitja_leallitja_az_elozo_futast(ci):
    """Új commit → a régi futás elhal. Enélkül a sor torlódik.

    ⚠️ A `main`-en ez NEM lehet bekapcsolva: ott minden commit
    CI-bizonyítéka kell, és a kiadási automatika is erre épül. Ezért a
    feltétel a `pull_request` eseményre szűkít, és a csoportkulcs a refet is
    tartalmazza."""
    egyidejuseg = ci.get("concurrency")
    assert egyidejuseg, "nincs `concurrency` — minden push külön futást pörget"

    csoport = str(egyidejuseg.get("group", ""))
    assert "github.ref" in csoport, (
        "a csoportkulcsban nincs benne a ref — két KÜLÖNBÖZŐ ág futása "
        "oltaná ki egymást"
    )

    megszakit = str(egyidejuseg.get("cancel-in-progress", ""))
    assert "pull_request" in megszakit, (
        "a megszakítás nincs `pull_request`-re szűkítve — a main futásai is "
        "elhalnának, és a kiadási automatika bizonyíték nélkül maradna"
    )


def test_minden_python_lepes_gyorsitotarazza_a_pipet(ci):
    """A pip-letöltés jobonként 1–2 perc; a gyorsítótár ezt levágja."""
    hianyzo = []
    for nev, job in (ci.get("jobs") or {}).items():
        for lepes in job.get("steps") or []:
            if not str(lepes.get("uses", "")).startswith("actions/setup-python"):
                continue
            with_ = lepes.get("with") or {}
            if with_.get("cache") != "pip":
                hianyzo.append(nev)
    assert not hianyzo, f"gyorsítótár nélküli Python-lépés ezekben: {hianyzo}"
