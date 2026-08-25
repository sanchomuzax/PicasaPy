"""A Mappakezelő OK gombjának MENTÉSI ÚTJA — sorrend és kapu (#1334).

Az eredeti Picasa OK-kezelője (`0x007c4df0`) **egyetlen** mentő függvényt
hív (`0x005cef20`, 1679 bájt), és az meghatározott sorrendben dolgozik:

| # | cím | lépés |
|---|---|---|
| 1 | `0x005cf49b` | `watchedfolders.txt` (`0x004f5960`) |
| 2 | `0x005cf500` | `]album:removed` sírkövek (`0x004b9200`) |
| 3 | `0x005cf529` | `frexcludefolders.txt` (`0x00491210` → `0x004f5d90`) — **kapuzva** |
| 4 | `0x005cf535` | záró lépés: a nézet frissítése (`0x0065b840`) |

A **kapu** (3.): a hívás csak akkor fut le, ha a `0x00491210`-nek átadott
KÉT lista bármelyike nem üres — a hozzáadandó és az eltávolítandó
arcfelismerés-kizárások. Üres-üres esetben a fájlhoz **nem nyúl** a
program (az `mtime`-ja sem változik).

**Negatív eredmény (17.2):** a `scanlist.txt` a párbeszédből NEM érhető
el — a mentési út **két** listafájlt ír, nem hármat.

Ez a modul a sorrendet és a kaput tartja, semmi mást: a tényleges írást a
hívó adja át függvényként (a vezérlő a `library_controller.py`-ban). Így a
szabály Qt nélkül, egyetlen helyen tesztelhető.

Levezetés: `docs/specs/picasa-mappakezelo.md` 17. szakasz.
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass, field

#: A mentés négy lépésének neve — a `save_folder_manager` ezeket adja
#: vissza, ebben a sorrendben (a kapuzott lépés kimaradhat).
STEP_WATCHED = "watchedfolders"
STEP_TOMBSTONE = "tombstone"
STEP_EXCLUDE = "frexclude"
STEP_FINISH = "finish"


@dataclass(frozen=True)
class FolderManagerSavePlan:
    """Amit az OK menteni akar — egyetlen, változtathatatlan pillanatkép.

    `watched`
        a figyelt mappák VÉGSŐ listája (`watchedfolders.txt` tartalma).
    `tombstones`
        a `]album:removed` sírkövet kapó mappák.
    `faces_excluded`
        az arcfelismerésből kizárt mappák VÉGSŐ listája — ez kerül a
        `frexcludefolders.txt`-be, ha a kapu nyitva van.
    `faces_added` / `faces_removed`
        a KAPUT vezérlő két lista: az újonnan kizárt, illetve a kizárás
        alól felszabadított mappák. Az eredetiben ez a `0x00491210` két
        lista-argumentuma; a fájl előjeles sorformátuma (`+%s` / `-%s`)
        is innen származik.
    """

    watched: tuple[str, ...] = ()
    tombstones: tuple[str, ...] = ()
    faces_excluded: tuple[str, ...] = ()
    faces_added: tuple[str, ...] = ()
    faces_removed: tuple[str, ...] = ()

    @property
    def faces_dirty(self) -> bool:
        """A frexclude-kapu (`0x005cf529`): a két lista bármelyike nem üres."""
        return bool(self.faces_added or self.faces_removed)


@dataclass(frozen=True)
class FolderManagerSaveDraft:
    """Az OK MENETE közben gyűlő, még ki nem írt szándékok.

    A párbeszéd tételenként jelenti be a változásokat (mappa hozzáadása,
    eltávolítása, arc-kapcsoló); a vezérlő ezeket ide gyűjti, és a végén
    egyetlen `FolderManagerSavePlan`-né alakítja. Minden módosító ÚJ
    példányt ad vissza — a piszkozat sosem mutálódik.
    """

    tombstones: tuple[str, ...] = field(default=())
    faces_added: tuple[str, ...] = field(default=())
    faces_removed: tuple[str, ...] = field(default=())

    def with_tombstone(self, path: str) -> FolderManagerSaveDraft:
        """Egy mappa sírkövet kap (`]album:removed`) — duplikátum nélkül."""
        if path in self.tombstones:
            return self
        return FolderManagerSaveDraft(
            tombstones=(*self.tombstones, path),
            faces_added=self.faces_added,
            faces_removed=self.faces_removed,
        )

    def with_face_change(self, path: str, enabled: bool) -> FolderManagerSaveDraft:
        """Az arcfelismerés-kapcsoló állása egy mappára.

        A két lista a KAPUT vezérli, ezért az oda-vissza kapcsolgatás nem
        halmozódhat: egy mappa mindig csak az egyik listán szerepel, az
        UTOLSÓ kattintás szerint.
        """
        added = tuple(item for item in self.faces_added if item != path)
        removed = tuple(item for item in self.faces_removed if item != path)
        if enabled:
            removed = (*removed, path)
        else:
            added = (*added, path)
        return FolderManagerSaveDraft(
            tombstones=self.tombstones,
            faces_added=added,
            faces_removed=removed,
        )

    def to_plan(
        self,
        *,
        watched: Sequence[str],
        faces_excluded: Sequence[str],
    ) -> FolderManagerSavePlan:
        """A piszkozatból mentési terv, a vezérlő aktuális listáival."""
        return FolderManagerSavePlan(
            watched=tuple(watched),
            tombstones=self.tombstones,
            faces_excluded=tuple(faces_excluded),
            faces_added=self.faces_added,
            faces_removed=self.faces_removed,
        )


def save_folder_manager(
    plan: FolderManagerSavePlan,
    *,
    write_watched: Callable[[tuple[str, ...]], None],
    write_tombstones: Callable[[tuple[str, ...]], None],
    write_faces: Callable[[tuple[str, ...]], None],
    finish: Callable[[], None],
) -> tuple[str, ...]:
    """A mentés végrehajtása a mért sorrendben; a lefutott lépések neve.

    A `write_faces` KIZÁRÓLAG akkor hívódik, ha a kapu nyitva van
    (`plan.faces_dirty`) — üres-üres esetben a `frexcludefolders.txt`-hez
    nem nyúlunk. A `finish` (záró lépés) mindig lefut.

    A hívó írói kivételt dobhatnak (lemezhiba, jogosultság): ezeket NEM
    nyeljük el itt — a vezérlő naplóz és jelez —, de a záró lépés akkor is
    lefut, hogy a felület ne maradjon félkész állapotban.
    """
    steps: list[str] = []
    try:
        write_watched(plan.watched)
        steps.append(STEP_WATCHED)
        write_tombstones(plan.tombstones)
        steps.append(STEP_TOMBSTONE)
        if plan.faces_dirty:
            write_faces(plan.faces_excluded)
            steps.append(STEP_EXCLUDE)
    finally:
        finish()
        steps.append(STEP_FINISH)
    return tuple(steps)
