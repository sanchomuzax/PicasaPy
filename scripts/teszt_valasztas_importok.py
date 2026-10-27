"""AST-alapú importgráf a PR-tesztválasztóhoz (#4922)."""

from __future__ import annotations

import ast
import functools
from collections import defaultdict
from pathlib import Path
from typing import Iterable


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


# a passzív fájlok rekurzív feloldása (`_passziv_fajl`) lépésenként újra
# kérte; a gráf a futás alatt nem változik, és senki nem módosítja
@functools.lru_cache(maxsize=None)
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
