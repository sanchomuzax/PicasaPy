"""A Picasa-hű kollázs RAJZOLÓJA — a hat elrendezés és a három keret (#431).

## Miért külön modul

A #431 magja (`pile`, `packing`, `regular_grid`, `contact_sheet`,
`multi_exposure`, `frames`, `rects`, `themes`) elkészült és 214 teszt fedte,
**de senki nem hívta** — a `render.make_collage` a #29-es, SAJÁT TERVEZÉSŰ
négy elrendezésen maradt. A kollázs tehát működött, csak nem a Picasa
elrendezéseivel. Ez a modul köti össze a kettőt: itt fut össze a hat téma,
a keretek és a közös illesztő.

A régi `render.make_collage` egyelőre MEGMARAD (a `.picasa.ini`/API
kompatibilitás miatt), de a felület mostantól ezt hívja.

## A hat téma és a hozzájuk tartozó mag

| téma (`.cxf` kulcs) | felületi név | a geometriát adó modul |
|---|---|---|
| `picturepile` | Képkupac | `pile.pile_layout` |
| `picturegrid` | Mozaik | `packing.pack` |
| `framegrid` | Képkockamozaik | `packing.pack` **korláttal** |
| `regulargrid` | Rács | `regular_grid` |
| `contactsheet` | Indexkép | `regular_grid` + fejléc |
| `multiexp` | Többszörös exponálás | `multi_exposure.blend_multi_exposure` |

⚠️ A `themes.py` csapdája itt is él: a felületi „Mozaik" kulcsa
`picturegrid`, a „Rács"-é `regulargrid`. A `.cxf` ezeket írja ki, tehát a
kettő felcserélése olvashatatlan projektfájlt adna.

Bemenet/kimenet: OpenCV **BGR** `uint8` képek (a `render.py` konvenciója).
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .fitting import MsvcRandom, fit_inside
from .frames import apply_border
from .multi_exposure import blend_multi_exposure
from .packing import pack
from .pile import pile_layout, pile_top_left
from .rects import NormRect, to_pixel_rects
from .regular_grid import regular_grid_rects, regular_grid_shape
from .render import CollageReport, _decode, _paste, _rotated_paste, fit_to_frame
from .themes import (
    BORDER_THEMES,
    COLLAGE_THEMES,
    THEME_CAPABILITIES,
    CONTACTSHEET,
    FRAMEGRID,
    MULTIEXP,
    NOBORDER,
    PICTUREGRID,
    PICTUREPILE,
    REGULARGRID,
)

_DEFAULT_WIDTH = 1600
_DEFAULT_HEIGHT = 1200

#: A Képkockamozaik hangsúlyos, KÖZPONTI képének helye a lapon.
#:
#: ⚠️ **Közelítés, tudatosan.** A `framegrid` valódi pakolója a
#: `CLocationTree` (spec 1.9.14), amelynek csak a VÁZA van visszafejtve:
#: időkorlátos, véletlen újrapróbálkozású keresés, ahol a rögzített képek
#: `(x0,y0,x1,y1)` téglalapot és egy „van már helye" jelzőt kapnak. A pontos
#: keresés még nincs meg, ezért itt a rögzített kép egyszerűen a középső
#: területre kerül, a többi pedig az alap pakolóval köré. A külön jegy: #916.
_FRAMEGRID_CENTER = NormRect(0.25, 0.25, 0.75, 0.75)

#: Az Indexkép fejlécsávja a lap magasságának ennyied része.
_HEADER_RATIO = 0.08


@dataclass(frozen=True)
class PicasaCollageSettings:
    """A Picasa kollázs-panel beállításai.

    `theme` a `themes.COLLAGE_THEMES` egyike, `border` a
    `themes.BORDER_THEMES` egyike. A `spacing` a „Rács vastagsága" csúszka
    **0…1** értéke (nem képpont) — a `rects.to_pixel_rects` így várja.
    `background` BGR hármas.
    """

    theme: str = PICTUREGRID
    border: str = NOBORDER
    width: int = _DEFAULT_WIDTH
    height: int = _DEFAULT_HEIGHT
    background: tuple[int, int, int] = (255, 255, 255)
    spacing: float = 0.0
    seed: int = 0
    caption: str = ""
    #: A „Beállítás képkockaközéppontként" gomb eredménye: melyik kép kapja
    #: a hangsúlyos középső helyet a Képkockamozaikban. `None` esetén NINCS
    #: rögzített kép — és ilyenkor az eredeti is az alap (Mozaik-)pakolóra
    #: esik vissza (spec 1.9.14: „a `CLocationTree` nem helyettesíti, hanem
    #: kiegészíti az alap algoritmust").
    frame_center: int | None = None
    #: Rajzoljunk-e árnyékot. `None` = a téma alapértelmezése (a maszk
    #: 14. bitje) — ez az eredeti viselkedése, ld. `effective_shadow`.
    shadow: bool | None = None

    @property
    def effective_border(self) -> str:
        """A ténylegesen alkalmazott képkeret — a téma képességével szűrve.

        #923: a Picasában a keretválasztó CSAK a Képkupacnál és az
        Indexképnél látszik (a maszk 9. bitje). A többi témánál a beállítás
        elő sem állítható a felületen, ezért itt **figyelmen kívül marad**.

        Miért nem hiba, hanem elhagyás: a `.cxf` projektfájl tartalmazhat
        sávon kívüli értéket (kézzel szerkesztve, vagy régebbi verzióból),
        és a round-trip elv szerint azt MEGŐRIZZÜK — csak nem rajzoljuk ki.
        A tárolt `border` ezért változatlan marad; a renderelő ezt a
        property-t használja.
        """
        return self.border if THEME_CAPABILITIES[self.theme].borders else NOBORDER

    @property
    def effective_spacing(self) -> float:
        """A ténylegesen alkalmazott térköz — a téma képességével szűrve.

        A térköz-csúszka a három rácsos témánál látszik (10. bit); a
        Képkupacnál, az Indexképnél és a Többszörös exponálásnál nincs
        értelmezve. Ld. `effective_border` a megőrzés indoklásáért.
        """
        return self.spacing if THEME_CAPABILITIES[self.theme].spacing else 0.0

    @property
    def effective_shadow(self) -> bool:
        """Rajzolunk-e árnyékot. A 11. bit engedélyezi, a 14. az ALAPÉRTÉKE.

        A Többszörös exponálásnál az árnyék tiltott (a maszk 11. bitje 0),
        a Képkupacnál és az Indexképnél alapból BE, a többinél KI.
        """
        képesség = THEME_CAPABILITIES[self.theme]
        if not képesség.shadow:
            return False
        return képesség.shadow_default if self.shadow is None else self.shadow

    def __post_init__(self) -> None:
        if self.theme not in COLLAGE_THEMES:
            raise ValueError(f"Ismeretlen kollázs-téma: {self.theme!r}")
        if self.border not in BORDER_THEMES:
            raise ValueError(f"Ismeretlen képkeret: {self.border!r}")
        if self.width < 16 or self.height < 16:
            raise ValueError(f"Érvénytelen lapméret: {self.width}×{self.height}")
        if not 0.0 <= self.spacing <= 1.0:
            raise ValueError(f"A rács vastagsága 0..1 közé esik: {self.spacing}")
        if len(self.background) != 3 or not all(0 <= c <= 255 for c in self.background):
            raise ValueError(f"Érvénytelen háttérszín: {self.background}")


_DEFAULT_SETTINGS = PicasaCollageSettings()


def _canvas(settings: PicasaCollageSettings) -> np.ndarray:
    canvas = np.empty((settings.height, settings.width, 3), dtype=np.uint8)
    canvas[:, :] = settings.background
    return canvas


def _aspects(images: list[np.ndarray]) -> list[float]:
    return [image.shape[1] / image.shape[0] for image in images]


def _place_in_cells(
    canvas: np.ndarray,
    images: list[np.ndarray],
    rects: tuple[NormRect, ...],
    settings: PicasaCollageSettings,
    *,
    fill: bool = True,
) -> None:
    """A képek a cellákba illesztve, kerettel, a vászonra rajzolva."""
    cells = to_pixel_rects(
        rects, settings.width, settings.height, settings.effective_spacing
    )
    for image, cell in zip(images, cells, strict=False):
        width = max(1, cell.x1 - cell.x0)
        height = max(1, cell.y1 - cell.y0)
        tile = apply_border(
            fit_to_frame(image, width, height, fill=fill), settings.effective_border
        )
        # a keret megnöveli a csempét — középre igazítva rajzoljuk a cellába
        offset_x = cell.x0 + (width - tile.shape[1]) // 2
        offset_y = cell.y0 + (height - tile.shape[0]) // 2
        _paste(canvas, tile, offset_x, offset_y)


def _draw_contact_header(canvas: np.ndarray, settings: PicasaCollageSettings) -> int:
    """Az Indexkép fejlécsávja; a felhasznált magasságot adja vissza.

    A `contact_sheet.header_font_size` a betűméretet a lap magasságából és a
    panel oldalarányából számolja; a sáv maga a lap tetején ül.
    """
    from .contact_sheet import header_font_size

    band = max(1, round(settings.height * _HEADER_RATIO))
    canvas[:band, :] = settings.background
    felirat = settings.caption.strip()
    if not felirat:
        return band
    meret = header_font_size(settings.height, settings.width / settings.height)
    skala = max(0.4, meret / 32.0)
    vastagsag = max(1, round(skala * 1.5))
    (_, szoveg_h), _ = cv2.getTextSize(felirat, cv2.FONT_HERSHEY_SIMPLEX, skala, vastagsag)
    szin = tuple(255 - c for c in settings.background)
    cv2.putText(
        canvas,
        felirat,
        (max(4, round(settings.width * 0.02)), (band + szoveg_h) // 2),
        cv2.FONT_HERSHEY_SIMPLEX,
        skala,
        szin,
        vastagsag,
        cv2.LINE_AA,
    )
    return band


def _render_pile(
    canvas: np.ndarray, images: list[np.ndarray], settings: PicasaCollageSettings
) -> None:
    from .render import Placement

    rng = MsvcRandom(settings.seed)
    places = pile_layout(len(images), settings.width, settings.height, rng)
    for image, place in zip(images, places, strict=False):
        oldal = max(1, place.size)
        magassag, szelesseg = image.shape[:2]
        cel_w, cel_h = fit_inside(szelesseg, magassag, oldal, oldal)
        tile = apply_border(
            fit_to_frame(image, max(1, cel_w), max(1, cel_h), fill=False),
            settings.effective_border
        )
        # a `pile_top_left` TENGELYENKÉNT dolgozik (skalárokkal), ezért
        # kétszer hívjuk — a szórási terület itt a teljes lap
        x = pile_top_left(place.center_x, tile.shape[1], settings.width, settings.width)
        y = pile_top_left(place.center_y, tile.shape[0], settings.height, settings.height)
        _rotated_paste(
            canvas,
            tile,
            Placement(
                x=round(x),
                y=round(y),
                width=tile.shape[1],
                height=tile.shape[0],
                angle=math.degrees(place.theta),
            ),
        )


def make_picasa_collage(
    sources, settings: PicasaCollageSettings = _DEFAULT_SETTINGS
) -> CollageReport:
    """Picasa-hű kollázs a hat téma egyikével.

    A hibás/hiányzó források kimaradnak, nem állítják meg a munkát — a hívó
    a `CollageReport.used` üres voltából látja, ha nincs mit menteni (ez a
    `render.make_collage` viselkedése, szándékosan azonos).
    """
    paths = [Path(s) for s in sources]
    if not paths:
        raise ValueError("Kollázshoz legalább egy kép kell.")

    decoded: list[np.ndarray] = []
    used: list[Path] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    for path in paths:
        if not path.exists():
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            decoded.append(_decode(path))
            used.append(path)
        except (ValueError, OSError) as error:
            skipped.append(path)
            reasons.append(str(error))

    canvas = _canvas(settings)
    if not decoded:
        return CollageReport(
            image=canvas,
            used=(),
            skipped=tuple(skipped),
            reasons=tuple(reasons),
            missing=tuple(missing),
        )

    if settings.theme == MULTIEXP:
        canvas = blend_multi_exposure(
            decoded, settings.width, settings.height, settings.background
        )
    elif settings.theme == PICTUREPILE:
        _render_pile(canvas, decoded, settings)
    elif settings.theme in (PICTUREGRID, FRAMEGRID):
        rogzitett = (
            settings.frame_center
            if settings.theme == FRAMEGRID
            and settings.frame_center is not None
            and 0 <= settings.frame_center < len(decoded)
            else None
        )
        if rogzitett is None:
            # nincs rögzített kép → az EREDETI IS az alap pakolóra esik vissza
            rects = pack(
                _aspects(decoded), settings.width / settings.height, MsvcRandom(settings.seed)
            )
            _place_in_cells(canvas, decoded, rects, settings)
        else:
            tobbi = [kep for index, kep in enumerate(decoded) if index != rogzitett]
            if tobbi:
                rects = pack(
                    _aspects(tobbi), settings.width / settings.height, MsvcRandom(settings.seed)
                )
                _place_in_cells(canvas, tobbi, rects, settings)
            # a hangsúlyos kép LEGFELÜL, a középső területre
            _place_in_cells(canvas, [decoded[rogzitett]], (_FRAMEGRID_CENTER,), settings)
    elif settings.theme == REGULARGRID:
        sorok, oszlopok = regular_grid_shape(
            _aspects(decoded), settings.width, settings.height
        )
        rects = regular_grid_rects(len(decoded), sorok, oszlopok)
        _place_in_cells(canvas, decoded, rects, settings)
    elif settings.theme == CONTACTSHEET:
        sav = _draw_contact_header(canvas, settings)
        also = settings.height - sav
        alvaszon = np.empty((max(1, also), settings.width, 3), dtype=np.uint8)
        alvaszon[:, :] = settings.background
        alsobeallitas = PicasaCollageSettings(
            theme=REGULARGRID,
            border=settings.border,
            width=settings.width,
            height=max(16, also),
            background=settings.background,
            spacing=settings.spacing,
            seed=settings.seed,
        )
        sorok, oszlopok = regular_grid_shape(
            _aspects(decoded), settings.width, max(1, also)
        )
        rects = regular_grid_rects(len(decoded), sorok, oszlopok)
        # az Indexképnél a TELJES kép látszik (nem vágunk), ez a lényege
        _place_in_cells(alvaszon, decoded, rects, alsobeallitas, fill=False)
        canvas[sav : sav + alvaszon.shape[0], :] = alvaszon
    else:  # pragma: no cover — a __post_init__ már kizárta
        raise ValueError(f"Ismeretlen kollázs-téma: {settings.theme!r}")

    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
    )


__all__ = ["PicasaCollageSettings", "make_picasa_collage"]
