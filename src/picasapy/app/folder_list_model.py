"""SQLite-alapú mappalista QML-nézetekhez."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterable

from PySide6.QtCore import Property, QAbstractListModel, Qt, Signal, Slot

from picasapy.index.hidden_scope import show_hidden_folders
from picasapy.paths import flat_key

from .model_helpers import (
    _PATH_SEPARATORS,
    _ROOT_INDEX,
    _descending,
    _rejtett_csomopont,
    _sort_key,
    _with_year_separators,
)

def sorted_folder_rows(
    conn: sqlite3.Connection,
    sort_mode: str = "date",
    reverse: bool = False,
    *,
    include_hidden: bool | None = None,
) -> list[tuple[str, str, int, str, int, int, bool, bool, bool]]:
    """A mappák (név, útvonal, darabszám, dátum, méret, változás, offline,
    rejtett, olvasatlan) sorai a kért rendezésben.

    Külön függvény, mert két, egymástól FÜGGETLEN sorrendet kell kiszolgálnia
    (#321): a bal hasáb a saját, rögzített Picasa-sorrendjében áll, a rács
    (feed) viszont a Mappa ▸ Rendezés beállítását követi (#1454-ig ez a
    menü Nézet ▸ Mappanézet néven szerepelt — tévesen).
    """
    # #1637: a REJTETT mappák alapból kimaradnak — ugyanaz a Nézet ▸
    # Rejtett képek kapcsoló hozza vissza őket, ami a rejtett fotókat.
    # #4887: `None` = a felület által az indexszel közölt láthatóság
    # (képernyővédő-forráslista, feed-sorrend).
    if include_hidden is None:
        include_hidden = show_hidden_folders(conn)
    rejtett_szuro = "" if include_hidden else " WHERE f.hidden = 0"
    db_rows = conn.execute(
        "SELECT f.path, f.date, f.offline, f.hidden, f.unread,"
        " count(p.id) AS n,"
        " COALESCE(SUM(p.size), 0) AS total_size,"
        " COALESCE(MAX(p.mtime_ns), 0) AS last_change"
        " FROM folders f LEFT JOIN photos p ON p.folder_id = f.id"
        f"{rejtett_szuro}"
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
            # #459/5: a jelenleg nem elérhető mappa jelölése — a sor
            # bennmarad a listában, csak külön jelzést kap.
            bool(row["offline"]),
            # #1637/2: a rejtettség a soron utazik, hogy a hívó a
            # „Rejtett mappák" csomópont alá tudja gyűjteni őket
            bool(row["hidden"]),
            # #1644: „olvasatlan" — új kép került a mappába, amit a
            # felhasználó még nem nézett meg. A bal hasáb KÖVÉREN szedi.
            bool(row["unread"]),
        )
        for row in db_rows
    ]
    folders.sort(key=_sort_key(sort_mode), reverse=_descending(sort_mode) != reverse)
    return folders


def folder_order(
    conn: sqlite3.Connection, sort_mode: str = "date", reverse: bool = False
) -> tuple[str, ...]:
    """Csak a mappa-útvonalak a kért sorrendben (a rács sorrendjéhez, #321)."""
    return tuple(path for _name, path, *_rest in sorted_folder_rows(
        conn, sort_mode, reverse
    ))


class FolderListModel(QAbstractListModel):
    """Mappa-lista évszám-elválasztó sorokkal (Picasa-minta).

    Egy sor: (kind, name, path, count) — kind='year' az elválasztó,
    kind='folder' a kattintható mappa.
    """

    KindRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    PathRole = Qt.ItemDataRole.UserRole + 3
    CountRole = Qt.ItemDataRole.UserRole + 4
    # #459/5: „jelenleg nem elérhető" (levált NAS-mount, kihúzott lemez)
    OfflineRole = Qt.ItemDataRole.UserRole + 5
    #: #1644: „olvasatlan" — új kép került a mappába. A bal hasáb KÖVÉREN
    #: szedi, ahogy az eredeti is (a tulajdonos élő megfigyelése).
    UnreadRole = Qt.ItemDataRole.UserRole + 6

    folderCountChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._rows: tuple[tuple[str, str, str, int, bool, bool], ...] = ()

    def load(
        self,
        conn: sqlite3.Connection,
        sort_mode: str = "date",
        reverse: bool = False,
        *,
        include_hidden: bool = False,
        exclude_paths: Iterable[str] = (),
    ) -> None:
        """Mappalista Picasa-rendezéssel.

        sort_mode: 'date' (létrehozási dátum, legújabb elöl — alapérték),
        'changed' (legutóbbi változtatás), 'size' (méret), 'név' (name).
        A reverse a kiválasztott rendezést fordítja meg.

        `exclude_paths` (#2031): a PROJEKT-mappák útvonalai. A `P2category`
        az eredetiben **kizáró**: egy projekt-mappa CSAK a Projektek alatt
        látszik, a Mappák listában nem (#1033 verdiktje,
        `docs/specs/export-parbeszed.md` 12.5).

        ⚠️ A mappa az INDEXBEN marad — a kategória megjelenítési
        besorolás, nem törlés. A fotói, a keresés és a darabszámok
        érintetlenek; a Projektek alól ugyanaz a rács nyílik.
        """
        kizart = {str(u) for u in exclude_paths}
        folders = [
            sor
            for sor in sorted_folder_rows(
                conn, sort_mode, reverse, include_hidden=include_hidden
            )
            if sor[1] not in kizart
        ]
        # #1637/2: a rejtett mappák nem VEGYÜLNEK vissza a listába — a
        # végén, saját fejléc alatt állnak. Az eredetiben az elrejtés
        # adatvédelmi funkció (`IDS_HIDDEN` = „Rejtett mappák"), nem
        # nézeti szűrő: a csomópont léte a funkció lényege. Nélküle a
        # bekapcsolt kapcsoló mellett nem lehetne megmondani, melyik
        # mappa volt elrejtve.
        rows = (
            (name, path, count, date, offline, unread)
            for name, path, count, date, _size, _change, offline, hidden, unread
            in folders
            if not hidden
        )
        rejtettek = tuple(
            ("folder", name, path, count, offline, unread)
            for name, path, count, _date, _size, _change, offline, hidden, unread
            in folders
            if hidden
        )
        # #461/3: az ÉVSZÁM-csoportok a DÁTUM-nézethez tartoznak. Név vagy
        # méret szerinti rendezésnél a fejlécek értelmüket vesztenék (egy
        # évszám többször, összevissza sorrendben bukkanna fel), ezért ott
        # sima felsorolás áll — ahogy az eredetiben is.
        if sort_mode in ("date", "changed"):
            lathato = _with_year_separators(rows)
        else:
            lathato = tuple(
                ("folder", name, path, count, offline, unread)
                for name, path, count, _date, offline, unread in rows
            )
        self._set_rows(lathato + _rejtett_csomopont(rejtettek))

    def load_matches(self, groups) -> None:
        """Keresési találatok mappái (#49): csak a találatos mappák
        látszanak, a darabszám a találatok száma. Évszám-elválasztó nélkül —
        a Picasa találati mappalistája is sima felsorolás."""
        self._set_rows(
            tuple(
                #: #1644: a keresési TALÁLATOK listája sosem „olvasatlan" —
                #: a jelölő a mappa tartalmának újdonságáról szól, nem a
                #: találatokéról.
                (
                    "folder",
                    g.folder_name,
                    g.folder_path,
                    len(g.photos),
                    False,
                    False,
                )
                for g in groups
            )
        )

    def _set_rows(
        self, rows: tuple[tuple[str, str, str, int, bool, bool], ...]
    ) -> None:
        # Változatlan adatnál nincs reset: a reset eldobná a delegate-eket
        # és nullázná a görgetést, így a lista minden háttér-szinkronnál
        # a tetejére ugrana (#10).
        if rows == self._rows:
            return
        self.beginResetModel()
        self._rows = rows
        self.endResetModel()
        self.folderCountChanged.emit()

    def rowCount(self, parent=_ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._rows)

    @Property(int, notify=folderCountChanged)
    def folderCount(self) -> int:
        """Csak a valódi mappák száma (az évszám-elválasztók nélkül)."""
        return sum(1 for row in self._rows if row[0] == "folder")

    def offline_paths(self) -> frozenset[str]:
        """A jelenleg nem elérhető mappák útvonalai (#459/5) — ebből tudja a
        vezérlő, hogy a mappára irányuló műveletnél értelmes üzenetet
        adjon néma bukás helyett."""
        return frozenset(
            row[2] for row in self._rows if row[0] == "folder" and row[4]
        )

    def folder_paths(self) -> tuple[str, ...]:
        """A hasáb mappa-sorrendje (évszám-elválasztók nélkül) — a rács-feed
        (#64) ebben a sorrendben fűzi egymás után a mappákat."""
        return tuple(row[2] for row in self._rows if row[0] == "folder")

    @Slot(str, result=int)
    def rowOfPath(self, path: str) -> int:
        """A mappa sor-indexe (évszám-sorokkal együtt számolva); -1, ha
        nincs ilyen mappa — a lista ebből görgeti láthatóra a kijelöltet.

        #3776: az összehasonlítás `flat_key`-jel megy — a nyers pontos
        egyezés egy eltérő betűzésű Windows-gyökér alatt (a mentés-szűrő
        lapos listáját hívja innen a `FolderPane`) hamis negatívot adna."""
        kulcs = flat_key(path)
        for i, row in enumerate(self._rows):
            if row[0] == "folder" and flat_key(row[2]) == kulcs:
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
        kind, name, path, count, offline, unread = self._rows[index.row()]
        if role == self.KindRole:
            return kind
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return name
        if role == self.PathRole:
            return path
        if role == self.CountRole:
            return count
        if role == self.OfflineRole:
            return offline
        if role == self.UnreadRole:
            return unread
        return None

    def roleNames(self):
        return {
            self.KindRole: b"kind",
            self.NameRole: b"name",
            self.PathRole: b"path",
            self.CountRole: b"count",
            self.OfflineRole: b"offline",
            self.UnreadRole: b"unread",
        }
