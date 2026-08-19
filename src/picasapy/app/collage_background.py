"""A kollázs HÁTTERE — mód, szín és a háttérkép (#943, #946, #1009).

A `collage_controller.CollageMixin` szelete: a spec **6.4** három
háttérmódja (`solid`, `image`, `avg`), a színválasztó és a „Kép
használata" háttérképe. A vágás oka ugyanaz, mint a `collage_save`-é: a
vezérlő fájlja a #1009-cel 800 sor fölé nőtt volna. Kifelé EGY objektum
marad — a spec 8. szakaszának név szerinti szerződése változatlan.

## A háttérkép NEM tetszőleges fájl

Az eredeti Picasa a háttérképet a kollázs SAJÁT képei közül veszi, és
**indexszel** hivatkozik rá: a `0x00830a00(this, index)` tölti fel a
`collagepanel/current_background` előnézetet, és `index == -1` esetén
kilép (`0x00830a8b`). Ezt a szelet is így tartja: az igazságforrás egy
index a csomópont-listába, az útvonal ebből SZÁMOLÓDIK
(`collageBackgroundImage`). Két haszna van:

1. **Nem születhet törött hivatkozás.** Ha a képet kiveszik a kollázsból,
   az index elveszti az érvényét, és a háttér a következő érvényesre esik
   vissza — üres előnézet helyett.
2. **A háttér a KÉPET követi, nem a rést.** A keverés és a csere a képeket
   a rések között mozgatja; ezért a csomópont-csere UTÁN az útvonal alapján
   kötjük vissza az indexet (`_sync_background_index`).

⚠️ A `_collage_panel_bg_*` mezőket a `CollageMixin._ensure_collage_panel()`
hozza létre — a panelnek EGY, lusta inicializálója van, hogy ne legyen két
félig kész állapot ugyanarra a lapra.
"""

from __future__ import annotations

from PySide6.QtCore import Property, QUrl, Signal, Slot
from PySide6.QtGui import QColor

from . import collage_prefs as prefs
from .formatting import to_file_url

#: A háttér három módja (spec 6.4). Az `avg` a `collage::avgcolor`.
BACKGROUND_MODES = ("solid", "image", "avg")


class CollageBackgroundMixin:
    """A háttér három módja, a színe és a háttérképe (spec 6.4)."""

    # -- property-jelzések (8.1) -------------------------------------------

    collageBackgroundModeChanged = Signal()
    collageBackgroundColorChanged = Signal()
    collageBackgroundImageChanged = Signal()

    # -- property-k (8.1) --------------------------------------------------

    @Property(str, notify=collageBackgroundModeChanged)
    def collageBackgroundMode(self) -> str:
        self._ensure_collage_panel()
        return self._collage_panel_bg_mode

    @Property(QColor, notify=collageBackgroundColorChanged)
    def collageBackgroundColor(self) -> QColor:
        self._ensure_collage_panel()
        return self._collage_panel_bg_color

    @Property(str, notify=collageBackgroundImageChanged)
    def collageBackgroundImage(self) -> str:
        """A háttérkép útvonala — a CSOMÓPONTBÓL, nem külön tárolt szövegből.

        Így nem születhet törött hivatkozás: ha a képet kivették a
        kollázsból, az index elveszti az érvényét, és a felület üres helyett
        a következő érvényes hátteret látja (`_sync_background_index`)."""
        self._ensure_collage_panel()
        nodes = self._nodes()
        index = self._collage_panel_bg_index
        return nodes[index].path if 0 <= index < len(nodes) else ""

    @Property(QUrl, notify=collageBackgroundImageChanged)
    def collageBackgroundImageUrl(self) -> QUrl:
        """Ugyanaz az útvonal, de a QML `Image.source`-ának való URL-ként.

        ⚠️ **Miért kell külön property.** A felület korábban `"file://" + út`
        módon fűzte össze a forrást. Ez a windows-CI-lábon éles hibát adott:
        a `C:` a QUrl-nek PORTNAK látszik, az URL érvénytelen lesz, és a
        `source` üresre normalizálódik — vagyis a háttérkép-előnézet
        Windowson MINDEN útvonalra üres maradt. Ékezetes vagy `#`-et
        tartalmazó fájlnévnél a kézi fűzés Linuxon is romlik.

        Az átalakítás EGY helyen él (`formatting.to_file_url`), és a Qt saját
        `QUrl.fromLocalFile`-jára épül — a szabályt nem mi találjuk ki
        platformonként."""
        return to_file_url(self.collageBackgroundImage)

    # -- slotok (8.2) ------------------------------------------------------

    @Slot(str)
    def setCollageBackgroundMode(self, mode: str) -> None:
        self._ensure_collage_panel()
        if mode not in BACKGROUND_MODES or mode == self._collage_panel_bg_mode:
            return
        self._collage_panel_bg_mode = mode
        self.collageBackgroundModeChanged.emit()
        if mode == "image":
            self._ensure_background_picture()
        self._set_dirty(True)

    @Slot("QColor")
    def setCollageBackgroundColor(self, color) -> None:
        self._ensure_collage_panel()
        value = QColor(color)
        if not value.isValid() or value == self._collage_panel_bg_color:
            return
        self._collage_panel_bg_color = value
        self._get_settings().setValue(prefs.BGCOLOR_KEY, value.name())
        self.collageBackgroundColorChanged.emit()
        self._set_dirty(True)

    @Slot()
    def setBackgroundFromSelection(self) -> None:
        """„A kijelölt elemek használata" — a háttérkép a kijelölt képből.

        Ez ERŐSEBB a módváltás alapértelmezésénél: a `_ensure_background_picture`
        csak akkor választ, ha nincs érvényes háttér."""
        index = self._single_selected_index()
        if index < 0:
            return
        self._set_background_index(index)
        self.setCollageBackgroundMode("image")
        self._set_dirty(True)

    # -- a háttérkép indexe (#1009) ----------------------------------------

    def _set_background_index(self, index: int) -> None:
        """A háttérkép indexe + a jelzés. Jelzés nélkül a QML-kötés nem
        frissül, és a 37 × 37-es előnézet üres marad — pontosan ez volt a
        #1009 második tünete."""
        if self._collage_panel_bg_index == index:
            return
        self._collage_panel_bg_index = index
        self.collageBackgroundImageChanged.emit()

    def _ensure_background_picture(self) -> None:
        """Képhátteres módban LEGYEN háttérkép — alapból az első kép.

        ⚠️ Ez **alapértelmezés, nem törvény**: hogy az eredeti magától az
        elsőt választja-e, *erős, de nem megerősített* következtetés (a
        golden-anyag két képhátteres mintájában, `AI2.cxf` és `AI5.cxf`, a
        háttér mindkétszer a csomópontlista első eleme). A felhasználó
        bármikor felülírja „A kijelölt elemek használatá"-val — és
        mindenképp jobb, mint a v0.8.1 üres állapota, ahol a mód átbillent,
        de háttérkép nem lett."""
        nodes = self._nodes()
        if 0 <= self._collage_panel_bg_index < len(nodes):
            return
        self._set_background_index(0 if nodes else -1)

    def _sync_background_index(self, path: str) -> None:
        """A háttér a KÉPET kövesse, ne a rést — és sose maradjon törött.

        A keverés és a csere a képeket a rések között mozgatja: puszta index
        mellett a háttér arra a képre ugrana, ami épp a helyére csúszott.
        Ezért az útvonal a horgony. Ha a kép kikerült a kollázsból, képhátteres
        módban a következő érvényes háttérre (az elsőre) esünk vissza — üres
        előnézetet nem hagyunk."""
        paths = [node.path for node in self._nodes()]
        if path and path in paths:
            self._set_background_index(paths.index(path))
        elif self._collage_panel_bg_mode == "image" and paths:
            self._set_background_index(0)
        else:
            self._set_background_index(-1)

    def _background_image_for_cxf(self) -> str:
        """A `.cxf`-be írandó háttérkép — csak KÉP módban van ilyen (#1009).

        Egyszínű (és átlagszín-) módban üres: a projektfájl akkor a színt
        őrzi, ahogy a golden `AI.cxf` is teszi."""
        self._ensure_collage_panel()
        return (
            self.collageBackgroundImage
            if self._collage_panel_bg_mode == "image"
            else ""
        )


__all__ = ["BACKGROUND_MODES", "CollageBackgroundMixin"]
