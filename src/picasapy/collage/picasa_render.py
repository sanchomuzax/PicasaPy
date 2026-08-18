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

## Elrendezés ÉS rajzolás — két lépés, egy rajzoló (#942)

A modul **kettéválik**: a téma pakolója `CollageNode` csomópontokat állít
elő (hol, mekkorán, milyen szögben áll egy kép), a rajzoló pedig CSAK
kirajzolja őket. Enélkül a kollázs-panel élő vászna hazudna: a
`make_picasa_collage` mindig újraszámolta az elrendezést, tehát egy kézzel
átrendezett vászon mentéskor visszaugrott volna a gépi elrendezésre.

```
make_picasa_collage ─→ layout_nodes ─→ csomópontok ─┐
render_nodes ─→ (a felülettől kapott csomópontok) ──┴─→ nodes.draw_nodes
```

A `render_nodes` a felület bejárata: MEGADOTT elhelyezésekből rajzol,
elrendezés-számolás nélkül. A csomópont-modell és a közös rajzoló a
`nodes.py`-ban él.

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

from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

import cv2
import numpy as np

from .fitting import MsvcRandom, fit_inside
from .multi_exposure import blend_multi_exposure
from .nodes import (
    SHEET_UNITS,
    CollageNode,
    border_growth,
    draw_nodes,
    outer_box,
    photo_box,
    pixels_to_sheet,
    sheet_to_pixels,
)
from .packing import pack
from .pile import pile_layout
from .rects import NormRect, to_pixel_rects
from .regular_grid import regular_grid_rects, regular_grid_shape
from .render import CollageReport, _decode
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


def render_nodes(
    nodes: Sequence[CollageNode],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> CollageReport:
    """A MEGADOTT csomópont-elhelyezésekből rajzol — nem számol elrendezést.

    Ez a kollázs-panel élő vásznának mentő-bejárata (spec 6.5): a
    felhasználó által kézzel átrendezett vászon PONTOSAN úgy kerül a
    kimenetre, ahogy a képernyőn áll. A `make_picasa_collage` ugyanezt a
    rajzolót használja, csak előbb lefuttatja a téma pakolóját — egy
    rajzoló, két hívó.

    A hibás vagy hiányzó képek nem állítják meg a munkát: helykitöltő
    csempeként jelennek meg, és a `CollageReport.missing` / `skipped`
    sorolja fel őket."""
    canvas = _canvas(settings)
    images: list[np.ndarray | None] = []
    used: list[Path] = []
    skipped: list[Path] = []
    reasons: list[str] = []
    missing: list[Path] = []
    for node in nodes:
        path = Path(node.path) if node.path is not None else None
        if path is None:
            images.append(None)
            continue
        if node.missing or not path.exists():
            images.append(None)
            missing.append(path)
            skipped.append(path)
            reasons.append("a fájl nem található")
            continue
        try:
            images.append(_decode(path))
            used.append(path)
        except (ValueError, OSError) as error:
            images.append(None)
            skipped.append(path)
            reasons.append(str(error))

    draw_nodes(canvas, nodes, images, settings.width)
    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
    )


# --- Az elrendezések → csomópontok -------------------------------------------


def _cell_nodes(
    paths: Sequence[Path],
    rects: tuple[NormRect, ...],
    settings: PicasaCollageSettings,
    *,
    fill: bool = True,
) -> list[CollageNode]:
    """A rácsos témák cellái csomópontokká.

    A **cella a fotó doboza**, a keret ezen KÍVÜL nő — ezért a csomópont
    külső doboza `outer_box(cella)`, amiből a rajzoló `photo_box`-szal
    pontosan a cellát kapja vissza. A csomópont középpontja a cella
    középpontja: a rajzoló a csempét erre igazítja, ami szó szerint a régi
    „a csempe a cellába középre" szabály."""
    keret = settings.effective_border
    cells = to_pixel_rects(
        rects, settings.width, settings.height, settings.effective_spacing
    )
    nodes: list[CollageNode] = []
    for path, cell in zip(paths, cells, strict=False):
        cella_w = max(1, cell.x1 - cell.x0)
        cella_h = max(1, cell.y1 - cell.y0)
        kulso_w, kulso_h = outer_box(cella_w, cella_h, keret)
        # a régi rajzoló a CELLA közepére igazította a csempét; a csempe
        # középpontja ezért a cella közepétől a keret aszimmetriájával tér el
        kozep_x = cell.x0 + cella_w / 2.0
        kozep_y = cell.y0 + cella_h / 2.0
        nodes.append(
            CollageNode(
                path=path,
                center_x=pixels_to_sheet(kozep_x, settings.width),
                center_y=pixels_to_sheet(kozep_y, settings.width),
                width=pixels_to_sheet(kulso_w, settings.width),
                height=pixels_to_sheet(kulso_h, settings.width),
                border=keret,
                fill=fill,
            )
        )
    return nodes


def _pile_nodes(
    images: Sequence[np.ndarray],
    paths: Sequence[Path],
    settings: PicasaCollageSettings,
) -> list[CollageNode]:
    """A Képkupac szórása csomópontokká.

    A kupac a képet egy NÉGYZETBE illeszti arányosan (`fit_inside`), és a
    kapott doboz köré nő a keret. A csomópont középpontja a szórás
    középpontja — a `pile_top_left` ugyanezt a „középre" szabályt írja le,
    csak a bal felső sarok felől."""
    keret = settings.effective_border
    rng = MsvcRandom(settings.seed)
    # a `pile.pile_top_left` ugyanezt a szabályt írja le a bal felső sarok
    # felől (`x − szélesség · 0,5`); a csomópont a KÖZÉPPONTOT tárolja, a
    # sarokra váltás a rajzoló `_origin` dolga
    places = pile_layout(len(images), settings.width, settings.height, rng)
    nodes: list[CollageNode] = []
    for image, path, place in zip(images, paths, places, strict=False):
        oldal = max(1, place.size)
        magassag, szelesseg = image.shape[:2]
        cel_w, cel_h = fit_inside(szelesseg, magassag, oldal, oldal)
        kulso_w, kulso_h = outer_box(max(1, cel_w), max(1, cel_h), keret)
        nodes.append(
            CollageNode(
                path=path,
                center_x=pixels_to_sheet(place.center_x, settings.width),
                center_y=pixels_to_sheet(place.center_y, settings.width),
                width=pixels_to_sheet(kulso_w, settings.width),
                height=pixels_to_sheet(kulso_h, settings.width),
                theta=place.theta,
                border=keret,
                fill=False,
            )
        )
    return nodes


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


def layout_nodes(
    images: Sequence[np.ndarray],
    paths: Sequence[Path],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> list[CollageNode]:
    """A téma pakolója: a képekből csomópontok — rajzolás NÉLKÜL.

    Ez a `make_picasa_collage` első fele, önmagában is használható: a
    kollázs-panel ezzel tölti fel a vásznat induláskor és a „Képek
    szétszórása" parancsnál. A felhasználó kézi mozgatásai után ugyanezeket
    a — közben módosított — csomópontokat rajzolja ki a `render_nodes`.
    Enélkül a mentés újraszámolna, és a felhasználó mást kapna, mint amit a
    képernyőn lát (spec 6.5).

    Két téma NEM ide tartozik: a Többszörös exponálás nem helyez el képeket
    (egymásra keveri őket), az Indexkép pedig a fejlécsáv alatti önálló
    lapra rendez — mindkettőt a `make_picasa_collage` kezeli.
    """
    if len(images) != len(paths):
        raise ValueError("Minden képhez tartoznia kell útvonalnak.")
    if settings.theme == PICTUREPILE:
        return _pile_nodes(images, paths, settings)
    if settings.theme in (PICTUREGRID, FRAMEGRID):
        rogzitett = (
            settings.frame_center
            if settings.theme == FRAMEGRID
            and settings.frame_center is not None
            and 0 <= settings.frame_center < len(images)
            else None
        )
        if rogzitett is None:
            # nincs rögzített kép → az EREDETI IS az alap pakolóra esik vissza
            rects = pack(
                _aspects(list(images)),
                settings.width / settings.height,
                MsvcRandom(settings.seed),
            )
            return _cell_nodes(paths, rects, settings)
        tobbi = [kep for index, kep in enumerate(images) if index != rogzitett]
        tobbi_ut = [ut for index, ut in enumerate(paths) if index != rogzitett]
        nodes: list[CollageNode] = []
        if tobbi:
            rects = pack(
                _aspects(tobbi),
                settings.width / settings.height,
                MsvcRandom(settings.seed),
            )
            nodes.extend(_cell_nodes(tobbi_ut, rects, settings))
        # a hangsúlyos kép LEGFELÜL — a lista végén, a középső területre
        nodes.extend(
            _cell_nodes([paths[rogzitett]], (_FRAMEGRID_CENTER,), settings)
        )
        return nodes
    if settings.theme == REGULARGRID:
        sorok, oszlopok = regular_grid_shape(
            _aspects(list(images)), settings.width, settings.height
        )
        rects = regular_grid_rects(len(images), sorok, oszlopok)
        return _cell_nodes(paths, rects, settings)
    raise ValueError(
        f"Ehhez a témához nincs csomópont-elrendezés: {settings.theme!r}"
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
        # A Többszörös exponálás nem HELYEZ el képeket, hanem egymásra keveri
        # őket — nincsenek csomópontjai, ezért nem a közös rajzolón megy át.
        # A képesség-maszkja is ezt mondja: se kijelölés, se keret, se háttér.
        canvas = blend_multi_exposure(
            decoded, settings.width, settings.height, settings.background
        )
    elif settings.theme == CONTACTSHEET:
        # Az Indexkép a fejlécsáv ALATT kap egy önálló lapot. A külön
        # vászonra rajzolás nem kényelmi kérdés, hanem VÁGÁS: a cellából
        # kilógó keret nem írhat bele a fejlécbe.
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
        nodes = _cell_nodes(used, rects, alsobeallitas, fill=False)
        draw_nodes(alvaszon, nodes, decoded, alsobeallitas.width)
        canvas[sav : sav + alvaszon.shape[0], :] = alvaszon
    else:
        nodes = layout_nodes(decoded, used, settings)
        draw_nodes(canvas, nodes, decoded, settings.width)

    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
    )


__all__ = [
    "SHEET_UNITS",
    "CollageNode",
    "PicasaCollageSettings",
    "border_growth",
    "layout_nodes",
    "make_picasa_collage",
    "outer_box",
    "photo_box",
    "pixels_to_sheet",
    "render_nodes",
    "sheet_to_pixels",
]
