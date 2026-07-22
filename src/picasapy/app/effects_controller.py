"""Effektlánc másolás/beillesztés (#152) — a Kép menü „Copy/Paste All
Effects" pontjainak bekötése: az `EditSession.copy_effects()`/
`paste_effects()` API-t emeli QML-slotokká, több kijelölt képre.

Mixin-osztály: az `AppController` örökli, a `PhotoOpsMixin` batch-ini-írás
mintáját (`_apply_batch`-hez hasonló, mappánkénti egyetlen írás) követve."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.session import EditSession
from picasapy.index import open_index
from picasapy.ini import update_document
from picasapy.ini.rect64 import encode_rect64
from picasapy.scanner import PICASA_INI_NAME


class EffectsClipboardMixin:
    """„Vágólap"-pillanatkép egy kép effektláncáról + beillesztés, undóval."""

    effectsClipboardChanged = Signal()

    def _ensure_effects_clipboard(self) -> None:
        """Lusta állapot-inicializálás (#150-minta: nem kell az __init__-et
        (forró fájl) módosítani a szelet bevezetéséhez)."""
        if not hasattr(self, "_effects_clipboard"):
            self._effects_clipboard: EditSession | None = None
            # verem: minden elem egy beillesztés-köteg — (mappa, fájlnév,
            # ELŐZŐ nyers filters=, ELŐZŐ nyers crop=) négyesek listája
            self._effects_undo_stack: list[
                list[tuple[str, str, str | None, str | None]]
            ] = []

    @Property(bool, notify=effectsClipboardChanged)
    def hasEffectsClipboard(self) -> bool:
        """Van-e másolt effektlánc — a „Paste All Effects" menüpont
        engedélyezési feltétele."""
        self._ensure_effects_clipboard()
        return self._effects_clipboard is not None

    @Property(bool, notify=effectsClipboardChanged)
    def canUndoPasteEffects(self) -> bool:
        self._ensure_effects_clipboard()
        return bool(self._effects_undo_stack)

    @Slot(list)
    def copyEffects(self, rows) -> None:
        """A kijelölés ELSŐ képének teljes effektlánca a „vágólapra" (#152,
        Picasa „Copy All Effects"): a crop64 és minden ismeretlen/idegen
        bejegyzés is átkerül, string-kerülő úton (bitre pontos round-trip)."""
        self._ensure_effects_clipboard()
        photos = self._photos.photos
        valid_rows = [int(r) for r in rows if 0 <= int(r) < len(photos)]
        if not valid_rows:
            return
        photo = photos[valid_rows[0]]
        source = EditSession.from_value(photo.filters or "")
        self._effects_clipboard = EditSession(ops=source.copy_effects())
        self.effectsClipboardChanged.emit()

    @Slot(list)
    def pasteEffects(self, rows) -> None:
        """A vágólap láncának beillesztése a kijelölt kép(ek)re (#152,
        Picasa „Paste All Effects"): minden cél TELJES lánca lecserélődik
        (nem rétegez rá), a `crop=` tükör-kulcs is követi a crop64-et.

        Mappánként egyetlen ini-írás + resync (a `PhotoOpsMixin._apply_batch`
        mintája); a beillesztés előtti állapot undo-veremre kerül."""
        self._ensure_effects_clipboard()
        if self._effects_clipboard is None:
            return
        photos = self._photos.photos
        valid = [photos[int(r)] for r in rows if 0 <= int(r) < len(photos)]
        if not valid:
            return
        pasted_ops = self._effects_clipboard.ops
        undo_batch: list[tuple[str, str, str | None, str | None]] = []
        by_folder: dict[str, list] = {}
        for photo in valid:
            by_folder.setdefault(photo.folder_path, []).append(photo)
        with open_index(self._db_path) as conn:
            for folder, folder_photos in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME
                # #137: ütközésbiztos mentés. A beillesztés ELŐTTI (nyers)
                # értékeket a mutate-en belül olvassuk ki, hogy ütközéskori
                # újrajátszásnál a FRISS (más író általi) alapállapotot
                # tükrözzék; az `entries` listát minden hívás felülírja
                # (nem hozzáfűzi), így az újrajátszás nem duplikál.
                entries: list[tuple[str, str, str | None, str | None]] = []

                def mutate(document, folder=folder, folder_photos=folder_photos):
                    fresh: list[tuple[str, str, str | None, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        fresh.append((
                            folder,
                            photo.name,
                            section.get("filters") if section else None,
                            section.get("crop") if section else None,
                        ))
                        document = _write_session(
                            document, photo.name, EditSession(ops=pasted_ops)
                        )
                    entries[:] = fresh
                    return document

                update_document(ini_path, mutate, backup=True)
                undo_batch.extend(entries)
                self._sync_tree(conn, folder)
        self._effects_undo_stack.append(undo_batch)
        self.effectsClipboardChanged.emit()
        self._refresh_view()

    @Slot()
    def undoPasteEffects(self) -> None:
        """Az utolsó „Paste All Effects" visszavonása — minden érintett kép
        filters=/crop= kulcsa visszaáll a beillesztés előtti (nyers) értékre."""
        self._ensure_effects_clipboard()
        if not self._effects_undo_stack:
            return
        batch = self._effects_undo_stack.pop()
        by_folder: dict[str, list[tuple[str, str | None, str | None]]] = {}
        for folder, name, prev_filters, prev_crop in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters, prev_crop))
        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for name, prev_filters, prev_crop in entries:
                        document = (
                            document.with_value(name, "filters", prev_filters)
                            if prev_filters is not None
                            else document.with_removed(name, "filters")
                        )
                        document = (
                            document.with_value(name, "crop", prev_crop)
                            if prev_crop is not None
                            else document.with_removed(name, "crop")
                        )
                    return document

                update_document(ini_path, mutate, backup=True)  # #137
                self._sync_tree(conn, folder)
        self.effectsClipboardChanged.emit()
        self._refresh_view()


def _write_session(document, section_name: str, session: EditSession):
    """A `session` filters=/crop= kulcsainak beírása (a `EditController._save`
    mintájával megegyezően, hogy a két bekötés ne térjen el egymástól)."""
    if session.is_empty():
        document = document.with_removed(section_name, "filters")
    else:
        document = document.with_value(section_name, "filters", session.to_value())
    crop = session.crop()
    if crop is not None:
        document = document.with_value(
            section_name, "crop", f"rect64({encode_rect64(crop)})"
        )
    else:
        document = document.with_removed(section_name, "crop")
    return document
