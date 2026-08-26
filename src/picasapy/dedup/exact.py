"""Pontos (bitre azonos) duplikátumok felderítése (#31).

**Három** egyre drágább lépés — mindegyik csak azt engedi tovább, amit az
előző nem tudott kizárni:

1. **méret** — a fájlrendszer `stat()`-jából ingyen jön; egyedi méretű
   fájlnak nem lehet bitre azonos párja;
2. **Picasa gyors kulcs** (#1481, `dedup/fastkey.py`) — a méret + az első és
   az utolsó 16834 bájt MD5-e, azaz fájlonként legfeljebb ~33 KB olvasás, a
   fájl méretétől függetlenül; eltérő kulcs = biztosan eltérő tartalom;
3. **teljes SHA-256** — csak azokra, amiket a kulcs sem tudott elválasztani.

**Miért marad meg a 3. lépés** (a #1481 (a)/(b) döntése): a gyors kulcs 64
bites, és csak a fájl két végét nézi, tehát két azonos méretű kép, amely
csak a KÖZEPÉN tér el, ütközik. Az eredeti Picasa ezt elfogadta; ez a réteg
viszont "bitre azonos"-t ígér, és a rá épülő két funkció visszafordíthatatlan:
a Duplikátum-kezelő törölni ajánl (#287), az importálás pedig szótlanul
kihagyja a jelöltet (`importsource.duplicate_paths`, #441). Egyetlen téves
egyezés ott egy elveszett fényképet jelentene, ezért a kulcs nálunk
**kizárólag előszűrő** — a jegy **(b)** változatát választottuk.
"""

from __future__ import annotations

import hashlib
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from picasapy.dedup.fastkey import picasa_fast_key

_CHUNK_SIZE = 1 << 20  # 1 MiB — nagy fájloknál sem terheli túl a memóriát


@dataclass(frozen=True)
class ExactDuplicateGroup:
    """Bitre azonos tartalmú fájlok csoportja.

    `paths` legalább két elemű, determinisztikusan (útvonal szerint) rendezve.
    """

    content_hash: str
    paths: tuple[Path, ...]


def file_content_hash(path: Path) -> str | None:
    """A fájl bájtjainak SHA-256 hash-e (hex string).

    `None`, ha a fájl időközben eltűnt/elérhetetlen (NAS-forrás) — ez nem
    kivétel, a hívó egyszerűen kihagyja a fájlt az összevetésből."""
    digest = hashlib.sha256()
    try:
        with open(path, "rb") as handle:
            for chunk in iter(lambda: handle.read(_CHUNK_SIZE), b""):
                digest.update(chunk)
    except OSError:
        return None
    return digest.hexdigest()


def _kulcs_szerint_ellenorzendok(candidates: list[Path], size: int) -> list[Path]:
    """Az azonos méretű jelöltekből azok, akikre tényleg kell teljes hash.

    A gyors kulcs (2. lépés) minden jelöltre legfeljebb ~33 KB-ot olvas; akinek
    a csoportjában egyedi a kulcsa, az biztosan nem másodpéldány, róla a drága
    teljes olvasás elmarad.

    Két eset kerüli meg a kulcsot:
    * `size <= 0` — az üres fájlok a méretük alapján már bitre azonosak, a
      "teljes" hash rajtuk nulla bájt olvasás, a kulcs csak felesleges kör;
    * kulcs nélküli fájl (olvashatatlan vagy olvasás közben rövidült) — nem
      zárjuk ki előszűréssel, a teljes hash döntsön (az is `None`-t ad majd,
      ha tényleg elérhetetlen)."""
    if size <= 0:
        return list(candidates)
    kulcs_szerint: dict[int | None, list[Path]] = defaultdict(list)
    for candidate in candidates:
        kulcs_szerint[picasa_fast_key(candidate)].append(candidate)
    return [
        candidate
        for kulcs, csoport in kulcs_szerint.items()
        if kulcs is None or len(csoport) >= 2
        for candidate in csoport
    ]


def group_exact_duplicates(
    paths: Sequence[Path],
    progress: Callable[[int], object] | None = None,
) -> tuple[ExactDuplicateGroup, ...]:
    """Bitre azonos fájlok csoportosítása.

    `progress` (#294): a feldolgozott képek KUMULÁLT száma, képenként hívva;
    igaz visszatérési érték megszakítás-kérés, ilyenkor a függvény üres
    eredménnyel tér vissza (a részleges csoportosítás félrevezető lenne).
    A két előszűrő miatt a teljes hash-elés a képek töredékére fut le, a
    haladás-jelzés viszont MINDEN képre lépked — a felhasználónak egyenletes
    mozgás kell, nem a belső optimalizálás lenyomata.

    A bemeneti sorozatot NEM mutálja. Az eredmény determinisztikus sorrendű:
    a csoportok az első (rendezett) útvonaluk szerint következnek, a
    csoporton belüli útvonalak szintén rendezve vannak — így a kimenet a
    bemeneti sorrendtől függetlenül reprodukálható."""
    by_size: dict[int, list[Path]] = defaultdict(list)
    for path in paths:
        try:
            size = path.stat().st_size
        except OSError:
            continue  # törölt/elérhetetlen fájl — kihagyjuk
        by_size[size].append(path)

    by_hash: dict[str, list[Path]] = defaultdict(list)
    done = 0
    for size, candidates in by_size.items():
        if len(candidates) < 2:
            done += len(candidates)  # egyedi méret: bitre azonos párja nem lehet
            if progress is not None and progress(done):
                return ()
            continue
        ellenorzendok = _kulcs_szerint_ellenorzendok(candidates, size)
        done += len(candidates) - len(ellenorzendok)  # a kulccsal kizártak
        if progress is not None and done and progress(done):
            return ()
        for candidate in ellenorzendok:
            content_hash = file_content_hash(candidate)
            if content_hash is not None:
                by_hash[content_hash].append(candidate)
            done += 1
            if progress is not None and progress(done):
                return ()

    groups = [
        ExactDuplicateGroup(
            content_hash=content_hash,
            paths=tuple(sorted(group_paths, key=str)),
        )
        for content_hash, group_paths in by_hash.items()
        if len(group_paths) >= 2
    ]
    return tuple(sorted(groups, key=lambda group: str(group.paths[0])))
