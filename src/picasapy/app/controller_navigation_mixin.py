"""A mappanavigáció és az index állapotának segédei."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import Slot
from picasapy.index import open_index
from picasapy.index.hidden_scope import visible_folder_sql

class FolderNavigationMixin:
    """A mappanavigáció és az index állapotának segédei."""

    @Slot()
    def restoreSession(self) -> None:
        """Az utoljára kiválasztott mappa visszaállítása (session restore).

        Ha nincs mentett mappa, vagy az már nincs az indexben, az első
        mappát választjuk. Nem ír felül kézi választást: csak akkor fut,
        ha még nincs kiválasztott mappa."""
        if self._current_folder:
            return
        saved = self._get_settings().value("session/lastFolder", "")
        with open_index(self._db_path) as conn:
            paths = [
                row["path"]
                # #4887: rejtett mappa nem állhat vissza jelenlegi mappának
                for row in conn.execute(
                    "SELECT path FROM folders f"
                    f" WHERE {visible_folder_sql(conn)} ORDER BY path"
                )
            ]
        if saved and saved in paths:
            self.selectFolder(saved)
        elif paths:
            self.selectFolder(paths[0])

    @Slot(str)
    def focusFolder(self, folder_path: str) -> None:
        """A rács fókusza másik mappára került (#1183) — a bal hasáb
        kiemelése kövesse, de a nézet NE mozduljon.

        Az eredetiben a jelenlegi mappa a rács fókuszát követi: a váltó
        (`0x0056bc10`) elengedi az előző mappa kijelölés-csomópontját
        (`0x718a50`), beállítja az újat (`[this+0xeac]`), és kimondja, hogy
        „a jelenlegi album megváltozott" (`0x56b910`). Ez tehát nem
        nézetváltás — ezért itt NINCS `folderActivated` (nem görgetünk oda,
        a felhasználó már ott van) és nincs feed-újraolvasás sem.

        Csak sima mappanézetben fut: keresés/album nézetben a bal hasáb mást
        mutat, ott a fókusz nem határozza meg a kiemelést.
        """
        if not folder_path or self._view_mode[0] != "folder":
            return
        if folder_path == self._current_folder:
            return
        self._current_folder = folder_path
        self._view_mode = ("folder", folder_path)
        self._folder_description = self._read_folder_description(folder_path)
        self.statusChanged.emit()

    def _clear_unread(self, folder_path: str) -> None:
        """Az „olvasatlan" jelölő törlése egy mappára (#1644).

        Csak akkor ír, ha a jelölő tényleg fent van: a mappaváltás gyakori
        művelet, és egy feltétel nélküli UPDATE minden kattintásra
        WAL-bejegyzést szülne (a #139 azonos megfontolása)."""
        if not folder_path:
            return
        with open_index(self._db_path) as conn:
            kurzor = conn.execute(
                "UPDATE folders SET unread = 0 WHERE path = ? AND unread = 1",
                (str(folder_path),),
            )
            if not kurzor.rowcount:
                return
            conn.commit()
        # A bal hasáb kövér szedése ebből a mezőből él — újratöltés nélkül
        # a mappa megnyitás után is kövér maradna.
        self._reload_folders()

    def _index_stamp(self) -> tuple:
        """Az index-adatbázis olcsó változás-pecsétje (#142): a db és a
        -wal fájl (mtime_ns, méret) párja. Bármely index-írás (sync,
        fotóművelet — akár külső folyamatból) megváltoztatja, így a
        mappaváltás gyorsútja sosem mutathat elavult feedet."""
        stamp = []
        for path in (self._db_path, Path(f"{self._db_path}-wal")):
            try:
                stat = path.stat()
                stamp.append((stat.st_mtime_ns, stat.st_size))
            except OSError:
                stamp.append(None)
        return tuple(stamp)
