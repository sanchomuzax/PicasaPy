"""A bal panel HIERARCHIKUS mappanézetének adatszerkezete (#702).

Tiszta függvények, Qt nélkül: a lapos mappalistából (a `folders` tábla
sorai) építik fel a fát, és lapítják ki megjelenítendő sorokká. Így a
viselkedés a QML és a szálkezelés nélkül is tesztelhető.

**Mit követ ez az eredetiből** (bizonyíték: `docs/specs/ui-audit-mainwindow.md`
1.4 és 1.7, a `Picasa3i18n.dll` string-táblája és a `Picasa3.exe` index):

- a fa gyökere egy VIRTUÁLIS sor, `ViewRoot::All` = „My Computer"
  (magyarul „Sajátgép") — nem valódi mappa, ezért az útvonala üres;
- a darabszám a részfa ÖSSZES fotóját számolja (a képernyőképen
  `Sajátgép (1 072)` = 227 + 842 + 3);
- az „egyszerűsített fanézet" (`eMenuView::ID_VIEW_WATCHED`, a
  `SimplifiedHierarchy` beállításkulcs) az egygyermekes, saját fotó
  nélküli KÖZTES szinteket vonja össze egyetlen sorrá.

Minden érték immutábilis (`frozen` dataclass, tuple) — a fa átépítése új
objektumot ad, sosem módosít meglévőt.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, replace

#: Importált Windows-útvonalak is előfordulhatnak a `folders` táblában,
#: ezért mindkét elválasztót fogadjuk (a `models.py` mintájára).
_PATH_SEPARATORS = re.compile(r"[/\\]")

#: A virtuális nézet-gyökér útvonala. Szándékosan üres sztring: nem valódi
#: mappa, tehát nem is választható ki fotólistának.
ROOT_PATH = ""


@dataclass(frozen=True)
class HierNode:
    """Egy csomópont a mappafában.

    name:  a megjelenő felirat (összevont láncnál a teljes lánc)
    path:  a valódi útvonal (a virtuális gyökérnél `ROOT_PATH`)
    own:   a mappa SAJÁT fotóinak száma (indexeletlen köztes szinten 0)
    total: a részfa összes fotója (`own` + a gyermekek `total`-jai)
    """

    name: str
    path: str
    own: int
    total: int
    children: tuple[HierNode, ...] = ()


def _split(path: str) -> list[str]:
    """Egy útvonal nem üres komponensei.

    A POSIX-gyökér (a vezető perjel) üres tagként esne ki, ezért itt
    kimarad — önálló szintként a hívó teszi vissza.
    """
    return [part for part in _PATH_SEPARATORS.split(path) if part]


def _join(parent_path: str, name: str) -> str:
    """Gyermek-útvonal a szülő útvonalából és a komponens nevéből."""
    if parent_path in ("", "/"):
        return parent_path + name
    return parent_path + "/" + name


def _insert(tree: dict, path: str, count: int) -> None:
    """Egy mappa beszúrása a köztes szintekkel együtt (mutábilis
    segéd-szótár, kizárólag az építés idejére — a kifelé adott fa
    immutábilis)."""
    parts = _split(path)
    if not parts:
        return
    node = tree
    if path.startswith("/"):
        # A POSIX-gyökér önálló szint: `/mnt/photo` → `/` → `mnt` → `photo`
        node = node.setdefault("/", {"name": "/", "own": 0, "children": {}})[
            "children"
        ]
    for index, part in enumerate(parts):
        child = node.setdefault(
            part, {"name": part, "own": 0, "children": {}}
        )
        if index == len(parts) - 1:
            child["own"] += count
            # A VALÓDI (indexelt) mappa útvonala betűre pontosan megmarad
            # — importált Windows-útvonalnál a visszafelé alkotott alak
            # (`C:/Users`) nem egyezne az index `folders.path` értékével,
            # és a sorra kattintás némán nem találna mappát.
            child["real"] = path
        node = child["children"]


def _freeze(raw: dict, parent_path: str) -> tuple[HierNode, ...]:
    """A mutábilis építő-szótárból immutábilis `HierNode`-fa, a
    részfa-összegek kiszámításával. Testvérek név szerint, kis-nagybetűt
    nem különböztetve rendezve — ahogy a Mappakezelő fája is."""
    nodes = []
    for key in sorted(raw, key=str.lower):
        entry = raw[key]
        computed = _join(parent_path, key) if key != "/" else "/"
        path = entry.get("real") or computed
        children = _freeze(entry["children"], computed)
        own = entry["own"]
        nodes.append(
            HierNode(
                name=entry["name"],
                path=path,
                own=own,
                total=own + sum(child.total for child in children),
                children=children,
            )
        )
    return tuple(nodes)


#: #1407: a mért szűrő — a két karakternél nem hosszabb bejegyzés kimarad
#: (`0x0057430b cmp eax, 2` / `jbe`), tehát a puszta meghajtó-gyökerek
#: (`C:`, `/`) nem lesznek ágak.
_LEGROVIDEBB_GYOKER = 3


def _simplify(node: HierNode) -> HierNode:
    """Egygyermekes, saját fotó nélküli köztes szintek összevonása.

    ⚠️ #1407: ez NEM az „Egyszerűsített fanézet" — az a fa HATÓKÖRÉT
    szűkíti (`_watched_root`). Ez útvonal-tömörítés: a
    `/` → `mnt` → `photo` lánc egyetlen `/mnt/photo` sorrá válik. A kettő
    EGYÜTT megy: a szűkített fa ágain belül a tömörítés továbbra is
    olvashatóbbá teszi a hosszú láncokat.
    """
    children = tuple(_simplify(child) for child in node.children)
    if len(children) == 1 and node.own == 0:
        only = children[0]
        merged_name = (
            "/" + only.name if node.name == "/" else node.name + "/" + only.name
        )
        return replace(only, name=merged_name)
    return replace(node, children=children)


def build_hierarchy(
    folders, *, simplified: bool = False, watched_roots=()
) -> HierNode:
    """A virtuális nézet-gyökér a teljes mappafával.

    folders: `{"path": str, "count": int}` alakú elemek (a `name` mezőt
    nem használjuk — a fa a saját komponens-neveit rajzolja, mert a
    köztes szintek nincsenek benne a listában).

    watched_roots: a FIGYELT mappák útvonalai. Az „Egyszerűsített
    fanézet" ezekre szűkíti a fát (#1407) — ez a mért szemantika, nem az
    útvonal-tömörítés.
    """
    raw: dict = {}
    for folder in folders:
        path = str(folder.get("path", ""))
        try:
            count = int(folder.get("count", 0) or 0)
        except (TypeError, ValueError):
            count = 0
        _insert(raw, path, count)
    children = _freeze(raw, "")
    root = HierNode(
        name="",
        path=ROOT_PATH,
        own=0,
        total=sum(child.total for child in children),
        children=children,
    )
    if simplified:
        #: #1407: az eredetiben a `SimplifiedHierarchy = 1` az `all`
        #: gyökeret `watched`-re cseréli (`0x0057517c`–`0x005751ec`),
        #: vagyis a fa a FIGYELT MAPPÁK ágaira szűkül. Enélkül a mód csak
        #: útvonal-tömörítés volt, ami sosem rejtett el mappát.
        root = _watched_root(root, watched_roots)
        # A gyökér maga sosem olvad össze (ő a `ViewRoot::All` sor), csak
        # a gyermek-ágai rövidülnek.
        root = replace(root, children=tuple(_simplify(c) for c in root.children))
    return root


def _keresd(node: HierNode, path: str) -> HierNode | None:
    """A megadott útvonalú csomópont a fában, vagy `None`."""
    if node.path == path:
        return node
    for child in node.children:
        if path == child.path or path.startswith(child.path.rstrip("/") + "/"):
            talalat = _keresd(child, path)
            if talalat is not None:
                return talalat
    return None


def _watched_root(root: HierNode, watched_roots) -> HierNode:
    """A fa hatókörét a figyelt mappák ágaira szűkíti (#1407).

    ⚠️ Üres listára a TELJES fa marad. Ha nem tudjuk, mi a figyelt mappa,
    a szűkítés nem találgat: a felhasználó mappáit elrejteni rosszabb
    kimenet, mint a szűkítés elmaradása."""
    utak = [
        str(ut) for ut in (watched_roots or ())
        if len(str(ut)) >= _LEGROVIDEBB_GYOKER
    ]
    if not utak:
        return root
    agak: list[HierNode] = []
    for ut in sorted(set(utak)):
        csomopont = _keresd(root, ut.rstrip("/") or ut)
        if csomopont is not None and csomopont is not root:
            agak.append(csomopont)
    if not agak:
        return root
    return replace(
        root, children=tuple(agak), total=sum(ag.total for ag in agak)
    )


def expandable_paths(root: HierNode) -> frozenset[str]:
    """Minden olyan csomópont útvonala, aminek van gyermeke — ebből lesz
    az „Expand All" (`Folder::ID_HIER_FOLDER_EXPAND`) új állapota."""
    paths: set[str] = set()

    def walk(node: HierNode) -> None:
        if node.children:
            paths.add(node.path)
        for child in node.children:
            walk(child)

    walk(root)
    return frozenset(paths)


def flatten(root: HierNode, expanded) -> tuple[dict, ...]:
    """A fa megjelenítendő soraivá lapítva, a kinyitott ágakat követve.

    Egy sor: `kind` („root" a virtuális gyökérsor, egyébként „folder"),
    `name`, `path`, `depth`, `count` (a részfa összege), `own` (a mappa SAJÁT
    fotói), `hasChildren`, `expanded`. A `kind` azért kell, mert a gyökérsor
    feliratát a QML adja (`qsTr("My Computer")`) — felhasználói szöveg nem
    Pythonból jön.

    Az `own` a #2983 óta van a soron: a mappa-borítót CSAK saját fotóval
    rendelkező sorra kérjük el. A szintetikus köztes szintek (`C:`,
    `C:/Users`, a hálózati gazdanév) `own = 0`-sak — nincs mit kupacba
    rakni, és a borító-kérés minden ilyen sorra egy „Failed to get image
    from provider" naplósort írt a felhasználó konzoljára.
    """
    open_paths = frozenset(expanded)
    rows: list[dict] = []

    def emit(node: HierNode, depth: int, kind: str) -> None:
        is_open = node.path in open_paths and bool(node.children)
        rows.append(
            {
                "kind": kind,
                "name": node.name,
                "path": node.path,
                "depth": depth,
                "count": node.total,
                "own": node.own,
                "hasChildren": bool(node.children),
                "expanded": is_open,
            }
        )
        if is_open:
            for child in node.children:
                emit(child, depth + 1, "folder")

    emit(root, 0, "root")
    return tuple(rows)
