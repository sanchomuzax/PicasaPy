#!/usr/bin/env python3
"""Éjszakai, szűk hatókörű mutációs mérés (#6587).

Helyi ismétlés a futtató egyidejűségi kapuján át:

    python scripts/run_tests.py --mutmut --mutmut-package=ini
    python scripts/run_tests.py --mutmut --mutmut-package=render-sample

A render-minta kizárólag a `flip.py` modult méri; nem render-csomagpontszám.
"""

from __future__ import annotations

import argparse
import ast
import difflib
import importlib
import importlib.metadata
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import textwrap
import time
import tomllib
from collections import Counter, defaultdict
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[1]
_PYTHON_EXECUTABLE = sys.executable
_MUTMUT_PATH_LOOKUP = shutil.which
_SCRATCH = _ROOT / ".tmp" / "picasapy-mutmut"
_PROJECT = _SCRATCH / "project"
_REPORT = _SCRATCH / "report.md"
_TARGETS = {"ini", "render"}
_RENDER_SAMPLE_SOURCE = "src/picasapy/render/flip.py"
_RENDER_SAMPLE_TEST = "tests/render/test_flip_2902.py"
_MUTMUT_MAX_GYERMEK = 2
_IGNORE_NAMES = {
    ".git", ".tmp", ".bt", ".pytest_cache", ".ruff_cache", ".mypy_cache",
    ".venv", "venv", "__pycache__", "build", "dist",
}
_NAS_UT = re.compile(r"/mnt/|nas", re.IGNORECASE)
_MUTANT_SORSZAM = re.compile(r"__mutmut_\d+$")
_SOURCE_ROOT_PARTS = {"src", "picasapy"}
_MUTATED_PACKAGE_PARTS = {"ini", "render"}
_SOURCE_READ_CALLS = {"open", "read_text", "read_bytes", "glob", "rglob", "run"}

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


def _celteszt_fajlok(
    gyoker: Path,
    csomagok: set[str],
    kivalasztottak: list[str] | None = None,
) -> list[Path]:
    if kivalasztottak is not None:
        return [gyoker / ut for ut in kivalasztottak if (gyoker / ut).is_file()]
    return [
        fajl
        for csomag in sorted(csomagok)
        for fajl in sorted((gyoker / "tests" / csomag).rglob("test_*.py"))
    ]


def _nas_testfajlok(
    gyoker: Path,
    csomagok: set[str] | None = None,
    kivalasztottak: list[str] | None = None,
) -> list[str]:
    """A NAS-útvonalat tartalmazó céltesztfájlokat futtatás előtt kizárja."""
    kihagyas: list[str] = []
    for fajl in _celteszt_fajlok(gyoker, set(csomagok or _TARGETS), kivalasztottak):
        if _NAS_UT.search(fajl.read_text(encoding="utf-8", errors="replace")):
            kihagyas.append(fajl.relative_to(gyoker).as_posix())
    return kihagyas


def _hivasok_nevei(node: ast.AST) -> set[str]:
    nevek: set[str] = set()
    for elem in ast.walk(node):
        if not isinstance(elem, ast.Call):
            continue
        cel = elem.func
        if isinstance(cel, ast.Name):
            nevek.add(cel.id)
        elif isinstance(cel, ast.Attribute):
            nevek.add(cel.attr)
    return nevek


def _nevek(node: ast.AST) -> set[str]:
    return {elem.id for elem in ast.walk(node) if isinstance(elem, ast.Name)}


def _szovegek(node: ast.AST) -> set[str]:
    return {
        elem.value.replace("\\", "/")
        for elem in ast.walk(node)
        if isinstance(elem, ast.Constant) and isinstance(elem.value, str)
    }


def _forrasgyoker_kifejezes(node: ast.AST) -> bool:
    szovegek = _szovegek(node)
    for ut in szovegek:
        normalizalt = ut.strip("/")
        darabok = set(normalizalt.split("/"))
        if _SOURCE_ROOT_PARTS <= darabok and _MUTATED_PACKAGE_PARTS & darabok:
            return True
    return _SOURCE_ROOT_PARTS <= szovegek and bool(_MUTATED_PACKAGE_PARTS & szovegek)


def _forrasut_valtozonevek(statements: list[ast.stmt]) -> set[str]:
    valtozonevek: set[str] = set()
    for statement in statements:
        if isinstance(statement, (ast.Assign, ast.AnnAssign)):
            ertek = statement.value
            if ertek is None or not _forrasgyoker_kifejezes(ertek):
                continue
            celok = statement.targets if isinstance(statement, ast.Assign) else [statement.target]
            for cel in celok:
                valtozonevek.update(_nevek(cel))
    return valtozonevek


def _forrasolvaso_fuggveny(
    node: ast.FunctionDef | ast.AsyncFunctionDef,
    modul_forras_nevek: set[str],
) -> bool:
    """Igaz, ha a függvény forráskódot olvas, nem a termék viselkedését méri."""
    hivasok = _hivasok_nevei(node)
    if "getsource" in hivasok:
        return True

    forras_nevek = modul_forras_nevek | _forrasut_valtozonevek(node.body)
    if not forras_nevek and not _forrasgyoker_kifejezes(node):
        return False

    hivasutak = {
        elem.attr
        for elem in ast.walk(node)
        if isinstance(elem, ast.Attribute)
    }
    fajlolvasonak_latszik = bool(hivasok & _SOURCE_READ_CALLS) or "__file__" in hivasutak
    return fajlolvasonak_latszik and (
        bool(_nevek(node) & forras_nevek)
        or _forrasgyoker_kifejezes(node)
        or "__file__" in hivasutak
    )


def _teszt_nodeok(
    fa: ast.Module,
) -> tuple[
    dict[str, ast.FunctionDef | ast.AsyncFunctionDef],
    list[tuple[list[str], ast.FunctionDef | ast.AsyncFunctionDef]],
]:
    fuggvenyek: dict[str, ast.FunctionDef | ast.AsyncFunctionDef] = {}
    tesztek: list[tuple[list[str], ast.FunctionDef | ast.AsyncFunctionDef]] = []
    feldolgozando = [(fa.body, [])]
    while feldolgozando:
        body, osztalyok = feldolgozando.pop()
        for elem in body:
            if isinstance(elem, ast.ClassDef):
                feldolgozando.append((elem.body, [*osztalyok, elem.name]))
            elif isinstance(elem, (ast.FunctionDef, ast.AsyncFunctionDef)):
                fuggvenyek[elem.name] = elem
                if elem.name.startswith("test_"):
                    tesztek.append(([*osztalyok, elem.name], elem))
    return fuggvenyek, tesztek


def _forrasolvaso_tesztazonositok(
    gyoker: Path,
    csomagok: set[str] | None = None,
    kivalasztottak: list[str] | None = None,
) -> list[str]:
    """A mutált `src/picasapy`-t vizsgáló őrteszteket nodeid szinten azonosítja."""
    kizart: list[str] = []
    for fajl in _celteszt_fajlok(gyoker, set(csomagok or _TARGETS), kivalasztottak):
        try:
            fa = ast.parse(fajl.read_text(encoding="utf-8"))
        except (OSError, SyntaxError, UnicodeError):
            continue

        modul_forras_nevek = _forrasut_valtozonevek(fa.body)
        fuggvenyek, tesztek = _teszt_nodeok(fa)
        forrasolvaso_nevek = {
            nev for nev, fuggveny in fuggvenyek.items()
            if _forrasolvaso_fuggveny(fuggveny, modul_forras_nevek)
        }
        valtozott = True
        while valtozott:
            valtozott = False
            for nev, fuggveny in fuggvenyek.items():
                if (
                    nev not in forrasolvaso_nevek
                    and _hivasok_nevei(fuggveny) & forrasolvaso_nevek
                ):
                    forrasolvaso_nevek.add(nev)
                    valtozott = True

        rel = fajl.relative_to(gyoker).as_posix()
        for utvonal, teszt in tesztek:
            if teszt.name in forrasolvaso_nevek:
                kizart.append(f"{rel}::" + "::".join(utvonal))
    return sorted(kizart)


def _toml_lista_csere(szoveg: str, kulcs: str, ertekek: list[str]) -> str:
    sor = re.compile(rf"(?m)^{re.escape(kulcs)}\s*=\s*\[[^\]]*\]")
    uj = f"{kulcs} = " + json.dumps(ertekek, ensure_ascii=False)
    szoveg, darab = sor.subn(uj, szoveg, count=1)
    if darab != 1:
        raise ValueError(f"A pyproject.toml nem tartalmazza a mutmut {kulcs} beállítását.")
    return szoveg


def _pytest_kivalasztas_frissitese(
    csomagok: set[str] | None = None,
    *,
    render_minta: bool = False,
) -> tuple[list[str], list[str]]:
    pyproject = _PROJECT / "pyproject.toml"
    szoveg = pyproject.read_text(encoding="utf-8")
    beallitas = tomllib.loads(szoveg).get("tool", {}).get("mutmut", {})
    csomagok = set(csomagok or _TARGETS)
    vart = [f"src/picasapy/{nev}" for nev in sorted(_TARGETS)]
    if beallitas.get("paths_to_mutate") != vart:
        raise ValueError(f"A mutmut forráshatókör eltér a kértől: {beallitas.get('paths_to_mutate')}")

    if not csomagok or not csomagok <= _TARGETS:
        raise ValueError(f"Érvénytelen mutációs csomaghatókör: {sorted(csomagok)}")
    if render_minta and csomagok != {"render"}:
        raise ValueError("A render-minta csak render csomaghatókörrel használható.")
    if render_minta:
        forrasutak = [_RENDER_SAMPLE_SOURCE]
        tesztargs = [_RENDER_SAMPLE_TEST]
        jelolt_tesztfajlok = tesztargs
    else:
        forrasutak = [f"src/picasapy/{nev}" for nev in sorted(csomagok)]
        tesztargs = [f"tests/{nev}" for nev in sorted(csomagok)]
        jelolt_tesztfajlok = None
    kizart_nas = _nas_testfajlok(_PROJECT, csomagok, jelolt_tesztfajlok)
    kizart_forras = _forrasolvaso_tesztazonositok(
        _PROJECT, csomagok, jelolt_tesztfajlok,
    )
    tesztargs.extend(f"--ignore={ut}" for ut in kizart_nas)
    tesztargs.extend(f"--deselect={nodeid}" for nodeid in kizart_forras)
    friss = _toml_lista_csere(szoveg, "paths_to_mutate", forrasutak)
    friss = _toml_lista_csere(friss, "pytest_add_cli_args_test_selection", tesztargs)
    pyproject.write_text(friss, encoding="utf-8")
    return kizart_nas, kizart_forras


def _mutmut_tamogato_forrasok(csomagok: set[str] | None = None) -> None:
    """A nem célzott modulokat a mutmut importútvonalába másolja.

    A mutmut csak a két kijelölt könyvtárat másolja a `mutants/` alá. A
    csomag `__init__.py`-je és a tesztek által használt szomszédos modulok is
    kellenek ahhoz, hogy a mutált csomag valóban importálódjon.
    """
    forras = _PROJECT / "src" / "picasapy"
    cel = _PROJECT / "mutants" / "src" / "picasapy"
    cel.mkdir(parents=True, exist_ok=True)
    for elem in forras.iterdir():
        if elem.name in (csomagok or _TARGETS):
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


def _mutmut_parancs(
    mutmut: str, mutant_nevek: list[str] | None = None
) -> list[str]:
    """A globális tesztkapu által engedett legfeljebb két gyermeket használja."""
    return [
        mutmut,
        "run",
        "--max-children",
        str(_MUTMUT_MAX_GYERMEK),
        *(mutant_nevek or []),
    ]


def _mutmut_futtathato() -> str | None:
    """Az aktív Python venv-jében keresi a mutmutot, majd a PATH-on."""
    venv_mutmut = Path(_PYTHON_EXECUTABLE).with_name("mutmut")
    if venv_mutmut.is_file():
        return str(venv_mutmut)
    return _MUTMUT_PATH_LOOKUP("mutmut")


def _mutansok(mutants: Path, csomagok: set[str] | None = None) -> list[dict[str, Any]]:
    eredmeny: list[dict[str, Any]] = []
    for meta_ut in sorted(mutants.glob("src/picasapy/**/*.py.meta")):
        forras_ut = meta_ut.relative_to(mutants).with_suffix("")
        reszek = forras_ut.parts
        if len(reszek) < 4 or reszek[2] not in (csomagok or _TARGETS):
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


def _elso_elteres_sora(eredeti: str, mutalt: str, kezdo_sor: int) -> int | None:
    """A függvénykódok diffjéből visszaadja az első módosított forrássort."""
    for muvelet, kezdet, _veg, _uj_kezdet, _uj_veg in difflib.SequenceMatcher(
        a=eredeti.splitlines(), b=mutalt.splitlines(), autojunk=False,
    ).get_opcodes():
        if muvelet != "equal":
            return max(1, kezdo_sor + kezdet)
    return None


def _fuggveny_node(
    fa: ast.Module, nev: str, osztalynev: str | None,
) -> ast.FunctionDef | ast.AsyncFunctionDef | None:
    if osztalynev is not None:
        osztaly = next(
            (node for node in ast.walk(fa) if isinstance(node, ast.ClassDef) and node.name == osztalynev),
            None,
        )
        if osztaly is None:
            return None
        return next(
            (node for node in osztaly.body
             if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == nev),
            None,
        )
    return next(
        (node for node in fa.body
         if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == nev),
        None,
    )


def _mutacio_sora(
    mutans: dict[str, Any],
    projekt: Path,
    mutmut_api: Any,
    forras_cache: dict[str, tuple[str, ast.Module]],
    mutans_cache: dict[str, Any],
) -> int | None:
    fajlnev = mutans["fajl"]
    forras = forras_cache.get(fajlnev)
    if forras is None:
        try:
            szoveg = (projekt / fajlnev).read_text(encoding="utf-8")
            fa = ast.parse(szoveg)
        except (OSError, SyntaxError):
            return None
        forras = (szoveg, fa)
        forras_cache[fajlnev] = forras

    szoveg, fa = forras
    mutant_modul = mutans_cache.get(fajlnev)
    if mutant_modul is None:
        mutant_fajl = projekt / "mutants" / fajlnev
        try:
            mutant_modul = mutmut_api.cst.parse_module(
                mutant_fajl.read_text(encoding="utf-8"),
            )
        except (OSError, SyntaxError):
            return None
        mutans_cache[fajlnev] = mutant_modul
    try:
        fuggvenynev, osztalynev = mutmut_api.orig_function_and_class_names_from_key(mutans["nev"])
        eredeti_node = _fuggveny_node(fa, fuggvenynev, osztalynev)
        mutalt_node = mutmut_api.read_mutant_function(mutant_modul, mutans["nev"])
        if eredeti_node is None:
            return None
        eredeti_kod = ast.get_source_segment(szoveg, eredeti_node)
        if eredeti_kod is None:
            return None
        dekorator_sorok = [dekorator.lineno for dekorator in eredeti_node.decorator_list]
        kezdo_sor = min([eredeti_node.lineno, *dekorator_sorok])
        mutalt_kod = mutmut_api.cst.Module([mutalt_node]).code
        return _elso_elteres_sora(
            textwrap.dedent(eredeti_kod),
            textwrap.dedent(mutalt_kod).strip("\n"),
            kezdo_sor,
        )
    except (AttributeError, IndexError, KeyError, TypeError, ValueError):
        return None


def _osszefoglal(
    mutansok: list[dict[str, Any]], csomagok: set[str] | None = None,
) -> dict[str, dict[str, Any]]:
    kivant_csomagok = csomagok or _TARGETS
    osszesito: dict[str, dict[str, Any]] = {
        nev: {"ossz": 0, "megolt": 0, "tulelte": 0, "statuszok": Counter()}
        for nev in sorted(kivant_csomagok)
    }
    for mutans in mutansok:
        adat = osszesito[mutans["csomag"]]
        adat["ossz"] += 1
        adat["statuszok"][mutans["status"]] += 1
        if mutans["status"] == "megölte a teszt":
            adat["megolt"] += 1
        elif mutans["status"] == "túlélte":
            adat["tulelte"] += 1
    return osszesito


def _relacio_fajlok(projekt: Path, csomagok: set[str] | None = None) -> list[str]:
    """Kifejezett metamorf/relációjelölést keres; név alapján nem találgat."""
    jelolo = re.compile(r"pytest\.mark\.(?:metamorphic|metamorf|mutation_relation|mutacio_relacio)")
    talalatok: list[str] = []
    for csomag in sorted(csomagok or _TARGETS):
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
    kizart_forras: list[str],
    csomagok: set[str],
    teljes: bool,
    projekt: Path,
    render_minta: bool = False,
) -> str:
    osszesites = _osszefoglal(mutansok, csomagok)
    sorok = [
        "# Mutációs mérés — #6587",
        "",
        f"- Időpont: {datetime.now(UTC).isoformat(timespec='seconds')}",
        f"- Eszköz: mutmut 3.5.0; legfeljebb {_MUTMUT_MAX_GYERMEK} párhuzamos gyermek.",
        (
            "- Mérési mód: egyetlen render-modul mintája (`flip.py`); "
            "nem teljes render-pontszám."
            if render_minta else "- Mérési mód: teljesen kiválasztott csomag(ok)."
        ),
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
    for nev in sorted(csomagok):
        adat = osszesites[nev]
        pont = f"{adat['megolt'] / adat['ossz'] * 100:.1f}%" if adat["ossz"] else "n/a"
        nev_megjelenites = f"`{nev}/`" + (" (`flip.py` minta)" if render_minta else "")
        sorok.append(
            f"| {nev_megjelenites} | {adat['megolt']} / {adat['ossz']} | {pont} | {adat['tulelte']} |"
        )
        reszletek = ", ".join(
            f"{nev}: {db}" for nev, db in sorted(adat["statuszok"].items())
        ) or "nincs létrehozott mutáns"
        sorok.append(f"<!-- {nev} státuszok: {reszletek} -->")

    tulelok = [m for m in mutansok if m["status"] == "túlélte"]
    csoportok: dict[str, list[dict[str, Any]]] = defaultdict(list)
    forras_cache: dict[str, tuple[str, ast.Module]] = {}
    mutans_cache: dict[str, Any] = {}
    try:
        mutmut_api = importlib.import_module("mutmut.__main__")
    except ImportError:
        mutmut_api = None
    for mutans in tulelok:
        csoportok[mutans["fajl"]].append(mutans)
    sorok.extend(["", "## Túlélők, modulonként csoportosítva", ""])
    if not tulelok:
        sorok.append("Nincs túlélő mutáns a rögzített eredményekben.")
    for fajl, csoport in sorted(csoportok.items()):
        sorok.append(f"### `{fajl}` — {len(csoport)} túlélő")
        for mutans in sorted(csoport, key=lambda m: m["nev"]):
            if mutmut_api is None:
                try:
                    eredeti = (projekt / mutans["fajl"]).read_text(encoding="utf-8")
                except OSError:
                    line = None
                else:
                    line = _fuggveny_sora(eredeti, mutans["nev"])
            else:
                line = _mutacio_sora(
                    mutans, projekt, mutmut_api, forras_cache, mutans_cache,
                )
            hely = f"{fajl}:{line}" if line is not None else f"{fajl}:?"
            sorok.append(f"- `{hely}` — `{mutans['nev']}`")
        sorok.append("")

    sorok.extend(["## NAS-kizárások", ""])
    sorok.extend(f"- `{ut}`" for ut in kizart_nas)
    if not kizart_nas:
        sorok.append("Nem volt NAS-útvonalat tartalmazó céltesztfájl.")

    sorok.extend(["", "## Mutált forrást olvasó őrtesztek kizárva", ""])
    sorok.extend(f"- `{nodeid}`" for nodeid in kizart_forras)
    if not kizart_forras:
        sorok.append("Nem találtam forráskódot olvasó céltesztet.")

    relaciok = _relacio_fajlok(projekt, csomagok)
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
    run_tests = f"{_PYTHON_EXECUTABLE} scripts/run_tests.py"
    if render_minta:
        ujrafuttatas = f"{run_tests} --mutmut --mutmut-package=render-sample"
    elif csomagok == {"ini"}:
        ujrafuttatas = f"{run_tests} --mutmut --mutmut-package=ini"
    elif csomagok == {"render"}:
        ujrafuttatas = f"{run_tests} --mutmut --mutmut-package=render"
    else:
        ujrafuttatas = f"{run_tests} --mutmut"
    sorok.extend([
        "",
        "## Csoportosított következő lépések",
        "",
        "A túlélők fájlonkénti csoportjai fent láthatók. Jegyazonosítót vagy "
        "egyenértékűmutáns-döntést a mérő nem talál ki; ezek kézi besorolásra várnak.",
        "",
        "A mutáns cache és ez a jelentés a munkafa `.tmp/picasapy-mutmut/` könyvtárában marad, "
        f"így megszakítás után ezzel folytatható: `{ujrafuttatas}`.",
        "",
    ])
    return "\n".join(sorok)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--package", choices=("all", *sorted(_TARGETS), "render-sample"), default="all",
        help="mérési hatókör; csomagonkénti első méréshez szűkíthető",
    )
    parser.add_argument(
        "--mutant", action="append", default=[],
        help="egyedi mutáns újrafuttatása (többször megadható)",
    )
    args = parser.parse_args(argv)
    render_minta = args.package == "render-sample"
    csomagok = (
        set(_TARGETS) if args.package == "all"
        else {"render"} if render_minta
        else {args.package}
    )
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
    mutmut = _mutmut_futtathato()
    if mutmut is None:
        print("A mutmut 3.5.0 csomag megvan, de a `mutmut` parancs hiányzik.", file=sys.stderr)
        return 2

    _frissit_masolat()
    kizart_nas, kizart_forras = _pytest_kivalasztas_frissitese(
        csomagok, render_minta=render_minta,
    )
    _mutmut_tamogato_forrasok(csomagok)
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    if render_minta:
        print(f"Hatókör: {_RENDER_SAMPLE_SOURCE} + {_RENDER_SAMPLE_TEST} (render-minta)")
    else:
        print("Hatókör:", " + ".join(f"src/picasapy/{nev} + tests/{nev}" for nev in sorted(csomagok)))
    print("NAS-t tartalmazó tesztfájlok kizárva:", ", ".join(kizart_nas) or "nincs")
    print("Mutált forrást olvasó tesztek kizárva:", ", ".join(kizart_forras) or "nincs")
    parancs = _mutmut_parancs(mutmut, args.mutant)
    kod, futasido, csucs = _futtat_meressel(parancs, env)
    if kod == 130:
        mutansok = _mutansok(_PROJECT / "mutants", csomagok)
        resz = _jelentes(
            mutansok, futasido=futasido, csucs_bajt=csucs,
            kizart_nas=kizart_nas, kizart_forras=kizart_forras,
            csomagok=csomagok, teljes=False, projekt=_PROJECT,
            render_minta=render_minta,
        )
        _REPORT.write_text(resz, encoding="utf-8")
        print(f"Megszakadt; folytatáshoz futtasd újra. Részjelentés: {_REPORT}")
        return 130

    if kod == 0:
        subprocess.run([mutmut, "export-cicd-stats"], cwd=_PROJECT, env=env, check=False)
    mutansok = _mutansok(_PROJECT / "mutants", csomagok)
    jelentes = _jelentes(
        mutansok, futasido=futasido, csucs_bajt=csucs,
        kizart_nas=kizart_nas, kizart_forras=kizart_forras,
        csomagok=csomagok, teljes=kod == 0, projekt=_PROJECT,
        render_minta=render_minta,
    )
    _REPORT.write_text(jelentes, encoding="utf-8")
    print(jelentes)
    print(f"Jelentés mentve: {_REPORT}")
    return kod


if __name__ == "__main__":
    raise SystemExit(main())
