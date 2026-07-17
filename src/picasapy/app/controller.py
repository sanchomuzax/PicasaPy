"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Property, QObject, Signal, Slot

from picasapy.index import (
    open_index,
    photos_in_folder,
    search_photos,
    starred_photos,
    sync_tree,
)
from .models import FolderListModel, PhotoGridModel
from .thumbnail_provider import ThumbnailProvider


class AppController(QObject):
    statusChanged = Signal()
    syncFinished = Signal()

    def __init__(
        self,
        db_path: Path,
        roots: tuple[str, ...],
        provider: ThumbnailProvider,
        parent=None,
    ):
        super().__init__(parent)
        self._db_path = db_path
        self._roots = roots
        self._provider = provider
        self._folders = FolderListModel(self)
        self._photos = PhotoGridModel(self)
        self._current_folder = ""
        self._status = ""
        self.syncFinished.connect(self._reload)

    # -- QML-nek kitett tulajdonságok --------------------------------------

    @Property(QObject, constant=True)
    def folders(self):
        return self._folders

    @Property(QObject, constant=True)
    def photos(self):
        return self._photos

    @Property(str, notify=statusChanged)
    def statusText(self):
        return self._status

    @Property(str, notify=statusChanged)
    def currentFolder(self):
        return self._current_folder

    # -- műveletek ----------------------------------------------------------

    def start(self) -> None:
        """Indulás: modellek betöltése, majd háttér-szinkron."""
        self._reload()
        self.rescan()

    @Slot()
    def rescan(self) -> None:
        threading.Thread(target=self._sync_worker, daemon=True).start()

    @Slot(str)
    def selectFolder(self, folder_path: str) -> None:
        self._current_folder = folder_path
        with open_index(self._db_path) as conn:
            records = photos_in_folder(conn, folder_path)
        self._show(records)

    @Slot(str)
    def search(self, text: str) -> None:
        query = text.strip()
        with open_index(self._db_path) as conn:
            if not query:
                records = (
                    photos_in_folder(conn, self._current_folder)
                    if self._current_folder
                    else ()
                )
            else:
                records = search_photos(conn, query)
        self._show(records)

    @Slot()
    def showStarred(self) -> None:
        self._current_folder = ""
        with open_index(self._db_path) as conn:
            records = starred_photos(conn)
        self._show(records)

    # -- belső --------------------------------------------------------------

    def _sync_worker(self) -> None:
        with open_index(self._db_path) as conn:
            for root in self._roots:
                sync_tree(conn, root)
        self.syncFinished.emit()

    def _reload(self) -> None:
        with open_index(self._db_path) as conn:
            self._folders.load(conn)
        if self._current_folder:
            self.selectFolder(self._current_folder)
        else:
            self._update_status(())

    def _show(self, records) -> None:
        self._provider.register_photos(records)
        self._photos.set_photos(records)
        self._update_status(records)

    def _update_status(self, records) -> None:
        if not records:
            self._status = self.tr("0 pictures")
        else:
            total_mb = sum(r.size for r in records) / (1024 * 1024)
            dates = sorted(r.taken_at for r in records if r.taken_at)
            date_part = ""
            if dates:
                first, last = dates[0][:10], dates[-1][:10]
                date_part = first if first == last else f"{first} – {last}"
            self._status = self.tr("%n picture(s)", "", len(records)) + (
                f"   {date_part}   " if date_part else "   "
            ) + self.tr("%1 MB on disk").replace("%1", f"{total_mb:.1f}")
        self.statusChanged.emit()
