#!/usr/bin/env python3
"""Szövegőr — Claude Code PostToolUse hook, a PR megnyitása után.

Miért: a tesztek a viselkedést őrzik, a magyar szöveg helyességét semmi.
Bizonyítottan ment ki zöld teszt mellett "Többválaszás", "Modellek fülöt" és
spanyol szó magyar mondatban. Ez a hook a commitban hozzáadott, felhasználónak
látszó magyar szövegeket egy olcsó nyelvi körrel átolvastatja (sonnet — a
Haiku nyelvi munkára bizonyítottan alkalmatlan).

Nem blokkol soha (mindig 0-val lép ki): a lelet tanács, a session dönt.
Ha nincs magyar szöveg a commitban (a commitok többsége), <1 mp alatt kilép.
Vészkapcsoló: PICASA_SZOVEGOR=ki környezeti változóval kikapcsolható.
"""

import json
import os
import re
import subprocess
import sys

EKEZET = re.compile(r"[áéíóöőúüűÁÉÍÓÖŐÚÜŰ]")
IDEZETT = re.compile(r'"([^"\\]{2,})"' + r"|'([^'\\]{2,})'")
TRANSLATION = re.compile(r"<(?:translation|source)[^>]*>([^<]+)<")
MAX_SOR = 80
CLAUDE_IDOKERET_S = 150


def _futtat(args: list[str], cwd: str) -> str:
    return subprocess.run(
        args, cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30
    ).stdout


def _magyar_szovegek(cwd: str, tartomany: str) -> list[str]:
    """A tartományban hozzáadott, felhasználónak látszó magyar szövegek."""
    diff = _futtat(
        ["git", "diff", "--unified=0", tartomany, "--", "*.ts", "*.qml"],
        cwd,
    )
    talalatok: list[str] = []
    for sor in diff.splitlines():
        if not sor.startswith("+") or sor.startswith("+++"):
            continue
        tartalom = sor[1:]
        jeloltek = [m.group(1) for m in TRANSLATION.finditer(tartalom)]
        # kommentek levágása, hogy a magyar kódkomment ne riasszon
        kod = re.split(r"(?://|#)", tartalom, maxsplit=1)[0]
        jeloltek += [a or b for a, b in IDEZETT.findall(kod)]
        talalatok += [j.strip() for j in jeloltek if EKEZET.search(j)]
    # dedup, sorrendtartóan
    return list(dict.fromkeys(t for t in talalatok if t))


def main() -> int:
    if os.environ.get("PICASA_SZOVEGOR") == "ki":
        return 0
    try:
        adat = json.load(sys.stdin)
    except Exception:
        return 0
    cmd = (adat.get("tool_input") or {}).get("command") or ""
    # A PR NYITÁSA a helyes pillanat: a commitonkénti futás 16 óra alatt 11
    # magyar szöveget hozó commitból egyet sem látott (a munka külön
    # munkamásolatokban folyik). A széles hálót a CI-ellenőrzés adja
    # (scripts/nyelvi_ellenorzes.py); ez itt a mély, modell-alapú kör, ami a
    # helyesírás-ellenőrzőnek láthatatlan nyelvtani hibákat is megfogja.
    if "gh pr create" not in cmd:
        return 0
    cwd = adat.get("cwd") or os.getcwd()
    try:
        gitdir = _futtat(["git", "rev-parse", "--git-dir"], cwd).strip()
        fej = _futtat(["git", "rev-parse", "HEAD"], cwd).strip()
        tartomany = "origin/main...HEAD"
        if not gitdir or not fej:
            return 0
        allapot = os.path.join(cwd, gitdir, "szovegor-utolso")
        try:
            if open(allapot, encoding="utf-8").read().strip() == fej:
                return 0  # ezt a commitot már néztük
        except OSError:
            pass
        with open(allapot, "w", encoding="utf-8") as f:
            f.write(fej)  # előre írjuk, hogy hibázó kör se ismételjen
        szovegek = _magyar_szovegek(cwd, tartomany)[:MAX_SOR]
        if not szovegek:
            return 0
        prompt = (
            "Magyar nyelvű asztali fotókezelő most megnyitott PR-jének "
            "felületi szövegei. KIZÁRÓLAG magyar nyelvhelyességet ellenőrizz: "
            "helyesírás, hangrendi illeszkedés (pl. toldalékok), nem létező "
            "szóalak, magyar mondatba tévedt idegen szó, értelemzavaró elütés. "
            "Stílust, terminológiát, kódot NE véleményezz. Ha minden rendben, "
            "válaszod pontosan ennyi legyen: RENDBEN. Ha hibát találsz, "
            "hibánként egy sor: a hibás alak -> a helyes alak (rövid indok). "
            "A szövegek:\n" + "\n".join("- " + s for s in szovegek)
        )
        valasz = subprocess.run(
            ["claude", "-p", "--model", "sonnet", prompt],
            capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=CLAUDE_IDOKERET_S,
        ).stdout.strip()
        if valasz and valasz != "RENDBEN":
            sys.stderr.write(
                "[Szövegőr] A PR magyar szövegeiben nyelvi hiba gyanúja van "
                "(HEAD: " + fej[:10] + "):\n" + valasz + "\n"
                "[Szövegőr] Ha valós, javítsd még ebben a körben — a zöld "
                "teszt a szöveg helyességéről semmit nem mond.\n"
            )
        elif valasz == "RENDBEN":
            sys.stderr.write("[Szövegőr] Magyar szövegek ellenőrizve: rendben.\n")
    except Exception:
        return 0  # fail-open: a szövegőr sosem akaszthatja meg a munkát
    return 0


if __name__ == "__main__":
    sys.exit(main())
