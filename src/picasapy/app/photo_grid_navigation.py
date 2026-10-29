"""A képrács csoporthatárai, navigációja és Qt-listamodell szerepei."""

from __future__ import annotations

from PySide6.QtCore import Qt, QUrl

from .model_helpers import _ROOT_INDEX, _felbontas


class PhotoGridNavigation:
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
        if self._linear_navigation:
            return max(0, min(len(self._photos) - 1, row + delta))
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
        if self._linear_navigation:
            return [0, len(self._photos)]
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
            return self._sor_url(photo)
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
            return _felbontas(photo)
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

