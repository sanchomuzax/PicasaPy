"""QML-modellek az SQLite index fölött (csak olvasnak, állapotuk immutábilis
rekord-tuple)."""

from __future__ import annotations

import re
import sqlite3

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, QUrl, Slot

from picasapy.index import PhotoRecord

# Importált Windows-útvonalak is előfordulhatnak a folders táblában.
_PATH_SEPARATORS = re.compile(r"[/\\]")


class FolderListModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    PathRole = Qt.ItemDataRole.UserRole + 2
    CountRole = Qt.ItemDataRole.UserRole + 3

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folders: tuple[tuple[str, str, int], ...] = ()

    def load(self, conn: sqlite3.Connection) -> None:
        rows = conn.execute(
            "SELECT f.path, count(p.id) AS n FROM folders f "
            "LEFT JOIN photos p ON p.folder_id = f.id "
            "GROUP BY f.id ORDER BY f.path"
        ).fetchall()
        self.beginResetModel()
        self._folders = tuple(
            (_PATH_SEPARATORS.split(row["path"])[-1], row["path"], row["n"])
            for row in rows
        )
        self.endResetModel()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._folders)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._folders):
            return None
        name, path, count = self._folders[index.row()]
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return name
        if role == self.PathRole:
            return path
        if role == self.CountRole:
            return count
        return None

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.PathRole: b"path",
            self.CountRole: b"count",
        }


class PhotoGridModel(QAbstractListModel):
    NameRole = Qt.ItemDataRole.UserRole + 1
    ThumbUrlRole = Qt.ItemDataRole.UserRole + 2
    StarRole = Qt.ItemDataRole.UserRole + 3
    CaptionRole = Qt.ItemDataRole.UserRole + 4
    IsVideoRole = Qt.ItemDataRole.UserRole + 5
    TakenAtRole = Qt.ItemDataRole.UserRole + 6
    FileUrlRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, parent=None):
        super().__init__(parent)
        self._photos: tuple[PhotoRecord, ...] = ()

    def set_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        self.beginResetModel()
        self._photos = photos
        self.endResetModel()

    @property
    def photos(self) -> tuple[PhotoRecord, ...]:
        return self._photos

    @Slot(int, result=str)
    def fileUrlAt(self, row: int) -> str:
        """A kép file:// URL-je a nézőnek; üres, ha az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return QUrl.fromLocalFile(f"{photo.folder_path}/{photo.name}").toString()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._photos)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._photos):
            return None
        photo = self._photos[index.row()]
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return photo.name
        if role == self.ThumbUrlRole:
            return f"image://thumbs/{photo.id}"
        if role == self.StarRole:
            return photo.star
        if role == self.CaptionRole:
            return photo.caption or ""
        if role == self.IsVideoRole:
            return photo.kind == "video"
        if role == self.TakenAtRole:
            return photo.taken_at or ""
        if role == self.FileUrlRole:
            return QUrl.fromLocalFile(
                f"{photo.folder_path}/{photo.name}"
            ).toString()
        return None

    def roleNames(self):
        return {
            self.NameRole: b"name",
            self.ThumbUrlRole: b"thumbUrl",
            self.StarRole: b"star",
            self.CaptionRole: b"caption",
            self.IsVideoRole: b"isVideo",
            self.TakenAtRole: b"takenAt",
            self.FileUrlRole: b"fileUrl",
        }
