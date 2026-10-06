#!/usr/bin/env python3
"""A QML-oldali néma vezérlők statikus őre — #4438.

Az őr a látható UI-hoz közeli három kockázatot tartja szemmel:

* üres, illetve csak ``console.log``-ot végző kattintás/menükezelő;
* forrásban állandóra ``enabled: false`` tett elem;
* olyan QML-jelzés, amelynek nincs QML-kezelője és Python ``connect``-je.

A meglévő, indokolt letiltások és jelzések a baseline-ban vannak. A baseline
csak fogyhat; új sor engedélyezéséhez a felső korlátot is tudatosan kellene
módosítani. Ez az ellenőrzés szándékosan nem vizsgál Python-oldali slotokat.
"""

from __future__ import annotations

import argparse
import re
import sys
from collections import Counter
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_BASELINE = Path(__file__).with_name("silent_qml_controls_baseline.txt")
_QML_ROOT = Path("src/picasapy/app/qml")

# A plafon az auditkor megállapított baseline mérete. Csak csökkenthető.
MAX_BASELINE_ENTRIES = 40

_HANDLER = re.compile(r"\b(onClicked|onTriggered)\s*:")
_SIGNAL = re.compile(r"\bsignal\s+(\w+)\s*\(")
_DISABLED = re.compile(r"\benabled\s*:\s*false\b")


@dataclass(frozen=True, order=True)
class Finding:
    """Egy gépi jelölt, a baseline-kulccsal és a helyével."""

    category: str
    key: str
    path: str
    line: int
    description: str


def _mask_comments_and_strings(source: str) -> str:
    """A kommenteket és idézett szövegeket azonos hosszú szóközre cseréli."""
    out = list(source)
    i = 0
    state = "code"
    quote = ""
    while i < len(source):
        char = source[i]
        following = source[i + 1] if i + 1 < len(source) else ""
        if state == "code":
            if char == "/" and following == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "line-comment"
                continue
            if char == "/" and following == "*":
                out[i] = out[i + 1] = " "
                i += 2
                state = "block-comment"
                continue
            if char in ('"', "'", "`"):
                quote = char
                out[i] = " "
                state = "string"
        elif state == "line-comment":
            if char == "\n":
                state = "code"
            else:
                out[i] = " "
        elif state == "block-comment":
            if char == "*" and following == "/":
                out[i] = out[i + 1] = " "
                i += 2
                state = "code"
                continue
            if char != "\n":
                out[i] = " "
        else:  # quoted string
            out[i] = " "
            if char == "\\":
                if i + 1 < len(source):
                    if source[i + 1] != "\n":
                        out[i + 1] = " "
                    i += 2
                    continue
            elif char == quote:
                state = "code"
        i += 1
    return "".join(out)


def _matching_brace(masked: str, opening: int) -> int | None:
    depth = 0
    for index in range(opening, len(masked)):
        if masked[index] == "{":
            depth += 1
        elif masked[index] == "}":
            depth -= 1
            if depth == 0:
                return index
    return None


def _object_block_spans(masked: str, type_name: str) -> list[tuple[int, int]]:
    """A megadott QML-típus objektumtörzseinek határai."""
    start_pattern = re.compile(r"\b" + re.escape(type_name) + r"\s*\{")
    spans: list[tuple[int, int]] = []
    for match in start_pattern.finditer(masked):
        opening = masked.find("{", match.start(), match.end())
        closing = _matching_brace(masked, opening)
        if closing is not None:
            spans.append((opening + 1, closing))
    return spans


def _object_blocks(masked: str, type_name: str) -> list[str]:
    """A megadott QML-típus objektumtörzsei a forrásban."""
    return [masked[start:end] for start, end in _object_block_spans(masked, type_name)]


def _signal_owner_type(owner_path: Path, masked: str, position: int) -> str:
    """Az inline QML-komponens neve, vagy a fájlnevet adó gyökérkomponens."""
    declarations = re.compile(
        r"\bcomponent\s+(\w+)\s*:\s*[A-Z]\w*\s*\{"
    )
    containing: list[tuple[int, str]] = []
    for match in declarations.finditer(masked):
        opening = masked.find("{", match.start(), match.end())
        closing = _matching_brace(masked, opening)
        if closing is not None and opening < position < closing:
            containing.append((closing - opening, match.group(1)))
    return min(containing)[1] if containing else owner_path.stem


def _has_top_level_handler(masked_block: str, handler: str) -> bool:
    """A handler közvetlenül az adott QML-objektum tulajdonsága-e."""
    pattern = re.compile(
        r"\b(?:function\s+)?" + re.escape(handler) + r"\s*(?=:|\()"
    )
    for match in pattern.finditer(masked_block):
        depth = 0
        for char in masked_block[: match.start()]:
            if char == "{":
                depth += 1
            elif char == "}":
                depth -= 1
        if depth == 0:
            return True
    return False


def _root_body(masked: str) -> str:
    """The top-level QML object body, if the file has one."""
    match = re.search(r"(?m)^[ \t]*[A-Z]\w*\s*\{", masked)
    if not match:
        return ""
    opening = masked.find("{", match.start(), match.end())
    closing = _matching_brace(masked, opening)
    return masked[opening + 1 : closing] if closing is not None else ""


def _qml_handler_receives(
    owner_path: Path,
    name: str,
    owner_type: str,
    qml_sources: dict[Path, tuple[str, str]],
) -> bool:
    """QML-oldali fogadót keres a jelzést deklaráló komponensen.

    A puszta, bárhol előforduló `onX` név nem fogadó: egy másik QML-típus
    ugyanolyan nevű jelzése nem fedheti el ezt a jelzést.
    """
    handler = "on" + name[:1].upper() + name[1:]
    _, owner_masked = qml_sources[owner_path]
    root_body = _root_body(owner_masked)
    if owner_type == owner_path.stem and _has_top_level_handler(root_body, handler):
        return True

    aliases_by_file: dict[Path, set[str]] = {}
    if owner_type == owner_path.stem:
        root_id = re.search(r"\bid\s*:\s*(\w+)\b", root_body)
        if root_id:
            aliases_by_file.setdefault(owner_path, set()).add(root_id.group(1))

    for path, (_, masked) in qml_sources.items():
        for body in _object_blocks(masked, owner_type):
            if _has_top_level_handler(body, handler):
                return True
            identifier = re.search(r"\bid\s*:\s*(\w+)\b", body)
            if identifier:
                aliases_by_file.setdefault(path, set()).add(identifier.group(1))

    for path, (_, masked) in qml_sources.items():
        aliases = aliases_by_file.get(path, set())
        for body in _object_blocks(masked, "Connections"):
            target = re.search(r"\btarget\s*:\s*([\w.]+)", body)
            if not target or target.group(1).split(".")[-1] not in aliases:
                continue
            if _has_top_level_handler(body, handler):
                return True

    # A Loader does not spell the loaded type as a QML object (its target is
    # `loaderId.item`), so follow literal `<Type>.qml` sources explicitly.
    # This covers the production VideoPlayerView and SlideshowMusicPlayer
    # components without treating an unrelated same-named Connections handler
    # as a consumer.
    component_file = re.compile(
        r"[\"'][^\"']*(?:[/\\])?" + re.escape(owner_type) + r"\.qml[\"']"
    )
    for _path, (source, masked) in qml_sources.items():
        for start, end in _object_block_spans(masked, "Loader"):
            if not component_file.search(source[start:end]):
                continue
            body = masked[start:end]
            identifier = re.search(r"\bid\s*:\s*(\w+)\b", body)
            if not identifier:
                continue
            loader_id = identifier.group(1)
            for connections in _object_blocks(masked, "Connections"):
                target = re.search(r"\btarget\s*:\s*([\w.]+)", connections)
                if (
                    target
                    and target.group(1) == f"{loader_id}.item"
                    and _has_top_level_handler(connections, handler)
                ):
                    return True
    return False


def _only_console_logs(source: str) -> bool:
    """Igaz, ha a kezelő törzse csak nulla vagy több console.log-hívás."""
    masked = _mask_comments_and_strings(source)
    i = 0
    logs = 0
    while i < len(masked):
        while i < len(masked) and (masked[i].isspace() or masked[i] == ";"):
            i += 1
        if i == len(masked):
            return True
        if not masked.startswith("console.log", i):
            return False
        i += len("console.log")
        while i < len(masked) and masked[i].isspace():
            i += 1
        if i >= len(masked) or masked[i] != "(":
            return False
        depth = 0
        while i < len(masked):
            if masked[i] == "(":
                depth += 1
            elif masked[i] == ")":
                depth -= 1
                if depth == 0:
                    i += 1
                    break
            i += 1
        if depth != 0:
            return False
        logs += 1
    # A completely empty (or whitespace-only) body is silent as well.
    return True


def _handler_is_silent(source: str, masked: str, match: re.Match[str]) -> bool:
    value_start = match.end()
    while value_start < len(masked) and masked[value_start].isspace():
        value_start += 1
    if value_start == len(masked):
        return True
    if masked[value_start] == "{":
        closing = _matching_brace(masked, value_start)
        if closing is None:
            return False
        body = source[value_start + 1 : closing]
        return _only_console_logs(body)

    # A property-alak végét a sorvég, pontosvessző vagy a QML-objektum záró
    # kapcsosa jelöli. Függvény- és nyílfüggvény-törzsek is lehetnek benne.
    end = value_start
    parentheses = 0
    braces = 0
    while end < len(masked):
        char = masked[end]
        if char == "(":
            parentheses += 1
        elif char == ")":
            parentheses = max(0, parentheses - 1)
        elif char == "{":
            braces += 1
        elif char == "}":
            if braces == 0 and parentheses == 0:
                break
            braces = max(0, braces - 1)
        elif char in (";", "\n") and parentheses == 0 and braces == 0:
            break
        end += 1

    expression_masked = masked[value_start:end]
    expression_source = source[value_start:end]
    function_body = re.match(r"\s*function\b[^{}]*\{", expression_masked)
    arrow = expression_masked.find("=>")
    if function_body:
        opening = value_start + function_body.end() - 1
        closing = _matching_brace(masked, opening)
        if closing is None:
            return False
        return _only_console_logs(source[opening + 1 : closing])
    if arrow >= 0:
        arrow_body_start = arrow + 2
        while (
            arrow_body_start < len(expression_masked)
            and expression_masked[arrow_body_start].isspace()
        ):
            arrow_body_start += 1
        if arrow_body_start < len(expression_masked) and expression_masked[
            arrow_body_start
        ] == "{":
            opening = value_start + arrow_body_start
            closing = _matching_brace(masked, opening)
            if closing is None:
                return False
            return _only_console_logs(source[opening + 1 : closing])
        return _only_console_logs(expression_source[arrow_body_start:])
    return _only_console_logs(expression_source)


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def scan(repo_root: Path) -> list[Finding]:
    """A QML-fát és az alkalmazáskód .py fájljait bejárva jelölteket gyűjt."""
    qml_root = repo_root / _QML_ROOT
    if not qml_root.is_dir():
        raise FileNotFoundError(f"Hiányzó QML-gyökér: {qml_root}")

    qml_sources: dict[Path, tuple[str, str]] = {}
    for path in sorted(qml_root.rglob("*.qml")):
        source = _read(path)
        qml_sources[path] = (source, _mask_comments_and_strings(source))

    app_root = repo_root / "src" / "picasapy" / "app"
    all_python = "\n".join(
        _mask_comments_and_strings(_read(path))
        for path in sorted(app_root.rglob("*.py"))
    )
    findings: list[Finding] = []

    for path, (source, masked) in qml_sources.items():
        relative = path.relative_to(repo_root).as_posix()
        for match in _HANDLER.finditer(masked):
            if _handler_is_silent(source, masked, match):
                line = masked.count("\n", 0, match.start()) + 1
                handler = match.group(1)
                findings.append(
                    Finding(
                        "silent-handler",
                        f"{relative}:{line}:{handler}",
                        relative,
                        line,
                        "üres vagy csak console.log-ot végző kezelő",
                    )
                )

        for match in _DISABLED.finditer(masked):
            line = masked.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    "constant-disabled",
                    f"{relative}:{line}:enabled=false",
                    relative,
                    line,
                    "állandóra letiltott QML-elem",
                )
            )

        for match in _SIGNAL.finditer(masked):
            name = match.group(1)
            owner_type = _signal_owner_type(path, masked, match.start())
            if _qml_handler_receives(path, name, owner_type, qml_sources):
                continue
            connected = re.search(
                r"\b" + re.escape(name) + r"\s*\.\s*connect\s*\(",
                "\n".join(masked for _, masked in qml_sources.values())
                + "\n"
                + all_python,
            )
            if connected:
                continue
            line = masked.count("\n", 0, match.start()) + 1
            findings.append(
                Finding(
                    "unbound-signal",
                    f"{relative}::{name}",
                    relative,
                    line,
                    "nincs QML-kezelője vagy produkciós .connect fogadója",
                )
            )

    return sorted(findings)


def load_baseline(path: Path) -> dict[tuple[str, str], str]:
    """A kategória, kulcs és indoklás tételes alapállapotát olvassa be."""
    entries: dict[tuple[str, str], str] = {}
    for number, raw in enumerate(_read(path).splitlines(), start=1):
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        fields = line.split("\t", 2)
        if len(fields) != 3 or not all(value.strip() for value in fields):
            raise ValueError(f"Hibás baseline-sor ({path}:{number}): {raw!r}")
        category, key, reason = (field.strip() for field in fields)
        identity = (category, key)
        if identity in entries:
            raise ValueError(f"Kétszer szereplő baseline-tétel ({path}:{number}): {key}")
        entries[identity] = reason
    if len(entries) > MAX_BASELINE_ENTRIES:
        raise ValueError(
            f"A QML-baseline {len(entries)} tételes, a felső korlát "
            f"{MAX_BASELINE_ENTRIES}; csak csökkenthető."
        )
    return entries


_SORSZAM = re.compile(r":\d+:")


def _sor_nelkul(identity: tuple[str, str]) -> tuple[str, str]:
    """A kulcs sorszám nélkül: egy fölötte beszúrt sor ne tegye a tételt
    „újjá" és „elavulttá" egyszerre. Ugyanabban a fájlban több azonos
    fajtájú tétel is lehet, ezért az összevetés darabszámra megy."""
    category, key = identity
    return category, _SORSZAM.sub(":", key, count=1)


def compare(
    findings: list[Finding], baseline: dict[tuple[str, str], str]
) -> tuple[list[Finding], list[tuple[str, str]]]:
    maradek = Counter(_sor_nelkul(key) for key in baseline)
    new: list[Finding] = []
    for finding in sorted(findings):
        kulcs = _sor_nelkul((finding.category, finding.key))
        if maradek[kulcs] > 0:
            maradek[kulcs] -= 1
        else:
            new.append(finding)
    stale: list[tuple[str, str]] = []
    for key in sorted(baseline):
        kulcs = _sor_nelkul(key)
        if maradek[kulcs] > 0:
            maradek[kulcs] -= 1
            stale.append(key)
    return new, stale


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=_REPO_ROOT, help="a repó gyökere")
    parser.add_argument(
        "--baseline", type=Path, default=_DEFAULT_BASELINE, help="indokolt alapállapot"
    )
    parser.add_argument("--list", action="store_true", help="minden mai jelölt kiírása")
    args = parser.parse_args(argv)

    try:
        findings = scan(args.root)
    except (OSError, ValueError) as exc:
        print(f"HIBA: {exc}", file=sys.stderr)
        return 2

    if args.list:
        for finding in findings:
            print(
                f"{finding.category}\t{finding.key}\t"
                f"{finding.description}"
            )
        return 0

    try:
        baseline = load_baseline(args.baseline)
    except (OSError, ValueError) as exc:
        print(f"HIBA: {exc}", file=sys.stderr)
        return 2

    new, stale = compare(findings, baseline)
    if new or stale:
        if new:
            print(f"ÚJ QML-jelölt ({len(new)}):")
            for finding in new:
                print(f"  {finding.category}\t{finding.key}\t{finding.description}")
        if stale:
            print(f"ELAVULT QML-baseline ({len(stale)}):")
            for category, key in stale:
                print(f"  {category}\t{key}")
        return 1

    print(
        f"Rendben: a {len(findings)} QML-jelölt mindegyike indokolt baseline-tétel."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
