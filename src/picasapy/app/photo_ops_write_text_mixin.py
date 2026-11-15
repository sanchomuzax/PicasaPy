"""A fotóíró mixin felirat- és szövegréteg-segédjei."""

from __future__ import annotations

import os
import stat
from pathlib import Path

from picasapy.index import open_index
from picasapy.ini import load_or_empty, with_backuphash
from picasapy.ini.text_overlay import parse_text
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

from .ini_ujraprobalas import update_document_ujraprobalva
from .photo_ops_compat import update_document


def _irasvedett(path: Path) -> bool:
    """Írásvédett-e a fájl (#7027, J4).

    Az eredeti a fájl írásvédett attribútumánál kihagyja a fájlba írást, és a
    feliratot a `.picasa.ini`-be teszi (`0x0043859e-0x004385a5`). Az írási
    jog hiányát a mód-bitből ÉS a tényleges hozzáférésből is vesszük: az
    elsőt a Windows az írásvédett attribútumra képezi, a másodikat más
    felhasználó tulajdonában álló fájl elkapja. (Az atomikus csere a
    könyvtár jogán fut, ezért az írásvédett fájlt némán lecserélné.)"""
    try:
        mod = path.stat().st_mode
    except OSError:
        return False
    return not mod & stat.S_IWRITE or not os.access(path, os.W_OK)


class PhotoOpsWriteTextMixin:

    def _fuggo_feliratok(self) -> dict[int, str]:
        """Az épp írás alatt álló feliratok: kép azonosítója -> szöveg."""
        if not hasattr(self, "_fuggo_felirat_irasok"):
            self._fuggo_felirat_irasok: dict[int, str] = {}
        return self._fuggo_felirat_irasok

    def _ensure_text_layer_clipboard(self) -> None:
        if not hasattr(self, "_text_layer_clipboard_value"):
            self._text_layer_clipboard_value: str | None = None

    @staticmethod
    def _text_layer_value(photo) -> str | None:
        """A kép értelmezhető, nem üres Text eszközös `text=` sora."""
        if photo.kind == "video":
            return None
        try:
            document = load_or_empty(
                Path(photo.folder_path) / PICASA_INI_NAME
            )
        except (OSError, UnicodeError):
            return None
        section = document.section(photo.name)
        raw = section.get("text") if section is not None else None
        if not raw:
            return None
        try:
            overlay = parse_text(raw)
        except ValueError:
            return None
        if overlay is None or not any(block.content for block in overlay.blocks):
            return None
        return raw

    def _felirat_iras(self, photo, text: str):
        """Egy kép felirat-írása `(photo_id, perform)` párként (#2915).

        A `perform()` a teljes lassú munka (IPTC- vagy ini-írás). JPEG-nél
        a felirat a fájl IPTC-jébe megy; ha a fájl írásvédett (#7027), vagy
        az IPTC-írás nem sikerül, a `.picasa.ini` `caption=` kulcsába."""
        text = (text or "").strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))

        def perform() -> dict:
            if is_jpeg:
                path = Path(photo.folder_path) / photo.name
                if not _irasvedett(path) and write_iptc_caption(path, text):
                    ini_path = Path(photo.folder_path) / PICASA_INI_NAME
                    # #5900: az IPTC-írás után Windowson az ini átmenetileg
                    # zárolt lehet; a backuphash-lépés ezért újrapróbál.
                    update_document_ujraprobalva(
                        ini_path,
                        lambda document: with_backuphash(document, photo.name),
                        backup=True,
                    )
                    return {"caption_file": text or None}
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME

            def mutate(document):
                if text:
                    document = document.with_value(photo.name, "caption", text)
                else:
                    document = document.with_removed(photo.name, "caption")
                return with_backuphash(document, photo.name)

            update_document(ini_path, mutate, backup=True)
            return {"caption_ini": text or None}

        return photo.id, perform

    def _rows_to_photos(self, rows) -> list:
        photos = self._photos.photos
        return [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]

    def _apply_batch(self, photos, mutate) -> None:
        """Kötegelt ini-módosítás: mappánként egyetlen (atomikus, backupolt)
        írás és resync, de EGYETLEN index-kapcsolat a teljes köteg körül
        (#141) — nem mappánként újracsatlakozás."""
        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                # #137: a köteg egyetlen tiszta mutate-ként fut az
                # update_document alatt — ütközés esetén az egész köteg
                # újrajátszódik a friss (más író általi) dokumentumon.
                def batch_mutate(document, folder_photos=folder_photos):
                    for photo in folder_photos:
                        document = mutate(document, photo)
                    return document

                update_document(ini_path, batch_mutate, backup=True)
                self._sync_tree(conn, folder)
        self._refresh_view()
