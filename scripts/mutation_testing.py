#!/usr/bin/env python3
"""Éjszakai, szűk hatókörű mutációs mérés (#6587)."""

from __future__ import annotations

import argparse
import ast
import difflib
import importlib.metadata
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import time
import tomllib
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_SCRATCH = _ROOT / ".tmp" / "picasapy-mutmut"
_PROJECT = _SCRATCH / "project"
_REPORT = _SCRATCH / "report.md"
_TARGETS = {"ini", "render"}
_IGNORE_NAMES = {
    ".git", ".tmp", ".bt", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "__pycache__", "build", "dist",
}
_NAS_UT = re.compile(r"/mnt/|nas", re.IGNORECASE)
_MUTANT_SORSZAM = re.compile(r"__mutmut_\d+$")

# A mutmut 3.5 exitkódjai. A pontszám a kért „megölt / összes”; az időtúllépés
# és a teszt nélküli mutáns külön státusz, nem számít megölt mutánsnak.
_STATUS = {
    0: "túlélte",
    1: "megölte a teszt",
    2: "megszakadt",
    3: "megölte a teszt",
    5: "nincs teszt",
    24: "időtúllépés",
    33: "nincs teszt",
    34: "kihagyta az eszköz",
    35: "gyanús eredmény",
    36: "időtúllépés",
    37: "típusellenőrző elkapta",
    152: "időtúllépés",
    255: "időtúllépés",
    -9: "szegmentációs hiba",
    -11: "szegmentációs hiba",
    -24: "időtúllépés",
}


def _kihagyando(_konyvtar: str, nevek: list[str]) -> set[str]:
    return {nev for nev in nevek if nev in _IGNORE_NAMES}


def _masolat_fajl(forras: Path, cel: Path) -> None:
    cel.parent.mkdir(parents=True, exist_ok=True)
    if forras.is_symlink():
        cel.symlink_to(os.readlink(forras))
    else:
        shutil.copy2(forras, cel)


def _frissit_masolat() -> None:
    """A projekt forrásmásolatát frissíti, a mutmut `mutants/` cache-ét hagyja."""
    _SCRATCH.mkdir(parents=True, exist_ok=True)
    _PROJECT.mkdir(parents=True, exist_ok=True)
    for forras in _ROOT.iterdir():
        if forras.name in _IGNORE_NAMES or forras.name == "mutants":
            continue
        cel = _PROJECT / forras.name
        if cel.is_dir() and not cel.is_symlink():
            shutil.rmtree(cel)
        elif cel.exists() or cel.is_symlink():
            cel.unlink()
        if forras.is_dir() and not forras.is_symlink():
            shutil.copytree(
                forras, cel, symlinks=True, ignore=_kihagyando,
            )
        else:
            _masolat_fajl(forras, cel)


def _nas_testfajlok(gyoker: Path) -> list[str]:
    """A NAS-útvonalat tartalmazó céltesztfájlokat futtatás előtt kizárja."""
    kihagyas: list[str] = []
    for csomag in sorted(_TARGETS):
        tesztgyoker = gyoker / "tests" / csomag
        if not tesztgyoker.is_dir():
            continue
        for fajl in sorted(tesztgyoker.rglob("test_*.py")):
            if _NAS_UT.search(fajl.read_text(encoding="utf-8", errors="replace")):
                kihagyas.append(fajl.relative_to(gyoker).as_posix())
    return kihagyas


def _pytest_kivalasztas_frissitese() -> list[str]:
    pyproject = _PROJECT / "pyproject.toml"
    szoveg = pyproject.read_text(encoding="utf-8")
    beallitas = tomllib.loads(szoveg).get("tool", {}).get("mutmut", {})
    vart = ["src/picasapy/ini", "src/picasapy/render"]
    if beallitas.get("paths_to_mutate") != vart:
        raise ValueError(f"A mutmut forráshatókör eltér a kértől: {beallitas.get('paths_to_mutate')}")

    kizart = _nas_testfajlok(_PROJECT)
    args = ["tests/ini", "tests/render", *(f"--ignore={ut}" for ut in kizart)]
    sor = re.compile(
        r"(?m)^pytest_add_cli_args_test_selection\s*=\s*\[[^\]]*\]"
    )
    uj = "pytest_add_cli_args_test_selection = " + json.dumps(args, ensure_ascii=False)
    friss, darab = sor.subn(uj, szoveg, count=1)
    if darab != 1:
        raise ValueError("A pyproject.toml nem tartalmazza a mutmut pytest-kiválasztását.")
    pyproject.write_text(friss, encoding="utf-8")
    return kizart


def _mutmut_tamogato_forrasok() -> None:
    """A nem célzott modulokat a mutmut importútvonalába másolja.

    A mutmut csak a két kijelölt könyvtárat másolja a `mutants/` alá. A
    csomag `__init__.py`-je és a tesztek által használt szomszédos modulok is
    kellenek ahhoz, hogy a mutált csomag valóban importálódjon.
    """
    forras = _PROJECT / "src" / "picasapy"
    cel = _PROJECT / "mutants" / "src" / "picasapy"
    cel.mkdir(parents=True, exist_ok=True)
    for elem in forras.iterdir():
        if elem.name in _TARGETS:
            continue
        cel_elem = cel / elem.name
        if cel_elem.is_dir() and not cel_elem.is_symlink():
            shutil.rmtree(cel_elem)
        elif cel_elem.exists() or cel_elem.is_symlink():
            cel_elem.unlink()
        if elem.is_dir() and not elem.is_symlink():
            shutil.copytree(elem, cel_elem, symlinks=True)
        else:
            _masolat_fajl(elem, cel_elem)


def _folyamatfa_rss(pid_gyoker: int) -> int | None:
    """A mutmut-folyamat és leszármazottai RSS-ét összegzi Linuxon."""
    proc = Path("/proc")
    if not proc.is_dir():
        return None
    adatok: dict[int, tuple[int, int]] = {}
    try:
        bejegyzesek = list(os.scandir(proc))
    except OSError:
        return None
    lap = os.sysconf("SC_PAGE_SIZE")
    for bejegyzes in bejegyzesek:
        if not bejegyzes.name.isdecimal():
            continue
        pid = int(bejegyzes.name)
        try:
            stat = Path(bejegyzes.path, "stat").read_text(encoding="ascii")
            mezok = stat.rsplit(")", 1)[1].split()
            szulo = int(mezok[1])
            rss_oldal = int(
                Path(bejegyzes.path, "statm").read_text(encoding="ascii").split()[1]
            )
        except (OSError, ValueError, IndexError):
            continue
        adatok[pid] = (szulo, rss_oldal * lap)
    if pid_gyoker not in adatok:
        return None
    utodok = {pid_gyoker}
    valtozott = True
    while valtozott:
        valtozott = False
        for pid, (szulo, _rss) in adatok.items():
            if szulo in utodok and pid not in utodok:
                utodok.add(pid)
                valtozott = True
    return sum(adatok[pid][1] for pid in utodok if pid in adatok)


def _futtat_meressel(parancs: list[str], kornyezet: dict[str, str]) -> tuple[int, float, int | None]:
    kezdet = time.monotonic()
    csucs = 0
    folyamat = subprocess.Popen(
        parancs, cwd=_PROJECT, env=kornyezet, start_new_session=True,
    )
    megszakadt = False
    try:
        while folyamat.poll() is None:
            mert = _folyamatfa_rss(folyamat.pid)
            if mert is not None:
                csucs = max(csucs, mert)
            time.sleep(0.1)
    except KeyboardInterrupt:
        megszakadt = True
        try:
            os.killpg(folyamat.pid, signal.SIGINT)
            folyamat.wait(timeout=10)
        except (ProcessLookupError, subprocess.TimeoutExpired):
            try:
                os.killpg(folyamat.pid, signal.SIGTERM)
            except ProcessLookupError:
                pass
            folyamat.wait()
    mert = _folyamatfa_rss(folyamat.pid)
    if mert is not None:
        csucs = max(csucs, mert)
    meres = time.monotonic() - kezdet
    return (130 if megszakadt else folyamat.returncode), meres, csucs or None


def _status(kod: int | None) -> str:
    return "nem futott le" if kod is None else _STATUS.get(kod, "gyanús eredmény")


def _mutansok(mutants: Path) -> list[dict[str, Any]]:
    eredmeny: list[dict[str, Any]] = []
    for meta_ut in sorted(mutants.glob("src/picasapy/**/*.py.meta")):
        forras_ut = meta_ut.relative_to(mutants).with_suffix("")
        reszek = forras_ut.parts
        if len(reszek) < 4 or reszek[2] not in _TARGETS:
            continue
        adat = json.loads(meta_ut.read_text(encoding="utf-8"))
        for nev, kod in adat.get("exit_code_by_key", {}).items():
            eredmeny.append({
                "csomag": reszek[2],
                "fajl": forras_ut.as_posix(),
                "nev": nev,
                "kod": kod,
                "status": _status(kod),
            })
    return eredmeny


def _fuggveny_sora(forras: str, mutans: str) -> int | None:
    fuggveny = _MUTANT_SORSZAM.sub("", mutans.rsplit(".", 1)[-1])
    try:
        fa = ast.parse(forras)
    except SyntaxError:
        return None
    talalat = next(
        (n.lineno for n in ast.walk(fa)
         if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == fuggveny),
        None,
    )
    return talalat


def _mutacio_sora(mutans: dict[str, Any], futtato: str, projekt: Path) -> int | None:
    fajl = projekt / "mutants" / mutans["fajl"]
    try:
        eredeti = fajl.read_text(encoding="utf-8")
        allapot = fajl.stat()
    except OSError:
        return None
    alkalmaz = subprocess.run(
        [futtato, "apply", mutans["nev"]], cwd=projekt,
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        check=False,
    )
    try:
        if alkalmaz.returncode != 0:
            return _fuggveny_sora(eredeti, mutans["nev"])
        valtozott = fajl.read_text(encoding="utf-8")
        regi_sorok = eredeti.splitlines()
        uj_sorok = valtozott.splitlines()
        for op, kezdet, _veg, _uj_kezdet, _uj_veg in difflib.SequenceMatcher(
            a=regi_sorok, b=uj_sorok, autojunk=False,
        ).get_opcodes():
            if op != "equal":
                return max(1, kezdet + 1)
        return _fuggveny_sora(eredeti, mutans["nev"])
    except OSError:
        return _fuggveny_sora(eredeti, mutans["nev"])
    finally:
        fajl.write_text(eredeti, encoding="utf-8")
        os.utime(fajl, ns=(allapot.st_atime_ns, allapot.st_mtime_ns))


def _osszefoglal(mutansok: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    csomagok: dict[str, dict[str, Any]] = {
        nev: {"ossz": 0, "megolt": 0, "tulelte": 0, "statuszok": Counter()}
        for nev in sorted(_TARGETS)
    }
    for mutans in mutansok:
        adat = csomagok[mutans["csomag"]]
        adat["ossz"] += 1
        adat["statuszok"][mutans["status"]] += 1
        if mutans["status"] == "megölte a teszt":
            adat["megolt"] += 1
        elif mutans["status"] == "túlélte":
            adat["tulelte"] += 1
    return csomagok


def _relacio_fajlok(projekt: Path) -> list[str]:
    """Kifejezett metamorf/relációjelölést keres; név alapján nem találgat."""
    jelolo = re.compile(r"pytest\.mark\.(?:metamorphic|metamorf|mutation_relation|mutacio_relacio)")
    talalatok: list[str] = []
    for csomag in sorted(_TARGETS):
        tesztgyoker = projekt / "tests" / csomag
        for fajl in sorted(tesztgyoker.rglob("test_*.py")):
            if jelolo.search(fajl.read_text(encoding="utf-8", errors="replace")):
                talalatok.append(fajl.relative_to(projekt).as_posix())
    return talalatok


def _jelentes(
    mutansok: list[dict[str, Any]],
    *,
    futasido: float,
    csucs_bajt: int | None,
    kizart_nas: list[str],
    teljes: bool,
    projekt: Path,
    mutmut_parancs: str,
) -> str:
    csomagok = _osszefoglal(mutansok)
    sorok = [
        "# Mutációs mérés — #6587",
        "",
        f"- Időpont: {datetime.now(UTC).isoformat(timespec='seconds')}",
        "- Eszköz: mutmut 3.5.0; mutánsonként egy worker.",
        f"- Állapot: {'teljes' if teljes else 'megszakadt vagy hibás'}.",
        f"- Futásidő: {futasido:.1f} s.",
        f"- Csúcsmemória: {csucs_bajt / (1024 * 1024):.1f} MiB."
        if csucs_bajt is not None else "- Csúcsmemória: nem mérhető `/proc` nélkül.",
        "",
        "## Pontszámok",
        "",
        "| Csomag | Megölt / összes | Pontszám | Túlélő |",
        "|---|---:|---:|---:|",
    ]
    for nev in sorted(_TARGETS):
        adat = csomagok[nev]
        pont = f"{adat['megolt'] / adat['ossz'] * 100:.1f}%" if adat["ossz"] else "n/a"
        sorok.append(
            f"| `{nev}/` | {adat['megolt']} / {adat['ossz']} | {pont} | {adat['tulelte']} |"
        )
        reszletek = ", ".join(
            f"{nev}: {db}" for nev, db in sorted(adat["statuszok"].items())
        ) or "nincs létrehozott mutáns"
        sorok.append(f"<!-- {nev} státuszok: {reszletek} -->")

    tulelok = [m for m in mutansok if m["status"] == "túlélte"]
    csoportok: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for mutans in tulelok:
        csoportok[mutans["fajl"]].append(mutans)
    sorok.extend(["", "## Túlélők, modulonként csoportosítva", ""])
    if not tulelok:
        sorok.append("Nincs túlélő mutáns a rögzített eredményekben.")
    for fajl, csoport in sorted(csoportok.items()):
        sorok.append(f"### `{fajl}` — {len(csoport)} túlélő")
        for mutans in sorted(csoport, key=lambda m: m["nev"]):
            line = _mutacio_sora(mutans, mutmut_parancs, projekt)
            hely = f"{fajl}:{line}" if line is not None else f"{fajl}:?"
            sorok.append(f"- `{hely}` — `{mutans['nev']}`")
        sorok.append("")

    sorok.extend(["## NAS-kizárások", ""])
    sorok.extend(f"- `{ut}`" for ut in kizart_nas)
    if not kizart_nas:
        sorok.append("Nem volt NAS-útvonalat tartalmazó céltesztfájl.")

    relaciok = _relacio_fajlok(projekt)
    sorok.extend(["", "## Metamorf relációk", ""])
    if relaciok:
        sorok.append(
            "Relációjelölést tartalmazó tesztfájlok: "
            + ", ".join(f"`{ut}`" for ut in relaciok)
            + ". A mutmut 3.5 nem rögzíti, melyik egyedi teszt bukott el mutánsonként; "
              "ezért a relációnkénti ölési számot ez az eredmény nem állítja elő."
        )
    else:
        sorok.append(
            "A célcsomagok tesztjeiben nincs kifejezett metamorf/relációjelölés; "
            "a #6586 relációnkénti ölési száma nem mérhető ezen a forrásállapoton."
        )
    sorok.extend([
        "",
        "## Csoportosított következő lépések",
        "",
        "A túlélők fájlonkénti csoportjai fent láthatók. Jegyazonosítót vagy "
        "egyenértékűmutáns-döntést a mérő nem talál ki; ezek kézi besorolásra várnak.",
        "",
        "A mutáns cache és ez a jelentés a munkafa `.tmp/picasapy-mutmut/` könyvtárában marad, "
        "így megszakítás után a `python scripts/run_tests.py --mutmut` folytatható.",
        "",
    ])
    return "\n".join(sorok)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args(argv)
    if os.name == "nt":
        print("A mutmut 3.5 Linux/WSL alatt fut; natív Windowson nem támogatott.", file=sys.stderr)
        return 2
    try:
        verzio = importlib.metadata.version("mutmut")
    except importlib.metadata.PackageNotFoundError:
        print("Hiányzik a mutmut; telepítsd a fejlesztői extra alapján.", file=sys.stderr)
        return 2
    if verzio != "3.5.0":
        print(f"Mutmut 3.5.0 szükséges, a talált verzió: {verzio}.", file=sys.stderr)
        return 2
    mutmut = shutil.which("mutmut")
    if mutmut is None:
        print("A mutmut 3.5.0 csomag megvan, de a `mutmut` parancs hiányzik.", file=sys.stderr)
        return 2

    _frissit_masolat()
    kizart_nas = _pytest_kivalasztas_frissitese()
    _mutmut_tamogato_forrasok()
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    print("Hatókör: src/picasapy/ini + tests/ini és src/picasapy/render + tests/render.")
    print("NAS-t tartalmazó tesztfájlok kizárva:", ", ".join(kizart_nas) or "nincs")
    parancs = [mutmut, "run", "--max-children", "1"]
    kod, futasido, csucs = _futtat_meressel(parancs, env)
    if kod == 130:
        mutansok = _mutansok(_PROJECT / "mutants")
        resz = _jelentes(
            mutansok, futasido=futasido, csucs_bajt=csucs,
            kizart_nas=kizart_nas, teljes=False, projekt=_PROJECT,
            mutmut_parancs=mutmut,
        )
        _REPORT.write_text(resz, encoding="utf-8")
        print(f"Megszakadt; folytatáshoz futtasd újra. Részjelentés: {_REPORT}")
        return 130

    if kod == 0:
        subprocess.run([mutmut, "export-cicd-stats"], cwd=_PROJECT, env=env, check=False)
    mutansok = _mutansok(_PROJECT / "mutants")
    jelentes = _jelentes(
        mutansok, futasido=futasido, csucs_bajt=csucs,
        kizart_nas=kizart_nas, teljes=kod == 0, projekt=_PROJECT,
        mutmut_parancs=mutmut,
    )
    _REPORT.write_text(jelentes, encoding="utf-8")
    print(jelentes)
    print(f"Jelentés mentve: {_REPORT}")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
