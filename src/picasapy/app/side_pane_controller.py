"""#1601: a bal hasáb ini-alapú gyűjteményeinek betöltése — a felület
szálát kímélve.

## Mit mértünk

Az induláskor SZINKRONBAN futó munka (RPi5, tmpfs, szintetikus index,
2026-08-27) — a két ini-olvasó gyűjtemény az összes szakasz **94%-a**, és
egyedül ők skálázódnak érdemben a könyvtár méretével:

| szakasz | 100 mappa | 1 000 mappa | 5 000 mappa |
|---|---|---|---|
| `prune_foreign_folders` (#58) | 2,8 ms | 23,9 ms | 120,9 ms |
| `merge_duplicate_folders` (#507) | 3,1 ms | 29,6 ms | 154,3 ms |
| `sorted_folder_rows` (mappafa) | 1,1 ms | 15,2 ms | 78,7 ms |
| **`people_in_index` (#26)** | **44,4 ms** | **609,7 ms** | **3 765,0 ms** |
| **`project_folders` (#1029)** | **19,3 ms** | **295,9 ms** | **1 526,7 ms** |

Ez a tulajdonos „egyre lassabb" tapasztalata: a költség a MAPPÁK számával
nő, a mappák száma pedig soha nem csökken. NAS-on (ahol a gyűjteménye él)
egy fájlnyitás nagyságrenddel drágább, mint helyi lemezen.

## A két lépés, amit ez a szelet visz

1. **Egy söprés kettő helyett** — a két gyűjtemény ugyanazt a
   `.picasa.ini`-halmazt olvasta végig egymástól függetlenül; mostantól
   egyetlen menetben állnak elő (`index/side_pane.py`).
2. **Az induláskori söprés lekerül a felület száláról** — a `start()` a
   gyűjtemények nélkül tölti be a hasábot, a söprést pedig a MÁR MEGLÉVŐ
   háttér-szinkron szála (`_sync_worker`) végzi el, és az eredményt
   átadja. Nem indítunk hozzá új szálat: a szinkron úgyis lefut minden
   induláskor, és a végén amúgy is frissítenénk a hasábot.

⚠️ **Nem törlünk és nem dobunk el adatot.** A gyűjtemények tartalma
változatlan — csak később és máshol áll elő."""

from __future__ import annotations

import logging
import sqlite3
import threading

from picasapy.index.side_pane import SidePaneCollections, load_side_pane_collections

logger = logging.getLogger(__name__)

#: A háttérszál → felület szála átadás zára. SZÁNDÉKOSAN modul-szintű, nem
#: példányonkénti: a példányonkénti, lustán létrehozott zárnak magának is
#: versenyhelyzete volna (két szál egyszerre hozná létre, és két KÜLÖNBÖZŐ
#: zárral védenék ugyanazt a letétet). A védett szakasz két attribútum-
#: művelet, tehát a közös zár versengése mérhetetlen.
_ATADAS_ZAR = threading.Lock()


class SidePaneMixin:
    """Az Emberek + Projektek gyűjtemény betöltése egy söpréssel.

    Mixin `__init__` NÉLKÜL (a `controller.py` konstruktora forró fájl): az
    állapotát lustán hozza létre, a `_init_people`/`_init_project_folders`
    mintáját követve, de azok bolygatása nélkül."""

    # -- háttérszál oldala ---------------------------------------------------

    def _precompute_side_pane(self, conn: sqlite3.Connection) -> None:
        """A gyűjtemények előállítása a HÁTTÉRSZÁLON, letéve átvételre.

        A `_sync_worker` hívja, a saját kapcsolatával, közvetlenül a
        `syncFinished` előtt — a felület szálán futó `_reload()` ezt már
        csak átveszi, nem söpri újra az ini-ket.

        A hiba nyelt, de NAPLÓZVA: egy diagnosztikai kellemetlenség soha
        nem viheti el a háttér-szinkront, viszont vakon sem állhatunk."""
        try:
            collections = load_side_pane_collections(conn)
        except Exception:  # noqa: BLE001 — a szinkron nem hiúsulhat meg tőle
            logger.warning(
                "a hasáb gyűjteményeinek háttérbeli előállítása hibára futott",
                exc_info=True,
            )
            return
        with _ATADAS_ZAR:
            self._side_pane_stash = collections

    # -- a felület szála -----------------------------------------------------

    def _take_side_pane_stash(self) -> SidePaneCollections | None:
        """Az előre kiszámolt eredmény ÁTVÉTELE (egyszer használatos).

        A kivétel után a letét ürül: a következő frissítés vagy kap újat a
        háttérszáltól, vagy maga söpör — elavult adatot nem szolgálunk ki
        másodszor."""
        with _ATADAS_ZAR:
            stash = getattr(self, "_side_pane_stash", None)
            self._side_pane_stash = None
        return stash

    def _load_side_pane(self, conn: sqlite3.Connection) -> None:
        """A hasáb két ini-alapú gyűjteményének frissítése.

        Ha a háttérszál már letette az eredményt, azt vesszük át (nulla
        lemezmunka a felület szálán); különben itt söprünk — EGYETLEN
        menetben mindkettőhöz."""
        collections = self._take_side_pane_stash()
        if collections is None:
            collections = load_side_pane_collections(conn)
        self._apply_side_pane(collections)

    def _apply_side_pane(self, collections: SidePaneCollections) -> None:
        """A kész gyűjtemények beállítása + a hasáb értesítése.

        Szándékosan a MEGLÉVŐ `peopleChanged`/`projectFoldersChanged`
        jelzéseken megy: a QML-oldali kötések változatlanok maradnak."""
        self._people = collections.people
        self._project_folders = collections.project_folders
        self.peopleChanged.emit()
        self.projectFoldersChanged.emit()
        # #2031: a Mappák listából a projekt-mappák KIMARADNAK, és ezt
        # csak most tudjuk — a projekt-útvonalak épp itt lettek meg. A
        # frissítés nélkül a mappa a hasáb-betöltésig MINDKÉT helyen
        # látszana (villanás), utána eltűnne az egyikről: pont az a
        # zavaró állapot, amitől a felhasználó azt hinné, elveszett.
        self._reload_folders()


__all__ = ["SidePaneMixin"]
