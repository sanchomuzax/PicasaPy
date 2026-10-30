"""A kollázsvezérlő megnyitási és beállítási műveletei."""

from __future__ import annotations

from collections.abc import Sequence

from PySide6.QtCore import Slot

from picasapy.collage.page_formats import ORIENTATIONS, is_known_format
from picasapy.collage.themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    CONTACTSHEET,
    WHITEBORDER,
)

from . import collage_layout as layout
from . import collage_prefs as prefs
from .collage_album_fields import album_fields_of
from .collage_model import selected_indices, with_selection
from .collage_sources import common_source_folder_name


class _CollageControllerSettingsMixin:
    """A kollázslap megnyitása, újraelrendezése és beállítása."""

    def _title_from_sources(self, sources) -> str:
        """A közös FORRÁSMAPPA neve — ez lesz a kimeneti fájl neve (9.1).

        A „mi a közös mappa" szabály a `collage_sources`-ban él, egyetlen
        példányban (#1092): ugyanaz dönti el a címet, az `albumUID`-ot és
        az `<albumDate>`-et, tehát a három nem mondhat ellent egymásnak."""
        return common_source_folder_name(sources)

    def _apply_source_album_fields(self, sources) -> None:
        """Az `albumUID` és az `<albumDate>` a FORRÁSMAPPÁBÓL (#1092).

        A `.cxf`-jeinkből eddig mindkettő hiányzott, pedig a 12 golden
        mintában mind ott van. A forrás ugyanaz, mint a címé: a képek közös
        mappája — több mappánál nincs egy forrásalbum, tehát üresen maradnak.

        ⚠️ Az `albumID`-t NEM töltjük ki: a golden készlet 12 mintájából
        **egyben sem** szerepel (az író, `0x008347b0`, nem is írja) — csak
        az olvasó ismeri. Ami az eredetiben nincs, azt nem gyártjuk le.

        ⚠️ Új kollázs indul, tehát a MEGNYITOTT projekt csomópont-
        azonosítói sem érvényesek többé: a leképezés ürül. Enélkül egy
        korábban megnyitott Picasa-fájl azonosítója átszivárogna az új
        kollázsba, ha ugyanaz a kép kerül bele."""
        # A hónapnév a FELÜLET nyelvéből jön, nem a `QLocale()`
        # rendszerlokáljából — ugyanaz a forrás, mint a Kollázsok mappa
        # nevéé (#1131): magyar rendszeren angol felülettel a rendszerlokál
        # hazudna, a CI „C" lokálján pedig a kimenet a futtatókörnyezettől
        # függene.
        from .collage_output import _felulet_nyelve

        self._collage_panel_node_uids = {}
        self._collage_panel_node_scales = {}
        self._collage_panel_album_id = ""
        self._collage_panel_album_uid, self._collage_panel_album_date = (
            album_fields_of(
                sources,
                db_path=getattr(self, "_db_path", None),
                language=_felulet_nyelve(),
            )
        )

    @Slot(list)
    def openCollage(self, rows) -> None:
        """A kollázs-lap megnyitása a megadott rács-sorokkal."""
        self._ensure_collage_panel()
        self._collage_panel_frame_center = -1
        self._set_saved_path("")
        # #1387: friss, forrásalbumból induló kollázs — nincs hozzá TÉNYLEGES
        # piszkozat-mappa, amíg a felhasználó nem ment. A korábbi (más
        # képről nyitott) piszkozat mappája itt nem élhet tovább.
        self._collage_panel_draft_source_dir = None
        sources = self._sources_from_rows(rows)
        self.setCollageTitle(self._title_from_sources(sources))
        self._apply_source_album_fields(sources)
        self._relayout(sources, dirty=False)
        if not self._collage_panel_open:
            self._collage_panel_open = True
            self.collageOpenChanged.emit()

    @Slot()
    def closeCollage(self) -> None:
        """A lap bezárása. A mentetlen módosítás kérdése a felületé (9.2).

        ⚠️ #1092: a forrásalbum mezői és a csomópont-azonosítók
        leképezése is ürül. A bezárt lap adatai nem tapadhatnak rá a
        következőre — a `openCollage` ugyan felülírja őket, de a
        `openCollageProject` csak azt írja felül, ami a MEGNYITOTT fájlban
        benne van: egy `albumUID` nélküli piszkozat így az előző kollázs
        azonosítóját örökölte volna."""
        self._ensure_collage_panel()
        self._set_nodes((), dirty=False)
        self._set_dirty(False)
        self._collage_panel_node_uids = {}
        self._collage_panel_node_scales = {}
        self._collage_panel_album_uid = ""
        self._collage_panel_album_id = ""
        self._collage_panel_album_date = ""
        if self._collage_panel_open:
            self._collage_panel_open = False
            self.collageOpenChanged.emit()

    def _sources_from_rows(self, rows) -> tuple[layout.CollageSource, ...]:
        """A rács-sorokból kép-források (a fotólista a host-controlleré)."""
        photos = getattr(getattr(self, "_photos", None), "photos", ())
        return layout.sources_from_photos(photos, rows)

    def _current_sources(self) -> tuple[layout.CollageSource, ...]:
        """A kollázs jelenlegi képei forrásként — a CSOMÓPONTOKBÓL.

        Külön forrás-listát tartani hibaforrás: a keverés és a csere a
        képeket a rések között mozgatja, tehát egy párhuzamosan vezetett
        lista pár művelet után más sorrendben állna, mint a vászon.

        ⚠️ #989: a kép oldalarányát a csomópont `aspect` mezője őrzi, NEM a
        `width / height` hányados — a rácsos témák CELLÁBA vágnak, ott a
        doboz a celláé."""
        return tuple(
            layout.CollageSource(node.path, node.caption, node.aspect)
            for node in self._nodes()
        )

    def _relayout_for_page_shape(self) -> None:
        """Újraszámolás a lap ALAKJÁNAK változása után (#991).

        A `setCollageFormat` és a `setCollageOrientation` eddig csak a lap
        arányát cserélte ki — a kártyák a régi helyükön maradtak, tehát
        kilógtak, összetorlódtak, vagy nagy üres rész maradt. A
        `setCollageTheme` már ma is helyesen újraszámol.

        Az eredetiben ezt a képesség-maszk **1. bitje** kapcsolja
        (`0x0087e960`, a kapcsolók a `0x00839f07` és a `0x0083a201` címen;
        spec 2.), és a rácsos témák pakolói eleve a lap arányából dolgoznak
        — mindkét ágon újraszámolás következik.

        ⚠️ A kézi elrendezés ilyenkor ELVESZIK. Ez az eredeti viselkedése
        (ugyanaz, mint téma-váltásnál, spec 5.), és nincs értelme
        megőrizni: a régi helyek a RÉGI lap alakjához tartoztak.

        A `dirty` jelző igazra vált — a `_relayout(dirty=True)` állítja be,
        ezért itt külön `_set_dirty` nem kell."""
        self._relayout(self._current_sources(), dirty=True)

    def _relayout(
        self, sources: Sequence[layout.CollageSource], *, dirty: bool
    ) -> None:
        """A csomópontok újraszámolása a TÉMA pakolójával (#989).

        A kézi szerkesztés ilyenkor ELVESZIK — ez az eredeti viselkedése
        téma-váltásnál és visszaállításnál (spec 5.), nem hiba. A
        képkockaközéppont indexe a pakolás UTÁN igazodik: a hangsúlyos kép a
        legfelső rétegbe, tehát a lista végére kerül."""
        self._set_nodes(
            layout.laid_out(
                sources,
                self.collagePageRatio,
                self._collage_panel_border,
                theme=self._collage_panel_theme,
                spacing=self._collage_panel_spacing,
                frame_center=self._collage_panel_frame_center,
                seed=self._collage_panel_seed,
            ),
            dirty=dirty,
        )
        self._set_frame_center(
            layout.frame_center_after(
                self._collage_panel_theme,
                self._collage_panel_frame_center,
                len(self._nodes()),
            )
        )
        self._set_dirty(dirty)

    def _set_frame_center(self, index: int) -> None:
        """A Python-oldali képkockaközéppont beállítása."""
        self._ensure_collage_panel()
        if self._collage_panel_frame_center == index:
            return
        self._collage_panel_frame_center = index

    @Slot(str)
    def setCollageTheme(self, key: str) -> None:
        """Téma-váltás. A kézi elrendezés ilyenkor ÚJRASZÁMOLÓDIK (a maszk
        1. bitje, spec 5.) — az eredeti sem kérdez rá."""
        self._ensure_collage_panel()
        if key not in COLLAGE_THEMES or key == self._collage_panel_theme:
            return
        self._collage_panel_theme = key
        self._get_settings().setValue(prefs.THEME_KEY, key)
        self.collageThemeChanged.emit()
        self.collageCapabilitiesChanged.emit()
        capabilities = self._capabilities()
        if key == CONTACTSHEET:
            # A valódi AI6 alap-Indexképe fehér szegélyes. A választó ettől
            # még aktív: a felhasználó a témaváltás UTÁN felülírhatja.
            self._collage_panel_border = WHITEBORDER
            self.collageBorderChanged.emit()
        if not self._collage_panel_shadows_explicit:
            self._collage_panel_shadows = capabilities.shadow_default
        self.collageShadowsChanged.emit()
        if not capabilities.selection:
            self._set_nodes(with_selection(self._nodes(), ()), dirty=False)
        if self._nodes():
            self._relayout(self._current_sources(), dirty=True)

    @Slot(str)
    def setCollageBorder(self, key: str) -> None:
        """Képkeret — a KIJELÖLTEKRE, ha van kijelölés; egyébként mindenkire."""
        self._ensure_collage_panel()
        if key not in BORDER_THEMES:
            return
        self._collage_panel_border = key
        self.collageBorderChanged.emit()
        nodes = self._nodes()
        if not nodes:
            return
        selection = selected_indices(nodes) or range(len(nodes))
        self._set_nodes(layout.replaced_many(nodes, selection, border=key))

    @Slot(float)
    def setCollageSpacing(self, value: float) -> None:
        """A „Rács vastagsága" csúszka 0…1 értéke (nem képpont!)."""
        self._ensure_collage_panel()
        spacing = min(1.0, max(0.0, float(value)))
        if spacing != self._collage_panel_spacing:
            self._collage_panel_spacing = spacing
            self.collageSpacingChanged.emit()
            # #1121: a térköz a PAKOLÁS bemenete, nem csak a rajzolásé — a
            # rácsos témák cellamérete tőle függ. Enélkül a vászon a RÉGI
            # elrendezést mutatta, és a felhasználó azt látta, hogy a
            # csúszka nem csinál semmit („hiába állítom be"). A
            # `setCollageFormat`/`setCollageOrientation` ugyanígy rendez újra.
            self._relayout_for_page_shape()
        self._apply_zero_spacing_shadow_rule()

    def _apply_zero_spacing_shadow_rule(self) -> None:
        """Spec 5./1.: ha a térköz-csúszka LÁTSZIK és az értéke 0, az
        árnyék-jelölő BEkapcsol (nem tiltódik le) — nulla térköznél az árnyék
        az egyetlen, ami elválasztja egymástól a képeket.

        Ez ÁLLAPOT-szabály, nem esemény: akkor is érvényesül, ha a csúszka
        már eddig is nullán állt."""
        if self._collage_panel_spacing == 0.0 and self._capabilities().spacing:
            self.setCollageShadows(True)

    @Slot(bool)
    def setCollageShadows(self, on: bool) -> None:
        self._ensure_collage_panel()
        wanted = bool(on) and self._capabilities().shadow
        self._collage_panel_shadows_explicit = True
        self._get_settings().setValue(
            prefs.SHADOWS_KEY, "true" if wanted else "false"
        )
        if wanted == self._collage_panel_shadows:
            return
        self._collage_panel_shadows = wanted
        self.collageShadowsChanged.emit()
        self._set_dirty(True)

    @Slot(bool)
    def setCollageCaptions(self, on: bool) -> None:
        self._ensure_collage_panel()
        wanted = bool(on)
        self._get_settings().setValue(
            prefs.CAPTIONS_KEY, "true" if wanted else "false"
        )
        if wanted == self._collage_panel_captions:
            return
        self._collage_panel_captions = wanted
        self.collageCaptionsChanged.emit()
        self._set_dirty(True)

    @Slot(str)
    def setCollageOrientation(self, kind: str) -> None:
        self._ensure_collage_panel()
        if kind not in ORIENTATIONS or kind == self._collage_panel_orientation:
            return
        self._collage_panel_orientation = kind
        self._get_settings().setValue(prefs.ORIENTATION_KEY, kind)
        self.collageOrientationChanged.emit()
        self.collagePageRatioChanged.emit()
        self._relayout_for_page_shape()

    @Slot(str)
    def setCollageFormat(self, key: str) -> None:
        self._ensure_collage_panel()
        if not is_known_format(key) or key == self._collage_panel_format:
            return
        self._collage_panel_format = key
        self._get_settings().setValue(prefs.FORMAT_KEY, key)
        self.collageFormatKeyChanged.emit()
        self.collagePageRatioChanged.emit()
        self._relayout_for_page_shape()
