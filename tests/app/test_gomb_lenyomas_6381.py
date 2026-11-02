"""#6381: a gombok lenyomása azonnal látható legyen."""

from __future__ import annotations

import re

import pytest


_GOMB_TIPUSOK = (
    "PicasaButton",
    "Button",
    "ToolButton",
    "RoundButton",
    "CheckBox",
    "RadioButton",
    "TabButton",
    "AbstractButton",
    "MouseArea",
    "TapHandler",
)
_GOMB_MINTA = re.compile(
    r"(?m)^(?P<indent>[ \t]*)(?P<type>"
    + "|".join(sorted(_GOMB_TIPUSOK, key=len, reverse=True))
    + r")\s*\{"
)


@pytest.fixture
def app_module():
    import picasapy.app.application as module

    return module


def _zarojel_par(text: str, opening: int) -> int:
    """A QML objektum záró kapcsos zárójelét keresi, kommenteket kihagyva."""
    depth = 0
    quote = ""
    escaped = False
    line_comment = False
    block_comment = False
    index = opening
    while index < len(text):
        char = text[index]
        next_char = text[index + 1] if index + 1 < len(text) else ""
        if line_comment:
            if char == "\n":
                line_comment = False
            index += 1
            continue
        if block_comment:
            if char == "*" and next_char == "/":
                block_comment = False
                index += 2
            else:
                index += 1
            continue
        if quote:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == quote:
                quote = ""
            index += 1
            continue
        if char == "/" and next_char == "/":
            line_comment = True
            index += 2
            continue
        if char == "/" and next_char == "*":
            block_comment = True
            index += 2
            continue
        if char in {'"', "'"}:
            quote = char
        elif char == "{":
            depth += 1
        elif char == "}":
            depth -= 1
            if depth == 0:
                return index + 1
        index += 1
    return len(text)


def _kozvetlen_object_name(block: str, indent: str) -> str | None:
    """A vezérlő közvetlen objectName értékét veszi, nem egy gyermekét."""
    property_indent = indent + "    "
    pattern = re.compile(
        rf"(?m)^{re.escape(property_indent)}objectName\s*:\s*(.*?)\s*$"
    )
    match = pattern.search(block)
    return match.group(1).strip() if match else None


def qml_gomb_leltar(app_module) -> tuple[dict[str, object], ...]:
    """Felsorolja a QML-gombokat típus, fájl, objectName és sor szerint."""
    qml_root = app_module._APP_DIR / "qml"
    entries = []
    for path in sorted(qml_root.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        for match in _GOMB_MINTA.finditer(source):
            block_end = _zarojel_par(source, match.end() - 1)
            block = source[match.start() : block_end]
            type_name = match.group("type")
            if type_name in {"MouseArea", "TapHandler"} and not re.search(
                r"\bon(?:Clicked|Tapped|Pressed)\s*:", block
            ):
                continue
            line = source.count("\n", 0, match.start()) + 1
            object_name = _kozvetlen_object_name(block, match.group("indent"))
            entries.append(
                {
                    "file": path.relative_to(qml_root).as_posix(),
                    "objectName": object_name or f"<névtelen:{line}>",
                    "type": type_name,
                    "line": line,
                }
            )
    return tuple(entries)


def test_a_qml_gombleltar_fajlt_es_objectname_erteket_ad(app_module):
    leltar = qml_gomb_leltar(app_module)

    assert len(leltar) >= 400, f"a gombleltár hiányos: {len(leltar)} elem"
    assert all(entry["file"] and entry["objectName"] for entry in leltar)
    assert {entry["type"] for entry in leltar} >= {
        "PicasaButton",
        "Button",
        "CheckBox",
        "RadioButton",
        "MouseArea",
        "TapHandler",
    }
def test_a_sajat_hatterrel_rajzolt_vezérlok_kezelik_a_lenyomott_allapotot(
    app_module,
):
    qml_root = app_module._APP_DIR / "qml"
    hibak = []
    for path in sorted(qml_root.rglob("*.qml")):
        source = path.read_text(encoding="utf-8")
        for match in _GOMB_MINTA.finditer(source):
            if match.group("type") not in {
                "PicasaButton",
                "Button",
                "ToolButton",
                "RoundButton",
                "CheckBox",
                "RadioButton",
                "TabButton",
                "AbstractButton",
            }:
                continue
            block = source[match.start() : _zarojel_par(source, match.end() - 1)]
            has_custom_background = re.search(r"(?m)^\s*background\s*:", block)
            overrides_background = re.search(
                r"(?m)^\s*background\s*:\s*null\s*$", block
            )
            has_pressed_visual = re.search(
                r"\b(?:down|pressed|visiblyDown)\b", block, re.IGNORECASE
            )
            if (has_custom_background or overrides_background) and not has_pressed_visual:
                line = source.count("\n", 0, match.start()) + 1
                object_name = _kozvetlen_object_name(block, match.group("indent"))
                hibak.append(
                    f"{path.relative_to(qml_root)}:{line} "
                    f"{object_name or match.group('type')}"
                )

    assert not hibak, "lenyomásra nem reagáló saját vezérlő-háttér:\n" + "\n".join(hibak)
