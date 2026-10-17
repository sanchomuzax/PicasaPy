#!/usr/bin/env python3
"""Audit named QML controls for real mouse or keyboard input in tests.

The inventory intentionally follows the 5150 B-item definition: controls with
an ``objectName`` whose QML type is Button, ToolButton, MenuItem, CheckBox,
RadioButton, ComboBox, Switch, TextField, MouseArea, TapHandler, Action, or
Shortcut.  A test counts only when a test function (possibly through a local
test helper) resolves that name and reaches a QTest/pytest-qt physical input
call.  Slot invocation, signal emission, property writes, and textual mentions
do not count.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
import warnings
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Iterable


CONTROL_TYPES = {
    "Button",
    "ToolButton",
    "MenuItem",
    "CheckBox",
    "RadioButton",
    "ComboBox",
    "Switch",
    "TextField",
    "MouseArea",
    "TapHandler",
    "Action",
    "Shortcut",
}
INPUT_METHODS = {
    "mouseClick",
    "mousePress",
    "mouseDClick",
    "keyClick",
    "keyClicks",
    "mouseMove",
}
GROUP_ORDER = ("Rács", "Néző", "Szerkesztő", "Menüsor", "Tálca", "Párbeszédek", "Egyéb")


@dataclass(frozen=True)
class Control:
    file: str
    object_name: str
    line: int
    group: str
    qml_type: str
    dynamic: bool = False


@dataclass
class FunctionInfo:
    path: Path
    module: str
    node: ast.FunctionDef | ast.AsyncFunctionDef
    aliases: dict[str, tuple[str, str]]
    module_constants: dict[str, object]


def _qml_tokens(source: str) -> Iterable[tuple[str, str, int]]:
    """Yield QML identifiers, strings, and punctuation while skipping comments."""
    i = 0
    line = 1
    length = len(source)
    while i < length:
        char = source[i]
        if char == "\n":
            line += 1
            i += 1
            continue
        if char.isspace():
            i += 1
            continue
        if source.startswith("//", i):
            end = source.find("\n", i)
            i = length if end < 0 else end
            continue
        if source.startswith("/*", i):
            end = source.find("*/", i + 2)
            if end < 0:
                line += source[i:].count("\n")
                break
            line += source[i : end + 2].count("\n")
            i = end + 2
            continue
        if char in ('"', "'"):
            quote = char
            start_line = line
            i += 1
            chars: list[str] = []
            while i < length:
                current = source[i]
                if current == "\\" and i + 1 < length:
                    escaped = source[i + 1]
                    chars.append({"n": "\n", "r": "\r", "t": "\t"}.get(escaped, escaped))
                    if escaped == "\n":
                        line += 1
                    i += 2
                elif current == quote:
                    i += 1
                    break
                else:
                    chars.append(current)
                    if current == "\n":
                        line += 1
                    i += 1
            yield "string", "".join(chars), start_line
            continue
        if char.isalpha() or char == "_" or char == "$":
            start = i
            while i < length and (source[i].isalnum() or source[i] in "_$"):
                i += 1
            yield "identifier", source[start:i], line
            continue
        yield "punctuation", char, line
        i += 1


def _qml_controls(qml_root: Path) -> list[Control]:
    controls: list[Control] = []
    for path in sorted(qml_root.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        tokens = list(_qml_tokens(source))
        stack: list[str | None] = []
        for index, (kind, value, line) in enumerate(tokens):
            if kind == "punctuation" and value == "{":
                previous = tokens[index - 1] if index else ("", "", line)
                qml_type = previous[1].split(".")[-1] if previous[0] == "identifier" else ""
                stack.append(qml_type if qml_type in CONTROL_TYPES else None)
            elif kind == "punctuation" and value == "}":
                if stack:
                    stack.pop()
            elif kind == "identifier" and value == "objectName" and stack and stack[-1]:
                colon = tokens[index + 1] if index + 1 < len(tokens) else None
                literal = tokens[index + 2] if index + 2 < len(tokens) else None
                if colon and colon[:2] == ("punctuation", ":") and literal and literal[0] == "string":
                    object_name = literal[1]
                    next_index = index + 3
                    while (
                        next_index + 1 < len(tokens)
                        and tokens[next_index][:2] == ("punctuation", "+")
                        and tokens[next_index + 1][0] == "string"
                    ):
                        object_name += tokens[next_index + 1][1]
                        next_index += 2
                    dynamic = next_index < len(tokens) and tokens[next_index][:2] == ("punctuation", "+")
                    controls.append(
                        Control(
                            file=path.relative_to(qml_root).as_posix(),
                            object_name=object_name,
                            line=line,
                            group=_group_for(path.name),
                            qml_type=stack[-1] or "",
                            dynamic=dynamic,
                        )
                    )
    return controls


def _group_for(filename: str) -> str:
    stem = Path(filename).stem
    lower = stem.lower()
    if stem in {"Main", "PicasaMenuBar"}:
        return "Menüsor"
    if stem in {"TrayBar", "TrayContextMenu", "MainToolbar"}:
        return "Tálca"
    if stem in {
        "PhotoViewer",
        "PhotoViewerSettingsDialog",
        "ViewerContextMenu",
        "VideoPlayerControls",
        "VideoPlayerView",
        "VideoEditPanel",
        "SlideshowView",
        "CaptureMoviePanelPopup",
    }:
        return "Néző"
    if stem.startswith(("Collage", "CreateDialogs", "Editor")) or stem in {
        "EmailChoiceDialog",
        "PrintDialog",
        "PrintOptionsPanel",
    }:
        return "Szerkesztő"
    if stem in {
        "FolderContextMenu",
        "FolderListContextMenu",
        "AlbumContextMenu",
        "PhotoContextMenu",
        "PeopleAlbumContextMenu",
        "TagContextMenu",
        "FolderPane",
        "LightboxHeader",
        "LightboxFeed",
        "UnnamedFacesView",
        "PropertiesPanel",
        "PlacesPanel",
        "PlacesMarker",
        "PeopleManagerDialog",
        "TimelineView",
        "QuickTagsConfigDialog",
        "TagsPanel",
        "FolderManagerDialog",
        "FolderPropertiesDialog",
    }:
        return "Rács"
    if "dialog" in lower or lower.startswith(("options", "import", "export", "save")):
        return "Párbeszédek"
    return "Egyéb"


def _dotted_name(node: ast.expr) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _dotted_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return ""


def _function_nodes(tree: ast.AST) -> Iterable[ast.FunctionDef | ast.AsyncFunctionDef]:
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            yield node


def _collect_functions(tests_root: Path) -> list[FunctionInfo]:
    infos: list[FunctionInfo] = []
    for path in sorted(tests_root.rglob("*.py")):
        source = path.read_text(encoding="utf-8")
        try:
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", SyntaxWarning)
                tree = ast.parse(source, filename=str(path))
        except SyntaxError:
            continue
        aliases: dict[str, tuple[str, str]] = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                for alias in node.names:
                    aliases[alias.asname or alias.name] = (node.module, alias.name)
        constants = _module_constants(tree)
        module = path.stem
        for node in _function_nodes(tree):
            infos.append(FunctionInfo(path, module, node, aliases, constants))
    return infos


_UNKNOWN = object()


def _static_value(node: ast.AST, constants: dict[str, object]) -> object:
    """Evaluate only inert Python syntax used by module constants/decorators."""
    if isinstance(node, ast.Constant):
        return node.value
    if isinstance(node, ast.Name):
        return constants.get(node.id, _UNKNOWN)
    if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
        values = [_static_value(item, constants) for item in node.elts]
        if isinstance(node, ast.List):
            return values
        if isinstance(node, ast.Set):
            return set(values) if all(value is not _UNKNOWN for value in values) else tuple(values)
        return tuple(values)
    if isinstance(node, ast.Dict):
        entries = [
            (_static_value(key, constants), _static_value(value, constants))
            for key, value in zip(node.keys, node.values, strict=True)
            if key is not None
        ]
        if any(key is _UNKNOWN for key, _value in entries):
            return _UNKNOWN
        try:
            return dict(entries)
        except TypeError:
            return _UNKNOWN
    if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add):
        left = _static_value(node.left, constants)
        right = _static_value(node.right, constants)
        if isinstance(left, str) and isinstance(right, str):
            return left + right
        return _UNKNOWN
    if isinstance(node, ast.Call) and _dotted_name(node.func).split(".")[-1] == "param":
        # A pytest.param row is its positional data; id=/marks= do not affect columns.
        return tuple(_static_value(argument, constants) for argument in node.args)
    return _UNKNOWN


def _module_constants(tree: ast.Module) -> dict[str, object]:
    constants: dict[str, object] = {}
    for statement in tree.body:
        if isinstance(statement, ast.Assign):
            value = _static_value(statement.value, constants)
            for target in statement.targets:
                if isinstance(target, ast.Name):
                    constants[target.id] = value
        elif isinstance(statement, ast.AnnAssign) and isinstance(statement.target, ast.Name) and statement.value:
            constants[statement.target.id] = _static_value(statement.value, constants)
    return constants


def _matching_control_names(value: object, controls: set[str], dynamic_controls: set[str]) -> set[str]:
    if not isinstance(value, str):
        return set()
    matches = {value} if value in controls else set()
    if value not in controls:
        matches.update(prefix for prefix in dynamic_controls if prefix and value.startswith(prefix))
    return matches


def _parametrize_values(
    function: ast.FunctionDef | ast.AsyncFunctionDef,
    controls: set[str],
    module_constants: dict[str, object],
    dynamic_controls: set[str],
) -> dict[str, set[str]]:
    result: dict[str, set[str]] = {}
    for decorator in function.decorator_list:
        if not isinstance(decorator, ast.Call) or _dotted_name(decorator.func).split(".")[-1] != "parametrize":
            continue
        if len(decorator.args) < 2:
            continue
        names = _static_value(decorator.args[0], module_constants)
        values = _static_value(decorator.args[1], module_constants)
        params = names.split(",") if isinstance(names, str) else list(names) if isinstance(names, (list, tuple)) else []
        if not isinstance(values, (list, tuple)) or not params:
            continue
        for index, param in enumerate(params):
            if not isinstance(param, str):
                continue
            found: set[str] = set()
            for row in values:
                item = row[index] if isinstance(row, (list, tuple)) and index < len(row) else row
                found.update(_matching_control_names(item, controls, dynamic_controls))
            if found:
                result[param.strip()] = found
    return result


class _TestInputAnalyzer:
    def __init__(
        self,
        functions: list[FunctionInfo],
        control_types: dict[str, set[str]],
        dynamic_control_names: set[str],
    ):
        self.functions = functions
        self.control_types = control_types
        self.control_names = set(control_types)
        self.dynamic_control_names = dynamic_control_names
        self.functions_by_name: dict[str, list[FunctionInfo]] = defaultdict(list)
        self.functions_by_module: dict[tuple[str, str], list[FunctionInfo]] = defaultdict(list)
        for info in functions:
            self.functions_by_name[info.node.name].append(info)
            self.functions_by_module[(info.module, info.node.name)].append(info)

    def _resolve_helper(self, caller: FunctionInfo, name: str) -> FunctionInfo | None:
        if (caller.module, name) in self.functions_by_module:
            return self.functions_by_module[(caller.module, name)][0]
        imported = caller.aliases.get(name)
        if imported:
            module, imported_name = imported
            module_tail = module.rsplit(".", 1)[-1]
            for info in self.functions_by_name.get(imported_name, []):
                if info.path.stem == module_tail:
                    return info
        candidates = self.functions_by_name.get(name, [])
        return candidates[0] if len(candidates) == 1 else None

    def test_coverage(self) -> dict[str, set[str]]:
        covered: dict[str, set[str]] = defaultdict(set)
        for info in self.functions:
            if not info.node.name.startswith("test_"):
                continue
            initial = _parametrize_values(
                info.node,
                self.control_names,
                info.module_constants,
                self.dynamic_control_names,
            )
            _returned, clicked, _found = self._run_function(info, initial, set())
            for name in clicked:
                covered[name].add(f"{info.path.name}:{info.node.name}")
        return covered

    def _run_function(
        self,
        info: FunctionInfo,
        initial: dict[str, set[str]],
        call_stack: set[int],
        inherited_found: set[str] | None = None,
    ) -> tuple[set[str], set[str], set[str]]:
        if id(info.node) in call_stack:
            return set(), set(), set()
        stack = call_stack | {id(info.node)}
        env = {name: set(values) for name, values in initial.items()}
        clicked: set[str] = set()
        found: set[str] = set(inherited_found or set())
        return_values: set[str] = set()

        def expression(node: ast.AST | None) -> set[str]:
            nonlocal clicked, found
            if node is None:
                return set()
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                return _matching_control_names(node.value, self.control_names, self.dynamic_control_names)
            if isinstance(node, ast.Name):
                return set(env.get(node.id, set()))
            if isinstance(node, (ast.List, ast.Tuple, ast.Set)):
                values: set[str] = set()
                for item in node.elts:
                    values.update(expression(item))
                return values
            if isinstance(node, ast.IfExp):
                return expression(node.body) | expression(node.orelse)
            if isinstance(node, ast.Call):
                name = _dotted_name(node.func)
                method = name.rsplit(".", 1)[-1]
                arg_values: list[set[str]] = [expression(arg) for arg in node.args]
                kw_values: list[set[str]] = [expression(kw.value) for kw in node.keywords]
                receiver = name.rsplit(".", 1)[0] if "." in name else ""
                qtest_alias = info.aliases.get(receiver) == ("PySide6.QtTest", "QTest")
                imported_input = info.aliases.get(method) == ("PySide6.QtTest", method)
                if method in INPUT_METHODS and (
                    receiver == "QTest"
                    or qtest_alias
                    or imported_input
                    or receiver in {"qtbot", "bot"}
                ):
                    for value in arg_values + kw_values:
                        clicked.update(value)
                    if method in {"keyClick", "keyClicks"}:
                        clicked.update(
                            name
                            for name in found
                            if self.control_types.get(name, set()) & {"Shortcut", "Action"}
                        )
                    if method in {"mouseClick", "mousePress", "mouseDClick", "mouseMove"}:
                        clicked.update(
                            name
                            for name in found
                            if self.control_types.get(name, set()) & {"MouseArea", "TapHandler"}
                        )
                    return set()
                if method in {"findChild", "findChildren", "find_child", "get_child"}:
                    values: set[str] = set()
                    for candidate in arg_values + kw_values:
                        values.update(candidate)
                    found.update(values)
                    return values
                helper_name = node.func.id if isinstance(node.func, ast.Name) else ""
                helper = self._resolve_helper(info, helper_name) if helper_name else None
                if helper:
                    positional = [*node.args]
                    helper_env: dict[str, set[str]] = {}
                    params = [
                        *helper.node.args.posonlyargs,
                        *helper.node.args.args,
                    ]
                    for index, param in enumerate(params):
                        if index < len(positional):
                            helper_env[param.arg] = set(arg_values[index])
                    for keyword in node.keywords:
                        for param in params:
                            if keyword.arg == param.arg:
                                helper_env[param.arg] = expression(keyword.value)
                    returned, helper_clicked, helper_found = self._run_function(
                        helper, helper_env, stack, found
                    )
                    if not returned and any(
                        isinstance(child, ast.Call)
                        and isinstance(child.func, ast.Attribute)
                        and child.func.attr == "objectName"
                        for child in ast.walk(helper.node)
                    ):
                        returned.update(value for values in arg_values for value in values)
                    clicked.update(helper_clicked)
                    found.update(helper_found)
                    return returned
                # Geometry helpers preserve the identity of the item whose point
                # is passed to QTest.mouseClick(window, ..., point).
                if method.startswith("mapTo") or method in {"position", "centerIn"}:
                    values = set()
                    if isinstance(node.func, ast.Attribute):
                        values.update(expression(node.func.value))
                    for candidate in arg_values:
                        values.update(candidate)
                    return values
                # Arithmetic and QPoint/QPointF constructors retain provenance
                # from an item when a test clicks the parent window at its point.
                values: set[str] = set()
                for candidate in arg_values + kw_values:
                    values.update(candidate)
                if isinstance(node.func, ast.Attribute):
                    values.update(expression(node.func.value))
                return values
            if isinstance(node, ast.Attribute):
                return expression(node.value)
            if isinstance(node, ast.BinOp):
                return expression(node.left) | expression(node.right)
            if isinstance(node, ast.UnaryOp):
                return expression(node.operand)
            if isinstance(node, ast.Lambda):
                return expression(node.body)
            return set()

        def assign(target: ast.AST, values: set[str]) -> None:
            if isinstance(target, ast.Name):
                env[target.id] = set(values)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for item in target.elts:
                    assign(item, values)

        def run_statements(statements: list[ast.stmt]) -> None:
            nonlocal clicked, return_values
            for statement in statements:
                if isinstance(statement, ast.Assign):
                    values = expression(statement.value)
                    for target in statement.targets:
                        assign(target, values)
                elif isinstance(statement, ast.AnnAssign):
                    assign(statement.target, expression(statement.value))
                elif isinstance(statement, ast.AugAssign):
                    values = expression(statement.value) | expression(statement.target)
                    assign(statement.target, values)
                elif isinstance(statement, ast.Expr):
                    expression(statement.value)
                elif isinstance(statement, ast.Return):
                    return_values.update(expression(statement.value))
                elif isinstance(statement, ast.If):
                    expression(statement.test)
                    before = {key: set(value) for key, value in env.items()}
                    run_statements(statement.body)
                    then_env = {key: set(value) for key, value in env.items()}
                    env.clear()
                    env.update({key: set(value) for key, value in before.items()})
                    run_statements(statement.orelse)
                    else_env = {key: set(value) for key, value in env.items()}
                    env.clear()
                    for key in then_env.keys() | else_env.keys():
                        env[key] = then_env.get(key, set()) | else_env.get(key, set())
                elif isinstance(statement, (ast.For, ast.AsyncFor)):
                    iter_values = expression(statement.iter)
                    assign(statement.target, iter_values)
                    run_statements(statement.body)
                    run_statements(statement.orelse)
                elif isinstance(statement, (ast.With, ast.AsyncWith)):
                    for item in statement.items:
                        expression(item.context_expr)
                        if item.optional_vars:
                            assign(item.optional_vars, expression(item.context_expr))
                    run_statements(statement.body)
                elif isinstance(statement, ast.Try):
                    run_statements(statement.body)
                    run_statements(statement.orelse)
                    for handler in statement.handlers:
                        run_statements(handler.body)
                    run_statements(statement.finalbody)
                elif isinstance(statement, (ast.Assert, ast.Raise)):
                    expression(statement.test if isinstance(statement, ast.Assert) else statement.exc)
                elif isinstance(statement, ast.Match):
                    expression(statement.subject)
                    for case in statement.cases:
                        run_statements(case.body)

        run_statements(info.node.body)
        return return_values, clicked, found


def _audit(qml_root: Path, tests_root: Path) -> dict[str, object]:
    controls = _qml_controls(qml_root)
    control_types: dict[str, set[str]] = defaultdict(set)
    for control in controls:
        control_types[control.object_name].add(control.qml_type)
    dynamic_control_names = {control.object_name for control in controls if control.dynamic}
    functions = _collect_functions(tests_root)
    coverage = _TestInputAnalyzer(functions, control_types, dynamic_control_names).test_coverage()
    remaining_controls = [control for control in controls if control.object_name not in coverage]
    groups: dict[str, list[dict[str, object]]] = {group: [] for group in GROUP_ORDER}
    for control in remaining_controls:
        groups[control.group].append(asdict(control))
    for entries in groups.values():
        entries.sort(key=lambda item: (str(item["file"]), int(item["line"]), str(item["object_name"])))
    covered = len(controls) - len(remaining_controls)
    return {
        "total": len(controls),
        "covered": covered,
        "remaining": len(remaining_controls),
        "groups": groups,
        "coverage": {
            control.object_name: sorted(coverage.get(control.object_name, set()))
            for control in controls
            if control.object_name in coverage
        },
    }


def _text_report(report: dict[str, object]) -> str:
    lines = [
        "Valódi kattintásos QML-vezérlő audit",
        f"Összesen: {report['total']} · valódi bemenettel fedett: {report['covered']} · maradék: {report['remaining']}",
    ]
    groups = report["groups"]
    assert isinstance(groups, dict)
    for group in GROUP_ORDER:
        entries = groups[group]
        if not entries:
            continue
        by_file: dict[str, list[dict[str, object]]] = defaultdict(list)
        for entry in entries:
            by_file[str(entry["file"])].append(entry)
        lines.append(f"\n{group}")
        for filename, file_entries in by_file.items():
            lines.append(f"- {filename} [{len(file_entries)}]: ")
            lines.append(
                "  "
                + ", ".join(
                    f"{entry['object_name']}{'…' if entry['dynamic'] else ''}:{entry['line']}"
                    for entry in file_entries
                )
            )
    if int(report["remaining"]) == 0:
        lines.append("\nNincs fedetlen vezérlő.")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    root = Path(__file__).resolve().parents[1]
    parser.add_argument("--qml-root", type=Path, default=root / "src/picasapy/app/qml")
    parser.add_argument("--tests-root", type=Path, default=root / "tests/app")
    parser.add_argument("--json", action="store_true", help="géppel feldolgozható JSON kimenet")
    args = parser.parse_args()
    # Windowson a konzol kódolása cp1252; az ékezetes kimenet UTF-8-ban menjen.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
    for directory in (args.qml_root, args.tests_root):
        if not directory.is_dir():
            parser.error(f"nem létező könyvtár: {directory}")
    report = _audit(args.qml_root, args.tests_root)
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(_text_report(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
