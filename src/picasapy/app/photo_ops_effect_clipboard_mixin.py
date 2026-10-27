"""A teljes effektlánc másolásának, beillesztésének és visszavonásának mixinje."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.effect_clipboard import (
    copy_all_effects,
    crop_mirror_value,
    paste_all_effects,
)
from picasapy.index import open_index
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_compat import _WRITE_ERRORS, update_document


class PhotoOpsEffectClipboardMixin:
    allEffectsClipboardChanged = Signal()
    def _ensure_effect_clipboard(self) -> None:
        """Lusta állapot-inicializálás (#150-minta: nem kell az __init__-et
        (forró fájl) módosítani a szelet bevezetéséhez). Szándékosan KÜLÖN
        állapot a `effects_controller.EffectsClipboardMixin`-től (#152) — a
        modul docstringje indokolja, miért két önálló funkció."""
        if not hasattr(self, "_effect_clipboard_value"):
            self._effect_clipboard_value: str | None = None
            # egyetlen visszavonási lépés (#426 elfogadási kritérium): az
            # utolsó beillesztés ELŐTTI (mappa, fájlnév, nyers filters=,
            # nyers crop=) NÉGYESEINEK listája; None = nincs (törölve/le nem
            # futott). #1544: a `crop=` tükör-kulcs is a négyesbe került —
            # enélkül a visszavonás a régi láncot adná vissza az ÚJ vágással
            # (ugyanaz a hiba, amit a #465 a köteges úton javított).
            self._effect_clipboard_undo: (
                list[tuple[str, str, str | None, str | None]] | None
            ) = None

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
        """„Az összes effektus másolása": a kijelölés ELSŐ képének TELJES
        `filters=` lánca kerül az alkalmazás-szintű vágólapra — a vágással
        (`crop64`) és a régió-adatokkal (`redeye`/`retouch`) együtt, ahogy az
        eredeti Picasa másolója teszi (#1544; a szűrés a `mode="history"`
        oszlopból következtetett, téves szabály volt, ld.
        `picasapy.edit.effect_clipboard`). Tiszta lekérdezés — nem ír semmit."""
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
        nyers `filters=` és `crop=` értékek egyetlen undo-lépésként kerülnek
        a verembe, hogy a teljes köteg egy `undoPasteAllEffects()` hívással
        visszavonható legyen. Nincs háttérszál — az ini-írás gyors (nincs
        képfeldolgozás), a `_apply_batch`/`EffectsClipboardMixin.
        pasteEffects` szinkron mintáját követi.

        #1544: a lánccal EGYÜTT jár a `crop=rect64(...)` tükör-kulcs is (az
        `edit_controller._save()`/`effects_controller._write_session()`
        szabálya szerint). A `filters=`-beli `crop64` az EREDETI Picasában
        önmagában nem vág — a renderelést a `crop=` hajtja —, ezért e nélkül
        ugyanaz a NAS-mappa a windowsos Picasában vágatlan képet mutatna.
        Vágás nélküli lánc beillesztésekor a célkép meglévő `crop=` kulcsa
        TÖRLŐDIK: `crop64` nélküli `crop=` az éles korpuszban nulla esetben
        fordul elő (761-ből).

        ⚠️ **Más méretarányú célkép.** A `crop64` rect64-koordinátái
        relatívak ([0..1]), ezért a vágás a más alakú célképre is érvényes
        marad — arányosan ugyanazt a részt jelöli ki, sosem lóg ki a képből,
        és nem hibázik. A KOMPOZÍCIÓ más lesz (mérve: ugyanaz a rect 800×600
        képen 364×523, 600×800-on 273×697 kivágást ad), adat viszont nem
        vész el: az eredeti JPEG érintetlen, a `.picasa.ini` nem destruktív,
        és a művelet visszavonható. Az eredeti Picasa beillesztője sem tesz
        célkép-méret szerinti kivételt."""
        self._ensure_effect_clipboard()
        if self._effect_clipboard_value is None:
            return
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        clipboard_value = self._effect_clipboard_value
        new_value = paste_all_effects(clipboard_value)
        # #1544: a lánccal együtt járó `crop=` tükör-kulcs — minden célképre
        # ugyanaz, ezért egyszer számoljuk ki.
        new_crop = crop_mirror_value(new_value)

        by_folder: dict[str, list] = {}
        for photo in valid:
            by_folder.setdefault(photo.folder_path, []).append(photo)

        undo_batch: list[tuple[str, str, str | None, str | None]] = []
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None, str | None]] = []

                # B023: az `entries` alapértelmezett argumentumként kötve —
                # a mutate szinkron fut, mielőtt a következő iteráció
                # újrakötné (az `effects_controller.pasteEffects` mintája).
                def mutate(
                    document, folder=folder, folder_photos=folder_photos, entries=entries
                ):
                    fresh: list[tuple[str, str, str | None, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        prev_crop = section.get("crop") if section else None
                        fresh.append((folder, photo.name, prev, prev_crop))
                        if new_value:
                            # #643: a vágólapról ÁTVITT lánc — az idegen tag
                            # nem most keletkezik, ezért nem utasítjuk vissza.
                            document = document.with_value(
                                photo.name, "filters", new_value, carried=True
                            )
                        else:
                            document = document.with_removed(photo.name, "filters")
                        if new_crop is not None:
                            document = document.with_value(
                                photo.name, "crop", new_crop
                            )
                        else:
                            document = document.with_removed(photo.name, "crop")
                    entries[:] = fresh
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                undo_batch.extend(entries)
                # #750: a beillesztett lánc a TARTÓS naplóba is — mappánként
                # EGY naplóírással, hogy a köteget ne lassítsa. Üres
                # `new_value`-nál a bejegyzés törlődik, ahogy a `filters=`
                # kulcs is (ld. a mutate két ágát).
                self.recordSavedChains(
                    [
                        (str(Path(folder) / photo.name), new_value)
                        for photo in folder_photos
                    ]
                )
                self._sync_tree(conn, folder)

        self._effect_clipboard_undo = undo_batch
        self.allEffectsClipboardChanged.emit()
        self._refresh_view()

    @Slot()
    def undoPasteAllEffects(self) -> None:
        """Az utolsó „Az összes effektus beillesztése" visszavonása — minden
        érintett kép `filters=` ÉS `crop=` kulcsa visszaáll a beillesztés
        előtti (nyers) értékre (#426 elfogadási kritérium: egyetlen
        visszavonási lépés).

        #1544: a `crop=` azért van itt, mert a beillesztés is írja. Enélkül a
        visszavonás a RÉGI láncot adná vissza az ÚJ vágással — a célkép a
        windowsos Picasában olyan rect szerint vágódna, aminek a láncában
        nincs párja."""
        self._ensure_effect_clipboard()
        if not self._effect_clipboard_undo:
            return
        batch = self._effect_clipboard_undo
        self._effect_clipboard_undo = None

        by_folder: dict[str, list[tuple[str, str | None, str | None]]] = {}
        for folder, name, prev_filters, prev_crop in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters, prev_crop))

        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for name, prev_filters, prev_crop in entries:
                        if prev_filters is not None:
                            document = document.with_value(
                                name, "filters", prev_filters, carried=True  # #643
                            )
                        else:
                            document = document.with_removed(name, "filters")
                        if prev_crop is not None:
                            document = document.with_value(name, "crop", prev_crop)
                        else:
                            document = document.with_removed(name, "crop")
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                # #750: a visszavonás is a MI írásunk — a napló a beillesztés
                # ELŐTTI láncot védi tovább (üresnél törlődik a bejegyzés).
                self.recordSavedChains(
                    [
                        (str(Path(folder) / name), prev_filters or "")
                        for name, prev_filters, _prev_crop in entries
                    ]
                )
                self._sync_tree(conn, folder)

        self.allEffectsClipboardChanged.emit()
        self._refresh_view()
