"""A szerkesztési munkamenet, eszközváltás és effektlánc kezelése."""

from __future__ import annotations

import logging
import threading
from typing import TYPE_CHECKING

from PySide6.QtCore import QMetaObject
from picasapy.halozati_ut import halozati_gyoker
from picasapy.ini import parse_document
from picasapy.metadata.reader import _cache_exif_details, _cached_exif_details

from .edit_controller_shared import (
    AZONOSSAG,
    EditSession,
    PICASA_INI_NAME,
    Path,
    Property,
    QLocale,
    QtNamespace,
    Slot,
    _DEFAULT_BRUSH_SIZE,
    _DEFAULT_TEXT_ALIGN,
    _DEFAULT_TEXT_BOLD,
    _DEFAULT_TEXT_FILL_COLOR,
    _DEFAULT_TEXT_FILL_ENABLED,
    _DEFAULT_TEXT_ITALIC,
    _DEFAULT_TEXT_OPACITY,
    _DEFAULT_TEXT_OUTLINE_COLOR,
    _DEFAULT_TEXT_OUTLINE_THICKNESS,
    _DEFAULT_TEXT_SIZE_PT,
    _DEFAULT_TEXT_UNDERLINE,
    _ONE_SHOT_NAMES,
    _TOGGLE_NAMES,
    formatting,
    read_exif_details,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

if TYPE_CHECKING:
    from .edit_controller import EditController


_NETWORK_EDIT_STATE_LOCK = threading.Lock()
_log = logging.getLogger(__name__)


class EditControllerSessionMixin:
    """A szerkesztési munkamenet, eszközváltás és effektlánc kezelése."""

    @Slot(str, str)
    def beginEdit(self, photo_id: str, image_path: str) -> None:
        """Szerkesztés indítása: a filters= betöltése az iniből (hiányzó
        ini/szekció/kulcs esetén üres lánc), regisztráció a previewnél."""
        # #546: a képváltás érvényteleníti a futó háttér-rendert — az az
        # ELŐZŐ fotó képét tárolná el (és emitálna rá revíziót)
        self._preview_job += 1
        # #3773: MÁSIK fotóra nyitva a régi RENDERELT kép elengedése. A
        # szolgáltató képtára két helyes, és a kettős nézetben két vezérlő
        # tölti: bent hagyva a régi kép a MÁSIK vezérlő élő képét
        # szoríthatja ki (mérve: „ab" módba lépéskor a bal fél a
        # helykitöltőt kapta). A dekódolt forrás marad — a visszalapozás
        # arra épít.
        if self._photo_id and self._photo_id != photo_id:
            self._provider.kepet_elenged(self._kulcs)
        path = Path(image_path)
        # #3014: minden sima nyitás ÍRÓ munkamenet — a memóriás mód csak a
        # `beginEditInMemory`-vel jár, és nem ragadhat át a következő fotóra
        self._memory_only = False
        self._photo_id = photo_id
        self._image_path = path
        network_path = halozati_gyoker(path) is not None
        self._network_edit_generation = getattr(
            self, "_network_edit_generation", 0
        ) + 1
        generation = self._network_edit_generation
        self._network_edit_load_pending = network_path
        self._network_edit_load_failed = False
        self._network_edit_load_error = ""
        self._network_edit_filters_dirty_pending = False
        self._network_edit_text_dirty_pending = False
        self._cached_ini_document = None
        self._network_crop_suggestions_key = None
        self._network_crop_suggestions = []
        self._network_crop_suggestions_pending = set()
        self._network_crop_suggestion_results = {}
        self._image_size = None if network_path else self._read_image_size(path)
        self._ini_path = path.parent / PICASA_INI_NAME
        self._section_name = path.name
        self._session = (
            EditSession()
            if network_path
            else EditSession.from_value(self._read_filters_value())
        )
        # #1908/#4067: a festett ecset-maszk munkamenet-élettartamú — MÁS
        # képre váltva eldobódik (az eredeti sem tárolja). A
        # `paintMaskSupported` az új `_session`-ből számolódik, ezért a
        # `paintMaskChanged` jelzés csak a lánc betöltése UTÁN mehet ki;
        # közben még az előnézet regisztrációja előtt ürítjük a régi maszkot.
        self._paint_mask_kepvaltas(photo_id)
        if network_path:
            self._opening_crop, self._opening_crop_ini_readable = None, True
        else:
            self._opening_crop, self._opening_crop_ini_readable = (
                self._crop_reader.read(self._ini_path, self._section_name)
            )
        self._opening_crop_ops = self._crop_ops(self._session)
        self._camera_summary = "" if network_path else formatting.camera_summary_text(
            read_exif_details(path), QLocale(), formatting.fordit
        )
        # Perzisztens, rétegenkénti undo (#116 visszajelzés): a mentett lánc
        # maga a réteg-verem — minden elemhez visszavonás-lépés jár, fordított
        # sorrendben, képváltás és újranyitás után is.
        self._undo_stack = self._seed_undo_from_chain(self._session)
        self._redo_stack.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._redeye_regions = ()
        self._redeye_region_undo = []
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        # #448: a vágás-javaslatokhoz kért képarány (None = a
        # forráskép arányát tartjuk)
        self._crop_aspect: float | None = None
        self._brush_size = _DEFAULT_BRUSH_SIZE
        self._restore_text_overlay_state(read_ini=not network_path)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        if network_path:
            self._start_network_edit_state_load(
                generation, path, self._ini_path, self._section_name
            )


    def _start_network_edit_state_load(
        self, generation: int, image_path: Path, ini_path: Path, section_name: str
    ) -> None:
        """A hálózati kép méretét, ini-állapotát és EXIF-jét egy worker olvassa."""
        def worker() -> None:
            error = None
            try:
                document = self._load_ini_document_from_disk(ini_path)
                section = document.section(section_name)
                crop = section.get("crop") if section is not None else None
                crop_readable = True
            except OSError as exc:
                document = parse_document("")
                crop = None
                crop_readable = False
                error = str(exc)
                _log.warning("A hálózati .picasa.ini nem olvasható: %s", ini_path)
            size = self._read_image_size(image_path)
            details = _cached_exif_details(image_path)
            if details is None:
                details = read_exif_details(image_path)
                _cache_exif_details(image_path, details)
            result = (
                generation,
                str(image_path),
                document,
                crop,
                crop_readable,
                size,
                details,
                error,
            )
            with _NETWORK_EDIT_STATE_LOCK:
                self._network_edit_state_result = result
            QMetaObject.invokeMethod(
                self,
                "_apply_network_edit_state",
                QtNamespace.ConnectionType.QueuedConnection,
            )

        self._start_background(worker, name="picasapy-edit-file-read", busy=False)


    @Slot()
    def _apply_network_edit_state(self) -> None:
        """A háttérben beolvasott hálózati metaadat GUI-szálas átvétele."""
        with _NETWORK_EDIT_STATE_LOCK:
            result = getattr(self, "_network_edit_state_result", None)
            self._network_edit_state_result = None
        if result is None:
            return
        (
            generation,
            image_path,
            document,
            crop,
            crop_readable,
            size,
            details,
            error,
        ) = result
        if (
            generation != getattr(self, "_network_edit_generation", -1)
            or str(self._image_path) != image_path
        ):
            return
        self._network_edit_load_pending = False
        self._network_edit_load_failed = error is not None
        self._network_edit_load_error = error or ""
        self._cached_ini_document = document
        self._image_size = size
        loaded_session = EditSession.from_value(self._read_filters_value())
        if self._network_edit_filters_dirty_pending:
            loaded_session = EditSession(
                ops=loaded_session.ops + self._session.ops
            )
        self._session = loaded_session
        self._opening_crop = crop
        self._opening_crop_ini_readable = crop_readable
        self._opening_crop_ops = self._crop_ops(self._session)
        self._undo_stack = self._seed_undo_from_chain(self._session)
        self._redo_stack.clear()
        if not self._network_edit_text_dirty_pending:
            self._restore_text_overlay_state()
        self._camera_summary = formatting.camera_summary_text(
            details, QLocale(), formatting.fordit
        )
        filters_dirty = self._network_edit_filters_dirty_pending
        text_dirty = self._network_edit_text_dirty_pending
        self._network_edit_filters_dirty_pending = False
        self._network_edit_text_dirty_pending = False
        self._bump_revision()
        self._register_preview()
        self.toolsChanged.emit()
        if error:
            self.editSaveFailed.emit(error)
            return
        # A betöltés alatt tett szerkesztés eddig csak a memóriában állt:
        # most, a beolvasott ini-re fésülve kerül a lemezre.
        if filters_dirty:
            self._save()
        if text_dirty:
            self._save_text()


    @Slot()
    def endEdit(self) -> None:
        """Szerkesztés lezárása: leregisztrálás a previewnél, állapot ürítése.

        #546: a `_preview_job` léptetése érvényteleníti a futó háttér-
        rendert. Enélkül az a lezárt fotót a végén ÚJRA beregisztrálná (a
        10–30 MB-os dekódolt forrás visszakerülne az LRU-ba), és utólagos
        `revisionChanged`-et emitálna egy már üres szerkesztő-állapotra."""
        self._preview_job += 1
        self._network_edit_generation = getattr(
            self, "_network_edit_generation", 0
        ) + 1
        self._network_edit_load_pending = False
        if self._photo_id:
            self._provider.unregister(self._kulcs)
        self._memory_only = False
        self._photo_id = ""
        self._image_path = None
        self._image_size = None
        self._ini_path = None
        self._section_name = ""
        self._session = EditSession()
        self._camera_summary = ""
        self._undo_stack.clear()
        self._redo_stack.clear()
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._redeye_regions = ()
        self._redeye_region_undo = []
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False
        self._crop_aspect = None
        self._brush_size = _DEFAULT_BRUSH_SIZE
        self._text_overlay = None
        self._text_selected_index = None
        self._text_active = False
        self._text_overlay_visible = True
        self._text_draft = ""
        self._text_pending_pos = None
        self._text_fill_color = _DEFAULT_TEXT_FILL_COLOR
        self._text_outline_color = _DEFAULT_TEXT_OUTLINE_COLOR
        self._text_outline_thickness = _DEFAULT_TEXT_OUTLINE_THICKNESS
        self._text_fill_enabled = _DEFAULT_TEXT_FILL_ENABLED
        self._text_opacity = _DEFAULT_TEXT_OPACITY
        # #6688: az alapértelmezett családot a `_text_family` az első
        # olvasáskor számolja újra (az `endEdit` induláskor is lefut)
        self._text_family_value = None
        self._text_size_pt = _DEFAULT_TEXT_SIZE_PT
        self._text_size_edited = False
        self._text_bold = _DEFAULT_TEXT_BOLD
        self._text_italic = _DEFAULT_TEXT_ITALIC
        self._text_underline = _DEFAULT_TEXT_UNDERLINE
        self._text_align = _DEFAULT_TEXT_ALIGN
        self._bump_revision()
        self._bump_gpu_revision()
        self.toolsChanged.emit()


    def beginEditInMemory(self, photo_id: str, image_path: str) -> None:
        """#3014: munkamenet a mentett lánccal, de ini-írás NÉLKÜL.

        Az „aa" mód nem kijelölt fele: a kép jelenlegi láncával indul
        (`docs/specs/ui-audit-editor.md` 4/b.1), a szerkesztései csak
        memóriában élnek, amíg a kilépéskori döntés ki nem írja
        (`persistChain`). Nem `@Slot`: a QML a `SecondPreview` hídján éri el."""
        self.beginEdit(photo_id, image_path)
        self._memory_only = True


    def link_aa_partner(self, partner: EditController) -> None:
        """#3649: a két „aa"-fél vezérlőjének összekötése (`application.py`).

        A `swapAaFocus` ezen át éri el a párt — enélkül a fókuszváltás nem
        tudná, KIVEL cserélje a festett maszkot."""
        self._aa_partner = partner


    @Property(str, notify=_Signals.toolsChanged)
    def chainValue(self) -> str:
        """#3014: a munkamenet jelenlegi `filters=` értéke (üres = nincs lánc).

        Az „aa" mód ebből dönti el, módosult-e egy fél a belépés óta, és ezt
        cseréli a fókuszváltáskor a két fél között."""
        return self._session.to_value()


    def _apply_chain_value(self, value: str) -> None:
        """A lánc lecserélése — az eszközpuffer sorsát a hívó dönti el.

        `setChainValue` ürít, `swapAaFocus` (#3649) a párral cserél."""
        self._require_active()
        self._session = EditSession.from_value(value)
        self._undo_stack = self._seed_undo_from_chain(self._session)
        self._redo_stack.clear()
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def setChainValue(self, value: str) -> None:
        """#3014: a lánc lecserélése — a festett maszkot és az eszközpuffert
        ÜRÍTI (a #3649 `swapAaFocus`-a helyette a párral cseréli).

        A visszavonás-verem az új lánc rétegeiből épül újra — ugyanúgy, mint
        egy újranyitáskor (`beginEdit`). Memóriás munkamenetben nem ír.

        #3649: NEM `@Slot` — a QML az „aa" fókuszváltáshoz a `swapAaFocus`-t
        hívja, ezt csak a Python-oldal (tesztek, `beginEdit` társai) hívja
        közvetlenül."""
        self._apply_chain_value(value)
        # A fél ALKALMAZATLAN eszközpuffere a régi lánchoz tartozott — a
        # csere után a másik fél láncára kerülne (#3644 3.). Ugyanúgy ürül,
        # mint egy újranyitáskor (`beginEdit`). Az „aa" fókuszváltás nem ezt
        # hívja: az a festett maszkot megőrzi (`swapAaFocus`, #3649).
        self._reset_tool_buffers()
        if not self._paint_mask.ures:
            self._paint_mask.torold()
            self.paintMaskChanged.emit()


    @Slot()
    def swapAaFocus(self) -> None:
        """#3649: az „aa" mód fókuszváltása — a lánc cseréje mellett a fél
        FESTETT MASZKJA is a párjával cserélődik (nem ürül), hogy a félkész
        festés a saját felén megmaradjon.

        A festés NEM része a `chainValue`-nak, ezért a korai kilépés is a
        vonásokat nézi, nem csak a láncot — azonos láncnál is lehet
        csereigény, ha csak az egyik fél festett (code review lelet #3).

        A maszkot a lánc cseréje ELŐTT visszük át: az `_apply_chain_value`
        (`_save()`-en át) azonnal új előnézetet kér, és ha az még a RÉGI
        festéssel menne ki az ÚJ lánccal összepárosítva, a másik fél
        pillanatra a rossz maszkkal látszana (code review lelet #2).

        A retusálás/vörösszem alkalmazatlan puffere továbbra is ürül: az a
        modális eszköz bezárásakor (QML `retouchActive`/`redeyeActive` ->
        `false`, ami `exitRetouchTool`/`exitRedeyeTool`-t hív) amúgy is
        elvész, ugyanúgy, mint más fotóra lépéskor (`docs/specs/
        ui-audit-editor.md` 4/b.1) — ezt nem ez a hívás dobja el.

        Pár nélkül (`link_aa_partner` hiányában) no-op."""
        partner = self._aa_partner
        if partner is None:
            return
        my_chain = self.chainValue
        partner_chain = partner.chainValue
        if my_chain == partner_chain and self._paint_mask.vonasok == partner._paint_mask.vonasok:
            return
        self._swap_paint_with(partner)
        self._apply_chain_value(partner_chain)
        self._reset_tool_buffers()
        self.paintMaskChanged.emit()
        partner._apply_chain_value(my_chain)
        partner._reset_tool_buffers()
        partner.paintMaskChanged.emit()


    def _reset_tool_buffers(self) -> None:
        """A retusálás- és a vörösszem-eszköz alkalmazatlan pufferének ürítése."""
        self._retouch_patches = ()
        self._retouch_target = None
        self._retouch_patch_undo = []
        self._retouch_patch_redo = []
        self._redeye_regions = ()
        self._redeye_region_undo = []
        self._redeye_eye_circles = ()
        self._redeye_eye_image_size = None
        self._redeye_eye_overlay_size = None
        self._redeye_eye_to_overlay = AZONOSSAG
        self._redeye_full_image_fallback = False
        self._redeye_found = -1
        self._redeye_can_reapply_auto = False
        self._redeye_reset_message = False


    @Slot(str)
    def toggleTool(self, name: str) -> None:
        """Paraméter nélküli szűrő alkalmazása (#116).

        Egygombos javítás (enhance/autolight/autocolor): append-only réteg a
        lánc végére; ha ugyanez a szűrő a lánc utolsó eleme, a hívás no-op
        (a gomb ilyenkor a UI-ban tiltott — ez a védőkorlát). A redeye
        teljes képes be/ki kapcsoló a régió-alapú eszközig."""
        self._require_active()
        key = name.casefold()
        if key in _ONE_SHOT_NAMES:
            if self._session.last_is(key):
                return
            self._push_undo(key)
            self._session = self._session.apply(key)
        elif key in _TOGGLE_NAMES:
            self._push_undo(key)
            self._session = self._session.toggle(key)
        else:
            raise ValueError(f"Érvénytelen szerkesztő-eszköz: {name!r}")
        self._save()
        self._bump_revision()
        self.toolsChanged.emit()


    def _require_active(self) -> None:
        if not self._photo_id or self._image_path is None:
            raise ValueError("Nincs aktív szerkesztés (beginEdit hívása szükséges)")
