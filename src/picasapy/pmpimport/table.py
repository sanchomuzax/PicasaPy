"""Logikai PMP-tábla: egy könyvtár `tábla_*.pmp` oszlopfájljainak együttese.

A táblák sparse-ok: az oszlopok rekordszáma eltérhet; a tábla hossza a
leghosszabb oszlop hossza (valódi db3-on igazolva, docs/specs/pmp-database.md).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .pmp import PmpColumn, read_pmp


@dataclass(frozen=True)
class PmpTable:
    """Egy logikai tábla (imagedata / albumdata / catdata) oszlopai."""

    name: str
    columns: dict[str, PmpColumn] = field(default_factory=dict)

    @property
    def row_count(self) -> int:
        return max((len(col.values) for col in self.columns.values()), default=0)

    def row(self, index: int) -> dict:
        """Az `index`-edik sor; a rövidebb (sparse) oszlopok kimaradnak."""
        if not 0 <= index < self.row_count:
            raise IndexError(f"{self.name}: sorindex a tartományon kívül: {index}")
        return {
            name: column.values[index]
            for name, column in self.columns.items()
            if index < len(column.values)
        }

    def rows(self):
        """Az összes sor bejárása sorindex szerint."""
        return (self.row(i) for i in range(self.row_count))


def read_table(db_dir: Path, table: str) -> PmpTable:
    """A `db_dir` könyvtár `{table}_*.pmp` fájljainak beolvasása egy táblává."""
    columns: dict[str, PmpColumn] = {}
    for path in sorted(db_dir.glob(f"{table}_*.pmp")):
        column = read_pmp(path)
        columns[column.name] = column
    return PmpTable(name=table, columns=columns)
