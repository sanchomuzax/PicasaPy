"""XMP sidecar-export: MWG-RS arc-régiók + hierarchikus címkék (#27).

UX-alapelv (docs/specs/ux-principles.md): "az adat soha ne ragadjon halott
formátumba" — a Picasa-specifikus `.picasa.ini` (arcok, címkék) mellé egy
digiKam/Lightroom-kompatibilis `.xmp` sidecar-t is írunk, hogy a metaadat
más eszközzel is tovább élhessen, ha a PicasaPy-t elhagyja a felhasználó.

Formátum-döntések:
- **Sidecar, nem beágyazott.** A `<kép>.xmp` a kép MELLÉ kerül (a teljes
  fájlnevet megőrizve, pl. `kep.jpg.xmp`), nem a kép belsejébe. Ez a
  darktable/exiftool-konvenció (nem az Adobe-féle kiterjesztés-cserés
  `kep.xmp`), mert RAW+JPEG párosnál (azonos törzsnév, más kiterjesztés)
  ütközés nélkül külön sidecart kap mindkét fájl. A JPEG-be ágyazott XMP
  (App1 szegmens) külön feladatra való — ld. záró jegyzet.
- **RDF/XML, sablon-alapú string-építés.** A projektnek nincs XMP/RDF
  függősége (`pyproject.toml`), és a szabvány XMP-csomag (xpacket-burok +
  fix névtér-készlet) egyszerűbb determinisztikus sablonnal, mint egy új
  külső könyvtárral. A kimenet szabványos, névtér-helyes XML — bármely
  `xml.etree.ElementTree`-vel vagy más XMP-olvasóval parse-olható.
- **Névterek**: `mwg-rs` (Metadata Working Group Regions), `stArea`/`stDim`
  (Adobe struktúra-típusok), `dc:subject` (lapos címkék, Dublin Core),
  `lr:hierarchicalSubject` (Lightroom-hierarchia, `|` elválasztóval).
- **stArea**: a Picasa rect64 (left/top/right/bottom) helyett az MWG-RS a
  téglalap KÖZEPÉT (x,y) + szélesség/magasság (w,h) tárolja, mindegyik a
  kép méretéhez viszonyítva [0..1] normalizálva (`stArea:unit="normalized"`).
"""

from __future__ import annotations

from pathlib import Path
from xml.sax.saxutils import escape, quoteattr

from picasapy.ioutil import write_atomic

from .xmp_regions import FaceRegion

_RETRY_DELAY = 0.05
_RETRY_COUNT = 4

_XPACKET_BEGIN = '<?xpacket begin="﻿" id="W5M0MpCehiHzreSzNTczkc9d"?>'
_XPACKET_END = '<?xpacket end="w"?>'
_XMPTK = "PicasaPy XMP export"

_NAMESPACES = (
    ('xmlns:rdf', "http://www.w3.org/1999/02/22-rdf-syntax-ns#"),
    ('xmlns:dc', "http://purl.org/dc/elements/1.1/"),
    ('xmlns:lr', "http://ns.adobe.com/lightroom/1.0/"),
    ('xmlns:mwg-rs', "http://www.metadataworkinggroup.com/schemas/regions/"),
    ('xmlns:stArea', "http://ns.adobe.com/xmp/sType/Area#"),
    ('xmlns:stDim', "http://ns.adobe.com/xap/1.0/sType/Dimensions#"),
)


def build_xmp(
    *,
    image_width: int,
    image_height: int,
    faces: tuple[FaceRegion, ...] = (),
    tags: tuple[str, ...] = (),
) -> str:
    """XMP RDF/XML sidecar-tartalom építése.

    Paraméterek:
    - image_width/image_height: a kép pixel-mérete ABBAN a keretben, amelyre
      a `faces` téglalapjai vonatkoznak (ha a régiók már orientáció-
      korrigáltak, ld. `xmp_regions.apply_orientation`, akkor ez a
      megjelenített méret).
    - faces: megnevezett arc-régiók (`FaceRegion`), normalizált [0..1]
      koordinátákkal (rect64-stílus: left/top/right/bottom).
    - tags: címkék; egy bejegyzés lehet lapos (`"Nyaralás"`) vagy
      hierarchikus (`"Család|Gyerekek"`, `|`-vel tagolva, Lightroom-stílus).
      A hierarchikus bejegyzés levél-eleme (utolsó szegmense) a lapos
      `dc:subject`-be is bekerül; a teljes út a `lr:hierarchicalSubject`-be.

    Visszatérési érték: teljes, xpacket-burkolt XMP-dokumentum stringként.
    """
    if image_width <= 0 or image_height <= 0:
        raise ValueError(
            f"A kép méretének pozitívnak kell lennie: {image_width}x{image_height}"
        )

    flat_tags, hierarchical_tags = _split_tags(tags)

    body_parts: list[str] = []
    if faces:
        body_parts.append(_regions_block(image_width, image_height, faces))
    if flat_tags:
        body_parts.append(_bag_block("dc:subject", flat_tags))
    if hierarchical_tags:
        body_parts.append(_bag_block("lr:hierarchicalSubject", hierarchical_tags))

    description = (
        f'<rdf:Description rdf:about=""\n    '
        + "\n    ".join(f'{name}={quoteattr(value)}' for name, value in _NAMESPACES)
        + ">\n"
        + "".join(body_parts)
        + "</rdf:Description>"
    )

    return (
        f"{_XPACKET_BEGIN}\n"
        f'<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk={quoteattr(_XMPTK)}>\n'
        '<rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">\n'
        f"{description}\n"
        "</rdf:RDF>\n"
        "</x:xmpmeta>\n"
        f"{_XPACKET_END}\n"
    )


def sidecar_path(image_path: str | Path) -> Path:
    """A kép mellé kerülő `.xmp` fájl útvonala (teljes fájlnév + `.xmp`)."""
    path = Path(image_path)
    return path.with_name(path.name + ".xmp")


def write_sidecar(
    image_path: str | Path,
    *,
    image_width: int,
    image_height: int,
    faces: tuple[FaceRegion, ...] = (),
    tags: tuple[str, ...] = (),
) -> Path:
    """XMP sidecar atomikus írása a kép mellé; visszaadja a sidecar útvonalát."""
    xmp = build_xmp(
        image_width=image_width,
        image_height=image_height,
        faces=faces,
        tags=tags,
    )
    target = sidecar_path(image_path)
    write_atomic(
        target,
        xmp.encode("utf-8"),
        lock_retries=_RETRY_COUNT,
        lock_retry_delay=_RETRY_DELAY,
        fallback_direct=True,
        suffix=".xmptmp",
    )
    return target


def _split_tags(tags: tuple[str, ...]) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """(lapos levél-címkék, teljes hierarchikus utak) — sorrend- és
    duplikátum-mentesen (a beszúrási sorrend megmarad, dict-tel dedupolva)."""
    flat: dict[str, None] = {}
    hierarchical: dict[str, None] = {}
    for tag in tags:
        if not tag:
            continue
        hierarchical[tag] = None
        leaf = tag.rsplit("|", 1)[-1]
        if leaf:
            flat[leaf] = None
    return tuple(flat), tuple(hierarchical)


def _regions_block(width: int, height: int, faces: tuple[FaceRegion, ...]) -> str:
    items = "".join(_region_item(face) for face in faces)
    return (
        '<mwg-rs:Regions rdf:parseType="Resource">\n'
        "<mwg-rs:AppliedToDimensions rdf:parseType=\"Resource\" "
        f'stDim:w="{width}" stDim:h="{height}" stDim:unit="pixel"/>\n'
        "<mwg-rs:RegionList>\n<rdf:Bag>\n"
        f"{items}"
        "</rdf:Bag>\n</mwg-rs:RegionList>\n"
        "</mwg-rs:Regions>\n"
    )


def _region_item(face: FaceRegion) -> str:
    rect = face.rect
    width = rect.right - rect.left
    height = rect.bottom - rect.top
    center_x = rect.left + width / 2
    center_y = rect.top + height / 2
    return (
        '<rdf:li rdf:parseType="Resource">\n'
        '<mwg-rs:Area rdf:parseType="Resource" '
        f'stArea:x="{center_x:.6f}" stArea:y="{center_y:.6f}" '
        f'stArea:w="{width:.6f}" stArea:h="{height:.6f}" '
        'stArea:unit="normalized"/>\n'
        f"<mwg-rs:Name>{escape(face.name)}</mwg-rs:Name>\n"
        "<mwg-rs:Type>Face</mwg-rs:Type>\n"
        "</rdf:li>\n"
    )


def _bag_block(element: str, values: tuple[str, ...]) -> str:
    items = "".join(f"<rdf:li>{escape(value)}</rdf:li>\n" for value in values)
    return f"<{element}>\n<rdf:Bag>\n{items}</rdf:Bag>\n</{element}>\n"
