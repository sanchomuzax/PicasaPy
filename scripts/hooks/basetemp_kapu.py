#!/usr/bin/env python3
"""Basetemp-kapu — Claude Code PreToolUse hook (#1649).

**A hibaosztály.** A `PROTOKOLL.md` kimondja, hogy a tesztfuttató a
`scripts/run_tests.py`, vagy fájlonkénti futtatásnál KÖZÖS `--basetemp` kell
(a pytest a „tartsd meg az utolsó hármat" takarítást basetemp-enként végzi,
tehát minden külön basetemp hagy maga után egy könyvtárat).

Ez a szabály **le volt írva, és mégis megsérült**: 2026-08-15-én öt párhuzamos
kör csupasz `python3 -m pytest`-tel **5,8 GB**-ot hagyott a `pytest-of-sancho`
alatt, és a 8 GB-os tmpfs 85%-ra telt. A kár nem a vétkes körnél jelentkezik,
hanem a **párhuzamosan futó** munkameneteknél, némán, félrevezető `ENOSPC`-vel.

**Miért hook, és nem több szöveg.** Mert a szöveget már kipróbáltuk. A
`release_kapu.py` ugyanezt a mintát követi, és bevált: a kiadás-tilalom azért
nem jelenik meg az agent-briefekben, mert **nem is kell** — ki van véve a
promptból, kódba.

**Vaklárma-osztályok, amiket a `release_kapu` élesben tanult (2026-08-19), és
itt előre kivédünk:**

1. a parancs SZÖVEGÉBEN előforduló említés (`grep`, fájlírás) nem blokkolhat —
   ezért az idézett szakaszokat kivágjuk az elemzés előtt;
2. a listázó/segítség-alakok nem hoznak létre tmpdir-t (`--help`, `--version`,
   `--collect-only`), tehát átmennek.

**A második hibaosztály — MAPPÁRA indított `tests/app` (#2558).** A
`run_tests.py` az `app`-teszteket SZÁNDÉKOSAN fájlonként, külön processzben
futtatja: „mindegyik KÜLÖN processzben, hogy egy fájlon belüli sok
engine-életciklus se torlódjon egyetlen processzbe". Egy mappára indított
csupasz `pytest tests/app/...` ezt megkerüli: az összes QML-motor egyetlen
processzben halmozódik.

MÉRVE (2026-09-06, ez a gép): `pytest tests/app/qml_functional -q` egyetlen
processze 12:28-kor 446 MiB-ról 12:32-re **3,18 GiB**-ra hízott, a 2 GiB
swap teljesen betelt, a terhelés 5-ről **105**-re ment, és a tulajdonosnak
**újra kellett indítania a gépet**. A közös `--basetemp` megvolt — az a
kapu ezt az alakot nem fogta meg.

**A harmadik hibaosztály — MEMÓRIAPLAFON nélküli app-teszt (#2646).** A
fenti kettő a LEMEZT és a mappa-alakot védi; a RAM-ot semmi. 2026-09-07
08:48-kor az `earlyoom` a Claude Desktop rendererét lőtte ki (VmRSS 3579 MiB)
egy 1031 MiB-os QML-teszt helyett — az earlyoom a LEGNAGYOBB RSS-t öli, tehát
**az áldozat strukturálisan sosem a tettes**. A kiváltó egyetlen, önmagában
LEGITIM fájl volt (`tests/app/qml_functional/test_keptalca_455.py`), amely 30
másodperc alatt 898 → 1401 MiB-ra nőtt; három párhuzamos munkamenet vitte el
a gépet. Sem ez a kapu, sem a foglalási korlát (#2532) nem foghatta meg: az
egyik a mappa-alakot nézi, a másik csak a `run_tests.py` teljes futásait.

A javítás a jelentés szava szerint **plafon a forrásnál, nem utólagos
kilövés**: a `systemd-run --user --scope -p MemoryMax=…` cgroupba teszi a
futást, így a túllépő **egyedül** hal meg, determinisztikusan (mérve ezen a
gépen: 300 MiB-os plafonnál exit 137).

Minden hibaágon **fail-open**: egy elromlott kapu nem foghatja meg a
párhuzamos munkameneteket — épp azokat védené.
"""

from __future__ import annotations

import json
import re
import sys

#: Idézett szakaszok — ezeket kivágjuk, mielőtt parancsot keresnénk benne.
_IDEZET = re.compile(r"'[^']*'|\"[^\"]*\"")

#: Szakaszhatárok: külön parancsnak számít mindegyik oldal.
_HATAR = re.compile(r"&&|\|\||[;|]")

#: `VAR=ertek` alakú előtag a parancs elején.
_ERTEKADAS = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

#: Burkoló programok, amik után a VALÓDI parancs jön.
_BURKOLO = {"env", "nice", "xvfb-run", "stdbuf", "time"}

#: Python-értelmezők, amikkel a `-m pytest` alak indul.
_PYTHON = re.compile(r"^(.*/)?python[0-9.]*$")

#: Ezek az alakok nem hoznak létre ideiglenes könyvtárat.
_ARTALMATLAN_KAPCSOLO = {"-h", "--help", "--version", "--collect-only", "--co"}

#: #2558: az `app`-tesztek gyökere. Az ez alatti MAPPÁKAT csak a
#: `run_tests.py` indíthatja, mert az fájlonként, külön processzben futtat.
_APP_GYOKER = "tests/app"

#: Fájlnak számít, aminek `.py` a vége (a `::teszt` szűrő is ide tartozik).
_FAJL = re.compile(r"\.py(::|$)")

#: #2646: a memóriaplafon burkolója. Enélkül a `tests/app` alatti pytest —
#: akár EGYETLEN fájlra — a gépet viheti el, nem csak magát.
_PLAFON_JELE = "systemd-run"
_PLAFON_KAPCSOLO = "MemoryMax="


def _szakaszok(cmd: str) -> list[list[str]]:
    """A parancs szakaszai tokenekre bontva, idézetek nélkül."""
    tiszta = _IDEZET.sub(" ", cmd)
    return [r.split() for r in _HATAR.split(tiszta) if r.split()]


def _fej(tokenek: list[str]) -> list[str]:
    """A tokenlista az értékadások és burkolók levágása után."""
    i = 0
    while i < len(tokenek):
        t = tokenek[i]
        if _ERTEKADAS.match(t) or t in _BURKOLO:
            i += 1
            continue
        if t == "timeout":
            i += 1
            # a timeout első argumentuma az időkorlát (pl. `timeout 60 …`)
            if i < len(tokenek) and re.fullmatch(r"[0-9]+[smhd]?", tokenek[i]):
                i += 1
            continue
        if t == _PLAFON_JELE or t.endswith("/" + _PLAFON_JELE):
            # #2646: a plafon-burkoló saját kapcsolói után `--` jelzi a
            # VALÓDI parancsot. Enélkül a kapu a `systemd-run`-t látná
            # fejnek, nem ismerné fel a pytestet, és a `--basetemp`
            # ellenőrzés NÉMÁN kiesne — épp a plafont használó, jó
            # szándékú hívásokon.
            while i < len(tokenek) and tokenek[i] != "--":
                i += 1
            i += 1  # magát a `--`-t is átlépjük
            continue
        break
    return tokenek[i:]


def _pytest_hivas(tokenek: list[str]) -> bool:
    """Igaz, ha ez a szakasz TÉNYLEGESEN pytestet indít."""
    t = _fej(tokenek)
    if not t:
        return False
    fej = t[0]
    if fej == "pytest" or fej.endswith("/pytest"):
        return True
    # `python -m pytest …` — a `-m pytest` közvetlenül az értelmező után áll
    return bool(_PYTHON.match(fej)) and t[1:3] == ["-m", "pytest"]


def _app_mappa_cel(tokenek: list[str]) -> str | None:
    """A `tests/app` alatti MAPPÁRA mutató cél, ha van (#2558).

    Fájlra (`.py`, `.py::teszt`) mutató cél rendben van: az egy processz,
    egy fájl. A mappa viszont az egész készletet egy processzbe húzza."""
    for t in tokenek:
        if t.startswith("-"):
            continue
        cel = t.rstrip("/")
        if cel != _APP_GYOKER and not cel.startswith(_APP_GYOKER + "/"):
            continue
        if _FAJL.search(cel):
            continue
        return cel
    return None


def _app_cel(tokenek: list[str]) -> bool:
    """Igaz, ha a hívás a `tests/app` alá céloz (fájlra vagy mappára)."""
    return any(not t.startswith("-")
               and (t.rstrip("/") == _APP_GYOKER
                    or t.rstrip("/").startswith(_APP_GYOKER + "/"))
               for t in tokenek)


def _van_plafon(tokenek: list[str]) -> bool:
    """Igaz, ha a szakasz memóriaplafon alatt indítja a pytestet."""
    return (any(t == _PLAFON_JELE or t.endswith("/" + _PLAFON_JELE)
                for t in tokenek)
            and any(_PLAFON_KAPCSOLO in t for t in tokenek))


def blokkolando(cmd: str) -> str | None:
    """Az indok, ha a parancsot blokkolni kell — különben None."""
    for tokenek in _szakaszok(cmd):
        if not _pytest_hivas(tokenek):
            continue
        if any(k in _ARTALMATLAN_KAPCSOLO for k in tokenek):
            continue
        mappa = _app_mappa_cel(tokenek)
        if mappa is not None:
            return f"a `{mappa}` MAPPA egyetlen pytest-processzben"
        if not any(k == "--basetemp" or k.startswith("--basetemp=") for k in tokenek):
            return "pytest-hívás közös `--basetemp` nélkül"
        if _app_cel(tokenek) and not _van_plafon(tokenek):
            return "`tests/app` alatti pytest MEMÓRIAPLAFON nélkül"
    return None


def main() -> int:
    try:
        adat = json.load(sys.stdin)
        cmd = (adat.get("tool_input") or {}).get("command") or ""
    except Exception:
        return 0  # fail-open: rossz bemenet nem blokkolhat
    try:
        indok = blokkolando(cmd)
    except Exception:
        return 0  # fail-open: elromlott kapu nem akaszthat meg munkát
    if indok is None:
        return 0
    sys.stderr.write(
        "[Basetemp-kapu] BLOKKOLVA: " + indok + ".\n"
        "\n"
        "Használd a projekt futtatóját:\n"
        "    python scripts/run_tests.py\n"
        "\n"
        "Vagy futtass FÁJLONKÉNT, közös basetemppel:\n"
        "    BT=\"$SCRATCH/bt\"; mkdir -p \"$BT\"\n"
        "    python3 -m pytest <egy fájl>.py -q --basetemp=\"$BT\"\n"
        "\n"
        "Miért a MAPPA tilos (#2558): a `run_tests.py` az app-teszteket\n"
        "szándékosan fájlonként, KÜLÖN processzben futtatja, hogy a sok\n"
        "QML-motor életciklusa ne torlódjon egyetlen processzbe. Mappára\n"
        "indítva 2026-09-06-án egyetlen pytest-processz négy perc alatt\n"
        "446 MiB-ról 3,18 GiB-ra hízott, a swap betelt, a terhelés 105-re\n"
        "ment, és a gépet ÚJRA KELLETT INDÍTANI.\n"
        "\n"
        "Miért a közös basetemp (#1649): a pytest a „tartsd meg az utolsó\n"
        "hármat\" takarítást basetemp-enként végzi. 2026-08-15-én öt\n"
        "párhuzamos kör így 5,8 GB-ot hagyott a tmpfs-en.\n"
        "\n"
        "Miért a MEMÓRIAPLAFON (#2646): 2026-09-07 08:48-kor az earlyoom a\n"
        "Claude Desktop rendererét lőtte ki (3579 MiB) egy 1031 MiB-os\n"
        "QML-teszt HELYETT — az earlyoom a legnagyobb RSS-t öli, tehát az\n"
        "áldozat sosem a tettes. A kiváltó EGYETLEN fájl volt, ami 30\n"
        "másodperc alatt 898-ról 1401 MiB-ra nőtt.\n"
        "\n"
        "Plafon alatt így indítsd (a túllépő EGYEDÜL hal meg, exit 137):\n"
        "    systemd-run --user --scope -q \\\n"
        "        -p MemoryMax=2400M -p MemorySwapMax=0 -- \\\n"
        "        python3 -m pytest <egy fájl>.py -q --basetemp=\"$BT\"\n"
        "\n"
        "A kár egyik esetben sem NÁLAD jelentkezik, hanem a gépen és a\n"
        "párhuzamos munkameneteknél — ezért kapu ez, és nem ajánlás.\n"
    )
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
