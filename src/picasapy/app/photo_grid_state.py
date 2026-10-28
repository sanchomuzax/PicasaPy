"""A képrács modell állapotkezelése és frissítése."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QModelIndex, Slot

from picasapy.index import PhotoRecord
from picasapy.ini.movie_trim import trim_from_filters

from .display_mode_paint import current_display_mode_suffix, display_mode_url_suffix
from .model_helpers import _felbontas, _has_edits, _thumb_url
from .photo_sort import DEFAULT_SORT_MODE, sort_folder_blocks


class PhotoGridState:
    def initialize(self) -> None:
        self._photos: tuple[PhotoRecord, ...] = ()
        self._revision = 0
        # #5762: a gyorsnézegető egy külön kijelölt fájlsort mutat, amely
        # több könyvtárból is állhat. A szokásos könyvtárnézet mappahatára
        # marad; csak a közvetlen fájl-listás indítás lép át rajta.
        self._linear_navigation = False
        # #1436: a mappa TARTALMÁNAK rendezése („Mappa rendezésének alapja ▸").
        # A beállítást a `FolderPhotoSortMixin` tolja ide; az `is_active`
        # predikátum mondja meg, szabad-e a JELEN nézetben átrendezni (csak a
        # mappa-feedben — ld. a szelet `_apply_folder_photo_sort` docstringjét).
        # Amíg senki nem állította be, a modell nem rendez át semmit.
        self._folder_photo_sort = DEFAULT_SORT_MODE
        self._folder_photo_sort_reverse = False
        self._folder_photo_sort_active = None
        #: #467: a szín-rendezés adatforrása (a vezérlő adja) — enélkül a
        #: szempont a fájlnév-sorrendre esik vissza, nem ürül ki a rács
        self._folder_photo_hues = None
        #: #1721: a kézi sorrend adatforrása (a mappák `.picasa.ini`-je)
        self._folder_photo_prioritasok = None
        # #1596: a `Nézet ▸ Megjelenítési mód` aktív tétele. A modell csak
        # az URL-cimkét adja hozzá (`display_mode_url_suffix`); a képpontokat
        # a `thumbnail_provider` írja át. Amíg senki nem állította be, a
        # bélyegkép-URL-ek bájtra a mód bevezetése előttiek.
        self._display_mode = ""
        #: #598: a rács bélyegkép-SZINTJE. `None` = a felső szint, azaz a
        #: mai viselkedés; a QML a csúszka fokozatából állítja be.
        self._thumb_level: int | None = None
        #: #2187: az arc-nagyítás keretei fotó-azonosító szerint. `None` = a
        #: teljes kép (a mai viselkedés); a személy-album vezérlője tölti.
        self._arc_teglalapok: dict[int, tuple] | None = None

    def set_face_zoom(self, teglalapok: dict[int, tuple] | None) -> None:
        """Az arc-nagyítás (`face_zoom`) átvezetése a bélyegkép-URL-ekre
        (#2187) — `{fotó-azonosító: (bal, fent, jobb, lent)}`, vagy `None` a
        teljes képhez.

        A `set_display_mode` mintáját követi: az URL-t írja át, tehát a
        látható cellák újrakérik a képet. Keret nélküli sor (pl. egy
        hiányos indexű kép) a teljes képet mutatja."""
        uj = dict(teglalapok) if teglalapok is not None else None
        if uj == self._arc_teglalapok:
            return
        self._arc_teglalapok = uj
        self._revision += 1
        self.revisionChanged.emit()
        if self._photos:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._photos) - 1, 0),
                [self.ThumbUrlRole],
            )

    def _sor_url(self, photo: PhotoRecord) -> str:
        """Egy sor bélyegkép-URL-je a modell mostani állapotával."""
        arc = (
            self._arc_teglalapok.get(photo.id)
            if self._arc_teglalapok is not None
            else None
        )
        return _thumb_url(photo, self._display_mode, self._thumb_level, arc)

    def set_thumb_level(self, level: int | None) -> None:
        """A rács bélyegkép-szintje (#598) — a cellaméretből.

        A `set_display_mode` mintáját követi, mert ugyanaz a természete: az
        URL-t írja át, tehát minden látható cellát újrakér. Ezért **csak
        SZINTVÁLTÁSKOR** jelez: a csúszka fokozatai között egy szint több
        fokozatot fed le (72 · 144 · a maximum), így a csúszka húzása nem
        kér újra mindent, csak a szinthatár átlépése."""
        uj = None if level is None else int(level)
        if uj == self._thumb_level:
            return
        self._thumb_level = uj
        self._revision += 1
        self.revisionChanged.emit()
        if self._photos:
            self.dataChanged.emit(
                self.index(0, 0),
                self.index(len(self._photos) - 1, 0),
                [self.ThumbUrlRole],
            )

    def set_folder_photo_sort(
        self,
        sort_mode: str,
        reverse: bool,
        is_active=None,
        hues=None,
        prioritasok=None,
    ) -> None:
        """A mappán belüli képsorrend beállítása (#1436).

        A MÁR megjelenített képekre azonnal érvényesül, hogy a menüpont
        hatása ne csak a következő újratöltéskor látszódjon.

        `hues` (#467): a szín-rendezés adatforrása — `rekordok → {fájl-
        azonosság: színezet}` visszahívás. **Csak `color` szempontnál hívjuk
        meg**: az index olvasása minden más rendezésnél fölösleges munka
        lenne, egy nagy könyvtárban pedig minden frissítéskor.

        `prioritasok` (#1721): a KÉZI sorrend adatforrása — `rekordok →
        {(mappa, fájlnév): priority}` visszahívás, a mappák
        `.picasa.ini`-jéből. Ugyanaz a szerződés: **csak `priority`
        szempontnál** hívjuk, mert minden más rendezésnél fölösleges
        fájlolvasás lenne.
        """
        self._folder_photo_sort = sort_mode
        self._folder_photo_sort_reverse = bool(reverse)
        self._folder_photo_sort_active = is_active
        if hues is not None:
            self._folder_photo_hues = hues
        if prioritasok is not None:
            self._folder_photo_prioritasok = prioritasok
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
        hues = None
        if self._folder_photo_sort == "color" and self._folder_photo_hues is not None:
            hues = self._folder_photo_hues(photos)
        prioritasok = None
        forras = getattr(self, "_folder_photo_prioritasok", None)
        if self._folder_photo_sort == "priority" and forras is not None:
            prioritasok = forras(photos)
        return sort_folder_blocks(
            photos,
            self._folder_photo_sort,
            self._folder_photo_sort_reverse,
            hues,
            prioritasok,
        )

    def set_photos(self, photos: tuple[PhotoRecord, ...]) -> None:
        photos = self._in_folder_photo_order(tuple(photos))
        # #142: változatlan tartalomnál no-op — a reset eldobná a
        # delegate-eket és a revision-bump minden élő cellát újraköttetne,
        # így minden háttér-szinkron a teljes rácsot újrarajzolná
        # (a FolderListModel._set_rows mintája).
        #: #2187: minden betöltés új nézet — az arc-nagyítás nem öröklődhet
        #: egy mappára; a személy-album vezérlője a betöltés UTÁN újra
        #: beállítja, ha kell. Azonos sorok mellett is törölni kell (pl.
        #: ugyanazok a képek egy keresésben): ott a `set_face_zoom` jelez,
        #: vágás nélkül pedig no-op, tehát a #142 nyeresége megmarad.
        if photos == self._photos:
            self.set_face_zoom(None)
            return
        self._arc_teglalapok = None
        self.beginResetModel()
        self._photos = photos
        self.endResetModel()
        self._revision += 1
        self.revisionChanged.emit()

    def set_linear_navigation(self, enabled: bool) -> None:
        """A fájlargumentumokkal megnyitott néző teljes sorának léptetése."""
        enabled = bool(enabled)
        if enabled == self._linear_navigation:
            return
        self._linear_navigation = enabled
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

