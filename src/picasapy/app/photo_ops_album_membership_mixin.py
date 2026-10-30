"""Az album-műveletek membership reszmixinje (#6273)."""

from __future__ import annotations

from pathlib import Path
import secrets

from PySide6.QtCore import QCoreApplication, Slot

from picasapy.index import open_index
from picasapy.index.albums import (
    _pending_empty_album,
    _remove_empty_album,
    _store_empty_album,
)
from picasapy.ini import STAR_ALBUM_TOKEN
from picasapy.ini.albums import (
    ensure_album,
    with_album,
    with_album_fields,
    without_album,
    without_album_everywhere,
)

from .photo_ops_compat import _WRITE_ERRORS, update_document


class PhotoOpsAlbumMembershipMixin:
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
        maradnak. A még tag nélküli albumot az index függő tárából veszi ki
        (#6281). Visszatérés: töröltünk-e bármit.
        """
        token = (token or "").strip()
        if not token:
            return False
        erintett = list(self._album_dokumentumok(token))

        try:
            with open_index(self._db_path) as conn:
                # #6281: a még tag nélküli album csak az indexben él
                fuggo = _remove_empty_album(conn, token)
                if not erintett and not fuggo:
                    return False
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
