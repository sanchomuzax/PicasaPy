"""Verzió- és build-azonosító a futó példány pontos azonosításához.

A csomag verziója (``__version__``) az igazságforrás; a build-azonosítót
futásidőben a git adja (commit-szám + rövid hash), hogy egy fejlesztői
példányról is látsszon, PONTOSAN melyik commit fut. Ahol a git nem érhető
el (telepített csomag, tarball), a build csendben ``"dev"`` lesz — ez soha
nem akadályozhatja az indulást.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

from picasapy import __version__

# A repó gyökere: src/picasapy/version.py → parents[2]
_REPO_ROOT = Path(__file__).resolve().parents[2]


def _git(*args: str) -> str | None:
    """Egy git-parancs kimenete a repó gyökeréből, vagy None hiba esetén."""
    try:
        out = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), *args],
            capture_output=True,
            text=True,
            timeout=5,
            check=True,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    value = out.stdout.strip()
    return value or None


def build_number() -> str | None:
    """Monoton build-szám: a HEAD-ig vezető commitok száma (vagy None)."""
    return _git("rev-list", "--count", "HEAD")


def build_id() -> str | None:
    """A HEAD rövid commit-hash-e (vagy None, ha nincs git)."""
    return _git("rev-parse", "--short", "HEAD")


def build_label() -> str:
    """Ember-olvasható build-címke: ``"<szám>.<hash>"``, vagy ``"dev"``.

    Ha csak az egyik elérhető, azt adjuk vissza; ha egyik sem, ``"dev"``.
    """
    number = build_number()
    commit = build_id()
    if number and commit:
        return f"{number}.{commit}"
    return number or commit or "dev"


def version_string() -> str:
    """A fejlécben megjelenő címke, pl. ``"v0.4.0 (81.3706d78)"``."""
    return f"v{__version__} ({build_label()})"
