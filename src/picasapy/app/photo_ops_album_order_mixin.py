"""Az album-műveletek order reszmixinje (#6273)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Slot
from PySide6.QtGui import QGuiApplication

from picasapy.app.kezi_sorrend import mappa_prioritasai, mentsd_a_prioritasokat
from picasapy.index import album_photos, open_index, photos_in_folder
from picasapy.index.album_sort import SORT_MODES, new_places, sorted_album
from picasapy.ini.album_order import AlbumOrderWriteError, write_album_places
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_compat import _WRITE_ERRORS


class PhotoOpsAlbumOrderMixin:
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
