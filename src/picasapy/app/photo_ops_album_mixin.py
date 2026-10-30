"""Az albumok, címkék és mappasorrend képműveleti témamixinje."""

from __future__ import annotations

import secrets
from pathlib import Path

from PySide6.QtCore import QCoreApplication, Qt, Signal, Slot
from PySide6.QtGui import QGuiApplication

from picasapy.app.kezi_sorrend import mappa_prioritasai, mentsd_a_prioritasokat
from picasapy.index import (
    album_photos,
    open_index,
    photos_in_folder,
    photos_with_keyword,
)
from picasapy.index.albums import (
    _pending_empty_album,
    _remove_empty_album,
    _store_empty_album,
)
from picasapy.index.album_sort import SORT_MODES, new_places, sorted_album
from picasapy.ini import (
    STAR_ALBUM_TOKEN,
    load_existing,
)
from picasapy.ini.albums import (
    albums_of,
    ensure_album,
    with_album,
    with_album_fields,
    without_album,
    without_album_everywhere,
)
from picasapy.ini.album_order import AlbumOrderWriteError, write_album_places
from picasapy.ini.document import ALBUM_SECTION_PREFIX
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .photo_ops_compat import _WRITE_ERRORS, update_document


class PhotoOpsAlbumMixin:
    albumWriteFailed = Signal(str)

    # -- virtuális albumok (#9, 2. lépés) ------------------------------------

    @Slot(list, str)
    def addRowsToAlbum(self, rows, token: str) -> None:
        """A kijelölés felvétele egy MEGLÉVŐ albumba: az `albums=` CSV
        bővítése minden érintett fotónál, mappánként egyetlen útvonalanként
        szerializált, best-effort konkurenciakezelésű ini-írással
        (`_apply_batch`, a `setGeotagRows` mintája)."""
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        with open_index(self._db_path) as conn:
            pending = _pending_empty_album(conn, token)

        if pending is None:
            def mutate(document, photo):
                return with_album(document, photo.name, token)
        else:
            def mutate(document, photo):
                document = ensure_album(document, token, pending.name)
                document = with_album_fields(
                    document,
                    token,
                    name=pending.name,
                    date=pending.date,
                    location=pending.location,
                    description=pending.description,
                    use_music=pending.use_music,
                    music_file=pending.music_file,
                )
                return with_album(document, photo.name, token)

        if self._write_album_batch(valid, mutate) and pending is not None:
            with open_index(self._db_path) as conn:
                _remove_empty_album(conn, token)
                self._load_albums(conn)

    @Slot(list, str)
    def removeRowsFromAlbum(self, rows, token: str) -> None:
        """A kijelölés kivétele egy albumból (a definíció, `[.album:token]`,
        a mappában marad — csak a tagság törlődik, ahogy a Picasa is teszi).

        A `]star` különleges albumnál a tagság az INI `star` kulcsa, ezért
        annak levétele nem az `albums=` CSV-t módosítja (#4883).
        """
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        if token == STAR_ALBUM_TOKEN:
            def mutate(document, photo):
                return document.with_removed(photo.name, "star")
        else:
            def mutate(document, photo):
                return without_album(document, photo.name, token)

        self._write_album_batch(valid, mutate)

    @Slot(str, result=bool)
    def deleteAlbum(self, token: str) -> bool:  # noqa: N802
        """Egy album teljes törlése minden érintett mappa ini-jéből (#4598).

        A törlés a `[.album:<token>]` definíciót és a képek `albums=`
        hivatkozásait is kiveszi. A képfájlok és a többi album érintetlenek
        maradnak. Visszatérés: legalább egy albumot ismerő mappába írtunk-e.
        """
        token = (token or "").strip()
        if not token:
            return False
        erintett = list(self._album_dokumentumok(token))
        if not erintett:
            return False

        try:
            with open_index(self._db_path) as conn:
                for ini_ut, _document in erintett:
                    update_document(
                        ini_ut,
                        lambda document: without_album_everywhere(document, token),
                        backup=True,
                    )
                    self._sync_tree(conn, str(ini_ut.parent))
                self._load_albums(conn)
        except _WRITE_ERRORS as error:
            self.albumWriteFailed.emit(str(error))
            return False

        self._refresh_view()
        return True

    @Slot(str, str, result=bool)
    def sortAlbum(self, token: str, mode: str) -> bool:  # noqa: N802
        """Az album „Sort Album By" almenüje (#4599, ADR-016): az album képeinek
        TÁROLT sorrendjét egyszer átrendezi — `date` / `name` / `size` kulcs
        szerint, vagy `reverse`: megfordítja. A Shift (a kiválasztás
        pillanatában lenyomva) a három kulcsnál csökkenővé teszi, ahogy az
        eredeti kezelő (`GetKeyState(VK_SHIFT)`, `0x005cc09d`); a `reverse`
        Shifttel is megfordít."""
        shift = bool(
            QGuiApplication.keyboardModifiers() & Qt.KeyboardModifier.ShiftModifier
        )
        return self.sortAlbumBy(token, mode, descending=shift)

    def sortAlbumBy(  # noqa: N802
        self, token: str, mode: str, *, descending: bool = False
    ) -> bool:
        """A `sortAlbum` magja, a Shift állapotától függetlenül (#4599).

        A mód nem tárolódik: minden tag új helyet kap (`1.0 … n`) az
        `albumorder=` kulcsban, mappánként EGY ini-írással. Több mappára szóró
        albumnál a tagok mappákon át összefésülve rendeződnek. Bukott írásnál
        a hiba megnevezi a mappát (`albumWriteFailed`), és a művelet
        megismételhető. Visszatérés: kiírtuk-e az egész új sorrendet.
        """
        token = (token or "").strip()
        if not token or mode not in SORT_MODES:
            return False
        with open_index(self._db_path) as conn:
            tarolt = album_photos(conn, token)
        if not tarolt:
            return False
        rendezett = sorted_album(tarolt, mode, descending=bool(descending))
        helyek = new_places(rendezett)
        mappankent: dict[str, dict[str, float]] = {}
        for (mappa, nev), hely in helyek.items():
            mappankent.setdefault(mappa, {})[nev] = hely

        try:
            with open_index(self._db_path) as conn:
                write_album_places(
                    token,
                    (
                        (Path(mappa) / PICASA_INI_NAME, places)
                        for mappa, places in mappankent.items()
                    ),
                    on_written=lambda ini_ut: self._sync_tree(
                        conn, str(ini_ut.parent)
                    ),
                )
        except (AlbumOrderWriteError, *_WRITE_ERRORS) as error:
            self.albumWriteFailed.emit(str(error))
            self._refresh_view()
            return False
        self._refresh_view()
        return True

    @Slot("QVariantList", int, result=bool)
    def reorderAlbumPhotos(self, rows, target_row: int) -> bool:  # noqa: N802
        """Húzással átrendezi az aktív album képeit (#5008).

        A `rows` a rácsmodell aktuális sorai, a cél elé kerülnek. Az album
        teljes tárolt sorrendjéből indulunk ki, és mappánként az `ini` API
        albumorder-íróján keresztül mentünk; az `albums=` tagság nem változik.
        """
        token = str(self.currentAlbumToken or "").strip()
        if not token:
            return False
        with open_index(self._db_path) as conn:
            ordered = list(album_photos(conn, token))
        grid_rows = list(getattr(self._photos, "_photos", ()) or ())
        selected_indexes = sorted(
            {int(row) for row in rows if 0 <= int(row) < len(grid_rows)}
        )
        if not ordered or not selected_indexes:
            return False

        def key(photo):
            return (photo.folder_path, photo.name)

        selected_keys = {key(grid_rows[index]) for index in selected_indexes}
        album_keys = {key(photo) for photo in ordered}
        selected_keys.intersection_update(album_keys)
        if not selected_keys:
            return False

        moved = [photo for photo in ordered if key(photo) in selected_keys]
        remaining = [photo for photo in ordered if key(photo) not in selected_keys]
        destination = (
            grid_rows[int(target_row)]
            if 0 <= int(target_row) < len(grid_rows)
            else None
        )
        destination_key = key(destination) if destination is not None else None
        if destination_key in selected_keys:
            return True
        insertion = (
            next(
                (index for index, photo in enumerate(remaining)
                 if key(photo) == destination_key),
                len(remaining),
            )
            if destination_key is not None
            else len(remaining)
        )
        reordered = [*remaining[:insertion], *moved, *remaining[insertion:]]
        placements = new_places(reordered)
        by_folder: dict[str, dict[str, float]] = {}
        for (folder, name), place in placements.items():
            by_folder.setdefault(folder, {})[name] = place

        try:
            with open_index(self._db_path) as conn:
                write_album_places(
                    token,
                    (
                        (Path(folder) / PICASA_INI_NAME, places)
                        for folder, places in by_folder.items()
                    ),
                    on_written=lambda ini_path: self._sync_tree(
                        conn, str(ini_path.parent)
                    ),
                )
        except (AlbumOrderWriteError, *_WRITE_ERRORS) as error:
            self.albumWriteFailed.emit(str(error))
            self._refresh_view()
            return False
        self._refresh_view()
        return True

    @Slot(str, str, result=bool)
    def sortFolderBy(self, folder: str, mode: str) -> bool:  # noqa: N802
        """Egyszer átrendezi a célmappa listáját, és elmenti a kézi sorrendet.

        A rendezési mód nem tárolódik. A névrendezés az album-rendezés
        természetes összevetését használja; a fordított művelet a már
        eltárolt kézi sorrendet fordítja meg.
        """
        folder = str(folder or "")
        supported = (*SORT_MODES, "color", "priority")
        if not folder or not folder.strip() or mode not in supported:
            return False
        with open_index(self._db_path) as conn:
            photos = photos_in_folder(conn, folder)
        if not photos:
            return False

        from .photo_sort import sort_folder_blocks, szin_adat_hiany

        prioritasok = mappa_prioritasai(folder)
        if mode in SORT_MODES:
            if mode == "reverse":
                stored_order = sort_folder_blocks(
                    photos,
                    "priority",
                    prioritasok={
                        (folder, name): value
                        for name, value in prioritasok.items()
                    },
                )
                ordered = sorted_album(stored_order, mode)
            else:
                ordered = sorted_album(photos, mode)
        elif mode == "color":
            hues = self._folder_photo_hues(photos)
            if szin_adat_hiany(photos, hues):
                # A színindex még nem kész: a fájlnév-sorrend ilyenkor
                # véglegesen kiíródna, ezért nem rendezünk és nem írunk.
                return False
            ordered = sort_folder_blocks(photos, mode, hues=hues)
        else:
            ordered = sort_folder_blocks(
                photos,
                "priority",
                prioritasok={
                    (folder, name): value for name, value in prioritasok.items()
                },
            )

        places = {
            photo.name: float(position)
            for position, photo in enumerate(ordered, start=1)
        }
        try:
            mentsd_a_prioritasokat(folder, places)
        except _WRITE_ERRORS as error:
            self.albumWriteFailed.emit(
                f"A mappa sorrendje nem menthető ({folder}): {error}"
            )
            return False
        self._refresh_view()
        return True

    # -- Album-tulajdonságok (#3173) -------------------------------------------

    @Slot(str, result="QVariantMap")
    def albumProperties(self, token: str):  # noqa: N802
        """Az album MAI tulajdonságai a párbeszéd előtöltéséhez (#3173).

        Üres szótár, ha a token nem szerepel egyetlen mappa ini-jében sem —
        a hívó ebből tudja, hogy nincs mit szerkeszteni.
        """
        token = (token or "").strip()
        if not token:
            return {}
        for _ut, dokumentum in self._album_dokumentumok(token):
            for album in albums_of(dokumentum):
                if album.token != token:
                    continue
                return {
                    "name": album.name or "",
                    "date": album.date or "",
                    "location": album.location or "",
                    "description": album.description or "",
                    "use_music": album.use_music,
                    "music_file": album.music_file or "",
                }
        return {}

    def albumMusicFile(self, token: str) -> str:  # noqa: N802
        """Az engedélyezett albumzene meglévő, helyi fájlútvonala."""
        token = (token or "").strip()
        if not token:
            return ""
        for ini_path, document in self._album_dokumentumok(token):
            for album in albums_of(document):
                if album.token != token:
                    continue
                if not album.use_music or not album.music_file:
                    return ""
                local_path = formatting.to_local_path(album.music_file)
                if not local_path:
                    return ""
                music_path = Path(local_path).expanduser()
                if not music_path.is_absolute():
                    music_path = ini_path.parent / music_path
                try:
                    return str(music_path.resolve()) if music_path.is_file() else ""
                except OSError:
                    return ""
        return ""

    def albumMusicTrackUrls(self, token: str) -> list:  # noqa: N802
        """Az album egyetlen kiválasztott zeneszáma file-URL-ként."""
        music_path = self.albumMusicFile(token)
        return [formatting.to_file_url(music_path)] if music_path else []

    @Slot(str, str, str, str, str, result=bool)
    def editAlbumProperties(  # noqa: N802
        self,
        token: str,
        name: str,
        date: str,
        location: str,
        description: str,
    ) -> bool:
        """Az album tulajdonságainak mentése MINDEN érintett mappa ini-jébe.

        A definíció (`[.album:<token>]`) minden olyan mappában ott van, ahol az
        albumnak van tagja — a `createAlbum` így írja ki, ahogy a Picasa is.
        Az átnevezésnek tehát mindegyiket át kell írnia, különben a bal hasáb
        mappánként MÁS nevet látna.

        ⛔ Album nélküli mappához **hozzá sem nyúlunk**: a `with_album_fields`
        nem létező szekcióra nem csinál semmit, és a száraz futás miatt ilyen
        mappában írás sem indul (nem keletkezik szellem-album).

        Visszatérés: írtunk-e legalább egy mappába.
        """
        token = (token or "").strip()
        if not token:
            return False

        def mutate(dokumentum):
            return with_album_fields(
                dokumentum,
                token,
                name=name,
                date=date,
                location=location,
                description=description,
            )

        irt = False
        try:
            with open_index(self._db_path) as conn:
                for ut, dokumentum in self._album_dokumentumok(token):
                    if mutate(dokumentum) is dokumentum:
                        continue  # nincs mit írni ebbe a mappába
                    update_document(ut, mutate, backup=True)
                    self._sync_tree(conn, str(ut.parent))
                    irt = True
                if irt:
                    self._load_albums(conn)
        except _WRITE_ERRORS as hiba:
            self.albumWriteFailed.emit(str(hiba))
            return False
        if irt:
            self._refresh_view()
        return irt

    @Slot(str, bool, str, result=bool)
    def editAlbumMusic(  # noqa: N802
        self, token: str, use_music: bool, music_file: str
    ) -> bool:
        """A zene két mezőjének mentése az albumot ismerő mappák ini-jébe."""
        token = (token or "").strip()
        if not token:
            return False

        def mutate(dokumentum):
            return with_album_fields(
                dokumentum,
                token,
                use_music=use_music,
                music_file=music_file,
            )

        irt = False
        try:
            with open_index(self._db_path) as conn:
                for ut, dokumentum in self._album_dokumentumok(token):
                    if mutate(dokumentum) is dokumentum:
                        continue
                    update_document(ut, mutate, backup=True)
                    self._sync_tree(conn, str(ut.parent))
                    irt = True
                if irt:
                    self._load_albums(conn)
        except _WRITE_ERRORS as hiba:
            self.albumWriteFailed.emit(str(hiba))
            return False
        if irt:
            self._refresh_view()
        return irt

    def _album_dokumentumok(self, token: str):
        """(ini-útvonal, dokumentum) párok azokra a mappákra, amelyek ini-je
        ismeri ezt az albumot — a `[.album:<token>]` szekció jelenléte szerint.

        Az index `has_ini` jelzőjéből indul (ugyanaz a forrás, mint a
        `queries._album_suggestions`-nél), és az olvashatatlan ini-t kihagyja.
        """
        szakasz = f"{ALBUM_SECTION_PREFIX}{token}"
        with open_index(self._db_path) as conn:
            mappak = [
                row["path"]
                for row in conn.execute(
                    "SELECT path FROM folders WHERE has_ini = 1"
                )
            ]
        for mappa in mappak:
            ut = Path(mappa) / PICASA_INI_NAME
            try:
                dokumentum = load_existing(ut)
            except (OSError, ValueError):
                continue
            if dokumentum.section(szakasz) is not None:
                yield ut, dokumentum

    @Slot(str, list, result=str)
    def createAlbum(self, name: str, rows) -> str:
        """Új virtuális album a kijelölt képekkel: véletlen (32 hex karakteres)
        token, a `[.album:<token>]` definíció MINDEN érintett mappa ini-jébe
        kiírva — a Picasa is minden mappába kiírja, ahol az albumnak van
        tagja —, a tagság pedig `with_album`-mal minden kijelölt fotónál.
        Visszaadja az új tokent (üres kijelölésnél/hibánál üres stringet)."""
        return self._albumot_keszit(name, self._rows_to_photos(rows))

    @Slot(str, list, str, str, str, bool, str, result=str)
    def createAlbumWithProperties(
        self,
        name: str,
        rows,
        date: str,
        location: str,
        description: str,
        use_music: bool,
        music_file: str,
    ) -> str:
        """Album Properties párbeszédből, a kijelölt képek tagságával (#5846).

        A tulajdonságok és a tagság együtt, az érintett fotók mappáinak
        `.picasa.ini` fájljaiba kerülnek, ugyanazon a kötegelt íróúton, mint
        a meglévő „Create Album from Selection” művelet.
        """
        photos = self._rows_to_photos(rows)
        if not photos:
            return ""
        token = secrets.token_hex(16)
        clean_name = (name or "").strip() or None

        def mutate(document, photo):
            document = ensure_album(document, token, clean_name)
            document = with_album_fields(
                document,
                token,
                name=clean_name,
                date=date,
                location=location,
                description=description,
                use_music=use_music,
                music_file=music_file,
            )
            return with_album(document, photo.name, token)

        if not self._write_album_batch(photos, mutate):
            return ""
        return token

    @Slot(str, str, str, str, str, bool, str, result=str)
    def createEmptyAlbum(
        self,
        name: str,
        folder_path: str,
        date: str,
        location: str,
        description: str,
        use_music: bool,
        music_file: str,
    ) -> str:
        """Üres albumot ment az index tartós helyi tárába (#6278).

        Az album tulajdonságai a profil-indexben maradnak, a mappa ini-je
        változatlan. Az első kép tagságának írásakor kerül a definíció és a
        tagság együtt az érintett mappa ini-jébe.
        """
        folder_path = (folder_path or "").strip()
        folder_error = QCoreApplication.translate(
            "PhotoOpsMixin",
            "An album must be saved in an indexed photo folder.",
        )
        if not folder_path:
            self.albumWriteFailed.emit(folder_error)
            return ""
        folder = Path(folder_path)
        if not folder.is_dir():
            self.albumWriteFailed.emit(folder_error)
            return ""

        token = secrets.token_hex(16)
        clean_name = (name or "").strip() or None

        try:
            with open_index(self._db_path) as conn:
                indexed = conn.execute(
                    "SELECT 1 FROM folders WHERE path = ?", (str(folder),)
                ).fetchone()
                if indexed is None:
                    self.albumWriteFailed.emit(folder_error)
                    return ""
                _store_empty_album(
                    conn,
                    token=token,
                    folder_path=str(folder),
                    name=clean_name,
                    date=date,
                    location=location,
                    description=description,
                    use_music=use_music,
                    music_file=music_file,
                )
                self._load_albums(conn)
        except _WRITE_ERRORS as error:
            self.albumWriteFailed.emit(str(error))
            return ""
        return token

    def _albumot_keszit(self, name: str, photos) -> str:
        """Album készítése MEGADOTT fotókból (a `createAlbum` magja, #1406).

        A `createAlbum` a KIJELÖLÉS soraiból hívja, a „Címke megjelenítése
        albumként" pedig a címke szerint lekérdezett fotókkal — a kettő
        ugyanezt az egyetlen írási utat használja, tehát az ini-írás, a
        hibakezelés és az albumlista-frissítés is közös."""
        if not photos:
            return ""
        token = secrets.token_hex(16)
        clean_name = (name or "").strip() or None

        def mutate(document, photo):
            document = ensure_album(document, token, clean_name)
            return with_album(document, photo.name, token)

        if not self._write_album_batch(photos, mutate):
            return ""
        return token

    # -- Beállítás asztali háttérképként (#1775) --------------------------------

    @Slot(int, result=bool)
    def setPhotoAsDesktopBackground(self, row: int) -> bool:  # noqa: N802
        """A kijelölt kép asztali háttérképnek (`eMenuCreate::ID_WALLPAPER`).

        Az eredeti (mérve, `0x0057aa10`, 1143 b) **másolatot** ír:
        `picasabackground.bmp` a `Picasa/Backgrounds` mappába — NEM az eredeti
        fájlra mutat —, majd középre teszi (`WallpaperStyle=0`,
        `TileWallpaper=0`). A másolat azért fontos, mert így a kép átnevezése
        vagy törlése nem viszi el az asztal hátterét.

        A motor közös a kollázs-ágéval (`app/wallpaper.py`, #1005): ugyanaz a
        BMP-írás, ugyanaz a beállító lánc, és ugyanaz a két visszajelzés
        (`desktopBackgroundApplied` / `desktopBackgroundFailed`) — egy hely,
        egy viselkedés.

        Visszatérés: elindult-e a művelet. Érvénytelen sorra `False`, és a
        hívó ebből tud üzenetet adni."""
        from . import collage_output as output
        from . import collage_prefs, wallpaper

        fotok = self._photos.photos
        if not 0 <= int(row) < len(fotok):
            return False
        foto = fotok[int(row)]
        forras = Path(foto.folder_path) / foto.name
        try:
            mappa = wallpaper.backgrounds_dir(
                output.output_dir(
                    self._get_settings().value(collage_prefs.OUTPUT_DIR_KEY)
                ),
                output._felulet_nyelve(),
            )
            bmp = wallpaper.write_background_bmp(forras, mappa)
        except OSError as hiba:
            self.photoOpFailed.emit(str(hiba))
            return False
        eszkoz = wallpaper.set_desktop_background(bmp)
        if eszkoz:
            self.desktopBackgroundApplied.emit(eszkoz)
        else:
            self.desktopBackgroundFailed.emit(str(bmp))
        return True

    @Slot(str, result=str)
    def showTagAsAlbum(self, tag: str) -> str:
        """Egy CÍMKE tartalmából rendes album (#1406, `ID_SEARCHTOKEN`).

        Az eredeti a színkeresés FORDÍTOTTJA: ott a menüpont a keresőmezőbe
        ír (#1399), itt a felhasználó megad egy címkét, és abból **rendes
        album** lesz — nem élő szűrő.

        A címkét tételenként egyeztetjük (`index.photos_with_keyword`), tehát
        a „nyár" címke nem húzza be a „nyaralás"-t. Üres címkére és találat
        nélküli címkére üres stringgel térünk vissza — a felület ebből tud
        üzenetet adni (néma hatástalanság helyett)."""
        cimke = (tag or "").strip()
        if not cimke:
            return ""
        with open_index(self._db_path) as conn:
            fotok = photos_with_keyword(conn, cimke)
        return self._albumot_keszit(cimke, list(fotok))

    # -- Keresési eredmények mentése albumként (#1405) -------------------------

    #: A megerősítés küszöbe: az eredeti CSAK e FELETT kérdez
    #: (`0x005d86a0`, `CThumbUI::SaveSearchBig`). Alatta csendben létrejön az
    #: album — a kérdés nem „biztonsági", hanem a nagy album miatti
    #: figyelmeztetés.
    SAVE_SEARCH_CONFIRM_OVER = 1000

    def _mentheto_kereses(self) -> bool:
        """Menthető-e a jelenlegi nézet albumként (a `canSaveSearch` magja).

        Csak KERESÉSI nézetben él (az eredeti parancsa is az aktív keresés
        találatát mentette), és csak ha van találat — üres keresésből album
        sem lesz. A property a fővezérlőben áll, mert a `notify` jelzései
        (`statusChanged`, `feedChanged`) ott élnek.
        """
        return self._view_mode[0] in ("search", "search-folder") and bool(
            self._photos.photos
        )

    @Slot(result=str)
    def saveSearchAsAlbum(self) -> str:
        """A keresés TELJES találata új albumba (#1405).

        Az album neve a keresés szövege. ⚠️ Ez a MI döntésünk: az eredeti
        menüfelirat három pontra végződik („Save &search results..."), ami
        párbeszédet sejtet, a mért kezelő (`0x005d86a0`, 362 bájt) viszont
        CSAK az 1000 fölötti megerősítést tartalmazza — névkérő párbeszédnek
        nincs nyoma benne. A keresés szövege a legkézenfekvőbb név, és a
        felhasználó az albumot bármikor átnevezheti.

        A megerősítést a FELÜLET kéri (a küszöb fölött), mert az eredeti is
        ott kérdez; ez a slot már a döntés utáni munkát végzi. Visszatérés: az
        új album tokenje, üres stringgel jelezve, hogy nem jött létre."""
        if not self._mentheto_kereses():
            return ""
        mode, param = self._view_mode
        nev = param if isinstance(param, str) else str(param[0])
        return self.createAlbum(nev, list(range(len(self._photos.photos))))

    def _write_album_batch(self, photos, mutate) -> bool:
        """Kötegelt albumtagság-írás hibakezeléssel (a `_write_geotag`
        mintája, `geo_controller.py`): sikertelen ütközésnél emberi
        hibaüzenet, nem néma adatvesztés. Sikeres írás után az albumlista
        (`controller.albums`) frissül, hogy a bal hasáb/menü azonnal lássa
        az új tagot/albumot. Visszaadja, hogy sikerült-e."""
        try:
            self._apply_batch(photos, mutate)
        except _WRITE_ERRORS as error:
            self.albumWriteFailed.emit(str(error))
            return False
        with open_index(self._db_path) as conn:
            self._load_albums(conn)
        return True
