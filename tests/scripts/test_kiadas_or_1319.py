"""A kiadási őr: mit tesz a félbemaradt automatikával? (#1319)

A #1318 nem attól lett baj, hogy egy PR létrejött, hanem attól, hogy utána
NEM volt, aki elrendezze. A bot-PR-en a GitHub szándékosan nem indít
ellenőrzést (#1190, #1204), így az auto-merge sosem sült el, és a PR némán
ott ült — a rendrakás egy figyelmes műszakon múlt.

⚠️ A legfontosabb állítás ebben a fájlban a `test_emberi_pr_hoz_SOHA_nem_nyul`:
egy őr, ami emberi PR-t zárhat le, többet ront, mint amennyit ment.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "scripts"))

import kiadas_or as ko  # noqa: E402


def _pr(szam: int, ag: str, *, automerge: bool = True, ellenorzes: bool = True) -> dict:
    return {"szam": szam, "ag": ag, "automerge": automerge, "van_ellenorzes": ellenorzes}


class _Naplozo:
    """`gh`-helyettes, ami rögzíti a hívásokat és előre adott válaszokat ad."""

    def __init__(self, valaszok: dict[str, tuple[int, str]] | None = None) -> None:
        self.hivasok: list[list[str]] = []
        self._valaszok = valaszok or {}

    def __call__(self, args: list[str]) -> subprocess.CompletedProcess[str]:
        self.hivasok.append(args)
        for kulcs, (kod, kimenet) in self._valaszok.items():
            if kulcs in " ".join(args):
                return subprocess.CompletedProcess(args, kod, kimenet, "")
        return subprocess.CompletedProcess(args, 0, "", "")

    def parancsok(self, resz: str) -> list[list[str]]:
        return [h for h in self.hivasok if resz in " ".join(h)]


class TestTeendok:
    def test_emberi_pr_hoz_SOHA_nem_nyul(self) -> None:
        """Az őr hatóköre kizárólag a SAJÁT automatika-ágai."""
        prek = [
            _pr(1300, "feat/1299-uj-effekt", automerge=False, ellenorzes=False),
            _pr(1301, "fix/vezerlo-hurok", automerge=False, ellenorzes=False),
        ]
        assert ko.teendok(prek, kiadott_verziok=set(), fo_verzio="0.8.69") == ()

    def test_a_mukodo_pr_hez_nincs_teendo(self) -> None:
        prek = [_pr(1318, "chore/auto-bump-0.8.70")]
        assert ko.teendok(prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69") == ()

    def test_ellenorzes_nelkuli_pr_re_CI_t_indit(self) -> None:
        prek = [_pr(1318, "chore/auto-bump-0.8.70", ellenorzes=False)]
        teendo = ko.teendok(prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69")
        assert [t.fajta for t in teendo] == ["ci"]
        assert teendo[0].pr == 1318

    def test_elszallt_automerge_ujraelesites(self) -> None:
        prek = [_pr(1318, "chore/auto-bump-0.8.70", automerge=False)]
        teendo = ko.teendok(prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69")
        assert [t.fajta for t in teendo] == ["automerge"]

    def test_mar_kiadott_verzio_pr_je_elavult(self) -> None:
        prek = [_pr(1318, "chore/auto-bump-0.8.70")]
        teendo = ko.teendok(prek, kiadott_verziok={"0.8.70"}, fo_verzio="0.8.70")
        assert [t.fajta for t in teendo] == ["zaras"]
        assert "0.8.70" in teendo[0].indok

    def test_a_main_altal_lehagyott_pr_elavult(self) -> None:
        """A main már 0.8.71-nél tart — a 0.8.70-es emelés értelmét vesztette."""
        prek = [_pr(1318, "chore/auto-bump-0.8.70")]
        teendo = ko.teendok(prek, kiadott_verziok=set(), fo_verzio="0.8.71")
        assert [t.fajta for t in teendo] == ["zaras"]

    def test_egyszerre_csak_EGY_verzioemelo_pr_maradhat(self) -> None:
        """Több gyors egymás utáni merge több PR-t szült — a legújabb marad."""
        prek = [
            _pr(1318, "chore/auto-bump-0.8.70", ellenorzes=False),
            _pr(1320, "chore/auto-bump-0.8.71", ellenorzes=False),
            _pr(1321, "chore/auto-bump-0.8.72", ellenorzes=False),
        ]
        teendo = ko.teendok(prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69")
        zarva = {t.pr for t in teendo if t.fajta == "zaras"}
        assert zarva == {1318, 1320}
        assert [t.pr for t in teendo if t.fajta == "ci"] == [1321]

    def test_ertelmezhetetlen_verzioju_ag_erintetlen(self) -> None:
        prek = [_pr(1318, "chore/auto-bump-kiserleti", automerge=False)]
        assert ko.teendok(prek, kiadott_verziok=set(), fo_verzio="0.8.69") == ()


class TestHianyzoKiadas:
    def test_kiadatlan_fo_verziohoz_kiadast_kezdemenyez(self) -> None:
        assert ko.kiadas_teendo("0.8.70", {"0.8.69"}) is not None

    def test_kiadott_verziohoz_nincs_teendo(self) -> None:
        assert ko.kiadas_teendo("0.8.69", {"0.8.69"}) is None


class TestVegrehajtas:
    def test_a_ci_t_kezzel_inditja_az_agon(self) -> None:
        """A bizonyítottan működő út: a v0.8.69 is így ment be."""
        naplo = _Naplozo()
        ko.vegrehajt(
            (ko.Teendo("ci", 1318, "chore/auto-bump-0.8.70", "nincs ellenőrzés"),),
            repo="sanchomuzax/PicasaPy",
            runner=naplo,
        )
        assert naplo.parancsok("workflow run") == [
            ["gh", "workflow", "run", "ci.yml", "--repo", "sanchomuzax/PicasaPy",
             "--ref", "chore/auto-bump-0.8.70"]
        ]

    def test_zaraskor_indokot_ir_es_agat_torol(self) -> None:
        naplo = _Naplozo()
        ko.vegrehajt(
            (ko.Teendo("zaras", 1318, "chore/auto-bump-0.8.70", "elavult"),),
            repo="sanchomuzax/PicasaPy",
            runner=naplo,
        )
        assert naplo.parancsok("issue comment") == []
        komment = naplo.parancsok("pr comment")
        assert komment and "elavult" in " ".join(komment[0])
        assert naplo.parancsok("pr close")[0][-1] == "--delete-branch"

    def test_automerge_ujraelesites(self) -> None:
        naplo = _Naplozo()
        ko.vegrehajt(
            (ko.Teendo("automerge", 1318, "chore/auto-bump-0.8.70", "leesett"),),
            repo="sanchomuzax/PicasaPy",
            runner=naplo,
        )
        assert naplo.parancsok("pr merge")[0][-3:] == ["--auto", "--squash", "--delete-branch"]

    def test_a_bukott_lepes_nem_akasztja_meg_a_tobbit(self) -> None:
        """Egy elbukó `gh` hívás után a többi teendő MÉG lefut."""
        naplo = _Naplozo({"pr close": (1, "hiba")})
        bukott = ko.vegrehajt(
            (
                ko.Teendo("zaras", 1318, "chore/auto-bump-0.8.70", "elavult"),
                ko.Teendo("ci", 1321, "chore/auto-bump-0.8.72", "nincs ellenőrzés"),
            ),
            repo="sanchomuzax/PicasaPy",
            runner=naplo,
        )
        assert naplo.parancsok("workflow run")
        assert [t.pr for t in bukott] == [1318]


class TestHibajelzes:
    def test_hibarol_issue_t_nyit(self) -> None:
        naplo = _Naplozo({"issue list": (0, "[]")})
        ko.jelents_hibat(
            "A kiadási őr nem tudta rendezni a #1318-at",
            "részletek",
            repo="sanchomuzax/PicasaPy",
            runner=naplo,
        )
        assert naplo.parancsok("issue create")

    def test_ugyanarrol_nem_nyit_masodik_issue_t(self) -> None:
        """Negyedóránként futó őr — issue-áradat nélkül."""
        cim = "A kiadási őr nem tudta rendezni a #1318-at"
        naplo = _Naplozo({"issue list": (0, f'[{{"number":9,"title":"{cim}"}}]')})
        ko.jelents_hibat(cim, "részletek", repo="sanchomuzax/PicasaPy", runner=naplo)
        assert naplo.parancsok("issue create") == []


class TestFolosleges1324:
    """A PR nem csak ELAVULT lehet, hanem FÖLÖSLEGES is (#1324).

    Élesben mérve, a #1321 beolvadásának percében: egy dokumentáció-only
    merge még a RÉGI automatikával nyitott egy verzióemelő PR-t (#1322), és
    az őr — mert csak az elavult esetet ismerte — szabályosan el is indította
    rajta a CI-t. Kis híján kiment egy 0.8.70, amiben a felhasználó számára
    semmi nem változott.
    """

    def test_indokolatlan_emelest_lezar(self) -> None:
        prek = [_pr(1322, "chore/auto-bump-0.8.70", ellenorzes=False)]
        teendo = ko.teendok(
            prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69", indokolt=False
        )
        assert [t.fajta for t in teendo] == ["zaras"]
        assert "nincs kiadandó változás" in teendo[0].indok

    def test_indokolatlan_emelesre_NEM_indit_CI_t(self) -> None:
        """A fölösleges PR-re indított teljes mátrix tiszta veszteség."""
        prek = [_pr(1322, "chore/auto-bump-0.8.70", automerge=False, ellenorzes=False)]
        teendo = ko.teendok(
            prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69", indokolt=False
        )
        assert not [t for t in teendo if t.fajta in {"ci", "automerge"}]

    def test_indokolt_esetben_valtozatlan_a_viselkedes(self) -> None:
        prek = [_pr(1322, "chore/auto-bump-0.8.70", ellenorzes=False)]
        teendo = ko.teendok(
            prek, kiadott_verziok={"0.8.69"}, fo_verzio="0.8.69", indokolt=True
        )
        assert [t.fajta for t in teendo] == ["ci"]


class TestIndokoltsagMerese1324:
    def test_a_kiadas_ota_torteneteket_meri(self) -> None:
        naplo = _Naplozo({"diff": (0, "docs/a.md\n")})
        assert ko.indokolt_e_az_emeles("0.8.69", runner=naplo) is False
        assert ["git", "diff", "--name-only", "v0.8.69", "HEAD"] in naplo.hivasok

    def test_kodos_valtozasra_indokolt(self) -> None:
        naplo = _Naplozo({"diff": (0, "src/picasapy/app/controller.py\n")})
        assert ko.indokolt_e_az_emeles("0.8.69", runner=naplo) is True

    def test_meresi_bukas_eseten_INDOKOLTNAK_veszi(self) -> None:
        """Ha nem tudunk mérni, nem zárunk le semmit — a kiadás felé tévedünk."""
        naplo = _Naplozo({"diff": (128, "")})
        assert ko.indokolt_e_az_emeles("0.8.69", runner=naplo) is True
