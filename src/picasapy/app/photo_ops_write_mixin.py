"""A fotómezők, feliratok, vágólapok és közös írási út témamixinje."""

from __future__ import annotations

# A régi modulútvonal nyilvános importjai kompatibilitásból újraexportálódnak.
# ruff: noqa: F401

from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.index import open_index, photo_by_id, search_photos, update_photo_fields
from picasapy.ini import load_or_empty, with_backuphash
from picasapy.ini.text_overlay import parse_text
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

from . import formatting
from .ini_ujraprobalas import update_document_ujraprobalva
from .photo_ops_compat import _WRITE_ERRORS, update_document


from .photo_ops_write_core_mixin import PhotoOpsWriteCoreMixin as _PhotoOpsWriteCoreMixin
from .photo_ops_write_text_mixin import PhotoOpsWriteTextMixin as _PhotoOpsWriteTextMixin


class PhotoOpsWriteMixin(_PhotoOpsWriteCoreMixin, _PhotoOpsWriteTextMixin):
    _photoFieldUpdated = Signal("qint64", object, object)
    _photoWriteAborted = Signal(object)
    photoOpFailed = Signal(str)
    textLayerClipboardChanged = Signal()
    captionPasteConfirmationRequested = Signal()
    @Slot(int, result=str)
    def hoverPreviewFileUrlAt(self, row: int) -> str:  # noqa: N802 — QML-hívás
        """A rács egy sorának eredeti képe, URL-kódolva az előnézeti ablaknak."""
        path = self._photos.filePathAt(row)
        return formatting.to_file_url(path).toString()
    # #459: sérült/betölthetetlen kép(ek) — a QML ebből építi az eredeti
    # Picasa szövege szerinti elrejtés-felajánlást ("...Would you like to
    # hide the files on disk?"). Elemek: {"id": int, "name": str}.
    brokenPhotosDetected = Signal(list)

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

    @Slot("qint64", object, object)
    def _on_photo_field_updated(self, photo_id: int, record, after=None) -> None:
        if record is not None:
            # A provider regiszterét a modell értesítése ELŐTT frissítjük.
            # Az update_photo revisionChanged/dataChanged jele azonnal
            # újraértékelheti a QML Image.source kötését, amely rögtön az új
            # URL-lel kér képet. Ha a provider csak utána kapja meg a
            # forgatott rekordot, ezt az első kérést még a régi rekordból
            # rendereli, a Qt URL-cache pedig később is azt tartja meg.
            frissitett = tuple(
                record if photo.id == photo_id else photo
                for photo in self._photos.photos
            )
            self._provider.register_photos(frissitett)
            self._photos.update_photo(photo_id, record)
        # #1443: az utómunka a sor frissítése után fut. `record is None`
        # esetén is lefut: ha a kép eltűnt az indexből, a nézetnek pláne
        # frissülnie kell. #3830 esetén az utómunka a következő forgatást
        # indíthatja, a modell így csak a lánc végső értékét kapja meg.
        if after is not None:
            after()

    @Slot(object)
    def _on_photo_write_aborted(self, on_error) -> None:
        on_error()

    @Slot(str)
    def _on_photo_write_failed(self, message: str) -> None:
        # meglévő hibajelzési minta (#86/#150): ugyanaz a csatorna, mint a
        # háttér-szinkron hibáié
        self.syncFailed.emit(message)

    #: #1443: azok a nézetmódok, amelyek TAGSÁGA a csillag-mezőtől függ.
    #: Ha itt állunk, a csillag ki/be kapcsolása nem egy sor megjelenését
    #: változtatja, hanem a lista TARTALMÁT — a nézetet újra le kell
    #: kérdezni. A mappa-nézetben ellenben a sornak maradnia kell.
    _CSILLAG_SZURT_NEZETEK = ("starred", "starred_album")

    #: #1515: azok a nézetmódok, amelyek TAGSÁGÁT a keresés dönti el. A
    #: `search-folder` (#45: keresés közben mappára kattintva) is ide
    #: tartozik: a rács ott a találatok egy mappára szűkített része, tehát
    #: a kiesés ott is kiesés.
    _KERESES_SZURT_NEZETEK = ("search", "search-folder")

    @Slot(int)
    def toggleStar(self, row: int) -> None:
        """Csillag be/ki — a .picasa.ini-be írva (kétirányú kompatibilitás:
        a párhuzamosan futó eredeti Picasa is látja). Levételkor a kulcs
        törlődik, ahogy a Picasa csinálja.

        #1443: csillag-szűrt nézetben (Csillagozottak) a művelet a lista
        TARTALMÁT változtatja, ezért utómunkaként újralekérdezzük a nézetet
        — a kötegelt út (`toggleStarMany` → `_apply_batch`) ezt már eddig is
        megtette."""
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
                return document.with_removed_preserving_section(
                    photo.name, "star"
                )

            update_document(ini_path, mutate, backup=True)
            return {"star": int(new_star)}

        def after() -> None:
            # A közvetlenül megnyitott gyorsnézeti kép nincs az SQLite
            # indexben, ezért a `photo_by_id` nem ad új rekordot. Az ini-írás
            # után a néző élő rekordját is frissíteni kell, különben a következő
            # kattintás ugyanabból a régi csillagállapotból indulna.
            row_now = self._photos.row_of_id(photo.id)
            if row_now >= 0:
                current = self._photos.photos[row_now]
                if current.star != new_star:
                    updated = replace(current, star=new_star)
                    records = tuple(
                        updated if existing.id == photo.id else existing
                        for existing in self._photos.photos
                    )
                    self._provider.register_photos(records)
                    self._photos.update_photo(photo.id, updated)
            self._refresh_if_star_filtered()

        self._run_photo_write(
            photo.id, perform, after=after
        )

    @Slot(list, result=bool)
    def hasTextLayerInSelection(self, rows) -> bool:  # noqa: N802
        """A kijelölés első képén van-e nem üres Text eszközös réteg."""
        photos = self._rows_to_photos(rows or ())
        return bool(photos and self._text_layer_value(photos[0]) is not None)

    @Property(bool, notify=textLayerClipboardChanged)
    def hasTextLayerClipboard(self) -> bool:  # noqa: N802
        """Van-e a Text eszköz rétegpuffere a `Paste Text` számára."""
        self._ensure_text_layer_clipboard()
        return self._text_layer_clipboard_value is not None

    @Slot(list, result=bool)
    def copyTextLayer(self, rows) -> bool:  # noqa: N802
        """A kijelölés első képének Text eszközös rétegét másolja.

        A `.picasa.ini` `text=` értéke a képhez írt szövegréteg, nem a kép
        felirata. A felirat-vágólap (#1526) másik adatot kezel.
        """
        self._ensure_text_layer_clipboard()
        photos = self._rows_to_photos(rows or ())
        if not photos:
            return False
        value = self._text_layer_value(photos[0])
        if value is None:
            return False
        self._text_layer_clipboard_value = value
        self.textLayerClipboardChanged.emit()
        return True

    @Slot(list)
    def pasteTextLayer(self, rows) -> None:  # noqa: N802
        """A Text eszközös réteget a kijelölt képekre írja.

        A Text eszköz által az aktuális képre mentett réteg a Picasa belső
        szövegpuffere is lehet (#5881, `this+0xcc8`), ezért ha még nem futott
        le külön Copy Text, a kijelölés első rétege adja a beilleszthető
        tartalmat. Így a mért job-287 állapotban a Paste Text is elérhető.
        """
        self._ensure_text_layer_clipboard()
        photos = [
            photo for photo in self._rows_to_photos(rows or ())
            if photo.kind != "video"
        ]
        if not photos:
            return
        value = self._text_layer_clipboard_value
        if value is None:
            value = self._text_layer_value(photos[0])
            if value is None:
                return
            self._text_layer_clipboard_value = value
            self.textLayerClipboardChanged.emit()

        def mutate(document, photo):
            document = document.with_value(photo.name, "text", value)
            document = document.with_value(photo.name, "textactive", "1")
            return with_backuphash(document, photo.name)

        self._apply_batch(photos, mutate)

    @Slot(result=int)
    def confirmCaptionPaste(self) -> int:  # noqa: N802
        """A felhasználó jóváhagyta a függő felirat-beillesztést."""
        pending = getattr(self, "_caption_paste_pending", None)
        self._caption_paste_pending = None
        if pending is None:
            return 0
        photo_ids, szoveg = pending
        photos_by_id = {photo.id: photo for photo in self._photos.photos}
        kijeloles = [
            photos_by_id[photo_id]
            for photo_id in photo_ids
            if photo_id in photos_by_id
        ]
        return self._write_caption_text(kijeloles, szoveg)

    @Slot()
    def cancelCaptionPaste(self) -> None:  # noqa: N802
        """A felhasználó elutasította a függő felirat-beillesztést."""
        self._caption_paste_pending = None

    @Slot(int, str)
    def setCaption(self, row: int, text: str) -> None:
        """Felirat mentése — Picasa írási szabály (spec #3): JPEG-nél az
        IPTC-be (a képfájlba) írjuk, minden más formátumnál a .picasa.ini-be,
        ahogy a csillag/forgatás is. Az IPTC-írás sikertelensége esetén
        (pl. sérült fájl) defenzíven az ini-útra esünk vissza.

        #1515: a felirat FTS-mező, tehát keresési nézetben a művelet a lista
        TARTALMÁT is változtathatja — az utómunka ezért megnézi, találat
        maradt-e a kép, és csak kiesésnél kérdezi újra a nézetet."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return
        photo = photos[row]
        photo_id, perform = self._felirat_iras(photo, text)
        self._run_photo_write(
            photo_id,
            perform,
            after=lambda: self._refresh_if_dropped_from_search(photo_id),
        )
