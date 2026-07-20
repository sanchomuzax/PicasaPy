"""Logikai PMP-tábla összeállítása oszlopfájlokból (#1).

A db3 könyvtárban a `<tábla>_<oszlop>.pmp` fájlok együtt adnak ki egy
logikai táblát (`imagedata`, `albumdata`, `catdata`). Az oszlopok élesben
eltérő hosszúak (sparse tárolás, ld. docs/specs/pmp-database.md): a tábla
sor-száma = a leghosszabb oszlop hossza (ez egyezik a thumbindex
bejegyzésszámával), a rövidebb oszlopok hiányzó értékei `None`-nal
töltődnek fel.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

from .pmp_column import PmpColumn, read_pmp_column


@dataclass(frozen=True)
class PmpTable:
    """Egy logikai tábla: oszlopnév → sorrendhelyes, None-nal kipótolt tuple.

    A `columns` írásvédett leképezés (`MappingProxyType`) — a frozen
    dataclass immutabilitása így a beágyazott gyűjteményre is kiterjed,
    nem csak a mezők újra-hozzárendelésére."""

    name: str
    row_count: int
    columns: MappingProxyType[str, tuple]

    def column(self, name: str) -> tuple:
        """Az oszlop értékei (üres tuple, ha az oszlop hiányzik)."""
        return self.columns.get(name, ())

    def value(self, column_name: str, row: int):
        """Egy cella értéke; None, ha az oszlop hiányzik vagy sparse."""
        column = self.columns.get(column_name)
        if column is None or row >= len(column):
            return None
        return column[row]


def read_table(db3_dir: Path, table_name: str) -> PmpTable:
    """A `<table_name>_*.pmp` fájlok beolvasása és kipótolt táblává fűzése.

    Raises:
        FileNotFoundError: Ha a könyvtár nem létezik, vagy egyetlen
            oszlopfájl sem tartozik a táblához.
        PmpFormatError: Bármely oszlopfájl sérülése esetén (a fájlnévvel
            kiegészítve továbbgördül).
    """
    db3_dir = Path(db3_dir)
    if not db3_dir.is_dir():
        raise FileNotFoundError(f"A db3 könyvtár nem létezik: {db3_dir}")
    prefix = f"{table_name}_"
    raw_columns: dict[str, PmpColumn] = {}
    for path in sorted(db3_dir.glob(f"{prefix}*.pmp")):
        column_name = path.stem[len(prefix) :]
        raw_columns[column_name] = read_pmp_column(path)
    if not raw_columns:
        raise FileNotFoundError(
            f"Nincs egyetlen {prefix}*.pmp oszlopfájl sem itt: {db3_dir}"
        )
    row_count = max(len(column) for column in raw_columns.values())
    padded = {
        name: column.values + (None,) * (row_count - len(column))
        for name, column in raw_columns.items()
    }
    return PmpTable(
        name=table_name, row_count=row_count, columns=MappingProxyType(padded)
    )
