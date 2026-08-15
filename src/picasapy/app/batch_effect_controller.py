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

#505: a háttérmunka a `BackgroundWorkerMixin._start_background`-on fut,
ami MAGÁTÓL bejelentkezik a közös busy-nyilvántartásba (`busy_registry.py`)
— a korábbi, itt élt kézi `_begin_sync_job`/`_on_sync_job_done` hívások
emiatt megszűntek.

A Szöveg megjelenítése/elrejtése (`ID_PICTURE_SHOW_TEXT`/`…HIDE_TEXT`) NEM
része ennek a szeletnek: az index nem tárolja, mely fotóknak van szöveg-
overlay-je (`text=`/`textactive=`, ld. `picasapy.ini.text_overlay`), így a
menüpont #425 5. pontban leírt feltételes engedélyezése (csak akkor aktív,
ha a kijelölésben van szövegréteges kép) jelen ismeretekkel nem
állapítható meg olcsón — a `PicasaMenuBar.qml`-ben egyelőre placeholder.

„Undo All Edits" (#465 3. pont, a Kép-menü ugyanezen tétele, a Csoportos
szerkesztés almenün KÍVÜL): a `clearAllEffectsMany` a fenti infrastruktúrát
(mappánkénti írás, undo-verem) újrahasználva törli a kijelölt képek TELJES
`filters=` láncát a `crop=` tükör-kulccsal együtt — a `_write_filters`-től
eltérően EZ igen érinti a crop64-et, hiszen a „mindent vissza" definíció
szerint (ld. #465 issue) a teljes láncot törli, nem csak egy effektet. Az
`_batch_edit_undo` verem ezért MINDKÉT kulcs (`filters=`, `crop=`) előző
nyers értékét megőrzi — enélkül az „Undo All Edits" visszavonása a vágást
véglegesen elveszítené, miközben a szűrőlánc visszatérne (#465 javítás)."""

from __future__ import annotations

import threading
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.session import EditSession
from picasapy.ini import load_or_empty, update_document
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_controller import _WRITE_ERRORS
from .worker_thread import BackgroundWorkerMixin

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


def _clear_all_effects(document, section_name: str):
    """A `filters=` lánc TELJES törlése a `crop=` tükör-kulccsal együtt
    (#465 3. pont, „Undo All Edits") — az `edit_controller._save()` mintája:
    a crop64 a láncon belül lakik, ezért a láncot törölve a külön
    Picasa-paritás `crop=rect64(...)` kulcs is elavulttá válna, ha
    érintetlenül maradna."""
    document = document.with_removed(section_name, "filters")
    return document.with_removed(section_name, "crop")


class BatchEffectMixin(BackgroundWorkerMixin):
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
        # filters=, ELŐZŐ nyers crop=) négyesek listája; None = nincs
        # (törölve/le nem futott). A `crop=` Picasa-paritás tükör-kulcs is
        # KELL az undóhoz (#465 javítás): a `clearAllEffectsMany` ezt is
        # törli, enélkül az „Undo All Edits" visszavonása után a vágás
        # véglegesen elveszne, miközben a szűrőlánc visszatér — ez
        # adatvesztés lenne. Az `applyEffectMany` nem érinti a crop=-ot,
        # de ártalmatlan ugyanazt az (érintetlen) értéket visszaírni.
        self._batch_edit_undo: (
            list[tuple[str, str, str | None, str | None]] | None
        ) = None
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
        # A nem-dolgozó ágakon is JELEZNÜNK kell a befejezést: a hívó (és a
        # teszt) a photoOpFinished-re vár, és néma visszatérésnél örökre
        # várna. A hibát a #475-ös hangos vészfék buktatta ki — a néma,
        # 5 mp-es változat alatt a rá írt teszt hamisan ment át.
        if effect_name not in _KNOWN_EFFECTS:
            self.photoOpFinished.emit()
            return
        photos = self._rows_to_photos(rows)
        if not photos:
            self.photoOpFinished.emit()
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

        def worker() -> None:
            undo_batch: list[tuple[str, str, str | None, str | None]] = []
            done = 0
            for folder, folder_photos in by_folder.items():
                if self._batch_edit_cancel.is_set():
                    break
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None, str | None]] = []

                # B023-minta (`effects_controller.pasteEffects`): az
                # `entries` alapértelmezett argumentumként kötve, mert a
                # mutate szinkron fut a ciklus adott körén belül.
                def mutate(
                    document, folder=folder, folder_photos=folder_photos,
                    entries=entries,
                ):
                    fresh: list[tuple[str, str, str | None, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        prev_crop = section.get("crop") if section else None
                        fresh.append((folder, photo.name, prev, prev_crop))
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

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-batcheffect")

    @Slot(list, result=bool)
    def selectionHasRedeye(self, rows) -> bool:
        """Van-e a kijelölésben vörösszem-javítás (#465)?

        Az eredeti Picasa a teljes visszaállítás előtt KÜLÖN figyelmeztet
        rá (`IDS_CONFIRM_REDEYE_REVERT`), mert a vörösszem régió-adatot
        hordoz: a törléssel véglegesen elvész, az „Újra" nem hozza vissza.

        A megerősítő dialógus hívja, tehát a GUI-szálon fut — ezért csak a
        `.picasa.ini` fájlokat olvassa (mappánként egyszer), képet nem nyit
        meg. Olvashatatlan ini-nél `False` (a #301-elv szerint: idegen/sérült
        adat nem szökhet ki kivétellel, és a hiánya nem hazudik javítást).
        """
        by_folder: dict[str, set[str]] = {}
        for photo in self._rows_to_photos(rows):
            by_folder.setdefault(photo.folder_path, set()).add(photo.name)
        for folder, names in by_folder.items():
            try:
                document = load_or_empty(Path(folder) / PICASA_INI_NAME)
            except OSError:
                continue
            for name in names:
                section = document.section(name)
                if section is None:
                    continue
                if EditSession.from_value(section.get("filters")).has("redeye"):
                    return True
        return False

    @Slot(list)
    def clearAllEffectsMany(self, rows) -> None:
        """„Undo All Edits" (#465 3. pont): a kijelölt képek MINDEGYIKÉNEK
        teljes szerkesztési lánca (`filters=`, a `crop=` tükör-kulccsal
        együtt) törlődik — az `applyEffectMany` mappánkénti, háttérszálas,
        megszakítható mintáját követi, és UGYANAZT az `_batch_edit_undo`
        vermet tölti, tehát a `undoBatchEdit()` ezt is visszavonja — a
        `crop=` tükör-kulccsal EGYÜTT (#465 javítás): enélkül a vágás
        visszavonás után is véglegesen elveszne, miközben a szűrőlánc
        visszatérne."""
        self._ensure_batch_edit()
        photos = self._rows_to_photos(rows)
        if not photos:
            # ld. az applyEffectMany-nél: a néma visszatérés örökké várató
            # hívót hagyna maga után (#475)
            self.photoOpFinished.emit()
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

        def worker() -> None:
            undo_batch: list[tuple[str, str, str | None, str | None]] = []
            done = 0
            for folder, folder_photos in by_folder.items():
                if self._batch_edit_cancel.is_set():
                    break
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[tuple[str, str, str | None, str | None]] = []

                def mutate(
                    document, folder=folder, folder_photos=folder_photos,
                    entries=entries,
                ):
                    fresh: list[tuple[str, str, str | None, str | None]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        prev = section.get("filters") if section else None
                        prev_crop = section.get("crop") if section else None
                        fresh.append((folder, photo.name, prev, prev_crop))
                        document = _clear_all_effects(document, photo.name)
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

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-batcheffect")

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
        """Az utolsó kötegelt effekt-alkalmazás (vagy „Undo All Edits")
        visszavonása — minden érintett kép `filters=` KULCSA ÉS `crop=`
        tükör-kulcsa is visszaáll az alkalmazás előtti (nyers) értékre
        (#425 4. pont: egyetlen visszavonási lépés; #465 javítás: a
        `crop=` visszaállítása nélkül a `clearAllEffectsMany` által törölt
        vágás visszavonás után is véglegesen elveszne — az `applyEffectMany`
        nem érinti a crop=-ot, ott ugyanazt az értéket írjuk vissza, ami
        ártalmatlan no-op)."""
        self._ensure_batch_edit()
        if not self._batch_edit_undo:
            return
        batch = self._batch_edit_undo
        self._batch_edit_undo = None

        by_folder: dict[str, list[tuple[str, str | None, str | None]]] = {}
        for folder, name, prev_filters, prev_crop in batch:
            by_folder.setdefault(folder, []).append((name, prev_filters, prev_crop))

        from picasapy.index import open_index

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
                            document = document.with_value(
                                name, "crop", prev_crop
                            )
                        else:
                            document = document.with_removed(name, "crop")
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                self._sync_tree(conn, folder)

        self.canUndoBatchEditChanged.emit()
        self._refresh_view()
