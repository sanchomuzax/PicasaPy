"""A verzióemelő PR nem maradhat NÉMÁN jóváhagyásra várva (#1204).

## A lelet

A GitHub a `GITHUB_TOKEN`-nel nyitott PR-en **szándékosan nem indít
workflow-t** (#1190) — ez nem kapcsolható ki. A gond nem a jóváhagyás,
hanem hogy néma volt: a PR csendben ott ült ellenőrzés nélkül, és
2026-08-21-én a **tulajdonos** vette észre:

> „Kérlek, ezt ne hagyd parlagon, valaki elhagyta"

## Amit a workflow-nak tennie kell

1. **auto-merge élesítése** a nyitáskor — így a jóváhagyás után magától
   beolvad, nem kell rá visszatérni;
2. **`::warning::`** — ez a futáslistában is látszik, nem csak a naplóban;
3. **futás-összefoglaló** (`$GITHUB_STEP_SUMMARY`) a PR számával.

Ez a fájl a workflow SZÖVEGÉRE néz, mert a hatást csak egy valódi
GitHub-futásban lehetne előidézni; a szabály viszont statikusan
kimondható. Ugyanaz az elv, mint a `test_ci_kor_ideje_1127.py`-nál.
"""

from __future__ import annotations

import pathlib

import pytest

yaml = pytest.importorskip("yaml")

RELEASE = (
    pathlib.Path(__file__).resolve().parents[1]
    / ".github"
    / "workflows"
    / "release.yml"
)


@pytest.fixture(scope="module")
def bump_lepes() -> str:
    adat = yaml.safe_load(RELEASE.read_text(encoding="utf-8"))
    for lepes in adat["jobs"]["release"]["steps"]:
        if lepes.get("id") == "bump":
            return lepes["run"]
    raise AssertionError("nincs `bump` azonosítójú lépés a release.yml-ben")


def test_a_PR_nyitasa_utan_auto_merge_elesedik(bump_lepes):
    """Enélkül a jóváhagyás után is kézzel kellene beolvasztani."""
    assert "pr merge" in bump_lepes and "--auto" in bump_lepes, (
        "a verzióemelő PR-en nem élesedik auto-merge"
    )


def test_a_jovahagyas_igenye_WARNINGKENT_is_megjelenik(bump_lepes):
    """A napló mélyén elrejtett sor nem jelzés — a warning a futáslistában
    is látszik."""
    assert "::warning" in bump_lepes, "nincs figyelmeztetés a jóváhagyás igényéről"
    assert "jóváhagyásra vár" in bump_lepes


def test_a_futas_osszefoglaloja_megkapja_a_PR_szamat(bump_lepes):
    assert "GITHUB_STEP_SUMMARY" in bump_lepes, (
        "a futás összefoglalójába nem kerül bele a PR"
    )


def test_a_nema_echo_helyett_warning_all_a_bukasi_agakon(bump_lepes):
    """A korábbi ágak sima `echo`-val jeleztek — az elveszik a naplóban."""
    for reszlet in ("A verzióemelő PR nyitása nem sikerült", "Az ág feltolása nem sikerült"):
        sor = next(s for s in bump_lepes.splitlines() if reszlet in s)
        assert "::warning" in sor, f"néma marad: {reszlet}"
