"""A verzióemelő kapu őrei (#1348).

## Mit fog meg

Két verzióemelő PR keletkezett ugyanarra a verzióra (0.8.74: #1346 beolvadt,
#1347 öt perccel később `CONFLICTING` állapotban nyílt). A #1319
konkurenciazára a FUTÁSOKAT sorbaállítja, de a második futás akkor is a
SAJÁT, korábbi commitját nézi — ott még a régi verzió áll —, és ugyanarra a
számra nyit másodikat.

A `scripts/bump_kapu.py` ezt a döntést hozza meg a módosítás ELŐTT. Az itteni
őrök egyrészt a döntésre, másrészt a `release.yml`-be kötésre néznek: a
munkafolyamatot semmilyen teszt nem futtatja, tehát a bekötés némán
kikerülhetne.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

_UT = Path(__file__).resolve()
sys.path.insert(0, str(_UT.parents[2] / "scripts"))

import bump_kapu  # noqa: E402

RELEASE_YML = _UT.parents[2] / ".github" / "workflows" / "release.yml"


def _valasz(kimenet: str = "", *, kod: int = 0) -> subprocess.CompletedProcess[str]:
    return subprocess.CompletedProcess(args=[], returncode=kod, stdout=kimenet, stderr="")


class TestDontes:
    """A tiszta döntésfüggvény — ez a lelke a kapunak."""

    def test_a_versenyhelyzet_MASODIK_futasat_megfogja(self):
        """A jegy mért esete: a 0.8.74 emelése már úton van egy nyitott PR-en."""
        szabad, indok = bump_kapu.dontes(
            "0.8.74",
            nyitott_agak=["chore/auto-bump-0.8.74"],
            fo_verzio="0.8.73",
            van_kiadas=False,
        )
        assert szabad is False
        assert "0.8.74" in indok

    def test_barmely_MAS_verziora_nyitott_emeles_is_megallit(self):
        """Egyszerre EGY emelés lehet úton — különben láncban duplikálódik."""
        szabad, _ = bump_kapu.dontes(
            "0.8.75",
            nyitott_agak=["chore/auto-bump-0.8.74"],
            fo_verzio="0.8.73",
            van_kiadas=False,
        )
        assert szabad is False

    def test_emberi_PR_nem_akadaly(self):
        """⚠️ A kapu hatóköre az automatika ága. Egy nyitott emberi PR-től
        a kiadás nem állhat meg — abból napi tucat van."""
        szabad, _ = bump_kapu.dontes(
            "0.8.74",
            nyitott_agak=["fix/1348-dupla-verzioemelo", "feat/valami"],
            fo_verzio="0.8.73",
            van_kiadas=False,
        )
        assert szabad is True

    def test_a_lejart_emeles_nem_indul_ujra(self):
        """A másik futás PR-je már BE is olvadt: a main ott tart, a mi
        emelésünk lejárt. Enélkül született a #1347 `CONFLICTING` PR."""
        szabad, indok = bump_kapu.dontes(
            "0.8.74", nyitott_agak=[], fo_verzio="0.8.74", van_kiadas=False
        )
        assert szabad is False
        assert "0.8.74" in indok

    def test_a_mar_kiadott_celra_nem_emel(self):
        szabad, _ = bump_kapu.dontes(
            "0.8.74", nyitott_agak=[], fo_verzio="0.8.73", van_kiadas=True
        )
        assert szabad is False

    def test_tiszta_helyzetben_ENGED(self):
        """⚠️ A kapunak nem elég tiltania: ha mindig „nem"-et mondana, a
        kiadás állna meg — az a súlyosabb hiba."""
        szabad, _ = bump_kapu.dontes(
            "0.8.74", nyitott_agak=[], fo_verzio="0.8.73", van_kiadas=False
        )
        assert szabad is True

    def test_a_tajekozodas_bukasa_a_kiadas_fele_dont(self):
        """Nem tudjuk kiolvasni az origin/main verzióját, sem a kiadást.

        Az elmaradt kiadás drágább, mint egy fölösleges PR (azt a kiadási
        őr lezárja, #1319) — ugyanaz az elv, mint a `kiadas_szukseges.py`-ben."""
        szabad, _ = bump_kapu.dontes(
            "0.8.74", nyitott_agak=[], fo_verzio=None, van_kiadas=None
        )
        assert szabad is True


class TestLekerdezes:
    """A `gh`/`git` felőli oldal — hamis futtatóval."""

    def test_csak_az_automatika_agait_veszi(self):
        def futtato(args):
            adat = [
                {"headRefName": "fix/1348-valami"},
                {"headRefName": "chore/auto-bump-0.8.74"},
            ]
            return _valasz(json.dumps(adat))

        assert bump_kapu.nyitott_auto_agak("o/r", futtato=futtato) == (
            "chore/auto-bump-0.8.74",
        )

    def test_a_lekerdezes_bukasa_ures_listat_ad(self):
        assert bump_kapu.nyitott_auto_agak(
            "o/r", futtato=lambda args: _valasz(kod=1)
        ) == ()

    def test_a_romlott_JSON_sem_dol_el(self):
        assert bump_kapu.nyitott_auto_agak(
            "o/r", futtato=lambda args: _valasz("{ nem json")
        ) == ()

    def test_a_fo_verziot_az_origin_mainrol_olvassa(self):
        """⚠️ NEM a munkafáéból: a futás a saját, korábbi commitját nézi —
        épp ez a versenyhelyzet forrása."""
        hivasok: list[list[str]] = []

        def futtato(args):
            hivasok.append(args)
            if args[:2] == ["git", "fetch"]:
                return _valasz()
            return _valasz('[project]\nname = "picasapy"\nversion = "0.8.74"\n')

        assert bump_kapu.fo_ag_verzioja(futtato=futtato) == "0.8.74"
        assert ["git", "show", "origin/main:pyproject.toml"] in hivasok

    def test_a_fetch_bukasa_None(self):
        assert bump_kapu.fo_ag_verzioja(futtato=lambda args: _valasz(kod=1)) is None

    def test_van_e_kiadas(self):
        assert bump_kapu.van_e_kiadas("0.8.74", "o/r", futtato=lambda a: _valasz()) is True
        assert (
            bump_kapu.van_e_kiadas("0.8.74", "o/r", futtato=lambda a: _valasz(kod=1))
            is False
        )

    def test_a_main_elso_sora_a_valasz(self, capsys):
        """A `release.yml` a kimenet ELSŐ sorát olvassa — ha az elcsúszik,
        a kapu némán engedni fog mindent."""
        def futtato(args):
            if args[:3] == ["gh", "pr", "list"]:
                return _valasz(json.dumps([{"headRefName": "chore/auto-bump-0.8.74"}]))
            return _valasz(kod=1)

        assert bump_kapu.main(["--repo", "o/r", "--cel", "0.8.74"], futtato=futtato) == 0
        assert capsys.readouterr().out.splitlines()[0] == "nem"


class TestWorkflowBekotes:
    """A munkafolyamatot semmilyen teszt nem futtatja — ez az őr szól, ha a
    bekötés némán kikerül."""

    @staticmethod
    def _szoveg() -> str:
        return RELEASE_YML.read_text(encoding="utf-8")

    def test_a_kapu_be_van_kotve(self):
        assert "scripts/bump_kapu.py" in self._szoveg(), (
            "a verzióemelő kapu kikerült a release.yml-ből — a második futás "
            "újra duplikált verzióemelő PR-t nyit (#1348)"
        )

    def test_a_kapu_a_MODOSITAS_ELOTT_dont(self):
        """⚠️ Utólag futtatva marad egy commit és egy árva `chore/auto-bump-*`
        ág — 2026-09-05-én nyolc ilyen ág hevert a távolban."""
        szoveg = self._szoveg()
        kapu = szoveg.index("scripts/bump_kapu.py")
        assert kapu < szoveg.index("python3 scripts/auto_bump.py"), (
            "a kapu az auto_bump UTÁN fut — a fölösleges commit már megvan"
        )
        assert kapu < szoveg.index("git push --force origin"), (
            "a kapu az ág feltolása UTÁN fut — az árva ág már ottmarad"
        )

    def test_a_kapu_valasza_szamit(self):
        """A kimenet olvasása nélkül a hívás díszlet volna."""
        szoveg = self._szoveg()
        assert '"$kapu"' in szoveg and 'head -n1' in szoveg, (
            "a kapu válaszát nem olvassa senki"
        )

    def test_a_bukott_PR_nyitas_utan_nem_marad_arva_ag(self):
        """⚠️ A kapu NYITOTT PR-t néz — egy PR nélküli ág nem látszik neki.

        Mérve 2026-09-05: nyolc `chore/auto-bump-*` ág hevert a távolban PR
        nélkül, mert a `gh pr create` a repó beállítása miatt bukott
        („GitHub Actions is not permitted to create or approve pull
        requests"). Az ilyen ág se nem véd, se nem hasznos."""
        szoveg = self._szoveg()
        assert 'git push origin --delete "$ag"' in szoveg, (
            "a PR nélkül maradt verzióemelő ágat senki nem takarítja el"
        )

    def test_a_kapu_a_lepesen_BELUL_marad(self):
        """A bump lépés `continue-on-error` — a kapu bukása nem viheti el a
        kiadást (#1165). Ha külön lépésbe kerülne, ez a védelem elveszne."""
        yaml = pytest.importorskip("yaml")
        adat = yaml.safe_load(self._szoveg())
        bump = next(
            lepes
            for lepes in adat["jobs"]["release"]["steps"]
            if lepes.get("id") == "bump"
        )
        assert "scripts/bump_kapu.py" in bump["run"]
        assert bump.get("continue-on-error") is True
