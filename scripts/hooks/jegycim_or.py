#!/usr/bin/env python3
"""Jegycím-őr — Claude Code PreToolUse hook (#1378).

## Miért

A jegy címe a **legtartósabb** szövegünk: bekerül a commit-üzenetbe, a
PR-címbe, a változásnaplóba és a keresésbe. Az állapot viszont a
**leghamarabb avuló** adat. A kettőt összekötni garantált elavulás — mérve:
a #1276 és a #1153 címében ott a „P1:", miközben a `P1` ÉS a `blocked`
címke is rajtuk van. Ha a blokk feloldódik, a címke változik, a cím tovább
kiabál.

A tulajdonos kérése (2026-08-24):

    „Ne odaírjuk bele, hogy P0, ne odaírjuk bele, hogy blokkolt…
     Alany-állítmány kell, hogy szerepeljen benne, valamiféle cél:
     honnan és hová tartunk? … a kapcsolódó funkció megnevezése sem
     maradjon ki, hiszen így sokkal könnyebb rákeresni később."

## A kívánt alak

    [érintett funkció] + alany + állítmány, és látszódjon a honnan-hová

    Hiba:        „A Klipek fül a kollázs csomópontjait sorolja fel a mappa
                  képei helyett"
    Fejlesztés:  „Az Exportálás mappába párbeszéd az eredeti Picasa
                  elrendezését követi"

## Amit ez az őr NEM csinál

Nem nyelvtant ellenőriz. Csak a **mechanikusan biztosat** blokkolja
(prioritás-jelölés, állapot-előtag, commit-előtag, nyomatékszó, semmitmondó
rövidség); az alany-állítmányt és a funkciónevet a hibaüzenet KÉRI, nem
méri. A téves blokk drágább, mint egy gyengébb cím: aki nem tud jegyet
nyitni, az nem jegyez fel semmit.

⚠️ A PR-címekhez NEM nyúl: ott a `fix:`/`feat:` előtag a projekt
konvenciója. Kizárólag `gh issue create` és `gh issue edit --title`.

Minden hibaágon átenged (fail-open): egy elromlott kapu nem foghatja meg a
párhuzamos munkameneteket.
"""

import json
import re
import shlex
import sys

#: Parancspozíció: sor eleje vagy shell-elválasztó után. Enélkül a parancs
#: SZÖVEGÉBEN előforduló említés is kiváltaná a kaput — ez a hibaosztály a
#: kiadás-kaput élesben megvezette (2026-08-19).
_POZICIO = r"(?:^|[;&|]\s*|\n\s*|\$\(\s*|`\s*)(?:\w+=\S*\s+)*"

#: Prioritás-jelölés: `P0`–`P4` önálló szóként. Prózában gyakorlatilag nem
#: fordul elő, címkeként viszont létezik — oda való.
_PRIORITAS = re.compile(r"\bP[0-4]\b")

#: Állapot ELŐTAGKÉNT: „BLOKKOLT: …", „[blocked] …". Csak a cím elején
#: fogjuk meg, mert a „blokkol" IGE jogos címszó (#1056: „a kiadás-kapu jó
#: szándékú munkát is blokkol").
_ALLAPOT_SZO = (
    r"(?:blokkolt|blocked|in-progress|ready|folyamatban|kész|done|"
    r"sürgős|surgos|kritikus|urgent|asap)"
)
#: Szögletes/kerek zárójelben elválasztó sem kell — a `[blocked] …` alak
#: önmagában is állapot-előtag.
_ALLAPOT_ELOTAG = re.compile(
    rf"^\s*(?:[\[(]\s*{_ALLAPOT_SZO}\s*[\])]|{_ALLAPOT_SZO}\s*[:\-–—])",
    re.IGNORECASE,
)

#: Ezek soha nem prózai szavak egy címben.
_MUNKAJELOLO = re.compile(r"\b(WIP|TODO|FIXME|XXX)\b")

#: A conventional-commit előtag a COMMITÉ és a PR-é, nem a jegyé.
_COMMIT_ELOTAG = re.compile(
    r"^\s*(fix|feat|chore|docs|test|refactor|perf|ci|build|style)"
    r"(\([^)]*\))?\s*:",
    re.IGNORECASE,
)

#: Nagybetűs NYOMATÉK — burkolt prioritás. Szándékosan zárt lista: a
#: csupa nagybetűs NÉV (pl. a „KLIPEK" fül) megkülönböztetés, nem nyomaték,
#: és azt átengedjük.
_NYOMATEK = re.compile(
    r"\b(KRITIKUS|SÜRGŐS|SURGOS|FONTOS|AZONNAL|URGENT|ASAP|SOHA|MINDIG|"
    r"MUSZÁJ|KÖTELEZŐ|NEM)\b"
)

#: Ennél kevesebb szóból nem lesz kereshető, leíró cím („Hisztogram").
_MIN_SZO = 4


def _jegycimek(cmd: str) -> list[str]:
    """A parancsban szereplő JEGY-címek (`gh issue create/edit --title`).

    A `gh pr create --title` szándékosan kimarad: ott más a konvenció."""
    cimek: list[str] = []
    minta = _POZICIO + r"gh\s+issue\s+(?:create|edit)\b(.*)"
    for talalat in re.finditer(minta, cmd):
        maradek = re.split(r"[|;&]", talalat.group(1))[0]
        try:
            tokenek = shlex.split(maradek)
        except ValueError:
            continue
        for i, token in enumerate(tokenek):
            if token == "--title" and i + 1 < len(tokenek):
                cimek.append(tokenek[i + 1])
            elif token.startswith("--title="):
                cimek.append(token.split("=", 1)[1])
    return cimek


def _kifogas(cim: str) -> str | None:
    """Mi a baj a címmel? `None`, ha átmehet."""
    if _PRIORITAS.search(cim):
        return "prioritás-jelölés van benne (P0–P4)"
    if _ALLAPOT_ELOTAG.search(cim):
        return "állapottal kezdődik (blokkolt/kész/sürgős…)"
    if _MUNKAJELOLO.search(cim):
        return "munkajelölőt tartalmaz (WIP/TODO/FIXME)"
    if _COMMIT_ELOTAG.search(cim):
        return "commit-előtaggal kezdődik (fix:/feat:…) — az a commité, nem a jegyé"
    if _NYOMATEK.search(cim):
        return "csupa nagybetűs nyomatékot tartalmaz — az burkolt prioritás"
    if len(cim.split()) < _MIN_SZO:
        return f"túl rövid ({len(cim.split())} szó) — így nem kereshető és nem leíró"
    return None


def _blokkolando(cmd: str) -> tuple[str, str] | None:
    for cim in _jegycimek(cmd):
        kifogas = _kifogas(cim)
        if kifogas is not None:
            return cim, kifogas
    return None


_SEGITSEG = """
A jegy címe a legtartósabb szövegünk: commit-üzenetbe, PR-címbe,
változásnaplóba és keresésbe kerül. Az állapot a leghamarabb avuló adat —
és VAN rá címke: P0–P4, blocked, in-progress, ready, felhasználóra-vár.
Tedd oda; a cím maradjon leíró.

A kívánt alak — [érintett funkció] + alany + állítmány, honnan-hová:

  Hiba:        „A Klipek fül a kollázs csomópontjait sorolja fel a mappa
                képei helyett"
  Fejlesztés:  „Az Exportálás mappába párbeszéd az eredeti Picasa
                elrendezését követi"

A funkció megnevezése nem díszítés: enélkül a jegy fél év múlva
kereshetetlen — senki nem a számára emlékszik, hanem a „kollázs" szóra
keres rá. A MEGOLDÁS viszont ne legyen benne: az is vélemény, ami munka
közben változik.
"""


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    try:
        talalat = _blokkolando(cmd)
    except Exception:
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkát
    if talalat is None:
        return 0
    cim, kifogas = talalat
    sys.stderr.write(
        f"[Jegycím-őr] BLOKKOLVA: {kifogas}.\n"
        f"A cím: {cim!r}\n"
        + _SEGITSEG
    )
    return 2


if __name__ == "__main__":  # pragma: no cover
    sys.exit(main())
