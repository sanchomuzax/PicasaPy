"""A jegycím-őr próbasora (#1378).

## A szabály, amit őriz

A cím a jegy **legtartósabb** része: commit-üzenetbe, PR-címbe,
változásnaplóba és keresésbe kerül. Az állapot viszont a **leghamarabb
avuló** adat — a repóban van rá címke (`P0`–`P4`, `blocked`, `in-progress`,
`ready`). A kettőt összekötni garantált elavulás: mérve a #1276 és a #1153,
ahol a „P1:" a címben ÉS a `P1` címke is ott van.

A cím helyette: **[érintett funkció] + alany + állítmány**, és látszódjon a
honnan-hová. A funkciónév nem díszítés — enélkül a jegy fél év múlva
kereshetetlen.

⚠️ Az őr csak a MECHANIKUSAN BIZTOSAT blokkolja. A téves blokk drágább, mint
egy gyengébb cím: aki nem tud jegyet nyitni, az nem jegyez fel semmit.
"""

from __future__ import annotations

import importlib.util
import io
import json
import pathlib

import pytest

_UT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts" / "hooks" / "jegycim_or.py"
)
_spec = importlib.util.spec_from_file_location("jegycim_or", _UT)
őr = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(őr)


BLOKKOLANDO = [
    # prioritás a címben — a #1276 és a #1153 valódi alakja
    'gh issue create --title "P1: a Klipek lap a KOLLAZS csomopontjait mutatja"',
    "gh issue create --title 'P0 - a mentés elveszti a képaláírást'",
    # állapot a címben
    'gh issue create --title "BLOKKOLT: a kollázs exportja nem indul"',
    'gh issue create --title "[blocked] a hisztogram nem frissül nagyításkor"',
    'gh issue create --title "WIP a mappanézet átalakítása fa-nézetté"',
    'gh issue create --title "TODO: a nyelvi ellenőrzés bekötése a CI-be"',
    # conventional-commit előtag — az a COMMITÉ, nem a jegyé
    'gh issue create --title "fix: a kollázs gombfelirata levágódik"',
    'gh issue create --title "feat(export): a mappába mentés párbeszéde"',
    # nyomaték nagybetűvel = burkolt prioritás
    'gh issue create --title "KRITIKUS: a szerkesztő elveszti a módosításokat"',
    'gh issue create --title "A mentés SOHA nem írhatja felül az eredetit"',
    # semmitmondó, kereshetetlen
    'gh issue create --title "Hisztogram"',
    'gh issue create --title "Kollázs hiba"',
    # a szerkesztés ugyanúgy jegycím
    'gh issue edit 1276 --title "P1: a Klipek lap üres"',
    # ⛔ agent#32: eszközönként KÜLÖN bot-burkoló. Az őr eddig csak a
    # `gh`/`gh-bot` alakot ismerte, tehát a Codexből nyitott jegyek címét
    # meg sem nézte volna — harmadik névre kötött vakfolt a projektben.
    'codex-bot issue create --title "P1: a Klipek lap üres"',
    '~/picasapy-agent/eszkozok/codex-bot issue create --title "Hisztogram"',
    'opencode-bot issue edit 1276 --title "BLOKKOLT: a mentés elvész"',
]

ATENGEDENDO = [
    # a kívánt alak: funkciónév + alany + állítmány + honnan-hová
    'gh issue create --title "A Klipek fül a kollázs csomópontjait sorolja fel '
    'a mappa képei helyett"',
    'gh issue create --title "Az Exportálás mappába párbeszéd az eredeti Picasa '
    'elrendezését követi"',
    # a „blokkol" IGE nem állapotcímke — élő példa a repóból (#1056)
    'gh issue create --title "A kiadás-kapu jó szándékú munkát is blokkol az '
    'expanduser sorrendje miatt"',
    # csupa nagybetűs NÉV megkülönböztetésre — nem nyomaték
    'gh issue create --title "A kollázs-szerkesztő KLIPEK füle nem frissíti az '
    'indexképeket"',
    # a PR-cím MÁS konvenció: ott a conventional-commit előtag KELL
    'gh pr create --title "fix: a kollázs gombfelirata levágódik (#1116)"',
    # nem jegynyitás
    "gh issue list --state open",
    'gh issue comment 1276 --body "P1 marad"',
    "git commit -m 'fix: valami'",
]


def _futtat(monkeypatch, parancs: str) -> tuple[int, str]:
    monkeypatch.setattr(
        őr.sys, "stdin",
        io.StringIO(json.dumps({"tool_input": {"command": parancs}, "cwd": "/tmp"})),
    )
    hiba = io.StringIO()
    monkeypatch.setattr(őr.sys, "stderr", hiba)
    return őr.main(), hiba.getvalue()


@pytest.mark.parametrize("parancs", BLOKKOLANDO)
def test_blokkolando(monkeypatch, parancs: str) -> None:
    kod, uzenet = _futtat(monkeypatch, parancs)
    assert kod == 2, f"átengedte: {parancs}"
    assert "Jegycím-őr" in uzenet


@pytest.mark.parametrize("parancs", ATENGEDENDO)
def test_atengedendo(monkeypatch, parancs: str) -> None:
    kod, _ = _futtat(monkeypatch, parancs)
    assert kod == 0, f"tévesen blokkolta: {parancs}"


class TestUzenet:
    def test_megmondja_hova_valo_az_allapot(self, monkeypatch) -> None:
        _, uzenet = _futtat(
            monkeypatch, 'gh issue create --title "P1: a kollázs exportja néma"'
        )
        assert "címke" in uzenet, "nem mondja meg, hogy címkébe való"

    def test_megmutatja_a_kivant_alakot(self, monkeypatch) -> None:
        _, uzenet = _futtat(monkeypatch, 'gh issue create --title "Hisztogram"')
        assert "alany" in uzenet and "funkció" in uzenet


class TestFailOpen:
    def test_rossz_bemenet_nem_blokkol(self, monkeypatch) -> None:
        monkeypatch.setattr(őr.sys, "stdin", io.StringIO("nem json"))
        assert őr.main() == 0

    def test_elromlott_or_nem_akaszt_meg_munkat(self, monkeypatch) -> None:
        """Egy elromlott kapu nem foghatja meg a párhuzamos munkameneteket."""
        monkeypatch.setattr(
            őr, "_blokkolando", lambda cmd: (_ for _ in ()).throw(RuntimeError("x"))
        )
        monkeypatch.setattr(
            őr.sys, "stdin",
            io.StringIO(json.dumps({"tool_input": {"command": 'gh issue create --title "P1: x"'}})),
        )
        assert őr.main() == 0


class TestBotEszkoz:
    """#72: az őr eddig CSAK a csupasz `gh` alakot ismerte fel.

    A projekt szabálya viszont kimondja, hogy GitHub-műveletet **kizárólag**
    a `gh-bot`-tal szabad kiadni — az őr tehát élesben soha nem futott le.

    ⚠️ A kár mért: 2026-09-09-én egy kör egy egybetűs helyőrző címmel
    átnevezte a termék-repó egyik lezárt jegyét, `gh-bot`-tal, és az őr
    **nem szólt**. Ugyanaznap viszont **kétszer blokkolta a jelenségről
    szóló PRÓZÁT**, mert abban ott állt a csupasz alak. A kapu a szöveget
    fogta meg, a műveletet nem — pontosan a „fogat csak lefutott
    ellenőrzésnek" tiltása.
    """

    ROSSZ_CIM = "Hisztogram"

    @pytest.mark.parametrize("program", [
        "gh",
        "gh-bot",
        "./eszkozok/gh-bot",
        "/home/sancho/picasapy-agent/eszkozok/gh-bot",
        "~/picasapy-agent/eszkozok/gh-bot",
    ])
    def test_minden_irasmod_BLOKKOL(self, monkeypatch, program: str) -> None:
        kod, uzenet = _futtat(
            monkeypatch, f'{program} issue edit 66 --title "{self.ROSSZ_CIM}"')

        assert kod == 2, f"átengedte: {program}"
        assert "Jegycím-őr" in uzenet

    @pytest.mark.parametrize("program", ["gh", "./eszkozok/gh-bot"])
    def test_a_JO_cim_minden_irasmoddal_atmegy(self, monkeypatch, program: str) -> None:
        """Kapu-ellenőrzés: a bővítés nem lett túl mohó."""
        kod, _ = _futtat(
            monkeypatch,
            f'{program} issue create --title "A tálca gombja nem jelenik meg '
            f'indulás után"')

        assert kod == 0

    def test_a_PROZA_tovabbra_is_atmegy(self, monkeypatch) -> None:
        """A parancspozíció-szabály nem romolhat el: a szövegben EMLÍTETT
        alak nem futtatás. Enélkül nem lehetne magáról a hibáról írni —
        élesben pontosan ez akadályozta meg kétszer a #72 rögzítését."""
        kod, _ = _futtat(
            monkeypatch,
            "echo './eszkozok/gh-bot issue edit 1 --title Hisztogram' >> jegyzet.md")

        assert kod == 0

    def test_a_bot_PR_cime_tovabbra_is_kimarad(self, monkeypatch) -> None:
        """A `pr create` más konvenció — ez a bővítéssel sem változik."""
        kod, _ = _futtat(
            monkeypatch,
            './eszkozok/gh-bot pr create --title "fix: a gombfelirat levágódik (#72)"')

        assert kod == 0
