"""A `.cxf` kollázs-projektfájl — írás és olvasás (#431).

Forrás: `docs/specs/picasa-create-features.md` 1.6 (a formátum a felhasználó
valódi, windowsos Picasával készített mintájából lett megfejtve, #436),
1.6/b (a téma- és keret-azonosítók) és 1.6/c (a mezőnév-lista az `.exe`-ből).

A `.cxf` a kollázs **szerkeszthető** állapota — a Picasa ezt nevezte
„piszkozatnak", és a kirenderelt JPEG mellett is megőrizte, hogy a kollázs
később is módosítható maradjon. Ezért fontos, hogy a körbejárás
(írás → olvasás → írás) bájtra pontos legyen: a Mozaik elrendezése nem
determinisztikus, tehát az egyetlen mód a pontos visszaállításra az, hogy a
fájl minden képre eltárolja a helyét, szögét és méretét.

**Formátum:** UTF-8 XML, **CRLF** sorvégekkel, `%f` (hat tizedes) számokkal.

Két meglepetés a formátumban, amit könnyű elrontani:

1. **A keret KÉPENKÉNT állítható** — a `<theme>` a `<node>`-on belül van,
   nem a gyökérben. A felület globálisnak mutatja, de az adatmodell
   megengedi a vegyes kollázst.
2. **A pozíció és a méret arányos (0…1), a `scale` viszont képpontban van**
   — a fájl felbontásfüggetlenül tárolja az elrendezést, de megőrzi az
   eredeti vetítési méretet is.

A `<src>` útvonalát **érintetlenül** őrizzük (`$My Pictures\\…`, windowsos
fordított perjelekkel): a változó feloldása az útvonal-réteg dolga. Ha itt
„megjavítanánk", a fájl az eredeti Picasában használhatatlan lenne.

> ⚠️ Amit NEM tudunk a mintából: az eredeti fájl pontos sortördelése a
> gyökérelemen belül. Mi minden attribútumot egy sorba írunk. A Picasa XML-t
> olvas vissza, nem szöveget, tehát ez nem befolyásolja a kompatibilitást.

**A három azonosító (`albumUID`, `<albumDate>`, `<uid>`) — #1092.** Ez a
modul mind a hármat ISMERI (írja is, olvassa is), üresen viszont nem írja
ki őket; a KITÖLTÉSÜK nem itt dől el:

- a csomópontok `<uid>`-ját a `draft.project_from_nodes` teszi be
  (`uids.node_uid_for`, illetve a megnyitott fájlból hozott érték),
- az `albumUID`-ot és az `<albumDate>`-et a panel adja át a képek közös
  forrásmappájából (`app/collage_album_fields.py`).

A képzési szabály a MIÉNK (a jelölés és az indoklás a `uids.py`-ban): az eredeti
értékek a Picasa belső adatbázisából jönnek. Az `albumID`-t szándékosan
NEM írjuk — a 12 golden mintából egyben sincs, és az eredeti író sem
hivatkozik rá (csak az olvasó, `0x00832830`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree
from xml.sax.saxutils import escape, quoteattr

from .themes import BORDER_THEMES, COLLAGE_THEMES, DIMMED, NOBORDER, PICTUREPILE

CXF_VERSION = 2

# A gyökér `format` attribútuma és a `CollageSpec` további alapértékei
# (`0x008342b0`): oldalarány 4:3, háttér átlátszatlan fekete.
DEFAULT_ASPECT_RATIO = "4:3"
DEFAULT_BACKGROUND_COLOR = "FF000000"

# A `<background type=…>` ismert értékei (a writer szótárából, `0x008347b0`,
# kiegészítve az 1.9.11-ben azonosított átlagszín-móddal).
BACKGROUND_TYPES = ("solid", "image", "avgcolor")

ORIENTATIONS = ("portrait", "landscape")

# A csomóponton a `dimmed` is megengedett: ezt a program a háttérként
# használt képre teszi (1.6/b).
NODE_THEMES = (*BORDER_THEMES, DIMMED)

_XML_DECLARATION = '<?xml version="1.0" encoding="utf-8" ?>'
_NEWLINE = "\r\n"


def _f(value: float) -> str:
    """A Picasa `%f`-je: mindig hat tizedes."""
    return f"{value:.6f}"


def _flag(value: bool) -> str:
    return "1" if value else "0"


@dataclass(frozen=True)
class CxfBackground:
    """A kollázs háttere — KÉT alakja van, és a különbség nem díszítés.

    Egyszínű háttérnél önzáró elem, színnel:
    `<background type="solid" color="FFFFFFFF"/>`. A szín **ARGB hexa**,
    nyolc karakter, nagybetűvel — ahogy a minta tartalmazza.

    **Képháttérnél** viszont (`AI2.cxf`, `AI5.cxf`, #1009) az eredeti Picasa
    a `color` attribútumot **el is hagyja**, és a képet gyerekelemben adja:

    ```
     <background type="image">
      <src>$My Pictures\\AI\\kep.png</src>
     </background>
    ```

    A `src` a kollázs SAJÁT képeinek egyike (a program indexszel hivatkozik
    rá, `0x00830a00`), és az útvonal — a `<node><src>`-hez hasonlóan —
    **érintetlenül** őrződik. A `color` ilyenkor a mi alapértékünk marad;
    kiírni nem írjuk ki, mert az eredeti sem teszi."""

    type: str = "solid"
    color: str = DEFAULT_BACKGROUND_COLOR
    #: A háttérként használt kép útvonala — csak `type="image"` esetén.
    src: str = ""

    def __post_init__(self) -> None:
        if self.type not in BACKGROUND_TYPES:
            raise ValueError(
                f"Ismeretlen háttértípus: {self.type!r} (várt: {BACKGROUND_TYPES})"
            )
        if len(self.color) != 8 or any(c not in "0123456789abcdefABCDEF" for c in self.color):
            raise ValueError(f"A háttérszín nyolcjegyű ARGB hexa kell legyen: {self.color!r}")


@dataclass(frozen=True)
class CxfNode:
    """Egy kép a kollázsban.

    `x`, `y`, `w`, `h` a vászon **arányában** (0…1), `theta` **radiánban**,
    `scale` **képpontban** (a forrás vetített szélessége)."""

    x: float
    y: float
    w: float
    h: float
    theta: float
    scale: float
    theme: str = NOBORDER
    src: str = ""
    uid: str = ""

    def __post_init__(self) -> None:
        if self.theme not in NODE_THEMES:
            raise ValueError(
                f"Ismeretlen képkeret: {self.theme!r} (várt: {NODE_THEMES})"
            )
        if self.w <= 0.0 or self.h <= 0.0:
            raise ValueError(f"Érvénytelen csomópont-méret: {self.w}×{self.h}")


@dataclass(frozen=True)
class CxfProject:
    """A teljes kollázs-projekt — a `.cxf` gyökere és a képei."""

    version: int = CXF_VERSION
    aspect_ratio: str = DEFAULT_ASPECT_RATIO  # a `format` attribútum, `SZ:M`
    orientation: str = "landscape"
    theme: str = PICTUREPILE
    shadows: bool = False
    captions: bool = False
    album_uid: str = ""
    album_id: str = ""
    album_title: str = ""
    album_date: str = ""
    background: CxfBackground = field(default_factory=CxfBackground)
    spacing: float = 0.0
    nodes: tuple[CxfNode, ...] = ()

    def __post_init__(self) -> None:
        if self.theme not in COLLAGE_THEMES:
            raise ValueError(
                f"Ismeretlen kollázs-típus: {self.theme!r} (várt: {COLLAGE_THEMES})"
            )
        if self.orientation not in ORIENTATIONS:
            raise ValueError(f"Ismeretlen tájolás: {self.orientation!r}")
        if not 0.0 <= self.spacing <= 1.0:
            raise ValueError(f"Érvénytelen térköz: {self.spacing} (várt: 0…1)")


# --- Írás -------------------------------------------------------------------


def _node_lines(node: CxfNode) -> list[str]:
    lines = [
        f' <node x="{_f(node.x)}" y="{_f(node.y)}"'
        f' w="{_f(node.w)}" h="{_f(node.h)}"'
        f' theta="{_f(node.theta)}" scale="{_f(node.scale)}">',
        f"  <theme>{escape(node.theme)}</theme>",
    ]
    if node.src:
        lines.append(f"  <src>{escape(node.src)}</src>")
    if node.uid:
        lines.append(f"  <uid>{escape(node.uid)}</uid>")
    lines.append(" </node>")
    return lines


def _background_lines(background: CxfBackground) -> list[str]:
    """A `<background>` elem sorai — a KÉT alak közül a megfelelő.

    A `src` jelenléte dönt, nem a `type`: így egy `type="image"`, de kép
    nélküli (sérült vagy kézzel írt) projekt sem veszíti el a színét."""
    if not background.src:
        return [
            f" <background type={quoteattr(background.type)}"
            f" color={quoteattr(background.color)}/>"
        ]
    return [
        f" <background type={quoteattr(background.type)}>",
        f"  <src>{escape(background.src)}</src>",
        " </background>",
    ]


def dumps(project: CxfProject) -> bytes:
    """A projekt `.cxf` bájtsorozattá alakítása (UTF-8, CRLF)."""
    root_attributes = [
        f'version="{project.version}"',
        f"format={quoteattr(project.aspect_ratio)}",
        f"orientation={quoteattr(project.orientation)}",
        f"theme={quoteattr(project.theme)}",
        f'shadows="{_flag(project.shadows)}"',
        f'captions="{_flag(project.captions)}"',
    ]
    if project.album_uid:
        root_attributes.append(f"albumUID={quoteattr(project.album_uid)}")
    if project.album_id:
        root_attributes.append(f"albumID={quoteattr(project.album_id)}")

    lines = [
        _XML_DECLARATION,
        "<collage " + " ".join(root_attributes) + ">",
    ]
    if project.album_title:
        lines.append(f" <albumTitle>{escape(project.album_title)}</albumTitle>")
    if project.album_date:
        lines.append(f" <albumDate>{escape(project.album_date)}</albumDate>")
    lines.extend(_background_lines(project.background))
    lines.append(f' <spacing value="{_f(project.spacing)}"/>')
    for node in project.nodes:
        lines.extend(_node_lines(node))
    lines.append("</collage>")
    return (_NEWLINE.join(lines) + _NEWLINE).encode("utf-8")


def write_cxf(target: Path | str, project: CxfProject) -> Path:
    """A projekt kiírása fájlba, **bájt-alapon**.

    Szövegmódú írásnál a Python a platform sorvégét használná (Linuxon LF),
    ami elrontaná a CRLF-et — ugyanaz a csapda, mint a `write_collage`
    ékezetes útvonalánál (#190)."""
    path = Path(target)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(dumps(project))
    return path


# --- Olvasás ----------------------------------------------------------------


def _text(parent: ElementTree.Element, tag: str) -> str:
    child = parent.find(tag)
    return "" if child is None or child.text is None else child.text


def _parse_node(element: ElementTree.Element) -> CxfNode:
    try:
        return CxfNode(
            x=float(element.get("x", "0")),
            y=float(element.get("y", "0")),
            w=float(element.get("w", "0")),
            h=float(element.get("h", "0")),
            theta=float(element.get("theta", "0")),
            scale=float(element.get("scale", "0")),
            theme=_text(element, "theme") or NOBORDER,
            src=_text(element, "src"),
            uid=_text(element, "uid"),
        )
    except (TypeError, ValueError) as error:
        raise ValueError(f"Hibás `<node>` a .cxf-ben: {error}") from error


def loads(data: bytes | str) -> CxfProject:
    """`.cxf` bájtsorozat (vagy szöveg) beolvasása projektté."""
    try:
        root = ElementTree.fromstring(data)
    except ElementTree.ParseError as error:
        raise ValueError(f"A .cxf nem értelmezhető XML: {error}") from error
    if root.tag != "collage":
        raise ValueError(
            f"A .cxf gyökéreleme `collage` kell legyen, nem {root.tag!r}."
        )

    background_element = root.find("background")
    background = (
        CxfBackground(
            type=background_element.get("type", "solid"),
            color=background_element.get("color", DEFAULT_BACKGROUND_COLOR),
            src=_text(background_element, "src"),
        )
        if background_element is not None
        else CxfBackground()
    )
    spacing_element = root.find("spacing")
    spacing = (
        float(spacing_element.get("value", "0")) if spacing_element is not None else 0.0
    )

    return CxfProject(
        version=int(root.get("version", CXF_VERSION)),
        aspect_ratio=root.get("format", DEFAULT_ASPECT_RATIO),
        orientation=root.get("orientation", "landscape"),
        theme=root.get("theme", PICTUREPILE),
        shadows=root.get("shadows", "0") == "1",
        captions=root.get("captions", "0") == "1",
        album_uid=root.get("albumUID", ""),
        album_id=root.get("albumID", ""),
        album_title=_text(root, "albumTitle"),
        album_date=_text(root, "albumDate"),
        background=background,
        spacing=spacing,
        nodes=tuple(_parse_node(node) for node in root.findall("node")),
    )


def read_cxf(source: Path | str) -> CxfProject:
    """`.cxf` beolvasása fájlból."""
    path = Path(source)
    try:
        return loads(path.read_bytes())
    except OSError as error:
        raise ValueError(f"A .cxf nem olvasható ({path}): {error}") from error


__all__ = [
    "BACKGROUND_TYPES",
    "CXF_VERSION",
    "DEFAULT_ASPECT_RATIO",
    "DEFAULT_BACKGROUND_COLOR",
    "NODE_THEMES",
    "ORIENTATIONS",
    "CxfBackground",
    "CxfNode",
    "CxfProject",
    "dumps",
    "loads",
    "read_cxf",
    "write_cxf",
]
