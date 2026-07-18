"""Az alkalmazás vezérlője: index-lekérdezések és a QML közti híd."""

from __future__ import annotations

import re
import threading
from pathlib import Path

from PySide6.QtCore import (
    Property,
    QDate,
    QDateTime,
    QLocale,
    QObject,
    Signal,
    Slot,
)

from picasapy.index import (
    open_index,
    photos_in_folder,
    search_photos,
    starred_photos,
    sync_tree,
)
from picasapy.ini import load_document, parse_document, save_document
from picasapy.scanner import PICASA_INI_NAME
from .models import FolderListModel, PhotoGridModel
from .thumbnail_provider import ThumbnailProvider


_PATH_TAIL = re.compile(r"[/\\]")


class AppController(QObject):
    statusChanged = Signal()
    syncFinished = Signal()
    syncFailed = Signal(str)

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
        self._folder_date = ""
        self._sync_running = False
        self._view_mode = ("folder", "")  # (mód, paraméter) az újratöltéshez
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

    @Property(str, notify=statusChanged)
    def folderDateText(self):
        """A mappa-fejléc dátumsora (a legkorábbi felvétel hosszú dátuma)."""
        return self._folder_date

    # -- műveletek ----------------------------------------------------------

    def start(self) -> None:
        """Indulás: modellek betöltése, majd háttér-szinkron."""
        self._reload()
        self.rescan()

    @Slot()
    def rescan(self) -> None:
        if self._sync_running:
            return  # egy író elég; a futó szinkron végén úgyis frissülünk
        self._sync_running = True
        threading.Thread(target=self._sync_worker, daemon=True).start()

    @Slot(str)
    def selectFolder(self, folder_path: str) -> None:
        self._current_folder = folder_path
        self._view_mode = ("folder", folder_path)
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
                self._view_mode = ("search", query)
                records = search_photos(conn, query)
        self._show(records)

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        ini_path = Path(photo.folder_path) / PICASA_INI_NAME
        document = (
            load_document(ini_path) if ini_path.exists() else parse_document("")
        )
        if photo.star:
            document = document.with_removed(photo.name, "star")
        else:
            document = document.with_value(photo.name, "star", "yes")
        save_document(document, ini_path, backup=True)
        with open_index(self._db_path) as conn:
            sync_tree(conn, photo.folder_path)
        self._refresh_view()

    def _refresh_view(self) -> None:
        """Az aktuális nézet újratöltése az indexből (mód szerint)."""
        mode, param = self._view_mode
        if mode == "search":
            with open_index(self._db_path) as conn:
                self._show(search_photos(conn, param))
        elif mode == "starred":
            with open_index(self._db_path) as conn:
                self._show(starred_photos(conn))
        elif param:
            with open_index(self._db_path) as conn:
                self._show(photos_in_folder(conn, param))

    @Slot(int, result=str)
    def photoInfo(self, row: int) -> str:
        """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
        `név   dátum   SZxM képpont   méret`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        locale = QLocale()
        parts = [photo.name]
        if photo.taken_at:
            taken = QDateTime.fromString(photo.taken_at, "yyyy-MM-ddTHH:mm:ss")
            parts.append(locale.toString(taken, QLocale.FormatType.ShortFormat))
        if photo.width and photo.height:
            parts.append(
                self.tr("%1x%2 pixels")
                .replace("%1", str(photo.width))
                .replace("%2", str(photo.height))
            )
        parts.append(_format_size(photo.size, locale, self.tr))
        return "   ".join(parts)

    @Slot(int, result=str)
    def viewerInfo(self, row: int) -> str:
        """A néző infó-sávja: `mappa > név   ...   (i / N)` — Picasa-minta."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        folder = _PATH_TAIL.split(photo.folder_path)[-1]
        base = self.photoInfo(row).replace(photo.name, f"{folder} > {photo.name}", 1)
        return f"{base}   ({row + 1} / {len(photos)})"

    @Slot()
    def showStarred(self) -> None:
        self._current_folder = ""
        self._view_mode = ("starred", "")
        with open_index(self._db_path) as conn:
            records = starred_photos(conn)
        self._show(records)

    # -- belső --------------------------------------------------------------

    def _sync_worker(self) -> None:
        """Háttér-szinkron. Egy rossz gyökér (pl. elavult Windows-útvonal a
        WatchedFolders-ből) nem nyelhet el mindent némán: hibánként jelzünk,
        a többi gyökér feldolgozása folytatódik, és a vége mindig
        syncFinished."""
        errors = []
        try:
            with open_index(self._db_path) as conn:
                for root in self._roots:
                    try:
                        sync_tree(conn, root)
                    except (OSError, RuntimeError) as error:
                        errors.append(f"{root}: {error}")
        except Exception as error:  # pl. index-migrációs hiba
            errors.append(str(error))
        finally:
            self._sync_running = False
            if errors:
                self.syncFailed.emit("; ".join(errors))
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
        dates = sorted(r.taken_at for r in records if r.taken_at)
        self._folder_date = _long_date(dates[0], QLocale()) if dates else ""
        self._update_status(records)

    def _update_status(self, records) -> None:
        if not records:
            self._status = self.tr("0 pictures")
        else:
            locale = QLocale()
            total_mb = sum(r.size for r in records) / (1024 * 1024)
            dates = sorted(r.taken_at for r in records if r.taken_at)
            date_part = ""
            if dates:
                first = _long_date(dates[0], locale)
                last = _long_date(dates[-1], locale)
                date_part = first if first == last else f"{first}-{last}"
            self._status = self.tr("%n picture(s)", "", len(records)) + (
                f"   {date_part}   " if date_part else "   "
            ) + self.tr("%1 MB on disk").replace(
                "%1", locale.toString(total_mb, "f", 1)
            )
        self.statusChanged.emit()


def _long_date(iso: str, locale: QLocale) -> str:
    """Picasa-stílusú hosszú dátum: `2026. január 2., péntek`."""
    date = QDate.fromString(iso[:10], "yyyy-MM-dd")
    return locale.toString(date, QLocale.FormatType.LongFormat)


def _format_size(size_bytes: int, locale: QLocale, tr) -> str:
    if size_bytes < 1024 * 1024:
        return tr("%1 KB").replace("%1", str(round(size_bytes / 1024)))
    return tr("%1 MB").replace(
        "%1", locale.toString(size_bytes / (1024 * 1024), "f", 1)
    )
