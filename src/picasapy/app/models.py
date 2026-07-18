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

    def load(
        self,
        conn: sqlite3.Connection,
        sort_mode: str = "date",
        reverse: bool = False,
    ) -> None:
        """Mappalista Picasa-rendezéssel.

        sort_mode: 'date' (létrehozási dátum, legújabb elöl — alapérték),
        'changed' (legutóbbi változtatás), 'size' (méret), 'name' (név).
        A reverse a kiválasztott rendezést fordítja meg.
        """
        db_rows = conn.execute(
            "SELECT f.path, f.date, count(p.id) AS n,"
            " COALESCE(SUM(p.size), 0) AS total_size,"
            " COALESCE(MAX(p.mtime_ns), 0) AS last_change"
            " FROM folders f LEFT JOIN photos p ON p.folder_id = f.id"
            " GROUP BY f.id ORDER BY f.path"
        ).fetchall()
        folders = [
            (
                _PATH_SEPARATORS.split(row["path"])[-1],
                row["path"],
                row["n"],
                row["date"],
                row["total_size"],
                row["last_change"],
            )
            for row in db_rows
        ]
        folders.sort(key=_sort_key(sort_mode), reverse=_descending(sort_mode) != reverse)
        rows = _with_year_separators(
            (name, path, count, date)
            for name, path, count, date, _size, _change in folders
        )
        # Változatlan adatnál nincs reset: a reset eldobná a delegate-eket
        # és nullázná a görgetést, így a lista minden háttér-szinkronnál
        # a tetejére ugrana (#10).
        if rows == self._rows:
            return
        self.beginResetModel()
        self._rows = rows
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


def _sort_key(sort_mode: str):
    """Rendezőkulcs; dátum-módokban a dátumtalan mappák a sor végére."""
    if sort_mode == "name":
        return lambda f: f[0].casefold()
    if sort_mode == "size":
        return lambda f: f[4]
    if sort_mode == "changed":
        return lambda f: f[5]
    return lambda f: (f[3] is not None, f[3] or "", f[1])


def _descending(sort_mode: str) -> bool:
    """A Picasa alapértéke: dátum/változás/méret csökkenő, név növekvő."""
    return sort_mode != "name"


def _with_year_separators(folders) -> tuple[tuple[str, str, str, int], ...]:
    """Évszám-elválasztók a mappa-dátum évéből (fallback: név-prefix)."""
    rows = []
    last_year = None
    for name, path, count, date in folders:
        year = None
        if date:
            year = date[:4]
        else:
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
    KeywordsRole = Qt.ItemDataRole.UserRole + 8
    ResolutionRole = Qt.ItemDataRole.UserRole + 9

    revisionChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._photos: tuple[PhotoRecord, ...] = ()
        self._revision = 0

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        """Minden set_photos-nál nő — QML-kötések frissítés-triggere.

        (A statusText-re kötés nem elég: pl. forgatásnál a szöveg nem
        változik, így a kötés nem értékelődne újra.)
        """
        return self._revision

    def set_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        self.beginResetModel()
        self._photos = photos
        self.endResetModel()
        self._revision += 1
        self.revisionChanged.emit()

    @property
    def photos(self) -> tuple[PhotoRecord, ...]:
        return self._photos

    @Slot(int, result=int)
    def rotateAt(self, row: int) -> int:
        """A sor nem-destruktív forgatási lépésszáma (0–3) a nézőnek."""
        if not 0 <= row < len(self._photos):
            return 0
        return self._photos[row].rotate_steps

    @Slot(int, result=str)
    def thumbUrlAt(self, row: int) -> str:
        """Thumbnail-URL a kijelölés-tálca miniatűrjeihez."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return f"image://thumbs/{photo.id}?r={photo.rotate_steps}"

    @Slot(int, result=bool)
    def starAt(self, row: int) -> bool:
        """A sor csillag-állapota (a tálca ★ gombjának színezéséhez)."""
        return 0 <= row < len(self._photos) and self._photos[row].star

    @Slot(int, result=str)
    def captionAt(self, row: int) -> str:
        """A sor felirata (üres, ha nincs vagy az index érvénytelen) — a
        néző szerkeszthető felirat-mezőjének."""
        if not 0 <= row < len(self._photos):
            return ""
        return self._photos[row].caption or ""

    @Slot(int, result=str)
    def fileUrlAt(self, row: int) -> str:
        """A kép file:// URL-je a nézőnek; üres, ha az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return QUrl.fromLocalFile(f"{photo.folder_path}/{photo.name}").toString()

    @Slot(int, result=str)
    def idAt(self, row: int) -> str:
        """A sor fotó-azonosítója — az EditController/editpreview kulcsa."""
        if not 0 <= row < len(self._photos):
            return ""
        return str(self._photos[row].id)

    @Slot(int, result=str)
    def filePathAt(self, row: int) -> str:
        """A kép abszolút útvonala (EditController.beginEdit-hez); üres, ha
        az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return f"{photo.folder_path}/{photo.name}"

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._photos)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._photos):
            return None
        photo = self._photos[index.row()]
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return photo.name
        if role == self.ThumbUrlRole:
            # a lépésszám cache-buster: forgatás után új URL → friss kép
            return f"image://thumbs/{photo.id}?r={photo.rotate_steps}"
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
        if role == self.KeywordsRole:
            return photo.keywords or ""
        if role == self.ResolutionRole:
            return (
                f"{photo.width}x{photo.height}"
                if photo.width and photo.height
                else ""
            )
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
            self.KeywordsRole: b"keywords",
            self.ResolutionRole: b"resolution",
        }
