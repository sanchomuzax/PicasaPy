"""A push-azonosság kapu próbasora (picasapy-agent#84).

## A szabály, amit őriz

A GitHub idővonalán az **„X added N commits"** sort nem a commit szerzője
adja, hanem az, aki **feltolta** az ágat. Tárolt HTTPS-hitelesítéssel tolva
ott a TULAJDONOS neve jelenik meg a gépi munkán.

Mérve 2026-09-12-én, a repók `events` folyamán: a `PicasaPy`-n 11, a
`picasapy-agent`-en **63** push ment az ő fiókjával. Nem egyetlen kör
baklövése — ez volt az alapértelmezett út.

⚠️ A próbasor súlypontja a **`git push` alakjai**. A projektben ez a
hibaosztály már kétszer megharapott: a kiadás-kapu a `git -C <út>` alakon
csúszott el, a jegycím-őr azon, hogy csak a csupasz `gh`-t ismerte. Egy
kapu, ami a leggyakoribb alakot nem látja, nem kapu.
"""

from __future__ import annotations

import importlib.util
import io
import json
import pathlib

import pytest

_UT = (
    pathlib.Path(__file__).resolve().parents[2]
    / "scripts" / "hooks" / "push_azonossag_kapu.py"
)
_spec = importlib.util.spec_from_file_location("push_azonossag_kapu", _UT)
kapu = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(kapu)


BLOKKOLANDO = [
    # a csupasz alak
    "git push",
    "git push origin main",
    "git push -q origin main",
    "git push -u origin fix/valami",
    "git push --force-with-lease origin main",
    # ⚠️ a worktree-s alak — a kiadás-kapu ÉPPEN ezen csúszott el
    "git -C ~/picasapy-agent push origin main",
    "git -C /home/sancho/Documents/PicasaPy-wt-42 push -u origin fix/x",
    "git --git-dir=/x/.git --work-tree=/x push origin main",
    "git -c user.name=X push origin main",
    # összetett parancsban, a második tagként
    # ⚠️ #3105 óta a MEGNEVEZETT út dönt, nem a cwd — ezért a projekt
    # egyik munkafájára mutat. Idegen útra ugyanez ÁTMEGY (TestHatokor).
    "cd ~/Documents/PicasaPy-wt-42 && git push",
    'git commit -q -m "üzenet" && git push origin main',
    "git add f && git commit -m x && git push -q origin main",
    "git pull --rebase --quiet && git push -q origin main",
    # teljes útvonallal hívva
    "/usr/bin/git push origin main",
]

ATENGEDENDO = [
    # a HELYES út
    "~/picasapy-agent/eszkozok/git-push-bot . main",
    "~/picasapy-agent/eszkozok/git-push-bot ../PicasaPy-wt-42 fix/x --force",
    "eszkozok/git-push-bot . main",
    # a burkoló BELSEJE — az maga a bot azonossága
    'git -C "$munkafa" push "https://x-access-token:${token}@github.com/r.git" HEAD:refs/heads/x',
    # más git-műveletek
    "git status -sb",
    "git pull --rebase --quiet",
    "git log --oneline -5",
    "git fetch -q origin",
    # ⚠️ PRÓZA: a jegycím-őrt élesben KÉTSZER vezette meg ez az alak
    'echo "a csupasz git push tiltva, használd a burkolót"',
    "gh issue create --title 'A git push a tulajdonos fiókjával megy'",
]


#: A projekt egyik munkafája — a kapu hatóköre (#3105).
PROJEKT = "/home/sancho/Documents/PicasaPy"

#: A felhasználó egy MÁSIK projektje. Ott a bot GitHub Appja nincs telepítve,
#: tehát a kapu javasolta burkoló sem járható út.
IDEGEN = "/home/sancho/Documents/claude-code-rules"


@pytest.mark.parametrize("cmd", BLOKKOLANDO)
def test_blokkolja(cmd: str) -> None:
    assert kapu.blokkolando(cmd, PROJEKT), cmd


@pytest.mark.parametrize("cmd", ATENGEDENDO)
def test_atengedi(cmd: str) -> None:
    assert not kapu.blokkolando(cmd, PROJEKT), cmd


class TestHatokor:
    """#3105 — a kapu MÁS projektben néma.

    Élesben azonnal megharapott: a felhasználó egy másik projektjének
    repójába menő feltöltést blokkolta, ahol a bot Appja nincs is telepítve.
    A rosszul méretezett őr a HELYES utat zárja el.
    """

    def test_idegen_repoban_nem_blokkol(self) -> None:
        assert not kapu.blokkolando("git push", IDEGEN)

    def test_a_MEGNEVEZETT_ut_dont_a_cwd_helyett(self) -> None:
        """`cd <idegen repó>` után a munkamenet cwd-je még a miénk."""
        assert not kapu.blokkolando(f"cd {IDEGEN} && git push", PROJEKT)

    def test_a_mi_repnkra_idegen_cwd_bol_is_blokkol(self) -> None:
        assert kapu.blokkolando(
            "git -C ~/picasapy-agent push origin main", IDEGEN)

    def test_a_projekt_munkafajaban_blokkol(self) -> None:
        assert kapu.blokkolando("git push", PROJEKT + "-wt-42")


class TestAProzaAtmegy:
    """#3105 — a kapu a SAJÁT jegyének megnyitását blokkolta.

    A jegy törzsében szerepelt a tiltott parancs neve, és a kapu a
    jegynyitást állította meg. Az azonosság-kapu ezt régóta jól kezeli:
    idézett szakaszokat kivág, mielőtt parancsot keresne.
    """

    def test_idezojelben_nem_parancs(self) -> None:
        assert not kapu.blokkolando(
            f'gh issue create --body "a csupasz {""}git push" tiltva"', PROJEKT)

    def test_backtickben_sem(self) -> None:
        assert not kapu.blokkolando(
            "gh issue edit 1 --body 'a `git push` helyett a burkolót'", PROJEKT)

    def test_a_helyes_parancs_idezojelben_is_atmegy(self) -> None:
        assert not kapu.blokkolando(
            '"~/picasapy-agent/eszkozok/git-push-bot" . main', PROJEKT)


class TestAHookVege:
    def _fut(self, cmd: str, monkeypatch) -> int:
        monkeypatch.setattr(
            "sys.stdin",
            io.StringIO(json.dumps({"tool_input": {"command": cmd}})),
        )
        return kapu.main()

    def test_blokkolas_kilepokodja_2(self, monkeypatch) -> None:
        assert self._fut("git push origin main", monkeypatch) == 2

    def test_atengedes_kilepokodja_0(self, monkeypatch) -> None:
        assert self._fut("git status", monkeypatch) == 0

    def test_a_hibauzenet_megmondja_a_HELYES_parancsot(self, monkeypatch, capsys) -> None:
        """A puszta tiltás kevés: aki elakad, tudja meg, mit írjon helyette."""
        self._fut("git push origin main", monkeypatch)
        assert "git-push-bot" in capsys.readouterr().err

    def test_rossz_bemenetre_atenged(self, monkeypatch) -> None:
        """Fail-open: elromlott kapu nem akaszthat meg munkát."""
        monkeypatch.setattr("sys.stdin", io.StringIO("nem json"))
        assert kapu.main() == 0
