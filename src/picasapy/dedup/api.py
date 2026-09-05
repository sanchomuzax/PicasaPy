"""A duplikátum-kereső egyesített API-ja (#31): `find_duplicates`.

#294 — a nagy könyvtárra skálázás három eleme itt találkozik:

* **haladás-jelzés** (`progress`) és **megszakítás** (`should_stop`) a
  `sync_tree` (#209/#216) mintája szerint: a callback igaz visszatérési
  értéke is megszakítás-kérés, a részeredmény `cancelled=True`-val jön;
* **külső dHash-forrás** (`dhash_source`): a hívó adhat gyorsítótárazott
  lenyomatot (ld. `picasapy.index.hashes`), így az ismételt keresés csak az
  új/megváltozott képeket dekódolja;
* a hasonlóság-klaszterezés sávos jelöltszűrése (ld. `dedup/similar.py`).

A callback a HÍVÓ szálán fut (az appban a háttér-worker szálán, NEM a
GUI-szálon) — a szál-átadás és a ritkítás a hívó dolga.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Sequence

from picasapy.dedup.exact import (
    ExactDuplicateGroup,
    FastKeySource,
    group_exact_duplicates,
)
from picasapy.dedup.phash import compute_dhash
from picasapy.dedup.similar import (
    DEFAULT_PHASH_THRESHOLD,
    SimilarGroup,
    group_similar,
)

# A haladás-jelzés fázis-tokenjei. Szándékosan technikai (nem fordítandó)
# azonosítók: az emberi szöveget a UI teszi hozzá `qsTr()`-rel.
PHASE_EXACT = "exact"  # tartalom-hash (bitre azonos fájlok)
PHASE_HASH = "phash"  # perceptuális lenyomat (dHash)

# (fázis, kész, összes) — igaz visszatérési érték = megszakítás-kérés
DedupProgressCallback = Callable[[str, int, int], object]

# Ennyi feldolgozott kép után megy ki egy haladás-jelzés. A jelzés
# szálhatáron átívelő Qt-signal lesz, képenként kibocsátva elárasztaná a
# GUI eseménysorát; 25-ös lépésköz 140k képnél is folyamatos mozgást ad.
_PROGRESS_STEP = 25


@dataclass(frozen=True)
class DuplicateReport:
    """A duplikátum-keresés teljes, immutábilis eredménye.

    `exact_groups`: bitre azonos fájlok csoportjai.
    `similar_groups`: perceptuálisan hasonló (de NEM bitre azonos) képek
    klaszterei — egy csoport, amelynek útvonal-halmaza megegyezik egy
    `exact_groups`-beli csoportéval, itt szándékosan nem szerepel újra
    (a hívónak nem kell kétszer megjelenítenie ugyanazt az együttest).
    `cancelled`: igaz, ha a futás megszakítás-kérésre állt le — ilyenkor a
    csoportok üresek (a részleges eredmény félrevezető lenne)."""

    exact_groups: tuple[ExactDuplicateGroup, ...]
    similar_groups: tuple[SimilarGroup, ...]
    cancelled: bool = False


_CANCELLED = DuplicateReport(exact_groups=(), similar_groups=(), cancelled=True)


class _Reporter:
    """Ritkított haladás-jelzés + megszakítás-figyelés egy helyen.

    A `cancelled` akkor billen igazra, ha a `should_stop` igazat ad, vagy
    ha a `progress` callback igaz értékkel tér vissza (a `sync_tree` #216-os
    szerződése). A None/False visszatérésű (érték nélküli) callbackek nem
    szakítanak meg — visszafelé kompatibilis."""

    def __init__(
        self,
        progress: DedupProgressCallback | None,
        should_stop: Callable[[], bool] | None,
        total: int,
    ) -> None:
        self._progress = progress
        self._should_stop = should_stop
        self._total = total
        self.cancelled = False

    def stopped(self) -> bool:
        if self.cancelled:
            return True
        if self._should_stop is not None and self._should_stop():
            self.cancelled = True
        return self.cancelled

    def step(self, phase: str, done: int, *, final: bool = False) -> bool:
        """Egy (ritkított) haladás-jelzés; igaz = megszakítás-kérés."""
        if self.stopped():
            return True
        if self._progress is None:
            return False
        if not final and done % _PROGRESS_STEP != 0:
            return False
        if self._progress(phase, done, self._total):
            self.cancelled = True
        return self.cancelled


def find_duplicates(
    paths: Sequence[str | Path],
    *,
    phash_threshold: int = DEFAULT_PHASH_THRESHOLD,
    progress: DedupProgressCallback | None = None,
    should_stop: Callable[[], bool] | None = None,
    dhash_source: Callable[[Path], int | None] | None = None,
    fast_key_source: FastKeySource | None = None,
) -> DuplicateReport:
    """Duplikátum- és hasonlóság-keresés a megadott képútvonalakon.

    Két független réteg fut:
    1. **Pontos duplikátum** — tartalom-hash (SHA-256), két előszűrővel:
       méret, majd a Picasa fej+farok gyors kulcsa (#1481).
    2. **Perceptuálisan hasonló** — dHash + Hamming-távolság, `phash_threshold`
       küszöbbel (alapértelmezés: `DEFAULT_PHASH_THRESHOLD` = 10).

    A képek, amik nem dekódolhatók (sérült fájl, nem támogatott formátum),
    a perceptuális rétegből szótlanul kimaradnak — a pontos-duplikátum
    rétegre ez nem vonatkozik, az bármilyen fájltípuson (bájt-szinten) működik.

    `progress`: `(fázis, kész, összes)` hívások a `PHASE_EXACT`, majd a
    `PHASE_HASH` fázisban (ritkítva, ld. `_PROGRESS_STEP`); igaz visszatérési
    érték megszakítás-kérés. `should_stop`: ugyanaz kívülről kérdezve.
    Megszakításnál `cancelled=True` és üres csoportok.

    `dhash_source`: a lenyomat forrása képenként (alapértelmezés a lemezről
    számoló `compute_dhash`); a hívó ide adhat gyorsítótárazott értéket.

    `fast_key_source` (#1494): ugyanez a pontos réteg Picasa-gyorskulcsára
    (alapértelmezés a lemezről számoló `picasa_fast_key`). Index-hátterű
    forrással az ismételt keresés a változatlan képek fájlvégeit sem
    olvassa be újra.

    A bemenetet nem mutálja, és nem is szűri/rendezi a hívó számára látható
    módon — az eredmény (`DuplicateReport`) determinisztikus sorrendű,
    független a `paths` bemeneti sorrendjétől."""
    normalized = tuple(Path(path) for path in paths)
    reporter = _Reporter(progress, should_stop, len(normalized))
    compute = compute_dhash if dhash_source is None else dhash_source

    exact_groups = group_exact_duplicates(
        normalized,
        progress=lambda done: reporter.step(PHASE_EXACT, done),
        fast_key_source=fast_key_source,
    )
    if reporter.stopped():
        return _CANCELLED
    reporter.step(PHASE_EXACT, len(normalized), final=True)
    if reporter.stopped():
        return _CANCELLED
    exact_path_sets = {frozenset(group.paths) for group in exact_groups}

    hashes: list[tuple[Path, int]] = []
    for done, path in enumerate(normalized, start=1):
        value = compute(path)
        if value is not None:
            hashes.append((path, value))
        if reporter.step(PHASE_HASH, done):
            return _CANCELLED
    reporter.step(PHASE_HASH, len(normalized), final=True)
    if reporter.stopped():
        return _CANCELLED

    similar_groups = tuple(
        group
        for group in group_similar(
            hashes, threshold=phash_threshold, should_stop=reporter.stopped
        )
        if frozenset(group.paths) not in exact_path_sets
    )
    if reporter.stopped():
        return _CANCELLED

    return DuplicateReport(exact_groups=exact_groups, similar_groups=similar_groups)
