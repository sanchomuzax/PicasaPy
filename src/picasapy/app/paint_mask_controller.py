"""Az ecset-maszk vezérlő-szelete (#1908) — az `EditController` mixinje.

A festhető-maszkos effektek (`Boost`, `Pixelate`, `Soften`, `PicnikTint`,
`ReanimatedEyeColor`) az eredetiben csak a BEFESTETT területre hatnak. A
render-oldal a #3225 óta tudja fogadni a maszkot, az állapot a
`paint_mask.MaszkAllapot`-ban él — ez a szelet a kettő közé áll: a
felülettől kapja a vonásokat, és a `provider.register()`-be teszi őket.

## Két mért alapérték, és ami NEM mért

A `filterdesc.xml` `BrushSizeAndEraserButton`-ja a `ReanimatedEyeColor`
családjára (`eff:PaintOnEffectBase`) `startValueFactor="0.03"` és
`maximumFactor="0.2"` — ezt vesszük át. ⚠️ A másik család
(`cnt:PaintEffectCanvas`: a maradék négy effekt) a leírásban **semmit** nem
deklarál az ecsethez; ott ugyanezt az alapértéket használjuk, és ezt ki is
mondjuk — SAJÁT döntés, nem mérés.

## A maszk munkamenet-élettartamú

Mérve (#1908, három telepítés `db3`-ában nulla találat): az eredeti sem
tárolja. Képváltásnál eldobjuk.
"""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from picasapy.render.chain_glimmer_handlers import PAINTABLE_MASK_OPS

from .paint_mask import KEZDO_ARANY, MAX_ARANY, MaszkAllapot


class PaintMaskMixin:
    """`paintStroke` / `setPaintBrushRatio` / `setPaintEraser` — az ecset felülete felé."""

    paintMaskChanged = Signal()

    def _init_paint_mask(self) -> None:
        """Az `EditController.__init__` hívja (a mixinek nem definiálnak
        sajátot — a repó konvenciója)."""
        self._paint_mask = MaszkAllapot()
        self._paint_brush = KEZDO_ARANY
        self._paint_eraser = False

    # -- QML-nek kitett állapot ---------------------------------------------

    @Property(bool, notify=paintMaskChanged)
    def paintMaskSupported(self) -> bool:  # noqa: N802 — QML-property-stílus
        """Van-e a láncban festhető-maszkos effekt — az ecset CSAK akkor
        jelenik meg. Bekötetlen eszközt nem mutatunk (#936)."""
        return any(
            op.name.casefold() in PAINTABLE_MASK_OPS for op in self._session.ops
        )

    @Property(float, notify=paintMaskChanged)
    def paintBrushRatio(self) -> float:  # noqa: N802
        """Az ecset sugara a kép rövidebb oldalának arányában."""
        return self._paint_brush

    @Property(bool, notify=paintMaskChanged)
    def paintEraser(self) -> bool:  # noqa: N802
        """Radír-üzemmód (a mért vezérlő méret ÉS radír egyben)."""
        return self._paint_eraser

    @Property(float, constant=True)
    def paintBrushMax(self) -> float:  # noqa: N802
        """A mért felső korlát (`maximumFactor`)."""
        return MAX_ARANY

    # -- slotok --------------------------------------------------------------

    @Slot(float, float)
    def paintStroke(self, x: float, y: float) -> None:  # noqa: N802
        """Egy ecsetvonás-pont a KIRAJZOLT képhez normálva (0…1).

        A felület a kirajzolt (letterboxolt) képhez normál, nem az ablakhoz —
        így a festés a nagyítástól és az illesztéstől függetlenül ugyanoda
        esik, mint a mentett képen.
        """
        if not self.paintMaskSupported:
            return
        self._paint_mask.fess(x, y, self._paint_brush, self._paint_eraser)
        self.paintMaskChanged.emit()
        self._register_preview()

    @Slot(float)
    def setPaintBrushRatio(self, arany: float) -> None:  # noqa: N802
        uj = max(0.005, min(float(arany), MAX_ARANY))
        if uj == self._paint_brush:
            return
        self._paint_brush = uj
        self.paintMaskChanged.emit()

    @Slot(bool)
    def setPaintEraser(self, radir: bool) -> None:  # noqa: N802
        if bool(radir) == self._paint_eraser:
            return
        self._paint_eraser = bool(radir)
        self.paintMaskChanged.emit()

    # -- a gazdának ----------------------------------------------------------

    def _paint_strokes(self) -> tuple:
        """A festés vonásai az előnézet-kérésbe.

        Ha a láncban MÁR NINCS festhető effekt (a felhasználó alkalmazta vagy
        elvetette), a festés is elvesztette az értelmét: ilyenkor magától
        eldobódik. Enélkül egy következő, szintén festhető effekt a korábbi
        vonásokat kapná meg — olyan maszkkal, amit a felületen épp nem is
        látott.
        """
        if not self.paintMaskSupported:
            if not self._paint_mask.ures:
                self._paint_mask.torold()
            return ()
        return self._paint_mask.vonasok

    def _paint_mask_kepvaltas(self, kulcs: str) -> None:
        """Képváltáskor a festés eldobódik (munkamenet-élettartamú)."""
        if self._paint_mask.valts_kepre(str(kulcs)):
            self.paintMaskChanged.emit()


__all__ = ["PaintMaskMixin"]
