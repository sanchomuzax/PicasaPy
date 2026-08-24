"""A vászon állapota → `.cxf` projekt, és vissza (#960).

A #431 megírta a `.cxf` írását/olvasását (`cxf.py`) és a piszkozat
életciklusát (`autosave.py`), a #942 pedig a csomópont-geometriát
(`nodes.CollageNode`, `picasa_render.render_nodes`). Hívó viszont nem volt
hozzá: **egyetlen kódút sem írt piszkozatot**, mert a rajzoló nem adott
vissza csomópont-geometriát, kitalált geometriával írt piszkozat pedig
rosszabb a semminél — a formátum épp azt ígéri, hogy visszaáll.

Ez a modul a hiányzó **leképezés**: `CollageNode` ⇄ `CxfNode`. Tiszta
függvények, Qt és fájlrendszer nélkül — a piszkozat kiírását a hívó
(`app/create_controller.py`) végzi az `autosave.write_autosave`-vel.

## A mértékegységek — itt a legkönnyebb hibázni

| | `CollageNode` (vászon) | `CxfNode` (`.cxf`) |
|---|---|---|
| hely | a csempe **középpontja** | a doboz **bal-felső sarka** |
| lépték | **lapegység** (`SHEET_UNITS` = 1024, MINDKÉT tengelyen ugyanaz az osztó) | **arányos**, 0…1, **tengelyenként** a lap saját oldalához |
| `theta` | radián | radián (azonos) |
| `scale` | — | **képpont** |

A vízszintes irány ezért egyszerű (`érték / 1024`), a függőleges viszont a
lap arányával oszt: a lap magassága lapegységben `1024 · magasság/szélesség`.

## Miért a NAGYOBBIK oldal a `scale`

A spec 1.6 mintája ezt eldönti. Az álló, `format="15:10"` lapon az első
csomópont `w=0,274210`, `h=0,219401`, `scale=337,000000`:

```
w · 1024        = 280,8 lapegység          (a lap szélessége 1024)
h · 1024 · 1,5  = 337,0 lapegység          (a lap magassága 1536)
```

vagyis a `scale` a doboz **nagyobbik** oldala, 1024 képpont széles lapon.
Kereszt-ellenőrzés: a 280,8 × 337,0 doboz pontosan egy NÉGYZETES fotó
polaroid-kerete (`280,8/1,145 = 245,2`, `337,0/1,374 = 245,3` — a két
arány a `frames.py` dekompilált konstansa), és a 337 egyben a Képkupac
`pile_size`-ja is (`0,33 · 1024`). Három, egymástól független szám esik
egybe — ezért nem a szélesség, hanem a befoglaló négyzet oldala.

*Bizonyítottsági fok: erős következtetés* (a valódi mintán mért egybeesés;
a writer utasításszintű olvasata a `scale` FORRÁSÁT nem mondja ki).
"""

from __future__ import annotations

from dataclasses import replace

import math
from collections.abc import Mapping, Sequence

from .cxf import CxfBackground, CxfNode, CxfProject
from .nodes import SHEET_UNITS, CollageNode
from .picasa_render import PicasaCollageSettings
from .page_formats import format_text, is_known_format
from .themes import BORDER_THEMES, MULTIEXP, NOBORDER
from .uids import node_uid_for
from .win_paths import decode_cxf_path, encode_cxf_path

#: A `CollageSpec` alapértelmezett címe (`0x008342b0`: „Untitled").
DEFAULT_ALBUM_TITLE = ""

#: Ha az oldalarány szövege értelmezhetetlen, erre esünk vissza. A
#: helyreállítás nem omolhat össze egy kézzel átírt `format`-tól.
_FALLBACK_PAGE_RATIO = 3.0 / 4.0


def aspect_ratio_text(width: int, height: int) -> str:
    """A `format` attribútum: `NAGYOBB:KISEBB`, legegyszerűbb alakra hozva.

    A minta `format="15:10" orientation="portrait"` párosa mutatja, hogy az
    arány szövege NEM forog a tájolással — a tájolást külön mező mondja
    meg."""
    nagy = max(int(width), int(height))
    kicsi = min(int(width), int(height))
    if kicsi < 1:
        return "1:1"
    oszto = math.gcd(nagy, kicsi)
    return f"{nagy // oszto}:{kicsi // oszto}"


def _format_szoveg(format_key: str, width: int, height: int) -> str:
    """A `format` attribútum: a formátum NEVE, ha van; különben az arány.

    A `Manual` és a `CurrentDisplay` tételnek nincs neve (nincs is rájuk
    mintánk), ezekre a régi, képpontból számoló ág marad."""
    if format_key and is_known_format(format_key):
        try:
            return format_text(format_key)
        except ValueError:
            pass  # dinamikus tétel: nincs neve
    return aspect_ratio_text(width, height)


def orientation_of(width: int, height: int) -> str:
    """`portrait`, ha a lap magasabb, mint amilyen széles."""
    return "portrait" if int(height) > int(width) else "landscape"


def page_ratio_of(aspect_ratio: str, orientation: str) -> float:
    """A lap **magasság/szélesség** aránya a `format`-ból és a tájolásból."""
    try:
        elso, masodik = (float(darab) for darab in str(aspect_ratio).split(":", 1))
    except (TypeError, ValueError):
        return _FALLBACK_PAGE_RATIO
    if elso <= 0.0 or masodik <= 0.0:
        return _FALLBACK_PAGE_RATIO
    nagy, kicsi = max(elso, masodik), min(elso, masodik)
    return nagy / kicsi if orientation == "portrait" else kicsi / nagy


def _argb(background_bgr: Sequence[int]) -> str:
    """OpenCV-BGR hármas → átlátszatlan ARGB hexa, NAGYBETŰSEN (spec 1.6/d)."""
    kek, zold, piros = (int(csatorna) & 0xFF for csatorna in background_bgr)
    return f"FF{piros:02X}{zold:02X}{kek:02X}"


def cxf_node_of(
    node: CollageNode, *, page_width: int, page_ratio: float
) -> CxfNode:
    """Egy vászon-csomópont `.cxf`-alakja.

    `page_ratio` a lap magasság/szélesség aránya (ebből a függőleges
    arányosítás).

    ⚠️ **#1071 (P0): a `scale` LAPEGYSÉGBEN megy ki, nem képpontban.**

    Korábban a kimeneti lapszélességgel váltottuk át
    (`sheet_to_pixels(..., page_width)`), és 5120 képpontos kimenetnél így
    **ötszörös** érték került a fájlba. A valódi Picasa 3 ettől
    **szerkesztéskor szétesett**: óriási, felnagyított töredékeket rajzolt.

    A saját oda-vissza utunk hibátlan volt — az olvasónk
    (`collage_node_of`) a `scale`-t **egyáltalán nem használja** —, ezért a
    kódolás önmagában konzisztens maradt, csak **nem szabványos**. A hiba
    kizárólag akkor látszik, ha a fájlt MÁS program nyitja meg.

    A csomópont méretei már lapegységben vannak, tehát átváltás nem kell.
    A `page_width` paraméter megmarad, hogy a hívók ne törjenek, de a
    `scale`-re **nem hat**."""
    if page_ratio <= 0.0:
        raise ValueError(f"Érvénytelen laparánya: {page_ratio}")
    lap_magassag = SHEET_UNITS * page_ratio
    return CxfNode(
        x=(node.center_x - node.width / 2.0) / SHEET_UNITS,
        y=(node.center_y - node.height / 2.0) / lap_magassag,
        w=node.width / SHEET_UNITS,
        h=node.height / lap_magassag,
        theta=node.theta,
        scale=max(node.width, node.height),
        theme=node.border,
        # #1096: az eredeti Picasa KÓDOLT alakot ír (`$My Pictures\…`),
        # ami túléli a költöztetést és megosztható. Ami egyik ismert
        # rendszermappa alá sem esik, az változatlanul megy ki.
        src="" if node.path is None else encode_cxf_path(str(node.path)),
    )


def collage_node_of(node: CxfNode, *, page_ratio: float) -> CollageNode:
    """A `cxf_node_of` megfordítása — ebből épül vissza a vászon.

    A `dimmed` keret a HÁTTÉRKÉPÉ (spec 1.6/b), a vászon-csomópont nem
    ismeri: ilyenkor keret nélkülinek vesszük, nem dobunk hibát — egy
    idegen `.cxf` sem teheti visszaállíthatatlanná a munkát."""
    if page_ratio <= 0.0:
        raise ValueError(f"Érvénytelen laparánya: {page_ratio}")
    lap_magassag = SHEET_UNITS * page_ratio
    szelesseg = node.w * SHEET_UNITS
    magassag = node.h * lap_magassag
    return CollageNode(
        path=node.src or None,
        center_x=node.x * SHEET_UNITS + szelesseg / 2.0,
        center_y=node.y * lap_magassag + magassag / 2.0,
        width=szelesseg,
        height=magassag,
        theta=node.theta,
        border=node.theme if node.theme in BORDER_THEMES else NOBORDER,
    )


def _multiexp_alak(node: CxfNode, theme: str) -> CxfNode:
    """A Többszörös exponálás csomópontjának `scale`-je MÉRTEN 1,0 (#1248).

    Az `AI7.cxf` (valódi Picasa-minta) teljes lapos csomópontjain
    `scale="1.000000"` áll, míg az általános képletünk a doboz nagyobbik
    oldalát írja ki lapegységben (1024). A különbség nem kozmetikai: a
    #1071 mérte ki, hogy a nem szabványos `scale` a VALÓDI Picasát viszi
    szét szerkesztéskor — óriási, felnagyított töredékeket rajzol. A többi
    téma képletéhez nem nyúlunk: ott nincs mérésünk, ami ellentmondana."""
    if theme != MULTIEXP:
        return node
    return replace(node, scale=1.0)


def _azonositoval(node: CxfNode, node_uids: Mapping[str, str]) -> CxfNode:
    """A csomópont `<uid>`-ja: a MEGŐRZÖTT érték, vagy a származtatott (#1092).

    Két forrás, ebben a sorrendben:

    1. **A megnyitott projektből hozott azonosító** (`node_uids`, kulcs a
       `.cxf`-be írt `src`). Egy Picasával készült kollázs újramentése nem
       cserélheti le az eredeti azonosítókat a sajátunkra — ugyanaz a
       körbejárás-elv, amit a #1274 az `albumUID`-nál mondott ki.
    2. **Származtatás a `src`-ből** (`uids.node_uid_for`) — SAJÁT FUNKCIÓ
       (#1092), mert az eredeti `uid64` a Picasa belső adatbázisából jön,
       és nem vezethető le. A `.cxf`-jeinkből eddig teljesen HIÁNYZOTT.

    Kép nélküli csomópont azonosító nélkül marad: nincs mit azonosítani."""
    if not node.src:
        return node
    return replace(node, uid=node_uids.get(node.src) or node_uid_for(node.src))


def project_from_nodes(
    nodes: Sequence[CollageNode],
    settings: PicasaCollageSettings,
    *,
    album_title: str = DEFAULT_ALBUM_TITLE,
    album_date: str = "",
    album_uid: str = "",
    album_id: str = "",
    background_image: str = "",
    format_key: str = "",
    node_uids: Mapping[str, str] | None = None,
) -> CxfProject:
    """A kirajzolt vászonból teljes `.cxf` projekt.

    A téma, a térköz, az árnyék és a háttér a beállításból jön — de a
    TÉNYLEGESEN alkalmazott alakjukban (`effective_*`), mert a piszkozatnak
    azt kell megőriznie, amit a felhasználó lát.

    ⚠️ A `background_image` NEM a `PicasaCollageSettings`-ből jön (#1009): a
    rajzoló egyszínű hátteret fest, a képhátteret a projektfájl őrzi. Aki a
    renderelő-beállításba tenné, azt ígérné, hogy ki is rajzolódik.

    ⚠️ A `format_key` a MENÜBEN kiválasztott oldalformátum kulcsa (#1089).
    A `format` attribútum ennek a NEVE (A4 = `297:210`), nem a képpontokból
    számolt arány — a tulajdonos 11 kollázsán a képpontos képlet 6-ot
    elrontott. Kulcs nélkül (és a két dinamikus tételnél) marad az arány.

    ⚠️ A `node_uids` a MEGNYITOTT projekt `src → uid` párjai (#1092). Ami
    benne van, az változatlanul megy vissza; a többi csomópont a `src`-ből
    származtatott azonosítót kapja (`uids.node_uid_for`)."""
    uids = dict(node_uids or {})
    page_ratio = settings.height / settings.width
    return CxfProject(
        aspect_ratio=_format_szoveg(format_key, settings.width, settings.height),
        orientation=orientation_of(settings.width, settings.height),
        theme=settings.theme,
        shadows=settings.effective_shadow,
        # a felirat a POLAROID keret alsó sávjára kerül; a kapcsoló akkor
        # igaz, ha van egyáltalán mit kiírni
        captions=any(node.caption for node in nodes),
        album_title=album_title,
        album_date=album_date,
        # ⚠️ #1274: az albumUID/albumID a MEGNYITOTT projektből él tovább.
        # A `.cxf`-jeink eddig nem írták (#1092), és ami rosszabb: egy
        # Picasával készült kollázs újramentésekor a MEGLÉVŐ értéket is
        # eldobtuk. Mérve: a 12 golden minta MINDEGYIKÉBEN van albumUID.
        album_uid=album_uid,
        album_id=album_id,
        background=(
            CxfBackground(type="image", src=encode_cxf_path(background_image))
            if background_image
            else CxfBackground(type="solid", color=_argb(settings.background))
        ),
        spacing=settings.effective_spacing,
        nodes=tuple(
            _azonositoval(
                _multiexp_alak(
                    cxf_node_of(
                        node, page_width=settings.width, page_ratio=page_ratio
                    ),
                    settings.theme,
                ),
                uids,
            )
            for node in nodes
        ),
    )


def nodes_from_project(project: CxfProject | None) -> tuple[CollageNode, ...]:
    """A projekt csomópontjai vászon-alakban (a helyreállításhoz).

    `None`-ra üres sorozat: a hívó a „nincs visszaállítható piszkozat"
    esetet ugyanígy kezelheti, külön elágazás nélkül."""
    if project is None:
        return ()
    page_ratio = page_ratio_of(project.aspect_ratio, project.orientation)
    return tuple(
        _feloldott(collage_node_of(node, page_ratio=page_ratio))
        for node in project.nodes
    )


def _feloldott(node: CollageNode) -> CollageNode:
    """A `.cxf` KÓDOLT útvonalát valódira fordítja (#1096).

    Az eredeti Picasa `$My Pictures\…`, `$UNC…` és `[C]\…` alakot is ír; a
    nyers szöveget fájlnévként megnyitni néma üres csempét adott. A `.cxf`-et
    magát ez NEM írja át — csak a megjelenítés felé fordít."""
    feloldott = decode_cxf_path(node.path)
    return node if feloldott == node.path else replace(node, path=feloldott)


__all__ = [
    "DEFAULT_ALBUM_TITLE",
    "aspect_ratio_text",
    "collage_node_of",
    "cxf_node_of",
    "nodes_from_project",
    "orientation_of",
    "page_ratio_of",
    "project_from_nodes",
]
