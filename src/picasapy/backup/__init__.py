"""Biztonsági mentés és visszaállítás nevesített készletekből (#440, #4614).

Az eredeti Picasa „Back Up Pictures" (`ID_TOOLS_BACKUP`) funkciójának az a
része, ami ma is értékes: a **mentés-készlet**. A fájlmappás készlet mellett
CD/DVD-lemezképet is ír, a mentési készletből pedig a képek visszaállíthatók.

A készlet tárolása az indexben él (`picasapy.index.backup_sets`), a
futtatás itt.
"""

from .futtatas import (
    MANIFESZT_NEVE,
    Terv,
    TervezettFajl,
    futtasd,
    mappankent,
    tervezd_meg,
)
from .szuro import szurd_meg
from .visszaallitas import VisszaallitasiEredmeny, visszaallit

__all__ = [
    "MANIFESZT_NEVE",
    "Terv",
    "TervezettFajl",
    "VisszaallitasiEredmeny",
    "futtasd",
    "mappankent",
    "szurd_meg",
    "tervezd_meg",
    "visszaallit",
]
