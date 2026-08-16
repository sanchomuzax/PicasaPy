"""Nem-destruktív fotó-műveletek (.picasa.ini-be írva): csillag, felirat,
forgatás, elrejtés, albumtagság — az AppController művelet-szelete (#150).

Mixin-osztály: az `AppController` örökli; minden írás a round-trip ini-
rétegen át történik (atomikus mentés + backup).

#141: a csillag/felirat/forgatás (egy-képes szerkesztés) a NAS-írást
(ini-mentés: backup-olvasás + temp-írás + fsync) ÉS az utána következő
index-frissítést háttérszálon végzi — a GUI-szál egy kattintásnál sem
fagy le NAS-mappán. Az érték már a hívás pillanatában ismert, ezért az
indexbe egyetlen célzott UPDATE kerül (`update_photo_fields`) a teljes
mappa-resync (`sync_tree`) helyett, a rács pedig csak az érintett sort
frissíti (`PhotoGridModel.update_photo`), nem a teljes feedet.

#9 (2. lépés): az albumtagság-írás (`addRowsToAlbum` / `removeRowsFromAlbum`
/ `createAlbum`) az `_apply_batch` kötegelt úton megy (a `setGeotagRows`
mintája, `geo_controller.py`) — az ini-réteg (`picasapy.ini.albums`) tiszta
függvényeit hívja mutate-ként.

#426: „Az összes effektus másolása/beillesztése" (Szerkesztés menü) — az
`EffectClipboardMixin` a `picasapy.edit.effect_clipboard` tiszta logikáját
köti QML-slotokká. FONTOS: ez SZÁNDÉKOSAN külön a `picasapy.app.
effects_controller.EffectsClipboardMixin`-től (#152, „Copy/Paste All
Effects", a Kép menüből) — az a `crop64`-et IS átviszi (Picasa
„pillanatkép"-jellegű, egy-képes variánsa), ez a szelet viszont a #426
jegyben leírt hivatalos „Az összes effektus másolása/beillesztése"
viselkedést valósítja meg, ami a `crop64`/`crop`/`redeye`/`retouch`/
`moviestart`/`movieend` bejegyzéseket KIFEJEZETTEN kihagyja (ld.
`effect_clipboard` modul docstringje). A két funkció más Picasa menüponthoz
(más `ID_EDIT_*` erőforráshoz) tartozik, ezért a két vágólap-állapot is
szándékosan független egymástól."""

from __future__ import annotations

import secrets
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.effect_clipboard import copy_all_effects, paste_all_effects
from picasapy.fileops import RenameItem, preview_name, rename_photos_many
from picasapy.index import open_index, photo_by_id, update_photo_fields
from picasapy.ini import (
    FilterWriteError,
    IniConflictError,
    IniSaveError,
    update_document,
)
from picasapy.ini.albums import ensure_album, with_album, without_album
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

from .worker_thread import BackgroundWorkerMixin

# #137: a tartós ütközés (párhuzamos Picasa-írás) is kezelt írási hiba — a
# felhasználó a megszokott hibacsatornán kap jelzést, nem néma adatvesztés.
# #643: a round-trip őr visszautasítása (`FilterWriteError`) ugyanígy KEZELT
# hiba — a szövege már magyar, felhasználónak szóló mondat (ld.
# `ini/filter_guard.py`), tehát a hibasávban olvashatóan jelenik meg. Nélküle
# nyers Python-kivételként bukna ki a háttérszálon: néma bukás a felületen.
_WRITE_ERRORS = (OSError, IniSaveError, IniConflictError, FilterWriteError)


class PhotoOpsMixin(BackgroundWorkerMixin):
    """Csillag, felirat, forgatás és elrejtés — egyesével és kötegelten."""

    # #141: a háttérszálas ini-írás/index-UPDATE eredménye — a rács-sor
    # frissítését a GUI-szálra tereli (Qt automatikusan sorba állítja a
    # más szálból jövő emitet, ahogy a watcherDirty is teszi).
    _photoFieldUpdated = Signal(int, object)  # (photo_id, PhotoRecord | None)
    photoOpFailed = Signal(str)
    photoOpFinished = Signal()
    # #9 (2. lépés): tartós ini-ütközésnél (párhuzamos Picasa-írás) emberi
    # hibaüzenet az albumtagság-íráshoz — a geoWriteFailed mintája.
    albumWriteFailed = Signal(str)
    # #366: a tömeges átnevezés (fájlrendszer-írás, lehet lassú NAS-on)
    # háttérszálon fut; ez a jelzés tereli a resync/refresh-t vissza a
    # GUI-szálra, a `_photoFieldUpdated` mintája szerint.
    _renameBatchDone = Signal(list)  # [érintett mappák]
    # #459: sérült/betölthetetlen kép(ek) — a QML ebből építi az eredeti
    # Picasa szövege szerinti elrejtés-felajánlást ("...Would you like to
    # hide the files on disk?"). Elemek: {"id": int, "name": str}.
    brokenPhotosDetected = Signal(list)

    def _ensure_broken_photo_wired(self) -> None:
        """#459: a ThumbnailProvider `brokenImageDetected`-jét a photo-id
        alapján a REGISZTRÁLT (jelenleg betöltött) fotóra oldja fel, és
        — fotónként EGYSZER — továbbítja a QML-nek. Külön a
        `_ensure_photo_ops_wired`-től: ez böngészés közben, bármilyen
        szerkesztés NÉLKÜL is bekövetkezhet, ezért a controller
        konstruktora hívja MÁR a `self._provider` beállítása után, nem
        lustán az első íráskor."""
        if getattr(self, "_broken_photo_wired", False):
            return
        self._broken_photo_wired = True
        self._broken_photo_ids: set[int] = set()
        self._provider.brokenImageDetected.connect(self._on_broken_image_detected)

    @Slot(str)
    def _on_broken_image_detected(self, photo_id: str) -> None:
        try:
            pid = int(photo_id.split("?", 1)[0])
        except ValueError:
            return
        if pid in self._broken_photo_ids:
            return
        photo = next((p for p in self._photos.photos if p.id == pid), None)
        if photo is None:
            return
        self._broken_photo_ids.add(pid)
        self.brokenPhotosDetected.emit([{"id": pid, "name": photo.name}])

    @Slot(list)
    def hidePhotosByIds(self, ids) -> None:
        """#459: a sérült-kép ajánlat "Hide Files" válasza — a MEGLÉVŐ
        elrejtés-úton (`_apply_batch`, a `toggleHiddenRows` mintája) fut,
        csak nem a rács aktuális sorindexeiből, hanem közvetlenül az
        id-kból dolgozik (a törött kép ekkorra már ki is görgethetett a
        nézetből)."""
        id_set = {int(i) for i in ids}
        photos = [p for p in self._photos.photos if p.id in id_set]
        if not photos:
            return

        def mutate(document, photo):
            return document.with_value(photo.name, "hidden", "yes")

        self._apply_batch(photos, mutate)

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
        self._renameBatchDone.connect(self._on_rename_batch_done)

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
        self.photoOpFinished.emit()

    @Slot(str)
    def _on_photo_write_failed(self, message: str) -> None:
        # meglévő hibajelzési minta (#86/#150): ugyanaz a csatorna, mint a
        # háttér-szinkron hibáié
        self.syncFailed.emit(message)
        self.photoOpFinished.emit()

    def _run_photo_write(self, photo_id: int, perform) -> None:
        """Ini/IPTC-írás (NAS: backup+temp+fsync) + célzott index-UPDATE
        háttérszálon (#141). A `perform()` a teljes lassú munkát végzi (fájl-
        írás + a {oszlop: érték} dict összeállítása), és teljes egészében a
        munkásszálon fut. #505: a busy-jelzést a `_start_background`
        (`worker_thread.py`) intézi, nem itt."""
        self._ensure_photo_ops_wired()

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

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-photowrite")

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

            def mutate(document):
                if new_star:
                    return document.with_value(photo.name, "star", "yes")
                return document.with_removed(photo.name, "star")

            update_document(ini_path, mutate, backup=True)
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

            def mutate(document):
                if text:
                    return document.with_value(photo.name, "caption", text)
                return document.with_removed(photo.name, "caption")

            update_document(ini_path, mutate, backup=True)
            return {"caption_ini": text or None}

        self._run_photo_write(photo.id, perform)

    # -- tömeges átnevezés (#366, rename.fen paritás) ------------------------

    @Slot(list, str, bool, bool, result=str)
    def renamePreview(
        self, rows, base_name: str, include_date: bool, include_size: bool
    ) -> str:
        """A `rename.fen` élő előnézete: a kijelölés ELSŐ fájljának végleges
        neve, ha most elfogadnák a dialógust (sorszám nélkül — ő az első a
        sorban). Tiszta lekérdezés, nem ír semmit."""
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
        self.photoOpFinished.emit()

    # -- virtuális albumok (#9, 2. lépés) ------------------------------------

    @Slot(list, str)
    def addRowsToAlbum(self, rows, token: str) -> None:
        """A kijelölés felvétele egy MEGLÉVŐ albumba: az `albums=` CSV
        bővítése minden érintett fotónál, mappánként egyetlen ütközésbiztos
        ini-írással (`_apply_batch`, a `setGeotagRows` mintája)."""
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        def mutate(document, photo):
            return with_album(document, photo.name, token)

        self._write_album_batch(valid, mutate)

    @Slot(list, str)
    def removeRowsFromAlbum(self, rows, token: str) -> None:
        """A kijelölés kivétele egy albumból (a definíció, `[.album:token]`,
        a mappában marad — csak a tagság törlődik, ahogy a Picasa is teszi)."""
        token = (token or "").strip()
        if not token:
            return
        valid = self._rows_to_photos(rows)
        if not valid:
            return

        def mutate(document, photo):
            return without_album(document, photo.name, token)

        self._write_album_batch(valid, mutate)

    @Slot(str, list, result=str)
    def createAlbum(self, name: str, rows) -> str:
        """Új virtuális album a kijelölt képekkel: véletlen (32 hex karakteres)
        token, a `[.album:<token>]` definíció MINDEN érintett mappa ini-jébe
        kiírva — a Picasa is minden mappába kiírja, ahol az albumnak van
        tagja —, a tagság pedig `with_album`-mal minden kijelölt fotónál.
        Visszaadja az új tokent (üres kijelölésnél/hibánál üres stringet)."""
        valid = self._rows_to_photos(rows)
        if not valid:
            return ""
        token = secrets.token_hex(16)
        clean_name = (name or "").strip() or None

        def mutate(document, photo):
            document = ensure_album(document, token, clean_name)
            return with_album(document, photo.name, token)

        if not self._write_album_batch(valid, mutate):
            return ""
        return token

    def _rows_to_photos(self, rows) -> list:
        photos = self._photos.photos
        return [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]

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

            def mutate(document):
                if steps == 0:
                    return document.with_removed(photo.name, "rotate")
                return document.with_value(photo.name, "rotate", f"rotate({steps})")

            update_document(ini_path, mutate, backup=True)
            return {"rotate_steps": steps}

        self._run_photo_write(photo.id, perform)

    # -- „Az összes effektus másolása/beillesztése" (#426) -------------------

    #: A vágólap tartalma/állapota változott (van-e másolt lánc, van-e
    #: visszavonható beillesztés) — a Szerkesztés menü két tételének
    #: engedélyezési feltétele.
    allEffectsClipboardChanged = Signal()

    def _ensure_effect_clipboard(self) -> None:
        """Lusta állapot-inicializálás (#150-minta: nem kell az __init__-et
        (forró fájl) módosítani a szelet bevezetéséhez). Szándékosan KÜLÖN
        állapot a `effects_controller.EffectsClipboardMixin`-től (#152) — a
        modul docstringje indokolja, miért két önálló funkció."""
        if not hasattr(self, "_effect_clipboard_value"):
            self._effect_clipboard_value: str | None = None
            # egyetlen visszavonási lépés (#426 elfogadási kritérium): az
            # utolsó beillesztés ELŐTTI (mappa, fájlnév, nyers filters=)
            # hármasainak listája; None = nincs (törölve/le nem futott)
            self._effect_clipboard_undo: list[tuple[str, str, str | None]] | None = (
                None
            )

    @Property(bool, notify=allEffectsClipboardChanged)
    def hasAllEffectsClipboard(self) -> bool:
        """Van-e másolt effektlánc — a „Beillesztés" menütétel engedélyezési
        feltétele."""
        self._ensure_effect_clipboard()
        return self._effect_clipboard_value is not None

    @Property(bool, notify=allEffectsClipboardChanged)
    def canUndoPasteAllEffects(self) -> bool:
        self._ensure_effect_clipboard()
        return self._effect_clipboard_undo is not None

    @Slot(list)
    def copyAllEffects(self, rows) -> None:
        """„Az összes effektus másolása": a kijelölés ELSŐ képének szűrt
        `filters=` lánca (a kép-/régióspecifikus bejegyzések nélkül, ld.
        `picasapy.edit.effect_clipboard`) kerül az alkalmazás-szintű
        vágólapra. Tiszta lekérdezés — nem ír semmit."""
        self._ensure_effect_clipboard()
        photos = self._photos.photos
        valid_rows = [int(r) for r in rows if 0 <= int(r) < len(photos)]
        if not valid_rows:
            return
        photo = photos[valid_rows[0]]
        self._effect_clipboard_value = copy_all_effects(photo.filters)
        self.allEffectsClipboardChanged.emit()

    @Slot(list)
    def pasteAllEffects(self, rows) -> None:
        """„Az összes effektus beillesztése": a vágólap láncát a kijelölt
        képek MINDEGYIKÉRE alkalmazza, felülírva a meglévő láncot (#426).

        Mappánként EGYETLEN ini-írás (a `_apply_batch`/`effects_controller.
        EffectsClipboardMixin.pasteEffects` mintája): a beillesztés előtti
        nyers `filters=` értékek egyetlen undo-lépésként kerülnek a verembe,
        hogy a teljes köteg egy `undoPasteAllEffects()` hívással
        visszavonható legyen. Nincs háttérszál — az ini-írás gyors (nincs
        képfeldolgozás), a `_apply_batch`/`EffectsClipboardMixin.
        pasteEffects` szinkron mintáját követi."""
        self._ensure_effect_clipboard()
        if self._effect_clipboard_value is None:
            return
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        clipboard_value = self._effect_clipboard_value
        new_value = paste_all_effects(clipboard_value)

        by_folder: dict[str, list] = {}
        for photo in valid:
            by_folder.setdefault(photo.folder_path, []).append(photo)

        undo_batch: list[tuple[str, str, str | None]] = []
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None]] = []

                # B023: az `entries` alapértelmezett argumentumként kötve —
                # a mutate szinkron fut, mielőtt a következő iteráció
                # újrakötné (az `effects_controller.pasteEffects` mintája).
                def mutate(
                    document, folder=folder, folder_photos=folder_photos, entries=entries
                ):
                    fresh: list[tuple[str, str, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        fresh.append((folder, photo.name, prev))
                        if new_value:
                            # #643: a vágólapról ÁTVITT lánc — az idegen tag
                            # nem most keletkezik, ezért nem utasítjuk vissza.
                            document = document.with_value(
                                photo.name, "filters", new_value, carried=True
                            )
                        else:
                            document = document.with_removed(photo.name, "filters")
                    entries[:] = fresh
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                undo_batch.extend(entries)
                self._sync_tree(conn, folder)

        self._effect_clipboard_undo = undo_batch
        self.allEffectsClipboardChanged.emit()
        self._refresh_view()

    @Slot()
    def undoPasteAllEffects(self) -> None:
        """Az utolsó „Az összes effektus beillesztése" visszavonása — minden
        érintett kép `filters=` kulcsa visszaáll a beillesztés előtti (nyers)
        értékre (#426 elfogadási kritérium: egyetlen visszavonási lépés)."""
        self._ensure_effect_clipboard()
        if not self._effect_clipboard_undo:
            return
        batch = self._effect_clipboard_undo
        self._effect_clipboard_undo = None

        by_folder: dict[str, list[tuple[str, str | None]]] = {}
        for folder, name, prev_filters in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters))

        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for name, prev_filters in entries:
                        if prev_filters is not None:
                            document = document.with_value(
                                name, "filters", prev_filters, carried=True  # #643
                            )
                        else:
                            document = document.with_removed(name, "filters")
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                self._sync_tree(conn, folder)

        self.allEffectsClipboardChanged.emit()
        self._refresh_view()
