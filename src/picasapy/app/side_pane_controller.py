"""#1601/#4589: a bal hasáb ini-alapú gyűjteményeinek betöltése.

Az Emberek, Projektek és az egyéni gyűjtemények egy közös söprésből
készülnek; az induláskori lemezmunka a háttér-szinkron szálára kerül.

## Mit mértünk

Az induláskor SZINKRONBAN futó munka (RPi5, tmpfs, szintetikus index,
2026-08-27) — a két korábbi ini-olvasó gyűjtemény az összes szakasz **94%-a**, és
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
from collections.abc import Iterable

from PySide6.QtCore import QMetaObject, Qt, Slot
from picasapy.index import open_index
from picasapy.index.side_pane import (
    SidePaneCollections,
    cached_side_pane_collections,
    refresh_side_pane_cache,
    side_pane_cache_ready,
)
from picasapy.ini import central_contacts_path

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

    def _precompute_side_pane(
        self,
        conn: sqlite3.Connection,
        folders: Iterable[str] | None = None,
        *,
        refresh: bool = True,
    ) -> bool:
        """A gyűjtemények előállítása a HÁTTÉRSZÁLON, letéve átvételre.

        A `_sync_worker` hívja, a saját kapcsolatával, közvetlenül a
        `syncFinished` előtt — a felület szálán futó `_reload()` ezt már
        csak átveszi, nem söpri újra az ini-ket.

        A hiba nyelt, de NAPLÓZVA: egy diagnosztikai kellemetlenség soha
        nem viheti el a háttér-szinkront, viszont vakon sem állhatunk."""
        central_path = central_contacts_path(self._db_path)
        try:
            if refresh:
                refresh_side_pane_cache(
                    conn, folders, central_path=central_path
                )
            collections = cached_side_pane_collections(
                conn, central_path=central_path
            )
            if collections is None:
                return False
        except Exception:  # noqa: BLE001 — a szinkron nem hiúsulhat meg tőle
            logger.warning(
                "a hasáb gyűjteményeinek háttérbeli előállítása hibára futott",
                exc_info=True,
            )
            return False
        with _ATADAS_ZAR:
            self._side_pane_stash = collections
        return True

    def _refresh_side_pane_cache(
        self,
        conn: sqlite3.Connection,
        folders: Iterable[str] | None = None,
    ) -> bool:
        """Az ini-gyorstárat frissíti a háttérszálon, előállítás nélkül."""
        return refresh_side_pane_cache(
            conn,
            folders,
            central_path=central_contacts_path(self._db_path),
        )

    def _side_pane_cache_ready(self, conn: sqlite3.Connection) -> bool:
        return side_pane_cache_ready(conn)

    def _finish_index_sync(
        self,
        conn: sqlite3.Connection,
        total_changes_before: int,
        cache_was_ready: bool,
        folders: Iterable[str] | None = None,
    ) -> bool:
        """Egy szinkron index- és ini-változását összesíti a jelzés előtt."""
        index_changed = conn.total_changes != total_changes_before
        if not cache_was_ready:
            folders = None
        ini_changed = self._refresh_side_pane_cache(conn, folders=folders)
        changed = index_changed or ini_changed
        self._last_sync_changed = changed
        if changed or not cache_was_ready:
            self._precompute_side_pane(conn, refresh=False)
        return changed

    # -- a felület szála -----------------------------------------------------

    def _take_side_pane_stash(self) -> SidePaneCollections | None:
        """Az előre kiszámolt eredmény ÁTVÉTELE (egyszer használatos).

        A kivétel után a letét ürül: a következő frissítés vagy kap újat a
        háttérszáltól, vagy a memóriabeli gyorstárból állítja elő; lemezről
        nem söpör."""
        with _ATADAS_ZAR:
            stash = getattr(self, "_side_pane_stash", None)
            self._side_pane_stash = None
        return stash

    def _load_side_pane(self, conn: sqlite3.Connection) -> None:
        """A hasáb két ini-alapú gyűjteményének frissítése.

        Ha a háttérszál már letette az eredményt, azt vesszük át. Máskülönben
        a mappánkénti gyorstárból állítjuk elő; ini-fájl olvasása itt nincs.
        Hiányos gyorstárnál a betöltés a háttérszálon indul el."""
        collections = self._take_side_pane_stash()
        if collections is None:
            collections = cached_side_pane_collections(
                conn, central_path=central_contacts_path(self._db_path)
            )
        if collections is None:
            self._schedule_side_pane_warmup()
            return
        self._init_custom_collections()
        self._apply_side_pane(collections)

    def _schedule_side_pane_warmup(self) -> None:
        """Hiányzó gyorstárat tölt fel háttérben, majd a felületen alkalmazza."""
        if getattr(self, "_side_pane_warmup_running", False):
            return
        if getattr(self, "_sync_running", False) or getattr(
            self, "_dirty_running", False
        ):
            return
        self._side_pane_warmup_running = True

        def worker() -> None:
            try:
                with open_index(self._db_path) as conn:
                    self._precompute_side_pane(conn)
            finally:
                try:
                    QMetaObject.invokeMethod(
                        self,
                        "_apply_side_pane_stash",
                        Qt.ConnectionType.QueuedConnection,
                    )
                except RuntimeError:
                    logger.debug("az oldalpanel-gyorstár alkalmazása elmaradt")

        try:
            self._start_background(worker, name="picasapy-side-pane-cache")
        except BaseException:
            self._side_pane_warmup_running = False
            raise

    @Slot()
    def _apply_side_pane_stash(self) -> None:
        """A háttérbeli első betöltés eredményét a felületi szálon alkalmazza."""
        self._side_pane_warmup_running = False
        collections = self._take_side_pane_stash()
        if collections is None:
            return
        self._init_custom_collections()
        self._apply_side_pane(collections)

    def _apply_side_pane(self, collections: SidePaneCollections) -> None:
        """A kész gyűjtemények beállítása + a hasáb értesítése.

        Szándékosan a MEGLÉVŐ `peopleChanged`/`projectFoldersChanged`
        jelzéseken megy: a QML-oldali kötések változatlanok maradnak."""
        self._people = collections.people
        self._project_folders = collections.project_folders
        self._apply_custom_collection_folders(
            collections.custom_collection_folders
        )
        self.peopleChanged.emit()
        self.projectFoldersChanged.emit()
        # #2031: a Mappák listából a projekt-mappák KIMARADNAK, és ezt
        # csak most tudjuk — a projekt-útvonalak épp itt lettek meg. A
        # frissítés nélkül a mappa a hasáb-betöltésig MINDKÉT helyen
        # látszana (villanás), utána eltűnne az egyikről: pont az a
        # zavaró állapot, amitől a felhasználó azt hinné, elveszett.
        self._reload_folders()


__all__ = ["SidePaneMixin"]
