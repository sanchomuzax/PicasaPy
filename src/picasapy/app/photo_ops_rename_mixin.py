"""A fényképfájlok tömeges átnevezésének témamixinje."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.fileops import PartialRenameError, RenameItem, preview_name, rename_photos_many
from picasapy.index import open_index
from picasapy.ini import IniConflictError, IniSaveError

from .appearance_controller import coerce_ui_preference_flag
from .photo_ops_compat import (
    RENAME_USE_DATE_KEY,
    RENAME_USE_SIZE_KEY,
    rename_sample_constants as _rename_sample_constants,
)


class PhotoOpsRenameMixin:
    _renameBatchDone = Signal(list)

    @Slot(result=bool)
    def renameUseDate(self) -> bool:
        """A „Date” jelölőnégyzet mentett állása (alap: ki)."""
        return coerce_ui_preference_flag(
            self._get_settings().value(RENAME_USE_DATE_KEY), False)

    @Slot(result=bool)
    def renameUseSize(self) -> bool:
        """Az „Image resolution” jelölőnégyzet mentett állása (alap: ki)."""
        return coerce_ui_preference_flag(
            self._get_settings().value(RENAME_USE_SIZE_KEY), False)

    @Slot(bool, bool)
    def setRenameUseFlags(self, use_date: bool, use_size: bool) -> None:
        """A két jelölőnégyzet állásának mentése (QSettings)."""
        settings = self._get_settings()
        settings.setValue(RENAME_USE_DATE_KEY, "true" if use_date else "false")
        settings.setValue(RENAME_USE_SIZE_KEY, "true" if use_size else "false")

    @Slot(list, str, bool, bool, result=str)
    def renamePreview(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> str:
        """A kijelölés első képének tényleges célneve, sorszám nélkül.

        A dialógus elfogadásakor ez tartja életben a meglévő átnevezési út
        célútvonalát; a látható, rögzített `Example` mintát a
        `renameSamplePreview` állítja elő.
        """
        photos = self._rows_to_photos(rows)
        if not photos or not (base_name or "").strip():
            return ""
        photo = photos[0]
        item = RenameItem(
            path=Path(photo.folder_path) / photo.name,
            date=photo.taken_at,
            width=photo.width,
            height=photo.height,
        )
        return preview_name(
            base_name.strip(), item,
            include_date=include_date, include_size=include_size, sequence=0,
        )

    @Slot(list, str, bool, bool, result=str)
    def renameSamplePreview(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> str:
        """A `rename.fen` Example sora a Picasa rögzített mintáival.

        Csak azt ellenőrzi, hogy van-e kijelölés; dátumot, felbontást és
        kiterjesztést nem olvas a fájlokból.
        """
        base_name = (base_name or "").strip()
        if not rows or not base_name:
            return ""
        sample_date, sample_size, sample_extension = _rename_sample_constants()
        date_sample = sample_date if include_date else ""
        size_sample = sample_size if include_size else ""
        return (
            f"{base_name}{date_sample}{size_sample}"
            f"{sample_extension}"
        )

    @Slot(list, str, bool, bool)
    def renamePhotosMany(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> None:
        """Tömeges átnevezés (#366): a kijelölt N fájl közös alapnevet kap
        (+ opcionális dátum-/felbontás-utótag), Picasa-mintájú sorszámozással
        (`név`, `név-1`, `név-2`…). Az egyfájlos F2-út
        (`FileOpsController.renamePhoto`) ettől függetlenül, változatlanul
        működik — ez egy külön, kötegelt művelet. A lemezírás (potenciálisan
        lassú NAS) és az utána következő resync háttérszálon fut, a
        csillag/felirat mintáját követve (#141)."""
        base_name = (base_name or "").strip()
        photos = self._rows_to_photos(rows)
        if not base_name or not photos:
            return
        self._ensure_photo_ops_wired()

        items = [
            RenameItem(
                path=Path(photo.folder_path) / photo.name,
                date=photo.taken_at,
                width=photo.width,
                height=photo.height,
            )
            for photo in photos
        ]

        def worker() -> None:
            try:
                rename_photos_many(
                    items, base_name,
                    include_date=include_date, include_size=include_size,
                )
            except PartialRenameError as error:
                # Részleges futásnál a fájlok/ini-szekciók egy része már
                # megváltozott. Frissítsük ugyanazokat a mappákat, majd a
                # strukturált hibaszöveg mutassa meg, mely nevek készültek el.
                folders = sorted({str(item.path.parent) for item in items})
                self._renameBatchDone.emit(folders)
                self.photoOpFailed.emit(str(error))
                return
            except (OSError, ValueError, IniSaveError, IniConflictError) as error:
                self.photoOpFailed.emit(str(error))
                return
            folders = sorted({str(item.path.parent) for item in items})
            self._renameBatchDone.emit(folders)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-rename")

    @Slot(list)
    def _on_rename_batch_done(self, folders: list[str]) -> None:
        """A háttérszálas tömeges átnevezés után (GUI-szálon): érintett
        mappák resyncje + a nézet frissítése — az `_apply_batch` mintája,
        csak háttérszálas indítással (a lemezírás már megtörtént)."""
        with open_index(self._db_path) as conn:
            for folder in folders:
                self._sync_tree(conn, folder)
        self._refresh_view()
