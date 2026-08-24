#!/usr/bin/env python3
"""A `SAJÁT FUNKCIÓ` jelölés őre — #1187.

**A hibaosztály.** A projekt módszertana a Windows-os Picasa binárisát
tekinti mércének: ha a kódunk eltér tőle, az az alapeset szerint HIBA. Ez
alól kivétel a SZÁNDÉKOSAN hozzáadott, nem eredeti funkció (pl. a
szerkesztő 7 effekt-füle az eredeti 5 helyett) — ott az eltérés a terv, nem
hiba. Ezeket a `SAJÁT FUNKCIÓ` kulcsszóval jelöljük a kódban/specben, és
felvesszük a `docs/decisions/vedett-sajat-funkciok.md` jegyzékbe (ld.
`docs/specs/binaris-regeszet-modszertan.md` 17. szakasza).

A jegyzék és a kód azonban **szétcsúszhat** két irányban, és mindkettő
némán történik — sem a jelölés, sem a hiánya nem hibázik le semmit:

1. **A jegyzék tétele elárvul.** A fájlt átnevezik/törlik, vagy a jelölő
   megjegyzést valaki „megtisztítja" a kódból egy refaktornál — a jegyzék
   ezután egy nem létező védelemre hivatkozik, ami hamis biztonságérzetet
   ad („ez már fel van véve, nem kell vele foglalkozni").
2. **A kódba kerül egy új jelölés, ami nincs a jegyzékben.** Valaki a
   mintát követve tesz ki egy `SAJÁT FUNKCIÓ` megjegyzést, de elfelejti
   felvenni a jegyzékbe — a jelölés így nem kereshető egy központi helyről,
   csak véletlen grep találja meg.

Ez a szkript mindkét irányt ellenőrzi. Az `EXCLUDED` fájlok (maga a
jegyzék és a módszertani szakasz) ki vannak véve a 2. irányú keresésből:
azok A KONVENCIÓRÓL beszélnek példákkal, nem egy konkrét eltérésről.

Használat::

    python scripts/check_protected_features.py

Kilépési kód: 0 ha nincs eltérés, 1 ha van, 2 ha a bemenet hibás (nincs
jegyzék-fájl, vagy egyetlen tételt sem sikerült beolvasni belőle).
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_DEFAULT_REGISTRY = _REPO_ROOT / "docs" / "decisions" / "vedett-sajat-funkciok.md"
_DEFAULT_ROOTS = (_REPO_ROOT / "src", _REPO_ROOT / "docs")
_SCAN_SUFFIXES = {".py", ".qml", ".md"}

#: A jelölő pontos, greppelhető alakja — ld. a jegyzék bevezetője.
MARKER = "SAJÁT FUNKCIÓ"

#: A módszertanról beszélő, nem konkrét esetet jelölő fájlok — ezeket a
#: 2. irányú (kód → jegyzék) ellenőrzés kihagyja, mert a `MARKER` bennük
#: PÉLDAKÉNT szerepel, nem egy tényleges eltérés jelöléseként.
EXCLUDED_FROM_REVERSE_CHECK = {
    "docs/decisions/vedett-sajat-funkciok.md",
    "docs/specs/binaris-regeszet-modszertan.md",
}

#: `- \`path/to/file.ext\` (#123[, #456]) — leírás`
_ENTRY = re.compile(r"^- `([^`]+)`\s*\(([^)]+)\)\s*—\s*(.+)$", re.M)


@dataclass(frozen=True)
class Entry:
    """Egy jegyzék-tétel: a hivatkozott hely, a jegyszám(ok), a leírás."""

    location: str
    issues: str
    description: str

    @property
    def path(self) -> str:
        """A puszta fájlútvonal — a `location` néha `fájl:sor` alakú."""
        path, _, _line = self.location.partition(":")
        return path


def _read_text(path: Path) -> str:
    """Fájl beolvasása; a nem UTF-8 bájtokat elnyeli, nem áll meg tőlük."""
    return path.read_text(encoding="utf-8", errors="replace")


def parse_registry(text: str) -> list[Entry]:
    """A jegyzék „Ismert esetek" listájának sorai."""
    return [
        Entry(location=m.group(1), issues=m.group(2), description=m.group(3))
        for m in _ENTRY.finditer(text)
    ]


def find_marked_files(roots: tuple[Path, ...], base: Path) -> set[str]:
    """A `MARKER`-t tartalmazó fájlok, a `base`-hez képesti, POSIX útvonalon."""
    found: set[str] = set()
    for root in roots:
        if not root.is_dir():
            continue
        for path in sorted(root.rglob("*")):
            if not path.is_file() or path.suffix not in _SCAN_SUFFIXES:
                continue
            if MARKER in _read_text(path):
                found.add(path.relative_to(base).as_posix())
    return found


def check(registry_path: Path, roots: tuple[Path, ...], base: Path = _REPO_ROOT) -> int:
    """A kétirányú ellenőrzés. 0 = nincs eltérés.

    A `base` az, amihez képest a jegyzék fájlútvonalai értendők — éles
    futásnál a repó gyökere; a tesztek egy ideiglenes fát adnak át helyette.
    """
    if not registry_path.is_file():
        print(f"nincs jegyzék-fájl: {registry_path}", file=sys.stderr)
        return 2

    entries = parse_registry(_read_text(registry_path))
    if not entries:
        print(
            f"nem sikerült egyetlen tételt sem beolvasni: {registry_path}",
            file=sys.stderr,
        )
        return 2

    problems: list[str] = []
    registered_paths: set[str] = set()

    # 1. irány: minden jegyzék-tétel fájlja létezik, és tartalmazza a jelölőt.
    for entry in entries:
        registered_paths.add(entry.path)
        full = base / entry.path
        if not full.is_file():
            problems.append(
                f"nincs ilyen fájl: {entry.location} (#{entry.issues}) — "
                "árva jegyzék-tétel"
            )
            continue
        if MARKER not in _read_text(full):
            problems.append(
                f"{entry.location} (#{entry.issues}): nincs benne a(z) "
                f"„{MARKER}” jelölő"
            )

    # 2. irány: minden jelölt fájl szerepel a jegyzékben.
    marked = find_marked_files(roots, base) - EXCLUDED_FROM_REVERSE_CHECK
    for path in sorted(marked - registered_paths):
        problems.append(
            f"{path}: van „{MARKER}” jelölés a fájlban, de nincs hozzá "
            "jegyzék-tétel"
        )

    if problems:
        print(f"{len(problems)} probléma a védett-funkció jelölésben:\n")
        for problem in problems:
            print(f"  - {problem}")
        return 1

    print(
        f"Rendben: {len(entries)} jegyzék-tétel, mind jelölve a kódban/"
        "specben, jelöletlenül maradt fájl nincs."
    )
    return 0


def main(argv: list[str] | None = None) -> int:
    """Parancssori belépési pont."""
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument(
        "--registry",
        type=Path,
        default=_DEFAULT_REGISTRY,
        help="a jegyzék-fájl útvonala",
    )
    parser.add_argument(
        "--roots",
        type=Path,
        nargs="+",
        default=None,
        help="a vizsgált fák (alapértelmezés: src/ és docs/)",
    )
    parser.add_argument(
        "--base",
        type=Path,
        default=_REPO_ROOT,
        help="mihez képest értendők a jegyzék fájlútvonalai (alapértelmezés: a repó gyökere)",
    )
    args = parser.parse_args(argv)
    roots = tuple(args.roots) if args.roots else _DEFAULT_ROOTS
    return check(args.registry, roots, args.base)


if __name__ == "__main__":
    raise SystemExit(main())
