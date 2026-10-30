"""Az album-műveletek properties reszmixinje (#6273)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import open_index
from picasapy.ini import load_existing
from picasapy.ini.albums import albums_of, with_album_fields
from picasapy.ini.document import ALBUM_SECTION_PREFIX
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .photo_ops_compat import _WRITE_ERRORS, update_document


class PhotoOpsAlbumPropertiesMixin:
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
