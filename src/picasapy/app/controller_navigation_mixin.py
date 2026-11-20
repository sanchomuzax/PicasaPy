"""A mappanavigáció és az index állapotának segédei."""

from __future__ import annotations

from pathlib import Path
from PySide6.QtCore import QObject, Qt, Signal, Slot
from picasapy.index import open_index
from picasapy.index.hidden_scope import visible_folder_sql


class _UnreadClearSignals(QObject):
    finished = Signal(int, str, bool)


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
                    " WHERE (f.has_ini = 0 OR EXISTS ("
                    " SELECT 1 FROM photos p WHERE p.folder_id = f.id))"
                    f" AND {visible_folder_sql(conn)} ORDER BY path"
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
        self._folder_description = self._folder_description_for_open(folder_path)
        self.statusChanged.emit()

    def _clear_unread(self, folder_path: str) -> None:
        """Az „olvasatlan" jelölő törlése egy mappára (#1644).

        Csak akkor ír, ha a jelölő tényleg fent van: a mappaváltás gyakori
        művelet, és egy feltétel nélküli UPDATE minden kattintásra
        WAL-bejegyzést szülne (a #139 azonos megfontolása). Az SQLite
        írása háttérben fut, mert a szinkron írózárára várakozás a GUI-szálat
        is megállíthatja."""
        if not folder_path:
            return
        sequence = getattr(self, "_unread_clear_sequence", 0) + 1
        self._unread_clear_sequence = sequence
        signals = _UnreadClearSignals(self)
        pending = getattr(self, "_unread_clear_signals", None)
        if pending is None:
            pending = self._unread_clear_signals = {}
        pending[sequence] = signals
        signals.finished.connect(
            self._on_unread_clear_finished,
            Qt.ConnectionType.QueuedConnection,
        )

        def worker() -> None:
            changed = False
            try:
                with open_index(self._db_path) as conn:
                    cursor = conn.execute(
                        "UPDATE folders SET unread = 0 WHERE path = ? AND unread = 1",
                        (str(folder_path),),
                    )
                    changed = bool(cursor.rowcount)
                    if changed:
                        conn.commit()
            except Exception:  # noqa: BLE001 — a megnyitás ne várjon az indexre
                import logging

                logging.getLogger(__name__).exception(
                    "Az olvasatlan mappajelölő nem törölhető: %s", folder_path
                )
            signals.finished.emit(sequence, str(folder_path), changed)

        self._start_background(worker, name="picasapy-clear-unread", busy=False)

    @Slot(int, str, bool)
    def _on_unread_clear_finished(
        self, sequence: int, _folder_path: str, changed: bool
    ) -> None:
        signals = getattr(self, "_unread_clear_signals", {}).pop(sequence, None)
        if signals is not None:
            signals.deleteLater()
        if changed:
            # A bal hasáb kövér szedése ebből a mezőből él — újratöltés
            # nélkül a mappa megnyitás után is kövér maradna.
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
                if path.name.endswith("-wal") and stat.st_size == 0:
                    # Az üres WAL nem hordoz adatot: egy olvasó kapcsolat
                    # megnyitása is létrehozhatja, és ettől a feed nem avul
                    # el (#7334, a CI-n ingadozó gyorsút-pecsét).
                    stamp.append(None)
                    continue
                stamp.append((stat.st_mtime_ns, stat.st_size))
            except OSError:
                stamp.append(None)
        return tuple(stamp)
