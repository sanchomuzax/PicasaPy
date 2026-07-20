"""Útvonal-átírás (path remap) a PMP-importhoz (#1, 7. rögzített döntés).

A db3-ban az útvonalak Windows-formátumúak és abszolútak
(`C:\\Users\\anna\\Pictures\\...`); a PicasaPy Linuxon (NAS-ra mountolt
fotókkal) fut, ezért az importnak minden futáskor át kell írnia őket a
helyi megfelelőre. Az átírás prefix-alapú és kis-nagybetű-tűrő (a Windows
fájlrendszere is az), a leghosszabb egyező prefix nyer.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath, PureWindowsPath


@dataclass(frozen=True)
class PathRemapper:
    """Prefix-leképezések: Windows-útvonal-előtag → helyi (POSIX) előtag."""

    mappings: tuple[tuple[str, str], ...]

    @classmethod
    def from_dict(cls, mappings: dict[str, str]) -> PathRemapper:
        ordered = sorted(mappings.items(), key=lambda kv: len(kv[0]), reverse=True)
        return cls(mappings=tuple(ordered))

    def remap(self, windows_path: str) -> str | None:
        """A Windows-útvonal helyi megfelelője, vagy None ha nincs egyező
        prefix (az ilyen bejegyzést az import kihagyja)."""
        # komponensenkénti (nem karakterhossz-alapú) illesztés — a casefold
        # egyes karaktereknél hosszváltozással jár (pl. ß→ss), ezért a
        # foldolt prefix HOSSZA nem használható levágási határnak az
        # eredeti (nem foldolt) útvonalon: elcsúsztatná a maradékot
        parts = tuple(_to_slashes(windows_path).split("/"))
        folded_parts = tuple(part.casefold() for part in parts)
        for source_prefix, target_prefix in self.mappings:
            prefix_parts = tuple(_to_slashes(source_prefix).split("/"))
            folded_prefix_parts = tuple(part.casefold() for part in prefix_parts)
            if (
                len(folded_prefix_parts) <= len(folded_parts)
                and folded_parts[: len(folded_prefix_parts)] == folded_prefix_parts
            ):
                # a maradékot az EREDETI (nem casefoldolt) komponensekből
                # vesszük — a fájlnevek kis-nagybetűi nem sérülhetnek
                remainder_parts = parts[len(folded_prefix_parts) :]
                base = PurePosixPath(target_prefix)
                return (
                    str(base.joinpath(*remainder_parts)) if remainder_parts
                    else str(base)
                )
        return None


def _to_slashes(path: str) -> str:
    """Windows-útvonal / határolós, záró-perjel nélküli alakja."""
    return str(PureWindowsPath(path)).replace("\\", "/").rstrip("/")
