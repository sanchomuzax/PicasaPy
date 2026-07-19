"""Útvonal-átírás: Windows-os db3-útvonalak leképezése helyi útvonalakra.

A db3-ban minden útvonal abszolút Windows-formátumú (`C:\\Users\\...`), ezért
az import más gépen/OS-en csak átíró szabályokkal használható (7. rögzített
döntés: ismételhető migráció). A prefix-illesztés kis-nagybetű-független
(Windows-fájlrendszer), és mindig a leghosszabb illeszkedő szabály nyer.
"""

from __future__ import annotations

from collections.abc import Mapping


def _normalize(path: str) -> str:
    return path.replace("\\", "/").rstrip("/")


class PathRemapper:
    """Prefix-alapú útvonal-átíró (forrásprefix → célprefix szabályokkal)."""

    def __init__(self, rules: Mapping[str, str]) -> None:
        normalized = [
            (_normalize(source), _normalize(target))
            for source, target in rules.items()
        ]
        # Leghosszabb prefix elöl, hogy az első találat nyerjen.
        self._rules = tuple(
            sorted(normalized, key=lambda rule: len(rule[0]), reverse=True)
        )

    def remap(self, path: str) -> str | None:
        """A `path` helyi megfelelője, vagy None, ha nincs illeszkedő szabály."""
        normalized = _normalize(path)
        folded = normalized.casefold()
        for source, target in self._rules:
            source_folded = source.casefold()
            if folded == source_folded:
                return target
            # Csak teljes útvonal-komponensre illesztünk ("C:/Kep" ≠ "C:/Képek").
            if folded.startswith(source_folded + "/"):
                return target + normalized[len(source) :]
        return None
