#!/usr/bin/env python3
"""PR-diff alapján válassza ki a teszteket, majd tervezze meg a darabokat (#4922).

A választás biztonsági elve: amit nem lehet statikusan követni, az teljes
készletet indít. A Python-importoknál az AST a függvények törzsét is bejárja,
így a lusta importok is bekerülnek a visszafelé követett gráfba.
"""

from __future__ import annotations

import argparse
import ast
import json
import math
import os
import re
import subprocess
import sys
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, Mapping, Sequence


SMOKE_TESTS = (
    "tests/test_teszt_valasztas.py",
    "tests/test_ci_valtozas_3298.py",
    "tests/app/test_startup_smoke_4687.py",
)
HELP_TESTS = (
    "tests/app/test_sugo_tartalom_2054.py",
    "tests/test_help_hivatkozasok_2212.py",
    "tests/test_help_kereses_2214.py",
    "tests/app/qml_functional/test_sugo_kereso_lista_2214.py",
)
I18N_TESTS = (
    "tests/app/test_i18n_completeness.py",
    "tests/app/test_i18n_dictionary_4313.py",
    "tests/app/test_hivatalos_feliratok_3358.py",
    "tests/app/test_hivatalos_feliratok_3573.py",
    "tests/test_i18n_build_4817.py",
    "tests/test_i18n_generator_4866.py",
)
TARGET_SHARD_SECONDS = 180
MAX_SHARDS = 16
# Mérés nélküli projektnél az ismert készletből választott konzervatív
# fájlszám. A tényleges időt ilyenkor nem becsüljük meg.
FILES_PER_SHARD_WITHOUT_TIMINGS = 30
MAX_SELECTED_FRACTION = 0.6
# A nem-app fájlok korábbi teljes futásának összesített mérési kulcsa.
# Teljes készletnél ez a súlyozást és a darabszámot segíti, nem futtatási egység.
NON_APP_UNIT = "tests --ignore=tests/app"
_FULL_TRIGGER_FILES = frozenset({"pyproject.toml", "scripts/run_tests.py"})
_VERSION_LINE = re.compile(
    r"^\s*version\s*=\s*(['\"])(?P<value>[^'\"]+)\1\s*(?:#.*)?$"
)
_ROOT = Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Selection:
    fajlok: tuple[str, ...]
    teljes: bool
    indok: str
    nem_merheto: tuple[str, ...] = ()


@dataclass(frozen=True)
class ShardPlan:
    darabszam: int
    mert_masodperc: float
    ismeretlen_fajlok: tuple[str, ...]
    tul_hosszu_fajlok: tuple[str, ...]


def discover_tests(root: Path) -> list[str]:
    """A pytest által futtatható, név szerint felismert tesztfájlok."""
    tests = root / "tests"
    if not tests.is_dir():
        return []
    return sorted(
        path.relative_to(root).as_posix()
        for path in tests.rglob("test_*.py")
        if path.is_file()
    )


def pyproject_only_version_changed(old: str, new: str) -> bool:
    """Igaz, ha kizárólag a pyproject egy meglévő verziósora változott."""
    regi_sorok = old.splitlines()
    uj_sorok = new.splitlines()
    regi_verziok = [s for s in regi_sorok if _VERSION_LINE.fullmatch(s)]
    uj_verziok = [s for s in uj_sorok if _VERSION_LINE.fullmatch(s)]
    if len(regi_verziok) != 1 or len(uj_verziok) != 1:
        return False
    regi_maras = [s for s in regi_sorok if not _VERSION_LINE.fullmatch(s)]
    uj_maras = [s for s in uj_sorok if not _VERSION_LINE.fullmatch(s)]
    regi_ertek = _VERSION_LINE.fullmatch(regi_verziok[0]).group("value")
    uj_ertek = _VERSION_LINE.fullmatch(uj_verziok[0]).group("value")
    return regi_maras == uj_maras and regi_ertek != uj_ertek


def _module_name(path: str, *, root_kind: str) -> str | None:
    """Fájlból importálható modulnevet készít a három projektgyökérhez."""
    tiszta = path.replace("\\", "/")
    if root_kind == "source":
        prefix = "src/picasapy/"
        if not tiszta.startswith(prefix) or not tiszta.endswith(".py"):
            return None
        resz = tiszta[len("src/"):-3]
    elif root_kind == "scripts":
        prefix = "scripts/"
        if not tiszta.startswith(prefix) or not tiszta.endswith(".py"):
            return None
        resz = tiszta[:-3]
    else:
        prefix = "tests/"
        if not tiszta.startswith(prefix) or not tiszta.endswith(".py"):
            return None
        resz = tiszta[:-3]
        resz = f"tests/{resz}"
    if resz.endswith("/__init__"):
        resz = resz[:-9]
    elif resz == "__init__":
        resz = ""
    return resz.replace("/", ".").strip(".") or None


def _relative_import_base(module: str, is_package: bool, level: int) -> str:
    package = module if is_package else module.rpartition(".")[0]
    parts = package.split(".") if package else []
    keep = max(0, len(parts) - level + 1)
    return ".".join(parts[:keep])


def _import_graph(
    root: Path,
) -> tuple[dict[str, set[str]], dict[str, set[str]], set[str]]:
    """Visszaadja a modulgráfot és a modulnév → tesztfájl leképezést."""
    paths: dict[str, list[tuple[str, str]]] = defaultdict(list)
    all_python: list[tuple[str, str, str]] = []
    for prefix, kind in (
        (root / "src" / "picasapy", "source"),
        (root / "scripts", "scripts"),
        (root / "tests", "tests"),
    ):
        if not prefix.is_dir():
            continue
        for file in prefix.rglob("*.py"):
            rel = file.relative_to(root).as_posix()
            module = _module_name(rel, root_kind=kind)
            if module:
                paths[module].append((rel, kind))
                all_python.append((rel, module, kind))

    # A tests/app alatti segédmodulok egy részét szándékosan a saját
    # könyvtárukból, csupasz néven importálják.
    test_nodes: dict[str, set[str]] = defaultdict(set)
    test_aliases: dict[str, set[str]] = defaultdict(set)
    script_aliases: dict[str, set[str]] = defaultdict(set)
    test_modules_by_path: dict[str, str] = {}
    conftest_modules: list[tuple[str, str]] = []
    for rel, module, kind in all_python:
        if kind == "tests" and Path(rel).name.startswith("test_"):
            test_nodes[module].add(rel)
            test_modules_by_path[rel] = module
            test_aliases[Path(rel).stem].add(module)
            parts = Path(rel).relative_to("tests").with_suffix("").parts
            if parts and parts[-1] == "__init__":
                parts = parts[:-1]
            for idx in range(1, len(parts) + 1):
                test_aliases[".".join(parts[:idx])].add(module)
        elif kind == "tests":
            test_aliases[Path(rel).stem].add(module)
        elif kind == "scripts":
            script_aliases[Path(rel).stem].add(module)
        if kind == "tests" and Path(rel).name == "conftest.py":
            conftest_modules.append((rel, module))

    existing = set(paths)
    graph: dict[str, set[str]] = defaultdict(set)
    bizonytalan_dinamikus = set()

    def add_import(caller: str, imported: str, *, package_import: bool = False) -> None:
        if not imported:
            return
        # Importáláskor a csomag szülői is betöltődnek. Ezeket is élként
        # vesszük fel, hogy a package __init__.py módosítása se maradjon ki.
        pieces = imported.split(".")
        candidates = [".".join(pieces[:i]) for i in range(1, len(pieces) + 1)]
        for candidate in candidates:
            if (
                candidate in existing
                or candidate.startswith("picasapy")
                or candidate in test_aliases
                or candidate in script_aliases
            ):
                graph[caller].add(candidate)
        if package_import:
            for candidate in candidates:
                for child in existing:
                    if child.startswith(candidate + ".") and child == f"{candidate}.{child.rsplit('.', 1)[-1]}":
                        # `from package import module`-alaknál a modulnév is
                        # a cél lehet; a fa többi gyermekét nem találgatjuk.
                        graph[caller].add(child)

    for rel, module, kind in all_python:
        path = root / rel
        try:
            source_text = path.read_text(encoding="utf-8")
            tree = ast.parse(source_text, filename=rel)
        except (OSError, UnicodeError, SyntaxError) as exc:
            raise ValueError(f"nem elemezhető Python-fájl: {rel}: {exc}") from exc
        is_package = path.name == "__init__.py"
        importlib_names = {"importlib"}
        import_module_names = {"import_module"}
        module_values: dict[str, set[str]] = defaultdict(set)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "importlib":
                        importlib_names.add(alias.asname or "importlib")
            elif isinstance(node, ast.ImportFrom) and node.module == "importlib":
                for alias in node.names:
                    if alias.name == "import_module":
                        import_module_names.add(alias.asname or "import_module")
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                value = node.value
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                for target in targets:
                    if not isinstance(target, ast.Name) or not isinstance(value, ast.Dict):
                        continue
                    if target.id == "_EXPORT_MODULES":
                        module_values[target.id].update(
                            key.value for key in value.keys
                            if isinstance(key, ast.Constant)
                            and isinstance(key.value, str)
                        )
                    elif target.id.endswith(("_TO_MODULE", "_TO_MODULES")) or target.id.startswith("_LAZY_APP_"):
                        module_values[target.id].update(
                            item.value for item in value.values
                            if isinstance(item, ast.Constant)
                            and isinstance(item.value, str)
                        )

        def literal_targets(
            node: ast.AST, module_values: dict[str, set[str]] = module_values
        ) -> set[str] | None:
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return {node.value}
            if isinstance(node, ast.Name):
                return module_values.get(node.id) or None
            if isinstance(node, ast.Subscript) and isinstance(node.value, ast.Name):
                return module_values.get(node.value.id) or None
            if isinstance(node, ast.JoinedStr):
                targets = {""}
                for part in node.values:
                    if isinstance(part, ast.Constant) and isinstance(part.value, str):
                        pieces = {part.value}
                    elif isinstance(part, ast.FormattedValue):
                        pieces = literal_targets(part.value)
                        if pieces is None:
                            return None
                    else:
                        return None
                    targets = {left + right for left in targets for right in pieces}
                return targets
            return None

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    add_import(module, alias.name)
            elif isinstance(node, ast.ImportFrom):
                base = (
                    _relative_import_base(module, is_package, node.level)
                    if node.level else (node.module or "")
                )
                if base:
                    add_import(module, base)
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    child = f"{base}.{alias.name}" if base else alias.name
                    if child in existing or child.startswith("picasapy"):
                        add_import(module, child)
            elif isinstance(node, ast.Call) and node.args:
                import_call = (
                    isinstance(node.func, ast.Attribute)
                    and node.func.attr == "import_module"
                    and isinstance(node.func.value, ast.Name)
                    and node.func.value.id in importlib_names
                ) or (
                    isinstance(node.func, ast.Name)
                    and node.func.id in import_module_names
                )
                builtin_call = (
                    isinstance(node.func, ast.Name) and node.func.id == "__import__"
                )
                if not (import_call or builtin_call):
                    continue
                targets = literal_targets(node.args[0])
                if targets is None and import_call and is_package:
                    # A csomag-API-k (__getattr__) gyakran az exporttáblából
                    # állítják össze a relatív modult. Ha ezt a táblát AST-vel
                    # nem lehet teljesen feloldani, a csomag összes forrás-gyerekét
                    # bekötjük, így egy publikus név mögötti modul sem marad ki.
                    targets = {
                        child[len(module) + 1:]
                        for child in existing if child.startswith(module + ".")
                    }
                if targets is None:
                    # A platform-őr név szerint csak a standard könyvtár
                    # modulneveit importálja; minden más dinamikus tesztimport
                    # bizonytalanság, ezért kódváltozásnál teljes készlet kell.
                    stdlib_only = (
                        kind == "tests"
                        and "stdlib_module_names" in source_text
                    )
                    if kind == "source" or (kind == "tests" and not stdlib_only):
                        bizonytalan_dinamikus.add(module)
                    continue
                for dynamic_name in targets:
                    if dynamic_name.startswith("."):
                        dots = len(dynamic_name) - len(dynamic_name.lstrip("."))
                        base = _relative_import_base(module, is_package, dots)
                        dynamic_name = f"{base}.{dynamic_name.lstrip('.')}".strip(".")
                    elif "." not in dynamic_name and module.startswith("picasapy."):
                        package = module if is_package else module.rpartition(".")[0]
                        dynamic_name = f"{package}.{dynamic_name}"
                    add_import(module, dynamic_name)

    # A csupasz helper- és scripts-importok aliasait a valódi modulhoz kötjük.
    # Alias → modul indexet használunk, hogy ez a lépés lineáris maradjon a
    # tesztfájlok számának növekedésével.
    alias_targets: dict[str, set[str]] = defaultdict(set)
    for aliases in (test_aliases, script_aliases):
        for alias, targets in aliases.items():
            alias_targets[alias].update(targets)
    for importer, imported_names in list(graph.items()):
        for imported in tuple(imported_names):
            for target in alias_targets.get(imported, ()):
                if importer != target:
                    graph[importer].add(target)

    # A pytest-conftest implicit betöltése nem látszik AST-importként. Ha egy
    # közös fixture egy megváltozott termékmodult importál, minden alatta levő
    # teszt fogyasztónak számít.
    for test_path, test_module in test_modules_by_path.items():
        for conftest_path, conftest_module in conftest_modules:
            conf_dir = Path(conftest_path).parent.as_posix()
            if test_path.startswith(conf_dir + "/"):
                graph[test_module].add(conftest_module)

    return graph, test_nodes, bizonytalan_dinamikus


def _dependento_tesztek(
    root: Path, changed_modules: Iterable[str]
) -> dict[str, set[str]]:
    graph, test_nodes, bizonytalan_dinamikus = _import_graph(root)
    modositott = set(changed_modules)
    bizonytalan = modositott & bizonytalan_dinamikus
    ismeretlen_tesztimport = {
        module for module in bizonytalan_dinamikus
        if module.startswith("tests.")
    }
    if ismeretlen_tesztimport and any(
        module.startswith("picasapy.") for module in modositott
    ):
        bizonytalan.update(ismeretlen_tesztimport)
    if bizonytalan:
        raise ValueError(
            "nem feloldható dinamikus import a módosított modulban: "
            + ", ".join(sorted(bizonytalan))
        )
    reverse: dict[str, set[str]] = defaultdict(set)
    for caller, imports in graph.items():
        for imported in imports:
            reverse[imported].add(caller)
    result: dict[str, set[str]] = {}
    for changed in set(changed_modules):
        reached = {changed}
        queue = [changed]
        while queue:
            node = queue.pop()
            for caller in reverse.get(node, ()):
                if caller not in reached:
                    reached.add(caller)
                    queue.append(caller)
        consumers: set[str] = set()
        for node in reached:
            consumers.update(test_nodes.get(node, ()))
        result[changed] = consumers
    return result


def select_tests(
    root: Path,
    changed: Sequence[str] | None,
    *,
    pyproject_version_only: bool = False,
    force_full: bool = False,
) -> Selection:
    """Válassza ki a diff által érintett teszteket; bizonytalanságnál mindet."""
    all_tests = discover_tests(root)
    all_set = set(all_tests)
    smoke = sorted(path for path in SMOKE_TESTS if path in all_set)
    if force_full:
        return Selection(tuple(all_tests), True, "teljes futás kérése")
    if not changed:
        return Selection(tuple(all_tests), True, "üres vagy nem megállapítható diff")

    selected: set[str] = set(smoke)
    modules: set[str] = set()
    qml_paths: list[str] = []
    source_files = 0
    uncertainty: list[str] = []
    actionable = False

    for raw in changed:
        path = raw.replace("\\", "/").lstrip("./")
        if path in _FULL_TRIGGER_FILES:
            if path == "pyproject.toml" and pyproject_version_only:
                continue
            return Selection(tuple(all_tests), True, f"teljes készletet kiváltó fájl: {path}")
        if path.endswith("/conftest.py") or path == "conftest.py":
            return Selection(tuple(all_tests), True, f"közös pytest-beállítás változott: {path}")
        if path.startswith("tests/support/"):
            return Selection(tuple(all_tests), True, "a tests/support közös segédei változtak")
        if path.startswith((".github/", "packaging/")):
            return Selection(tuple(all_tests), True, f"közös CI/csomagolási fájl változott: {path}")
        if path == "CHANGELOG.md" or path.startswith("changelog.d/"):
            continue
        if path == "pyproject.toml" and pyproject_version_only:
            continue
        if path.startswith(("docs/",)) or path in {"README.md", "LICENSE", "CONTRIBUTING.md"}:
            continue
        if path in all_set:
            selected.add(path)
            actionable = True
            continue
        if path.startswith("tests/") and path.endswith(".py"):
            module = _module_name(path, root_kind="tests")
            if module:
                modules.add(module)
                modules.add(Path(path).stem)
                actionable = True
                continue
            uncertainty.append(path)
            continue
        if path.startswith("src/picasapy/"):
            if path.endswith(".qml"):
                qml_paths.append(path)
                source_files += 1
                actionable = True
                continue
            if path.startswith("src/picasapy/app/i18n/") and path.endswith((".ts", ".qm")):
                selected.update(test for test in I18N_TESTS if test in all_set)
                # Az egyedi katalógust közvetlenül olvasó tesztek is fussanak.
                for test in all_tests:
                    try:
                        content = (root / test).read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if Path(path).name in content:
                        selected.add(test)
                actionable = True
                continue
            if path.startswith("src/picasapy/help/") and path.endswith(".md"):
                help_tests = {test for test in HELP_TESTS if test in all_set}
                if not help_tests:
                    return Selection(tuple(all_tests), True, "a súgó tartalmához nem található őrteszt")
                selected.update(help_tests)
                actionable = True
                continue
            if path.startswith("src/picasapy/help/") and Path(path).name in {
                ".last_documented_commit", ".update.log"
            }:
                helper_test = "tests/scripts/test_kiadas_szukseges_1319.py"
                if helper_test in all_set:
                    selected.add(helper_test)
                    actionable = True
                    continue
            if path.endswith(".py"):
                module = _module_name(path, root_kind="source")
                if module:
                    modules.add(module)
                    source_files += 1
                    actionable = True
                    continue
            uncertainty.append(path)
            continue
        if path.startswith("scripts/") and path.endswith(".py"):
            module = _module_name(path, root_kind="scripts")
            if module:
                modules.add(module)
                source_files += 1
                actionable = True
                continue
        # A fentieken kívüli adat, beállítás vagy új forrásfajta hatását nem
        # lehet megbízhatóan az importgráfból követni.
        uncertainty.append(path)

    if uncertainty:
        return Selection(
            tuple(all_tests), True,
            "nem követhető fájltípus vagy útvonal: " + ", ".join(uncertainty[:4]),
            tuple(uncertainty),
        )
    if source_files >= 20:
        return Selection(tuple(all_tests), True, "nagy, legalább 20 forrásfájlos átalakítás")

    if modules:
        try:
            for module, consumers in _dependento_tesztek(root, modules).items():
                if not consumers:
                    return Selection(
                        tuple(all_tests), True,
                        f"a forrás importgráfjában nincs biztos tesztfogyasztó: {module}",
                    )
                selected.update(consumers & all_set)
        except ValueError as exc:
            return Selection(tuple(all_tests), True, f"az AST-importgráf bizonytalan: {exc}")
    if qml_paths:
        qml_tests = {
            path for path in all_tests
            if path.startswith("tests/app/qml_functional/")
        }
        if not qml_tests:
            return Selection(tuple(all_tests), True, "QML-változáshoz nem található funkcionális teszt")
        selected.update(qml_tests)
        # A funkcionális tesztek mindegyike QML-ből indul, de a nem-funkcionális
        # forrásőrök közvetlen fájlnév-hivatkozásait is felvesszük.
        patterns = [
            re.compile(rf"\b{re.escape(Path(path).stem)}(?:\.qml)?\b")
            for path in qml_paths
        ]
        for test in all_tests:
            if test in qml_tests:
                continue
            try:
                content = (root / test).read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            if any(pattern.search(content) for pattern in patterns):
                selected.add(test)
        actionable = True

    if not actionable:
        # Ismert dokumentáció-/változásnapló-diffnél csak a rövid füstkészlet
        # marad. Minden más útvonal fent már teljes készletre esett vissza.
        return Selection(tuple(smoke), False, "csak dokumentáció/verzió/változásnapló")
    if len(selected) > MAX_SELECTED_FRACTION * len(all_tests):
        return Selection(tuple(all_tests), True, "a kiválasztás a készlet több mint 60%-át érinti")
    return Selection(tuple(sorted(selected)), False, "érintett tesztek + füstkészlet")


def meresi_idok(root: Path, path: Path | None = None) -> dict[str, float]:
    """A commitolt tesztfutás-idők; hibás vagy hiányzó táblánál üres."""
    file = path or (root / "scripts" / "teszt_idok.json")
    try:
        adat = json.loads(file.read_text(encoding="utf-8"))
        if not isinstance(adat, dict):
            return {}
        return {
            str(name).replace("\\", "/"): float(seconds)
            for name, seconds in adat.items()
            if isinstance(seconds, (int, float)) and seconds >= 0
        }
    except (OSError, ValueError, TypeError):
        return {}


def tervezz_darabokat(
    files: Sequence[str],
    timings: Mapping[str, float],
    *,
    teljes: bool,
    cel_masodperc: int = TARGET_SHARD_SECONDS,
    max_darab: int = MAX_SHARDS,
) -> ShardPlan:
    """A futásidők összege vagy mérés híján a fájlszám alapján tervez."""
    all_files = tuple(sorted(set(files)))
    non_app = tuple(path for path in all_files if not path.startswith("tests/app/"))
    has_non_app_total = teljes and bool(non_app) and NON_APP_UNIT in timings
    ismert_nem_app = sum(
        float(timings[path]) for path in non_app if path in timings
    )
    known = sum(float(timings[path]) for path in all_files if path in timings)
    if has_non_app_total:
        # A teljes készlet mért ideje továbbra is beleszámít a darabszámba,
        # de az egyedi nem-app fájlok idejét nem mérte külön.
        known += max(0.0, float(timings[NON_APP_UNIT]) - ismert_nem_app)
    unknown = tuple(path for path in all_files if path not in timings)
    becslendo = tuple(
        path for path in unknown
        if not (has_non_app_total and path in non_app)
    )
    measured_file_times = sorted(
        float(value)
        for name, value in timings.items()
        if name in all_files and value > 0
    )
    if measured_file_times:
        # A futtató is a mért idők 90. percentilisével tervez a hiányzó
        # fájloknak (#4825); ezt a darabszámnál is beszámítjuk, különben egy
        # néhány mért + sok új fájlos PR túl kevés darabra oszlana.
        ismeretlen_becsles = measured_file_times[
            min(len(measured_file_times) - 1, int(len(measured_file_times) * 0.9))
        ]
        becsult_osszeg = known + len(becslendo) * ismeretlen_becsles
        count = math.ceil(becsult_osszeg / cel_masodperc)
    elif known > 0:
        count = math.ceil((known + len(becslendo)) / cel_masodperc)
    else:
        # A teljesen mérés nélküli repónál nincs miből időt becsülni.
        count = math.ceil(len(all_files) / FILES_PER_SHARD_WITHOUT_TIMINGS)
    count = max(1, min(max_darab, count))
    too_long = tuple(
        path for path in all_files
        if path in timings and float(timings[path]) > cel_masodperc
    )
    return ShardPlan(count, known, unknown, too_long)


def _shard_units(
    files: Sequence[str], timings: Mapping[str, float], *, teljes: bool
) -> tuple[list[str], dict[str, float]]:
    all_files = tuple(sorted(set(files)))
    non_app = tuple(path for path in all_files if not path.startswith("tests/app/"))
    missing_non_app = tuple(path for path in non_app if path not in timings)
    has_non_app_total = (
        teljes and bool(non_app) and NON_APP_UNIT in timings
    )
    measured = [
        float(timings[name])
        for name in all_files
        if name in timings and float(timings[name]) > 0
    ]
    measured.sort()
    fallback = (
        measured[min(len(measured) - 1, int(len(measured) * 0.9))]
        if measured else 1.0
    )
    non_app_known = sum(
        float(timings[name]) for name in non_app if name in timings
    )
    non_app_fajl_atlag = (
        max(0.0, float(timings[NON_APP_UNIT]) - non_app_known)
        / len(missing_non_app)
        if has_non_app_total and missing_non_app else 0.0
    )
    weights: dict[str, float] = {}
    for unit in all_files:
        if unit in timings:
            weights[unit] = float(timings[unit])
        elif has_non_app_total and unit in missing_non_app:
            # A fájlokat külön futtatjuk, ezért az összesített mérést az
            # egyedi, még nem mért fájlok között osztjuk szét a kiosztáshoz.
            weights[unit] = non_app_fajl_atlag
        else:
            weights[unit] = fallback
    return list(all_files), weights


def darab_fajljai(
    files: Sequence[str],
    timings: Mapping[str, float],
    shard: int,
    count: int,
    *,
    teljes: bool = False,
) -> tuple[str, ...]:
    """Mohó, leghosszabb-először kiosztás; az egységek pontosan egyszer futnak."""
    if count < 1 or not 1 <= shard <= count:
        raise ValueError("a darabszám és a darab sorszáma érvénytelen")
    units, weights = _shard_units(files, timings, teljes=teljes)
    loads = [0.0] * count
    assigned: list[list[str]] = [[] for _ in range(count)]
    for unit in sorted(units, key=lambda name: (-weights[name], name)):
        target = min(range(count), key=lambda idx: (loads[idx], idx))
        assigned[target].append(unit)
        loads[target] += weights[unit]
    return tuple(sorted(assigned[shard - 1]))


def _changed_files(root: Path, base: str, head: str) -> list[str] | None:
    if not base or not head:
        return None
    try:
        result = subprocess.run(
            ["git", "diff", "--name-only", f"{base}...{head}"],
            cwd=root, check=True, capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
    except (OSError, subprocess.CalledProcessError):
        return None
    return [line.strip() for line in result.stdout.splitlines() if line.strip()]


def _version_only_for_refs(root: Path, base: str, head: str) -> bool:
    if not base or not head:
        return False
    try:
        old = subprocess.run(
            ["git", "show", f"{base}:pyproject.toml"], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
        new = subprocess.run(
            ["git", "show", f"{head}:pyproject.toml"], cwd=root,
            check=True, capture_output=True, text=True, encoding="utf-8", errors="replace",
        ).stdout
    except (OSError, subprocess.CalledProcessError):
        return False
    return pyproject_only_version_changed(old, new)


def _selection_for_cli(root: Path, *, base: str, head: str, force_full: bool) -> Selection:
    changed = None if force_full else _changed_files(root, base, head)
    return select_tests(
        root, changed,
        pyproject_version_only=_version_only_for_refs(root, base, head),
        force_full=force_full,
    )


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_ROOT)
    parser.add_argument("--darabszam", action="store_true", help="GitHub Actions matrix-kimenet")
    parser.add_argument("--lista", type=Path, help="a kiválasztott tesztek JSON-listájának kiírása")
    parser.add_argument("--alap", default=os.environ.get("PICASAPY_ERINTETT_ALAP", ""))
    parser.add_argument("--fej", default=os.environ.get("GITHUB_SHA", "HEAD"))
    parser.add_argument(
        "--teljes", action="store_true",
        default=os.environ.get("PICASAPY_TESZT_TELJES") == "1",
    )
    args = parser.parse_args(argv)
    root = args.root.resolve()
    selection = _selection_for_cli(
        root, base=args.alap, head=args.fej, force_full=args.teljes
    )
    timings = meresi_idok(root)
    plan = tervezz_darabokat(selection.fajlok, timings, teljes=selection.teljes)

    if args.darabszam:
        output = os.environ.get("GITHUB_OUTPUT")
        values = (
            f"darabok={[*range(1, plan.darabszam + 1)]}\n"
            f"darabszam={plan.darabszam}\n"
        )
        if output:
            with open(output, "a", encoding="utf-8") as stream:
                stream.write(values)
        else:
            print(values, end="")
        print(
            f"Tesztek: {len(selection.fajlok)} fájl; teljes={selection.teljes}; "
            f"ok={selection.indok}; ismert idő={plan.mert_masodperc:.1f}s; "
            f"mérés nélküli={len(plan.ismeretlen_fajlok)}; "
            f"darab={plan.darabszam}.",
            file=sys.stderr,
        )
        return 0

    if args.lista:
        args.lista.write_text(
            json.dumps(
                {"fajlok": selection.fajlok, "teljes": selection.teljes,
                 "indok": selection.indok},
                ensure_ascii=False,
            ) + "\n",
            encoding="utf-8",
        )
        print(
            f"{len(selection.fajlok)} tesztfájl; teljes={selection.teljes}; "
            f"{selection.indok}",
            file=sys.stderr,
        )
        return 0
    parser.error("add meg a --darabszam vagy --lista kapcsolót")
    return 2


if __name__ == "__main__":
    raise SystemExit(main())
