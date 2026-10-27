"""A retusáló eszköz és a nem mentett javítófoltok kezelése."""

from __future__ import annotations

from .edit_controller_shared import (
    EditSession,
    Property,
    RetouchPatch,
    Slot,
    _BRUSH_SIZE_MAX,
    _BRUSH_SIZE_MIN,
    _BRUSH_SIZE_TO_RELATIVE_DIVISOR,
    _clamp01,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

class EditControllerRetouchMixin:
    """A retusáló eszköz és a nem mentett javítófoltok kezelése."""

    @Property(bool, notify=_Signals.toolsChanged)
    def hasRetouch(self) -> bool:
        """Van-e MENTETT retusálás — akár a jelenlegi (v2, folt-alapú, #445),
        akár egy korábbi PicasaPy-verzió (v1, téglalap-régiós, #148) által
        mentett alakban — a „Visszavonás: Retusálás" felirathoz és a UI
        állapot-jelzéséhez."""
        return bool(self._session.retouch_patches()) or bool(self._session.retouch_regions())


    @Property(int, notify=_Signals.revisionChanged)
    def retouchPendingCount(self) -> int:
        """A retusálás-eszközben véglegesített (kétkattintásos), MÉG NEM
        alkalmazott foltok száma — az Alkalmaz gomb csak akkor engedélyezett,
        ha ez pozitív."""
        return len(self._retouch_patches)


    @Property(bool, notify=_Signals.revisionChanged)
    def retouchPatchPending(self) -> bool:
        """Van-e félbehagyott folt (cél kijelölve, forrás még nincs
        véglegesítve) — a „Refining…" felirathoz a QML-ben."""
        return self._retouch_target is not None


    @Property(bool, notify=_Signals.revisionChanged)
    def canUndoPatch(self) -> bool:
        """Van-e patch-enkénti visszavonható lépés a retusálás-pufferben
        (NEM a globális Visszavonás-verem, ld. `undoPatch`)."""
        return bool(self._retouch_patch_undo)


    @Property(bool, notify=_Signals.revisionChanged)
    def canRedoPatch(self) -> bool:
        return bool(self._retouch_patch_redo)


    @Property(int, notify=_Signals.toolsChanged)
    def brushSize(self) -> int:
        """A retusálás-ecset mérete [1..100] egészben ("Brush Size", #445)."""
        return self._brush_size


    @Property(float, notify=_Signals.toolsChanged)
    def retouchBrushRadiusRatio(self) -> float:  # noqa: N802 — QML-property
        """A retusáló ecset sugara a kép rövidebb oldalához mérve.

        Ugyanazt a saját, dokumentált méretleképezést adja a felületnek,
        amelyet a `_build_patch()` a képi javításnál használ.
        """
        return self._brush_size / _BRUSH_SIZE_TO_RELATIVE_DIVISOR


    @Slot()
    def enterRetouchTool(self) -> None:
        """A Retusálás eszköz megnyitása: a puffer a MENTETT foltokkal
        indul (ha a felhasználó korábban már alkalmazott retusálást ezzel
        az eszközzel — egy korábbi, v1 téglalap-régiós retusálás nem
        tölthető be foltként, ld. `EditSession.retouch_patches` docsztring),
        nem ír inibe, nem tol undo-lépést."""
        self._require_active()
        self._retouch_patches = self._session.retouch_patches()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()


    @Slot()
    def exitRetouchTool(self) -> None:
        """A Retusálás eszköz bezárása (Mégse): a puffer eldobása, visszaáll
        a ténylegesen mentett előnézetre — a mentett foltok érintetlenek."""
        self._require_active()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._register_preview()
        self._bump_revision()


    @Slot(float, float)
    def beginRetouchPatch(self, x: float, y: float) -> None:
        """1. kattintás: a javítandó folt (CÉL) kijelölése. Félbehagyott
        (korábban elkezdett, de nem véglegesített) folt esetén a régi
        cél-pontot csendben lecseréli az újra."""
        self._require_active()
        self._retouch_target = (_clamp01(x), _clamp01(y))
        self._bump_revision()


    @Slot(float, float)
    def previewRetouchSource(self, x: float, y: float) -> None:
        """Egérmozgatás a CÉL kijelölése UTÁN: a csereterület (FORRÁS) élő
        előnézete — NEM ír inibe, NEM tol undo-lépést. Cél nélkül (nincs
        folyamatban lévő folt) néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        patch = self._build_patch(self._retouch_target, (_clamp01(x), _clamp01(y)))
        preview_patches = (*self._retouch_patches, patch)
        self._register_preview(self._session.set_retouch_patches(preview_patches))
        self._bump_revision()


    @Slot(float, float)
    def commitRetouchPatch(self, x: float, y: float) -> None:
        """2. kattintás: a folt véglegesítése a PENDING pufferben (patch-
        enkénti undo-lépéssel) — NEM ír inibe (az Alkalmazásig). Cél nélkül
        néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        patch = self._build_patch(self._retouch_target, (_clamp01(x), _clamp01(y)))
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patch_redo.clear()
        self._retouch_patches = (*self._retouch_patches, patch)
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def cancelRetouchPatch(self) -> None:
        """Félbehagyott folt eldobása (pl. Esc) — a korábban VÉGLEGESÍTETT
        foltok érintetlenek. Félbehagyott folt nélkül néma no-op."""
        self._require_active()
        if self._retouch_target is None:
            return
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()


    @Slot(int)
    def setBrushSize(self, value: int) -> None:
        """Az ecset méretének beállítása ([1..100]-ra clampelve, #445)."""
        self._require_active()
        self._brush_size = max(_BRUSH_SIZE_MIN, min(_BRUSH_SIZE_MAX, value))
        self.toolsChanged.emit()


    @Slot()
    def undoPatch(self) -> None:
        """Az utoljára véglegesített folt visszavonása a pufferben."""
        if not self._retouch_patch_undo:
            return
        self._require_active()
        self._retouch_patch_redo.append(self._retouch_patches)
        self._retouch_patches = self._retouch_patch_undo.pop()
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def redoPatch(self) -> None:
        """A visszavont folt ismételt alkalmazása a pufferben."""
        if not self._retouch_patch_redo:
            return
        self._require_active()
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patches = self._retouch_patch_redo.pop()
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def resetPatches(self) -> None:
        """A puffer minden foltjának törlése (a félbehagyott folt is) —
        patch-enkénti undo-lépéssel (`undoPatch` visszaállíthatja). Üres
        pufferen/félbehagyott folt nélkül néma no-op."""
        if not self._retouch_patches and self._retouch_target is None:
            return
        self._require_active()
        self._retouch_patch_undo.append(self._retouch_patches)
        self._retouch_patch_redo.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._register_preview(self._session_with_retouch_pending())
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def applyRetouch(self) -> None:
        """Alkalmaz: a puffer foltjainak mentése a láncba (undo + ini-írás).
        Üres puffernél no-op (a gomb ilyenkor a UI-ban tiltott) — egy
        félbehagyott (cél nélküli forrás) folt csendben elvész."""
        self._require_active()
        if not self._retouch_patches:
            return
        self._push_undo("retouch")
        self._session = self._session.set_retouch_patches(self._retouch_patches)
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def _build_patch(
        self, target: tuple[float, float], source: tuple[float, float]
    ) -> RetouchPatch:
        return RetouchPatch(
            target_x=target[0],
            target_y=target[1],
            source_x=source[0],
            source_y=source[1],
            radius=self._brush_size / _BRUSH_SIZE_TO_RELATIVE_DIVISOR,
        )


    def _session_with_retouch_pending(self) -> EditSession:
        return self._session.set_retouch_patches(self._retouch_patches)

