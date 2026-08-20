"""A kollázs-vászon csomópont-modellje (#943).

Szerződés: `docs/specs/kollazs-panel-ui-spec.md` **6.2**.

A lista sorrendje a **RAJZOLÁSI sorrend**: a 0. index van legalul, az
utolsó legfelül — ugyanaz az irány, amit a `collage/canvas.py` és a `.cxf`
is tart. Ezért működnek a `canvas.py` rétegsorrend-függvényei (`move_up`,
`move_to_top`, …) közvetlenül ezen a listán: azok is a lista VÉGÉT tekintik
a legfelső rétegnek.

**Minden szám a lap 1024 egységes koordinátarendszerében van** (6.1), nem
képpontban: `képernyő_x = lap.x + u * lap.szélesség / 1024`, és
ugyanezzel az OSZTÓVAL a függőleges is — a lap méretez, de nem torzít.

**A kép és a rés szétválasztása.** A csomópont két, jól elkülönülő dolgot
ír le: hol van a RÉS a lapon (középpont, méret, szög, keret, kijelöltség),
és melyik KÉP ül benne (útvonal, felirat, „nem található" jelző). A panel
két parancsa — a képek összekeverése és az egymásra ejtés — a KÉPET
mozgatja, a rést a helyén hagyja (spec: „a fogadó mérete/kerete/szöge
marad"). Ezt a `Picture` hármas és a `with_pictures*` függvények teszik
egyértelművé; a felirat és a hiány-jelző a képhez tartozik, tehát vele
együtt költözik — különben egy csere után idegen felirat maradna a
Polaroid-kereten.
"""

from __future__ import annotations

from collections.abc import Iterable, Sequence
from dataclasses import dataclass, replace
from typing import NamedTuple

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from picasapy.collage.pile import PILE_BASE_RATIO, pile_scale
from picasapy.collage.themes import BORDER_THEMES, NOBORDER
from .formatting import to_file_url

#: A lap belső szélessége egységben (6.1) — `0xcf3f68 = 1/1024`.
SHEET_UNITS = 1024.0

_ROOT_INDEX = QModelIndex()


@dataclass(frozen=True)
class CollageNode:
    """Egy kép helye a vásznon.

    `center_x` / `center_y` a középpont **lapegységben**, `width` / `height`
    a csomópont mérete **forgatás előtt, a kerettel együtt**, `theta` a
    forgatás **radiánban** (0 = felfelé, pozitív = az óramutató járása
    szerint).

    ⚠️ **Az `aspect` a KÉP oldalaránya, nem a résé** (#989). Amíg minden
    téma a Képkupac szórását kapta, a rés doboza mindig a kép arányát vette
    fel, tehát a `width / height` visszaadta azt. A rácsos témák viszont
    CELLÁBA vágnak: ott a doboz a celláé, és a kép aránya menthetetlenül
    elveszne — márpedig a következő újrarendezéshez (`packing.pack`,
    `regular_grid_shape`) pontosan a kép aránya kell. A képhez tartozik,
    ezért a `Picture`-rel EGYÜTT költözik cserénél és keverésnél.
    """

    path: str
    center_x: float
    center_y: float
    width: float
    height: float
    theta: float = 0.0
    border: str = NOBORDER
    caption: str = ""
    selected: bool = False
    missing: bool = False
    aspect: float = 1.0

    def __post_init__(self) -> None:
        if self.border not in BORDER_THEMES:
            raise ValueError(
                f"Ismeretlen képkeret: {self.border!r} (várt: {BORDER_THEMES})"
            )
        if self.width <= 0.0 or self.height <= 0.0:
            raise ValueError(
                f"Érvénytelen csomópont-méret: {self.width}×{self.height}"
            )
        if not self.aspect > 0.0:
            raise ValueError(f"Érvénytelen kép-oldalarány: {self.aspect}")


class Picture(NamedTuple):
    """A csomópontban ülő KÉP — a réstől független adatai."""

    path: str
    caption: str
    missing: bool
    #: A kép oldalaránya; a képpel EGYÜTT költözik (ld. `CollageNode.aspect`).
    aspect: float = 1.0


def initial_node_width(count: int) -> float:
    """A csomópontok kezdő szélessége lapegységben, a DARABSZÁMBÓL (6.2).

    ```
    n <= 1 → s = 1,0
    n  > 1 → s = min(1,0; 1 / sqrt(sqrt(n) − 1))
    alapszélesség = s * 1024 * 0,33
    ```

    A képlet nincs újraírva: a `collage.pile.pile_scale` UGYANEZ a
    lecsengés (ott a kép sorszámára alkalmazva), a 0,33-as alaparány pedig
    a `pile.PILE_BASE_RATIO`. Egy kép a lap szélességének harmadát kapja,
    10 képnél ~0,68-szorosát, 100-nál ~0,33-szorosát.
    """
    return pile_scale(max(1, int(count))) * PILE_BASE_RATIO * SHEET_UNITS


# --- Tiszta függvények a csomópont-listán ------------------------------------


def selected_indices(nodes: Sequence[CollageNode]) -> tuple[int, ...]:
    """A kijelölt csomópontok indexei, rajzolási sorrendben.

    A kijelölés EGYETLEN helyen él: a csomópont `selected` mezőjében. Így a
    rétegsorrend-műveletek (amik a listát rendezik át) automatikusan viszik
    magukkal a kijelölést — nincs mit szinkronban tartani."""
    return tuple(i for i, node in enumerate(nodes) if node.selected)


def with_selection(
    nodes: Sequence[CollageNode], indices: Iterable[int]
) -> tuple[CollageNode, ...]:
    """Új lista a megadott indexekre állított kijelöléssel.

    A sávon kívüli index csendben kimarad: a felületről érkező indexek
    versenyezhetnek egy közben megtörtént eltávolítással, és ezért nem
    érdemes az egész műveletet eldobni."""
    wanted = {int(i) for i in indices}
    return tuple(
        replace(node, selected=index in wanted) for index, node in enumerate(nodes)
    )


def pictures_of(nodes: Sequence[CollageNode]) -> tuple[Picture, ...]:
    """A csomópontokban ülő képek, rajzolási sorrendben."""
    return tuple(Picture(n.path, n.caption, n.missing, n.aspect) for n in nodes)


def with_pictures(
    nodes: Sequence[CollageNode], pictures: Sequence[Picture]
) -> tuple[CollageNode, ...]:
    """A képek újraosztása a RÉSEK között — a rések geometriája marad."""
    if len(nodes) != len(pictures):
        raise ValueError(
            f"A képek száma ({len(pictures)}) nem egyezik a csomópontokéval "
            f"({len(nodes)})."
        )
    return tuple(
        replace(
            node,
            path=kep.path,
            caption=kep.caption,
            missing=kep.missing,
            aspect=kep.aspect,
        )
        for node, kep in zip(nodes, pictures, strict=True)
    )


def with_pictures_swapped(
    nodes: Sequence[CollageNode], a: int, b: int
) -> tuple[CollageNode, ...]:
    """Két csomópont KÉPÉNEK cseréje; a méret, a keret és a szög marad."""
    if not (0 <= a < len(nodes) and 0 <= b < len(nodes)):
        raise ValueError(f"Érvénytelen csomópont-index: {a}, {b}")
    pictures = list(pictures_of(nodes))
    pictures[a], pictures[b] = pictures[b], pictures[a]
    return with_pictures(nodes, pictures)


# --- A Qt-modell -------------------------------------------------------------


class CollageNodeModel(QAbstractListModel):
    """A vászon `Repeater`-ének modellje — a 6.2 tíz szerepe.

    A modell csak OLVASHATÓ a QML felől: minden módosítás a vezérlőn megy
    át (`CollageMixin`), ami a tiszta függvényekkel új listát számol, és
    azt teszi be ide. Így a visszavonás és a `.cxf` mentése ugyanazokat az
    adatokat látja, mint a felület."""

    PathRole = Qt.ItemDataRole.UserRole + 1
    CenterXRole = Qt.ItemDataRole.UserRole + 2
    CenterYRole = Qt.ItemDataRole.UserRole + 3
    WidthRole = Qt.ItemDataRole.UserRole + 4
    HeightRole = Qt.ItemDataRole.UserRole + 5
    ThetaRole = Qt.ItemDataRole.UserRole + 6
    BorderRole = Qt.ItemDataRole.UserRole + 7
    CaptionRole = Qt.ItemDataRole.UserRole + 8
    SelectedRole = Qt.ItemDataRole.UserRole + 9
    MissingRole = Qt.ItemDataRole.UserRole + 10
    #: #1019: a csempe képének URL-je. Azért MODELL-szerep és nem
    #: felületi fűzés, mert a kézi `"file:" + útvonal` Windowson
    #: érvénytelen URL-t ad (a meghajtóbetű PORTNAK látszik), `#`-es
    #: fájlnévnél pedig Linuxon is elvágja a nevet — mindkét esetben
    #: NÉMÁN, üres képpel. A szabályt a Qt adja, nem mi.
    FileUrlRole = Qt.ItemDataRole.UserRole + 11

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._nodes: tuple[CollageNode, ...] = ()

    @property
    def nodes(self) -> tuple[CollageNode, ...]:
        """A csomópontok rajzolási sorrendben (0. legalul)."""
        return self._nodes

    def node_at(self, row: int) -> CollageNode:
        return self._nodes[row]

    def set_nodes(self, nodes: Sequence[CollageNode]) -> None:
        """A teljes lista cseréje.

        Azonos hosszúságnál NINCS reset, csak `dataChanged`: a reset eldobná
        a delegate-eket, és a vászon minden húzás-lépésnél villogna (a
        `FolderListModel` #10-es tanulsága). Változatlan tartalomnál semmi
        nem történik."""
        new = tuple(nodes)
        if new == self._nodes:
            return
        if len(new) == len(self._nodes):
            self._nodes = new
            top = self.index(0, 0)
            bottom = self.index(len(new) - 1, 0)
            self.dataChanged.emit(top, bottom, list(self.roleNames()))
            return
        self.beginResetModel()
        self._nodes = new
        self.endResetModel()

    def rowCount(self, parent=_ROOT_INDEX) -> int:  # noqa: N802 (Qt API)
        return 0 if parent.isValid() else len(self._nodes)

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None
        node = self._nodes[index.row()]
        return _ROLE_READERS.get(role, lambda _: None)(node)

    def roleNames(self):  # noqa: N802 (Qt API)
        return {
            self.PathRole: b"path",
            self.CenterXRole: b"centerX",
            self.CenterYRole: b"centerY",
            self.WidthRole: b"width",
            self.HeightRole: b"height",
            self.ThetaRole: b"theta",
            self.BorderRole: b"border",
            self.CaptionRole: b"caption",
            self.SelectedRole: b"selected",
            self.MissingRole: b"missing",
            self.FileUrlRole: b"fileUrl",
        }


#: Szerep → olvasó. Táblázatként rövidebb és bővítéskor egy helyen írandó,
#: mint tíz `if` a `data()`-ban.
_ROLE_READERS = {
    CollageNodeModel.PathRole: lambda n: n.path,
    CollageNodeModel.CenterXRole: lambda n: n.center_x,
    CollageNodeModel.CenterYRole: lambda n: n.center_y,
    CollageNodeModel.WidthRole: lambda n: n.width,
    CollageNodeModel.HeightRole: lambda n: n.height,
    CollageNodeModel.ThetaRole: lambda n: n.theta,
    CollageNodeModel.BorderRole: lambda n: n.border,
    CollageNodeModel.CaptionRole: lambda n: n.caption,
    CollageNodeModel.SelectedRole: lambda n: n.selected,
    CollageNodeModel.MissingRole: lambda n: n.missing,
    CollageNodeModel.FileUrlRole: lambda n: to_file_url(n.path),
    Qt.ItemDataRole.DisplayRole: lambda n: n.path,
}


__all__ = [
    "SHEET_UNITS",
    "CollageNode",
    "CollageNodeModel",
    "Picture",
    "initial_node_width",
    "pictures_of",
    "selected_indices",
    "with_pictures",
    "with_pictures_swapped",
    "with_selection",
]
