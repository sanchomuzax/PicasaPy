"""A verzióemelés bukása ne végződjön zölden (#2487).

## Mit fog meg

A `gh pr create` 2026-08-28 óta bukott egy repó-beállítás miatt, de a lépés
`##[warning]`-gal továbbment, és a futás ZÖLDEN fejeződött be. Emiatt EGY
HÉTIG egyetlen automatikus verzióemelő PR sem született úgy, hogy senki nem
tudott róla — pontosan az a néma meghibásodás, amit a projekt szabálya tilt.

A javítás: a bukó ág `pr_hiba=igen` jelzőt ír a lépés kimenetére, és a kiadás
UTÁN álló lépés ettől elbukik. A kiadás tehát változatlanul kimegy, csak a
futás lesz piros.

A néma bukásnak KÉT alakja van, és mindkettőt le kell fedni:

1. a lépés eljut a push/PR-nyitásig, és AZ bukik → `pr_hiba=igen`;
2. a lépés MAGA száll el (`kiadas_szukseges.py`, `auto_bump.py`, `git
   commit`, `gh pr list`) → a `continue-on-error: true` a `conclusion`-t
   zöldre írja, de az `outcome` `failure` marad.

⚠️ A kettéválasztás a lényeg: a „nincs mit emelni" utak (nincs kiadandó
változás, a kapu nem engedett, nem állapítható meg az alap) `exit 0`-val
zárnak és a jelzőt NEM állítják be — ez a NAPI útvonal (minden kód-PR maga
emel verziót, tehát a „nincs mit emelni" a szabályos alapeset), annak zöldnek
kell maradnia. Az itteni őrök mindkét irányt nézik, mert a munkafolyamatot
semmilyen teszt nem futtatja.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

_UT = Path(__file__).resolve()
RELEASE_YML = _UT.parents[2] / ".github" / "workflows" / "release.yml"

yaml = pytest.importorskip("yaml")
sys.path.insert(0, str(_UT.parents[2] / "scripts"))

JELZO = 'echo "pr_hiba=igen" >> "$GITHUB_OUTPUT"'


def _szoveg() -> str:
    return RELEASE_YML.read_text(encoding="utf-8")


def _lepesek() -> list[dict]:
    return yaml.safe_load(_szoveg())["jobs"]["release"]["steps"]


def _bukto_lepes() -> dict:
    for lepes in _lepesek():
        if "steps.bump.outputs.pr_hiba" in str(lepes.get("if", "")):
            return lepes
    raise AssertionError(
        "nincs olyan lépés, ami a verzióemelés bukására elbuktatná a futást — "
        "a bukás újra némán, zölden megy el (#2487)"
    )


class TestAJelzo:
    """A bukó ágak jelzést hagynak."""

class TestABuktatoLepes:
    def test_letezik_es_elbukik(self):
        lepes = _bukto_lepes()
        assert "exit 1" in str(lepes.get("run", "")), (
            "a lépés lefut, de nem buktatja el a futást — a jelzés díszlet"
        )

    def test_csak_a_JELZOTOL_fugg(self):
        felteteI = str(_bukto_lepes().get("if", ""))
        assert "pr_hiba" in felteteI and "igen" in felteteI

    def test_a_KIADAS_UTAN_all(self):
        """⚠️ A kiadásnak akkor is ki kell mennie, ha az emelés bukott — ezért
        a buktató lépés a kiadó lépés UTÁN áll, és a kiadó lépés nem függ
        tőle."""
        nevek = [str(lepes.get("name", "")) for lepes in _lepesek()]
        kiado = next(i for i, n in enumerate(nevek) if n.startswith("GitHub Release"))
        bukto = nevek.index(str(_bukto_lepes().get("name", "")))
        assert kiado < bukto, "a buktató lépés a kiadás ELŐTT áll — visszatartaná"

    def test_a_kiado_lepes_feltetel_nelkuli(self):
        kiado = next(
            lepes
            for lepes in _lepesek()
            if str(lepes.get("name", "")).startswith("GitHub Release")
        )
        assert kiado.get("if") is None, (
            "a kiadó lépés feltételes lett — a #2487 javítása nem tarthatja "
            "vissza a kiadást"
        )

    def test_a_kiadasi_or_a_bukas_utan_is_lefut(self):
        """Az `always()` nélkül a piros futás elhagyná a rendrakást (#1319)."""
        or_lepes = next(
            lepes
            for lepes in _lepesek()
            if str(lepes.get("name", "")).startswith("Kiadási őr")
        )
        assert "always()" in str(or_lepes.get("if", ""))

    def test_az_emelo_lepes_tovabbra_is_continue_on_error(self):
        """A bukás nem szakíthatja meg a futást a kiadás ELŐTT."""
        emelo = next(lepes for lepes in _lepesek() if lepes.get("id") == "bump")
        assert emelo.get("continue-on-error") is True


class TestAzElszallasIsPirosit:
    """⚠️ A bukás MÁSIK alakja: a lépés el sem jut a push/PR-nyitásig.

    A `continue-on-error: true` ilyenkor a `conclusion`-t zöldre írja, tehát
    a `pr_hiba` jelzőre épülő őr egymaga NEM fogja meg — a verzióemelés
    ugyanúgy elmarad, ugyanúgy némán. Az `outcome` őrzi meg a valóságot.
    """

    def test_az_elszallo_emelo_lepes_is_pirosra_viszi_a_futast(self):
        feltetel = str(_bukto_lepes().get("if", ""))
        assert "steps.bump.outcome" in feltetel and "failure" in feltetel, (
            "csak a `pr_hiba` jelző pirosít — ha az emelő lépés MAGA száll el "
            "(pl. az `auto_bump.py` vagy a `git commit` bukik), a "
            "`continue-on-error` zöldre írja a futást, és a verzióemelés "
            "megint némán marad el (#2487)"
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
# VISSZAVONVA EBBŐL A FÁJLBÓL: `test_a_PR_nyitas_bukasa_jelzot_ir`, `test_az_ag_feltolas_bukasa_is_jelzot_ir`, `test_a_bukas_HIBAKENT_naplozodik`, `test_a_NAPI_utvonalak_nem_allitanak_jelzot`, `test_a_NAPI_utak_exit_0_val_zarnak`
# ────────────────────────────────────────────────────────────────────────
