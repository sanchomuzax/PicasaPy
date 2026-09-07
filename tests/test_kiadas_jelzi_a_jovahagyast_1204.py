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


def test_a_futas_osszefoglaloja_megkapja_a_PR_szamat(bump_lepes):
    assert "GITHUB_STEP_SUMMARY" in bump_lepes, (
        "a futás összefoglalójába nem kerül bele a PR"
    )

# ────────────────────────────────────────────────────────────────────────
# VISSZAVONT ŐRÖK — #58 (2026-09-07)
#
# Az alábbi állítások a `chore/auto-bump-*` PR-útról szóltak, amit ezzel a
# változtatással ELHAGYTUNK. Nem „elrontottuk" őket, hanem a mechanizmus
# szűnt meg, amit mértek — ezért a helyes lépés a visszavonás, nem az
# átírás valami másra.
#
# Miért szűnt meg: a `main` védett, ezért a verzióemelés ágra + PR-re ment;
# a `GITHUB_TOKEN`-nel nyitott PR-en viszont a GitHub SZÁNDÉKOSAN nem indít
# ellenőrzést (#1190), és ez nem kapcsolható ki — az élesített auto-merge
# tehát sosem lefutó kötelező ellenőrzésre várt. Mérve: `chore/auto-bump-*`
# előtaggal HÁROM PR született (#2616, #2621, #2657), MIND A HÁRMAT a
# kiadási őr zárta le, egy sem olvadt be soha.
#
# Amit a visszavont őrök védtek, azt most a manager-kör
# `kiadas_lemaradas()` mérője adja (privát #59): 6 óra után figyelmeztet,
# 24 óra után P0. Előbb lett meg a mérő, és csak utána hagytuk el a
# tartalékot.
#
# VISSZAVONVA EBBŐL A FÁJLBÓL: `test_a_PR_nyitasa_utan_auto_merge_elesedik`, `test_a_jovahagyas_igenye_WARNINGKENT_is_megjelenik`, `test_a_nema_echo_helyett_HIBA_all_a_bukasi_agakon`
# ────────────────────────────────────────────────────────────────────────
