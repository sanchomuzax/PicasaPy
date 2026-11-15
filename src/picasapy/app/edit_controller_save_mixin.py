"""A szerkesztési lánc és a szövegréteg mentése."""

from __future__ import annotations

from .edit_controller_shared import (
    FilterWriteError,
    TextOverlay,
    _WRITE_ERRORS,
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
    _argb_to_rgb,
    alignment_name,
    default_family,
    _log,
    encode_rect64,
    is_folder_writable,
    load_or_empty,
    parse_text,
    parse_text_active,
    serialize_text,
    serialize_text_active,
    with_backuphash,
    _controller_update_document,
)

class EditControllerSaveMixin:
    """A szerkesztési lánc és a szövegréteg mentése."""

    def _load_ini_document_from_disk(self, path=None):
        """Egyetlen ini-dokumentum betöltése a közös ini API-val."""
        target = self._ini_path if path is None else path
        if target is None:
            return None
        return load_or_empty(target)

    def _current_ini_document(self):
        """A munkamenet már betöltött ini-je, vagy egy új közös API-olvasás."""
        if self._ini_path is None:
            return None
        document = getattr(self, "_cached_ini_document", None)
        if document is None:
            document = self._load_ini_document_from_disk()
            self._cached_ini_document = document
        return document

    def _restore_text_overlay_state(self, *, read_ini: bool = True) -> None:
        """A mentett feliratréteg betöltése vagy alaphelyzetbe állítása."""
        overlay = self._read_text_overlay() if read_ini else None
        self._text_overlay = overlay
        self._text_selected_index = None
        self._text_active = (
            self._read_text_active() if overlay is not None and read_ini else False
        )
        self._text_overlay_visible = True
        self._text_draft = ""
        self._text_pending_pos = None
        loaded = overlay.primary if overlay else None
        self._text_fill_color = (
            _argb_to_rgb(loaded.style.fill_argb)
            if loaded
            else _DEFAULT_TEXT_FILL_COLOR
        )
        self._text_outline_color = (
            _argb_to_rgb(loaded.style.outline_argb)
            if loaded
            else _DEFAULT_TEXT_OUTLINE_COLOR
        )
        self._text_outline_thickness = _DEFAULT_TEXT_OUTLINE_THICKNESS
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
        self._text_align = (
            alignment_name(loaded.style.alignment)
            if loaded
            else _DEFAULT_TEXT_ALIGN
        )

    def persistChain(self) -> None:
        """#3014: a memóriában élő lánc kiírása a `.picasa.ini`-be.

        Az „aa" mód kilépésekor fut, ha a döntés a memóriás felet tartja meg.
        Munkamenet nélkül no-op."""
        if not self._photo_id or self._ini_path is None:
            return
        self._memory_only = False
        self._save()


    def _read_filters_value(self) -> str:
        if self._ini_path is None:
            return ""
        document = self._current_ini_document()
        section = document.section(self._section_name) if document else None
        return (section.get("filters") if section else None) or ""


    def _read_text_overlay(self) -> TextOverlay | None:
        """A mentett `text=` érték típusos alakja, vagy None ha nincs (vagy
        nem értelmezhető, #301-elv — a generikus round-trip réteg ilyenkor
        érintetlenül megőrzi, amíg ez a modul nem szerkeszti)."""
        if self._ini_path is None:
            return None
        document = self._current_ini_document()
        section = document.section(self._section_name) if document else None
        raw = section.get("text") if section else None
        if not raw:
            return None
        try:
            return parse_text(raw)
        except ValueError:
            return None


    def _read_text_active(self) -> bool:
        """A mentett `textactive=` érték — hiányzó kulcsnál a MEGLÉVŐ
        `text=` bejegyzést alapból aktívnak vesszük (a Picasa-doksi szerint
        ez a gyakoribb eset)."""
        if self._ini_path is None:
            return True
        document = self._current_ini_document()
        section = document.section(self._section_name) if document else None
        raw = section.get("textactive") if section else None
        return parse_text_active(raw) if raw is not None else True


    def _save(self) -> None:
        assert self._ini_path is not None
        if getattr(self, "_network_edit_load_pending", False):
            self._network_edit_filters_dirty_pending = True
            return
        if getattr(self, "_network_edit_load_failed", False):
            self.editSaveFailed.emit(
                getattr(self, "_network_edit_load_error", "A hálózati ini nem olvasható")
            )
            return
        if self._memory_only:
            # #3014: az „aa" mód nem kijelölt fele — csak az előnézet frissül
            self._register_preview_async()
            return
        if not self._check_writable_before_save():
            return

        def mutate(document):
            if self._session.is_empty():
                document = document.with_removed(self._section_name, "filters")
            else:
                document = document.with_value(
                    self._section_name, "filters", self._session.to_value()
                )
            # #5854: a közös író a szerkesztési lánc frissítésekor a kép
            # szakaszának backuphash-ét is ugyanebben az ini-írásban állítja.
            document = with_backuphash(document, self._section_name)
            # Picasa-paritás (#73): a vágás a filters= mellett külön
            # crop=rect64(...) kulcsba is kerül — a Picasa 3.x is így ír.
            crop = self.crop()
            if crop is not None:
                document = document.with_value(
                    self._section_name, "crop", f"rect64({encode_rect64(crop)})"
                )
            else:
                document = document.with_removed(self._section_name, "crop")
            return document

        # #137: útvonalanként soros mentés — az előzetes ujjlenyomat-
        # ellenőrzésig észlelt másik kulcs újratöltést és újrajátszást kap.
        # A check/save közti külső írás teljes kizárását a fájlrendszer nem garantálja.
        try:
            _controller_update_document(self._ini_path, mutate, backup=True)
            self._cached_ini_document = None
        except FilterWriteError as error:
            # #643: NEM lemezhiba — az őr utasította vissza a láncot, a fájl
            # hozzá sem lett érintve. Saját csatornán megy ki, hogy a
            # felhasználó a valódi okot olvassa (ld. `editChainRejected`).
            _log.warning("A szerkesztési lánc kiírását az őr visszautasította: %s", error)
            self.editChainRejected.emit(str(error))
            return
        except _WRITE_ERRORS as error:
            self.editSaveFailed.emit(str(error))
            return
        # #644: a kiírt láncot a saját, TARTÓS naplónkba is felvesszük — ez az
        # egyetlen nyomunk, ha a párhuzamosan futó Picasa később felülírja az
        # init a saját adatbázis-rekordjával.
        if self._image_path is not None:
            self.chainSaved.emit(
                str(self._image_path), self._session.to_value()
            )
        # #514: a mentett lánc újrarenderelése HÁTTÉRSZÁLON — ez az a hely,
        # ahol egy lassú effekt (Lomo, Polaroid…) korábban befagyasztotta a
        # felületet. A csúszka-húzás alatti élő előnézet ettől független
        # (`_register_preview`, szinkron).
        self._register_preview_async()


    def _save_text(self) -> None:
        """A `text=`/`textactive=` kulcsok írása/törlése (#148) — külön az
        `_save()`-től, mert ezek NEM a `filters=` láncba tartoznak, hanem
        önálló, szekció-szintű kulcsok (ld. `picasapy.ini.text_overlay`)."""
        assert self._ini_path is not None
        if getattr(self, "_network_edit_load_pending", False):
            self._network_edit_text_dirty_pending = True
            return
        if getattr(self, "_network_edit_load_failed", False):
            self.editSaveFailed.emit(
                getattr(self, "_network_edit_load_error", "A hálózati ini nem olvasható")
            )
            return
        if not self._check_writable_before_save():
            return

        def mutate(document):
            has_content = self._text_overlay and any(
                block.content for block in self._text_overlay.blocks
            )
            if not has_content:
                document = document.with_removed(self._section_name, "text")
                document = document.with_removed(self._section_name, "textactive")
            else:
                document = document.with_value(
                    self._section_name, "text", serialize_text(self._text_overlay)
                )
                document = document.with_value(
                    self._section_name,
                    "textactive",
                    serialize_text_active(self._text_active),
                )
            return document

        try:
            _controller_update_document(self._ini_path, mutate, backup=True)
            self._cached_ini_document = None
        except _WRITE_ERRORS as error:
            self.editSaveFailed.emit(str(error))
            return
        self._register_preview()


    def _check_writable_before_save(self) -> bool:
        """#459: a mentés ELŐTTI, gyors csak-olvasható-ellenőrzés — az
        eredeti Picasa itt ajánlotta fel a mappa-másolást (*"This file is
        read only. In order to edit this file, Picasa needs to copy the
        file's folder. Would you like to make a copy now?"*). A tényleges
        másolás NEM készült el (a jegy szerint külön, nagyobb munka) — csak
        a FELISMERÉS és a látható jelzés (`editSaveReadOnly`), hogy a
        felhasználó NE néma bukást lásson. Visszaadja, hogy folytatható-e
        a mentés."""
        assert self._ini_path is not None
        folder = self._ini_path.parent
        if is_folder_writable(folder):
            return True
        self.editSaveReadOnly.emit()
        return False

