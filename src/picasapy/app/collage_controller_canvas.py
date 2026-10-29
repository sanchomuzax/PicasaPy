"""A kollázsvászon műveletei — a CollageMixin #6169 szelete."""

from __future__ import annotations

from PySide6.QtCore import Slot

from picasapy.collage import canvas

from . import collage_layout as layout
from .collage_model import (
    CollageNode,
    initial_node_width,
    pictures_of,
    selected_indices,
    with_pictures,
    with_pictures_swapped,
    with_selection,
)


class CollageCanvasMixin:
    """Kijelölés, vászonműveletek és klipkezelés a Kollázs-lapon."""

    def _single_selected_index(self) -> int:
        """A pontosan egy kijelölt csomópont INDEXE, vagy −1 + kérés a felület
        felé. A „Beállítás háttérként", a „Megjelenítés és szerkesztés" és a
        „Beállítás képkockaközéppontként" mind egy képet vár (spec 4.4).

        Külön az indexre (#1009): a háttérnek épp az index kell, a másik két
        hívónak a csomópont — a kijelölés SZABÁLYA viszont egy helyen él."""
        selection = selected_indices(self._nodes())
        if len(selection) != 1:
            self.collageNeedsSelection.emit()
            return -1
        return selection[0]

    def _single_selected(self) -> CollageNode | None:
        """A pontosan egy kijelölt csomópont, vagy `None`."""
        index = self._single_selected_index()
        return None if index < 0 else self._nodes()[index]

    # -- kijelölés (8.2) ---------------------------------------------------

    @Slot(list)
    def setCollageSelection(self, indices) -> None:
        self._ensure_collage_panel()
        wanted = indices if self._capabilities().selection else ()
        self._set_nodes(with_selection(self._nodes(), wanted or ()), dirty=False)

    @Slot()
    def selectAllNodes(self) -> None:
        self.setCollageSelection(list(range(len(self._nodes()))))

    @Slot()
    def selectNoNodes(self) -> None:
        self.setCollageSelection([])

    @Slot()
    def removeSelectedNodes(self) -> None:
        """A kijelöltek kivétele (Del). Minden kép eltávolítható — a mentés
        ilyenkor „Mentés mellőzve" üzenettel áll meg."""
        # #1276: a törlés MAGJA a `deleteClips` — benne a #996
        # lyuk-javításával (rácsos témánál újrarendezés). Korábban ez a
        # két út elvált, és a `Del` rácsos témán lyukat hagyott.
        self.deleteClips(selected_indices(self._nodes()))

    # -- vászon-manipuláció (8.2) ------------------------------------------

    @Slot(int, float, float)
    def moveNode(self, index: int, cx: float, cy: float) -> None:
        """Egy csomópont áthelyezése — a középpont LAPEGYSÉGBEN."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes):
            return
        self._set_nodes(
            layout.replaced_at(nodes, index, center_x=float(cx), center_y=float(cy))
        )

    @Slot(int, float, float)
    def transformNode(self, index: int, scale: float, theta: float) -> None:
        """Méretezés + forgatás EGY fogantyúval (7.4).

        A `scale` a kollázs ALAPMÉRETÉHEZ képest szól (1,0 = a kezdő méret),
        ahogy a húzás közbeni „Méretarány: %d%%" felirat is
        (`canvas.scale_caption_percent`). A kép oldalaránya megmarad."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes) or float(scale) <= 0.0:
            return
        node = nodes[index]
        width = float(scale) * initial_node_width(len(nodes))
        self._set_nodes(
            layout.replaced_at(
                nodes,
                index,
                width=width,
                height=width * node.height / node.width,
                theta=float(theta),
            )
        )

    @Slot(int, int)
    def swapNodes(self, a: int, b: int) -> None:
        """Egy képet a másikra ejtve CSERÉLNEK: a fogadó rés mérete, kerete
        és szöge marad, csak a kép költözik."""
        nodes = self._nodes()
        if not (0 <= a < len(nodes) and 0 <= b < len(nodes)) or a == b:
            return
        self._set_nodes(with_pictures_swapped(nodes, a, b))

    @Slot(int)
    def raiseNodeToTop(self, index: int) -> None:
        """Alt+húzás: a csomópont a legfelső rétegbe.

        Ha MÁR a legfelső (a lista végén áll), semmi nem történik — sem a
        modell, sem a „piszkos" jelző nem változik."""
        nodes = self._nodes()
        if not 0 <= index < len(nodes) or index == len(nodes) - 1:
            return
        self._set_nodes(canvas.move_to_top(nodes, [index]))

    @Slot()
    def moveSelectionTop(self) -> None:
        self._move_selection(canvas.move_to_top)

    @Slot()
    def moveSelectionUp(self) -> None:
        self._move_selection(canvas.move_up)

    @Slot()
    def moveSelectionDown(self) -> None:
        self._move_selection(canvas.move_down)

    @Slot()
    def moveSelectionBottom(self) -> None:
        self._move_selection(canvas.move_to_bottom)

    def _move_selection(self, operation) -> None:
        """A négy rétegsorrend-parancs közös törzse — a `canvas.py`-ból.

        A kijelölés a csomópont `selected` mezőjében él, ezért a lista
        átrendezésével MAGÁTÓL követi a képet; nincs mit újraszámolni."""
        nodes = self._nodes()
        selection = selected_indices(nodes)
        if not selection:
            return
        self._set_nodes(operation(nodes, selection))

    @Slot(str)
    def snapRotation(self, command: str) -> None:
        """A négy bepattintó forgatás (`snap_12`/`snap_3`/`snap_6`/`snap_9`).

        ⚠️ A `snap_9` **−90,0 fokot** tárol (nem 270-et): a `.cxf`-be
        −1,570796 kerül, különben a windowsos Picasával az oda-vissza olvasás
        elcsúszna. Az értéket a `canvas.snap_theta` adja.

        ⚠️ #1162: ez a művelet **NEM függ** a téma `rotate` képességétől.
        Kimérve az eredeti binárisból: a négy `collagepanel/snap_*`
        parancsnév a `0x0083b900` végrehajtóra fut (0 / 90 / 180 / −90 fok,
        `pi/180`-nal radiánra váltva, az elem `+0x15c` mezőjébe), és abban a
        függvényben nincs képesség-maszk vizsgálat. A maszk 7. bitjét a
        teljes `.text` egyetlen helyen nézi (`0x0083ad5f`), és az a
        szórás-animációt (`AnimPlacementHandler`: hely + szög + méret)
        kapuzza — vagyis a bit a SZABAD elrendezésé, nem a fix igazításé."""
        nodes = self._nodes()
        selection = selected_indices(nodes)
        if not selection:
            self.collageNeedsSelection.emit()
            return
        try:
            theta = canvas.snap_theta(command)
        except ValueError:
            return
        self._set_nodes(layout.replaced_many(nodes, selection, theta=theta))

    # -- véletlenszerűsítés (8.2) ------------------------------------------

    @Slot()
    def shufflePictures(self) -> None:
        """„Képek összekeverése" (`rand_order`): a KÉPEK cserélnek helyet, a
        rések (méret, keret, szög) maradnak — ugyanaz a szabály, mint az
        egymásra ejtésnél. A keverő a `canvas.shuffle_order`."""
        nodes = self._nodes()
        if len(nodes) < 2 or not self._capabilities().shuffle:
            return
        self._collage_panel_seed += 1
        pictures = canvas.shuffle_order(pictures_of(nodes), self._rng())
        self._set_nodes(with_pictures(nodes, pictures))

    @Slot()
    def scrambleCollage(self) -> None:
        """„Véletlenszerű kollázs" / „Képek szétszórása" (`rand_placement`):
        az ELRENDEZÉS sorsolódik újra, a képek sorrendje marad."""
        nodes = self._nodes()
        if not nodes or not self._capabilities().scramble:
            return
        self._collage_panel_seed += 1
        self._set_nodes(
            layout.rescattered(nodes, self.collagePageRatio, self._rng())
        )

    @Slot()
    def setFrameCenterFromSelection(self) -> None:
        """„Beállítás képkockaközéppontként" — a hangsúlyos központi kép.

        #989: a Képkockamozaiknál a beállítás UTÁN újrarendezünk, különben a
        parancsnak nem volna látható hatása — a hangsúlyos hely az
        elrendezésben születik meg (`picasa_render._FRAMEGRID_CENTER`). A
        többi téma pakolója nem olvassa ezt az értéket."""
        node = self._single_selected()
        if node is None:
            return
        self._set_frame_center(self._nodes().index(node))
        self._set_dirty(True)
        if layout.layout_uses_frame_center(self._collage_panel_theme):
            self._relayout(self._current_sources(), dirty=True)

    @Slot()
    def viewAndEditSelection(self) -> None:
        """„Megjelenítés és szerkesztés" — a képet a szerkesztő nyitja meg."""
        node = self._single_selected()
        if node is not None:
            self.collageEditRequested.emit(node.path)

    # -- klipek (8.2) ------------------------------------------------------

    @Slot(list)
    def addClips(self, rows) -> None:
        """A „+" gomb: további képek a kollázsba, a LEGFELSŐ rétegbe.

        ⚠️ #996: a SZÓRÁS csak a Képkupacnál helyes. A rácsos témáknál az
        új kép a kupac alapméretével, döntetlenül, véletlen helyre került —
        vagyis KILÓGOTT a rácsból. Ott a téma pakolójának kell újraszámolnia.

        A megkülönböztetés a téma `rotate` képessége (a szabad forgatás):
        ez EGYETLEN témánál áll, a Képkupacnál — pont annál, aminek az
        elrendezése eleve szórás, és amit a felhasználó kézzel rendez.
        A többinél a hely a pakoló dolga, nem a véletlené."""
        self._ensure_collage_panel()
        added = self._sources_from_rows(rows)
        if not added:
            return
        if not self._capabilities().rotate:
            self._relayout(self._current_sources() + tuple(added), dirty=True)
            return
        width = initial_node_width(len(self._nodes()) + len(added))
        centers = layout.scatter(len(added), self.collagePageRatio, self._rng())
        new_nodes = tuple(
            layout.node_for(source, center, width, self._collage_panel_border)
            for source, center in zip(added, centers, strict=True)
        )
        self._set_nodes((*self._nodes(), *new_nodes))

    def deleteClips(self, rows) -> None:
        """A megadott klipek (csomópont-indexek) kivétele a kollázsból.

        #1276: ez a tag SZÁNDÉKOSAN nem `@Slot`. Korábban a Klipek lap
        „–" gombja hívta — csakhogy annak a gombnak a saját buboréksúgója
        a TÁLCÁRÓL való eltávolítást ígéri, és a lap azóta tényleg a
        tálcát kezeli (`removeTrayItems`). A kollázsról levételnek egy
        felületi útja maradt: a vászon `Del` billentyűje, ami a
        `removeSelectedNodes`-on át IDE fut be — így a #996 lyuk-javítása
        arra az útra is érvényes lett (korábban nem volt az).

        ⚠️ #996: rácsos témánál a törölt kép helyén LYUK maradt — a rács
        hiányos lett. A Képkupacnál viszont a lyuk természetes: a csempék
        eleve átfedik egymást, és az újraszámolás elvenné a felhasználó
        kézi elrendezését. A határ ugyanaz, mint az `addClips`-nél: a téma
        `rotate` képessége."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        indices = [int(r) for r in (rows or ()) if 0 <= int(r) < len(nodes)]
        if not indices:
            return
        maradek = canvas.remove_at(nodes, indices)
        if not self._capabilities().rotate and maradek:
            self._set_nodes(maradek, dirty=True)
            self._relayout(self._current_sources(), dirty=True)
            return
        self._set_nodes(maradek)

    @Slot()
    def resetCollage(self) -> None:
        """A kézi szerkesztés elvetése: elrendezés újra, a jelenlegi képekből."""
        self._ensure_collage_panel()
        self._collage_panel_seed += 1
        self._relayout(self._current_sources(), dirty=False)
