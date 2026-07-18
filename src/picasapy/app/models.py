"""QML-modellek az SQLite index fölött (csak olvasnak, állapotuk immutábilis
rekord-tuple)."""

from __future__ import annotations

import re
import sqlite3

from PySide6.QtCore import (
    Property,
    QAbstractListModel,
    QModelIndex,
    Qt,
    QUrl,
    Signal,
    Slot,
)

from picasapy.index import PhotoRecord

# Importált Windows-útvonalak is előfordulhatnak a folders táblában.
_PATH_SEPARATORS = re.compile(r"[/\\]")
_YEAR_PREFIX = re.compile(r"^(\d{4})")


class FolderListModel(QAbstractListModel):
    """Mappa-lista évszám-elválasztó sorokkal (Picasa-minta).

    Egy sor: (kind, name, path, count) — kind='year' az elválasztó,
    kind='folder' a kattintható mappa.
    """

    KindRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    PathRole = Qt.ItemDataRole.UserRole + 3
    CountRole = Qt.ItemDataRole.UserRole + 4

    folderCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: tuple[tuple[str, str, str, int], ...] = ()

    def load(self, conn: sqlite3.Connection) -> None:
        db_rows = conn.execute(
            "SELECT f.path, count(p.id) AS n FROM folders f "
            "LEFT JOIN photos p ON p.folder_id = f.id "
            "GROUP BY f.id ORDER BY f.path"
        ).fetchall()
        self.beginResetModel()
        self._rows = _with_year_separators(
            (_PATH_SEPARATORS.split(row["path"])[-1], row["path"], row["n"])
            for row in db_rows
        )
        self.endResetModel()
        self.folderCountChanged.emit()

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._rows)

    @Property(int, notify=folderCountChanged)
    def folderCount(self) -> int:
        """Csak a valódi mappák száma (az évszám-elválasztók nélkül)."""
        return sum(1 for row in self._rows if row[0] == "folder")

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._rows):
            return None
        kind, name, path, count = self._rows[index.row()]
        if role == self.KindRole:
            return kind
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return name
        if role == self.PathRole:
            return path
        if role == self.CountRole:
            return count
        return None

    def roleNames(self):
        return {
            self.KindRole: b"kind",
            self.NameRole: b"name",
            self.PathRole: b"path",
            self.CountRole: b"count",
        }


def _with_year_separators(folders) -> tuple[tuple[str, str, str, int], ...]:
    rows = []
    last_year = None
    for name, path, count in folders:
        match = _YEAR_PREFIX.match(name)
        year = match.group(1) if match else None
        if year and year != last_year:
            rows.append(("year", year, "", 0))
        last_year = year
        rows.append(("folder", name, path, count))
    return tuple(rows)


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

    @Slot(int, result=bool)
    def starAt(self, row: int) -> bool:
        """A sor csillag-állapota (a tálca ★ gombjának színezéséhez)."""
        return 0 <= row < len(self._photos) and self._photos[row].star

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
