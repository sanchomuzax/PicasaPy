"""QML-modellek az SQLite index fölött (csak olvasnak, állapotuk immutábilis
rekord-tuple)."""

from __future__ import annotations

import re
import sqlite3
import zlib

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
        self._set_rows(
            _with_year_separators(
                (name, path, count, date)
                for name, path, count, date, _size, _change in folders
            )
        )

    def load_matches(self, groups) -> None:
        """Keresési találatok mappái (#49): csak a találatos mappák
        látszanak, a darabszám a találatok száma. Évszám-elválasztó nélkül —
        a Picasa találati mappalistája is sima felsorolás."""
        self._set_rows(
            tuple(
                ("folder", g.folder_name, g.folder_path, len(g.photos))
                for g in groups
            )
        )

    def _set_rows(self, rows: tuple[tuple[str, str, str, int], ...]) -> None:
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

    def folder_paths(self) -> tuple[str, ...]:
        """A hasáb mappa-sorrendje (évszám-elválasztók nélkül) — a rács-feed
        (#64) ebben a sorrendben fűzi egymás után a mappákat."""
        return tuple(row[2] for row in self._rows if row[0] == "folder")

    @Slot(str, result=int)
    def rowOfPath(self, path: str) -> int:
        """A mappa sor-indexe (évszám-sorokkal együtt számolva); -1, ha
        nincs ilyen mappa — a lista ebből görgeti láthatóra a kijelöltet."""
        for i, row in enumerate(self._rows):
            if row[0] == "folder" and row[2] == path:
                return i
        return -1

    @Slot(str, int, result=str)
    def neighborFolder(self, path: str, delta: int) -> str:
        """A `path` mappától `delta` lépésre lévő mappa útvonala (#77).

        Az évszám-elválasztó sorokat átugorja, a lista szélein megáll.
        Ismeretlen vagy üres path esetén az első mappát adja; üres listán
        üres sztringet.
        """
        folders = [row[2] for row in self._rows if row[0] == "folder"]
        if not folders:
            return ""
        if path not in folders:
            return folders[0]
        target = folders.index(path) + delta
        return folders[max(0, min(len(folders) - 1, target))]

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


def _has_edits(photo: PhotoRecord) -> bool:
    """Van-e a képen Picasa-szerkesztés (#100) — a kék visszahajtás-jelölő
    feltétele. A `filters=` lánc megléte dönt: a vágott képeknél a crop64 a
    filters-történetben is szerepel, így a crop= külön indexelése nélkül is
    lefedett; a sima forgatás (rotate=) és a csillag NEM módosítás."""
    return bool(photo.filters and photo.filters.strip())


def _thumb_url(photo: PhotoRecord) -> str:
    """Thumb-URL forgatás- és szerkesztés-érzékeny cache-busterrel (#59)."""
    filters_tag = zlib.crc32((photo.filters or "").encode("utf-8"))
    return f"image://thumbs/{photo.id}?r={photo.rotate_steps}&f={filters_tag}"


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
    FolderPathRole = Qt.ItemDataRole.UserRole + 10

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
        # #142: változatlan tartalomnál no-op — a reset eldobná a
        # delegate-eket és a revision-bump minden élő cellát újraköttetne,
        # így minden háttér-szinkron a teljes rácsot újrarajzolná
        # (a FolderListModel._set_rows mintája).
        if photos == self._photos:
            return
        self.beginResetModel()
        self._photos = photos
        self.endResetModel()
        self._revision += 1
        self.revisionChanged.emit()

    @property
    def photos(self) -> tuple[PhotoRecord, ...]:
        return self._photos

    def row_of_id(self, photo_id: int) -> int:
        """A fotó sor-indexe id alapján; -1, ha nincs a jelen nézetben
        (#141: a célzott frissítés így akkor sem hibázik, ha a sor
        időközben — pl. mappaváltás miatt — kikerült a nézetből)."""
        for i, photo in enumerate(self._photos):
            if photo.id == photo_id:
                return i
        return -1

    def update_photo(self, photo_id: int, record: PhotoRecord) -> None:
        """Egy sor célzott frissítése (csillag/felirat/forgatás, #141):
        NEM fut teljes beginResetModel/endResetModel — a görgetés és a
        delegate-ek megmaradnak. A `revision` mégis nő (ez hajtja a QML
        itemAt/revision-mintáját, ld. fent), és a sorra dataChanged is
        kimegy azoknak, akik szerep-alapú kötést használnak."""
        row = self.row_of_id(photo_id)
        if row < 0:
            return
        self._photos = self._photos[:row] + (record,) + self._photos[row + 1 :]
        self._revision += 1
        self.revisionChanged.emit()
        index = self.index(row, 0)
        self.dataChanged.emit(index, index)

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
        return _thumb_url(photo)

    @Slot(int, result="QVariantMap")
    def itemAt(self, row: int) -> dict:
        """Egy sor teljes rács-adata a feed-delegate-nek (#64) — a
        csoportokra bontott rács Repeater-e nem modell-szerepekből köt,
        hanem ebből a dict-ből (a photos.revision-nel együtt kötve)."""
        if not 0 <= row < len(self._photos):
            return {}
        photo = self._photos[row]
        return {
            "name": photo.name,
            "thumbUrl": _thumb_url(photo),
            "star": photo.star,
            "caption": photo.caption or "",
            "isVideo": photo.kind == "video",
            "keywords": photo.keywords or "",
            "resolution": (
                f"{photo.width}x{photo.height}"
                if photo.width and photo.height
                else ""
            ),
            "hasEdits": _has_edits(photo),
            "hidden": photo.hidden,
        }

    @Slot(int, result=bool)
    def starAt(self, row: int) -> bool:
        """A sor csillag-állapota (a tálca ★ gombjának színezéséhez)."""
        return 0 <= row < len(self._photos) and self._photos[row].star

    @Slot(int, result=bool)
    def isVideoAt(self, row: int) -> bool:
        """Videó-e a sor (#14) — a néző erre vált lejátszó-nézetre."""
        return 0 <= row < len(self._photos) and self._photos[row].kind == "video"

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

    @Slot(int, int, result=int)
    def folderNeighbor(self, row: int, delta: int) -> int:
        """A `row` sortól `delta` lépés a SAJÁT mappáján belül (#84).

        A nagy nézőben (PhotoViewer) a lapozás nem léphet át a szomszéd
        mappába, még akkor sem, ha a rács-modell (pl. csillag-szűrő,
        keresés) több mappa fotóit sorolja fel egymás után — a
        lekérdezések mindig mappa szerint rendezettek (f.path, p.name),
        így egy mappa fotói a listában folytonos tartományt alkotnak, és
        elég egyesével lépkedni, amíg a mappa-útvonal egyezik. A
        mappahatáron (vagy érvénytelen sornál) a lépés a helyben marad —
        ez adja a néző nyíl-/görgő-navigációjának és a ◀/▶ gombok
        enabled-jének is az alapját."""
        if not 0 <= row < len(self._photos) or delta == 0:
            return row
        folder = self._photos[row].folder_path
        step = 1 if delta > 0 else -1
        result = row
        for _ in range(abs(delta)):
            candidate = result + step
            if (
                not 0 <= candidate < len(self._photos)
                or self._photos[candidate].folder_path != folder
            ):
                break
            result = candidate
        return result

    @Slot(int, result=str)
    def filePathAt(self, row: int) -> str:
        """A kép abszolút útvonala (EditController.beginEdit-hez); üres, ha
        az index érvénytelen."""
        if not 0 <= row < len(self._photos):
            return ""
        photo = self._photos[row]
        return f"{photo.folder_path}/{photo.name}"

    def _group_bounds(self) -> tuple[tuple[int, int], ...]:
        """(start, count) mappánként, a feed sorrendjében — a fel/le
        léptetés rácssor-számításához (#77)."""
        bounds: list[tuple[int, int]] = []
        start = 0
        for i in range(1, len(self._photos)):
            if self._photos[i].folder_path != self._photos[i - 1].folder_path:
                bounds.append((start, i - start))
                start = i
        if self._photos:
            bounds.append((start, len(self._photos) - start))
        return tuple(bounds)

    @Slot(int, str, int, result=int)
    def navigate(self, row: int, direction: str, columns: int) -> int:
        """Kurzor-léptetés célsora a rács-feedben (#77).

        Balra/jobbra folytonos (mappahatáron is átlép, ahogy a feed maga);
        fel/le a mappa-csoport rácssorai közt ugrik `columns` oszloppal,
        a csoport szélén a szomszéd csoport azonos oszlopára lép. Érvénytelen
        sorról (pl. −1, nincs kijelölés) az első képre lép; üres modellnél −1.
        """
        count = len(self._photos)
        if count == 0:
            return -1
        if not 0 <= row < count:
            return 0
        if direction == "left":
            return max(0, row - 1)
        if direction == "right":
            return min(count - 1, row + 1)
        if direction not in ("up", "down"):
            return row
        cols = max(1, columns)
        bounds = self._group_bounds()
        group = next(i for i, (s, n) in enumerate(bounds) if s <= row < s + n)
        start, group_count = bounds[group]
        local = row - start
        grid_row, col = divmod(local, cols)
        if direction == "down":
            if grid_row < (group_count - 1) // cols:
                return start + min(local + cols, group_count - 1)
            if group + 1 < len(bounds):
                next_start, next_count = bounds[group + 1]
                return next_start + min(col, next_count - 1)
            return row
        if grid_row > 0:
            return start + local - cols
        if group > 0:
            prev_start, prev_count = bounds[group - 1]
            last_grid_row = (prev_count - 1) // cols
            return prev_start + min(last_grid_row * cols + col, prev_count - 1)
        return row

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._photos)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._photos):
            return None
        photo = self._photos[index.row()]
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return photo.name
        if role == self.ThumbUrlRole:
            # cache-buster: forgatás/szerkesztés után új URL → friss kép (#59)
            return _thumb_url(photo)
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
        if role == self.FolderPathRole:
            return photo.folder_path
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
            self.FolderPathRole: b"folderPath",
        }
