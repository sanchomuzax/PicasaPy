"""A Picasa kollázstémák képpont-geometriáját csomópontokká alakítja."""

from __future__ import annotations

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from PIL import ImageFont

from .fitting import MsvcRandom, fit_aspect_inside, picasa_round
from .frames import POLAROID_HEIGHT_RATIO
from .nodes import CollageNode, fit_outer_inside, outer_box, pixels_to_sheet
from .pile import pile_layout
from .rects import NormRect, to_pixel_rects
from .shadow import CONTACT_USABLE_HEIGHT, CONTACT_USABLE_WIDTH, cell_edge
from .themes import POLAROID

if TYPE_CHECKING:
    from .picasa_render import PicasaCollageSettings


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
            # #973: a KERETES csempe illeszkedik a négyzetbe, nem a fotó. A
            # fehér szegély korábban a négyzeten KÍVÜL nőtt (mérve +5…10%),
            # tehát a `scale`-be írt szám és a `w`/`h` ellentmondott a mért
            # szabálynak (spec 1.6/f). `noborder`-nél a növekmény nulla,
            # tehát ez visszaesik a puszta fotó-illesztésre.
            cel_w, cel_h, kulso_w, kulso_h = fit_outer_inside(aspect, oldal, keret)
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
    from .contact_sheet import CONTACT_SHEET_HEADER_RATIO

    return max(1, picasa_round(settings.height * CONTACT_SHEET_HEADER_RATIO))


def _framed_size_inside(
    aspect: float, width: int, height: int, border: str
) -> tuple[int, int]:
    """Aránytartó fotó + keret legnagyobb, a dobozba férő KÜLSŐ mérete."""
    photo_w, photo_h = fit_aspect_inside(aspect, width, height)
    # A keret a fotón KÍVÜL nő. Egész képpontos, ezért a zárt képlet helyett
    # legfeljebb a keret néhány tucat képpontját lépjük vissza.
    while photo_w > 1 and photo_h > 1:
        outer_w, outer_h = outer_box(photo_w, photo_h, border)
        if outer_w <= width and outer_h <= height:
            return outer_w, outer_h
        if aspect >= 1.0:
            photo_w -= 1
            photo_h = max(1, picasa_round(photo_w / aspect))
        else:
            photo_h -= 1
            photo_w = max(1, picasa_round(photo_h * aspect))
    return outer_box(max(1, photo_w), max(1, photo_h), border)


def _unicode_font(size: int):
    """Unicode-képes, rendszerfüggetlenül feloldható sans betű.

    A Windows Picasa Arial-közeli rajzához előbb Arialt/Liberation Sanst
    kérünk; a DejaVu Sans a Linux CI biztos tartaléka. A Pillow a puszta
    fájlnevet a platform szabványos fontmappáiban is keresi.
    """
    for name in (
        "arial.ttf",
        "Arial.ttf",
        "LiberationSans-Regular.ttf",
        "DejaVuSans.ttf",
        "NimbusSans-Regular.otf",
    ):
        try:
            return ImageFont.truetype(name, max(1, size))
        except OSError:
            continue
    # Rendkívül szűk, font nélküli környezetben legalább a rajzolás maradjon
    # működőképes; a támogatott Windows/Linux célokon a fenti ág mindig él.
    return ImageFont.load_default(size=max(1, size))


@dataclass(frozen=True)
class _ContactSheetGeometry:
    """Az Indexkép rácsa: margók, cellaméret, oszlop-/sorszám (18.2/18.4).

    Minden mező a lap ``1024 × P`` egységrendszerében (P = ``settings``
    magassága ugyanabban a léptékben, `_contact_sheet_band`-tól függetlenül).
    """

    bal: int
    fent: int
    cella_w: int
    cella_h: int
    belso: int
    oszlopok: int
    sorok: int


def _contact_sheet_geometry(
    width: int, height: int, count: int
) -> _ContactSheetGeometry:
    """Az Indexkép öt konstansa a binárisból, CSONKOLVA (kollazs-eletciklus.md 18.2).

    ⚠️ **CSONK, nem kerekítés.** A dekompilátum ``ROUND(...)``-ot mutat, de a
    bináris minden ``fistp`` elé beállítja az FPU vezérlőszavát
    (``or eax, 0xc00`` — ``0x00888258``, ``0x008882a7``, ``0x008882e6``,
    ``0x00888323``), ami a kerekítési mezőben **nulla felé csonkolást**
    jelent. A `picasa_round` (= ``floor(x+0,5)``) itt **rossz**: két
    oszlopnál a cellaszélesség kerekítéssel 451, csonkolással 450 — és a
    mért minták 450-et adnak (#2583)."""
    k = cell_edge(width, height, count)
    hasznos_w = int(width * CONTACT_USABLE_WIDTH)
    hasznos_h = int(height * CONTACT_USABLE_HEIGHT)
    oszlopok = max(1, hasznos_w // k)
    sorok = max(1, hasznos_h // k)
    return _ContactSheetGeometry(
        bal=math.trunc(width * 0.06),
        fent=math.trunc(height * 0.15),
        cella_w=math.trunc(width * CONTACT_USABLE_WIDTH / oszlopok),
        cella_h=math.trunc(height * CONTACT_USABLE_HEIGHT / sorok),
        belso=math.trunc(k * 0.08),
        oszlopok=oszlopok,
        sorok=sorok,
    )


def contact_sheet_cell_scale(width: int, height: int, count: int) -> float:
    """Az Indexkép LAP-SZINTŰ csomópontmagassága, LAPEGYSÉGBEN (18.5/18.6, #2583).

    Ez kerül a `.cxf` `scale` mezőjébe (`draft._tema_scale`) — NEM a
    csomópont saját (kirajzolt kép) doboza, mert az Indexképnél a `scale`
    a cellamagasság, amellyel a rajzoló FÜGGŐLEGESEN igazít (18.5: az
    `AI27` első sorában két, eltérő magasságú kép `y`-ja azonos).

    A `width`/`height` a lap TELJES képpontmérete (ugyanaz, amit
    `layout_nodes_for_aspects` kap `PicasaCollageSettings`-ben), a `count`
    a csomópontok száma.

    ## Miért SZÁMOLJUK, amikor az eredeti nem számolja (67. szakasz, #2923)

    A 277. kutatói kör a binárisban kimérte, hogy a csomópont `scale`-jéhez
    (`+0x2c`) **egyetlen előállító sem ír nem-konstans értéket**: az
    elrendezők nem nyúlnak hozzá, a hozzáfűző utak `1,0`-t vagy `0,0`-t
    írnak, a másolók és a dokumentum-`reset` változatlanul viszik tovább —
    az egyetlen nem-konstans forrás a FÁJL (`_atof`). A 67.4 ebből azt
    vezette le, hogy a frissen létrehozott csomópontnak `1,0`-t kellene
    kapnia, a közelítésnek pedig el kellene tűnnie.

    ⛔ **Ez a termékkövetkezmény a mérésen MEGDŐLT** (#2923), két egymástól
    független számon:

    1. a `.cxf` `y`-ja a `scale`-lel igazított doboz TETEJE (30.2: 10/10 sor,
       négy minta) — `scale = 1,0`-nál az Indexkép minden sora elcsúszna;
    2. a négy minta `scale`-je a MINTA SAJÁT cellageometriáját követi
       (31.5: 0…2 lapegység), és a másik három mintáé nem illik rá — egy
       idegen fájlból ÖRÖKÖLT érték ezt nem tudná megtenni.

    Ezért a frissen létrehozott Indexkép-csomópont itt számolt, lap-szintű
    `scale`-t kap. A MEGNYITOTT projektből hozott érték viszont érintetlenül
    megy vissza (`draft.project_from_nodes` `node_scales`, #2954) — az a
    jegynek az az ága, amelyet a mérés megerősített.

    A maradék 0…2 lapegység nem a mi hibánk: a 183. kutatói kör a bináris
    SAJÁT aritmetikájával számolva ugyanezt kapta (31.5). Őr:
    `tests/collage/test_scale_atvitel_2923.py`."""
    if count < 1:
        raise ValueError(f"Érvénytelen csomópontszám: {count}")
    geometria = _contact_sheet_geometry(width, height, count)
    cella_scale_px = max(1, geometria.cella_h - 2 * geometria.belso)
    return pixels_to_sheet(cella_scale_px, width)


def _contact_sheet_position(margo: int, cella: int, index: int, kulso: float) -> int:
    """Egy csomópont `x`-e vagy `y`-ja a sorában/oszlopában (18.4).

    ``margo + index·cella + CSONK((cella − kulso) / 2)`` — a fél-cellás
    középre igazítás OSZTÁSA is csonkol, nem csak a `cella` maga: az
    ``AI28`` második csempéjén ``(300−127)/2 = 86,5`` kerekítve 87, de a
    mért `x` csak 86-tal egyezik (#2583)."""
    return margo + index * cella + math.trunc((cella - kulso) / 2.0)


def _contact_sheet_nodes(
    aspects: Sequence[float],
    paths: Sequence[Path],
    settings: PicasaCollageSettings,
) -> tuple[list[CollageNode], int, PicasaCollageSettings]:
    """Az Indexkép Picasa-hű cellái a TELJES lap koordinátáiban.

    A ``0x00887e50`` / ``0x00888210`` bizonyított receptje: 6% bal margó,
    15% felső margó, 88% × 79% hasznos terület és a ``k`` cellaél 8%-os
    belső ráhagyása. A régi megoldás ehelyett egy 8%-os fejléc alatt a teljes
    maradék lapot hézagmentes ``regular_grid``-del töltötte ki.

    **A csomópont `h`-ja a KIRAJZOLT KÉP magassága, nem a cellamagasság**
    (18.5/18.8, #2583): az eredeti a `.cxf`-be a ``w / képarány`` dobozt
    írja, a `scale` mezőbe pedig egy LAP-SZINTŰ, minden csomópontra közös
    értéket. A régi kódunk a kettőt összemosta, ezért egy sorban a
    különböző arányú képek `h`-ja (helytelenül) mind a cellamagasságra
    ugrott.

    ⚠️ **A RAJZ ettől függetlenül a cella KÖZEPÉRE kerül** — ezt a
    tulajdonos `AI27.jpg` exportján mértük ki: a `.cxf` `y`-ra rajzolt
    változat 26…35 lapegységgel feljebb tette a képeket az eredetinél,
    a cella-közepes 1 lapegységen belül egyezik. A kettő ugyanannak a
    KÖZÉPNEK a két leolvasása: a `.cxf` `y` = közép − `scale`/2 (ezt a
    `draft._tema_scale` számolja), a rajzolt tető = közép − `h`/2.

    ⚠️ A `scale` PONTOS képlete nyitott (18.6, #1412 kutatói jegy) — a lenti
    ``cella_scale`` a legjobb ismert közelítés (``cella_h − 2·belső
    ráhagyás``), a négy mért mintán legfeljebb 2 lapegység eltéréssel. A
    183. kutatói kör megerősítette, hogy ez a maradék a bináris SAJÁT
    aritmetikájával is megvan — nem a mi hibánk, csak nem tudjuk pontosan
    reprodukálni a `scale` levezetését.
    """
    if not aspects:
        return [], _contact_sheet_band(settings), settings
    sav = _contact_sheet_band(settings)
    geometria = _contact_sheet_geometry(settings.width, settings.height, len(aspects))
    bal, fent = geometria.bal, geometria.fent
    cella_w, cella_h = geometria.cella_w, geometria.cella_h
    belso, oszlopok = geometria.belso, geometria.oszlopok
    cella_scale = max(1, cella_h - 2 * belso)
    keret = settings.effective_border
    nodes: list[CollageNode] = []
    for index, (aspect, path) in enumerate(zip(aspects, paths, strict=False)):
        sor, oszlop = divmod(index, oszlopok)
        # A bináris sorrendje számít: előbb a keretes befoglaló illeszkedik
        # a TELJES cellába (`FUN_009b4aa0`), aztán mind a négy él beljebb
        # lép `0,08·k`-val (`0x008884b4`–`0x008884da`). Ha előbb a cellát
        # szűkítjük, az AI6 csempéi körülbelül 4%-kal túl szélesek lesznek.
        kulso_w, _ = _framed_size_inside(aspect, cella_w, cella_h, keret)
        kulso_w = max(1, kulso_w - 2 * belso)
        # A kirajzolt kép magassága a SAJÁT szélességéből és arányából jön —
        # nem a cellából (18.8: a régi kód itt tévedésből a cellamagasságot
        # adta vissza minden csomópontra).
        kulso_h = max(1, picasa_round(kulso_w / aspect))
        x = _contact_sheet_position(bal, cella_w, oszlop, kulso_w)
        y = _contact_sheet_position(fent, cella_h, sor, cella_scale)
        # ⚠️ #2583 (a szem-teszt lelete): a csomópont KÖZEPE a cella közepe,
        # tehát a RAJZ a saját magasságával középre kerül — a `.cxf`-be írt
        # `y` viszont a LAP-SZINTŰ `scale`-lel középre igazított doboz teteje
        # (`draft._tema_scale`). A kettő ugyanannak a KÖZÉPNEK a két
        # leolvasása, és az eredeti mindkettőt így adja:
        #
        #   AI27, 1. sor: cella 217…788, scale 500 ⇒ `.cxf` y = 502,5 − 250 = 252 ✓
        #                 a rajzolt 459 magas kép teteje = 502,5 − 229,5 = 273 ✓
        #
        # MÉRVE a tulajdonos `AI27.jpg` exportján: a mi kimenetünk a
        # javítás előtt 26…35 lapegységgel FELJEBB rajzolt (a `scale`-lel
        # igazított tetőre), utána a négy kép eltérése dx ≤ 1, dy ≤ 1.
        nodes.append(
            CollageNode(
                path=path,
                center_x=pixels_to_sheet(x + kulso_w / 2.0, settings.width),
                center_y=pixels_to_sheet(y + cella_scale / 2.0, settings.width),
                width=pixels_to_sheet(kulso_w, settings.width),
                height=pixels_to_sheet(kulso_h, settings.width),
                border=keret,
                fill=False,
            )
        )
    return nodes, sav, settings
