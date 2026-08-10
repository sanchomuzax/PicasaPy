"""Lemezhely-ellenőrzés nagy műveletek (export, weboldal-export,
importálás) ELŐTT (#459, jegy 4. pontja).

Az eredeti Picasa több ponton külön ellenőrzést végzett és előre szólt,
mielőtt egy nagyobb másolásba kezdett volna: *"Sorry, there is not enough
free disk space to safely download pictures."* Mi ugyanezt az elvet
egyszerű, dokumentált módon valósítjuk meg: a becsléshez a forrásfájlok
TELJES méretét vetjük össze a céleszköz szabad helyével.

Szándékosan NINCS kitalált biztonsági szorzó/ráhagyás — a
`picasapy.index.relocate` 5%-os ráhagyása egy MÁSIK, dokumentált helyzetre
szól (a saját SQLite-index-másolat WAL-checkpointjára írás közben); itt
egyszerű fájl-másolásról van szó, ahol a forrásméretek összege önmagában
jó, indokolható közelítés a szükséges helyre. Ha a jegy egy konkrét
szorzót írt volna elő, azt vennénk át — mivel nem ír, nem találunk ki
egyet sem."""

from __future__ import annotations

import shutil
from collections.abc import Iterable
from pathlib import Path


def required_bytes_for(paths: Iterable[Path]) -> int:
    """A megadott fájlok méretének összege. A nem olvasható/eltűnt fájlok
    kimaradnak az összegből (a tényleges másolás úgyis jelezné a hibájukat
    — ez az előzetes becslés csak a hely mértékéről szól, nem az egyes
    fájlok elérhetőségéről)."""
    total = 0
    for path in paths:
        try:
            total += Path(path).stat().st_size
        except OSError:
            continue
    return total


def has_enough_free_space(target_dir: Path, required_bytes: int) -> bool:
    """`True`, ha a `target_dir` szerinti eszközön legalább
    `required_bytes` szabad hely van. Ha a szabad hely nem állapítható meg
    (pl. a cél még nem létezik, vagy a NAS épp nem érhető el), defenzíven
    `True`-t ad — ne EZ a becslés blokkolja a műveletet, a tényleges írás
    úgyis jelezné a valódi hibát."""
    probe = Path(target_dir)
    while not probe.exists():
        parent = probe.parent
        if parent == probe:
            return True
        probe = parent
    try:
        usage = shutil.disk_usage(probe)
    except OSError:
        return True
    return usage.free >= required_bytes
