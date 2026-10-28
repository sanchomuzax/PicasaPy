"""Leltárőr: a QML-ben maradó világos színállandók csak fogyhatnak (#6125)."""

from collections import Counter
from pathlib import Path
import re


_BINDING = re.compile(
    r"\b(?:border\.color|placeholderTextColor|selectedTextColor|"
    r"highlightedTextColor|styleColor|fillStyle|strokeStyle|color)\s*:\s*([^;]+)"
)
_LITERAL = re.compile(r"(?P<quote>['\"])(?P<value>#[0-9a-fA-F]{3,8}|white)\1", re.I)

# path -> (maximalis darabszám, indoklás). A régi, még indokolt színek helye
# itt van; egy későbbi átvezetés törölheti vagy csökkentheti a keretet, növelni
# nem szabad. A Theme.qml token-definíciói nem részei a leltárnak.
REMAINING_FIXED_LIGHT_COLORS: dict[str, tuple[int, str]] = {}


def _is_fixed_light(value: str) -> bool:
    if value.lower() == "white":
        return True
    if not value.startswith("#"):
        return False
    digits = value[1:]
    if len(digits) == 3:
        rgb = "".join(char * 2 for char in digits)
    elif len(digits) == 6:
        rgb = digits
    elif len(digits) == 8:
        if digits[:2].lower() != "ff":
            return False
        rgb = digits[2:]
    else:
        return False
    red, green, blue = (int(rgb[offset : offset + 2], 16) for offset in (0, 2, 4))
    return (
        (red == green == blue and red >= 120)
        or value.lower().startswith(("#e", "#f"))
    )


def _fixed_light_occurrences(root: Path) -> Counter[str]:
    qml_root = root / "src/picasapy/app/qml"
    found: Counter[str] = Counter()
    for path in sorted(qml_root.rglob("*.qml")):
        if path.name == "Theme.qml":
            continue
        relative = path.relative_to(root).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.lstrip()
            if stripped.startswith(("//", "/*", "*")):
                continue
            for binding in _BINDING.finditer(line):
                expression = binding.group(1)
                # A literal in a dark/light binding is not a bypass: the
                # Theme.dark branch supplies the paired dark value.
                if "Theme.dark" in expression:
                    continue
                for literal in _LITERAL.finditer(expression):
                    if _is_fixed_light(literal.group("value")):
                        found[relative] += 1
    return found


def test_remaining_fixed_light_colors_are_reasoned_and_only_decrease():
    root = Path(__file__).resolve().parents[2]
    found = _fixed_light_occurrences(root)
    unlisted = sorted(set(found) - set(REMAINING_FIXED_LIGHT_COLORS))
    over_budget = {
        path: (count, REMAINING_FIXED_LIGHT_COLORS[path][0])
        for path, count in found.items()
        if path in REMAINING_FIXED_LIGHT_COLORS
        and count > REMAINING_FIXED_LIGHT_COLORS[path][0]
    }
    empty_reasons = [
        path
        for path, (_, reason) in REMAINING_FIXED_LIGHT_COLORS.items()
        if not reason.strip()
    ]
    assert not unlisted and not over_budget and not empty_reasons, (
        f"Indoklás nélküli világos színállandó: {unlisted}; "
        f"leltárkeret túllépése (tényleges, engedélyezett): {over_budget}; "
        f"üres indoklás: {empty_reasons}"
    )

