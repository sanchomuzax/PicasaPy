"""Nem-destruktív fotó-műveletek (.picasa.ini-be írva): csillag, felirat,
forgatás, elrejtés — az AppController művelet-szelete (#150).

Mixin-osztály: az `AppController` örökli; minden írás a round-trip ini-
rétegen át történik (atomikus mentés + backup).

#141: a csillag/felirat/forgatás (egy-képes szerkesztés) a NAS-írást
(ini-mentés: backup-olvasás + temp-írás + fsync) ÉS az utána következő
index-frissítést háttérszálon végzi — a GUI-szál egy kattintásnál sem
fagy le NAS-mappán. Az érték már a hívás pillanatában ismert, ezért az
indexbe egyetlen célzott UPDATE kerül (`update_photo_fields`) a teljes
mappa-resync (`sync_tree`) helyett, a rács pedig csak az érintett sort
frissíti (`PhotoGridModel.update_photo`), nem a teljes feedet."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Signal, Slot

from picasapy.index import open_index, photo_by_id, update_photo_fields
from picasapy.ini import IniSaveError, load_or_empty, save_document
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

_WRITE_ERRORS = (OSError, IniSaveError)


class PhotoOpsMixin:
    """Csillag, felirat, forgatás és elrejtés — egyesével és kötegelten."""

    # #141: a háttérszálas ini-írás/index-UPDATE eredménye — a rács-sor
    # frissítését a GUI-szálra tereli (Qt automatikusan sorba állítja a
    # más szálból jövő emitet, ahogy a watcherDirty is teszi).
    _photoFieldUpdated = Signal(int, object)  # (photo_id, PhotoRecord | None)
    photoOpFailed = Signal(str)
    photoOpFinished = Signal()

    def _ensure_photo_ops_wired(self) -> None:
        """A jelzések bekötése lusta, egyszeri — így a controller.py
        (forró fájl) __init__-jét nem kell módosítani (#150 mintakövetés:
        az integrátor köti be a végleges osztályt, a szelet önmagában is
        működőképes)."""
        if getattr(self, "_photo_ops_wired", False):
            return
        self._photo_ops_wired = True
        self._photoFieldUpdated.connect(self._on_photo_field_updated)
        self.photoOpFailed.connect(self._on_photo_write_failed)

    @Slot(int, object)
    def _on_photo_field_updated(self, photo_id: int, record) -> None:
        if record is not None:
            self._photos.update_photo(photo_id, record)
            # a thumbnail-provider saját (memóriabeli) nyilvántartását is
            # frissíteni kell (forgatás!) — ezt eddig a teljes _show()
            # tette meg; célzott frissítésnél nem fut _show(), ezért itt
            # pótoljuk (olcsó, csak a jelen nézet listáját írja újra, nem
            # lemezműveletet indít)
            self._provider.register_photos(self._photos.photos)
        self._on_sync_job_done()
        self.photoOpFinished.emit()

    @Slot(str)
    def _on_photo_write_failed(self, message: str) -> None:
        # meglévő hibajelzési minta (#86/#150): ugyanaz a csatorna, mint a
        # háttér-szinkron hibáié
        self.syncFailed.emit(message)
        self._on_sync_job_done()
        self.photoOpFinished.emit()

    def _run_photo_write(self, photo_id: int, perform) -> None:
        """Ini/IPTC-írás (NAS: backup+temp+fsync) + célzott index-UPDATE
        háttérszálon (#141). A `perform()` a teljes lassú munkát végzi (fájl-
        írás + a {oszlop: érték} dict összeállítása), és teljes egészében a
        munkásszálon fut."""
        self._ensure_photo_ops_wired()
        self._begin_sync_job()

        def worker() -> None:
            try:
                fields = perform()
                with open_index(self._db_path) as conn:
                    if fields:
                        update_photo_fields(conn, photo_id, **fields)
                    record = photo_by_id(conn, photo_id)
            except _WRITE_ERRORS as error:
                self.photoOpFailed.emit(str(error))
                return
            self._photoFieldUpdated.emit(photo_id, record)

        threading.Thread(target=worker, daemon=True).start()

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        new_star = not photo.star

        def perform() -> dict:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME
            document = load_or_empty(ini_path)
            if new_star:
                document = document.with_value(photo.name, "star", "yes")
            else:
                document = document.with_removed(photo.name, "star")
            save_document(document, ini_path, backup=True)
            return {"star": int(new_star)}

        self._run_photo_write(photo.id, perform)

    @Slot(int, str)
    def setCaption(self, row: int, text: str) -> None:
        """Felirat mentése — Picasa írási szabály (spec #3): JPEG-nél az
        IPTC-be (a képfájlba) írjuk, minden más formátumnál a .picasa.ini-be,
        ahogy a csillag/forgatás is. Az IPTC-írás sikertelensége esetén
        (pl. sérült fájl) defenzíven az ini-útra esünk vissza."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        text = text.strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))

        def perform() -> dict:
            if is_jpeg:
                path = Path(photo.folder_path) / photo.name
                if write_iptc_caption(path, text):
                    return {"caption_file": text or None}
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME
            document = load_or_empty(ini_path)
            if text:
                document = document.with_value(photo.name, "caption", text)
            else:
                document = document.with_removed(photo.name, "caption")
            save_document(document, ini_path, backup=True)
            return {"caption_ini": text or None}

        self._run_photo_write(photo.id, perform)

    @Slot(list)
    def toggleHiddenRows(self, rows) -> None:
        """Elrejtés/Megjelenítés a kijelölésre (Picasa): ha van még nem
        rejtett a kijelöltek közt, mindet elrejti; ha mind rejtett, mindet
        megjeleníti. Az ini-be `hidden=yes` kulcs kerül (levételkor törlődik)."""
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        hide_all = not all(p.hidden for p in valid)

        def mutate(document, photo):
            if hide_all:
                return document.with_value(photo.name, "hidden", "yes")
            return document.with_removed(photo.name, "hidden")

        self._apply_batch(valid, mutate)

    @Slot(list)
    def toggleStarMany(self, rows) -> None:
        """Csillag a teljes kijelölésre (Picasa-viselkedés): ha van még
        csillagozatlan a kijelöltek közt, mindet csillagozza; ha mind az,
        mindről leveszi. Mappánként EGY ini-írás + sync."""
        photos = self._photos.photos
        valid = [
            photos[int(r)] for r in rows if 0 <= int(r) < len(photos)
        ]
        if not valid:
            return
        star_all = not all(p.star for p in valid)

        def mutate(document, photo):
            if star_all:
                return document.with_value(photo.name, "star", "yes")
            return document.with_removed(photo.name, "star")

        self._apply_batch(valid, mutate)

    @Slot(list)
    def rotateRightMany(self, rows) -> None:
        self._rotate_many(rows, 1)

    @Slot(list)
    def rotateLeftMany(self, rows) -> None:
        self._rotate_many(rows, -1)

    def _rotate_many(self, rows, delta: int) -> None:
        photos = self._photos.photos
        # #103: a videókat kihagyjuk — a rotate= kulcsnak videón nincs
        # értelmes hatása; vegyes kijelölésnél csak a fotók forognak
        valid = [
            photos[int(r)]
            for r in rows
            if 0 <= int(r) < len(photos) and photos[int(r)].kind != "video"
        ]
        if not valid:
            return

        def mutate(document, photo):
            steps = (photo.rotate_steps + delta) % 4
            if steps == 0:
                return document.with_removed(photo.name, "rotate")
            return document.with_value(photo.name, "rotate", f"rotate({steps})")

        self._apply_batch(valid, mutate)

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
                document = load_or_empty(ini_path)
                for photo in folder_photos:
                    document = mutate(document, photo)
                save_document(document, ini_path, backup=True)
                self._sync_tree(conn, folder)
        self._refresh_view()

    @Slot(int)
    def rotateRight(self, row: int) -> None:
        self._apply_rotate(row, 1)

    @Slot(int)
    def rotateLeft(self, row: int) -> None:
        self._apply_rotate(row, -1)

    def _apply_rotate(self, row: int, delta: int) -> None:
        """Nem-destruktív forgatás: rotate=rotate(n) az ini-be; n=0-nál a
        kulcs törlődik, így a teljes kör bitre pontos round-trip."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        if photo.kind == "video":
            return  # #103: videóra nem írunk rotate= kulcsot (QML-őr mellett)
        steps = (photo.rotate_steps + delta) % 4

        def perform() -> dict:
            ini_path = Path(photo.folder_path) / PICASA_INI_NAME
            document = load_or_empty(ini_path)
            if steps == 0:
                document = document.with_removed(photo.name, "rotate")
            else:
                document = document.with_value(photo.name, "rotate", f"rotate({steps})")
            save_document(document, ini_path, backup=True)
            return {"rotate_steps": steps}

        self._run_photo_write(photo.id, perform)
