"""A könyvtárvezérlő sync-homlokzata és kompatibilis importútvonala (#6257)."""

from __future__ import annotations

import importlib
import sqlite3 as sqlite3
import stat as stat
import sys
from pathlib import Path as Path

from PySide6.QtCore import Slot as Slot
from picasapy.index import folder_scan_stamps as folder_scan_stamps
from picasapy.index import open_index as open_index
from picasapy.index import remove_folder_tree as remove_folder_tree
from picasapy.scanner import DirectoryChange as DirectoryChange

from .busy_registry import get_app_busy_registry as get_app_busy_registry
from .folder_freshness import next_sweep_batch as next_sweep_batch
from .folder_freshness import stale_folders as stale_folders
from .library_controller_activity import _FILETYPE_SNAPSHOT_UNSET as _FILETYPE_SNAPSHOT_UNSET


def _legacy():
    """A régi modulból olvassa az örökölt, tesztek által foltozható neveket."""
    return sys.modules.get(
        f"{__package__}.library_controller"
    ) or importlib.import_module(".library_controller", __package__)


_dirty_sync_module = importlib.import_module(
    ".library_controller_sync_dirty", __package__
)
_rescan_sync_module = importlib.import_module(
    ".library_controller_sync_rescan", __package__
)
_sweep_sync_module = importlib.import_module(
    ".library_controller_sync_sweep", __package__
)
_LibrarySyncDirtyMixin = _dirty_sync_module._LibrarySyncDirtyMixin
_LibrarySyncRescanMixin = _rescan_sync_module._LibrarySyncRescanMixin
_LibrarySyncSweepMixin = _sweep_sync_module._LibrarySyncSweepMixin
del _dirty_sync_module, _rescan_sync_module, _sweep_sync_module


class _LibrarySyncMixin(
    _LibrarySyncDirtyMixin, _LibrarySyncSweepMixin, _LibrarySyncRescanMixin
):
    @Slot(int)
    def resyncFolderOfRow(self, row: int) -> None:
        """A sorhoz tartozó mappa resyncje — a néző bezárásakor hívjuk:
        a feedben (#64) a néző át is léphetett másik mappába, ezért nem a
        kiválasztott, hanem az épp nézett kép mappáját frissítjük."""
        photos = self._photos.photos
        if 0 <= row < len(photos):
            self.resyncFolder(photos[row].folder_path)


    # SZÁNDÉKOSAN nincs `@Slot`: a hívó a `wire_fileops` PYTHON-oldali
    # kötése (`photoDeleted` → itt), a QML soha nem hívja.
    def removeDeletedRow(self, path: str) -> bool:  # noqa: N802
        """A törölt kép sorának AZONNALI kivétele a rácsból (#1227).

        Eddig a sor eltűnése a célzott újraszinkronon múlt
        (`photoDeleted` → `resyncFolder` → háttérszál → `syncFinished`),
        tehát csak a szinkron VÉGÉN tűnt el — nagy könyvtárnál másodpercek
        vagy percek múlva. Az eredetiben a rács maga végzi a törlést
        (`CThumbUI::DeleteProgress`, `0x00894fb4`).

        A resync ezután is elindul: az utólag EGYEZTET (más program is
        nyúlhatott a mappához), ez a lépés csak előrehozza a látható
        hatást.

        ⚠️ A mappa-csoportokat (`feedGroups`) is frissíteni kell, különben
        a rács csoporthatárai elcsúsznak — a lasszó, a Shift-tartomány és
        a nyilas léptetés mind ezekre épül (#1219). Szerencsés szerkezet:
        a `build_feed_groups` a REKORDOKBÓL számol, tehát a sor kivétele
        után a `start`/`count` maguktól helyes.
        """
        if not self._photos.remove_by_path(path):
            return False
        self._update_feed_groups(self._photos.photos)
        self._update_status(self._photos.photos)
        return True


    @Slot(str)
    def resyncFolder(self, folder_path: str) -> None:
        """Egy mappa újraszinkronja + nézetfrissítés — a néző bezárásakor
        hívjuk (#59): a szerkesztések (filters=) így NAS-on is rögtön
        látszanak a rácson, nem az 5 perces rescanre várva.

        #86: a szinkron HÁTTÉRSZÁLON fut (a _on_folders_dirty útján), így a
        hívó nézetváltás — „Vissza a könyvtárhoz" — hálózati meghajtón sem
        blokkolja a UI-szálat; a végén a syncFinished frissíti a nézetet."""
        if not folder_path:
            return
        # #1458: ez a felhasználó KATTINTÁSA (Frissítés menüpont, néző
        # bezárása) — futó író mellett a kérés várólistára kerül, és a
        # visszajelzés nélkül úgy néz ki, mintha semmi nem történt volna.
        self._on_folders_dirty([folder_path], felhasznaloi=True)


    def set_edit_controllers(self, *edit_controllers) -> None:
        """Az aktív képek útvonalát adó szerkesztőrekeszek bekötése (#4482)."""
        self._edit_controllers = tuple(edit_controllers)
