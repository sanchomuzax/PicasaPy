#!/usr/bin/env python3
"""Kiadás-kapu — Claude Code PreToolUse hook.

Blokkolja a visszavonhatatlan kiadási lépéseket, hogy sub-agent vagy
elhamarkodott session ne adhasson ki verziót a kiadási ceremónia
(review -> zöld CI -> integrátor) előtt.

Két kiadási út van, mindkettőt őrizzük:

1. KÖZVETLEN: `gh release create`, címke létrehozása, címke pusholása.
2. KÖZVETETT (nálunk ez a valódi út): a `pyproject.toml` verziószámának
   emelése a main-re kerül, és a release.yml automatikája hozza létre a
   címkét és a kiadást. 2026-08-19-ig ez az út őrizetlen volt — négy kiadás
   ment ki mellette úgy, hogy a kapu semmit nem látott.

Minden hibaágon átenged (fail-open): egy elromlott kapu nem foghatja meg a
párhuzamos sessionök normál munkáját. A feloldó jelölőt szándékosan NEM ez a
fájl dokumentálja: a privát picasapy-agent repó munkafolyamat-lapján van.
"""

import json
import os
import re
import subprocess
import sys

FELOLDO = "PICASA_KIADAS=engedelyezve"

# --- git tag: a létrehozás kiadási lépés, a listázás/törlés nem ------------
_TAG_LETREHOZO = {"-a", "--annotate", "-s", "--sign", "-m", "--message",
                  "-F", "--file", "-f", "--force", "-u", "--local-user"}
_TAG_OLVASO = {"-l", "--list", "-n", "--sort", "--format", "--contains",
               "--no-contains", "--points-at", "--merged", "--no-merged",
               "--column", "--no-column", "-i", "--ignore-case", "--color",
               "-d", "--delete", "-v", "--verify", "--omit-empty"}

# Parancspozíció: sor eleje vagy shell-elválasztó után, opcionális
# környezeti értékadásokkal. Enélkül a kapu a parancs SZÖVEGÉBEN előforduló
# említést is blokkolja (pl. amikor épp ezt a fájlt írjuk) — 2026-08-19-ig
# ez is megtörtént.
_POZICIO = r"(?:^|[;&|]\s*|\n\s*|\$\(\s*|`\s*)(?:\w+=\S*\s+)*"

_VERZIO_SOR = re.compile(r"^[+-]\s*version\s*=", re.MULTILINE)

# A hook a MUNKAMENET mappáját kapja meg, nem azt, ahová a parancs belép.
# Nálunk viszont minden munka külön munkamásolatban folyik, `cd <út> && ...`
# alakban — enélkül a verzióemelés-őr a főmappában nézne diffet, ahol nincs
# eltérés, és NÉMÁN átengedne minden kiadást. Éles próbán bukott meg
# (2026-08-19): a verzióemelő push simán átment.
_CD = re.compile(r"(?:^|[;&|]\s*)cd\s+(?P<ut>'[^']*'|\"[^\"]*\"|[^\s;&|]+)")


def _munkakonyvtar(cmd: str, cwd: str) -> str:
    """A parancs TÉNYLEGES munkakönyvtára: az utolsó `cd` célja, ha van."""
    utolso = None
    for m in _CD.finditer(cmd):
        utolso = m.group("ut").strip("'\"")
    if not utolso:
        return cwd
    ut = utolso if os.path.isabs(utolso) else os.path.join(cwd, utolso)
    ut = os.path.expanduser(ut)
    return ut if os.path.isdir(ut) else cwd


def _parancsok(cmd: str, program: str, alparancs: str) -> list[str]:
    """A `program alparancs ...` előfordulásai PARANCSPOZÍCIÓBAN, a maradékkal."""
    minta = _POZICIO + re.escape(program) + r"\s+" + alparancs + r"\b(.*)"
    return [m.group(1) for m in re.finditer(minta, cmd)]


def _tag_letrehozas(cmd: str) -> bool:
    for maradek in _parancsok(cmd, "git", "tag"):
        tokenek = re.split(r"[|;&]", maradek)[0].split()
        kapcsolok = {t.split("=", 1)[0] for t in tokenek if t.startswith("-")}
        if kapcsolok & _TAG_LETREHOZO:
            return True
        if kapcsolok & _TAG_OLVASO:
            continue
        if any(not t.startswith("-") for t in tokenek):
            return True  # `git tag NEV`
    return False


def _tag_push(cmd: str) -> bool:
    minta = re.compile(r"(--tags\b|--follow-tags\b|refs/tags/|\sv\d+[.\w]*(\s|$))")
    return any(minta.search(re.split(r"[|;&]", m)[0])
               for m in _parancsok(cmd, "git", "push"))


def _verziot_emel(cwd: str) -> bool:
    """A pushra váró ág emeli-e a pyproject verziószámát az origin/main-hez képest."""
    try:
        diff = subprocess.run(
            ["git", "diff", "origin/main...HEAD", "--", "pyproject.toml"],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
        ).stdout
    except Exception:
        return False
    return bool(_VERZIO_SOR.search(diff))


def _pr_verziot_emel(cmd: str, cwd: str) -> bool:
    """A beolvasztandó PR emeli-e a verziószámot (a merge maga a kiadás)."""
    szam = None
    for maradek in _parancsok(cmd, "gh", "pr\\s+merge"):
        m = re.search(r"\b(\d+)\b", maradek)
        if m:
            szam = m.group(1)
    if szam is None:
        return False
    try:
        diff = subprocess.run(
            ["gh", "pr", "diff", szam], cwd=cwd,
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        ).stdout
    except Exception:
        return False
    reszek = diff.split("diff --git ")
    return any("pyproject.toml" in r.split("\n", 1)[0] and _VERZIO_SOR.search(r)
               for r in reszek)


def _vizsgalt_fa(cwd: str) -> str:
    """A vizsgált munkamásolat és ága — a blokkoló üzenetbe (#1113).

    ⚠️ Enélkül a legdrágább fals riasztásunk vakon hagy: a kapu a
    MUNKAMENET cwd-jében diffel, ami `cd` nélküli parancsnál a KÖZÖS
    főmásolat — nem a pusholó session worktree-je. Ha a főmásolat épp
    verzióemelő ágon áll, a kapu MINDEN session pushát blokkolja, és az
    üzenet olyan ágról szól, amihez a blokkolt félnek semmi köze.

    2026-08-20-án egy munkamenet ezért futott neki négyszer a SAJÁT ágának,
    ami végig üres volt. Egy sor megadta volna a választ."""
    try:
        ag = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=10,
        ).stdout.strip()
    except Exception:
        ag = "?"
    return f"a vizsgált fa: {cwd}   ág: {ag or '?'}"


def _blokkolando(cmd: str, cwd: str) -> str | None:
    """A parancs kiadási lépés-e; ha igen, rövid indok, ha nem, None."""
    if FELOLDO in cmd:
        return None
    if _parancsok(cmd, "gh", "release\\s+(?:create|edit|upload)"):
        return "GitHub release létrehozása/módosítása"
    if _tag_letrehozas(cmd):
        return "git tag létrehozása"
    if _tag_push(cmd):
        return "tag push (kiadás publikálása)"
    if _parancsok(cmd, "git", "push") and _verziot_emel(cwd):
        return ("verzióemelést tartalmazó push — a main-re érve a release.yml "
                "AUTOMATIKUSAN kiadást csinál belőle")
    if _pr_verziot_emel(cmd, cwd):
        return ("verzióemelő PR beolvasztása — a main-re érve a release.yml "
                "AUTOMATIKUSAN kiadást csinál belőle")
    return None


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
        cwd = adat.get("cwd") or os.getcwd()
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    fa = _munkakonyvtar(cmd, cwd)
    try:
        indok = _blokkolando(cmd, fa)
    except Exception:
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkát
    if indok is None:
        return 0
    sys.stderr.write(
        "[Kiadás-kapu] BLOKKOLVA: " + indok + ".\n"
        + _vizsgalt_fa(fa) + "\n"
        "⚠️ Ha ez NEM a te munkamásolatod: a kapu a munkamenet cwd-jében\n"
        "néz diffet, ami `cd` nélküli parancsnál a KÖZÖS főmásolat. Ha az\n"
        "épp verzióemelő ágon áll, a kapu a TE pushodat is blokkolja (#1113).\n"
        "Ilyenkor NE a feloldó jelölőt keresd: szólj az integrátornak, hogy\n"
        "tegye vissza a főmásolatot `main`-re.\n"
        "A kiadás visszavonhatatlan, ezért csak az integrátor session adhatja\n"
        "ki, a teljes ceremónia után (code review -> zöld CI -> éles próba).\n"
        "Ha sub-agent vagy: ÁLLJ LE, és jelentsd a hívónak, hogy a munkád\n"
        "kiadásra kész — a kiadásról a hívó dönt.\n"
        "Ha integrátor vagy és a ceremónia megvolt: a feloldó jelölő a privát\n"
        "picasapy-agent repó memory/munkafolyamat.md kiadási szakaszában van.\n"
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
