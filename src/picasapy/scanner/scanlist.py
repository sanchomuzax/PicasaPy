"""Picasa-kompatibilis ``scanlist.txt`` olvasása és teljes újraírása.

A fájl három, sorrendtartó szakasza: konkrét egyszer beolvasott mappák,
``-`` előtagú kizáró gyökerek, majd ``+`` előtagú befoglaló gyökerek.
"""

from __future__ import annotations

from pathlib import Path

SCAN_LIST_NAME = "scanlist.txt"


def read_scan_list(
    path: str | Path,
) -> tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]:
    file_path = Path(path)
    try:
        lines = file_path.read_text(encoding="utf-8-sig").splitlines()
    except OSError:
        return (), (), ()
    scanned: list[str] = []
    excluded: list[str] = []
    included: list[str] = []
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if line.startswith("-"):
            excluded.append(line[1:])
        elif line.startswith("+"):
            included.append(line[1:])
        else:
            scanned.append(line)
    return tuple(scanned), tuple(excluded), tuple(included)


def write_scan_list(
    path: str | Path,
    scanned: tuple[str, ...],
    excluded: tuple[str, ...],
    included: tuple[str, ...],
) -> None:
    """A teljes fájl atomnyi logikai egységként, nem hozzáfűzve íródik."""
    file_path = Path(path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    content = "".join(f"{item}\n" for item in scanned)
    content += "".join(f"-{item}\n" for item in excluded)
    content += "".join(f"+{item}\n" for item in included)
    file_path.write_text(content, encoding="utf-8")
