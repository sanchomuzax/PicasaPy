"""A kollázs-csomópont: a vászon és a rajzoló KÖZÖS nyelve (#942).

Spec: `docs/specs/kollazs-panel-ui-spec.md` **6.1–6.3**, **6.5**.

## Miért külön modul

A `picasa_render.make_picasa_collage` eredetileg MAGA számolta ki az
elrendezést, tehát egy kézzel átrendezett vásznat nem tudott kirenderelni:
mentéskor a felhasználó mást kapott volna, mint amit lát. A megoldás egy
közös adatszerkezet — a `CollageNode` —, amit a téma pakolója ÁLLÍT ELŐ, a
felhasználó MÓDOSÍT, a rajzoló pedig KIRAJZOL.

Ez a modul szándékosan nem ismeri a `PicasaCollageSettings`-t és a hat témát:
csak csomópontokat rajzol egy vászonra. Így ugyanaz a kód szolgálja ki az élő
előnézetet és a mentést, és önmagában is tesztelhető.

Bemenet/kimenet: OpenCV **BGR** `uint8` képek (a `render.py` konvenciója).
"""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy import cv as cv2
import numpy as np

from .fitting import picasa_round
from .frames import apply_border, polaroid_geometry, white_border_width
from .layout import Placement
from .render import _paste, _rotated_paste, fit_to_frame
from .shadow import ShadowParams, draw_shadow
from .themes import BORDER_THEMES, NOBORDER, POLAROID, WHITEBORDER


# --- A csomópont-modell és a lapegység-koordinátarendszer (#942) -------------

#: A lap belső SZÉLESSÉGE egységben (spec 6.1, `0xcf3f68 = 1/1024`).
#:
#: A csomópontok minden koordinátája és mérete ebben él — nem képpontban —,
#: és a `.cxf` is ezt írja. A képpontra váltás **mindkét tengelyen ugyanazzal
#: az osztóval** történik (`lap.szélesség / 1024`), ezért a lap nem torzít,
#: csak méretez.
SHEET_UNITS = 1024.0

#: Hány tizedesjegyre simítjuk a bal/felső sarkot, MIELŐTT a döntetlent
#: eldöntenénk.
#:
#: A lapegység → képpont oda-vissza váltás lebegőpontos, ezért egy „pontosan
#: félúton" álló érték `n + 0.5 ± 1e-13` alakban jöhet vissza. A maradék bitje
#: platformonként MÁS lehet (más libm, más fordító) — simítás nélkül tehát
#: ugyanaz a kollázs Linuxon és Windowson egy képpontot csúszna, ami pontosan
#: az a fajta néma, csak a felhasználónál jelentkező eltérés, amit kerülni
#: akarunk. Kilenc tizedesjegy jóval a zaj fölött és jóval a valódi
#: alképpontos különbségek alatt van.
_PLACEMENT_DECIMALS = 9

#: A nem található kép helykitöltő csempéjének színei BGR-ben (spec 9.4).
_MISSING_FILL_BGR = (200, 200, 200)
_MISSING_INK_BGR = (120, 120, 120)

#: A Polaroid-felirat tintája a `#D9D9D9` papíron (`frames.POLAROID_PAPER_BGR`).
_CAPTION_INK_BGR = (60, 60, 60)


@dataclass(frozen=True)
class CollageNode:
    """Egy kép helye a kollázs-lapon — a vászon és a rajzoló KÖZÖS nyelve.

    Minden hosszmérték **lapegységben** van (`SHEET_UNITS`), nem képpontban:
    így ugyanaz a csomópont ír le egy 400 képpontos élő előnézetet és a
    belőle mentett 3000 képpontos JPEG-et. A `.cxf` is ezt tárolja.

    | mező | jelentés |
    |---|---|
    | `path` | a kép útvonala (a `.cxf` `+0x48` mezője) |
    | `center_x`, `center_y` | a KIRAJZOLT csempe középpontja lapegységben |
    | `width`, `height` | a csomópont doboza lapegységben, **forgatás előtt**, a kerettel EGYÜTT |
    | `theta` | elforgatás radiánban |
    | `border` | `noborder` / `whiteborder` / `polaroid` |
    | `caption` | a Polaroid-keretre írt felirat |
    | `missing` | a fájl nem található → helykitöltő csempe |
    | `fill` | a doboz kitöltése vágással (rács) vagy arányos beillesztéssel (kupac) |

    **A `width`/`height` a KÜLSŐ, kerettel együtt értendő doboz** (spec 6.2).
    A rajzoló ebből számolja vissza a fotó helyét (`photo_box`), tehát a
    felületnek és a rajzolónak ugyanaz a doboz jelenti ugyanazt — enélkül a
    keretes kép a vásznon és a mentett képen más méretű lenne.

    **A `center_*` a csempe középpontja, nem a fotóé.** A Polaroid-keret alul
    feliratsávot hagy, tehát a kettő NEM esik egybe; a felhasználó azt fogja
    meg és forgatja, amit lát — a csempét.

    A `fill` nincs a spec 6.2 táblázatában, de a rajzolónak szüksége van rá:
    a rácsos témák a cellát hézag nélkül töltik ki (a túllógó rész vágva), az
    Indexkép és a Képkupac ellenben a TELJES képet mutatja. Egy csomópont
    magától nem tudná, melyikről van szó.
    """

    path: Path | str | None = None
    center_x: float = 0.0
    center_y: float = 0.0
    width: float = 0.0
    height: float = 0.0
    theta: float = 0.0
    border: str = NOBORDER
    caption: str = ""
    missing: bool = False
    fill: bool = True

    def __post_init__(self) -> None:
        if self.border not in BORDER_THEMES:
            raise ValueError(f"Ismeretlen képkeret: {self.border!r}")
        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError(
                f"Érvénytelen csomópont-méret: {self.width}×{self.height}"
            )


def sheet_to_pixels(value: float, page_width: int) -> float:
    """Lapegység → képpont. Ugyanaz az osztó mindkét tengelyen (spec 6.1)."""
    if page_width < 1:
        raise ValueError(f"Érvénytelen lapszélesség: {page_width}")
    return value * page_width / SHEET_UNITS


def pixels_to_sheet(value: float, page_width: int) -> float:
    """Képpont → lapegység; a `sheet_to_pixels` megfordítása."""
    if page_width < 1:
        raise ValueError(f"Érvénytelen lapszélesség: {page_width}")
    return value * SHEET_UNITS / page_width


# --- A keret külső és belső doboza ------------------------------------------


def border_growth(photo_width: int, photo_height: int, border: str) -> tuple[int, int]:
    """Mennyivel NŐ a csempe a fotóhoz képest az adott kerettől (szél., mag.).

    A `frames.py` geometriájából számol, nem találgat — ha ott változik a
    képlet, itt is együtt mozog."""
    if photo_width < 1 or photo_height < 1:
        raise ValueError(f"Érvénytelen fotóméret: {photo_width}×{photo_height}")
    if border == NOBORDER:
        return (0, 0)
    if border == WHITEBORDER:
        vastagsag = white_border_width(photo_width, photo_height)
        return (2 * vastagsag, 2 * vastagsag)
    if border == POLAROID:
        geometria = polaroid_geometry(photo_width, photo_height)
        return (
            geometria.outer_width - photo_width,
            geometria.outer_height - photo_height,
        )
    raise ValueError(f"Ismeretlen képkeret: {border!r} (várt: {BORDER_THEMES})")


def outer_box(photo_width: int, photo_height: int, border: str) -> tuple[int, int]:
    """A kerettel együtt értendő KÜLSŐ doboz egy adott fotóméretre."""
    novekmeny = border_growth(photo_width, photo_height, border)
    return (photo_width + novekmeny[0], photo_height + novekmeny[1])


#: Az `outer_box` megfordításának keresési sugara képpontban.
#:
#: A fixpont-iteráció a fehér szegélynél billeghet egyet a helyes érték
#: körül (a vastagság a rövidebb oldal 5%-ának KEREKÍTETT értéke, tehát
#: lépcsős), ezért a fixpont körül még megnézzük a szomszédokat, és azt
#: választjuk, amelyik VISSZAADJA a kért külső dobozt. Így az
#: `photo_box(outer_box(w, h, b), b) == (w, h)` azonosság pontos — erre
#: épül a `make_picasa_collage` bájtazonossága.
_BORDER_SEARCH_RADIUS = 2
_BORDER_FIXPOINT_STEPS = 8


def photo_box(outer_width: int, outer_height: int, border: str) -> tuple[int, int]:
    """A KÜLSŐ dobozból a fotó doboza — az `outer_box` megfordítása.

    Nem analitikus inverz: a keretnövekmény kerekítést tartalmaz, ezért
    fixpont-iterációval közelítünk, majd a fixpont szomszédságában keressük
    azt a fotóméretet, amelyre `outer_box` PONTOSAN a kért külső dobozt
    adja. Ha nincs ilyen (a külső doboz nem is állhatott elő kerettel), a
    legjobb közelítés marad."""
    if outer_width < 1 or outer_height < 1:
        raise ValueError(f"Érvénytelen külső doboz: {outer_width}×{outer_height}")
    if border == NOBORDER:
        return (outer_width, outer_height)

    szeles, magas = outer_width, outer_height
    for _ in range(_BORDER_FIXPOINT_STEPS):
        no_szeles, no_magas = border_growth(szeles, magas, border)
        kov_szeles = max(1, outer_width - no_szeles)
        kov_magas = max(1, outer_height - no_magas)
        if (kov_szeles, kov_magas) == (szeles, magas):
            break
        szeles, magas = kov_szeles, kov_magas

    sugar = range(-_BORDER_SEARCH_RADIUS, _BORDER_SEARCH_RADIUS + 1)
    for eltolas_w in sugar:
        for eltolas_h in sugar:
            jelolt_w = szeles + eltolas_w
            jelolt_h = magas + eltolas_h
            if jelolt_w < 1 or jelolt_h < 1:
                continue
            if outer_box(jelolt_w, jelolt_h, border) == (outer_width, outer_height):
                return (jelolt_w, jelolt_h)
    return (szeles, magas)


# --- A rajzoló ---------------------------------------------------------------


def _origin(center: float, extent: int) -> int:
    """A csempe bal (felső) sarka a középpontjából, egészre igazítva.

    A szabály: a LEGKÖZELEBBI egész, döntetlennél a bal/felső felé
    (`ceil(v − 0.5)`). Ez a látszólag apró részlet dönti el, hogy a
    refaktor bájtazonos maradt-e: a rácsos cellákban az érték pontosan
    félúton áll, és ott a `floor`-t kell hoznia; a Képkupac folytonos
    középpontjainál ellenben a legközelebbi egészre kell kerekítenie.

    A döntetlen eldöntése ELŐTT simítunk (`_PLACEMENT_DECIMALS`), különben a
    lapegység-váltás lebegőpontos maradéka platformonként más irányba
    billentené."""
    return math.ceil(round(center - extent / 2.0, _PLACEMENT_DECIMALS) - 0.5)


def _missing_tile(width: int, height: int) -> np.ndarray:
    """Helykitöltő csempe a nem található képnek (spec 9.4).

    A hiányzó kép NEM tűnhet el némán: a felhasználónak látnia kell, hogy a
    kollázsban lyuk van, különben azt hiszi, ő törölte."""
    tile = np.empty((max(1, height), max(1, width), 3), dtype=np.uint8)
    tile[:, :] = _MISSING_FILL_BGR
    magas, szeles = tile.shape[:2]
    cv2.rectangle(tile, (0, 0), (szeles - 1, magas - 1), _MISSING_INK_BGR, 1)
    cv2.line(tile, (0, 0), (szeles - 1, magas - 1), _MISSING_INK_BGR, 1)
    cv2.line(tile, (szeles - 1, 0), (0, magas - 1), _MISSING_INK_BGR, 1)
    return tile


def _draw_polaroid_caption(
    tile: np.ndarray, caption: str, photo_width: int, photo_height: int
) -> None:
    """A képfelirat a Polaroid-keret alsó sávjába, HELYBEN rajzolva.

    A felirat **csak** a Polaroid keretnél jelenik meg — ezt a buboréksúgó
    is kimondja („…szövegként való megjelenítése *Polaroid fényképezőgép*
    szegélyű képeken"). A tipográfia a MIÉNK: az eredeti bitmap-betűkészlete
    nem szállítható, a sáv geometriája viszont a `frames.polaroid_geometry`
    dekompilált értékeiből jön."""
    szoveg = caption.strip()
    if not szoveg:
        return
    geometria = polaroid_geometry(photo_width, photo_height)
    sav_teteje = geometria.photo_y + photo_height
    sav_magassag = geometria.caption_height
    if sav_magassag < 6:
        return
    hasznos = max(1, geometria.outer_width - 2 * geometria.margin)
    skala = max(0.25, sav_magassag / 44.0)
    vastagsag = max(1, round(skala * 1.4))
    (szeles, magas), _ = cv2.getTextSize(
        szoveg, cv2.FONT_HERSHEY_SIMPLEX, skala, vastagsag
    )
    if szeles > hasznos:
        skala = max(0.2, skala * hasznos / szeles)
        vastagsag = max(1, round(skala * 1.4))
        (szeles, magas), _ = cv2.getTextSize(
            szoveg, cv2.FONT_HERSHEY_SIMPLEX, skala, vastagsag
        )
    x = max(0, (geometria.outer_width - szeles) // 2)
    y = sav_teteje + (sav_magassag + magas) // 2
    if y >= tile.shape[0]:
        return
    cv2.putText(
        tile,
        szoveg,
        (x, y),
        cv2.FONT_HERSHEY_SIMPLEX,
        skala,
        _CAPTION_INK_BGR,
        vastagsag,
        cv2.LINE_AA,
    )


def _node_tile(
    node: CollageNode, image: np.ndarray | None, page_width: int
) -> np.ndarray:
    """Egy csomópont KIRAJZOLT csempéje: illesztés, keret, felirat.

    A csempe méretét a KÉP adja (a dobozba illesztve), nem a doboz maga —
    arányos illesztésnél (`fill=False`) a kép kisebb lehet a doboznál."""
    doboz_w = max(1, picasa_round(sheet_to_pixels(node.width, page_width)))
    doboz_h = max(1, picasa_round(sheet_to_pixels(node.height, page_width)))
    if image is None:
        return _missing_tile(doboz_w, doboz_h)
    foto_w, foto_h = photo_box(doboz_w, doboz_h, node.border)
    foto = fit_to_frame(image, max(1, foto_w), max(1, foto_h), fill=node.fill)
    tile = apply_border(foto, node.border)
    if node.border == POLAROID and node.caption:
        _draw_polaroid_caption(tile, node.caption, foto.shape[1], foto.shape[0])
    return tile


def draw_nodes(
    canvas: np.ndarray,
    nodes: Sequence[CollageNode],
    images: Sequence[np.ndarray | None],
    page_width: int,
    shadow: ShadowParams | None = None,
) -> None:
    """A KÖZÖS rajzoló: a csomópontokat a vászonra teszi, rajzolási sorrendben.

    A lista sorrendje a rajzolási sorrend: a **0. index van legalul, az
    utolsó legfelül** (`canvas.py` is ezt tartja). `images[i]` a már
    dekódolt kép, vagy `None`, ha nincs meg — akkor helykitöltő csempe jön.

    Elrendezést NEM számol: pontosan oda rajzol, ahova a csomópont mutat.

    A `shadow` a téma árnyék-paraméterei (#977) vagy `None`. Minden csempének
    a SAJÁT árnyéka közvetlenül előtte rajzolódik, nem előre az összes: így a
    felül lévő kép árnyéka ráesik az alatta lévőre — ez adja a Képkupac
    mélységét. A rajzoló nem ismeri a témát; a paramétereket a hívó adja."""
    for node, image in zip(nodes, images, strict=True):
        tile = _node_tile(node, image, page_width)
        kozep_x = sheet_to_pixels(node.center_x, page_width)
        kozep_y = sheet_to_pixels(node.center_y, page_width)
        x = _origin(kozep_x, tile.shape[1])
        y = _origin(kozep_y, tile.shape[0])
        if shadow is not None:
            draw_shadow(
                canvas,
                x=x,
                y=y,
                width=tile.shape[1],
                height=tile.shape[0],
                theta=node.theta,
                params=shadow,
            )
        if node.theta:
            _rotated_paste(
                canvas,
                tile,
                Placement(
                    x=x,
                    y=y,
                    width=tile.shape[1],
                    height=tile.shape[0],
                    angle=math.degrees(node.theta),
                ),
            )
        else:
            _paste(canvas, tile, x, y)


__all__ = [
    "SHEET_UNITS",
    "CollageNode",
    "ShadowParams",
    "border_growth",
    "draw_nodes",
    "outer_box",
    "photo_box",
    "pixels_to_sheet",
    "sheet_to_pixels",
]
