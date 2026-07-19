"""PMP/db3-import: a Windows-os Picasa adatbázisának beolvasása (csak olvasás).

Spec: docs/specs/pmp-database.md. A formátumtudás két független
implementációból keresztvalidált (docs/reference-repos-audit.md); kód-
referencia az MIT-licencű skisoo/PicasaDBReader volt.
"""

from .importer import (
    FaceRegion,
    ImageRecord,
    PmpImport,
    load_db3,
    merge_imports,
    parse_deferredregion,
)
from .pmp import PmpColumn, PmpFormatError, decode_ole_date, parse_pmp, read_pmp
from .remap import PathRemapper
from .table import PmpTable, read_table
from .thumbindex import (
    EntryKind,
    ThumbIndex,
    ThumbIndexEntry,
    parse_thumbindex,
    read_thumbindex,
)

__all__ = [
    "EntryKind",
    "FaceRegion",
    "ImageRecord",
    "PathRemapper",
    "PmpColumn",
    "PmpFormatError",
    "PmpImport",
    "PmpTable",
    "ThumbIndex",
    "ThumbIndexEntry",
    "decode_ole_date",
    "load_db3",
    "merge_imports",
    "parse_deferredregion",
    "parse_pmp",
    "parse_thumbindex",
    "read_pmp",
    "read_table",
    "read_thumbindex",
]
