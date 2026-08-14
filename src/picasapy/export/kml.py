"""Google Earth-export: KML-dokumentum építése geocímkézett képekből (#530).

**A szerkezet az eredeti Picasa `runtime/geotag.kml` sablonjából való**, a
dokumentum viszont KÓDBÓL épül, nem a Google fájljának másolatából — ahogy a
webexportnál is saját sablon (`webexport/templates/feher`) szállítunk. Amit
átveszünk, az a KML-váz és a viselkedés:

- képenként **két** stílus (`picasaDisplayNormal_<uid>` és
  `…Highlight_<uid>`), a kiemelt ikon `scale`-je 2, és egy `StyleMap` köti
  össze őket — ettől nő meg az ikon, ha az egérrel fölé mész;
- `LabelStyle/scale = 0`: a felirat **alapból rejtett**, csak a buborékban
  jelenik meg (különben a sok képnél olvashatatlan lenne a térkép);
- `BalloonStyle/text = $[description]` — a buborék a helyjelző saját
  leírását mutatja, benne a bélyegképpel és a felirattal;
- a helyjelzők egy `<Folder>`-be kerülnek, `<open>1</open>`-nel.

**Amit szándékosan NEM veszünk át:** az eredeti buborék alján egy
`picasa.google.com`-ra mutató logó-hivatkozás áll. A szolgáltatás megszűnt, a
kép nem tölthető be — halott hivatkozást nem exportálunk. A dokumentum neve
is a sajátunk.

A KML nyílt szabvány (OGC), a Google Earth ma is olvassa.
"""

from __future__ import annotations

from dataclasses import dataclass
from xml.sax.saxutils import escape

#: A nézőpont alapértelmezett magassága méterben. Az eredeti a kép helyéhez
#: állította a kamerát; a konkrét értéket a sablon `%LOOK_AT%` helyőrzője
#: mögött a program számolta, és az nem olvasható ki a telepítésből — ez a
#: ~1 km-es rálátás az, ami egy fotó környezetét még értelmesen mutatja.
DEFAULT_LOOK_AT_RANGE_M = 1000.0

#: A dokumentum és a mappa neve. Az eredeti „My Picasa Pictures"-t írt; mi a
#: saját nevünket használjuk (nem a Google termékét).
DOCUMENT_NAME = "PicasaPy Pictures"


@dataclass(frozen=True)
class KmlPlacemark:
    """Egy geocímkézett kép a KML-ben.

    A `uid` a stílus-azonosítókat különbözteti meg (az eredeti `%UID%`-je);
    egyedinek kell lennie a dokumentumon belül. A `thumb_href` és az
    `icon_href` a KML-hez KÉPEST relatív útvonal.
    """

    uid: str
    latitude: float
    longitude: float
    #: a helyjelző neve — az eredeti `%CAPTION_OR_NAME%`-je (felirat, vagy
    #: annak híján a fájlnév)
    name: str
    #: a buborékban megjelenő felirat (`%CAPTION%`) — lehet üres
    caption: str = ""
    icon_href: str = ""
    thumb_href: str = ""
    thumb_width: int = 0
    thumb_height: int = 0
    #: a buborékban megjelenő dátum (`%FILEDATE%`) — előre formázva
    file_date: str = ""


def _html_text(value: str) -> str:
    """Szöveg beillesztése a buborék HTML-jébe.

    A leírás CDATA-blokkban él, ezért a HTML-t is, és a CDATA lezárását is
    védeni kell: egy `]]>` sorozat a feliratban kiszakítaná a blokkot, és
    érvénytelen KML-t adna."""
    return escape(value).replace("]]>", "]]&gt;")


def _look_at(placemark: KmlPlacemark, range_m: float) -> str:
    """A kamera a kép helyére néz, felülről (`tilt` 0)."""
    return (
        "      <LookAt>\n"
        f"        <longitude>{placemark.longitude:.6f}</longitude>\n"
        f"        <latitude>{placemark.latitude:.6f}</latitude>\n"
        "        <altitude>0</altitude>\n"
        "        <heading>0</heading>\n"
        "        <tilt>0</tilt>\n"
        f"        <range>{range_m:.1f}</range>\n"
        "      </LookAt>\n"
    )


def _styles(placemark: KmlPlacemark) -> str:
    icon = escape(placemark.icon_href)
    uid = escape(placemark.uid)
    return (
        f'  <Style id="picasaDisplayNormal_{uid}">\n'
        "    <IconStyle>\n"
        f"      <Icon><href>{icon}</href></Icon>\n"
        "    </IconStyle>\n"
        "    <BalloonStyle><text>$[description]</text></BalloonStyle>\n"
        # a felirat alapból rejtett — csak a buborékban jelenik meg
        "    <LabelStyle><scale>0</scale></LabelStyle>\n"
        "  </Style>\n"
        f'  <Style id="picasaDisplayHighlight_{uid}">\n'
        "    <IconStyle>\n"
        "      <scale>2</scale>\n"
        f"      <Icon><href>{icon}</href></Icon>\n"
        "    </IconStyle>\n"
        "    <BalloonStyle><text>$[description]</text></BalloonStyle>\n"
        "  </Style>\n"
        f'  <StyleMap id="picasaDisplayStyleMap_{uid}">\n'
        "    <Pair><key>normal</key>"
        f"<styleUrl>#picasaDisplayNormal_{uid}</styleUrl></Pair>\n"
        "    <Pair><key>highlight</key>"
        f"<styleUrl>#picasaDisplayHighlight_{uid}</styleUrl></Pair>\n"
        "  </StyleMap>\n"
    )


def _description(placemark: KmlPlacemark) -> str:
    """A buborék HTML-tartalma (CDATA-ban), az eredeti táblázat-vázával."""
    sorok = ['<table width="400">']
    if placemark.thumb_href:
        meret = ""
        if placemark.thumb_width and placemark.thumb_height:
            meret = (
                f' width="{int(placemark.thumb_width)}"'
                f' height="{int(placemark.thumb_height)}"'
            )
        sorok.append(
            f'<tr><td><img src="{_html_text(placemark.thumb_href)}"{meret}></td></tr>'
        )
    if placemark.caption:
        sorok.append(f"<tr><td>{_html_text(placemark.caption)}</td></tr>")
    if placemark.file_date:
        sorok.append(
            f"<tr><td><em>{_html_text(placemark.file_date)}</em></td></tr>"
        )
    sorok.append("</table>")
    return "".join(sorok)


def _placemark(placemark: KmlPlacemark, range_m: float) -> str:
    uid = escape(placemark.uid)
    return (
        "    <Placemark>\n"
        f"      <name>{escape(placemark.name)}</name>\n"
        "      <description><![CDATA["
        f"{_description(placemark)}"
        "]]></description>\n"
        f"{_look_at(placemark, range_m)}"
        f"      <styleUrl>#picasaDisplayStyleMap_{uid}</styleUrl>\n"
        "      <Point><coordinates>"
        f"{placemark.longitude:.6f},{placemark.latitude:.6f},0"
        "</coordinates></Point>\n"
        "    </Placemark>\n"
    )


def build_kml(
    placemarks: tuple[KmlPlacemark, ...],
    *,
    folder_name: str,
    generated: str = "",
    look_at_range_m: float = DEFAULT_LOOK_AT_RANGE_M,
) -> str:
    """A teljes KML-dokumentum (#530).

    Args:
        placemarks: a geocímkézett képek — a `uid`-nak egyedinek kell lennie.
        folder_name: a képeket tartalmazó mappa neve a Google Earthben
            (nálunk az albumé/mappáé).
        generated: a dokumentum leírásába kerülő, előre formázott
            keltezés — üresnél a leírás kimarad (a tesztek így
            determinisztikusak: a modul nem olvas órát).

    Üres listánál is ÉRVÉNYES dokumentumot ad vissza (üres mappával) — a
    hívó eldöntheti, hogy egyáltalán kiírja-e.
    """
    reszek = [
        '<?xml version="1.0" encoding="UTF-8"?>\n',
        '<kml xmlns="http://earth.google.com/kml/2.0">\n',
        "<Document>\n",
        f"  <name>{escape(DOCUMENT_NAME)}</name>\n",
        "  <open>1</open>\n",
    ]
    reszek.extend(_styles(p) for p in placemarks)
    reszek.append("  <Folder>\n")
    reszek.append(f"    <name>{escape(folder_name)}</name>\n")
    if generated:
        reszek.append(
            "    <description><![CDATA["
            f"{_html_text(generated)}"
            "]]></description>\n"
        )
    reszek.append("    <open>1</open>\n")
    reszek.extend(_placemark(p, look_at_range_m) for p in placemarks)
    reszek.append("  </Folder>\n</Document>\n</kml>\n")
    return "".join(reszek)


__all__ = [
    "DEFAULT_LOOK_AT_RANGE_M",
    "DOCUMENT_NAME",
    "KmlPlacemark",
    "build_kml",
]
