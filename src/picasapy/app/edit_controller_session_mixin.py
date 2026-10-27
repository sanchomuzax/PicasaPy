"""A szerkesztési munkamenet, eszközváltás és effektlánc kezelése."""

from __future__ import annotations

from typing import TYPE_CHECKING

from .edit_controller_shared import (
    AZONOSSAG,
    EditSession,
    PICASA_INI_NAME,
    Path,
    Property,
    QLocale,
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
    _MOD_NINCS_KITOLTES,
    _ONE_SHOT_NAMES,
    _TOGGLE_NAMES,
    _argb_to_rgb,
    alignment_name,
    default_family,
    formatting,
    read_exif_details,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

if TYPE_CHECKING:
    from .edit_controller import EditController


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
        self._image_size = self._read_image_size(path)
        self._ini_path = path.parent / PICASA_INI_NAME
        self._section_name = path.name
        self._session = EditSession.from_value(self._read_filters_value())
        # #1908/#4067: a festett ecset-maszk munkamenet-élettartamú — MÁS
        # képre váltva eldobódik (az eredeti sem tárolja). A
        # `paintMaskSupported` az új `_session`-ből számolódik, ezért a
        # `paintMaskChanged` jelzés csak a lánc betöltése UTÁN mehet ki;
        # közben még az előnézet regisztrációja előtt ürítjük a régi maszkot.
        self._paint_mask_kepvaltas(photo_id)
        self._opening_crop, self._opening_crop_ini_readable = (
            self._crop_reader.read(self._ini_path, self._section_name)
        )
        self._opening_crop_ops = self._crop_ops(self._session)
        self._camera_summary = formatting.camera_summary_text(
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
        self._text_overlay = self._read_text_overlay()
        self._text_selected_index = None
        self._text_active = (
            self._read_text_active() if self._text_overlay is not None else False
        )
        self._text_overlay_visible = True
        self._text_draft = ""
        self._text_pending_pos = None
        # A mentett felirat KÉT színe visszatölthető (#371) — a többi
        # stílus-beállításnak nincs `text=` mezője, azok alapértékre állnak.
        loaded = self._text_overlay.primary if self._text_overlay else None
        self._text_fill_color = (
            _argb_to_rgb(loaded.style.fill_argb) if loaded else _DEFAULT_TEXT_FILL_COLOR
        )
        self._text_outline_color = (
            _argb_to_rgb(loaded.style.outline_argb)
            if loaded
            else _DEFAULT_TEXT_OUTLINE_COLOR
        )
        self._text_outline_thickness = _DEFAULT_TEXT_OUTLINE_THICKNESS
        # #2108: a mód 1-es értéke azt jelenti, hogy NINCS kitöltés.
        self._text_fill_enabled = (
            loaded.style.fill_mode != _MOD_NINCS_KITOLTES
            if loaded
            else _DEFAULT_TEXT_FILL_ENABLED
        )
        self._text_opacity = _DEFAULT_TEXT_OPACITY
        self._text_family = (
            loaded.font if loaded is not None and loaded.font else default_family()
        )
        self._text_size_pt = _DEFAULT_TEXT_SIZE_PT
        self._text_size_edited = False
        self._text_bold = _DEFAULT_TEXT_BOLD
        self._text_italic = _DEFAULT_TEXT_ITALIC
        self._text_underline = _DEFAULT_TEXT_UNDERLINE
        # #2108: a mentett igazítás visszatölt — eddig minden újranyitás
        # `left`-re esett vissza, akkor is, ha a fájlban `right` állt.
        self._text_align = (
            alignment_name(loaded.style.alignment)
            if loaded
            else _DEFAULT_TEXT_ALIGN
        )
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def endEdit(self) -> None:
        """Szerkesztés lezárása: leregisztrálás a previewnél, állapot ürítése.

        #546: a `_preview_job` léptetése érvényteleníti a futó háttér-
        rendert. Enélkül az a lezárt fotót a végén ÚJRA beregisztrálná (a
        10–30 MB-os dekódolt forrás visszakerülne az LRU-ba), és utólagos
        `revisionChanged`-et emitálna egy már üres szerkesztő-állapotra."""
        self._preview_job += 1
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
        self._text_family = default_family()
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
