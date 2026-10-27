"""A fotómezők, feliratok, vágólapok és közös írási út témamixinje."""

from __future__ import annotations

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


class PhotoOpsWriteMixin:
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
        self._photoWriteAborted.connect(self._on_photo_write_aborted)
        #: #3830: az egyképes forgatás (`rotateRight`/`rotateLeft`) FUTÓ
        #: írásainak és a rájuk közben érkezett újabb célértékeknek a
        #: nyilvántartása — ld. `_apply_rotate`.
        self._rotate_running: set[int] = set()
        self._rotate_target: dict[int, int] = {}

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

    def jelentsdAzIrasiHibat(self, error: BaseException | str) -> None:
        """Ini-írási hiba a LÁTHATÓ csatornán (#2506).

        ⚠️ A `photoOpFailed` önmagában NEM elég: a `syncFailed`-re (és így a
        `Main.qml` `errorBanner`-ére, #459) csak az
        `_ensure_photo_ops_wired()` köti rá, azt viszont eddig kizárólag a
        FOTÓ-írás útja hívta (`_run_photo_write`). Ha a felhasználó első
        művelete egy mappa-leírás, egy mappa-dátum vagy egy címke volt, a
        jelzés bekötetlen csatornára ment: a hiba jelezve volt, és mégsem
        látszott semmi. Ezért köt be ez a segéd, mielőtt emittál.
        """
        self._ensure_photo_ops_wired()
        self.photoOpFailed.emit(str(error))

    @Slot(str)
    def _on_photo_write_failed(self, message: str) -> None:
        # meglévő hibajelzési minta (#86/#150): ugyanaz a csatorna, mint a
        # háttér-szinkron hibáié
        self.syncFailed.emit(message)

    def _run_photo_write(
        self, photo_id: int, perform, after=None, on_error=None
    ) -> None:
        """Ini/IPTC-írás (NAS: backup+temp+fsync) + célzott index-UPDATE
        háttérszálon (#141). A `perform()` a teljes lassú munkát végzi (fájl-
        írás + a {oszlop: érték} dict összeállítása), és teljes egészében a
        munkásszálon fut. #505: a busy-jelzést a `_start_background`
        (`worker_thread.py`) intézi, nem itt.

        `after`: opcionális utómunka (#1443), amit a GUI-szálon, a rács-sor
        frissítése után hívunk. Írási hiba esetén NEM fut le — olyankor a
        nézet tartalma sem változott. A forgatás utómunkája a következő
        célértéket új háttérmunkában írja ki.
        `on_error`: opcionális hiba-utómunka (#3830) a GUI-szálon — a
        várt írási hibánál (`_WRITE_ERRORS`) ÉS nem várt kivételnél is
        lefut, hogy a hívó eldobhassa a függő állapotát."""
        self._ensure_photo_ops_wired()

        def hiba_utomunka() -> None:
            if on_error is not None:
                self._photoWriteAborted.emit(on_error)

        def worker() -> None:
            try:
                fields = perform()
                with open_index(self._db_path) as conn:
                    if fields:
                        update_photo_fields(conn, photo_id, **fields)
                    record = photo_by_id(conn, photo_id)
            except _WRITE_ERRORS as error:
                hiba_utomunka()
                self.photoOpFailed.emit(str(error))
                return
            except BaseException:
                hiba_utomunka()
                raise
            self._photoFieldUpdated.emit(photo_id, record, after)

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-photowrite")

    def _run_photo_writes(self, jobs, after=None, on_error=None) -> None:
        """Több kép írása SOROSAN, EGYETLEN háttérszálon (#2915).

        Képenként külön szálat indítani versenyhelyzet: a kijelölés képei
        jellemzően EGY mappában vannak, tehát ugyanabba a `.picasa.ini`-be
        és ugyanabba az indexbe írnak. A windowsos CI ki is mutatta: a
        kijelölés egy része felirat nélkül maradt. A soros út mellékesen a
        NAS-t is kíméli (N párhuzamos backup+temp+fsync helyett egy), és a
        `_apply_batch`-hez hasonlóan EGY index-kapcsolatot használ.

        `jobs`: `(photo_id, perform)` párok; a `perform()` a teljes lassú
        munka, ugyanúgy, mint a `_run_photo_write`-nál. Az `after` utómunka
        a GUI-szálon, a KÖTEG végén fut le egyszer. Az `on_error` lezáró
        visszahívás bármilyen workerhiba esetén lefut.
        """
        self._ensure_photo_ops_wired()
        jobs = tuple(jobs)
        if not jobs:
            return

        def worker() -> None:
            try:
                with open_index(self._db_path) as conn:
                    for index, (photo_id, perform) in enumerate(jobs):
                        fields = perform()
                        if fields:
                            update_photo_fields(conn, photo_id, **fields)
                        record = photo_by_id(conn, photo_id)
                        utolso = index == len(jobs) - 1
                        self._photoFieldUpdated.emit(
                            photo_id, record, after if utolso else None
                        )
            except _WRITE_ERRORS as error:
                self.photoOpFailed.emit(str(error))
                if on_error is not None:
                    on_error()
            except BaseException:
                if on_error is not None:
                    on_error()
                raise

        self._start_background(worker, name="picasapy-photowrite-koteg")

    #: #1443: azok a nézetmódok, amelyek TAGSÁGA a csillag-mezőtől függ.
    #: Ha itt állunk, a csillag ki/be kapcsolása nem egy sor megjelenését
    #: változtatja, hanem a lista TARTALMÁT — a nézetet újra le kell
    #: kérdezni. A mappa-nézetben ellenben a sornak maradnia kell.
    _CSILLAG_SZURT_NEZETEK = ("starred", "starred_album")

    def _refresh_if_star_filtered(self) -> None:
        """Újralekérdezés, ha a csillag a jelen nézet tagságát dönti el.

        Szándékosan lekérdezés (`_refresh_view`) és nem sor-eltávolítás: így
        a visszacsillagozás is magától bekerül, és a zöld eredménysáv
        darabszáma is követ."""
        if self._view_mode[0] in self._CSILLAG_SZURT_NEZETEK:
            self._refresh_view()

    #: #1515: azok a nézetmódok, amelyek TAGSÁGÁT a keresés dönti el. A
    #: `search-folder` (#45: keresés közben mappára kattintva) is ide
    #: tartozik: a rács ott a találatok egy mappára szűkített része, tehát
    #: a kiesés ott is kiesés.
    _KERESES_SZURT_NEZETEK = ("search", "search-folder")

    def _refresh_if_dropped_from_search(self, photo_id: int) -> None:
        """Újralekérdezés, ha a kép KIESETT az aktuális keresés találatai
        közül (#1515) — pl. mert töröltük a feliratot, ami miatt találat volt.

        **Miért nem kérdezzük újra mindig?** Mérve, valósághű indexen
        (140 755 kép / 3 000 mappa, a felhasználó gyűjteményének mérete):
        a teljes `search_photos` medián **597 ms** egy 27 179 találatos
        kulcsszónál, míg az EGY KÉPRE szűkített, ugyanazon a kódúton futó
        tagság-lekérdezés **6–11 ms**. A költséget a találatszám (a
        rekordépítés) viszi, nem az SQL, ezért a feliratmentésenkénti teljes
        újralekérdezés a felhasználó gyűjteményén fél másodperces
        akadásokat okozna. Összehasonlításul a #1443 csillag-nézete
        162 ms — az volt még kifizethető, ez már nem.

        **Bekerülést nem kell vizsgálni:** a szerkesztett kép a művelet
        pillanatában LÁTSZIK a rácson (a `setCaption` sorszámot kap a
        `self._photos` listájából), tehát biztosan találat VOLT. Csak az a
        kérdés maradt, találat-e még.

        Szándékosan `_refresh_view()` és nem sor-eltávolítás: így a bal
        hasáb „Search results for … (N)" darabszáma és a találatos mappák
        listája is követ, és a visszaadott felirat magától visszahozza a
        képet."""
        mode, param = self._view_mode
        if mode not in self._KERESES_SZURT_NEZETEK:
            return
        query = param if mode == "search" else param[0]
        with open_index(self._db_path) as conn:
            if search_photos(conn, query, only_id=photo_id):
                return  # találat maradt — a sor frissítése elég volt
        self._refresh_view()

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

    # -- Szöveg-vágólap: a FELIRATRA hat, nem a fájlra (#1526) -------------
    #
    # #5877: a menü Text eszköz réteget másol; a külön képfelirat-vágólap
    # Python oldali segédjei ettől elkülönülnek.
    #
    # ⚠️ Fej nélküli környezetben (`offscreen`/`minimal`) NEM nyúlunk a
    # rendszervágólaphoz: nincs mögötte vágólap-tulajdonos, és a Qt-hívás a
    # CI-n SZEGMENSHIBÁVAL állította meg a tesztfájlt (`exit -11`) — nem
    # kivétellel, amit el lehetne kapni (ld. `fileops_controller`
    # `_tegyd_a_vagolapra`). Ilyenkor egy munkamenet-szintű szövegtár áll a
    # helyén, tehát a művelet nem lesz néma, és a próbák AZT mérik, amit
    # feltennénk.

    def _ensure_caption_clipboard(self) -> None:
        """A külön felirat-segéd tartalék tárát inicializálja fej nélküli futáshoz."""
        if not hasattr(self, "_caption_clipboard"):
            self._caption_clipboard = ""

    #: ⚠️ SZÁNDÉKOSAN nem `@Slot`: ez a külön képfelirat-vágólap Python-API-ja;
    #: a Szerkesztés menü a Text eszköz réteget kezeli (#5877).
    def setCaptionClipboardText(self, text: str) -> None:  # noqa: N802
        """A szöveg-vágólap FELTÖLTÉSE."""
        from PySide6.QtGui import QGuiApplication

        self._ensure_caption_clipboard()
        self._caption_clipboard = str(text or "")
        if QGuiApplication.platformName() in ("offscreen", "minimal"):
            return
        vagolap = QGuiApplication.clipboard()
        if vagolap is not None:
            vagolap.setText(self._caption_clipboard)

    def captionClipboardText(self) -> str:  # noqa: N802
        """A szöveg-vágólap tartalma. Fej nélküli környezetben a
        munkamenet-szintű tár, egyébként a rendszervágólap.

        (Szintén nem `@Slot` — ld. a `setCaptionClipboardText` fölötti okot.)"""
        from PySide6.QtGui import QGuiApplication

        self._ensure_caption_clipboard()
        if QGuiApplication.platformName() in ("offscreen", "minimal"):
            return getattr(self, "_caption_clipboard", "")
        vagolap = QGuiApplication.clipboard()
        return "" if vagolap is None else vagolap.text()

    def copyCaptionText(self, row: int) -> bool:  # noqa: N802
        """Python oldali segéd a kép feliratának vágólapra másolásához.

        A `Copy Text` menütétel külön a Text eszköz rétegét kezeli (#5877).

        `False`, ha nincs mit másolni: érvénytelen sor, vagy a képnek nincs
        felirata. Üres szöveget feltenni annyi lenne, mint kiürítni a
        vágólapot — azt a felhasználó nem kérte."""
        photos = self._photos.photos
        if not 0 <= int(row) < len(photos):
            return False
        felirat = (self._photos.captionAt(int(row)) or "").strip()
        if not felirat:
            return False
        self.setCaptionClipboardText(felirat)
        return True

    def pasteCaptionText(self, rows) -> int:  # noqa: N802
        """Python oldali segéd a vágólap feliratként való beillesztéséhez.

        Nem a Szerkesztés menü `Paste Text` parancsa (#5877). Visszaadja,
        hány képre indult írás. Ha a kijelölésben van már feliratozott kép,
        a QML megerősítést kér; az írás csak a `confirmCaptionPaste`
        hívásakor indul.

        ⚠️ ÜRES vágólapra nem tesz semmit: a meglévő feliratok letörlése néma
        adatvesztés lenne — a törlésre a felirat-szerkesztő van."""
        szoveg = self.captionClipboardText().strip()
        if not szoveg:
            return 0
        photos = self._photos.photos
        kijeloles = []
        for row in rows:
            try:
                sor = int(row)
            except (TypeError, ValueError):
                continue
            if 0 <= sor < len(photos):
                kijeloles.append(photos[sor])
        if not kijeloles:
            return 0

        # #4628: a kérdésre várva rögzítjük a célképeket és a szöveget. Így
        # egy másik vágólap- vagy rácsváltozás nem módosítja a felhasználó
        # által épp jóváhagyott műveletet.
        if getattr(self, "_caption_paste_pending", None) is not None:
            return 0
        if any((photo.caption or "").strip() for photo in kijeloles):
            self._caption_paste_pending = (
                [photo.id for photo in kijeloles],
                szoveg,
            )
            self.captionPasteConfirmationRequested.emit()
            return 0

        return self._write_caption_text(kijeloles, szoveg)

    def _write_caption_text(self, kijeloles, szoveg: str) -> int:
        """A már jóváhagyott vagy üres képekre menő feliratköteg."""
        if not kijeloles or not szoveg:
            return 0
        # #2915: EGY soros köteg, nem képenként egy szál — ugyanabba az
        # ini-be és indexbe írás párhuzamosan versenyhelyzet volt.
        azonositok = [photo.id for photo in kijeloles]

        def utomunka() -> None:
            for photo_id in azonositok:
                self._refresh_if_dropped_from_search(photo_id)

        self._run_photo_writes(
            [self._felirat_iras(photo, szoveg) for photo in kijeloles],
            after=utomunka,
        )
        return len(kijeloles)

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

    def _felirat_iras(self, photo, text: str):
        """Egy kép felirat-írása `(photo_id, perform)` párként (#2915).

        A `perform()` a teljes lassú munka (IPTC- vagy ini-írás); így
        ugyanaz a kód szolgálja az egy képre menő `setCaption`-t és a
        kijelölésre menő, SOROS köteget (`pasteCaptionText`)."""
        text = (text or "").strip()
        is_jpeg = photo.name.lower().endswith((".jpg", ".jpeg"))

        def perform() -> dict:
            if is_jpeg:
                path = Path(photo.folder_path) / photo.name
                if write_iptc_caption(path, text):
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
