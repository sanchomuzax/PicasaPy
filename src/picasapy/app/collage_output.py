"""A kollázs mentése (#943, #949) — spec 9.1, jelzések nélkül.

Tiszta réteg: a panel állapotából renderelő-beállítás, a célfájl neve, és a
tényleges renderelés + írás. A jelzéseket (`collageProgress`, `collageDone`,
`collageFailed`) a vezérlő adja — így ez a rész Qt-eseményhurok nélkül is
tesztelhető.

## A kimeneti fájl törvénye (spec 9.1, #949)

**Fájlválasztó NINCS, soha.** A hét sor, amit ez a modul megvalósít:

| kérdés | a válasz |
|---|---|
| hova | `<Képek>/Picasa/Kollázsok` |
| milyen néven | a forrásmappa/album címe; üres címnél tartalék: „kollázs" |
| ütközéskor | `név1.jpg`, `név2.jpg`… — `%s%lu`, **szóköz nélkül** |
| mi íródik | a JPEG (minőség **90**) ÉS a vele azonos nevű **`.cxf`** |
| hogyan | tmp-fájlba, majd átnevezés — előbb a `.cxf`, aztán a `.jpg` |
| felső méret | **5120** a HOSSZABBIK oldalon |
| a kép tartalma | a vászon csomópontjai, ahogy a felhasználó látja |

Két dolog, amit könnyű elrontani:

1. **A pár együtt mozog.** A `.jpg` és a `.cxf` egyetlen mentés két fele.
   Ezért az ütközés-vizsgálat MINDKETTŐT nézi (egy szabad `.jpg` név egy
   foglalt `.cxf` mellett elhasítaná egy korábbi kollázs párját), és ezért
   íródik előbb mindkét ideiglenes fájl, és csak utána nevezzük át őket. Ha
   a JPEG kódolása elszáll, a felhasználó nem lát magányos `.cxf`-et.
2. **A rajzolás a `render_nodes`-on megy** (spec 6.5), nem a
   `make_picasa_collage`-on: az utóbbi MAGA rendezné el a képeket, tehát a
   kézi átrendezés némán elveszne a mentett képen. Egyetlen kivétel a
   Többszörös exponálás, aminek nincs csomópont-geometriája — az képeket
   egymásra vetít, nem elhelyez.
"""

from __future__ import annotations

import re
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path

from picasapy.collage import write_collage
from picasapy.collage.cxf import dumps
from picasapy.collage.draft import project_from_nodes
from picasapy.collage.nodes import CollageNode
from picasapy.collage.picasa_render import (
    PicasaCollageSettings,
    make_picasa_collage,
    render_nodes,
)
from picasapy.collage.themes import (
    FRAMEGRID,
    MULTIEXP,
    PICTUREGRID,
    REGULARGRID,
)

#: A kimeneti fájl TARTALÉK neve: `il_collagefilename` = „kollázs" (spec 9.1).
FILENAME_STEM = "kollázs"

#: A mentett kép HOSSZABBIK oldala képpontban (spec 9.1). A rövidebbik a lap
#: arányából jön — a lap alakja szent, a felbontás csak korlát.
MAX_OUTPUT_EDGE = 5120

#: A JPEG minősége (spec 9.1). Nem a `write_collage` alapértéke: az eredeti
#: 90-nel mentett, és a kollázs sok apró képet tartalmaz, ahol a 92 és a 90
#: közti különbség mérhető fájlméret, nem látható minőség.
JPEG_QUALITY = 90

#: A „Kollázsok" album alapértelmezett helye, ha nincs beállított mappa.
#: A `Picasa` közbülső szint NEM elhagyható: az eredeti oda írt, és a
#: kétirányú kompatibilitás azon múlik, hogy ugyanott keressük a `.cxf`-et.
DEFAULT_OUTPUT_DIR = Path("Pictures") / "Picasa" / "Kollázsok"

#: A fájlnévben nem szereplő karakterek. A cím a felhasználótól (album- vagy
#: mappanévből) jön, tehát tartalmazhat elválasztót — az útvonalból kiszökni
#: viszont nem szabad tudnia.
_TILTOTT_KARAKTEREK = re.compile(r'[\\/:*?"<>|\x00-\x1f]')

#: Az ideiglenes fájlok utótagja írás közben (a Picasa `.cxf.tmp`-je).
_TMP_SUFFIX = ".tmp"


@dataclass(frozen=True)
class SaveResult:
    """Egy mentés eredménye — a vezérlő ebből fogalmaz üzenetet.

    `path` `None`, ha egyetlen kép sem volt olvasható: olyankor fájl sem
    születik, mert egy üres lap mentése rosszabb a semminél."""

    path: Path | None
    used: int
    missing: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()
    image_shape: tuple[int, ...] = ()
    canceled: bool = False


def output_dir(configured: str | None) -> Path:
    """A célmappa: a beállított, egyébként `~/Pictures/Picasa/Kollázsok`.

    A mappanév MAGYAR („Kollázsok"), mert ez a felhasználónak megjelenő album
    neve (spec 9.1) — a szülőmappa viszont a rendszer szokásos képmappája
    marad."""
    if configured:
        return Path(str(configured))
    return Path.home() / DEFAULT_OUTPUT_DIR


def safe_stem(title: str | None) -> str:
    """A címből fájlnév-tő: elválasztók nélkül, üres címnél „kollázs".

    A cím a forrásmappa vagy az album neve, tehát a felhasználó írta —
    pontot, perjelet, kettőspontot is tartalmazhat. A csonkolás után is
    maradhat üres szöveg (pl. „...”), ezért a tartalékra esés az UTOLSÓ
    lépés, nem az első."""
    tiszta = _TILTOTT_KARAKTEREK.sub("", str(title or ""))
    tiszta = tiszta.strip().strip(".").strip()
    return tiszta or FILENAME_STEM


def output_path(folder: Path | str, title: str | None = "") -> Path:
    """A célfájl: `<cím>.jpg`, ütközéskor `<cím>1.jpg`, `<cím>2.jpg`…

    Az `%s%lu` formátum SZÓKÖZ NÉLKÜLI (spec 9.1) — a Picasa így számozott,
    és a mi kimenetünk mellette fog állni ugyanabban a mappában."""
    mappa = Path(folder)
    to = safe_stem(title)
    for sorszam in range(0, 10_000):
        nev = to if sorszam == 0 else f"{to}{sorszam}"
        jelolt = mappa / f"{nev}.jpg"
        if not jelolt.exists() and not jelolt.with_suffix(".cxf").exists():
            return jelolt
    raise ValueError(f"Nem található szabad fájlnév a(z) {mappa} mappában.")


def output_width(page_ratio: float) -> int:
    """A kimeneti kép SZÉLESSÉGE úgy, hogy a hosszabbik oldal 5120 legyen.

    Fekvő lapon (`page_ratio <= 1`) a szélesség a korlát, állón a magasság —
    az eredeti a hosszabbik oldalt maximálta, nem a szélességet."""
    if page_ratio <= 1.0:
        return MAX_OUTPUT_EDGE
    return max(16, round(MAX_OUTPUT_EDGE / page_ratio))


def render_settings(
    *,
    theme: str,
    border: str,
    spacing: float,
    shadows: bool,
    page_ratio: float,
    background_rgb: tuple[int, int, int],
    frame_center: int,
    seed: int,
    width: int | None = None,
) -> PicasaCollageSettings:
    """A panel állapotából renderelő-beállítás.

    ⚠️ A `PicasaCollageSettings.background` **BGR** sorrendű (az OpenCV
    csatornasorrendje), a felület viszont RGB-ben gondolkodik — a fordítás
    ITT történik, egy helyen. Aki ezt kihagyja, kék helyett pirosat rajzol.
    A `frame_center` −1 értéke azt jelenti, hogy nincs rögzített kép.

    A `width` megadás nélkül a `MAX_OUTPUT_EDGE`-ből számolódik; az élő
    előnézet és a teszt kisebb lappal is dolgozhat."""
    red, green, blue = background_rgb
    tenyleges = output_width(page_ratio) if width is None else int(width)
    return PicasaCollageSettings(
        theme=theme,
        border=border,
        width=tenyleges,
        height=max(16, round(tenyleges * page_ratio)),
        background=(blue, green, red),
        spacing=spacing,
        seed=seed,
        frame_center=None if frame_center < 0 else frame_center,
        shadow=shadows,
    )


#: Melyik témában TÖLTI KI a fotó a csempéjét (vágással), és melyikben
#: illeszkedik bele arányosan. A rácsos témák hézag nélkül töltenek, a
#: Képkupac és az Indexkép a TELJES képet mutatja (`picasa_render`
#: `_cell_nodes(fill=True)` / `_pile_nodes(fill=False)`).
_FILL_THEMES = (PICTUREGRID, FRAMEGRID, REGULARGRID)


def render_nodes_of(
    nodes: Sequence, *, theme: str
) -> tuple[CollageNode, ...]:
    """A panel modell-csomópontjaiból RAJZOLÓ-csomópontok.

    A két típus (`app.collage_model.CollageNode` és
    `collage.nodes.CollageNode`) szándékosan külön él: az egyik a felület
    állapota (kijelöléssel), a másik a rajzoló bemenete (kitöltés-móddal).
    Ez a függvény a HÍD közöttük, és egyben az egyetlen hely, ahol a
    `fill` a témából megszületik — a modell nem ismeri a témát, a rajzoló
    pedig nem ismeri a kijelölést."""
    kitolt = theme in _FILL_THEMES
    return tuple(
        CollageNode(
            path=node.path or None,
            center_x=node.center_x,
            center_y=node.center_y,
            width=node.width,
            height=node.height,
            theta=node.theta,
            border=node.border,
            caption=node.caption,
            missing=node.missing,
            fill=kitolt,
        )
        for node in nodes
    )


def _report(nodes: Sequence[CollageNode], settings: PicasaCollageSettings):
    """A rajzolás — a téma dönti el, melyik bejáraton.

    A Többszörös exponálás nem HELYEZ EL képeket, hanem egymásra vetíti
    őket: ott a csomópont-geometria nem hordoz információt, tehát a
    `make_picasa_collage` a helyes út. Minden más témánál a vászon
    csomópontjai mennek ki, változtatás nélkül."""
    if settings.theme == MULTIEXP:
        utak = [Path(node.path) for node in nodes if node.path is not None]
        return make_picasa_collage(utak, settings)
    return render_nodes(nodes, settings)


def _write_pair(target: Path, image, project) -> Path:
    """A JPEG és a `.cxf` ATOMI kiírása; a JPEG útvonalát adja vissza.

    Előbb MINDKÉT ideiglenes fájl elkészül, és csak utána nevezzük át őket —
    előbb a `.cxf`-et, aztán a `.jpg`-t (spec 9.1). Így a felhasználó vagy a
    teljes párt látja, vagy semmit; egy magányos `.cxf` azt hazudná, hogy van
    hozzá kép."""
    target = Path(target)
    target.parent.mkdir(parents=True, exist_ok=True)
    cxf = target.with_suffix(".cxf")
    cxf_tmp = cxf.with_name(cxf.name + _TMP_SUFFIX)
    jpg_tmp = target.with_name(target.name + _TMP_SUFFIX)
    try:
        cxf_tmp.write_bytes(dumps(project))
        write_collage(jpg_tmp, image, JPEG_QUALITY)
        cxf_tmp.replace(cxf)
        jpg_tmp.replace(target)
    finally:
        for maradek in (cxf_tmp, jpg_tmp):
            maradek.unlink(missing_ok=True)
    return target


#: A `[Picasa] P2category` értéke, amitől az album a PROJEKTEK gyűjteménybe
#: kerül (spec 1.5 és `picasa-kollazs-felulet.md` 9.1/b; a #1029 mérte ki,
#: hogy a valódi gyűjteményben pontosan a Picasa projekt-mappái hordozzák).
PROJECTS_CATEGORY = "Projects (internal)"


def write_album_ini(folder: Path | str, album_name: str) -> Path:
    """A kimeneti mappa `.picasa.ini`-je — ettől látszik a PROJEKTEK alatt.

    ⚠️ Ez a lépés hiányzott, és emiatt a felhasználó a mentés után **semmit
    nem talált** a Projektek gyűjteményben: a kollázs kimentődött, a program
    viszont sehol nem jelölte meg a mappát projekt-albumként, tehát a bal
    hasáb nem tudta hova sorolni.

    ⚠️ **A spec itt TÉVED, és a mérés erősebb.** A `picasa-create-features.md`
    115. sora `[encoding] utf8=1` és `[Picasa] name=` szekciókat ír elő — de
    az string-jelenlétből következtetett. A VALÓDI fájl a felhasználó
    gyűjteményében ennyi:

        [Picasa]
        P2category=Projects (internal)

    és a 67 fájlos ini-korpuszban **egyetlen** `[encoding]` szekció sincs.
    Mivel a felhasználó ugyanezt a mappát a windowsos Picasa 3-mal is nyitja,
    nem írunk olyan alakot, amilyet az eredeti soha (#1050).

    A meglévő kulcsokat **megőrizzük** — a mappában korábbi Picasa-adat is
    lehet, azt felülírni adatvesztés volna.
    """
    mappa = Path(folder)
    mappa.mkdir(parents=True, exist_ok=True)
    ut = mappa / ".picasa.ini"

    # A `.picasa.ini` NEM szabványos INI (ismétlődő szekciók, BOM nélküli
    # UTF-8), ezért nem a configparserrel írjuk: soralapon egészítjük ki, és
    # csak azt, ami hiányzik.
    sorok: list[str] = []
    if ut.exists():
        try:
            sorok = ut.read_text(encoding="utf-8", errors="replace").splitlines()
        except OSError:
            sorok = []

    def _van(kulcs: str) -> bool:
        elotag = kulcs.lower() + "="
        return any(sor.strip().lower().startswith(elotag) for sor in sorok)

    if not sorok:
        sorok = ["[Picasa]"]
    elif "[picasa]" not in [sor.strip().lower() for sor in sorok]:
        sorok += ["", "[Picasa]"]

    # Csak a projekt-besorolás — `name=` és `[encoding]` NEM, mert az
    # eredeti sem ír ilyet (ld. a docstringet).
    if not _van("P2category"):
        sorok += [f"P2category={PROJECTS_CATEGORY}"]

    ut.write_text("\n".join(sorok) + "\n", encoding="utf-8")
    return ut


def render_collage(
    nodes: Sequence[CollageNode],
    settings: PicasaCollageSettings,
    target: Path | str,
    *,
    album_title: str = "",
    background_image: str = "",
    should_cancel=None,
) -> SaveResult:
    """A vászon kirajzolása és kiírása — a JPEG és a `.cxf` párja.

    A csomópontok LAPEGYSÉGBEN érkeznek (spec 6.1), tehát ugyanaz a lista
    írja le a 400 képpontos élő előnézetet és az 5120 képpontos kimenetet.
    Ha egyetlen kép sem volt olvasható, fájl NEM születik — a hívó ebből
    fogalmazza meg a „Mentés mellőzve" üzenetet.

    A `background_image` a `.cxf`-be írandó háttérkép (#1009). A rajzoló
    egyszínű hátteret fest — a képhátteret EGYELŐRE csak a projektfájl őrzi,
    tehát a kirajzolt JPEG háttere a beállított szín marad.

    A `should_cancel` a megszakítás egyetlen fogantyúja (spec 9.1): a
    rajzolás UTÁN, az írás ELŐTT kérdezzük meg. Így a megszakított mentés
    biztosan nem hagy fájlt a Kollázsok albumban — félkész kollázst találni
    ott rosszabb volna, mint semmit."""
    jelentes = _report(tuple(nodes), settings)
    hianyzo = tuple(str(ut) for ut in jelentes.missing)
    kihagyott = tuple(str(ut) for ut in jelentes.skipped)
    if should_cancel is not None and should_cancel():
        return SaveResult(
            None,
            len(jelentes.used),
            hianyzo,
            kihagyott,
            tuple(jelentes.image.shape),
            canceled=True,
        )
    if not jelentes.used:
        return SaveResult(None, 0, hianyzo, kihagyott, tuple(jelentes.image.shape))
    projekt = project_from_nodes(
        jelentes.nodes,
        settings,
        album_title=album_title,
        background_image=background_image,
    )
    ut = _write_pair(Path(target), jelentes.image, projekt)
    # A mappa megjelölése projekt-albumként — enélkül a mentett kollázs
    # SEHOL nem jelenik meg a bal hasábon (#1029 forrása a `P2category`).
    write_album_ini(ut.parent, ut.parent.name)
    return SaveResult(
        ut, len(jelentes.used), hianyzo, kihagyott, tuple(jelentes.image.shape)
    )


__all__ = [
    "DEFAULT_OUTPUT_DIR",
    "FILENAME_STEM",
    "JPEG_QUALITY",
    "MAX_OUTPUT_EDGE",
    "SaveResult",
    "output_dir",
    "output_path",
    "PROJECTS_CATEGORY",
    "output_width",
    "write_album_ini",
    "render_collage",
    "render_nodes_of",
    "render_settings",
    "safe_stem",
    "write_collage",
]
