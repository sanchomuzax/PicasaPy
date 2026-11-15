"""„Csoportos szerkesztés ▸" — a Kép-menü kötegelt egykattintásos effektjei
(#425, `docs/specs/ui-audit-menus.md` K.1 szakasz).

Az `eMenuPicture` osztály K.1-ben dokumentált 9 képi művelete (automatikus
kontraszt/szín/vörösszem-eltávolítás, „Jó napom van", élesítés, filmszemcse,
melegítés, forgatás jobbra/balra) MIND a meglévő `EditSession`/`filters=`
motorra épül (ld. `picasapy.edit.session`) — ez a szelet csak a kijelölt N
képre való EGYSZERRE alkalmazást teszi hozzá, a `PhotoOpsMixin._apply_batch`/
`EffectsClipboardMixin.pasteEffects` mintáját követve (mappánként EGY,
útvonalanként soros, best-effort konkurenciakezelésű ini-írás), de HÁTTÉRSZÁLON és MEGSZAKÍTHATÓAN — nagy
kijelöléseknél (sok mappa, esetleg NAS) ez percekig tarthat (#425 4-5. pont).

A forgatás (jobbra/balra) NEM ide tartozik: az már kész és szinkron
(`PhotoOpsMixin.rotateRightMany`/`rotateLeftMany`) — a menü egyenesen azt
hívja, ez a modul a `filters=` láncot bővítő 8 effektet szolgálja ki.

Mixin-osztály: az `AppController` örökli, a `photo_ops_controller`
lusta-bekötés mintáját (#150) követve — nem kell az __init__-et (forró fájl)
módosítani.

#505: a háttérmunka a `BackgroundWorkerMixin._start_background`-on fut,
ami MAGÁTÓL bejelentkezik a közös busy-nyilvántartásba (`busy_registry.py`)
— a korábbi, itt élt kézi `_begin_sync_job`/`_on_sync_job_done` hívások
emiatt megszűntek.

`ID_PICTURE_SHOW_TEXT`/`ID_PICTURE_HIDE_TEXT` (#4335) külön parancsok: a
kijelölés `.picasa.ini`-bejegyzéseiből kérdezik le, van-e értelmezhető
szövegfedvény a kívánt `textactive=` állapotban, és a kijelölt fedvények
láthatóságát mappánként írják vissza.

„Undo All Edits" (#465 3. pont, a Kép-menü ugyanezen tétele, a Csoportos
szerkesztés almenün KÍVÜL): a `clearAllEffectsMany` a fenti infrastruktúrát
(mappánkénti írás, undo-verem) újrahasználva törli a kijelölt képek
szerkesztés-könyvelését. A kulcslistát az eredeti Picasa 3.9 képenkénti
törlője adja (`0x005ef6b0`, #7017): `filters`, `crop`, `flipped`, `redo`,
`text`, `textactive`; a `rotate` NEM törlődik. A `_write_filters`-től
eltérően EZ igen érinti a crop64-et is. Az `_batch_edit_undo` verem ezért
minden érintett kulcs előző nyers értékét megőrzi, enélkül az „Undo All
Edits" visszavonása a vágást, a tükrözést vagy a szövegfedvényt véglegesen
elveszítené, miközben a szűrőlánc visszatérne (#465 javítás, #7017)."""

from __future__ import annotations

import threading
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.edit.session import EditSession
from picasapy.ini import load_or_empty, update_document, with_backuphash
from picasapy.ini.text_overlay import (
    parse_text,
    parse_text_active,
    serialize_text_active,
)
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_controller import _WRITE_ERRORS
from .undo_all_edits_state import undo_all_edits_enabled
from .worker_thread import BackgroundWorkerMixin

# A K.1 táblázat 8, `filters=` láncot bővítő tétele — a forgatás a meglévő
# rotateRightMany/rotateLeftMany úton fut; a szöveg menüparancsai külön
# `textactive=` állapotot kezelnek.
# Az `EditSession` metódusa szerint csoportosítva:
_APPLY_NAMES = frozenset({"autolight", "autocolor", "enhance"})  # append-only
_TOGGLE_NAMES = frozenset({"redeye"})  # a meglévő egy-példányos kapcsoló
_APPEND_NAMES = frozenset({"unsharp", "grain2", "warm", "bw", "sepia"})
# #4624: a Sepia és a B&W a Picasa külön batch-parancsai; mindkettő
# paraméter nélküli effektet fűz a kijelölt képek `filters=` láncához.
# #2163: a `bw` azért került ide, mert az eredeti `Ctrl+Shift+B`-je
# ugyanezt teszi: a fekete-fehér szűrőt adja a KIJELÖLÉSRE
# (`0x005fe370(panel, "bw")`). A `render/chain.py` egykattintásos
# effektként már ismerte, csak a köteg-út nem.
_KNOWN_EFFECTS = _APPLY_NAMES | _TOGGLE_NAMES | _APPEND_NAMES


def _section_has_text_overlay(section) -> bool:
    """Van-e az EditController szabálya szerint értelmezhető `text=` érték."""
    raw = section.get("text") if section is not None else None
    if raw is None:
        return False
    try:
        overlay = parse_text(raw)
    except ValueError:
        return False
    return overlay is not None


def _section_text_overlay_visible(section) -> bool:
    """A hiányzó `textactive=` az edit_controller betöltési szabálya szerint látható."""
    raw = section.get("textactive") if section is not None else None
    return parse_text_active(raw) if raw is not None else True


def _selected_text_overlay_photos(controller, rows, visible: bool) -> list:
    """A megadott `textactive=` állapotú kijelölt fotók, mappánkénti olvasással."""
    documents: dict[str, object | None] = {}
    photos = []
    for photo in controller._rows_to_photos(rows or ()):
        if photo.kind == "video":
            continue
        folder = photo.folder_path
        if folder not in documents:
            try:
                documents[folder] = load_or_empty(
                    Path(folder) / PICASA_INI_NAME
                )
            except (OSError, UnicodeError):
                documents[folder] = None
        document = documents[folder]
        if document is None:
            continue
        section = document.section(photo.name)
        if (
            _section_has_text_overlay(section)
            and _section_text_overlay_visible(section) == bool(visible)
        ):
            photos.append(photo)
    return photos


def _apply_one(session: EditSession, name: str) -> EditSession:
    """Egyetlen egykattintásos effekt alkalmazása a session láncára.

    A metódus-választás az `EditSession` már meglévő, szűk API-ját követi
    (nem vezet be új réteg-fajtát) — `apply()` az append-only egygombos
    javításokhoz, `toggle()` a redeye-hoz (az egyetlen létező toggle-effekt),
    `append_effect()` a paraméter nélküli effektekhez; a kötegelt `unsharp`
    név az eredeti Picasa alapértelmezett `unsharp2=1,0.600000` tagjaként
    kerül a láncba."""
    if name == "unsharp":
        return session.append_effect("unsharp2", ("1", "0.600000"))
    if name in _APPLY_NAMES:
        return session.apply(name)
    if name in _TOGGLE_NAMES:
        return session.toggle(name)
    return session.append_effect(name)


def _write_filters(document, section_name: str, session: EditSession):
    """A `filters=` kulcs beírása/törlése (a `crop=` tükör-kulcs nélkül —
    ez a szelet sosem érinti a crop64-et); a kép `backuphash`-ével együtt."""
    if session.is_empty():
        document = document.with_removed(section_name, "filters")
    else:
        document = document.with_value(section_name, "filters", session.to_value())
    # #5854: a szűrőlánc és az időbélyeg ugyanazon mappánkénti ini-tranzakció része.
    return with_backuphash(document, section_name)


# Az eredeti Undo All Edits képenkénti törlőjének kulcsai (`0x005ef6b0`,
# hívási helyek `0x005ef8e8-0x005ef90c`, #7017). A `rotate` SZÁNDÉKOSAN
# hiányzik: az eredeti nem törli.
_UNDO_ALL_KEYS = ("filters", "crop", "flipped", "redo", "text", "textactive")
# A kötegelt effekt csak a láncot írja, a `crop=` tükör-kulcsot érintetlenül
# hagyja; az undo ezt az (ártalmatlan no-op) értéket is visszaírja.
_APPLY_UNDO_KEYS = ("filters", "crop")


@dataclass(frozen=True, slots=True)
class _UndoEntry:
    """Egy kép visszavonási adata: a MŰVELET által érintett kulcsok előző
    nyers értéke (`None` = a kulcs nem volt meg)."""

    folder: str
    name: str
    previous: tuple[tuple[str, str | None], ...]

    def value(self, key: str) -> str | None:
        return next((v for k, v in self.previous if k == key), None)


def _capture(folder: str, name: str, section, keys) -> _UndoEntry:
    """A `keys` kulcsok jelenlegi nyers értéke a kép szakaszából."""
    previous = tuple((key, section.get(key) if section else None) for key in keys)
    return _UndoEntry(folder, name, previous)


def _restore_keys(document, entry: _UndoEntry):
    """Az `entry` kulcsainak visszaírása változatlanul (`carried`, #643: a
    lánc máshonnan jön vissza, nem szerkesztőből); a hiányzó kulcs törlődik,
    hogy az undo ne szüljön olyan kulcsot, ami eredetileg nem volt."""
    for key, value in entry.previous:
        if value is None:
            document = document.with_removed(entry.name, key)
        else:
            document = document.with_value(entry.name, key, value, carried=True)
    # A visszaállított kulcsok ugyanúgy ini-írás, mint az alkalmazott
    # effekt: a képszakasz időbélyege frissül.
    return with_backuphash(document, entry.name)


def _clear_all_effects(document, section_name: str):
    """A szerkesztés-könyvelés TELJES törlése az eredeti Picasa kulcslistája
    szerint (#465 3. pont, #7017, „Undo All Edits"): `filters`, `crop`,
    `flipped`, `redo`, `text`, `textactive`; a `rotate` marad. A `crop=`
    tükör-kulcs az `edit_controller._save()` mintája szerint együtt megy a
    lánccal: a crop64 a láncon belül lakik, ezért a külön Picasa-paritás
    `crop=rect64(...)` kulcs a lánc törlése után elavulttá válna."""
    for key in _UNDO_ALL_KEYS:
        document = document.with_removed(section_name, key)
    return document


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
        # az utolsó köteg visszavonási adatai: képenkénti `_UndoEntry`-k
        # (mappa, fájlnév, az érintett kulcsok ELŐZŐ nyers értéke); None =
        # nincs (törölve/le nem futott). A `clearAllEffectsMany` a `crop=`,
        # `flipped=`, `redo=`, `text=`, `textactive=` kulcsot is törli
        # (#465 javítás, #7017): ezek nélkül az „Undo All Edits"
        # visszavonása után a vágás, a tükrözés és a szövegfedvény
        # véglegesen elveszne, miközben a szűrőlánc visszatér — ez
        # adatvesztés lenne.
        self._batch_edit_undo: list[_UndoEntry] | None = None
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
        képek MINDEGYIKÉRE (#425): mappánként EGY, útvonalanként soros,
        best-effort konkurenciakezelésű ini-írás,
        háttérszálon, mappánként frissülő haladásjelzéssel és
        megszakíthatósággal (`cancelBatchEdit`). A beillesztés előtti nyers
        `filters=` értékek egyetlen undo-lépésként kerülnek a verembe."""
        self._ensure_batch_edit()
        # A nem-dolgozó ágak egyszerűen visszatérnek; a felület a
        # PhotoGridModel tényleges változásait követi.
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

        def worker() -> None:
            undo_batch: list[_UndoEntry] = []
            done = 0
            for folder, folder_photos in by_folder.items():
                if self._batch_edit_cancel.is_set():
                    break
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[_UndoEntry] = []

                # #750: a mappa MOST kiírt láncai a naplóhoz — az `entries`
                # mintájára a mutate-ben töltjük (ütközéskori újrajátszásnál
                # a FRISS értékeket kell naplózni), és felülírással, hogy az
                # újrajátszás ne duplikáljon.
                naplo: list[tuple[str, str]] = []

                # B023-minta (`effects_controller.pasteEffects`): az
                # `entries` alapértelmezett argumentumként kötve, mert a
                # mutate szinkron fut a ciklus adott körén belül.
                def mutate(
                    document, folder=folder, folder_photos=folder_photos,
                    entries=entries, naplo=naplo,
                ):
                    fresh: list[_UndoEntry] = []
                    friss_naplo: list[tuple[str, str]] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        entry = _capture(
                            folder, photo.name, section, _APPLY_UNDO_KEYS
                        )
                        fresh.append(entry)
                        session = _apply_one(
                            EditSession.from_value(entry.value("filters")),
                            effect_name,
                        )
                        document = _write_filters(document, photo.name, session)
                        friss_naplo.append(
                            (str(Path(folder) / photo.name), session.to_value())
                        )
                    entries[:] = fresh
                    naplo[:] = friss_naplo
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    break
                undo_batch.extend(entries)
                # #750: MAPPÁNKÉNT egy naplóírás — a Picasa felülírása ellen
                # ez az egyetlen nyomunk ezen az úton is. Mappánként (és nem
                # képenként) írunk, hogy a napló ne lassítsa a köteget.
                self.recordSavedChains(naplo)
                self._sync_tree_locked(folder)
                done += 1
                self._batchEditProgress.emit(folder, done, len(by_folder))
            self._batch_edit_undo = undo_batch if undo_batch else None
            self._batchEditWorkDone.emit()

        # #438: nyilvántartott daemon-szál (BackgroundWorkerMixin, #430)
        self._start_background(worker, name="picasapy-batcheffect")

    @Slot(list, result=list)
    def redeyeNamesInSelection(self, rows) -> list[str]:
        """A kijelölés vörösszem-javítást hordozó képeinek neve (#3573).

        Az eredeti figyelmeztetés a képet NÉVVEL mondja
        (`IDS_CONFIRM_REDEYE_REVERT`: „Red eye fixes have been applied to
        %s.”). A sorrend a kijelölésé; a hibatűrése
        érvényes itt is: olvashatatlan ini-ből nem jön név.
        """
        photos = self._rows_to_photos(rows)
        documents: dict[str, object] = {}
        names: list[str] = []
        for photo in photos:
            folder = photo.folder_path
            if folder not in documents:
                try:
                    documents[folder] = load_or_empty(Path(folder) / PICASA_INI_NAME)
                except OSError:
                    documents[folder] = None
            document = documents[folder]
            if document is None:
                continue
            section = document.section(photo.name)
            if section is None:
                continue
            if EditSession.from_value(section.get("filters")).has("redeye"):
                names.append(photo.name)
        return names

    @Slot(list, bool, result=bool)
    def hasTextOverlayStateInSelection(self, rows, visible: bool) -> bool:  # noqa: N802
        """Van-e a kijelölésben a kért láthatósági állapotú szövegfedvény.

        Az index nem tartja a `text=`/`textactive=` értéket, ezért a kijelölt
        mappák `.picasa.ini`-jét olvassuk. A hibás vagy olvashatatlan bejegyzés
        nem teszi aktívvá a parancsot.
        """
        return bool(_selected_text_overlay_photos(self, rows, visible))

    @Slot(list, bool)
    def setTextOverlayVisibleMany(self, rows, visible: bool) -> None:  # noqa: N802
        """A kijelölt, szövegfedvényes képek `textactive=` állapotának beállítása."""
        photos = _selected_text_overlay_photos(self, rows, not visible)

        def mutate(document, photo):
            section = document.section(photo.name)
            if not _section_has_text_overlay(section):
                return document
            if _section_text_overlay_visible(section) == bool(visible):
                return document
            return document.with_value(
                photo.name, "textactive", serialize_text_active(visible)
            )

        if photos:
            self._apply_batch(photos, mutate)

    @Slot(list, result=bool)
    def undoAllEditsEnabled(self, rows) -> bool:  # noqa: N802
        """Él-e az „Összes szerkesztés visszavonása" a `rows` képekre (#7017).

        A Kép menü, a helyi menük és a néző menüje EZT hívja, tehát a
        szürkítés egyetlen helyen dől el (`undo_all_edits_state`). Az „első
        kijelölt" a RÁCS szerinti első, nem a kattintási sorrend szerinti
        (a #6995 „Locate on Disk" döntése: a Ctrl+katt sorrendje ne
        számítson)."""
        return undo_all_edits_enabled(self._rows_to_photos(sorted(map(int, rows))))

    @Slot(list)
    def clearAllEffectsMany(self, rows) -> None:
        """„Undo All Edits" (#465 3. pont): a kijelölt képek MINDEGYIKÉNEK
        szerkesztés-könyvelése törlődik az eredeti Picasa kulcslistája
        szerint (`filters`, `crop`, `flipped`, `redo`, `text`, `textactive`;
        a `rotate` marad, #7017). Az `applyEffectMany` mappánkénti,
        háttérszálas, megszakítható mintáját követi, és UGYANAZT az
        `_batch_edit_undo` vermet tölti, tehát a `undoBatchEdit()` ezt is
        visszavonja, MINDEN törölt kulccsal együtt (#465 javítás, #7017):
        enélkül a vágás, a tükrözés vagy a szövegfedvény visszavonás után
        is véglegesen elveszne."""
        self._ensure_batch_edit()
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

        def worker() -> None:
            undo_batch: list[_UndoEntry] = []
            done = 0
            for folder, folder_photos in by_folder.items():
                if self._batch_edit_cancel.is_set():
                    break
                ini_path = Path(folder) / PICASA_INI_NAME
                entries: list[_UndoEntry] = []

                def mutate(
                    document, folder=folder, folder_photos=folder_photos,
                    entries=entries,
                ):
                    fresh: list[_UndoEntry] = []
                    for photo in folder_photos:
                        section = document.section(photo.name)
                        fresh.append(
                            _capture(folder, photo.name, section, _UNDO_ALL_KEYS)
                        )
                        document = _clear_all_effects(document, photo.name)
                        document = with_backuphash(document, photo.name)
                    entries[:] = fresh
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    break
                undo_batch.extend(entries)
                # #750: a TÖRÖLT lánc üres bejegyzésként megy a naplóba, ami
                # ott törlést jelent — a felhasználó maga vonta vissza a
                # szerkesztéseit, nincs mit védeni (és riasztani sem szabad).
                self.recordSavedChains(
                    [(str(Path(folder) / photo.name), "") for photo in folder_photos]
                )
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
        visszavonása: minden érintett kép minden, a művelet által érintett
        kulcsa visszaáll az alkalmazás előtti (nyers) értékre (#425 4.
        pont: egyetlen visszavonási lépés). A `clearAllEffectsMany` által
        törölt `crop`, `flipped`, `redo`, `text` és `textactive` kulcs
        visszaállítása nélkül az adat véglegesen elveszne (#465 javítás,
        #7017). Az `applyEffectMany` csak a `filters`/`crop` kulcsot
        rögzíti, ott ugyanazt az értéket írjuk vissza, ami ártalmatlan
        no-op."""
        self._ensure_batch_edit()
        if not self._batch_edit_undo:
            return
        batch = self._batch_edit_undo
        self._batch_edit_undo = None

        by_folder: dict[str, list[_UndoEntry]] = {}
        for entry in batch:
            by_folder.setdefault(entry.folder, []).append(entry)

        from picasapy.index import open_index

        with open_index(self._db_path) as conn:
            for folder, entries in by_folder.items():
                ini_path = Path(folder) / PICASA_INI_NAME

                def mutate(document, entries=entries):
                    for entry in entries:
                        document = _restore_keys(document, entry)
                    return document

                try:
                    update_document(ini_path, mutate, backup=True)
                except _WRITE_ERRORS as error:
                    self.photoOpFailed.emit(str(error))
                    return
                # #750: a visszavonás is a MI írásunk — a napló ezután a
                # visszaállított (köteg előtti) láncot védi. Enélkül a
                # visszavonás után védtelenül maradna a kép, vagy — ha a
                # köteg bejegyzése bent maradna — hamisan riasztanánk.
                self.recordSavedChains(
                    [
                        (str(Path(folder) / entry.name), entry.value("filters") or "")
                        for entry in entries
                    ]
                )
                self._sync_tree(conn, folder)

        self.canUndoBatchEditChanged.emit()
        self._refresh_view()
