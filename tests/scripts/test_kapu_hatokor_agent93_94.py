"""A kapuk HATÓKÖRE: burkoló-nevek és ADAT-heredoc (agent#93, agent#94).

## Mit őriz

**agent#93** — a kiadás-kapu a kiadás-létrehozást csak a CSUPASZ `gh`
programnévvel kereste, miközben a projekt szabálya szerint GitHub-műveletet
kizárólag a bot-burkolókkal adunk ki. Mérve: a hat valódi írásmód közül
egyedül a tiltott csupasz alak blokkolt, mind az öt HASZNÁLT alak átment —
vagyis a kapu a kiadás-létrehozásra nézve nem létezett. Ez a negyedik
névre kötött vakfolt a projektben (#72, #84, #87 után).

**agent#94** — a kapuk a parancs teljes szövegét pásztázzák, és a
parancspozíció újsor után is kezdődik, ezért egy `cat > fájl <<EOF`
heredoc TÖRZSÉT is parancsnak vették. Következmény: nem lehetett
dokumentálni a szabályt, mert a dokumentációban ott áll a tiltott példa.
Egyetlen körön belül négyszer állított meg élesben.

⚠️ A próbák parancsszövegei **mértek**: ezek az alakok blokkoltak (vagy
mentek át) élesben. A tiltott mintákat a fájl összefűzéssel állítja elő,
különben ez a próbafájl a saját kapuit váltaná ki.
"""

from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import sys

import pytest

_HOOKOK = pathlib.Path(__file__).resolve().parents[2] / "scripts" / "hooks"

# A tiltott alakok — összefűzve, hogy a fájl SZÖVEGE ne váltsa ki a kapukat.
_JEGY = "gh-bot issue " + "create --title"
_PUSH = "git " + "push origin main"
_KIADAS = "release " + "create v9.9.9 --notes x"


def _kozos():
    ut = _HOOKOK / "kapu_kozos.py"
    spec = importlib.util.spec_from_file_location("kapu_kozos", ut)
    modul = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(modul)
    return modul


def _kapu(hook: str, cmd: str) -> int:
    """A hook kilépőkódja a parancsra. 2 = blokkol, 0 = átenged."""
    return subprocess.run(
        [sys.executable, str(_HOOKOK / hook)],
        input=json.dumps({"tool_input": {"command": cmd}, "cwd": str(_HOOKOK)}),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    ).returncode


# ---------------------------------------------------------------- agent#93

#: Mind a hat írásmód, ahogy élesben mérve lett. A csupasz `gh` az egyetlen,
#: amit a régi kapu fogott — a másik öt a TÉNYLEGES munkamenetünk alakja.
KIADAS_ALAKOK = [
    "gh " + _KIADAS,
    "gh-bot " + _KIADAS,
    "eszkozok/gh-bot " + _KIADAS,
    "~/picasapy-agent/eszkozok/gh-bot " + _KIADAS,
    "codex-bot " + _KIADAS,
    "hermes-bot " + _KIADAS,
    "opencode-bot " + _KIADAS,
]


@pytest.mark.parametrize("cmd", KIADAS_ALAKOK)
def test_a_kiadas_letrehozas_minden_irasmoddal_blokkol(cmd: str) -> None:
    assert _kapu("release_kapu.py", cmd) == 2, cmd


def test_a_burkolo_lista_egy_helyen_el() -> None:
    """A névre kötött vakfolt ellen: a lista a közös modulban van.

    Ha egy új eszköz felvételéhez több fájlt kell átírni, a hibaosztály
    visszatér — ezt a próba kimondja, nem csak reméli."""
    kozos = _kozos()
    assert set(kozos.BURKOLOK) >= {"gh-bot", "codex-bot", "hermes-bot",
                                   "opencode-bot"}
    for nev in ("jegycim_or.py", "release_kapu.py"):
        szoveg = (_HOOKOK / nev).read_text(encoding="utf-8")
        assert "from kapu_kozos import" in szoveg, nev
        # saját, párhuzamos burkoló-lista nem maradhat a fájlban
        assert 'r"(?:[\\w.~-]*' not in szoveg, nev


def test_a_cimke_OLVASO_parancs_atmegy() -> None:
    """Pozitív kontroll: a kapu ne legyen zajos.

    A kiadás-kapu szigorítása nem vonatkozhat az olvasásra."""
    assert _kapu("release_kapu.py", "gh-bot release " + "list --limit 5") == 0
    assert _kapu("release_kapu.py", "git " + "tag --list 'v0.8.*'") == 0


# ---------------------------------------------------------------- agent#94

#: Az ADAT-heredocba írt dokumentáció — pontosan az az alak, amit élesben
#: blokkolt. Mind átmenendő.
DOKUMENTACIO = [
    ("jegycim_or.py",
     "cat > /tmp/doc.md <<'EOF'\nRossz példa:\n" + _JEGY + ' "Hiba"\nEOF\n'),
    ("push_azonossag_kapu.py",
     "cd ~/Documents/PicasaPy && cat > /tmp/doc.md <<'EOF'\nTilos:\n"
     + _PUSH + "\nEOF\n"),
    ("release_kapu.py",
     "cat > /tmp/doc.md <<'EOF'\nTilos:\ngh-bot " + _KIADAS + "\nEOF\n"),
    # `tee` ugyanígy adat
    ("jegycim_or.py", "tee /tmp/doc.md <<EOF\n" + _JEGY + ' "Hiba"\nEOF\n'),
    # `<<-` tabos határoló
    ("jegycim_or.py",
     "cat > /tmp/d.md <<-EOF\n\t" + _JEGY + ' "Hiba"\n\tEOF\n'),
    # idézőjel nélküli határoló
    ("jegycim_or.py", "cat > /tmp/d.md <<VEGE\n" + _JEGY + ' "Hiba"\nVEGE\n'),
]


@pytest.mark.parametrize("hook,cmd", DOKUMENTACIO)
def test_az_adat_heredoc_torzse_nem_parancs(hook: str, cmd: str) -> None:
    assert _kapu(hook, cmd) == 0, cmd


def test_a_heredoc_UTAN_kovetkezo_valodi_parancs_blokkol() -> None:
    """A törzs kihagyása ne nyelje el a heredoc utáni parancsot."""
    cmd = "cat > /tmp/d.md <<'EOF'\nszöveg\nEOF\n" + _JEGY + ' "Hiba"'
    assert _kapu("jegycim_or.py", cmd) == 2


def test_a_VEGREHAJTO_heredoc_torzse_parancs_marad() -> None:
    """⛔ A legfontosabb kontroll: a `bash <<EOF` a törzsét FUTTATJA.

    Ha a törzset ott is kihagynánk, a heredoc kapumegkerülő alak lenne —
    egy sor beszúrásával bármelyik kapu megkerülhető volna."""
    cmd = "cd ~/Documents/PicasaPy && bash <<'EOF'\n" + _PUSH + "\nEOF\n"
    assert _kapu("push_azonossag_kapu.py", cmd) == 2


def test_a_sorok_szama_nem_valtozik() -> None:
    """A törzs üres sorokra cserélődik, nem törlődik.

    Az útvonal- és sor-alapú leletek így érvényben maradnak."""
    kozos = _kozos()
    cmd = "cat > /tmp/d.md <<'EOF'\na\nb\nc\nEOF\nls"
    assert len(kozos.adat_nelkul(cmd).split("\n")) == len(cmd.split("\n"))


def test_a_valodi_elkovetok_tovabbra_is_fogva() -> None:
    """Regresszió-kontroll: a két kapu eredeti foga megmaradt."""
    assert _kapu("jegycim_or.py",
                 "cd ~/picasapy-agent && eszkozok/" + _JEGY
                 + ' "P0: kesz"') == 2
    assert _kapu("push_azonossag_kapu.py",
                 "cd ~/Documents/PicasaPy && " + _PUSH) == 2

# ---------------------------------------------------------------- #3313

#: A projekt szabálya szerint hosszú szöveget (commit-üzenet, jegytörzs,
#: PR-leírás) MINDIG fájlból vagy szabvány bemenetről adunk át. A
#: leggyakoribb alak a `git commit -F - <<EOF`. A #3295 zárt listája ezt
#: nem tartalmazta, tehát a kapu épp az ELŐÍRT alakot tiltotta.
#:
#: ⚠️ Az alábbi első eset a MÉRT, valódi alak: a hivatkozás hátsó
#: idézőjelben (backtick) áll, és a parancspozíció-minta a backtick utáni
#: kezdetet is annak veszi. Ez akasztotta meg a #96 commit-üzenetét.
STDIN_UZENET = [
    ("release_kapu.py",
     "cd ~/picasapy-agent && git commit -q -F - <<'MSG'\n"
     "fix(hermes): a profil kötelességet is kap\n\n"
     "Mérve: a `hermes-bot " + _KIADAS + "` alak eddig ÁTMENT.\n"
     "MSG\n"),
    ("release_kapu.py",
     "gh-bot issue comment 5 --body-file - <<'EOF'\ngh-bot "
     + _KIADAS + "\nEOF\n"),
    ("push_azonossag_kapu.py",
     "cd ~/Documents/PicasaPy && git commit -q -F - <<'EOF'\nfix: x\n\n"
     "Tilos: " + _PUSH + "\nEOF\n"),
    ("jegycim_or.py",
     "git commit -q --file=- <<'EOF'\nfix: x\n\nPélda: " + _JEGY
     + ' "Hiba"\nEOF\n'),
]


@pytest.mark.parametrize("hook,cmd", STDIN_UZENET)
def test_a_stdin_uzenet_heredocja_adat(hook: str, cmd: str) -> None:
    """A `-F -` / `--body-file -` törzse üzenet, nem parancs."""
    assert _kapu(hook, cmd) == 0, cmd


def test_a_stdin_alak_nem_nyitja_meg_a_listat() -> None:
    """⛔ A legfontosabb kontroll: az ÉRTELMEZŐ törzse parancs marad.

    Ha a `-F -` jelenléte önmagában adattá tenné az egészet, egy
    `bash <<EOF` + egy odaírt `-F -` bármelyik kaput megkerülné."""
    cmd = ("cd ~/Documents/PicasaPy && bash <<'EOF'\n" + _PUSH + "\nEOF\n")
    assert _kapu("push_azonossag_kapu.py", cmd) == 2
