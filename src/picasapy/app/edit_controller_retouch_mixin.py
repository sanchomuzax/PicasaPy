"""A retusáló eszköz és a nem mentett javítófoltok kezelése."""

from __future__ import annotations

import logging

from . import retouch_brush as _brush
from .edit_controller_shared import (
    EditSession,
    Property,
    RetouchPatch,
    Slot,
    _BRUSH_SIZE_MAX,
    _BRUSH_SIZE_MIN,
    _clamp01,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

_log = logging.getLogger(__name__)

#: Ismeretlen képméretnél (olvashatatlan fejléc) csak ez a menekülő érték
#: tartja életben a foltot: a relatív sugár ehhez a rövidebb oldalhoz mér, és a
#: napló figyelmeztet. A mért méret nem ez, hanem a kép fejlécéből jön.
_FALLBACK_SHORTER_SIDE = 1024

class EditControllerRetouchMixin:
    """A retusáló eszköz és a nem mentett javítófoltok kezelése."""

    @Property(bool, notify=_Signals.hasRetouchChanged)
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


    @Property(int, notify=_Signals.brushSizeChanged)
    def brushSize(self) -> int:
        """A retusálás-ecset mérete [1..100] egészben ("Brush Size", #445)."""
        return self._brush_size


    @Property(float, notify=_Signals.retouchBrushSourceRadiusChanged)
    def retouchBrushSourceRadius(self) -> float:  # noqa: N802 (QML-property)
        """A retusáló ecset sugara a FORRÁSKÉPEN, képpontban (#7406).

        `r = max(3, 100·s·z) / z`, ahol `s` a csúszka mezője (érintetlen
        csúszkánál 0,25, utána a fogantyú helye a futásban) és `z` a nézet
        nagyítása. A kép méretétől nem függ; a felület a gyűrűt `r·z`
        képernyő-sugárral rajzolja, a `_build_patch()` pedig ebből számolja a
        mentett folt relatív sugarát."""
        fraction = _brush.brush_fraction(self._brush_size, touched=self._brush_touched)
        return _brush.source_radius(fraction, self._retouch_view_zoom)


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
        self._brush_touched = True
        self.toolsChanged.emit()


    @Slot(float)
    def setRetouchViewZoom(self, zoom: float) -> None:  # noqa: N802 (QML-slot)
        """A nézet nagyítása (1,0 = 100%, a forrásképhez mérve): a QML adja át,
        mert a gyűrű és a folt sugarának 3 képernyő-képpontos minimuma ettől
        függ (#7406). Nézet-állapot: nem kell aktív szerkesztés, nem ír inibe."""
        zoom = _brush.sanitize_zoom(zoom)
        if zoom == self._retouch_view_zoom:
            return
        self._retouch_view_zoom = zoom
        self.retouchBrushSourceRadiusChanged.emit()


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
            radius=_brush.relative_radius(
                self.retouchBrushSourceRadius, self._retouch_reference_side()
            ),
        )


    def _retouch_reference_side(self) -> int:
        """A kép rövidebb oldala képpontban: a forrásképi sugárból ezzel lesz a
        `retouch=2` token relatív sugara (a formátum változatlan, #7406)."""
        if self._image_size:
            return max(1, min(self._image_size))
        _log.warning(
            "A retusáláshoz nem ismert a kép mérete, a relatív sugár %d képpont "
            "rövidebb oldalhoz mér", _FALLBACK_SHORTER_SIDE,
        )
        return _FALLBACK_SHORTER_SIDE


    def _session_with_retouch_pending(self) -> EditSession:
        return self._session.set_retouch_patches(self._retouch_patches)

