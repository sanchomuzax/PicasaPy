"""Biztonsági mentés: nevesített, újrafuttatható, inkrementális készletek (#440).

Az eredeti Picasa „Back Up Pictures" (`ID_TOOLS_BACKUP`) funkciójának az a
része, ami ma is értékes: a **mentés-készlet**. A CD/DVD-ág szándékosan
kimarad (a jegy is így dönt) — a cél külső meghajtó vagy hálózati
megosztás.

A készlet tárolása az indexben él (`picasapy.index.backup_sets`), a
futtatás itt.
"""

from .futtatas import (
    MANIFESZT_NEVE,
    Terv,
    TervezettFajl,
    futtasd,
    tervezd_meg,
)
from .szuro import szurd_meg

__all__ = [
    "MANIFESZT_NEVE",
    "Terv",
    "TervezettFajl",
    "futtasd",
    "szurd_meg",
    "tervezd_meg",
]
