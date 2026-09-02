"""A napi súgófrissítő őrei — #2051.

A tervezet három ponton tért el a valóságtól, és mindhárom NÉMÁN bukott volna:

* `--max-turns` — ilyen kapcsoló nincs a telepített Claude Code-ban, a futás
  azonnal elszállt volna;
* `python -m picasapy --help` — a PicasaPy GUI, nincs parancssori felülete,
  tehát a súgóba kitalált parancsok kerültek volna;
* a fő checkoutban dolgozó `git checkout main` — ebből a repóból párhuzamos
  sessionök dolgoznak, egy éjszakai ágváltás elvinné a munkájukat.

Ezek az őrök azt védik, hogy a három hiba ne kúszhasson vissza.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

GYOKER = Path(__file__).resolve().parents[1]
SZKRIPT = GYOKER / "scripts" / "update_help.sh"
PROMPT = GYOKER / ".claude" / "prompts" / "update-help.md"
ENGEDELYEK = GYOKER / ".claude" / "help-agent-settings.json"


def _kod(ut: Path) -> str:
    """A fájl tartalma KOMMENTEK NÉLKÜL.

    A kommentek szándékosan leírják, mit NEM szabad használni (pl. hogy nincs
    `--max-turns`); ha az őr a nyers szöveget nézné, a saját magyarázatunkon
    bukna el.
    """
    sorok = [s for s in ut.read_text(encoding="utf-8").splitlines()
             if not s.lstrip().startswith("#")]
    return "\n".join(sorok)


def test_a_szkript_letezik_es_futtathato():
    assert SZKRIPT.is_file()
    assert SZKRIPT.stat().st_mode & 0o111, "nem futtatható"


def test_a_szkript_szintaktikailag_helyes():
    kesz = subprocess.run(["bash", "-n", str(SZKRIPT)], capture_output=True, text=True)
    assert kesz.returncode == 0, kesz.stderr


def test_nem_hasznal_nem_letezo_claude_kapcsolot():
    """A telepített Claude Code-ban nincs `--max-turns`; a keret dollárban megy."""
    kod = _kod(SZKRIPT)
    assert "--max-turns" not in kod
    assert "--max-budget-usd" in kod


def test_nem_a_kozos_checkoutban_dolgozik():
    """Párhuzamos sessionök: a fő checkoutban tilos ágat váltani."""
    kod = _kod(SZKRIPT)
    assert "flock" in kod, "hiányzik a párhuzamos futás elleni zár"
    assert 'cd "$MUNKAFA"' in kod, "nem a saját munkafájába lép be"
    assert not re.search(r'cd\s+"\$FO_CHECKOUT"', kod), "belépne a közös checkoutba"


def test_a_kizarolista_lefedi_a_fejlesztoi_mappakat():
    """Ami nem a felhasználónak szól, az ne indítson súgófrissítést."""
    kod = _kod(SZKRIPT)
    valodi_mappak = {p.name for p in GYOKER.iterdir()
                     if p.is_dir() and not p.name.startswith(".")}
    fejlesztoi = {"tests", "research", "tools", "scripts", "packaging"} & valodi_mappak
    hianyzo = [m for m in fejlesztoi if f"':!{m}'" not in kod]
    assert not hianyzo, f"nincs kizárva: {hianyzo}"


def test_a_prompt_nem_igert_nem_letezo_parancssort():
    """A PicasaPy-nak nincs CLI-je — a súgó ne hivatkozzon rá."""
    szoveg = PROMPT.read_text(encoding="utf-8")
    assert "python -m picasapy --help" not in szoveg.replace("`", "")
    assert "NINCS parancssori felülete" in szoveg


def test_a_prompt_eloirja_a_nyitott_kerdesek_fajlt():
    szoveg = PROMPT.read_text(encoding="utf-8")
    assert ".open-questions.md" in szoveg


def test_az_engedelyek_nem_engedik_a_kodot_irni():
    adat = json.loads(ENGEDELYEK.read_text(encoding="utf-8"))
    tilt = adat["permissions"]["deny"]
    for minta in ("Edit(src/**)", "Write(src/**)", "Bash(git push:*)"):
        assert minta in tilt, f"hiányzó tiltás: {minta}"
    enged = adat["permissions"]["allow"]
    assert not any(e.startswith(("Edit(src", "Write(src")) for e in enged)


def test_a_prompt_tiltja_az_eredeti_sugo_atmasolasat():
    """A `research/original-user-guides/` a Google anyaga — témalista, nem szöveg."""
    szoveg = PROMPT.read_text(encoding="utf-8")
    assert "research/original-user-guides/" in szoveg
    assert "SZERZŐI JOG" in szoveg
    assert "Egyetlen mondatot se másolj" in szoveg
