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

import logging
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PIL import Image, ImageDraw

from .fitting import MsvcRandom, picasa_round
from .frames import POLAROID_HEIGHT_RATIO, POLAROID_WIDTH_RATIO
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
from .location_tree import pack_with_center
from .packing import pack
from .regular_grid import regular_grid_rects, regular_grid_shape
from .render import CollageReport, _decode, fit_to_frame
from .shadow import (
    ShadowParams,
    shadow_params,
)
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
from .picasa_render_layouts import (
    _ContactSheetGeometry,  # noqa: F401 - régi modulimportútvonal
    _cell_nodes,
    _contact_sheet_band,
    _contact_sheet_geometry,  # noqa: F401 - régi modulimportútvonal
    _contact_sheet_nodes,
    _contact_sheet_position,  # noqa: F401 - régi modulimportútvonal
    _framed_size_inside,  # noqa: F401 - régi modulimportútvonal
    _multi_exposure_nodes,
    _pile_nodes,
    _polaroid_negyzet,  # noqa: F401 - régi modulimportútvonal
    _unicode_font,
    contact_sheet_cell_scale,
)

#: A polaroid csempe RÖGZÍTETT oldalaránya (#1053). Nem új szám: a keret két
#: aránya adja (`1,145 / 1,374 = 0,83333`), és a golden csempéken mérve
#: `0,83313` / `0,83328` — négy tizedesig egyezik. Azért él nevesítve, mert a
#: Képkupacban ez a csempe ALAKJA, nem csak a keret növekménye.
POLAROID_CSEMPE_ARANY = POLAROID_WIDTH_RATIO / POLAROID_HEIGHT_RATIO

logger = logging.getLogger(__name__)

#: A háttérkép TOMPÍTÁSA (`DimmedBitmapTheme`, spec 6.4) — a felület
#: `#26000000` fekete rétege, azaz **38/255** alfa.
BACKGROUND_DIM_ALPHA = 0x26

#: A szorzó, amivel a háttérkép képpontjai halványodnak: `(255 − 38) / 255`.
#:
#: ⚠️ A számot MÉRÉS adja, nem a felületi réteg átvétele. A tulajdonos
#: `AI2.jpg`-jének háttérképe csempeként is szerepel az `AI1.jpg`-ben,
#: tompítás NÉLKÜL — a két előfordulás közvetlenül összevethető:
#:
#: | | 90% | 99% | 99,9% |
#: |---|---:|---:|---:|
#: | csempeként | 255 | 255 | 255 |
#: | háttérként | 77 | **217** | 218 |
#:
#: A telített fehér 217-nél **falba ütközik** (117 646 képpont egyetlen
#: tüskében), és `(255 − 217) / 255 = 0,1490 = 38/255` — bájtra a felületi
#: `#26000000`. A kimenetnek tehát ugyanazt kell tennie, amit az élő
#: előnézet már ma is tesz.
BACKGROUND_DIM_FACTOR = (255 - BACKGROUND_DIM_ALPHA) / 255

_DEFAULT_WIDTH = 1600
_DEFAULT_HEIGHT = 1200


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
    #: Az Indexkép két fejlécsorának forrása (#1273). A mezők a `.cxf`
    #: `albumTitle` / `albumDate` értékei; a darabszámot a rajzoló ismeri.
    album_title: str = ""
    album_date: str = ""
    #: A „Beállítás képkockaközéppontként" gomb eredménye: melyik kép kapja
    #: a hangsúlyos középső helyet a Képkockamozaikban. `None` esetén NINCS
    #: rögzített kép — és ilyenkor az eredeti is az alap (Mozaik-)pakolóra
    #: esik vissza (spec 1.9.14: „a `CLocationTree` nem helyettesíti, hanem
    #: kiegészíti az alap algoritmust").
    frame_center: int | None = None
    #: #978: a felület „képfeliratok" kapcsolója (`collage/showcaptions`).
    #: Az eredetiben a Polaroid-felirat KÉT feltételhez kötött — a kapcsoló
    #: BE **és** a keret `polaroid` (`0x00839830`). Nálunk a rajzolási úton
    #: eddig csak a keret szerepelt, tehát a kapcsoló NÉMA volt: kikapcsolva
    #: is ott maradt a felirat a mentett képen.
    captions: bool = True
    #: Rajzoljunk-e árnyékot. `None` = a téma alapértelmezése (a maszk
    #: 14. bitje) — ez az eredeti viselkedése, ld. `effective_shadow`.
    shadow: bool | None = None
    #: A HÁTTÉRKÉP útvonala (#1015). Üresen a `background` szín marad. A
    #: kép a lapot KITÖLTI (arányt tartva, középről vágva) — a golden
    #: háttere a teljes lapot fedi, élesen, effekt nélkül.
    background_image: str = ""

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
    """A lap alapja: a beállított szín, vagy a HÁTTÉRKÉP (#1015).

    ⚠️ A háttérkép baja SOHA nem viheti el a kollázst. Hiányzó, olvashatatlan
    vagy sérült fájlnál a szín marad — a felhasználó képei fontosabbak, mint
    a háttér, és egy elszálló mentés sokkal rosszabb egy egyszínű háttérnél.

    A kép a lapot KITÖLTI (`fill=True`): arányt tartva nagyít, a túllógó részt
    középről vágja. A kitöltés-vagy-nyújtás kérdés nincs lemérve — a döntés
    indoklása a `tests/collage/test_kephatter_1015.py` modul-docstringjében.

    A háttér **TOMPÍTVA** kerül a lapra (`BACKGROUND_DIM_FACTOR`) — ez nem
    stílus, hanem mérés: a golden háttere a forráskép 85,1%-án áll."""
    canvas = np.empty((settings.height, settings.width, 3), dtype=np.uint8)
    canvas[:, :] = settings.background
    if not settings.background_image:
        return canvas
    try:
        hatter = _decode(Path(settings.background_image))
    except (ValueError, OSError) as hiba:
        logger.info(
            "A kollázs háttérképe nem olvasható (%s): %s",
            settings.background_image,
            hiba,
        )
        return canvas
    illesztett = fit_to_frame(hatter, settings.width, settings.height, fill=True)
    canvas[:, :] = np.rint(
        illesztett.astype(np.float32) * BACKGROUND_DIM_FACTOR
    ).astype(np.uint8)
    return canvas


def shadow_for_settings(
    settings: PicasaCollageSettings, count: int
) -> ShadowParams | None:
    """A téma árnyék-paraméterei, vagy `None`, ha nem kell árnyék (#977).

    Két kapu van, és MINDKETTŐ a képesség-maszkból jön: az
    `effective_shadow` (11. bit engedélyez, 14. bit az alapérték), és a
    `shadow.shadow_params` maga is a 11. bitet nézi. Így a Többszörös
    exponálás tiltása egyetlen forrásból származik — témanév-hasonlítás
    sehol nem születik.

    ⚠️ **Nyilvános** (#1021): az élő vászon UGYANEZT hívja, ugyanazzal a
    `render_settings()`-szel, amivel a mentés dolgozik. Enélkül a vászon
    egy párhuzamos számítást tartana, ami előbb-utóbb elválna — és a
    felhasználó azt látná, hogy a mentett kép mást mutat, mint az
    előnézet."""
    if not settings.effective_shadow:
        return None
    return shadow_params(
        settings.theme,
        page_width=settings.width,
        page_height=settings.height,
        count=max(1, count),
    )


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

    if settings.theme == CONTACTSHEET:
        # #1273: ez az ÉLŐ vászon és az újraszerkesztés bejárata. Korábban
        # csak a gépi `make_picasa_collage` rajzolta a fejlécet, ezért az a
        # szerkesztés első frissítésekor eltűnt.
        # A fejléc ugyanazt számolja, mint a mentett út: csak a ténylegesen
        # dekódolt képeket. A hiányzó helykitöltő nem lehet „kép” a számban.
        _draw_contact_header(canvas, settings, len(used))
    draw_nodes(
        canvas,
        nodes,
        images,
        settings.width,
        shadow_for_settings(settings, len(nodes)),
        captions=settings.captions,
    )
    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
        # #960: amit kirajzoltunk, azt jelentjük is — ebből lesz a piszkozat
        nodes=tuple(nodes),
    )


# --- Az elrendezések → csomópontok -------------------------------------------

def _draw_contact_header(
    canvas: np.ndarray, settings: PicasaCollageSettings, count: int = 0
) -> int:
    """Az Indexkép fejlécsávja; a felhasznált magasságot adja vissza.

    A `contact_sheet.header_font_size` a betűméretet a lap magasságából és a
    panel oldalarányából számolja; a sáv maga a lap tetején ül.
    """
    from .contact_sheet import (
        CONTACT_SHEET_LEFT_RATIO,
        CONTACT_SHEET_SUBTITLE_OFFSET_RATIO,
        CONTACT_SHEET_SUBTITLE_SIZE_RATIO,
        CONTACT_SHEET_TITLE_TOP_RATIO,
        NARROW_PANEL_FACTOR,
        header_font_size,
        header_lines,
    )

    band = _contact_sheet_band(settings)
    canvas[:band, :] = settings.background
    title, subtitle = header_lines(
        settings.album_title or settings.caption, settings.album_date, count
    )
    panel_aspect = settings.width / settings.height
    meret = header_font_size(settings.height, panel_aspect)
    factor = 1.0 if panel_aspect > 1.0 else NARROW_PANEL_FACTOR
    subtitle_size = max(
        1, picasa_round(factor * CONTACT_SHEET_SUBTITLE_SIZE_RATIO * settings.height)
    )
    # 0x00887aff–0x00887b23: világos háttéren #4A4A4A, sötéten fehér.
    blue, green, red = settings.background
    packed_rgb = (red << 16) | (green << 8) | blue
    color = (255, 255, 255) if packed_rgb < 0x7F7F7F else (74, 74, 74)
    x = picasa_round(settings.width * CONTACT_SHEET_LEFT_RATIO)
    title_top = picasa_round(settings.height * CONTACT_SHEET_TITLE_TOP_RATIO)
    subtitle_top = picasa_round(
        settings.height
        * (CONTACT_SHEET_TITLE_TOP_RATIO + factor * CONTACT_SHEET_SUBTITLE_OFFSET_RATIO)
    )
    # Az OpenCV Hershey-fontja nem Unicode: a „kép" szót „k??p" alakban
    # rajzolná. A Pillow/FreeType ugyanazt háttérszálon, GUI-objektum nélkül
    # és valódi magyar karakterekkel rajzolja.
    header_rgb = cv2.cvtColor(canvas[:band], cv2.COLOR_BGR2RGB)
    image = Image.fromarray(header_rgb)
    draw = ImageDraw.Draw(image)
    if title:
        draw.text((x, title_top), title, font=_unicode_font(meret), fill=color)
    draw.text(
        (x, subtitle_top), subtitle, font=_unicode_font(subtitle_size), fill=color
    )
    canvas[:band] = cv2.cvtColor(np.asarray(image), cv2.COLOR_RGB2BGR)
    return band


def layout_nodes_for_aspects(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> list[CollageNode]:
    """MIND A HAT téma pakolója, a képek OLDALARÁNYÁBÓL (#989).

    Ez a kollázs elrendezésének **egyetlen** forrása: innen tölti fel a
    vásznát a kollázs-panel, és ezt futtatja a `make_picasa_collage` is a
    rajzolás előtt. Aki két pakoló-utat épít, előbb-utóbb azt kapja, hogy a
    mentett kép mást mutat, mint a vászon (spec 6.5).

    Miért oldalarány és nem kép: a panel a képeket **nem dekódolja** (350
    képnél nem is tehetné) — az indexből csak az arányt ismeri. A rajzolónak
    van dekódolt képe, abból a `layout_nodes` számol arányt. A geometria
    egyik esetben sem függ a forrás abszolút képpontméretétől
    (`fitting.fit_aspect_inside`).

    | téma | a geometriát adó mag |
    |---|---|
    | `picturepile` | `pile.pile_layout` |
    | `picturegrid` | `packing.pack` |
    | `framegrid` | `packing.pack` + a hangsúlyos kép a középső területre |
    | `regulargrid` | `regular_grid` |
    | `contactsheet` | `regular_grid` a fejlécsáv ALATT |
    | `multiexp` | a közös illesztő: mindenki a teljes lapra, középre |

    A keret és a térköz a téma KÉPESSÉG-MASZKJÁN át hat (`effective_border`,
    `effective_spacing`) — témánkénti `if` sem itt, sem a felületen nem
    születik.
    """
    if len(aspects) != len(paths):
        raise ValueError("Minden képhez tartoznia kell útvonalnak.")
    if not aspects:
        return []
    if settings.theme == PICTUREPILE:
        return _pile_nodes(aspects, paths, settings)
    if settings.theme == MULTIEXP:
        return _multi_exposure_nodes(aspects, paths, settings)
    if settings.theme == CONTACTSHEET:
        nodes, _, _ = _contact_sheet_nodes(aspects, paths, settings)
        return nodes
    if settings.theme in (PICTUREGRID, FRAMEGRID):
        rogzitett = (
            settings.frame_center
            if settings.theme == FRAMEGRID
            and settings.frame_center is not None
            and 0 <= settings.frame_center < len(aspects)
            else None
        )
        if rogzitett is None:
            # nincs rögzített kép → az EREDETI IS az alap pakolóra esik vissza
            rects = pack(
                list(aspects),
                settings.width / settings.height,
                MsvcRandom(settings.seed),
            )
            return _cell_nodes(paths, rects, settings)
        #: #916: a hangsúlyos kép a MÉRT cellát kapja (`0x00889185`), a
        #: többi a maradék sávokra — a `CLocationTree` pakolója.
        rects = pack_with_center(
            list(aspects),
            settings.width / settings.height,
            MsvcRandom(settings.seed),
            center=rogzitett,
        )
        #: a hangsúlyos kép LEGFELÜL: a lista VÉGÉN áll, hogy a rajzoló ne
        #: takarja el a köré pakolt csempékkel
        sorrend = [i for i in range(len(aspects)) if i != rogzitett] + [rogzitett]
        nodes = _cell_nodes(
            [paths[i] for i in sorrend],
            tuple(rects[i] for i in sorrend),
            settings,
        )
        return nodes
    if settings.theme == REGULARGRID:
        sorok, oszlopok = regular_grid_shape(
            list(aspects), settings.width, settings.height
        )
        rects = regular_grid_rects(len(aspects), sorok, oszlopok)
        return _cell_nodes(paths, rects, settings)
    raise ValueError(
        f"Ehhez a témához nincs csomópont-elrendezés: {settings.theme!r}"
    )


def layout_nodes(
    images: Sequence[np.ndarray],
    paths: Sequence[Path],
    settings: PicasaCollageSettings = _DEFAULT_SETTINGS,
) -> list[CollageNode]:
    """A téma pakolója DEKÓDOLT képekből — a `make_picasa_collage` első fele.

    Csak annyit tesz, hogy a képekből oldalarányt számol, és átadja a
    `layout_nodes_for_aspects`-nek; a geometria egyetlen helyen él.
    """
    if len(images) != len(paths):
        raise ValueError("Minden képhez tartoznia kell útvonalnak.")
    return layout_nodes_for_aspects(_aspects(list(images)), paths, settings)


def _multiexp_node(path: Path, settings: PicasaCollageSettings) -> CollageNode:
    """A Többszörös exponálás egyetlen csomópont-alakja (#1248).

    Mérve az `AI7.cxf`-en: `x=0 y=0 w=1 h=1 theta=0`, `noborder` — vagyis
    minden kép a TELJES lapot fedi. Lapegységben ez a lap közepén álló,
    lap méretű doboz."""
    lap_magassag = SHEET_UNITS * settings.height / settings.width
    return CollageNode(
        path=str(path),
        center_x=SHEET_UNITS / 2.0,
        center_y=lap_magassag / 2.0,
        width=SHEET_UNITS,
        height=lap_magassag,
        theta=0.0,
        border=NOBORDER,
        fill=False,
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

    # #960: a kirajzolt csomópontok — a `.cxf` piszkozat egyetlen hiteles
    # forrása. A Többszörös exponálás sem kivétel (#1248): geometriát nem
    # ad, a FORRÁSKÉPEK listáját viszont neki is ki kell adnia.
    rajzolt: tuple[CollageNode, ...] = ()
    if settings.theme == MULTIEXP:
        # A Többszörös exponálás nem HELYEZ el képeket, hanem egymásra keveri
        # őket — ezért nem a közös rajzolón megy át. A képesség-maszkja is
        # ezt mondja: se kijelölés, se keret, se háttér.
        canvas = blend_multi_exposure(
            decoded, settings.width, settings.height, settings.background
        )
        # ⚠️ #1248: a csomópontok ettől függetlenül KELLENEK. A geometria
        # tényleg nem hordoz információt, a `.cxf`-nek viszont tudnia kell,
        # MELYIK képekből készült a kollázs — enélkül az újraszerkesztés
        # fekete lapot ad, és a mentés azt jelenti, hogy „az összes képet
        # eltávolították" (a tulajdonos jelentése, v0.8.45).
        #
        # Az alak MÉRVE (`referencia/kollazs-golden/AI7.cxf`, valódi
        # Picasa-minta): képenként EGY csomópont, mind a TELJES lapon,
        # forgatás és keret nélkül.
        rajzolt = tuple(_multiexp_node(ut, settings) for ut in used)
    elif settings.theme == CONTACTSHEET:
        # Ugyanez a teljes-lapos csomópontlista megy az élő vászonra és a
        # mentésbe; ettől a szerkesztés közbeni frissítés nem válhat el.
        _draw_contact_header(canvas, settings, len(decoded))
        nodes, _, alsobeallitas = _contact_sheet_nodes(
            _aspects(decoded), used, settings
        )
        draw_nodes(
            canvas,
            nodes,
            decoded,
            alsobeallitas.width,
            shadow_for_settings(settings, len(decoded)),
            captions=settings.captions,
        )
        rajzolt = tuple(nodes)
    else:
        nodes = layout_nodes(decoded, used, settings)
        draw_nodes(
            canvas,
            nodes,
            decoded,
            settings.width,
            shadow_for_settings(settings, len(decoded)),
            captions=settings.captions,
        )
        rajzolt = tuple(nodes)

    return CollageReport(
        image=canvas,
        used=tuple(used),
        skipped=tuple(skipped),
        reasons=tuple(reasons),
        missing=tuple(missing),
        nodes=rajzolt,
    )


__all__ = [
    "SHEET_UNITS",
    "CollageNode",
    "PicasaCollageSettings",
    "border_growth",
    "contact_sheet_cell_scale",
    "layout_nodes",
    "layout_nodes_for_aspects",
    "make_picasa_collage",
    "outer_box",
    "photo_box",
    "pixels_to_sheet",
    "render_nodes",
    "shadow_for_settings",
    "sheet_to_pixels",
]
