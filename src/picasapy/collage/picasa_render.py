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
from dataclasses import dataclass, replace
from pathlib import Path

import cv2
import numpy as np

from .fitting import MsvcRandom, fit_aspect_inside
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
from .packing import pack
from .pile import pile_layout
from .rects import NormRect, to_pixel_rects
from .regular_grid import regular_grid_rects, regular_grid_shape
from .render import CollageReport, _decode, fit_to_frame
from .shadow import ShadowParams, shadow_params
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
    POLAROID,
    REGULARGRID,
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

    draw_nodes(
        canvas, nodes, images, settings.width, shadow_for_settings(settings, len(nodes))
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


def _cell_nodes(
    paths: Sequence[Path],
    rects: tuple[NormRect, ...],
    settings: PicasaCollageSettings,
    *,
    fill: bool = True,
    border: str | None = None,
    spacing: float | None = None,
) -> list[CollageNode]:
    """A rácsos témák cellái csomópontokká.

    A **cella a fotó doboza**, a keret ezen KÍVÜL nő — ezért a csomópont
    külső doboza `outer_box(cella)`, amiből a rajzoló `photo_box`-szal
    pontosan a cellát kapja vissza. A csomópont középpontja a cella
    középpontja: a rajzoló a csempét erre igazítja, ami szó szerint a régi
    „a csempe a cellába középre" szabály.

    A `border` / `spacing` felülbírálás az Indexképé: ott a cellák egy
    ÖNÁLLÓ, fejléc alatti lapra készülnek `REGULARGRID` beállítással, de a
    keret és a térköz a HÍVÓ témájáé marad."""
    keret = settings.effective_border if border is None else border
    terkoz = settings.effective_spacing if spacing is None else spacing
    cells = to_pixel_rects(rects, settings.width, settings.height, terkoz)
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


def _polaroid_negyzet(oldal: int) -> tuple[int, int, int]:
    """A `scale` négyzetbe illeszkedő polaroid csempe: (fotó oldala, szél., mag.).

    #1053: az eredetiben a polaroid csempe KÜLSŐ doboza illeszkedik a `scale`
    négyzetbe, fix 0,8333 aránnyal, és a fotó ebből visszaszámolva NÉGYZET.

    ⚠️ Miért nem elég a `fit_aspect_inside` eredményét csomópont-méretnek
    venni: a keret egész képpontokkal nő (`picasa_round`), ezért nem minden
    külső doboz ÁLL ELŐ egy fotóméretből. A 134-es magasság például nem: a
    98-as fotóhoz a rajzoló 135-öt rajzol. Ha a csomópont 134-et állítana,
    a KIRAJZOLT csempe egy képponttal eltérne a bejelentettől — és a
    beszorítás, az élő vászon meg a mentett kép ezen a képponton szétcsúszna.

    Ezért a fotó oldalából indulunk vissza, és addig csökkentjük, amíg a
    keretes doboz tényleg befér a négyzetbe. A ciklus legfeljebb néhány
    lépés: a becslés már majdnem jó."""
    becsles = max(1, int(oldal / POLAROID_HEIGHT_RATIO))
    for foto in range(becsles + 2, 0, -1):
        szeles, magas = outer_box(foto, foto, POLAROID)
        if szeles <= oldal and magas <= oldal:
            return foto, szeles, magas
    szeles, magas = outer_box(1, 1, POLAROID)
    return 1, szeles, magas


def _pile_nodes(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings,
) -> list[CollageNode]:
    """A Képkupac szórása csomópontokká.

    A kupac a képet egy NÉGYZETBE illeszti arányosan (`fit_aspect_inside`),
    és a kapott doboz köré nő a keret. A csomópont középpontja a szórás
    középpontja — a `pile_top_left` ugyanezt a „középre" szabályt írja le,
    csak a bal felső sarok felől."""
    keret = settings.effective_border
    rng = MsvcRandom(settings.seed)
    # a `pile.pile_top_left` ugyanezt a szabályt írja le a bal felső sarok
    # felől (`x − szélesség · 0,5`); a csomópont a KÖZÉPPONTOT tárolja, a
    # sarokra váltás a rajzoló `_origin` dolga
    places = pile_layout(len(aspects), settings.width, settings.height, rng)
    nodes: list[CollageNode] = []
    for aspect, path, place in zip(aspects, paths, places, strict=False):
        oldal = max(1, place.size)
        # ⚠️ #1053: a POLAROID fotója NÉGYZET — az eredeti a `scale × scale`
        # négyzetre VÁGJA a képet, és a keret 1,145 / 1,374 arányai erre a
        # négyzetre mennek. Ezért ad ott MINDEN polaroid csempe 0,8333-at, a
        # forráskép arányától függetlenül (18 golden csomópont, két
        # lapformátum, több forráskép).
        #
        # Nálunk az arányok jók voltak, csak a fotó SAJÁT méretére mentek —
        # így a csempe alakja képfüggő lett (0,47-től 1,48-ig). Más alakú
        # csempe más helyre esik: ettől lógott ki a kupacunk már 9 képnél is,
        # miközben az eredeti ugyanott egyet sem.
        #
        # A vágás KÖRBEVÁGÁS (`kitolt=True`), nem illesztés: a golden csempe
        # fotóján belül nincs papír, ami 0,56 arányú forrásnál illesztéskor
        # látszana.
        #
        # A többi keret VÁLTOZATLAN: a golden `AI1.cxf` ugyanezekre a képekre
        # keret nélkül a kép arányát hozza (0,560 és 0,800 egy kollázsban).
        # A `scale` MINDIG a KÜLSŐ csempe befoglaló négyzete — a golden
        # `AI.cxf` polaroid csempéje és az `AI1.cxf` keret nélküli csempéje
        # ugyanazt a `h = 0,3291 = 337 / lapszélesség` magasságot adja, tehát
        # a keret NEM nő ki a négyzetből. A polaroidnál ezért a KÜLSŐ dobozt
        # illesztjük a négyzetbe (fix 0,8333 aránnyal), és abból számoljuk
        # vissza a fotót — nem fordítva.
        kitolt = keret == POLAROID
        if kitolt:
            foto_oldal, kulso_w, kulso_h = _polaroid_negyzet(oldal)
            cel_w = cel_h = foto_oldal
        else:
            cel_w, cel_h = fit_aspect_inside(aspect, oldal, oldal)
            kulso_w, kulso_h = outer_box(max(1, cel_w), max(1, cel_h), keret)
        # ⚠️ #1045 VISSZAVONVA (#1094). Volt itt egy beszorítás, amely a
        # csempét a lapon TARTOTTA. Az eredeti ezt NEM teszi: a tulajdonos
        # három A4-es FEKVŐ kollázsán (AI8, AI9, AI10) a valódi Picasa
        # kimenetében 89 csomópontból 3 kilóg — mind FÜGGŐLEGESEN, és egyik
        # sem kézi szerkesztés (egész `scale=337,0000`, a legyező
        # tartományán belüli theta; a kézi eseteket az AI2 nem egész
        # 295,392-je és +345°-a azonnal elárulja).
        #
        # A magyarázat: az eredeti a KÖZÉPPONTOT korlátozza egy sávra, a
        # csempe TÉGLALAPJÁT nem. Fekvő lapon a csempe magassága a lap
        # arányában nagyobb, ezért sávon belüli középpont mellett is
        # kilóghat a teteje vagy az alja — a három eltérés mind függőleges,
        # egy sem vízszintes.
        #
        # A SÁV-képlet marad: az hat mintán igazolt, álló, négyzetes ÉS
        # fekvő lapon. A beszorítás volt a hozzátoldás, és a tulajdonos
        # kikötése ezt nem engedi: „Minden UGYANÚGY működjön… Semmi
        # »kitaláljuk« funkció ebben!"
        kozep_x = place.center_x
        kozep_y = place.center_y
        nodes.append(
            CollageNode(
                path=path,
                center_x=pixels_to_sheet(kozep_x, settings.width),
                center_y=pixels_to_sheet(kozep_y, settings.width),
                width=pixels_to_sheet(kulso_w, settings.width),
                height=pixels_to_sheet(kulso_h, settings.width),
                theta=place.theta,
                border=keret,
                fill=kitolt,
            )
        )
    return nodes


def _multi_exposure_nodes(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings,
) -> list[CollageNode]:
    """A Többszörös exponálás geometriája csomópontokká (#989).

    A téma nem HELYEZ el képeket, hanem egymásra vetíti őket — de a
    vetítésnek is van geometriája: a `blend_multi_exposure` minden képet a
    TELJES lapra igazít (`multi_exposure_size` = a közös illesztő), és
    középre teszi. Pontosan ezt írja le ez a csomópont-lista, ugyanazzal az
    illesztővel; így a panel vászna sem talál ki saját elrendezést.

    ⚠️ A **rajzolás** ettől még más marad: a mentés az egyenlő súlyú
    keverést végzi (`make_picasa_collage`), a vászon pedig egymásra rakja a
    csempéket. A HELYÜK és a MÉRETÜK viszont ugyanaz.
    """
    keret = settings.effective_border
    kozep_x = pixels_to_sheet(settings.width / 2.0, settings.width)
    kozep_y = pixels_to_sheet(settings.height / 2.0, settings.width)
    nodes: list[CollageNode] = []
    for aspect, path in zip(aspects, paths, strict=False):
        cel_w, cel_h = fit_aspect_inside(aspect, settings.width, settings.height)
        kulso_w, kulso_h = outer_box(max(1, cel_w), max(1, cel_h), keret)
        nodes.append(
            CollageNode(
                path=path,
                center_x=kozep_x,
                center_y=kozep_y,
                width=pixels_to_sheet(kulso_w, settings.width),
                height=pixels_to_sheet(kulso_h, settings.width),
                border=keret,
                fill=False,
            )
        )
    return nodes


def _contact_sheet_band(settings: PicasaCollageSettings) -> int:
    """Az Indexkép fejlécsávjának magassága KÉPPONTBAN."""
    return max(1, round(settings.height * _HEADER_RATIO))


def _contact_sheet_nodes(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings,
) -> tuple[list[CollageNode], int, PicasaCollageSettings]:
    """Az Indexkép cellái az ALVÁSZON koordinátáiban + a fejlécsáv.

    A fejléc alatti rész önálló lap: a külön vászonra rajzolás nem kényelmi
    kérdés, hanem VÁGÁS (a cellából kilógó keret nem írhat a fejlécbe),
    ezért a csomópontok itt még nincsenek lejjebb tolva. A teljes lapra
    értendő változatot a `layout_nodes_for_aspects` adja.

    Hármast ad vissza, hogy a `make_picasa_collage` az alvászont és a
    hozzá tartozó beállítást ne számolja ki másodszor — egy elváló másolat
    pontosan az a néma hiba, amit a #942 kerülni akar."""
    sav = _contact_sheet_band(settings)
    also = settings.height - sav
    alsobeallitas = PicasaCollageSettings(
        theme=REGULARGRID,
        border=settings.border,
        width=settings.width,
        height=max(16, also),
        background=settings.background,
        spacing=settings.spacing,
        seed=settings.seed,
    )
    sorok, oszlopok = regular_grid_shape(aspects, settings.width, max(1, also))
    rects = regular_grid_rects(len(aspects), sorok, oszlopok)
    # az Indexképnél a TELJES kép látszik (nem vágunk), ez a lényege
    return (_cell_nodes(paths, rects, alsobeallitas, fill=False), sav, alsobeallitas)


def _draw_contact_header(canvas: np.ndarray, settings: PicasaCollageSettings) -> int:
    """Az Indexkép fejlécsávja; a felhasznált magasságot adja vissza.

    A `contact_sheet.header_font_size` a betűméretet a lap magasságából és a
    panel oldalarányából számolja; a sáv maga a lap tetején ül.
    """
    from .contact_sheet import header_font_size

    band = _contact_sheet_band(settings)
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
        nodes, sav, _ = _contact_sheet_nodes(aspects, paths, settings)
        # a cellák az ALVÁSZON koordinátáiban készültek; a lapra a
        # fejlécsávval lejjebb tolva kerülnek
        eltolas = pixels_to_sheet(sav, settings.width)
        return [replace(node, center_y=node.center_y + eltolas) for node in nodes]
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
        tobbi = [a for index, a in enumerate(aspects) if index != rogzitett]
        tobbi_ut = [ut for index, ut in enumerate(paths) if index != rogzitett]
        nodes = []
        if tobbi:
            rects = pack(
                tobbi,
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
    # forrása. A Többszörös exponálás nem helyez el képeket, ott üres marad.
    rajzolt: tuple[CollageNode, ...] = ()
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
        nodes, _, alsobeallitas = _contact_sheet_nodes(
            _aspects(decoded), used, settings
        )
        # az árnyék paraméterei a TELJES lapból jönnek (a `k` a lap hasznos
        # területéből számol, ld. 9/b.3) — nem az alvászonéból
        draw_nodes(
            alvaszon,
            nodes,
            decoded,
            alsobeallitas.width,
            shadow_for_settings(settings, len(decoded)),
        )
        canvas[sav : sav + alvaszon.shape[0], :] = alvaszon
        # a csomópontok az ALVÁSZON koordinátáiban készültek; a piszkozat a
        # TELJES lapot írja le, ezért a fejlécsávval lejjebb tolva jelentjük
        eltolas = pixels_to_sheet(sav, settings.width)
        rajzolt = tuple(
            replace(node, center_y=node.center_y + eltolas) for node in nodes
        )
    else:
        nodes = layout_nodes(decoded, used, settings)
        draw_nodes(
            canvas, nodes, decoded, settings.width, shadow_for_settings(settings, len(decoded))
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
