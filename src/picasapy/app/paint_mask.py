"""A festett ecset-maszk munkamenet-állapota (#1908).

Csak a `ReanimatedEyeColor` hat a **befestett** területre; a `Boost`,
`Pixelate`, `Soften` és `PicnikTint` ecset nélkül a teljes képre fut
(#3541). A render-oldal a #3225 óta tudja fogadni a maszkot
(`chain.apply_filters(paint_mask=…)`). Ez a modul tartja a munkamenetben
festett vonásokat.

## A PicasaPy új ecsetvonásainak tárolása még nincs bekötve

Az eredeti Picasa a Vámpírszem vonásait a `filters=` sorban tárolja. A
meglévő sorokból a maszkgenerátor a #4097-es ini-parserrel már beolvassa a
keménységet és a pontokat. A PicasaPy-ban létrehozott vonások egyelőre csak a
szerkesztő-munkamenet memóriájában élnek; tartós tárolásuk külön feladat
(#4046), ezért képváltásnál eldobódnak.

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

#: A mért ecset-alapértékek a Vámpírszem `eff:PaintOnEffectBase` családjából.
KEZDO_ARANY = 0.03
MAX_ARANY = 0.2

#: A `filterdesc.xml` `_nBrushHardness` mezőjének mért alapértéke.
KEZDO_KEMENYSEG = 0.15

#: Korábbi megjelenítések fix lágy peremének értéke; a maszk már profil-LUT-ot
#: használ, ezt csak a kompatibilitási tesztek és külső hivatkozások őrzik.
PEREM_ARANY = 0.15


# A #4096 15 pontos CircularBrush-mérései. A LUT bemenete a kör szélétől
# befelé mért, 0…1 közötti sugárarány; a táblázat a közös fedettséget tárolja.
_PROFIL_MINTAK = {
    0.0: (
        (0, 0.029239766, 0.048274282, 0.067308798, 0.124412335,
         0.181515887, 0.219584912, 0.257653952, 0.40993005, 0.4860681,
         0.543171644, 0.600275218, 0.695447743, 0.866758406, 1),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
    0.15: (
        (0, 0.171069175, 0.187322721, 0.203576267, 0.25233689,
         0.301097542, 0.333604634, 0.366111726, 0.496140063, 0.561154246,
         0.609914899, 0.658675551, 0.739943266, 0.886225164, 1),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
    0.5: (
        (0, 0.48120302, 0.491375506, 0.501547992, 0.532065451,
         0.56258291, 0.582927942, 0.603272915, 0.684652805, 0.725342751,
         0.755860269, 0.786377728, 0.83724016, 0.928792596, 1),
        (0, 0, 0, 2, 12, 32, 50, 69, 155, 189, 208, 223, 240, 252, 255),
    ),
}

# h=1 bypasses the 15-point interpolator. These are the measured left outer
# edge and right inner edge; the right outer edge is zero in the complete
# 21×21 and 41×41 native hard-brush middle rows (#4096).
_KEMENY_ELEK = {20: (241, 225), 40: (248, 232)}


def _lagy_profil(u: np.ndarray, kemenyseg: float) -> np.ndarray:
    """A legközelebbi mért lágy LUT-ok közti lineáris keménység-interpoláció."""

    def lut(hardness: float) -> np.ndarray:
        xs, ys = _PROFIL_MINTAK[hardness]
        return np.interp(u, xs, ys).astype(np.float32) / np.float32(255)

    if kemenyseg <= 0.15:
        also, felso = lut(0.0), lut(0.15)
        arany = np.float32(kemenyseg / 0.15)
    else:
        also, felso = lut(0.15), lut(0.5)
        arany = np.float32((kemenyseg - 0.15) / 0.35)
    return also + (felso - also) * arany


def _kemeny_profil(
    tavolsag: np.ndarray, sugar: float, dx: np.ndarray
) -> np.ndarray:
    """A mért h=1 sorokból felépített kétoldali, keményecset-profil."""
    meret = int(round(2 * sugar))
    if meret in _KEMENY_ELEK and abs(2 * sugar - meret) < 1e-5:
        bal_el, jobb_belso = _KEMENY_ELEK[meret]
        bal = np.interp(
            tavolsag,
            (0, sugar - 1, sugar),
            (255, 255, bal_el),
            left=255,
            right=0,
        )
        jobb = np.interp(
            tavolsag,
            (0, sugar - 2, sugar - 1, sugar),
            (255, 255, jobb_belso, 0),
            left=255,
            right=0,
        )
        return np.where(dx < 0, bal, jobb).astype(np.float32) / np.float32(255)
    return np.clip(sugar + 0.5 - tavolsag, 0, 1).astype(np.float32)


def _ecset_fedes(
    u: np.ndarray,
    tavolsag: np.ndarray,
    dx: np.ndarray,
    sugar: float,
    kemenyseg: float,
) -> np.ndarray:
    """A CircularBrush normalizált fedettségprofilja alfa-képbe skálázva."""
    hardness = float(np.clip(kemenyseg, 0.0, 1.0))
    if hardness >= 1.0:
        return _kemeny_profil(tavolsag, sugar, dx)
    lagy = _lagy_profil(u, hardness)
    if hardness <= 0.5:
        return lagy
    kemeny = _kemeny_profil(tavolsag, sugar, dx)
    arany = np.float32((hardness - 0.5) / 0.5)
    return lagy + (kemeny - lagy) * arany


@dataclass(frozen=True)
class Vonas:
    """Egy ecsetvonás-pont a KIRAJZOLT képhez normálva (0…1).

    `sugar` szintén normált (a kép RÖVIDEBB oldalához mérve, hogy a kör
    álló és fekvő képen is kör legyen). `hardness` a maszk alfa-profilját
    választja ki; az alapértéke 0.15. `torol=True` a radír.
    """

    x: float
    y: float
    sugar: float
    torol: bool = False
    hardness: float = KEZDO_KEMENYSEG
    alpha: float = 1.0


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

    def fess(
        self,
        x: float,
        y: float,
        sugar: float,
        torol: bool = False,
        hardness: float = KEZDO_KEMENYSEG,
    ) -> None:
        """Egy vonás-pont hozzáfűzése; a koordináták 0…1-re vágódnak."""
        self._vonasok = (
            *self._vonasok,
            Vonas(
                x=float(np.clip(x, 0.0, 1.0)),
                y=float(np.clip(y, 0.0, 1.0)),
                sugar=max(float(sugar), MIN_SUGAR_ARANY),
                torol=bool(torol),
                hardness=float(hardness),
            ),
        )

    def torold(self) -> None:
        """A teljes festés elvetése (a maszk üres lesz)."""
        self._vonasok = ()

    def allit(self, vonasok) -> None:
        """A vonások teljes cseréje (#3649: az „aa" fókuszváltás pufferje —
        a két fél festése EGYMÁSSAL cserélődik, nem ürül)."""
        self._vonasok = tuple(vonasok)

    def maszk(self, magassag: int, szelesseg: int) -> np.ndarray | None:
        """A vonásokból számolt (H, W) float32 [0,1] maszk, vagy `None`.

        `None`, ha nincs festés — így a hívó a maszk NÉLKÜLI útra mehet, és a
        lánc viselkedése bitre a régi marad.

        A radír-vonások a már festett súlyt VONJÁK le, a sorrendben: aki
        később festett, az ír felül. A bélyeg alfa-profilját a vonás
        keménysége választja ki a mért CircularBrush-görbékből.
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
            u = np.clip((r - tav) / r, 0.0, 1.0)
            folt = _ecset_fedes(
                u,
                tav,
                xs - cx,
                r,
                vonas.hardness,
            )
            folt = np.clip(folt * vonas.alpha, 0.0, 1.0)
            if vonas.torol:
                maszk = np.minimum(maszk, 1.0 - folt)
            else:
                maszk = np.maximum(maszk, folt)
        return maszk.astype(np.float32)


def maszk_vonasokbol(
    vonasok, magassag: int, szelesseg: int, *, filters=()
) -> np.ndarray | None:
    """Vonás-sorozat → (H, W) float32 [0,1] maszk, vagy `None`, ha nincs vonás.

    Azért önálló függvény (és nem csak metódus), mert az előnézet-szolgáltató
    a VONÁSOKAT kapja meg (nem az állapot-objektumot), és a bitképet a saját
    felbontásán állítja elő — ugyanaz a festés így az előnézeten és a mentett
    képen is ugyanoda esik. A `filters` opcionális szűrőműveleteiből a
    #4097-es ini-parserrel olvassa ki a már mentett Vámpírszem-vonásokat.
    """
    if magassag <= 0 or szelesseg <= 0:
        return None
    mentett = _ini_vonasok(filters, magassag, szelesseg)
    allapot = MaszkAllapot()
    allapot._vonasok = (*mentett, *tuple(vonasok))  # noqa: SLF001 — ugyanaz a modul
    return allapot.maszk(magassag, szelesseg)


def van_mentett_ecsetvonas(filters) -> bool:
    """Van-e a szűrőláncban szerializált Vámpírszem-vonásrekord."""
    return any(
        getattr(op, "name", None) == "ReanimatedEyeColor"
        and len(getattr(op, "params", ())) > 3
        for op in filters
    )


def _ini_vonasok(filters, magassag: int, szelesseg: int) -> tuple[Vonas, ...]:
    """A #4097 parserével olvasott ini-vonásokat maszkpontokká alakítja."""
    if not filters:
        return ()

    from picasapy.ini.eye_strokes import EyeStroke, parse_reanimated_eye_color

    rovidebb = float(min(magassag, szelesseg))
    vonasok = []
    for op in filters:
        if getattr(op, "name", None) != "ReanimatedEyeColor":
            continue
        modell = parse_reanimated_eye_color(op)
        for record in modell.strokes:
            if not isinstance(record, EyeStroke):
                continue
            sugar = max(record.style.size * 0.5, 0.5) / rovidebb
            vonasok.extend(
                Vonas(
                    x=pont.x,
                    y=pont.y,
                    sugar=sugar,
                    torol=bool(record.style.mode),
                    hardness=record.style.hardness,
                    alpha=record.alpha,
                )
                for pont in record.points
            )
    return tuple(vonasok)


__all__ = [
    "KEZDO_ARANY",
    "KEZDO_KEMENYSEG",
    "MAX_ARANY",
    "MIN_SUGAR_ARANY",
    "PEREM_ARANY",
    "MaszkAllapot",
    "maszk_vonasokbol",
    "van_mentett_ecsetvonas",
    "Vonas",
]
