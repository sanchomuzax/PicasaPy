"""XMP sidecar-export: MWG-RS arcrégiók + HierarchicalSubject (issue #27).

Az UX-alapelv 5 („az adat soha ne ragadjon halott formátumba") gyakorlati
megvalósítása: a Picasa-oldali kulcsszavak, feliratok és arcrégiók egy
digiKam/Lightroom által olvasható XMP-csomagba kerülnek.

Formátum-döntések (a MWG Region Schema és a digiKam/Lightroom gyakorlat
szerint):

- **dc:subject** — lapos címkelista (kulcsszavak + arcnevek levélszinten),
  ezt a legtöbb eszköz olvassa.
- **lr:hierarchicalSubject** — hierarchikus címkék `|` elválasztóval; az
  arcok a `People|Név` út alá kerülnek (a jegy kérése).
- **dc:description** — a felirat `x-default` nyelvű `rdf:Alt`-ban.
- **mwg-rs:Regions** — arcrégiók KÖZÉPPONT-alapú, normalizált (0..1)
  koordinátákkal; a Picasa `rect64` bal/fel/jobb/alul → MWG közép+méret
  átváltással (`region_from_rect64`).

A modul tiszta (I/O nélküli) marad a felépítésben — csak a `write_sidecar`
ír lemezre, atomikusan. Minden objektum immutábilis; a builder
determinisztikus (a bemenet sorrendjét megőrzi), hogy a kimenet
tesztelhető és bitre stabil legyen.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path
from xml.sax.saxutils import escape

from picasapy.ini.rect64 import Rect64
from picasapy.ioutil import write_atomic

# Névterek (kanonikus URI-k) — a digiKam/Lightroom ezekre a pontos
# azonosítókra illeszt.
_NS_RDF = "http://www.w3.org/1999/02/22-rdf-syntax-ns#"
_NS_DC = "http://purl.org/dc/elements/1.1/"
_NS_LR = "http://ns.adobe.com/lightroom/1.0/"
_NS_MWG_RS = "http://www.metadataworkinggroup.com/schemas/regions/"
_NS_ST_AREA = "http://ns.adobe.com/xmp/sType/Area#"
_NS_ST_DIM = "http://ns.adobe.com/xap/1.0/sType/Dimensions#"

# Az XMP-csomag szabványos burkolata: BOM + xpacket feldolgozási utasítások.
_XPACKET_BEGIN = "﻿<?xpacket begin=\"﻿\" id=\"W5M0MpCehiHzreSzNTczkc9d\"?>"
_XPACKET_END = '<?xpacket end="w"?>'

# A hierarchikus arc-út alapértelmezett gyökere (People|Név).
DEFAULT_PEOPLE_ROOT = "People"


@dataclass(frozen=True)
class XmpRegion:
    """Egy MWG-RS régió: normalizált KÖZÉPPONT (x, y) + méret (w, h), 0..1.

    A `kind` a MWG `Type` (tipikusan `Face`; lehet `Pet`, `Focus` stb.).
    """

    name: str
    x: float
    y: float
    w: float
    h: float
    kind: str = "Face"


@dataclass(frozen=True)
class XmpImageMetadata:
    """Egy kép XMP-exportjának hatásos bemenete.

    - `keywords`: lapos címkék (dc:subject).
    - `hierarchical`: hierarchikus címkék (lr:hierarchicalSubject), pl.
      `People|Anna`.
    - `caption`: felirat (dc:description, x-default).
    - `dimensions`: (szélesség_px, magasság_px) az AppliedToDimensions-höz;
      None esetén az elem kimarad (a régiók normalizáltak, tehát opcionális).
    - `regions`: MWG-RS arcrégiók.
    """

    keywords: tuple[str, ...] = ()
    hierarchical: tuple[str, ...] = ()
    caption: str | None = None
    dimensions: tuple[int, int] | None = None
    regions: tuple[XmpRegion, ...] = field(default_factory=tuple)


def region_from_rect64(rect: Rect64, name: str, kind: str = "Face") -> XmpRegion:
    """`rect64` (bal/fel/jobb/alul) → MWG-RS régió (közép + méret).

    A MWG-konvenció szerint az Area x/y a régió KÖZÉPPONTJA (nem a
    bal-felső sarok), a w/h pedig a normalizált méret.
    """
    w = rect.right - rect.left
    h = rect.bottom - rect.top
    return XmpRegion(
        name=name,
        x=rect.left + w / 2.0,
        y=rect.top + h / 2.0,
        w=w,
        h=h,
        kind=kind,
    )


def build_xmp(meta: XmpImageMetadata) -> str:
    """Strukturált metaadatból teljes, xpacket-burkolt XMP-csomag."""
    body = _rdf_description(meta)
    return (
        f"{_XPACKET_BEGIN}\n"
        '<x:xmpmeta xmlns:x="adobe:ns:meta/">\n'
        f' <rdf:RDF xmlns:rdf="{_NS_RDF}">\n'
        f"{body}"
        " </rdf:RDF>\n"
        "</x:xmpmeta>\n"
        f"{_XPACKET_END}\n"
    )


def build_sidecar_from_picasa(
    *,
    keywords: Iterable[str] = (),
    caption: str | None = None,
    faces: Iterable[tuple[Rect64, str]] = (),
    dimensions: tuple[int, int] | None = None,
    people_root: str = DEFAULT_PEOPLE_ROOT,
) -> str:
    """Picasa-oldali adatokból (kulcsszavak, felirat, arcok) XMP-csomag.

    A `faces` elemei (rect64, feloldott_név) párok — a nevet a hívó oldja fel
    (contacts.xml / [Contacts2] / deferredregion). Névtelen (üres nevű) arc
    kimarad a régiókból és a címkékből.

    Felépítés (digiKam-kompatibilis):
    - dc:subject = kulcsszavak + arcnevek (levélszint, sorrend-megőrző dedup),
    - lr:hierarchicalSubject = kulcsszavak + `People|Név`,
    - mwg-rs:Regions = a nevesített arcok.
    """
    keyword_tuple = tuple(k for k in keywords if k)
    named_faces = tuple((rect, name) for rect, name in faces if name and name.strip())
    face_names = tuple(name for _rect, name in named_faces)

    flat = _dedup(keyword_tuple + face_names)
    hierarchical = _dedup(
        keyword_tuple + tuple(f"{people_root}|{name}" for name in face_names)
    )
    regions = tuple(region_from_rect64(rect, name) for rect, name in named_faces)

    return build_xmp(
        XmpImageMetadata(
            keywords=flat,
            hierarchical=hierarchical,
            caption=caption,
            dimensions=dimensions,
            regions=regions,
        )
    )


def write_sidecar(image_path: Path, xmp: str) -> Path:
    """Az XMP-csomag kiírása `<fájlnév>.xmp` sidecarba, atomikusan.

    A digiKam alapértelmezett konvenciója szerint a sidecar a teljes fájlnév
    után fűzött `.xmp` (pl. `kép.jpg` → `kép.jpg.xmp`), így az azonos nevű,
    eltérő kiterjesztésű fájlok (kép.jpg / kép.png) nem ütköznek.
    """
    image_path = Path(image_path)
    sidecar = image_path.with_name(image_path.name + ".xmp")
    write_atomic(sidecar, xmp.encode("utf-8"))
    return sidecar


# -- belső felépítők --------------------------------------------------------


def _rdf_description(meta: XmpImageMetadata) -> str:
    """A tulajdonságokat hordozó rdf:Description blokk (fix sorrend)."""
    props: list[str] = []
    if meta.keywords:
        props.append(_bag_property("dc:subject", meta.keywords, indent="   "))
    if meta.caption is not None:
        props.append(_alt_property("dc:description", meta.caption, indent="   "))
    if meta.hierarchical:
        props.append(
            _bag_property("lr:hierarchicalSubject", meta.hierarchical, indent="   ")
        )
    if meta.regions:
        props.append(_regions_property(meta, indent="   "))

    open_tag = (
        '  <rdf:Description rdf:about=""\n'
        f'    xmlns:dc="{_NS_DC}"\n'
        f'    xmlns:lr="{_NS_LR}"\n'
        f'    xmlns:mwg-rs="{_NS_MWG_RS}"\n'
        f'    xmlns:stArea="{_NS_ST_AREA}"\n'
        f'    xmlns:stDim="{_NS_ST_DIM}">\n'
    )
    return open_tag + "".join(props) + "  </rdf:Description>\n"


def _bag_property(name: str, values: tuple[str, ...], indent: str) -> str:
    """Rendezetlen (rdf:Bag) tulajdonság — dc:subject / lr:hierarchicalSubject."""
    inner = "".join(
        f"{indent}   <rdf:li>{escape(v)}</rdf:li>\n" for v in values
    )
    return (
        f"{indent}<{name}>\n"
        f"{indent}  <rdf:Bag>\n"
        f"{inner}"
        f"{indent}  </rdf:Bag>\n"
        f"{indent}</{name}>\n"
    )


def _alt_property(name: str, text: str, indent: str) -> str:
    """Nyelvi alternatíva (rdf:Alt) — a felirat x-default nyelven."""
    return (
        f"{indent}<{name}>\n"
        f"{indent}  <rdf:Alt>\n"
        f'{indent}   <rdf:li xml:lang="x-default">{escape(text)}</rdf:li>\n'
        f"{indent}  </rdf:Alt>\n"
        f"{indent}</{name}>\n"
    )


def _regions_property(meta: XmpImageMetadata, indent: str) -> str:
    """Az mwg-rs:Regions blokk: opcionális AppliedToDimensions + RegionList."""
    lines = [f"{indent}<mwg-rs:Regions rdf:parseType=\"Resource\">\n"]
    if meta.dimensions is not None:
        width, height = meta.dimensions
        lines.append(
            f"{indent} <mwg-rs:AppliedToDimensions"
            f' stDim:w="{int(width)}" stDim:h="{int(height)}"'
            ' stDim:unit="pixel"/>\n'
        )
    lines.append(f"{indent} <mwg-rs:RegionList>\n")
    lines.append(f"{indent}  <rdf:Bag>\n")
    for region in meta.regions:
        lines.append(_region_li(region, indent=f"{indent}   "))
    lines.append(f"{indent}  </rdf:Bag>\n")
    lines.append(f"{indent} </mwg-rs:RegionList>\n")
    lines.append(f"{indent}</mwg-rs:Regions>\n")
    return "".join(lines)


def _region_li(region: XmpRegion, indent: str) -> str:
    return (
        f'{indent}<rdf:li rdf:parseType="Resource">\n'
        f"{indent} <mwg-rs:Name>{escape(region.name)}</mwg-rs:Name>\n"
        f"{indent} <mwg-rs:Type>{escape(region.kind)}</mwg-rs:Type>\n"
        f"{indent} <mwg-rs:Area"
        f' stArea:x="{_fmt(region.x)}" stArea:y="{_fmt(region.y)}"'
        f' stArea:w="{_fmt(region.w)}" stArea:h="{_fmt(region.h)}"'
        ' stArea:unit="normalized"/>\n'
        f"{indent}</rdf:li>\n"
    )


def _fmt(value: float) -> str:
    """Kompakt, determinisztikus lebegőpontos formázás (max 6 értékes jegy,
    lezáró nullák nélkül) — a normalizált koordinátákhoz."""
    text = f"{value:.6g}"
    return text


def _dedup(values: tuple[str, ...]) -> tuple[str, ...]:
    """Sorrend-megőrző deduplikáció (az első előfordulás marad)."""
    seen: set[str] = set()
    result: list[str] = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return tuple(result)
