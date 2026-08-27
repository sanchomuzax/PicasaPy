"""Felirat-írás egy és több képre (#1526) — az `AppController` szelete.

A Szerkesztés menü **„Szöveg beillesztése"** (`eMenuEdit::ID_EDIT_PASTETEXT`)
a TELJES kijelölésre hat, a „Szöveg másolása" párjaként — ugyanúgy, ahogy az
„Az összes effektus beillesztése" is. Egy sorra szabott `setCaption` ehhez
nem elég: N kép esetén N háttérszál indulna ugyanarra a `.picasa.ini`-re.

Ezért a köteg **egyetlen** háttérszálon, **sorban** fut, és a végén egyszer
frissíti a rács sorait — a `PhotoOpsMixin._run_photo_write` mintája, csak
több képre.

## Az írás helye: a Picasa szabálya (spec #3)

JPEG-nél a felirat a **képfájlba** megy (IPTC), minden más formátumnál a
`.picasa.ini`-be. Az IPTC-írás sikertelensége (sérült fájl, ismeretlen
szegmens) nem hibaág: defenzíven az ini-útra esünk vissza — ez a viselkedés
a `PhotoOpsMixin.setCaption`-ből származik, és a két út MOST MÁR UGYANAZT a
`write_caption()` függvényt használja, hogy ne csúszhassanak szét.

Külön fájlban, mert a `photo_ops_controller.py` már 800 sor fölött jár; a
bekötés a `PhotoOpsMixin` bázisosztályaként történik, tehát a forró
`controller.py` mixin-listája nem változik (az `AppearanceMixin` ↔
`FolderPhotoSortMixin` mintája, #1436).
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.index import open_index, photo_by_id, update_photo_fields
from picasapy.ini import IniConflictError, IniSaveError, update_document
from picasapy.ini.filter_guard import FilterWriteError
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

_JPEG_SUFFIXES = (".jpg", ".jpeg")

# #137/#643: a KEZELT írási hibák. Itt él, nem a `photo_ops_controller`-ben,
# mert ez a modul annak a BÁZISA — a `photo_ops_controller` innen importálja,
# hogy a két írási út ugyanazt a hibahalmazt kezelje.
WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)


def write_caption(folder_path: str, name: str, text: str) -> dict:
    """A felirat lemezre írása EGY képhez; a frissítendő index-mezőket adja.

    JPEG-nél az IPTC-be (a képfájlba), minden más formátumnál — és sikertelen
    IPTC-írás után — a `.picasa.ini`-be. Üres szöveg a kulcsot TÖRLI, ahogy a
    Picasa is teszi.
    """
    text = text.strip()
    if name.lower().endswith(_JPEG_SUFFIXES):
        if write_iptc_caption(Path(folder_path) / name, text):
            return {"caption_file": text or None}
    ini_path = Path(folder_path) / PICASA_INI_NAME

    def mutate(document):
        if text:
            return document.with_value(name, "caption", text)
        return document.with_removed(name, "caption")

    update_document(ini_path, mutate, backup=True)
    return {"caption_ini": text or None}


class CaptionOpsMixin:
    """`setCaptionMany` — kötegelt feliratírás EGY háttérszálon.

    A `PhotoOpsMixin` bázisa; a `self._photos`, `self._db_path`,
    `self._provider`, `self._start_background` és a `photoOpFailed` /
    `photoOpFinished` jelzések onnan valók.
    """

    #: A köteg lefutott — [(photo_id, record)] a GUI-szálra terelve.
    _captionBatchDone = Signal(list)

    def _ensure_caption_ops_wired(self) -> None:
        """Lusta, egyszeri bekötés — a forró `controller.py` __init__-je nem
        változik (a `_ensure_photo_ops_wired` mintája)."""
        if getattr(self, "_caption_ops_wired", False):
            return
        self._caption_ops_wired = True
        self._captionBatchDone.connect(self._on_caption_batch_done)

    @Slot(list, str)
    def setCaptionMany(self, rows, text: str) -> None:
        """Ugyanaz a felirat a kijelölés MINDEN képére (#1526).

        Üres kijelölésnél nem csinál semmit — a menüpont ilyenkor szürke,
        tehát ez csak védőháló."""
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        self._ensure_photo_ops_wired()
        self._ensure_caption_ops_wired()

        def worker() -> None:
            written: list[tuple[int, dict]] = []
            try:
                for photo in valid:
                    fields = write_caption(photo.folder_path, photo.name, text)
                    written.append((photo.id, fields))
                with open_index(self._db_path) as conn:
                    for photo_id, fields in written:
                        update_photo_fields(conn, photo_id, **fields)
                    records = [
                        (photo_id, photo_by_id(conn, photo_id))
                        for photo_id, _ in written
                    ]
            except WRITE_ERRORS as error:
                # #301 mintája: a köteg egy hibás fájlnál sem hallgathat el —
                # az addig megírt képek a lemezen maradnak, a felhasználó
                # pedig üzenetet kap
                self.photoOpFailed.emit(str(error))
                return
            self._captionBatchDone.emit(records)

        self._start_background(worker, name="picasapy-captionbatch")

    @Slot(list)
    def _on_caption_batch_done(self, records) -> None:
        for photo_id, record in records:
            if record is not None:
                self._photos.update_photo(photo_id, record)
        self._provider.register_photos(self._photos.photos)
        # #1515: a felirat FTS-mező — keresési nézetben a köteg kieshet a
        # találatok közül, ezért ugyanaz az utómunka fut, mint egy sorra
        for photo_id, _record in records:
            self._refresh_if_dropped_from_search(photo_id)
        self.photoOpFinished.emit()


__all__ = ["WRITE_ERRORS", "CaptionOpsMixin", "write_caption"]
