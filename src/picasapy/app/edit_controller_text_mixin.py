"""A szöveg-overlay tulajdonságai, elhelyezése és stílusa."""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QMetaObject, Qt
from picasapy.ini.text_overlay import DEFAULT_FAMILY
from picasapy.app.text_rotation import rotation_from_drag, rotated_top_left

from .edit_controller_shared import (
    BETUMERETEK,
    Property,
    Slot,
    TextBlock,
    TextGeometry,
    TextOverlay,
    TextOverlaySpec,
    TextStyle,
    _DEFAULT_TEXT_OPACITY,
    _MOD_NINCS_KITOLTES,
    _argb_to_rgb,
    _clamp01,
    _hex_to_rgb,
    _rgb_to_argb,
    _rgb_to_hex,
    alignment_code,
    alignment_name,
    fill_mode_from,
    meret_taroltbol,
    replace,
    tarolt_meret,
    _controller_family_labels,
)

from .edit_controller_signals import EditControllerSignalsMixin as _Signals

_FONT_FAMILIES_LOCK = threading.Lock()
_log = logging.getLogger(__name__)


class EditControllerTextMixin:
    """A szöveg-overlay tulajdonságai, elhelyezése és stílusa."""

    @property
    def _text_family(self) -> str:
        """A szöveg-eszköz betűcsaládja; katalógust csak használatkor kér."""
        if self._text_family_value is None:
            return DEFAULT_FAMILY
        return self._text_family_value

    @_text_family.setter
    def _text_family(self, value: str | None) -> None:
        self._text_family_value = value

    @Property(str, notify=_Signals.textDraftChanged)
    def textDraft(self) -> str:
        """A szöveg-eszköz megnyitásakor a mezőbe töltendő piszkozat — a
        mentett tartalommal indul (ha van), a szerkesztés alatt a
        `setTextDraft` frissíti."""
        return self._text_draft


    @Property(bool, notify=_Signals.textClearedChanged)
    def textCleared(self) -> bool:
        """Törölve lett-e a felirat a piszkozatban a Clear All gombbal (#7407)."""
        return getattr(self, "_text_cleared", False)


    @Property(bool, notify=_Signals.revisionChanged)
    def textHasPlacement(self) -> bool:
        """Van-e kijelölt vagy új pozícióra váró szövegdoboz."""
        return self._text_pending_pos is not None or self._text_selected_index is not None


    @Property("QVariant", notify=_Signals.revisionChanged)
    def textEditPlacement(self) -> dict:
        """HOL áll a képre gépelhető szövegdoboz (#7380): a kattintott pont,
        vagy - ha nincs új kattintás - a kijelölt mentett felirat bal felső
        sarka, a képre normalizálva. Üres szótár, ha nincs szerkesztett hely.
        """
        if self._text_pending_pos is not None:
            x, y = self._text_pending_pos
            return {"x": x, "y": y}
        index = self._text_selected_index
        overlay = self._text_overlay
        if index is None or overlay is None or not 0 <= index < len(overlay.blocks):
            return {}
        block = overlay.blocks[index]
        if not block.content:
            return {}
        return {"x": block.geometry.x, "y": block.geometry.y}


    @Slot(bool)
    def setTextInlineEditing(self, active: bool) -> None:
        """A képre gépelhető QML-doboz látszik-e (#7380).

        Ha igen, a szerkesztett szöveget a doboz maga rajzolja, ezért az
        előnézeti raszter azt a blokkot nem rajzolja (különben a két szöveg
        egymásra csúszna). Alapból kikapcsolt: a Python-oldali hívók a
        piszkozatot változatlanul a raszteren látják.
        """
        active = bool(active)
        if self._text_inline_editing == active:
            return
        self._text_inline_editing = active
        self._register_preview()
        self._bump_revision()


    @Property(int, notify=_Signals.textSelectedIndexChanged)
    def textSelectedIndex(self) -> int:
        """A kiválasztott mentett doboz sorszáma, vagy -1, ha nincs."""
        return self._text_selected_index if self._text_selected_index is not None else -1


    @Property("QVariantList", notify=_Signals.textOverlayItemsChanged)
    def textOverlayItems(self) -> list[dict]:
        """A QML kattintásos kijelölőinek képre normalizált adatai."""
        if not self._text_overlay_visible or not self._text_active or not self._text_overlay:
            return []
        items = []
        for index, block in enumerate(self._text_overlay.blocks):
            if not block.content:
                continue
            items.append(
                {
                    "index": index,
                    "content": (
                        self._text_draft
                        if index == self._text_selected_index
                        else block.content
                    ),
                    "x": (
                        self._text_pending_pos[0]
                        if index == self._text_selected_index
                        and self._text_pending_pos is not None
                        else block.geometry.x
                    ),
                    "y": (
                        self._text_pending_pos[1]
                        if index == self._text_selected_index
                        and self._text_pending_pos is not None
                        else block.geometry.y
                    ),
                    "size": (
                        self._text_size_pt
                        if index == self._text_selected_index
                        else block.geometry.size * 360.0
                    ),
                    "font": (
                        self._text_family if index == self._text_selected_index
                        else block.font or DEFAULT_FAMILY
                    ),
                    "bold": (
                        self._text_bold if index == self._text_selected_index
                        else block.style.weight >= 700
                    ),
                    "italic": (
                        self._text_italic if index == self._text_selected_index
                        else block.style.italic
                    ),
                    "underline": (
                        self._text_underline if index == self._text_selected_index
                        else block.style.underline
                    ),
                    "align": (
                        self._text_align if index == self._text_selected_index
                        else alignment_name(block.style.alignment)
                    ),
                    "rotation": block.geometry.rotation,
                }
            )
        return items


    @Property(bool, notify=_Signals.hasTextOverlayChanged)
    def hasTextOverlay(self) -> bool:
        """Van-e MENTETT, aktív szöveg-overlay — a „Visszavonás: Szöveg"
        felirathoz és a UI állapot-jelzéséhez."""
        return (
            self._text_active
            and self._text_overlay is not None
            and any(block.content for block in self._text_overlay.blocks)
        )


    @Property(bool, notify=_Signals.textOverlayVisibleChanged)
    def textOverlayVisible(self) -> bool:
        """A mentett szöveg látszik-e az előnézeten ebben a munkamenetben."""
        return self._text_overlay_visible


    @Property(str, notify=_Signals.textFillColorChanged)
    def textFillColor(self) -> str:
        """A kitöltés-szín `#rrggbb` alakban."""
        return _rgb_to_hex(self._text_fill_color)


    @Property(str, notify=_Signals.textOutlineColorChanged)
    def textOutlineColor(self) -> str:
        """A körvonal-szín `#rrggbb` alakban (a fill-től KÜLÖN választható)."""
        return _rgb_to_hex(self._text_outline_color)


    @Property(float, notify=_Signals.textOutlineThicknessChanged)
    def textOutlineThickness(self) -> float:
        """A körvonal vastagsága `[0, 1]` — `0` esetén nincs körvonal."""
        return self._text_outline_thickness


    @Property(bool, notify=_Signals.textFillEnabledChanged)
    def textFillEnabled(self) -> bool:
        """Kitöltve jelenjen-e meg a szöveg — `False` a „Don't show the
        solid fill color (show outline only)" kapcsolónak felel meg."""
        return self._text_fill_enabled


    @Property(float, notify=_Signals.textOpacityChanged)
    def textOpacity(self) -> float:
        """A szöveg-réteg átlátszósága [0..1] — `1.0` (alapérték) a
        teljesen fedő, korábbi viselkedés."""
        return self._text_opacity


    @Property("QVariant", notify=_Signals.textFontCatalogueChanged)
    def textFontFamilies(self):
        """A betűtípus-lenyíló adata: `key` + megjelenő `label`.

        A katalógust a Qt rendszer-betűtípus-adatbázisa adja, nem kézzel a
        QML-be írt rögzített lista."""
        families = getattr(self, "_text_font_families", None)
        if families is None:
            self._queue_text_font_families()
            return []
        return [dict(family) for family in families]

    @staticmethod
    def _preferred_text_family(families) -> str:
        available = {item["key"].casefold(): item["key"] for item in families}
        for preferred in ("Arial", "Liberation Sans", "DejaVu Sans"):
            if preferred.casefold() in available:
                return available[preferred.casefold()]
        return families[0]["key"] if families else DEFAULT_FAMILY

    def _default_text_family(self) -> str:
        families = getattr(self, "_text_font_families", None)
        if families is None:
            self._queue_text_font_families()
            return DEFAULT_FAMILY
        return self._preferred_text_family(families)

    def _queue_text_font_families(self) -> None:
        """A rendszercsaládokat egyszer, háttérben kéri le."""
        if getattr(self, "_text_font_families", None) is not None:
            return
        if getattr(self, "_text_font_families_pending", False):
            return
        self._text_font_families_pending = True

        def worker() -> None:
            try:
                families = tuple(dict(item) for item in _controller_family_labels())
            except Exception:
                _log.exception("A rendszer betűcsalád-listája nem kérdezhető le")
                families = ()
            with _FONT_FAMILIES_LOCK:
                self._text_font_families_result = families
            QMetaObject.invokeMethod(
                self,
                "_apply_text_font_families",
                Qt.ConnectionType.QueuedConnection,
            )

        self._start_background(
            worker, name="picasapy-font-family-list", busy=False
        )

    @Slot()
    def _apply_text_font_families(self) -> None:
        """A worker eredményét a GUI-szálon gyorsítótárazza."""
        with _FONT_FAMILIES_LOCK:
            families = getattr(self, "_text_font_families_result", None)
            self._text_font_families_result = None
        if families is None:
            return
        self._text_font_families = families
        self._text_font_families_pending = False
        if self._text_family_value is None:
            self._text_family_value = self._preferred_text_family(families)
        self.textFontCatalogueChanged.emit()


    @Property(str, notify=_Signals.textFontFamilyChanged)
    def textFontFamily(self) -> str:
        return self._text_family


    @Property(int, notify=_Signals.textFontSizeChanged)
    def textFontSize(self) -> int:
        """A választott betűméret (a `BETUMERETEK` egyike)."""
        return self._text_size_pt


    @Property("QVariantList", constant=True)
    def fontSizeChoices(self) -> list:
        """A 16 választható méret — a felület legördülőjének modellje."""
        return list(BETUMERETEK)


    @Property(bool, notify=_Signals.textBoldChanged)
    def textBold(self) -> bool:
        return self._text_bold


    @Property(bool, notify=_Signals.textItalicChanged)
    def textItalic(self) -> bool:
        return self._text_italic


    @Property(bool, notify=_Signals.textUnderlineChanged)
    def textUnderline(self) -> bool:
        return self._text_underline


    @Property(str, notify=_Signals.textAlignChanged)
    def textAlign(self) -> str:
        """`left` · `center` · `right` — a Picasa három igazítás-gombja."""
        return self._text_align


    @Slot(str)
    def setTextFontFamily(self, value: str) -> None:
        """A teljes rendszer-betűcsaládnév beállítása; élő előnézettel."""
        self._require_active()
        self._text_family = value.strip() or None
        self._refresh_text_preview()


    @Slot(int)
    def setTextFontSize(self, value: int) -> None:
        """A betűméret beállítása; élő előnézettel.

        A listán kívüli értéket a LEGKÖZELEBBIRE igazítjuk: a fogantyúval
        átméretezett feliratok nem egész listaértéket adnak (#2287), a
        választónak viszont akkor is mutatnia kell valamit.
        """
        self._require_active()
        if value <= 0:
            raise ValueError(f"A textFontSize pozitív kell legyen: {value}")
        self._text_size_pt = min(BETUMERETEK, key=lambda e: abs(e - int(value)))
        self._text_size_edited = True
        self._refresh_text_preview()


    @Slot(bool)
    def setTextBold(self, value: bool) -> None:
        self._require_active()
        self._text_bold = bool(value)
        self._refresh_text_preview()


    @Slot(bool)
    def setTextItalic(self, value: bool) -> None:
        self._require_active()
        self._text_italic = bool(value)
        self._refresh_text_preview()


    @Slot(bool)
    def setTextUnderline(self, value: bool) -> None:
        self._require_active()
        self._text_underline = bool(value)
        self._refresh_text_preview()


    @Slot(str)
    def setTextAlign(self, value: str) -> None:
        """A sorok igazítása; ismeretlen érték elutasítva (a rajzoló is
        azt tenné, csak később és zavarosabb hibával)."""
        self._require_active()
        if value not in ("left", "center", "right"):
            raise ValueError(f"Ismeretlen szöveg-igazítás: {value!r}")
        self._text_align = value
        self._refresh_text_preview()


    def _refresh_text_preview(self) -> None:
        """A szöveg-stílus változása utáni közös lezárás — élő előnézet,
        revízió-léptetés, jelzés (a stílus-slotok mind ezt hívják)."""
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textOverlayItemsChanged.emit()


    @Slot(str)
    def setTextFillColor(self, value: str) -> None:
        """A kitöltés-szín beállítása (`#rrggbb`); élő előnézettel."""
        self._require_active()
        self._text_fill_color = _hex_to_rgb(value)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(str)
    def setTextOutlineColor(self, value: str) -> None:
        """A körvonal-szín beállítása (`#rrggbb`); élő előnézettel."""
        self._require_active()
        self._text_outline_color = _hex_to_rgb(value)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(float)
    def setTextOutlineThickness(self, value: float) -> None:
        """A körvonal-vastagság beállítása `[0, 1]`-ben; élő előnézettel."""
        self._require_active()
        if value < 0:
            raise ValueError(f"A textOutlineThickness nem lehet negatív: {value}")
        if value > 1:
            raise ValueError(
                f"A textOutlineThickness legfeljebb 1 lehet: {value}"
            )
        self._text_outline_thickness = float(value)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(bool)
    def setTextFillEnabled(self, value: bool) -> None:
        """A kitöltés ki/be kapcsolása; élő előnézettel."""
        self._require_active()
        self._text_fill_enabled = value
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(float)
    def setTextOpacity(self, value: float) -> None:
        """Az átlátszóság beállítása [0..1]; élő előnézettel."""
        self._require_active()
        if not 0.0 <= value <= 1.0:
            raise ValueError(f"A textOpacity a [0..1] tartományon kívül: {value}")
        self._text_opacity = value
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot()
    def enterTextTool(self) -> None:
        """A szöveg-eszköz megnyitása: az első mentett doboz kijelölődik."""
        self._require_active()
        self._text_initial_overlay = self._text_overlay
        self._text_initial_active = self._text_active
        self._text_cleared = False
        primary = self._text_overlay.primary if self._text_overlay else None
        self._text_selected_index = 0 if primary and primary.content else None
        self._text_rotation_drag = None
        self._text_draft = primary.content if primary else ""
        self._text_pending_pos = None
        self._text_inline_editing = False
        if primary:
            self._load_text_settings_from_block(primary)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()
        self.textClearedChanged.emit()


    @Slot(int)
    def selectTextOverlay(self, index: int) -> None:
        """A képen kiválasztott szövegdoboz szerkesztésre megnyitása."""
        self._require_active()
        if self._text_overlay is None or not 0 <= index < len(self._text_overlay.blocks):
            return
        block = self._text_overlay.blocks[index]
        self._text_selected_index = index
        self._text_rotation_drag = None
        self._text_pending_pos = None
        self._text_draft = block.content
        self._load_text_settings_from_block(block)
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()


    @Slot(float, float, float, float, float, float, float)
    def beginTextRotation(
        self,
        pointer_angle: float,
        center_x: float,
        center_y: float,
        width: float,
        height: float,
        scale_x: float,
        scale_y: float,
    ) -> None:
        """Rögzíti a húzás szögét és a kép képpontméretű szöveggeometriáját."""
        self._require_active()
        index = self._text_selected_index
        overlay = self._text_overlay
        if index is None or overlay is None or not 0 <= index < len(overlay.blocks):
            return
        if width <= 0 or height <= 0 or scale_x <= 0 or scale_y <= 0:
            return
        self._text_rotation_drag = (
            index,
            float(pointer_angle),
            overlay.blocks[index].geometry.rotation,
            float(center_x),
            float(center_y),
            float(width),
            float(height),
            float(scale_x),
            float(scale_y),
        )


    @Slot(float)
    def updateTextRotation(self, pointer_angle: float) -> None:
        """A húzás végpontjából frissíti a forgatást és a befoglaló sarkát."""
        drag = self._text_rotation_drag
        overlay = self._text_overlay
        if (
            drag is None
            or overlay is None
            or drag[0] != self._text_selected_index
            or not 0 <= drag[0] < len(overlay.blocks)
        ):
            return
        (
            index,
            start_angle,
            start_rotation,
            center_x,
            center_y,
            width,
            height,
            scale_x,
            scale_y,
        ) = drag
        rotation = rotation_from_drag(start_angle, float(pointer_angle), start_rotation)
        x, y = rotated_top_left(
            center_x=center_x,
            center_y=center_y,
            width=width,
            height=height,
            angle=rotation,
            scale_x=scale_x,
            scale_y=scale_y,
        )
        blocks = list(overlay.blocks)
        block = blocks[index]
        blocks[index] = replace(
            block,
            geometry=replace(block.geometry, x=x, y=y, rotation=rotation),
        )
        self._text_overlay = TextOverlay(blocks=tuple(blocks))
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textOverlayItemsChanged.emit()


    @Slot()
    def endTextRotation(self) -> None:
        """Lezárja a húzást; a piszkozat Apply-ig szerkesztetlenül marad."""
        self._text_rotation_drag = None


    @Slot()
    def exitTextTool(self) -> None:
        """A Szöveg eszköz bezárása (Mégse): a piszkozat eldobása, visszaáll
        a megnyitáskori mentett előnézetre és állapotra (#7407)."""
        self._require_active()
        if hasattr(self, "_text_initial_overlay"):
            self._text_overlay = self._text_initial_overlay
            self._text_active = self._text_initial_active
        self._text_rotation_drag = None
        self._text_cleared = False
        self._text_selected_index = None
        self._text_pending_pos = None
        self._text_draft = ""
        self._text_inline_editing = False
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.hasTextOverlayChanged.emit()
        self.textDraftChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()
        self.textClearedChanged.emit()


    @Slot(str)
    def setTextDraft(self, content: str) -> None:
        """A szövegmező tartalmának élő követése — ha már van kattintott
        pozíció, az élő előnézet is frissül; NEM ír inibe."""
        self._require_active()
        self._text_draft = content
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textOverlayItemsChanged.emit()


    def previewTextPlacement(self, x: float, y: float) -> None:
        """Python API a piszkozat helyének előnézetéhez; QML külön slotot használ."""
        self._require_active()
        self._text_pending_pos = (_clamp01(x), _clamp01(y))
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()


    @Slot(float, float)
    def previewNewTextPlacement(self, x: float, y: float) -> None:
        """Üres képpontra kattintva új szövegdoboz helyének előnézete."""
        self._require_active()
        self._text_selected_index = None
        self._text_rotation_drag = None
        self._text_pending_pos = (_clamp01(x), _clamp01(y))
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()


    def _load_text_settings_from_block(self, block: TextBlock) -> None:
        """A kiválasztott blokk ismert stílusát a szerkesztőmezőkre tölti."""
        style = block.style
        self._text_fill_color = _argb_to_rgb(style.fill_argb)
        self._text_outline_color = _argb_to_rgb(style.outline_argb)
        self._text_outline_thickness = float(style.unknown_a)
        self._text_fill_enabled = style.fill_mode != _MOD_NINCS_KITOLTES
        self._text_family = block.font or None
        self._text_size_pt = meret_taroltbol(block.geometry.size)
        self._text_size_edited = False
        self._text_bold = style.weight >= 700
        self._text_italic = style.italic
        self._text_underline = style.underline
        self._text_align = alignment_name(style.alignment)


    @Slot(bool)
    def setTextOverlayVisible(self, visible: bool) -> None:
        """A szöveg nézeti láthatóságát váltja a szerkesztési munkamenetben.

        Az eredeti kapcsoló nem módosítja a fotóra mentett feliratot; a
        következő fotó megnyitásakor a szöveg ismét látszik.
        """
        self._require_active()
        visible = bool(visible)
        if self._text_overlay_visible == visible:
            return
        self._text_overlay_visible = visible
        self._refresh_text_preview()


    @Slot()
    def applyText(self) -> None:
        """A kijelölt blokk módosítása vagy új blokk hozzáfűzése az ini-hez.

        #7407: ha a Clear All után üres a piszkozat, a törlést véglegesíti az
        iniben (a text= és textactive= kulcsok kikerülnek)."""
        self._require_active()
        if (
            getattr(self, "_text_cleared", False)
            and not self._text_draft.strip()
            and self._text_pending_pos is None
        ):
            self._text_overlay = None
            self._text_active = False
            self._text_cleared = False
            self._text_initial_overlay = None
            self._text_initial_active = False
            self._text_selected_index = None
            self._text_rotation_drag = None
            self._text_pending_pos = None
            self._text_draft = ""
            self._text_inline_editing = False
            self._save_text()
            self._bump_revision()
            self.toolsChanged.emit()
            self.hasTextOverlayChanged.emit()
            self.textDraftChanged.emit()
            self.textSelectedIndexChanged.emit()
            self.textOverlayItemsChanged.emit()
            self.textClearedChanged.emit()
            return

        if not self._text_draft.strip():
            return

        previous = self._text_overlay or TextOverlay()
        target_index = self._text_selected_index
        if target_index is not None:
            if not 0 <= target_index < len(previous.blocks):
                return
            existing = previous.blocks[target_index]
            geometry = existing.geometry
            if self._text_pending_pos is not None:
                geometry = replace(
                    geometry,
                    x=self._text_pending_pos[0],
                    y=self._text_pending_pos[1],
                )
            if self._text_size_edited:
                geometry = replace(geometry, size=tarolt_meret(self._text_size_pt))
            style_template = existing.style
        else:
            if self._text_pending_pos is None:
                return
            geometry = TextGeometry(
                x=self._text_pending_pos[0],
                y=self._text_pending_pos[1],
                size=tarolt_meret(self._text_size_pt),
            )
            style_template = previous.primary.style if previous.primary else None

        style = self._text_style_for_apply(style_template)
        block = TextBlock(
            content=self._text_draft,
            font=self._text_family,
            geometry=geometry,
            style=style,
        )
        blocks = list(previous.blocks)
        if target_index is None:
            blocks.append(block)
            target_index = len(blocks) - 1
        else:
            blocks[target_index] = block

        self._text_overlay = TextOverlay(blocks=tuple(blocks))
        self._text_selected_index = target_index
        self._text_rotation_drag = None
        self._text_active = True
        self._text_pending_pos = None
        self._text_size_edited = False
        self._text_cleared = False
        self._text_initial_overlay = self._text_overlay
        self._text_initial_active = self._text_active
        self._save_text()
        self._bump_revision()
        self.toolsChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()
        self.hasTextOverlayChanged.emit()
        self.textClearedChanged.emit()


    def _text_style_for_apply(self, template: TextStyle | None) -> TextStyle:
        """Ismert stílust állít, a fájl többi mezőjét és bitjét megőrzi."""
        if template is None:
            style = TextStyle(
                fill_argb=_rgb_to_argb(self._text_fill_color),
                outline_argb=_rgb_to_argb(self._text_outline_color),
                weight=700 if self._text_bold else 400,
                unknown_a=float(self._text_outline_thickness),
            )
        else:
            style = replace(
                template,
                fill_argb=_rgb_to_argb(self._text_fill_color),
                outline_argb=_rgb_to_argb(self._text_outline_color),
                weight=700 if self._text_bold else 400,
                unknown_a=float(self._text_outline_thickness),
            )
        return style.with_style_flags(
            italic=self._text_italic, underline=self._text_underline
        ).with_text_layout(
            alignment=alignment_code(self._text_align),
            fill_mode=fill_mode_from(
                no_fill=not self._text_fill_enabled,
                outline_width=float(self._text_outline_thickness),
            ),
        )


    @Slot()
    def clearText(self) -> None:
        """A mentett vagy piszkozatbeli szöveg eltávolítása az eszközön belül.

        #7407: a Clear All csak az eszköz piszkozatából veszi le a szöveget,
        az inibe NEM ír; az eszköz nyitva marad, a „Clear All” tiltott, az
        „Apply” aktív. A „Cancel” (exitTextTool) visszahozza a megnyitáskori
        állapotot, az „Apply” (applyText) véglegesíti a törlést."""
        self._require_active()
        volt_mentett = bool(
            self._text_initial_overlay
            and any(block.content for block in self._text_initial_overlay.blocks)
        )
        self._text_overlay = None
        self._text_selected_index = None
        self._text_rotation_drag = None
        self._text_pending_pos = None
        self._text_draft = ""
        self._text_inline_editing = False
        self._text_cleared = volt_mentett
        self._register_preview()
        self._bump_revision()
        self.toolsChanged.emit()
        self.hasTextOverlayChanged.emit()
        self.textDraftChanged.emit()
        self.textSelectedIndexChanged.emit()
        self.textOverlayItemsChanged.emit()
        self.textClearedChanged.emit()


    def _current_text_spec(self) -> tuple[TextOverlaySpec, ...] | None:
        """Az előnézet aktív feliratai, a kijelölt piszkozatot is beleértve."""
        if not self._text_overlay_visible:
            return None
        specs: list[TextOverlaySpec] = []
        if self._text_active and self._text_overlay:
            for index, block in enumerate(self._text_overlay.blocks):
                if self._text_inline_editing and index == self._text_selected_index:
                    # #7380: a szerkesztett blokkot a QML-doboz rajzolja
                    continue
                content = (
                    self._text_draft
                    if index == self._text_selected_index
                    else block.content
                )
                if not content:
                    continue
                if (
                    index == self._text_selected_index
                    and self._text_pending_pos is not None
                ):
                    x, y = self._text_pending_pos
                else:
                    x, y = block.geometry.x, block.geometry.y
                style = (
                    self._text_style_kwargs()
                    if index == self._text_selected_index
                    else self._text_style_kwargs_for_block(block)
                )
                specs.append(
                    TextOverlaySpec(
                        content=content,
                        x=x,
                        y=y,
                        rotation=block.geometry.rotation,
                        **style,
                    )
                )
        if (
            self._text_pending_pos is not None
            and self._text_selected_index is None
            and not self._text_inline_editing
        ):
            content = self._text_draft
            if content.strip():
                x, y = self._text_pending_pos
                specs.append(
                    TextOverlaySpec(content=content, x=x, y=y, **self._text_style_kwargs())
                )
        return tuple(specs) or None


    def _text_style_kwargs(self) -> dict:
        """A `TextOverlaySpec` stílus-mezői a jelenlegi (#450, munkamenet-
        szintű, ini-be nem kerülő) beállításokból."""
        return {
            "fill_color": self._text_fill_color,
            "outline_color": self._text_outline_color,
            "outline_thickness": self._text_outline_thickness,
            "fill_enabled": self._text_fill_enabled,
            "opacity": self._text_opacity,
            "font_family": self._text_family,
            "font_size_pt": self._text_size_pt,
            "bold": self._text_bold,
            "italic": self._text_italic,
            "underline": self._text_underline,
            "align": self._text_align,
        }


    def _text_style_kwargs_for_block(self, block: TextBlock) -> dict:
        """A mentett blokk saját ismert stílusa a többblokkos előnézethez."""
        style = block.style
        return {
            "fill_color": _argb_to_rgb(style.fill_argb),
            "outline_color": _argb_to_rgb(style.outline_argb),
            "outline_thickness": style.unknown_a,
            "fill_enabled": style.fill_mode != _MOD_NINCS_KITOLTES,
            "opacity": _DEFAULT_TEXT_OPACITY,
            "font_family": block.font or self._default_text_family(),
            "font_size_pt": block.geometry.size * 360.0,
            "bold": style.weight >= 700,
            "italic": style.italic,
            "underline": style.underline,
            "align": alignment_name(style.alignment),
        }

