"""FolderHierarchyController: a bal panel fa-mappanézetének híd-objektuma
(#702).

Szándékosan ÖNÁLLÓ QObject (a `folder_tree_controller.py` és a
`discovery_controller.py` mintájára), NEM az `AppController` mixinje: a
`controller.py` és a `Main.qml` forró fájlok (CONTRIBUTING.md), azok csak
a végső bekötést kapják.

A tényleges fa-építés a Qt nélküli `folder_hierarchy` modulban van; itt
csak állapot (mely ágak nyitottak, egyszerűsített-e a lánc) és a QML felé
mutató felület él. Az állapot IMMUTÁBILIS: minden változás új
`frozenset`/tuple, sosem helyben módosítás.

Nincs benne fájlrendszer-olvasás: a mappalistát a hívó adja át (az index
`folders` táblájából), ezért nem kell háttérszál sem.
"""

from __future__ import annotations

import sys

from PySide6.QtCore import Property, QObject, Signal, Slot

from .folder_hierarchy import build_hierarchy, expandable_paths, flatten


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse.

    A #1217 szabálya: a platform-döntés MODULSZINTŰ fogantyún át menjen, ne
    nyers `os.name`/`platform.system()` hívással — különben a teszt nem
    tudja kimondani, melyik ágat méri. A projekt saját őre fogta meg,
    amikor ezt elsőre elrontottam."""
    return sys.platform


def _osszehasonlito_alak(path: str) -> str:
    """A két útvonal ÖSSZEHASONLÍTÓ alakja (#1477).

    ⚠️ A fa csomópontjai `/`-rel épülnek (a `build_hierarchy` így fűzi
    össze a szinteket), a kijelölt mappa útvonala viszont a rendszertől
    jön — Windowson `\\`-rel. A nyers `startswith` emiatt a MÁSODIK szint
    után elhasal: a `C:/Users` nem előtagja a `C:\\Users\\...`-nak.

    A CI windows-lába pontosan ezen bukott el: fanézetre váltás után a
    kirajzolt sorok `['', 'C:', 'C:/Users']` maradtak, a kijelölt mappa
    pedig nem látszott (#1454 őre fogta meg).

    Windowson a kis-nagybetű sem számít (a fájlrendszer sem érzékeny rá),
    POSIX-on viszont IGEN — ott két eltérő betűzésű mappa két különböző,
    valódi mappa lehet, az összemosás adatvesztő volna."""
    # ⚠️ A SORREND SZÁMÍT, és elsőre elrontottam: Windowson az
    # `os.path.normcase` nemcsak kisbetűsít, hanem a `/`-t VISSZA is
    # alakítja `\\`-re. Ha utána normalizálnánk az elválasztót, a POSIX
    # alakú útvonalak (`/mnt/photo/...`) is szétesnének — a CI windows-lába
    # pontosan ezen bukott el a javítás első változatában:
    # `assert '/mnt/photo/Kepek/AI' in {'', '/'}`.
    # Ezért előbb a kis-nagybetű, és CSAK UTÁNA az elválasztó.
    # ⚠️ Nem `os.path.normcase`: az MAGA is platformfüggő (Linuxon
    # azonosság), tehát a `_platform()` fogantyú kicserélése nem hatna rá,
    # és a windowsos ágat Linuxon nem lehetne MÉRNI. Kifejezett kisbetűsítés
    # kell — így a fogantyú tényleg eldönti, melyik ág fut.
    alak = path.lower() if _platform().startswith("win") else path
    return alak.replace("\\", "/")


def _is_ancestor(candidate: str, target: str) -> bool:
    """Őse-e a `candidate` útvonal a `target`-nek.

    Nem elég a `startswith`: a `/mnt/photo` úgy is előtagja a
    `/mnt/photoXYZ`-nek, hogy közben semmi köze hozzá — a határon
    elválasztónak kell állnia.
    """
    if not candidate or candidate == target:
        return False
    jelolt = _osszehasonlito_alak(candidate)
    cel = _osszehasonlito_alak(target)
    if jelolt == cel or not jelolt:
        return False
    if not cel.startswith(jelolt):
        return False
    return jelolt.endswith("/") or cel[len(jelolt)] == "/"


class FolderHierarchyController(QObject):
    """A `FolderHierarchyView.qml` adatforrása."""

    rowsChanged = Signal()
    simplifiedChanged = Signal()
    treeViewChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._folders: tuple[dict, ...] = ()
        self._expanded: frozenset[str] = frozenset()
        self._simplified = False
        self._tree_view = False
        self._rows: tuple[dict, ...] = ()
        self._rebuild()

    # -- adatforrás -----------------------------------------------------

    @Slot("QVariantList")
    def setFolders(self, folders) -> None:
        """A lapos mappalista átvétele — `{"path", "count"}` elemek.

        A kinyitott ágak megmaradnak: szinkron után a felhasználó ott
        találja a fát, ahol hagyta (a már nem létező útvonalak
        egyszerűen hatástalanok maradnak a halmazban).
        """
        self._folders = tuple(dict(folder) for folder in folders or ())
        self._rebuild()

    # -- nézetmód: Egyszerű ↔ Fa (`thumbui/hviewtoggle`) -----------------

    @Property(bool, notify=treeViewChanged)
    def treeView(self) -> bool:
        """Fa-módban áll-e a bal hasáb.

        Szándékosan BOOL, nem háromállású mód: az eredetiben az „Egyszerű
        mappanézet" (`eMenuView::ID_VIEW_FOLDERS`) és a „Fanézet"
        (`eMenuView::ID_VIEW_ALL`) EGYETLEN bájt (`[+0x9d]`) két állapota,
        tehát kizáró pár — a pipa-frissítő `0x00574b70` bizonyítja
        (`docs/specs/picasa-mappanezet.md` 3.). Az „Egyszerűsített
        fanézet" ettől független kapcsoló, ezért az külön property.
        """
        return self._tree_view

    @Slot(bool)
    def setTreeView(self, value: bool) -> None:
        """A nézetmód beállítása — a `Nézet ▸ Mappanézet` két rádiótétele
        (#1454) ezt hívja. A fa tartalmát nem érinti: a lapos és a fás
        nézet UGYANABBÓL a mappalistából él, csak más alakban."""
        if bool(value) == self._tree_view:
            return
        self._tree_view = bool(value)
        self.treeViewChanged.emit()

    # -- egyszerűsített fanézet (`SimplifiedHierarchy`) ------------------

    @Property(bool, notify=simplifiedChanged)
    def simplified(self) -> bool:
        """Az „Egyszerűsített fanézet" (`eMenuView::ID_VIEW_WATCHED`)
        állapota: az egygyermekes, fotó nélküli köztes szintek
        összevonása.

        ⚠️ A MECHANIZMUS eltér az eredetitől: ott a
        `SimplifiedHierarchy = 1` az `all` gyökeret `watched`-re cseréli
        (`0x0057517c`–`0x005751ec`), vagyis a fa HATÓKÖRÉT szűkíti a
        figyelt mappák ágaira; nálunk útvonal-tömörítés, ami sosem rejt
        el mappát. A látvány hasonló, a szemantika nem — a helyreállítása
        a #1407 tárgya, a #1454 csak bekötötte a menübe azt, ami van.
        """
        return self._simplified

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a menü a `toggleSimplified`-et
    # hívja, és AZ hívja ezt — a beállító ág tehát a felületről elérhető.
    @Slot(bool)
    def setSimplified(self, value: bool) -> None:
        if bool(value) == self._simplified:
            return
        self._simplified = bool(value)
        self.simplifiedChanged.emit()
        self._rebuild()

    @Slot()
    def toggleSimplified(self) -> None:
        """A kapcsoló átbillentése — az eredeti is logikai tagadással írja
        vissza a `SimplifiedHierarchy` kulcsot (`0x005cc63f`:
        olvas → `neg/sbb/add 1` → visszaír)."""
        self.setSimplified(not self._simplified)

    # -- sorok ----------------------------------------------------------

    @Property("QVariantList", notify=rowsChanged)
    def rows(self) -> list[dict]:
        """A megjelenítendő sorok (a csukott ágak gyermekei nélkül)."""
        return list(self._rows)

    # -- kinyitás / összecsukás -----------------------------------------

    @Slot(str)
    def toggle(self, path: str) -> None:
        """Egy ág átváltása — a fa nyitó-háromszögének kattintása."""
        key = str(path)
        if key in self._expanded:
            self._expanded = self._expanded - {key}
        else:
            self._expanded = self._expanded | {key}
        self._rebuild()

    @Slot()
    def expandAll(self) -> None:
        """`Folder::ID_HIER_FOLDER_EXPAND` — „Expand All"."""
        self._set_expanded(expandable_paths(self._tree()))

    @Slot()
    def collapseAll(self) -> None:
        """`Folder::ID_HIER_FOLDER_COLLAPSE` — „Collapse All"."""
        self._set_expanded(frozenset())

    @Slot(str)
    def revealPath(self, path: str) -> None:
        """A megadott mappáig minden ős kinyitása — a kijelölt mappa
        akkor is látszódjon, ha máshonnan (keresés, rács) került
        kiválasztásra."""
        target = str(path)
        tree = self._tree()
        opened = set(self._expanded)
        opened.add("")
        for candidate in expandable_paths(tree):
            if _is_ancestor(candidate, target):
                opened.add(candidate)
        self._set_expanded(frozenset(opened))

    # -- belső ----------------------------------------------------------

    def _tree(self):
        return build_hierarchy(self._folders, simplified=self._simplified)

    def _set_expanded(self, expanded: frozenset[str]) -> None:
        if expanded == self._expanded:
            return
        self._expanded = expanded
        self._rebuild()

    def _rebuild(self) -> None:
        rows = flatten(self._tree(), self._expanded)
        if rows == self._rows:
            return
        self._rows = rows
        self.rowsChanged.emit()
