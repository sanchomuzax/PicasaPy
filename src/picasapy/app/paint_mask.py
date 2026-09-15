"""A festett ecset-maszk munkamenet-állapota (#1908).

Öt effekt (`Boost`, `Pixelate`, `Soften`, `PicnikTint`,
`ReanimatedEyeColor`) az eredetiben csak a **befestett** területre hat; a
render-oldal a #3225 óta tudja fogadni a maszkot
(`chain.apply_filters(paint_mask=…)`). Ez a modul tartja azt, amit a
felhasználó festett.

## Miért NEM a `.picasa.ini`-ben

Mérve (#1908, három telepítés `db3`-ában nulla találat): az eredeti Picasa a
festett maszkot **nem tárolja** — a maszk a munkamenet végéig él. Ezért ez az
állapot a memóriában van, és képváltásnál eldobódik.

## A vonások, nem a bitkép

Az állapot **vonásokat** (`Vonas`) tart, nem kész bitképet: a felület a
KIRAJZOLT képhez normált koordinátákat ad (0…1), a bitkép pedig a kért
felbontáson áll elő (`maszk()`). Így ugyanaz a festés az előnézeten és a
mentett képen is ugyanoda esik — a nagyítástól és az illesztéstől
függetlenül.

A modul TISZTA: a bemenetét nem mutálja, és semmit nem ír lemezre.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np

#: A legkisebb értelmes ecset-átmérő a KIRAJZOLT kép arányában. A mért
#: `startValueFactor = 0.03` / `maximumFactor = 0.2` (a `filterdesc.xml`
#: `BrushSizeAndEraserButton`-ja, `eff:PaintOnEffectBase`) a KEZDŐ és a
#: MAXIMÁLIS méret; ez itt csak az alsó korlát, hogy a nulla sugarú vonás ne
#: legyen érzéketlen kattintás.
MIN_SUGAR_ARANY = 0.002

#: A mért ecset-alapértékek (`eff:PaintOnEffectBase`). ⚠️ A másik család
#: (`cnt:PaintEffectCanvas`: Boost, Pixelate, Soften, PicnikTint) a
#: `filterdesc.xml`-ben SEMMIT nem deklarál ezekhez — ott ezek a mi
#: döntésünk, és ezt ki is mondjuk (#1908).
KEZDO_ARANY = 0.03
MAX_ARANY = 0.2

#: A perem lágyítása a sugár arányában — a mért `_nBrushHardness = 0.15`
#: „keménység" komplementere: a lágy sáv a sugár 15%-a.
PEREM_ARANY = 0.15


@dataclass(frozen=True)
class Vonas:
    """Egy ecsetvonás-pont a KIRAJZOLT képhez normálva (0…1).

    `sugar` szintén normált (a kép RÖVIDEBB oldalához mérve, hogy a kör
    álló és fekvő képen is kör legyen). `torol=True` a radír.
    """

    x: float
    y: float
    sugar: float
    torol: bool = False


class MaszkAllapot:
    """A festett maszk munkamenet-állapota — vonásokból, képenként."""

    def __init__(self) -> None:
        self._vonasok: tuple[Vonas, ...] = ()
        self._kulcs: str = ""

    @property
    def vonasok(self) -> tuple[Vonas, ...]:
        return self._vonasok

    @property
    def ures(self) -> bool:
        return not self._vonasok

    def valts_kepre(self, kulcs: str) -> bool:
        """Képváltás: MÁS képnél a festés eldobódik.

        `True`, ha tényleg váltottunk (a hívó ilyenkor újraszámolja az
        előnézetet). Ugyanarra a kulcsra hívva nem csinál semmit — a
        felület sokszor újraköti ugyanazt.
        """
        if kulcs == self._kulcs:
            return False
        self._kulcs = kulcs
        self._vonasok = ()
        return True

    def fess(self, x: float, y: float, sugar: float, torol: bool = False) -> None:
        """Egy vonás-pont hozzáfűzése. A koordináták 0…1-re vágódnak."""
        self._vonasok = (
            *self._vonasok,
            Vonas(
                x=float(np.clip(x, 0.0, 1.0)),
                y=float(np.clip(y, 0.0, 1.0)),
                sugar=max(float(sugar), MIN_SUGAR_ARANY),
                torol=bool(torol),
            ),
        )

    def torold(self) -> None:
        """A teljes festés elvetése (a maszk üres lesz)."""
        self._vonasok = ()

    def maszk(self, magassag: int, szelesseg: int) -> np.ndarray | None:
        """A vonásokból számolt (H, W) float32 [0,1] maszk, vagy `None`.

        `None`, ha nincs festés — így a hívó a maszk NÉLKÜLI útra mehet, és a
        lánc viselkedése bitre a régi marad.

        A radír-vonások a már festett súlyt VONJÁK le, a sorrendben: aki
        később festett, az ír felül. A perem lágy (`PEREM_ARANY`), ahogy a
        mért `_nBrushHardness = 0.15` kéri.
        """
        if not self._vonasok or magassag <= 0 or szelesseg <= 0:
            return None
        ys = np.arange(magassag, dtype=np.float32)[:, None] + 0.5
        xs = np.arange(szelesseg, dtype=np.float32)[None, :] + 0.5
        maszk = np.zeros((magassag, szelesseg), dtype=np.float32)
        rovidebb = float(min(magassag, szelesseg))
        for vonas in self._vonasok:
            cx = vonas.x * szelesseg
            cy = vonas.y * magassag
            r = max(vonas.sugar * rovidebb, 0.5)
            tav = np.hypot(xs - cx, ys - cy)
            lagy = max(r * PEREM_ARANY, 1e-6)
            folt = np.clip((r - tav) / lagy + 0.5, 0.0, 1.0)
            if vonas.torol:
                maszk = np.minimum(maszk, 1.0 - folt)
            else:
                maszk = np.maximum(maszk, folt)
        return maszk.astype(np.float32)


def maszk_vonasokbol(
    vonasok, magassag: int, szelesseg: int
) -> np.ndarray | None:
    """Vonás-sorozat → (H, W) float32 [0,1] maszk, vagy `None`, ha nincs vonás.

    Azért önálló függvény (és nem csak metódus), mert az előnézet-szolgáltató
    a VONÁSOKAT kapja meg (nem az állapot-objektumot), és a bitképet a saját
    felbontásán állítja elő — ugyanaz a festés így az előnézeten és a mentett
    képen is ugyanoda esik.
    """
    allapot = MaszkAllapot()
    allapot._vonasok = tuple(vonasok)  # noqa: SLF001 — ugyanaz a modul
    return allapot.maszk(magassag, szelesseg)


__all__ = [
    "KEZDO_ARANY",
    "MAX_ARANY",
    "MIN_SUGAR_ARANY",
    "PEREM_ARANY",
    "MaszkAllapot",
    "maszk_vonasokbol",
    "Vonas",
]
