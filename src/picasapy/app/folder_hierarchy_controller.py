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

import os

from PySide6.QtCore import (
    Property,
    QObject,
    QSettings,
    QStandardPaths,
    Signal,
    Slot,
)

from .folder_hierarchy import build_hierarchy, expandable_paths, flatten


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse.

    A #1217 szabálya: a platform-döntés MODULSZINTŰ fogantyún át menjen, ne
    nyers `os.name`/`platform.system()` hívással — különben a teszt nem
    tudja kimondani, melyik ágat méri. A projekt saját őre fogta meg,
    amikor ezt elsőre elrontottam."""
    return sys.platform


#: #1407 (spec 4.5/b): a három rendszermappa-tétel CSIDL-je és a
#: platformfüggetlen megfelelője. Az eredeti a Win32 mappa-feloldóit hívja
#: (`0x009966a0` = `CSIDL_MYPICTURES` 0x27, `0x00996230` = `CSIDL_PERSONAL`
#: 0x05, `0x00996b90` = `CSIDL_DESKTOP` 0x00); a `QStandardPaths` ugyanezt
#: adja Windowson is, Linuxon pedig az XDG-mappákat.
_RENDSZERMAPPAK = {
    "mypics": QStandardPaths.StandardLocation.PicturesLocation,
    "mydocs": QStandardPaths.StandardLocation.DocumentsLocation,
    "desktop": QStandardPaths.StandardLocation.DesktopLocation,
}


def _rendszermappa(token: str) -> str:
    """Egy rendszermappa útvonala, vagy üres sztring, ha nem oldható fel.

    Külön modulszintű függvény, hogy a teszt helyettesíthesse — a #1217
    szabálya (ld. a `_platform()` megjegyzését): a környezettől függő
    döntés MINDIG cserélhető fogantyún menjen, különben a próba a futtató
    gép XDG-beállításait méri.

    ⚠️ Nem elég, hogy a `QStandardPaths` ad egy útvonalat: a mappa LÉTEZÉSE
    is feltétel. A natív kód is ezért esik vissza az `all` gyökérre, ha a
    feloldás nem ad használható útvonalat (spec 4.6)."""
    hely = _RENDSZERMAPPAK.get(token)
    if hely is None:
        return ""
    ut = QStandardPaths.writableLocation(hely)
    if ut and os.path.isdir(ut):
        return ut
    return ""


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
    #: #2049: a mappa-borítók (fotó-kupacok) megjelenítése.
    albumThumbsChanged = Signal()
    #: #1407: a hasáb GYÖKERE és a hozzá tartozó fejlécfelirat.
    viewRootChanged = Signal()
    #: #1407: a rendszermappa-tételek NEM gyökeret váltanak, hanem a
    #: teljes fára váltás után FELFEDIK és kijelölik a mappát — ez a
    #: jelzés viszi az útvonalat a gazdának (spec 4.5/b).
    rootFolderRevealed = Signal(str)

    #: #2154: a három nézet-kapcsoló `QSettings`-kulcsa. Az eredetiben
    #: mindhárom tartós felhasználói beállítás a `Preferences` alatt
    #: (`SimplifiedHierarchy`, `ShowAlbumThumbnails2`); nálunk a `view/`
    #: rekeszbe kerülnek, ahol a hasáb többi nézet-beállítása is él.
    _KULCS_TREE_VIEW = "view/folderTreeView"
    _KULCS_SIMPLIFIED = "view/folderSimplified"
    _KULCS_ALBUM_THUMBS = "view/folderAlbumThumbs"
    #: #1407 (8. pont): a választott gyökér. Az eredeti kilépéskor írja
    #: (`LastViewRoot`/`LastViewRoot2`, `0x00576660`); nálunk AZONNAL —
    #: ugyanaz a visszaállás, de összeomlás után sem veszik el. A
    #: kettéosztás Win32 registry-részlet, a spec 8. pontja szerint
    #: hatókörön kívül.
    _KULCS_VIEW_ROOT = "view/folderViewRoot"

    #: A hat érvényes gyökér-token. `flat` és `all` a KÉT valódi gyökér
    #: (a `watched` az `all` szűkítése), a másik három a teljes fára vált
    #: és odaugrik (spec 4.5/b).
    _GYOKEREK = ("flat", "all", "watched", "mypics", "mydocs", "desktop")

    def __init__(self, parent=None, settings: QSettings | None = None):
        super().__init__(parent)
        self._settings = settings
        self._folders: tuple[dict, ...] = ()
        #: #1407: a FIGYELT mappák — az „Egyszerűsített fanézet" ezekre
        #: szűkíti a fát. Üresen a szűkítés elmarad (nem találgatunk).
        self._watched_roots: tuple[str, ...] = ()
        self._expanded: frozenset[str] = frozenset()
        #: #1407: a rendszermappa-gyökér tokenje (`mypics`/`mydocs`/
        #: `desktop`), vagy üres sztring. CSAK ez tárolódik külön: a
        #: `flat`/`all`/`watched` a két meglévő kapcsolóból SZÁRMAZIK, tehát
        #: nincs második igazságforrás.
        self._rendszer_gyoker = self._olvas_gyokeret()
        self._simplified = self._olvas(self._KULCS_SIMPLIFIED)
        #: #2049: a mappa-borítók megjelenítése — az eredetiben is
        #: kikapcsolva indul (`ShowAlbumThumbnails2`, alapérték 0).
        self._album_thumbs = self._olvas(self._KULCS_ALBUM_THUMBS)
        self._tree_view = self._olvas(self._KULCS_TREE_VIEW)
        #: #1407: a rendszermappa-gyökér a TELJES fán áll — ha ilyen volt
        #: tárolva, a fanézet is visszaáll vele. A `simplified`-hez NEM nyúl:
        #: az független, tartós kapcsoló (spec 3.).
        if self._rendszer_gyoker:
            self._tree_view = True
        self._rows: tuple[dict, ...] = ()
        self._rebuild()

    # -- tartós beállítások (#2154) --------------------------------------

    def _get_settings(self) -> QSettings:
        """Lusta alapértelmezés — a `controller.py` mintájára.

        A tesztek saját, eldobható objektumot adnak át; az alkalmazás
        paraméter nélkül hozza létre a vezérlőt."""
        if self._settings is None:
            self._settings = QSettings("PicasaPy", "PicasaPy")
        return self._settings

    def _olvas(self, kulcs: str) -> bool:
        """Egy kapcsoló beolvasása; MINDHÁROM alapértéke kikapcsolt.

        A `QSettings` az `.ini`-alakból sztringet ad vissza („true"),
        a natív tárolóból viszont `bool`-t — ezért mindkettőt kezeljük.
        Ismeretlen érték kikapcsoltnak számít: hibás beállítás-fájl ne
        billentsen be egy nézetet a felhasználó tudta nélkül."""
        ertek = self._get_settings().value(kulcs, False)
        if isinstance(ertek, bool):
            return ertek
        return str(ertek).strip().casefold() in ("true", "1", "yes")

    def _olvas_gyokeret(self) -> str:
        """A tárolt RENDSZERMAPPA-token, vagy üres sztring.

        ⚠️ Ismeretlen értékre nem kivétel, hanem üres: egy régi vagy kézzel
        átírt beállítás ne akadályozza meg az indulást. A `flat`/`all`/
        `watched` itt szándékosan üresnek számít — azokat a két kapcsoló
        tárolja (#2154), és két igazságforrás némán szétcsúszna."""
        ertek = self._get_settings().value(self._KULCS_VIEW_ROOT, "")
        token = str(ertek) if ertek is not None else ""
        return token if token in _RENDSZERMAPPAK else ""

    def _ir(self, kulcs: str, ertek: bool) -> None:
        self._get_settings().setValue(kulcs, bool(ertek))

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

    #: ⚠️ SZÁNDÉKOSAN nem `@Slot`: a figyelt mappák listája a PROGRAMTÓL
    #: jön (`application.py`), nem a felületről. Slotként a #1476 őre
    #: joggal jelezné, hogy felületről elérhetetlen vezérlő-tag.
    def setWatchedRoots(self, roots) -> None:
        """A figyelt mappák átvétele (#1407).

        Az „Egyszerűsített fanézet" ezekre az ágakra szűkíti a fát — az
        eredetiben a `SimplifiedHierarchy = 1` az `all` gyökeret
        `watched`-re cseréli (`0x0057517c`–`0x005751ec`)."""
        ujak = tuple(str(ut) for ut in roots or ())
        if ujak == self._watched_roots:
            return
        self._watched_roots = ujak
        if self._simplified:
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
        self._ir(self._KULCS_TREE_VIEW, self._tree_view)   # #2154
        #: #1407: a nézetmód kézi váltása elhagyja a rendszermappa-gyökeret
        #: — különben a menü pipája ott maradna egy mappán, amin már nem
        #: állunk.
        self._rendszer_gyokeret_elhagy()
        self.treeViewChanged.emit()
        self.viewRootChanged.emit()

    # -- egyszerűsített fanézet (`SimplifiedHierarchy`) ------------------

    @Property(bool, notify=simplifiedChanged)
    def simplified(self) -> bool:
        """Az „Egyszerűsített fanézet" (`eMenuView::ID_VIEW_WATCHED`)
        állapota.

        #1407: a fa HATÓKÖRE szűkül a figyelt mappák ágaira — az
        eredetiben a `SimplifiedHierarchy = 1` az `all` gyökeret
        `watched`-re cseréli (`0x0057517c`–`0x005751ec`). A szűkített
        ágakon belül az útvonal-tömörítés is fut, hogy a hosszú láncok
        olvashatók maradjanak.

        ⚠️ Ha a figyelt mappák listája üres (a vezérlő még nem kapta
        meg), a szűkítés ELMARAD: a felhasználó mappáit elrejteni
        rosszabb kimenet, mint a szűkítés hiánya.
        """
        return self._simplified

    # SZÁNDÉKOSAN nincs QML-hivatkozása (#1052): a menü a `toggleSimplified`-et
    # hívja, és AZ hívja ezt — a beállító ág tehát a felületről elérhető.
    @Slot(bool)
    def setSimplified(self, value: bool) -> None:
        if bool(value) == self._simplified:
            return
        self._simplified = bool(value)
        self._ir(self._KULCS_SIMPLIFIED, self._simplified)   # #2154
        self._rendszer_gyokeret_elhagy()   # #1407
        self.simplifiedChanged.emit()
        self.viewRootChanged.emit()
        self._rebuild()

    # -- mappa-borítók (#2049) ------------------------------------------

    @Property(bool, notify=albumThumbsChanged)
    def albumThumbs(self) -> bool:
        """„Indexképek megjelenítése a könyvtárban" — a fasorok ikonja
        helyett fotó-kupac.

        Az eredeti kulcsa `Preferences` ▸ `ShowAlbumThumbnails2`, alapértéke
        **0** (`0x00761870`), ezért nálunk is kikapcsolva indul.

        ⚠️ Ez a kapcsoló — az „Egyszerűsített fanézet"-hez hasonlóan —
        **nem marad meg** újraindításig: a `folder_hierarchy_controller`
        egyik kapcsolója sem ír `QSettings`-be. Ez meglévő hiányosság,
        nem ezé a jegyé.
        """
        return self._album_thumbs

    # SZÁNDÉKOSAN nincs közvetlen QML-hivatkozása: a menü a
    # `toggleAlbumThumbs`-t hívja, és AZ hívja ezt — ugyanaz a felállás,
    # mint a `setSimplified`-nél (#1052).
    @Slot(bool)
    def setAlbumThumbs(self, value: bool) -> None:
        if bool(value) == self._album_thumbs:
            return
        self._album_thumbs = bool(value)
        self._ir(self._KULCS_ALBUM_THUMBS, self._album_thumbs)   # #2154
        self.albumThumbsChanged.emit()

    @Slot()
    def toggleAlbumThumbs(self) -> None:
        self.setAlbumThumbs(not self._album_thumbs)

    # -- a hasáb GYÖKERE (#1407, spec 2.2 / 4.2 / 4.5/b / 4.6) -----------

    @Property(str, notify=viewRootChanged)
    def viewRoot(self) -> str:
        """A választott gyökér tokenje — a menü rádió-pipái ezt olvassák.

        A hat token közül **kettő valódi gyökér** (`flat`, `all`), egy az
        `all` szűkítése (`watched`), és három rendszermappa-ugrás
        (`mypics`, `mydocs`, `desktop`). Az utóbbi három a TELJES fán áll,
        mégis külön tokent tárol — az eredeti `[+0x2e0]`/`[+0x2f0]` rekesze
        is ezért kap rádiógomb-pipát a helyi menüben (spec 4.5/b).

        SZÁRMAZTATOTT érték: a `flat`/`all`/`watched` a két kapcsolóból
        jön, csak a rendszermappa-token él önálló mezőben."""
        if self._rendszer_gyoker:
            return self._rendszer_gyoker
        if not self._tree_view:
            return "flat"
        return "watched" if self._simplified else "all"

    @Property(str, notify=viewRootChanged)
    def rootLabel(self) -> str:
        """A hasáb fejlécének felirata a gyökér szerint (spec 4.2, 4.5/c).

        Pontosan KETTŐ rögzített erőforrás-szöveg van (`ViewRoot::AllFolders`
        és `ViewRoot::All`), és nem öt: a három rendszermappa a feloldott
        mappa SAJÁT nevét mutatja (`0x00575483  mov esi, eax`).

        ⚠️ A szöveg fordítását a QML `qsTr`-je adja; itt a kulcs-alakú angol
        szöveg áll, mert ez a vezérlő nem tölt be fordítást."""
        token = self.viewRoot
        if token == "flat":
            return "Default View"
        if token in ("all", "watched"):
            return "My Computer"
        ut = _rendszermappa(token)
        if not ut and token == "mypics":
            ut = _rendszermappa("mydocs")
        return os.path.basename(ut.rstrip(os.sep)) if ut else "My Computer"

    @Slot(str)
    def setViewRoot(self, token: str) -> None:
        """Gyökérváltás a mért szemantikával.

        A három rendszermappa-tétel **előbb a teljes fára vált**
        (`push "all"`), és csak utána oldja fel a mappát — ezért a sorrend
        itt sem cserélhető meg (`0x005753b2`, `0x0057540b`, `0x00575461`).

        Feloldhatatlan mappánál a natív kód önmagát hívja `"all"` gyökérrel
        (`0x005753bd`, `0x00575416`, `0x0057546c`), tehát a hibakezelés
        **visszaesés a Sajátgép-gyökérre**, nem hibaüzenet (spec 4.6).

        ⚠️ Egyik ág sem nyúl az „Egyszerűsített fanézet" kapcsolójához: az
        FÜGGETLEN, tartós beállítás (spec 3.), és bekapcsolva az `all`
        gyökeret `watched`-re cseréli (`0x0057517c`–`0x005751ec`). Ezért a
        „Sajátgép" tétel bekapcsolt egyszerűsítés mellett `watched`-et ad —
        ez a mért viselkedés, nem elnézés."""
        kert = str(token)
        if kert not in self._GYOKEREK:
            return

        if kert in _RENDSZERMAPPAK:
            # ELŐBB a teljes fa — a sorrend mért
            self.setTreeView(True)
            ut = _rendszermappa(kert)
            if not ut and kert == "mypics":
                #: `0x00996747  call 0x996230` — a Képek feloldó maga esik
                #: vissza a Dokumentumokra
                ut = _rendszermappa("mydocs")
            if not ut:
                #: spec 4.6: visszaesés a Sajátgép-gyökérre, ugrás nélkül
                self._rendszer_gyokeret_allit("")
                return
            self._rendszer_gyokeret_allit(kert)
            self.rootFolderRevealed.emit(ut)
            return

        self._rendszer_gyokeret_allit("")
        if kert == "flat":
            self.setTreeView(False)
        else:
            self.setTreeView(True)
            if kert == "watched" and not self._simplified:
                #: az „Egyszerűsített fanézet" tétele ugyanaz a kapcsoló
                self.setSimplified(True)

    def _rendszer_gyokeret_elhagy(self) -> None:
        """A rendszermappa-gyökér elhagyása — a két kapcsoló kézi váltásakor."""
        self._rendszer_gyokeret_allit("")

    def _rendszer_gyokeret_allit(self, token: str) -> None:
        if token == self._rendszer_gyoker:
            return
        self._rendszer_gyoker = token
        self._get_settings().setValue(self._KULCS_VIEW_ROOT, token)
        self._get_settings().sync()
        self.viewRootChanged.emit()

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
        return build_hierarchy(
            self._folders,
            simplified=self._simplified,
            watched_roots=self._watched_roots,
        )

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
