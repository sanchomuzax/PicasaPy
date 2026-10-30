"""A fotóíró mixin felirat- és szövegréteg-segédjei."""

from __future__ import annotations

from pathlib import Path

from picasapy.index import open_index
from picasapy.ini import load_or_empty, with_backuphash
from picasapy.ini.text_overlay import parse_text
from picasapy.metadata import write_iptc_caption
from picasapy.scanner import PICASA_INI_NAME

from .ini_ujraprobalas import update_document_ujraprobalva
from .photo_ops_compat import update_document


class PhotoOpsWriteTextMixin:

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
