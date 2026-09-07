"""#58 — az automatikus verzióemelő PR-út ELHAGYVA; ne másszon vissza.

## Miért hagytuk el

A `main` védett, ezért a verzióemelés ágra + PR-re ment. A `GITHUB_TOKEN`-nel
nyitott PR-en viszont a GitHub **szándékosan nem indít ellenőrzést** (#1190),
és **ez nem kapcsolható ki** — az élesített auto-merge tehát olyan kötelező
ellenőrzésre várt, ami soha nem futott le. A PR elavult, és a kiadási őr
lezárta.

Mérve: `chore/auto-bump-*` előtaggal **három** PR született (#2616, #2621,
#2657), és **mind a hármat a kiadási őr zárta le** azzal, hogy „a kiadás már
megvan". Egy sem olvadt be soha. A kézi út — a fejlesztői kör a saját
PR-jében emel verziót — mindháromszor megelőzte.

## Miért nem hagy ez lyukat

A tartalék-út egyetlen valódi haszna az lett volna, hogy elkapja, ha
beolvadt munka kiadatlanul marad. Ezt 2026-09-07 óta **mérjük**: a
manager-kör `kiadas_lemaradas()` mérője 6 óra után figyelmeztet, 24 óra után
`P0`-t ad (privát #59). Előbb lett meg a mérő, és csak utána hagytuk el a
nem működő tartalékot.

## Amit ez a fájl őriz

Hogy a visszavonás **ne csússzon vissza** egy későbbi körben, és hogy a
kiadatlan állapot **hangos** maradjon (a #2487 néma-meghibásodás tilalma).
"""

from __future__ import annotations

from pathlib import Path

import pytest

yaml = pytest.importorskip("yaml")

GYOKER = Path(__file__).resolve().parents[2]
RELEASE = GYOKER / ".github" / "workflows" / "release.yml"


@pytest.fixture(scope="module")
def bump_lepes() -> str:
    adat = yaml.safe_load(RELEASE.read_text(encoding="utf-8"))
    for lepes in adat["jobs"]["release"]["steps"]:
        if lepes.get("id") == "bump":
            return str(lepes.get("run", ""))
    raise AssertionError("nincs `bump` azonosítójú lépés a release.yml-ben")


def test_a_kiado_NEM_nyit_verzioemelo_PR_t(bump_lepes: str) -> None:
    """A FOG: háromból három ilyen PR elavulva zárult le."""
    assert "gh pr create" not in bump_lepes, (
        "visszatért a verzióemelő PR nyitása — a bot-PR-en a GitHub "
        "szándékosan nem indít ellenőrzést (#1190), tehát az auto-merge "
        "sosem lefutó ellenőrzésre vár (#58)")


def test_a_kiado_NEM_tol_fel_automatika_agat(bump_lepes: str) -> None:
    """PR nélkül az ág csak szemét: 2026-09-05-én nyolc ilyen hevert."""
    assert "chore/auto-bump-" not in bump_lepes.replace(
        "chore/auto-bump-*", ""), (
        "visszatért a `chore/auto-bump-*` ág feltolása (#58)")


def test_a_kiadatlan_allapot_HANGOS_marad(bump_lepes: str) -> None:
    """#2487: a néma meghibásodás tilalma a visszavonás után is áll."""
    assert "::warning title=A beolvadt munka verzióemelés nélkül maradt" in bump_lepes, (
        "a kiadatlanul maradt munka némán megy el — pont ez volt a #2487")
    assert "GITHUB_STEP_SUMMARY" in bump_lepes, (
        "a futás összefoglalója nem mondja meg, mi történt")


def test_a_lelet_megnevezi_a_MEROT_ami_atveszi(bump_lepes: str) -> None:
    """Aki a piros helyett figyelmeztetést lát, tudja meg, mi őrzi tovább."""
    assert "#59" in bump_lepes, (
        "a jelzés nem mondja meg, hogy a lemaradást a manager-kör méri")


def test_a_kapu_tovabbra_is_a_dontes_elott_all(bump_lepes: str) -> None:
    """#1348: a versenyhelyzet-kapu nem eshetett ki a visszavonással."""
    assert "scripts/bump_kapu.py" in bump_lepes
    assert bump_lepes.index("kiadas_szukseges.py") < bump_lepes.index(
        "scripts/bump_kapu.py"), "a kapu a szükségesség-döntés ELŐTT fut"
