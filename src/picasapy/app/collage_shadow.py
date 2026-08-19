"""A vetett árnyék a KOLLÁZS-VÁSZONNAK — a #1021 szelete.

A #977 az árnyékot a magba építette be: a **mentett kép** azóta témánként
helyes árnyékot kap. Az **élő vászon** viszont változatlan maradt — a
felhasználó a v0.8.4-en jelezte, hogy a jelölőnégyzet kapcsolgatása nem
csinál semmit. Ez a szelet adja a vászonnak azt a két dolgot, amiből
árnyékot tud rajzolni:

1. **`collageShadow`** — a geometria **lapegységben** (eltolás, elmosás,
   alfa). Lapegység, mert a vászon szélessége az ablaktól függ, a mentett
   képé 5120: a lapegység (1024, spec 6.1) az egyetlen közös rendszer.
2. **`collageShadowSprite(elmosás, alfa)`** — a kirajzolható **csempe**
   `data:` URL-ként, a `BorderImage` szegélyméretével együtt.

## Egy forrás: a MENTÉS beállítása

A paraméterek a `_render_settings()`-ből jönnek — pontosan abból, amivel a
mentés dolgozik —, és a `picasa_render.shadow_for_settings` számolja ki
őket. A vászon tehát nem tart párhuzamos számítást: nincs mi elváljon.

⚠️ **Az átváltás a MENTÉS lapszélességével történik**, nem úgy, hogy a
képletet 1024-es lapra futtatnánk. Az eltolás képlete additív tagot is
tartalmaz (`+1`, `+2`), ami nem arányos a lapmérettel: 1024-es lapon
számolva az additív tag ötszörösére nagyulna.

## Miért nem shader (`MultiEffect`)

Mérve: a felhasználó gépén a `QtQuick.Effects` modul **nincs telepítve**
(`module "QtQuick.Effects" is not installed`), a CI-n viszont — ahol
`pip install PySide6` fut — megvan. Egy shader-alapú megoldás zöld CI
mellett hagyta volna árnyék nélkül épp azt a gépet, amelyikről a
bejelentés jött. A választott csempe shadert nem használ, tehát a
szoftveres (fejnélküli) háttéren is ugyanúgy rajzolódik — ezért mérhető
képpontokon a CI-ban is.
"""

from __future__ import annotations

import logging

from PySide6.QtCore import Property, Signal, Slot

from picasapy.collage.nodes import SHEET_UNITS
from picasapy.collage.picasa_render import shadow_for_settings
from picasapy.collage.shadow import CellEdgeTooSmall
from picasapy.collage.shadow_sprite import (
    sprite_border,
    sprite_data_url,
    sprite_support,
)

logger = logging.getLogger(__name__)


class CollageShadowMixin:
    """A vászon árnyék-szerződése: egy térkép és egy csempe-kérés."""

    #: A térkép értesítője. A vászon property-kötésen fogyasztja, ezért a
    #: néma-jelzés őre (`scripts/check_dead_signals.py`) helyesen hagyja ki.
    collageShadowChanged = Signal()

    def _wire_collage_shadow(self) -> None:
        """A négy meglévő jelzés átkötése az árnyék értesítőjére.

        Az árnyék NÉGY dologtól függ: a jelölőnégyzettől, a témától, a
        képek számától (a Képkupac léptéke és a rácsok cellaéle abból jön)
        és a lap arányától. Ezeket egyenként újra kibocsátani négy külön
        helyen kellene — és a negyedik előbb-utóbb kimaradna. Egyetlen
        átkötés helyette: ami már ma is jelez, az jelezze ezt is."""
        for jelzes in (
            self.collageShadowsChanged,
            self.collageThemeChanged,
            self.collageClipCountChanged,
            self.collagePageRatioChanged,
        ):
            jelzes.connect(self.collageShadowChanged)

    # -- a geometria -------------------------------------------------------

    @Property("QVariantMap", notify=collageShadowChanged)
    def collageShadow(self) -> dict:
        """A vetett árnyék paraméterei **lapegységben**, vagy üres térkép.

        | kulcs | jelentés |
        |---|---|
        | `offsetX`, `offsetY` | eltolás jobbra-le, lapegységben |
        | `blur` | az elmosás mértéke, lapegységben |
        | `opacity` | 0,4 vagy 0,6 (a téma receptje) |
        | `alpha` | `(egész)(átlátszatlanság · 256)` — 102 vagy 153 |

        Üres térkép, ha a témának nincs árnyéka (Többszörös exponálás, a
        maszk 11. bitje) vagy a jelölőnégyzet ki van kapcsolva."""
        self._ensure_collage_panel()
        beallitas = self._render_settings()
        try:
            keppontban = shadow_for_settings(beallitas, len(self._nodes()))
        except CellEdgeTooSmall as hiba:
            # A rácsos témák 8-képpontos érvényességi kapuja. A mentés
            # ilyenkor hangosan hibázik (ott az a helyes); a vászon nem
            # dőlhet el emiatt — árnyék nélkül rajzol tovább.
            logger.info("A kollázs-vászon árnyéka kimarad: %s", hiba)
            return {}
        if keppontban is None:
            return {}
        keppont_per_egyseg = beallitas.width / SHEET_UNITS
        return {
            "offsetX": keppontban.offset_x / keppont_per_egyseg,
            "offsetY": keppontban.offset_y / keppont_per_egyseg,
            "blur": keppontban.blur / keppont_per_egyseg,
            "opacity": keppontban.opacity,
            "alpha": keppontban.alpha,
        }

    # -- a csempe ----------------------------------------------------------

    @Slot(float, int, result="QVariantMap")
    def collageShadowSprite(self, blur: float, alpha: int) -> dict:
        """A kirajzolható árnyék-csempe — kép ÉS geometria egy kérésben.

        `blur` a vászon **képpontjaiban** értendő (a lapegységben kapott
        elmosás a vászon `unit` szorzójával felnagyítva).

        | kulcs | jelentés |
        |---|---|
        | `url` | `data:image/png;base64,…` — a `BorderImage` forrása |
        | `support` | a haló képpontban: ennyivel lóg túl az árnyék a csempén |
        | `border` | a `BorderImage.border` értéke (a haló kétszerese) |

        Miért egy kérés: két külön forrásból (kép itt, méret ott) a kettő
        előbb-utóbb elválna, és az árnyék elcsúszna a saját csempéjétől."""
        return {
            "url": sprite_data_url(float(blur), int(alpha)),
            "support": sprite_support(float(blur)),
            "border": sprite_border(float(blur)),
        }


__all__ = ["CollageShadowMixin"]
