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
        slashed = _to_slashes(windows_path)
        folded = slashed.casefold()
        for source_prefix, target_prefix in self.mappings:
            prefix = _to_slashes(source_prefix).casefold()
            if folded == prefix or folded.startswith(prefix + "/"):
                # a maradékot az EREDETI (nem casefoldolt) útvonalból vágjuk
                # ki — a fájlnevek kis-nagybetűi nem sérülhetnek
                remainder = slashed[len(prefix) :].lstrip("/")
                base = PurePosixPath(target_prefix)
                return str(base / remainder) if remainder else str(base)
        return None


def _to_slashes(path: str) -> str:
    """Windows-útvonal / határolós, záró-perjel nélküli alakja."""
    return str(PureWindowsPath(path)).replace("\\", "/").rstrip("/")
