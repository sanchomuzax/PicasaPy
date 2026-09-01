#!/usr/bin/env python3
"""Takarító: munkamásolatok és `/tmp`-maradékok — JELENT, és csak kérésre töröl.

## A hibaosztály (#1867)

A projektnek VAN takarítási szabálya, és a körök be is tartják — **amíg
eljutnak a végéig**. A szemetet a **félbeszakadt** munkamenetek hagyják:
azok soha nem érnek a takarító lépéshez. Ezért kell olyan mechanizmus,
ami nem a kör jószándékára épül.

Egyetlen éjszaka mérlege (2026-08-31 → 09-01): **4,6 GB** maradék és
**17** fölösleges munkamásolat; a `/tmp` 82%-ra telt, és a tulajdonos
rendszerszintű riasztást kapott. ⚠️ A kár **nem annál jelentkezik, aki
csinálja**: a megtelt `/tmp` a többi, EGYIDEJŰLEG futó munkamenetet
buktatja meg, félrevezető `ENOSPC`-vel.

## Három szabály, amit MÉRÉS kényszerített ki

**1. A beolvadást a PR-állapot mondja meg, nem a git.** Az összevont
(squash) beolvasztás új commitot készít, ezért a `git branch --merged` és
a `git merge-base --is-ancestor` az eredeti ágat NEM látja beolvadtnak.
Mérve (2026-09-01): **20 ágból 20 hamis negatív**, pedig 17 már bent volt.
Erre alapozva a takarító semmit nem törölne — a hiba a csendes irányba
téved, tehát észrevétlen marad.

**2. Idegen munkamenet fáját SOHA nem töröljük.** A takarító kizárólag a
SAJÁT azonosítója alatti `scratchpad`-et viheti el; minden mást
**legfeljebb jelent**, a tulajdonos azonosítójával és a korral. Ez sem
elvi finomkodás: ma éjjel egy kör három könyvtárat útvonal-forma alapján
sorolt egy másikhoz — tévesen. Ugyanez a tévedés két irányba mehet, és a
két irány nem egyformán súlyos:

* szigorú minta ⇒ ugyanaz a könyvtár MINDENKI szemszögéből idegen ⇒
  soha senki nem viszi el (csendes szivárgás — bosszantó, de javítható);
* megengedő minta ⇒ bárki elviheti bárkiét, **akár élő munkát is**
  (visszafordíthatatlan).

**3. Az „él-e még" kérdést a `/proc` dönti el, nem a kor.** A kor csak a
VÉGSŐ háló. Egy futó folyamat munkakönyvtára vagy nyitott leírója
elárulja, hogy a könyvtár HASZNÁLATBAN van — akkor is, ha épp régi.

## Használat

    python3 scripts/takarito.py             # csak JELENT (alapértelmezés)
    python3 scripts/takarito.py --torol     # a jelentett tételek elvitele
    python3 scripts/takarito.py --ora 12 --nap 3
"""

from __future__ import annotations

import argparse
import json
import re
import os
import shutil
import subprocess
import sys
import time
from dataclasses import dataclass
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent

#: A `run_tests.py` basetempjeinek előtagja a `/tmp` alatt.
TESZT_ELOTAG = "picasapy-tests-"

#: Ennyi óra után számít árvának egy basetemp, ha nem használja folyamat.
ALAP_ORA = 6

#: Ennyi nap után számít halottnak egy munkamenet-scratchpad.
ALAP_NAP = 2

#: Ez alatt nem soroljuk tételesen a csak-jelentett maradékot.
JELENTESI_KUSZOB = 5_000_000

#: A `/tmp` telítettségének figyelmeztetési küszöbe százalékban.
TMP_KUSZOB = 70

#: A munkamenet-könyvtár neve UUID. Enélkül a `claude-1000` alatti EGYÉB
#: könyvtárak is scratchpadnek látszanának — az első futásom a
#: `bundled-skills/2.1.227`-et is felkínálta törlésre, ami a KÉSZLET, nem
#: maradék. A minta szűkítése nem óvatoskodás: a takarító `--torol`
#: módban kérdés nélkül dolgozik.
_UUID = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
)


@dataclass(frozen=True)
class Tetel:
    """Egy takarítható (vagy csak jelentendő) tétel."""

    ut: Path
    fajta: str          # "munkamasolat" | "basetemp" | "scratchpad"
    indok: str
    meret: int
    elvihetjuk: bool    # False = csak jelentjük (idegen vagy élő)


# --- „használja-e valaki" -------------------------------------------------


def folyamat_hasznalja(ut: Path) -> bool:
    """Van-e futó folyamat, amelynek a munkakönyvtára vagy nyitott
    leírója az `ut` alatt van?

    A `/proc`-ot olvassuk, nem `lsof`-ot: a `lsof +D` REKURZÍVAN bejárja a
    célt, ami hálózati megosztáson önmagában is drága (a projekt egy
    korábbi köre ebbe futott bele). Itt csak szimbolikus linkeket
    olvasunk, bejárás nélkül.
    """
    proc = Path("/proc")
    if not proc.is_dir():
        return False   # nem Linux — a kor marad az egyetlen jel
    cel = str(ut.resolve())
    sajat = str(os.getpid())
    for pid_konyvtar in proc.iterdir():
        if not pid_konyvtar.name.isdigit() or pid_konyvtar.name == sajat:
            continue
        for jelolt in (pid_konyvtar / "cwd", *_leirok(pid_konyvtar)):
            try:
                cel_ut = os.readlink(jelolt)
            except OSError:
                continue
            if cel_ut == cel or cel_ut.startswith(cel + os.sep):
                return True
    return False


def _leirok(pid_konyvtar: Path):
    try:
        return list((pid_konyvtar / "fd").iterdir())
    except OSError:
        return []


# --- méret / kor ----------------------------------------------------------


def meret(ut: Path) -> int:
    """A fa mérete bájtban; olvashatatlan bejegyzést kihagy."""
    osszeg = 0
    for p in ut.rglob("*"):
        try:
            if p.is_file() and not p.is_symlink():
                osszeg += p.stat().st_size
        except OSError:
            continue
    return osszeg


def kor_masodperc(ut: Path, most: float) -> float:
    try:
        return most - ut.stat().st_mtime
    except OSError:
        return 0.0


# --- 1. munkamásolatok ----------------------------------------------------


def pr_allapot(ag: str) -> str | None:
    """A `gh` szerinti PR-állapot (`MERGED` / `CLOSED` / `OPEN`), vagy None.

    ⚠️ SZÁNDÉKOSAN nem `git branch --merged`: az összevont beolvasztás
    mellett 20/20 hamis negatívot adott (#1867). A None (nincs PR, vagy a
    `gh` nem elérhető) itt „NEM tudjuk" — ilyenkor a munkamásolat MARAD.
    """
    try:
        ki = subprocess.run(
            ["gh", "pr", "list", "--head", ag, "--state", "all",
             "--json", "state", "--limit", "1"],
            capture_output=True, text=True, timeout=30, cwd=REPO,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if ki.returncode != 0:
        return None
    try:
        sorok = json.loads(ki.stdout or "[]")
    except json.JSONDecodeError:
        return None
    return sorok[0]["state"] if sorok else None


def munkamasolatok(*, allapot=pr_allapot) -> list[Tetel]:
    """A befejezett PR-hez tartozó git-munkamásolatok."""
    try:
        ki = subprocess.run(
            ["git", "worktree", "list", "--porcelain"],
            capture_output=True, text=True, timeout=30, cwd=REPO, check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    talalt: list[Tetel] = []
    ut: Path | None = None
    elso = True
    for sor in ki.stdout.splitlines():
        if sor.startswith("worktree "):
            ut = Path(sor.split(" ", 1)[1])
        elif sor.startswith("branch ") and ut is not None:
            ag = sor.split(" ", 1)[1].removeprefix("refs/heads/")
            # ⚠️ A `git worktree list` ELSŐ tétele MINDIG a fő munkamásolat.
            # Ezt sosem szabad elvinni — az első futásomon a fő checkout
            # (6,3 GB) jelent meg „elvihető" tételként, mert éppen egy
            # beolvadt ágon állt. `--torol` mellett ez a projekt egészét
            # vitte volna el. A `REPO` erre NEM elég: ha a takarító egy
            # munkamásolatból fut, a `REPO` a munkamásolat.
            if elso:
                elso = False
            elif ut.resolve() != REPO.resolve():
                a = allapot(ag)
                if a in ("MERGED", "CLOSED"):
                    # Idegen munkamenet scratchpadje alatti munkamásolatot
                    # CSAK jelentünk: a fa a másiké, akkor is, ha az ág
                    # beolvadt (#1867).
                    enyem = not _idegen_scratchpadben(ut)
                    talalt.append(Tetel(
                        ut, "munkamasolat",
                        f"a PR-je {a} ({ag})" + ("" if enyem else " — de IDEGEN fában"),
                        meret(ut), enyem,
                    ))
            ut = None
    return talalt


def _idegen_scratchpadben(ut: Path) -> bool:
    """Más munkamenet scratchpadje alatt van-e az útvonal?"""
    sajat = sajat_munkamenet()
    reszek = ut.resolve().parts
    for i, resz in enumerate(reszek):
        if _UUID.match(resz) and "claude-1000" in reszek[:i]:
            return resz != sajat
    return False


# --- 2. basetempek --------------------------------------------------------


def basetempek(most: float, ora: int, *, hasznalja=folyamat_hasznalja) -> list[Tetel]:
    """Árva `run_tests.py`-basetempek a `/tmp` alatt."""
    talalt = []
    for p in sorted(Path("/tmp").glob(TESZT_ELOTAG + "*")):
        if not p.is_dir():
            continue
        oraban = kor_masodperc(p, most) / 3600
        if hasznalja(p):
            talalt.append(Tetel(p, "basetemp", "HASZNÁLJA egy futó folyamat",
                                meret(p), False))
        elif oraban >= ora:
            talalt.append(Tetel(p, "basetemp", f"{oraban:.1f} óra régi, nem használja senki",
                                meret(p), True))
    return talalt


# --- 3. scratchpadek ------------------------------------------------------


def sajat_munkamenet() -> str | None:
    """A saját munkamenet azonosítója a scratchpad útvonalából."""
    scratch = os.environ.get("CLAUDE_SCRATCHPAD") or os.environ.get("SCRATCH")
    if scratch:
        return Path(scratch).parent.name
    return None


def scratchpadek(most: float, nap: int, sajat: str | None,
                 *, hasznalja=folyamat_hasznalja) -> list[Tetel]:
    """Halott munkamenetek scratchpadjei.

    ⚠️ Csak a SAJÁT azonosító alattit jelöljük elvihetőnek. Idegen
    munkamenet fáját akkor sem töröljük, ha minden jel halottnak mutatja
    — a tévedés ott visszafordíthatatlan (#1867).
    """
    gyoker = Path("/tmp/claude-1000")
    if not gyoker.is_dir():
        return []
    talalt = []
    for projekt in sorted(gyoker.iterdir()):
        if not projekt.is_dir():
            continue
        for munkamenet in sorted(projekt.iterdir()):
            if not munkamenet.is_dir() or not _UUID.match(munkamenet.name):
                continue
            napban = kor_masodperc(munkamenet, most) / 86400
            if napban < nap or hasznalja(munkamenet):
                continue
            enyem = sajat is not None and munkamenet.name == sajat
            talalt.append(Tetel(
                munkamenet, "scratchpad",
                f"{napban:.1f} nap régi, munkamenet: {munkamenet.name}",
                meret(munkamenet), enyem,
            ))
    return talalt


# --- jelentés / törlés ----------------------------------------------------


def tmp_szazalek() -> int:
    try:
        st = os.statvfs("/tmp")
    except OSError:
        return 0
    osszes = st.f_blocks * st.f_frsize
    szabad = st.f_bavail * st.f_frsize
    return 0 if osszes == 0 else round((osszes - szabad) * 100 / osszes)


def torol(tetel: Tetel) -> bool:
    """Egy tétel elvitele. Munkamásolatnál `git worktree remove` —
    `rm -rf`-fel a git nyilvántartása elárvulna."""
    if not tetel.elvihetjuk:
        return False
    if tetel.fajta == "munkamasolat":
        vissza = subprocess.run(
            ["git", "worktree", "remove", str(tetel.ut), "--force"],
            capture_output=True, text=True, cwd=REPO,
        )
        if vissza.returncode != 0:
            return False
        subprocess.run(["git", "worktree", "prune"], capture_output=True, cwd=REPO)
        return True
    shutil.rmtree(tetel.ut, ignore_errors=True)
    return not tetel.ut.exists()


def _mb(bajt: int) -> str:
    return f"{bajt / 1e6:8.0f} MB"


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description="Takarító (#1867)")
    ertelmezo.add_argument("--torol", action="store_true",
                           help="a jelentett, elvihető tételek törlése")
    ertelmezo.add_argument("--ora", type=int, default=ALAP_ORA)
    ertelmezo.add_argument("--nap", type=int, default=ALAP_NAP)
    args = ertelmezo.parse_args(argv)

    most = time.time()
    tetelek = (munkamasolatok()
               + basetempek(most, args.ora)
               + scratchpadek(most, args.nap, sajat_munkamenet()))

    szazalek = tmp_szazalek()
    if szazalek >= TMP_KUSZOB:
        print(f"⚠️  A /tmp {szazalek}%-on áll (küszöb: {TMP_KUSZOB}%).")

    if not tetelek:
        print(f"Nincs takarítanivaló. (/tmp: {szazalek}%)")
        return 0

    elvihetok = [t for t in tetelek if t.elvihetjuk]
    jelentendok = [t for t in tetelek if not t.elvihetjuk]

    if elvihetok:
        print(f"ELVIHETŐ ({len(elvihetok)}):")
        for t in elvihetok:
            print(f"  {_mb(t.meret)}  {t.fajta:13} {t.ut}  — {t.indok}")
    # A jelentésnek OLVASHATÓNAK kell lennie: az első futásom 180 tételt
    # írt ki, szinte mind 0 MB — abban az érdemi sor elveszik. Csak az
    # érdemi méretűeket soroljuk, a többit egy sorban összegezzük.
    erdemi = [t for t in jelentendok if t.meret >= JELENTESI_KUSZOB]
    aprok = [t for t in jelentendok if t.meret < JELENTESI_KUSZOB]
    if erdemi:
        print(f"\nCSAK JELENTVE — nem a mienk vagy használatban ({len(erdemi)}):")
        for t in sorted(erdemi, key=lambda t: -t.meret):
            print(f"  {_mb(t.meret)}  {t.fajta:13} {t.ut}  — {t.indok}")
    if aprok:
        print(f"\n(+{len(aprok)} apró maradék {JELENTESI_KUSZOB / 1e6:.0f} MB alatt, "
              f"összesen {sum(t.meret for t in aprok) / 1e6:.0f} MB — nem soroljuk)")

    print(f"\nösszesen elvihető: {sum(t.meret for t in elvihetok) / 1e9:.2f} GB")
    if not args.torol:
        print("(csak jelentés — a törléshez: --torol)")
        return 0

    sikeres = sum(1 for t in elvihetok if torol(t))
    print(f"törölve: {sikeres}/{len(elvihetok)}   /tmp most: {tmp_szazalek()}%")
    return 0


if __name__ == "__main__":
    sys.exit(main())
