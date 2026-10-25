"""Ini-frissítés rövid újrapróbálással átmeneti Windows-hibákra (#5900).

Egy képfájl írása után Windowson a mappa `.picasa.ini`-je néhány
tizedmásodpercig zárolt lehet (vírusirtó, keresőindexelő, fájlfigyelő), vagy
közben egy másik írás megváltoztatja. Ilyenkor az első próbálkozás
`PermissionError`-ral vagy `IniConflictError`-ral bukik, a második sikerül.
"""

from __future__ import annotations

import time
from pathlib import Path
from typing import Callable

from picasapy.ini import IniConflictError, IniDocument, update_document

#: Ennyi próbálkozás összesen; a várakozás próbánként nő.
PROBAK = 5
ALAP_VARAKOZAS_MP = 0.1


def update_document_ujraprobalva(
    path: str | Path,
    mutate: Callable[[IniDocument], IniDocument],
    *,
    backup: bool = True,
    probak: int = PROBAK,
    varakozas_mp: float = ALAP_VARAKOZAS_MP,
    alvas: Callable[[float], None] = time.sleep,
) -> IniDocument:
    """Az `update_document` hívása; átmeneti hibánál várakozik és újrapróbál.

    Az utolsó próbálkozás hibáját változatlanul továbbadja, így a hívó
    hibacsatornája (például a `photoOpFailed`) ugyanúgy értesül róla."""
    if probak < 1:
        raise ValueError("a próbálkozások száma legalább 1")
    for proba in range(1, probak + 1):
        try:
            return update_document(path, mutate, backup=backup)
        except (PermissionError, IniConflictError):
            if proba == probak:
                raise
            alvas(varakozas_mp * proba)
    raise AssertionError("elérhetetlen")  # pragma: no cover
