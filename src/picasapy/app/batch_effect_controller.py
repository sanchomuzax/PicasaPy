"""„Csoportos szerkesztés ▸" — a Kép-menü kötegelt egykattintásos effektjei
(#425, `docs/specs/ui-audit-menus.md` K.1 szakasz).

Az `eMenuPicture` osztály K.1-ben dokumentált 9 képi művelete (automatikus
kontraszt/szín/vörösszem-eltávolítás, „Jó napom van", élesítés, filmszemcse,
melegítés, forgatás jobbra/balra) MIND a meglévő `EditSession`/`filters=`
motorra épül (ld. `picasapy.edit.session`) — ez a szelet csak a kijelölt N
képre való EGYSZERRE alkalmazást teszi hozzá, a `PhotoOpsMixin._apply_batch`/
`EffectsClipboardMixin.pasteEffects` mintáját követve (mappánként EGY
ütközésbiztos ini-írás), de HÁTTÉRSZÁLON és MEGSZAKÍTHATÓAN — nagy
kijelöléseknél (sok mappa, esetleg NAS) ez percekig tarthat (#425 4-5. pont).

A forgatás (jobbra/balra) NEM ide tartozik: az már kész és szinkron
(`PhotoOpsMixin.rotateRightMany`/`rotateLeftMany`) — a menü egyenesen azt
hívja, ez a modul a `filters=` láncot bővítő 7 effektet szolgálja ki.

Mixin-osztály: az `AppController` örökli, a `photo_ops_controller`
lusta-bekötés mintáját (#150) követve — nem kell az __init__-et (forró fájl)
módosítani.

A Szöveg megjelenítése/elrejtése (`ID_PICTURE_SHOW_TEXT`/`…HIDE_TEXT`) NEM
része ennek a szeletnek: az index nem tárolja, mely fotóknak van szöveg-
overlay-je (`text=`/`textactive=`, ld. `picasapy.ini.text_overlay`), így a
menüpont #425 5. pontban leírt feltételes engedélyezése (csak akkor aktív,
ha a kijelölésben van szövegréteges kép) jelen ismeretekkel nem
állapítható meg olcsón — a `PicasaMenuBar.qml`-ben egyelőre placeholder."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.session import EditSession
from picasapy.ini import update_document
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_controller import _WRITE_ERRORS

# A K.1 táblázat 7, `filters=` láncot bővítő tétele — a forgatás a meglévő
# rotateRightMany/rotateLeftMany úton fut, a Szöveg-tételek placeholderek.
# Az `EditSession` metódusa szerint csoportosítva:
_APPLY_NAMES = frozenset({"autolight", "autocolor", "enhance"})  # append-only
_TOGGLE_NAMES = frozenset({"redeye"})  # a meglévő egy-példányos kapcsoló
_APPEND_NAMES = frozenset({"unsharp", "grain2", "warm"})  # paraméter nélküli
_KNOWN_EFFECTS = _APPLY_NAMES | _TOGGLE_NAMES | _APPEND_NAMES


def _apply_one(session: EditSession, name: str) -> EditSession:
    """Egyetlen egykattintásos effekt alkalmazása a session láncára.

    A metódus-választás az `EditSession` már meglévő, szűk API-ját követi
    (nem vezet be új réteg-fajtát) — `apply()` az append-only egygombos
    javításokhoz, `toggle()` a redeye-hoz (az egyetlen létező toggle-effekt),
    `append_effect()` a paraméter nélküli effektekhez (unsharp alap-erőssége
    megegyezik a puszta `unsharp=1`-gyel, ld. `EditorPanel.qml` #315
    megjegyzése)."""
    if name in _APPLY_NAMES:
        return session.apply(name)
    if name in _TOGGLE_NAMES:
        return session.toggle(name)
    return session.append_effect(name)


def _write_filters(document, section_name: str, session: EditSession):
    """A `filters=` kulcs beírása/törlése (a `crop=` tükör-kulcs nélkül —
    ez a szelet sosem érinti a crop64-et)."""
    if session.is_empty():
        return document.with_removed(section_name, "filters")
    return document.with_value(section_name, "filters", session.to_value())


class BatchEffectMixin:
    """A Kép ▸ Csoportos szerkesztés almenü motorja (#425)."""

    # a lebegő haladás-panel állapota (az `ImportProgressPanel` mintája,
    # ld. `LibraryMixin.importChanged`/`importPanelVisible`)
    batchEditChanged = Signal()
    # egyetlen visszavonási lépés elérhetősége változott (#425 4. pont)
    canUndoBatchEditChanged = Signal()
    # worker szálból jövő, Qt által automatikusan a GUI-szálra sorolt jelzések
    _batchEditProgress = Signal(str, int, int)  # (mappa, kész, összes)
    _batchEditWorkDone = Signal()

    def _ensure_batch_edit(self) -> None:
        """Lusta állapot-inicializálás (#150-minta)."""
        if getattr(self, "_batch_edit_wired", False):
            return
        self._batch_edit_wired = True
        self._batch_edit_active = False
        self._batch_edit_folder = ""
        self._batch_edit_done = 0
        self._batch_edit_total = 0
        self._batch_edit_cancel = threading.Event()
        # az utolsó köteg visszavonási adatai: (mappa, fájlnév, ELŐZŐ nyers
        # filters=) hármasok listája; None = nincs (törölve/le nem futott)
        self._batch_edit_undo: list[tuple[str, str, str | None]] | None = None
        self._batchEditProgress.connect(self._on_batch_edit_progress)
        self._batchEditWorkDone.connect(self._on_batch_edit_work_done)

    @Property(bool, notify=batchEditChanged)
    def batchEditActive(self) -> bool:
        """Látszódjon-e a lebegő haladás-panel."""
        self._ensure_batch_edit()
        return self._batch_edit_active

    @Property(str, notify=batchEditChanged)
    def batchEditFolderName(self) -> str:
        self._ensure_batch_edit()
        return Path(self._batch_edit_folder).name if self._batch_edit_folder else ""

    @Property(int, notify=batchEditChanged)
    def batchEditDoneCount(self) -> int:
        self._ensure_batch_edit()
        return self._batch_edit_done

    @Property(int, notify=batchEditChanged)
    def batchEditTotalCount(self) -> int:
        self._ensure_batch_edit()
        return self._batch_edit_total

    @Property(bool, notify=canUndoBatchEditChanged)
    def canUndoBatchEdit(self) -> bool:
        """Van-e visszavonható köteg — a menüpont engedélyezési feltétele."""
        self._ensure_batch_edit()
        return self._batch_edit_undo is not None

    @Slot(list, str)
    def applyEffectMany(self, rows, effect_name: str) -> None:
        """A `effect_name` egykattintásos effekt alkalmazása a kijelölt
        képek MINDEGYIKÉRE (#425): mappánként EGY ütközésbiztos ini-írás,
        háttérszálon, mappánként frissülő haladásjelzéssel és
        megszakíthatósággal (`cancelBatchEdit`). A beillesztés előtti nyers
        `filters=` értékek egyetlen undo-lépésként kerülnek a verembe."""
        self._ensure_batch_edit()
        if effect_name not in _KNOWN_EFFECTS:
            return
        photos = self._rows_to_photos(rows)
        if not photos:
            return

        by_folder: dict[str, list] = {}
        for photo in photos:
            by_folder.setdefault(photo.folder_path, []).append(photo)

        self._batch_edit_cancel.clear()
        self._batch_edit_active = True
        self._batch_edit_done = 0
        self._batch_edit_total = len(by_folder)
        self._batch_edit_folder = next(iter(by_folder))
        self.batchEditChanged.emit()
        self._begin_sync_job()

        def worker() -> None:
            undo_batch: list[tuple[str, str, str | None]] = []
            done = 0
            for folder, folder_photos in by_folder.items():
                if self._batch_edit_cancel.is_set():
                    break
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None]] = []

                # B023-minta (`effects_controller.pasteEffects`): az
                # `entries` alapértelmezett argumentumként kötve, mert a
                # mutate szinkron fut a ciklus adott körén belül.
                def mutate(
                    document, folder=folder, folder_photos=folder_photos,
                    entries=entries,
                ):
                    fresh: list[tuple[str, str, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        fresh.append((folder, photo.name, prev))
                        session = _apply_one(EditSession.from_value(prev), effect_name)
                        document = _write_filters(document, photo.name, session)
                    entries[:] = fresh
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    break
                undo_batch.extend(entries)
                self._sync_tree_locked(folder)
                done += 1
                self._batchEditProgress.emit(folder, done, len(by_folder))
            self._batch_edit_undo = undo_batch if undo_batch else None
            self._batchEditWorkDone.emit()

        threading.Thread(target=worker, daemon=True).start()

    def _sync_tree_locked(self, folder: str) -> None:
        """A `folder` resync-je saját (a hívó szálán rövid életű)
        index-kapcsolattal — a köteg minden mappájának saját tranzakciója
        van, hogy egy megszakítás a már megírt mappákat konzisztensen
        hagyja (a `open_index` kontextuskezelő zárja/commitolja)."""
        from picasapy.index import open_index

        with open_index(self._db_path) as conn:
            self._sync_tree(conn, folder)

    @Slot(str, int, int)
    def _on_batch_edit_progress(self, folder: str, done: int, total: int) -> None:
        self._batch_edit_folder = folder
        self._batch_edit_done = done
        self._batch_edit_total = total
        self.batchEditChanged.emit()

    @Slot()
    def _on_batch_edit_work_done(self) -> None:
        self._batch_edit_active = False
        self.batchEditChanged.emit()
        self.canUndoBatchEditChanged.emit()
        self._refresh_view()
        self._on_sync_job_done()
        self.photoOpFinished.emit()

    @Slot()
    def cancelBatchEdit(self) -> None:
        """A futó köteg megszakítása: a MÉG el nem kezdett mappák kimaradnak
        — a már megírt mappák változása marad (egyetlen konzisztens ini-
        írásonként, nem félbehagyva), az `undoBatchEdit` az addig megírt
        mappákat vonja vissza."""
        self._ensure_batch_edit()
        self._batch_edit_cancel.set()

    @Slot()
    def undoBatchEdit(self) -> None:
        """Az utolsó kötegelt effekt-alkalmazás visszavonása — minden
        érintett kép `filters=` kulcsa visszaáll az alkalmazás előtti
        (nyers) értékre (#425 4. pont: egyetlen visszavonási lépés)."""
        self._ensure_batch_edit()
        if not self._batch_edit_undo:
            return
        batch = self._batch_edit_undo
        self._batch_edit_undo = None

        by_folder: dict[str, list[tuple[str, str | None]]] = {}
        for folder, name, prev_filters in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters))

        from picasapy.index import open_index

        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for name, prev_filters in entries:
                        if prev_filters is not None:
                            document = document.with_value(
                                name, "filters", prev_filters
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

        self.canUndoBatchEditChanged.emit()
        self._refresh_view()
