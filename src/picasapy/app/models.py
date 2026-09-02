"""QML-modellek az SQLite index fölött (csak olvasnak, állapotuk immutábilis
rekord-tuple)."""

from __future__ import annotations

import os
import re
import sqlite3
from pathlib import Path
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

from .display_mode_paint import (
    current_display_mode,
    display_mode_url_suffix,
)
from .photo_sort import DEFAULT_SORT_MODE, sort_folder_blocks

# Importált Windows-útvonalak is előfordulhatnak a folders táblában.
_PATH_SEPARATORS = re.compile(r"[/\\]")
_YEAR_PREFIX = re.compile(r"^(\d{4})")

# A `rowCount(parent=QModelIndex())` Qt-felülírás szokásos alapértéke — mivel
# a QModelIndex() érvénytelen (gyökér-) index, egyetlen, modul-szintű
# példányra hivatkozunk paraméter-alapértékként a B008 (function-call a
# default argumentumban) elkerülésére, viselkedésváltozás nélkül.
_ROOT_INDEX = QModelIndex()


def sorted_folder_rows(
    conn: sqlite3.Connection,
    sort_mode: str = "date",
    reverse: bool = False,
    *,
    include_hidden: bool = False,
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
    ) -> None:
        """Mappalista Picasa-rendezéssel.

        sort_mode: 'date' (létrehozási dátum, legújabb elöl — alapérték),
        'changed' (legutóbbi változtatás), 'size' (méret), 'name' (név).
        A reverse a kiválasztott rendezést fordítja meg.
        """
        folders = sorted_folder_rows(
            conn, sort_mode, reverse, include_hidden=include_hidden
        )
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


def _has_edits(photo: PhotoRecord) -> bool:
    """Van-e a képen Picasa-szerkesztés (#100) — a kék visszahajtás-jelölő
    feltétele. A `filters=` lánc megléte dönt: a vágott képeknél a crop64 a
    filters-történetben is szerepel, így a crop= külön indexelése nélkül is
    lefedett; a sima forgatás (rotate=) és a csillag NEM módosítás."""
    return bool(photo.filters and photo.filters.strip())


def _thumb_url(photo: PhotoRecord, display_mode: str | None = None) -> str:
    """Thumb-URL forgatás-, szerkesztés- és FÁJLVÁLTOZÁS-érzékeny
    cache-busterrel (#59, #1186), megjelenítési mód-cimkével (#1596).

    #1656: a `display_mode` alapértéke MOSTANTÓL a jelenlegi mód, nem az
    üres sztring. Az üres alapérték volt az oka, hogy az idővonal, a
    keresési találatok és a képtálca bélyegképein a mód hatástalan
    maradt: mind ezt a függvényt hívja, csak mód nélkül. A rács modellje
    továbbra is a SAJÁT másolatát adja át (`self._display_mode`), mert az
    a `set_display_mode()`-dal együtt lépteti a `revision`-t is.

    ⚠️ Az `mtime_ns`/`size` nélkül a felülírt fájl URL-je változatlan
    marad (ugyanaz a sor, forgatás és lánc), a Qt pedig URL szerint
    gyorstárazza a képet — a rácson a RÉGI képpontok maradnak. A
    bélyegkép-gyorstár maga jól működik: az is a (útvonal, mtime, méret)
    hármasra kulcsol, csak épp senki nem kérte el az újat. A tulajdonos
    ezt a kollázs véglegesítésekor látta (a „PISZKOZAT" felirat ottmaradt
    a bélyegképen), de minden külső felülírásra igaz volt.

    A `display_mode` (#1596) pontosan ugyanezért kell: a `Nézet ▸
    Megjelenítési mód` a KIRAJZOLT képpontokat írja át, tehát a mód
    ugyanúgy az URL része, mint a forgatás. Képpontot nem mozdító módra a
    cimke elmarad, vagyis az URL bájtra a mód bevezetése előtti — a rendes
    használat semmivel nem lassul, a módból kilépve pedig a Qt gyorstárában
    már ott lévő, festetlen kép jelenik meg azonnal. A cimkét a
    `thumbnail_provider` olvassa vissza; a két felet a
    `display_mode_paint` tartja együtt.
    """
    if display_mode is None:
        display_mode = current_display_mode()
    filters_tag = zlib.crc32((photo.filters or "").encode("utf-8"))
    return (
        f"image://thumbs/{photo.id}"
        f"?r={photo.rotate_steps}&f={filters_tag}"
        f"&m={photo.mtime_ns}&s={photo.size}"
        f"{display_mode_url_suffix(display_mode)}"
    )


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


#: A „Rejtett mappák" csomópont felirata (`IDS_HIDDEN`, bináris index).
REJTETT_MAPPAK_FEJLEC = "Rejtett mappák"


def _rejtett_csomopont(
    rejtettek: tuple[tuple[str, str, str, int, bool, bool], ...],
) -> tuple[tuple[str, str, str, int, bool, bool], ...]:
    """A rejtett mappák a saját fejlécük alatt, a lista végén (#1637/2).

    ÜRESEN nem ad fejlécet: aki nem rejtett el semmit, ne lásson egy
    örökké ott ülő, tartalmatlan csomópontot a hasáb alján.

    A fejléc `hidden` FAJTÁJÚ sor, útvonal nélkül — a delegate ugyanúgy
    nem engedi kijelölni, mint az évszám-elválasztót.
    """
    if not rejtettek:
        return ()
    fejlec = ("hidden", REJTETT_MAPPAK_FEJLEC, "", len(rejtettek), False, False)
    return (fejlec,) + rejtettek


def _with_year_separators(
    folders,
) -> tuple[tuple[str, str, str, int, bool, bool], ...]:
    """Évszám-elválasztók a mappa-dátum évéből (fallback: név-prefix).

    Audit (`docs/specs/ui-audit-mainwindow.md`, 1.1 pont): ha a listában
    MINDEN mappa dátumos ÉS ugyanabba az egyetlen évbe esik, a Picasa nem
    rajzol évszám-fejlécet — a mappák egyenesen a gyűjtemény-fejléc alá
    kerülnek (ez csak a homogén esetben áll fenn; ha akár egyetlen mappa is
    dátumtalan, vagy legalább két különböző év van jelen, az elválasztók a
    szokásos módon jelennek meg).
    """
    folders = list(folders)
    years = [
        _folder_year(name, date)
        for name, _path, _count, date, _offline, _unread in folders
    ]
    distinct_years = {year for year in years if year}
    if years and len(distinct_years) <= 1 and all(years):
        return tuple(
            ("folder", name, path, count, offline, unread)
            for name, path, count, _date, offline, unread in folders
        )

    rows = []
    last_year = None
    for (name, path, count, _date, offline, unread), year in zip(
        folders, years, strict=True
    ):
        if year and year != last_year:
            rows.append(("year", year, "", 0, False, False))
        last_year = year
        rows.append(("folder", name, path, count, offline, unread))
    return tuple(rows)


def _folder_year(name: str, date: str | None) -> str | None:
    """A mappa évszáma: a dátumból, vagy ennek híján a névből (`YYYY…`)."""
    if date:
        return date[:4]
    match = _YEAR_PREFIX.match(name)
    return match.group(1) if match else None


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
        # #1436: a mappa TARTALMÁNAK rendezése („Mappa rendezésének alapja ▸").
        # A beállítást a `FolderPhotoSortMixin` tolja ide; az `is_active`
        # predikátum mondja meg, szabad-e a JELEN nézetben átrendezni (csak a
        # mappa-feedben — ld. a szelet `_apply_folder_photo_sort` docstringjét).
        # Amíg senki nem állította be, a modell nem rendez át semmit.
        self._folder_photo_sort = DEFAULT_SORT_MODE
        self._folder_photo_sort_reverse = False
        self._folder_photo_sort_active = None
        # #1596: a `Nézet ▸ Megjelenítési mód` aktív tétele. A modell csak
        # az URL-cimkét adja hozzá (`display_mode_url_suffix`); a képpontokat
        # a `thumbnail_provider` írja át. Amíg senki nem állította be, a
        # bélyegkép-URL-ek bájtra a mód bevezetése előttiek.
        self._display_mode = ""

    def set_folder_photo_sort(
        self, sort_mode: str, reverse: bool, is_active=None
    ) -> None:
        """A mappán belüli képsorrend beállítása (#1436).

        A MÁR megjelenített képekre azonnal érvényesül, hogy a menüpont
        hatása ne csak a következő újratöltéskor látszódjon.
        """
        self._folder_photo_sort = sort_mode
        self._folder_photo_sort_reverse = bool(reverse)
        self._folder_photo_sort_active = is_active
        if self._photos:
            self.set_photos(self._photos)

    def set_display_mode(self, mode: str) -> None:
        """A megjelenítési mód átvezetése a rács bélyegkép-URL-jeire (#1596).

        A hívó a `wire_display_mode()`. A LÁTHATÓ cellákat azonnal
        frissíti: a `revision` lépése hajtja a feed `itemAt()`-mintáját
        (`LightboxFeed.qml`), a `dataChanged` pedig a modell-szerepekből
        kötő nézeteket (`TrayBar`, csoportos találati rács).

        Azonos értéknél NEM jelez — a rács újrakötése minden látható
        bélyegkép újrakérése, azt fölöslegesen kiváltani drága.
        """
        mode = str(mode or "")
        if mode == self._display_mode:
            return
        self._display_mode = mode
        self._revision += 1
        self.revisionChanged.emit()
        if self._photos:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._photos) - 1, 0),
                [self.ThumbUrlRole],
            )

    def _in_folder_photo_order(
        self, photos: tuple[PhotoRecord, ...]
    ) -> tuple[PhotoRecord, ...]:
        """Átrendezés mappa-blokkonként, ha a jelen nézet megengedi (#1436).

        A blokkhatárok nem mozdulnak, tehát a MAPPÁK sorrendje érintetlen —
        csak a mappán belüli képsorrend változik.

        Az ALAPÁLLAPOT (fájlnév, növekvő) pontosan az, amit az index
        lekérdezése már ad, ezért ott nem rendezünk újra: egy nagy
        könyvtárban ez minden frissítéskor felesleges munka lenne.
        """
        active = self._folder_photo_sort_active
        if active is None or not active():
            return photos
        if (
            self._folder_photo_sort == DEFAULT_SORT_MODE
            and not self._folder_photo_sort_reverse
        ):
            return photos
        return sort_folder_blocks(
            photos, self._folder_photo_sort, self._folder_photo_sort_reverse
        )

    @Property(int, notify=revisionChanged)
    def revision(self) -> int:
        """Minden set_photos-nál nő — QML-kötések frissítés-triggere.

        (A statusText-re kötés nem elég: pl. forgatásnál a szöveg nem
        változik, így a kötés nem értékelődne újra.)
        """
        return self._revision

    def set_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        photos = self._in_folder_photo_order(tuple(photos))
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

    def remove_by_path(self, path: str) -> bool:
        """Egy sor AZONNALI kivétele az útvonala alapján (#1227).

        A törölt kép sorának eltűnése eddig a célzott újraszinkronon múlt
        (`photoDeleted` → `resyncFolder` → háttérszál → `syncFinished`),
        tehát a sor csak a szinkron VÉGÉN tűnt el — nagy könyvtárnál
        másodpercek vagy percek múlva. Az eredetiben a rács maga végzi a
        törlést (`CThumbUI::DeleteProgress`, `0x00894fb4`).

        ⚠️ `beginRemoveRows`, NEM `set_photos`: a teljes reset eldobná a
        delegate-eket, és a rács visszaugrana a tetejére — épp azt a
        zavart okozná, amit ez a változás megszüntet.

        A hívó a resyncet ezután is elindíthatja: az utólag EGYEZTET, nem
        ez a metódus helyettesíti.

        Returns:
            `True`, ha volt ilyen sor. `False` ismeretlen útra — a
            törlés-jelzés olyan képre is jöhet, ami nincs a jelen
            nézetben (másik mappa, szűrt nézet), és az nem hiba.
        """
        cel = str(Path(path))
        for sor, rekord in enumerate(self._photos):
            if str(Path(rekord.folder_path) / rekord.name) != cel:
                continue
            self.beginRemoveRows(QModelIndex(), sor, sor)
            self._photos = self._photos[:sor] + self._photos[sor + 1:]
            self.endRemoveRows()
            self._revision += 1
            self.revisionChanged.emit()
            return True
        return False

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
        return _thumb_url(photo, self._display_mode)

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
            "thumbUrl": _thumb_url(photo, self._display_mode),
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
            # #463: piros geo-pin jelvény — a `PhotoRecord.location` az
            # ini `geotag=` és az EXIF GPS-t is feloldja (ld. metadata/gps.py),
            # itt csak a meglétét kérdezzük.
            "hasGeo": photo.location is not None,
            # #463: arc-jelvények — „van rajta felismert arc", illetve
            # „van jóváhagyásra váró névjavaslat". A kettő KÜLÖN jelvény
            # volt az eredetiben is: az utóbbi azt jelzi, hogy elintézetlen
            # dolgod van a képpel.
            "hasFaces": photo.face_count > 0,
            "hasFaceSuggestion": photo.unnamed_face_count > 0,
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

    @Slot(int, result=int)
    def rowOfId(self, photo_id: int) -> int:
        """A fotó sor-indexe id alapján (#135): a QML ezzel képezi újra a
        kijelölést háttér-frissítés (reset) után — -1, ha a fotó már nincs
        a jelen nézetben (törölve/kiszűrve)."""
        return self.row_of_id(photo_id)

    @Slot(str, result=int)
    def rowOfPath(self, path: str) -> int:
        """A kép sor-indexe ABSZOLÚT ÚTVONAL alapján; -1, ha nincs a nézetben.

        #1001: a kollázs a kép ÚTVONALÁT ismeri (a `.cxf` is azt tárolja), a
        néző és a szerkesztő viszont sorindexet vár — ez a kettő közti
        fordító. A `Main.qml` `collageSourceRows()`-a ezt a nevet már hívta
        a képtálcára (#985), csak a modellben nem volt meg: a tálcás ág néma
        QML-hibába futott.

        Az összehasonlítás NORMALIZÁLT útvonalon megy: a kollázs `Path`-ból
        építi a sztringet (Windowson fordított perjellel), a modell viszont
        `/`-t használ — a nyers egyenlőség a windows-lábon némán bukna."""
        if not path:
            return -1
        cel = os.path.normcase(os.path.normpath(str(path)))
        for i, photo in enumerate(self._photos):
            jelolt = os.path.normcase(
                os.path.normpath(os.path.join(photo.folder_path, photo.name))
            )
            if jelolt == cel:
                return i
        return -1

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

    @Slot(int, result="QVariantList")
    def folderRowRange(self, row: int) -> list:
        """A `row` sort tartalmazó MAPPA folytonos sortartománya: `[kezdet,
        darab]` (#1905).

        A szerkesztő felső filmszalagja eddig a TELJES rács-modellt
        listázta. A rács viszont FEED: több mappa fotóit sorolja fel
        egymás után (`build_feed_groups`), a csillag-szűrő és a keresés
        pedig végképp vegyít. A tulajdonos ezért egy ötképes mappa
        szerkesztésekor NYOLC elemet látott a szalagon — köztük egy másik
        mappa kollázs-képeit.

        Az eredeti Picasa a szalagon **pontosan a mappa képeit** mutatja
        (`research/Picasa3-vs-PicasaPy-fejlec-elteresek/`, egymás mellé
        tett felvétel ugyanazon a mappán).

        Ugyanazon a szerződésen áll, mint a `folderNeighbor` (#84): a
        lekérdezések mappa szerint rendezettek (`f.path, p.name`), tehát
        egy mappa fotói FOLYTONOS tartományt alkotnak. Érvénytelen sorra
        `[0, 0]`.
        """
        if not 0 <= row < len(self._photos):
            return [0, 0]
        folder = self._photos[row].folder_path
        kezdet = row
        while kezdet > 0 and self._photos[kezdet - 1].folder_path == folder:
            kezdet -= 1
        veg = row
        while (
            veg + 1 < len(self._photos)
            and self._photos[veg + 1].folder_path == folder
        ):
            veg += 1
        return [kezdet, veg - kezdet + 1]

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

    @Slot(int, result="QVariantList")
    def groupRange(self, row: int) -> list:
        """A sorhoz tartozó mappa-csoport [első, utolsó] sorindexe (#1219).

        A QML kijelölés-szorításához: a Shift+kattintás tartományát a
        KEZDŐPONT (horgony) mappacsoportjára kell szorítani, mert az
        eredetiben a tartomány-mag (`0x00716ae0`) mindig egyetlen album
        kijelölés-csomópontján fut. Érvénytelen sorra üres listát ad.
        """
        if not 0 <= row < len(self._photos):
            return []
        for start, count in self._group_bounds():
            if start <= row < start + count:
                return [start, start + count - 1]
        return []

    @Slot(int, str, int, result=int)
    def navigate(self, row: int, direction: str, columns: int) -> int:
        """Kurzor-léptetés célsora a rács-feedben (#77).

        ⚠️ #1219: MIND A NÉGY irány a MAPPA-CSOPORTON BELÜL marad.

        Az eredetiben ez nem ellenőrzés, hanem SZERKEZET: a feed konténere
        (`0x0076a390`, `CMultiAlbumNode` vtábla 33. rés) mindig pontosan
        EGY albumsor kijelölés-csomópontját éri el — nincs ciklus a
        `[+0x300]` sortömbön, tehát a léptetés fizikailag sem tud átlépni.

        A mappa végén MEGÁLL (mérve): `0x00718031` `cmp/jbe` ELŐJEL
        NÉLKÜLI, tehát a −1-re csökkenő index is ugyanide fut — mindkét
        vég ugyanaz az ág; a határ-ág (`0x00717d10`) a végén
        `0x00717e76`-nál `[this+0x2e0] = 0xFFFFFFFF`, azaz törli a jelölőt
        és NEM jelöl ki újat. Nem lép át, és nem fordul át.

        Korábban a balra/jobbra folytonos volt, a fel/le pedig a csoport
        szélén SZÁNDÉKOSAN a szomszéd csoportra ugrott.

        Érvénytelen sorról (pl. −1, nincs kijelölés) az első képre lép;
        üres modellnél −1.
        """
        count = len(self._photos)
        if count == 0:
            return -1
        if not 0 <= row < count:
            return 0
        bounds = self._group_bounds()
        group = next(i for i, (s, n) in enumerate(bounds) if s <= row < s + n)
        start, group_count = bounds[group]
        # a csoport utolsó sorának indexe — minden irány eddig mehet
        last = start + group_count - 1
        if direction == "left":
            return max(start, row - 1)
        if direction == "right":
            return min(last, row + 1)
        if direction not in ("up", "down"):
            return row
        cols = max(1, columns)
        local = row - start
        grid_row, col = divmod(local, cols)
        if direction == "down":
            if grid_row < (group_count - 1) // cols:
                return start + min(local + cols, group_count - 1)
            # #1219: a csoport alján MEGÁLL — nem lép a szomszéd csoportra
            return row
        if grid_row > 0:
            return start + local - cols
        # #1219: a csoport tetején MEGÁLL
        return row

    def rowCount(self, parent=_ROOT_INDEX) -> int:
        return 0 if parent.isValid() else len(self._photos)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._photos):
            return None
        photo = self._photos[index.row()]
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return photo.name
        if role == self.ThumbUrlRole:
            # cache-buster: forgatás/szerkesztés után új URL → friss kép (#59)
            return _thumb_url(photo, self._display_mode)
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
