"""A megjelenítési mód a FELÜLET színein (#3070).

## Miért a téma színein, és nem a kirajzolt jelenetgráfon

A hatókör-szerződés (`docs/specs/picasa-megjelenitesi-modok.md` 11.7) MÉRT
követelése: a módot **egy** helyen kell alkalmazni, a jelenetgráf gyökerére.
Nálunk a kézenfekvő út (`ShaderEffect` a burkoló `Item`-en) **elesett** — a
#3070 négy próbája kimérte, hogy a software jelenetgráf-háttér a shadert
egyáltalán nem futtatja le (még a tartalomfüggetlen, állandó pirosat sem).

A módok szabályai viszont **képpontonkénti, tiszta függvények**, tehát
ugyanazt adják, ha nem a kirajzolt képpontokra, hanem a felület **lapos
színeire** alkalmazzuk őket. A `Theme.qml` egyetlen szingleton: ha minden
nyilvános színe egy közös átvezetőn megy át, a menük, sávok és hátterek a
mód szerint világosodnak — shader nélkül, és offscreen platformon is
**mérhetően**.

## Miért EGY menetben

A 103 szín egyetlen `1 × N × 3` tömbbe kerül, és **egy** `apply_display_mode`
hívás dolgozza fel. Így a mód szabálya bitre ugyanaz, mint a képen (nincs
QML-be másolt színművelet — a hét szabály közül három kereszt-csatornás:
`bw`, `sepia`, `overflow`), és a költség egy kis tömbművelet, nem 103.

## Az ALFA érintetlen

A módok RGB-n dolgoznak; a tokenek egy része áttetsző (`selectionDim`
`#8f2f2f2f`, a tálca-pirula `#a822689a`, a `logoDisc` világos ága
`#00ffffff`). Az alfát a bemenetről vesszük át változatlanul — az eredeti
átalakítók sem nyúlnak hozzá (spec 5.4/5.5: „az alfa érintetlen").

## Az `overflow` BENNE VAN — és ez mért döntés

A túlcsordulás-jelölés (`ID_VIEW_OV`) a tökéletesen fehér képpontokat
`#FF7F7F`-re festi, tehát a felület fehér paneljeit is átszínezi. Ez nem
tévedés: a 11.7 szerint az eredeti **a gyökéren** alkalmazza a módot, tehát a
felület képpontjai ugyanazt a kezelést kapják, mint a fotó. Ha egy későbbi
képernyőkép az ellenkezőjét mutatja, a kizárás egy sor — de találgatásból
nem hagyjuk ki.
"""

from __future__ import annotations

from collections.abc import Mapping

import numpy as np
from PySide6.QtGui import QColor

from ..render.display_modes import apply_display_mode, display_mode_changes_pixels


def theme_palette(tokens: Mapping[str, QColor], mode: str) -> dict[str, str]:
    """Tokennév → átalakított szín (`#AARRGGBB`), EGY menetben.

    Üres szótárral tér vissza, ha a mód nem mozdít képpontot (`normal`,
    `auto`, a meg nem valósított módok és az ismeretlen azonosító) — a
    `Theme.qml` üres palettán a NYERS értékeket adja, tehát a felület képe
    ilyenkor nem mozdul.
    """
    if not display_mode_changes_pixels(mode) or not tokens:
        return {}

    nevek = list(tokens)
    tomb = np.array(
        [[(c.red(), c.green(), c.blue()) for c in (tokens[n] for n in nevek)]],
        dtype=np.uint8,
    )
    atalakitott = apply_display_mode(tomb, mode)
    if atalakitott is None:
        return {}

    paletta: dict[str, str] = {}
    for i, nev in enumerate(nevek):
        r, g, b = (int(x) for x in atalakitott[0, i])
        # az alfa a BEMENETRŐL jön: a módok nem nyúlnak hozzá
        szin = QColor(r, g, b, tokens[nev].alpha())
        paletta[nev] = szin.name(QColor.NameFormat.HexArgb)
    return paletta


def qobject_color_tokens(objektum) -> dict[str, QColor]:
    """Egy QObject SAJÁT szín-tulajdonságai: név → `QColor`.

    A `Theme.nyers` belső rétegét járja be a Qt metaobjektumán — így egy
    JÖVŐBEN hozzáadott token magától bekerül, felsorolás nélkül.
    """
    mo = objektum.metaObject()
    tokenek: dict[str, QColor] = {}
    for i in range(mo.propertyOffset(), mo.propertyCount()):
        p = mo.property(i)
        if p.typeName() != "QColor":
            continue
        ertek = objektum.property(p.name())
        if isinstance(ertek, QColor):
            tokenek[p.name()] = ertek
    return tokenek
