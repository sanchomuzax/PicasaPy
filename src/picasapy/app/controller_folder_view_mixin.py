"""A bal mappasáv rendezési és megjelenítési beállításai."""

from __future__ import annotations

from PySide6.QtCore import Property, Slot
from picasapy.index import open_index
from .collections import COLLECTIONS, DEFAULT_COLLAPSED, collection_setting_key
from .controller_signals import AppControllerSignalsMixin as _Signals

# A QML-ből választható bélyegképfeliratok.
_THUMB_CAPTION_MODES = ("none", "filename", "caption", "tags", "resolution")

# A bal oldali mappapanel határai (#322, #587, #2329).
FOLDER_PANE_WIDTH_DEFAULT = 240
FOLDER_PANE_WIDTH_MIN = 240
FOLDER_PANE_WIDTH_MAX = 4000

def _clamp_folder_pane_width(width: int) -> int:
    return max(FOLDER_PANE_WIDTH_MIN, min(FOLDER_PANE_WIDTH_MAX, width))

class FolderViewMixin:
    """A bal mappasáv rendezési és megjelenítési beállításai."""

    @Property(str, notify=_Signals.statusChanged)
    def folderSort(self):
        return self._get_settings().value("view/folderSort", "date")

    @Property(bool, notify=_Signals.statusChanged)
    def folderSortReverse(self):
        value = self._get_settings().value("view/folderSortReverse", "false")
        return value in (True, "true", "1")

    @Property(str, notify=_Signals.statusChanged)
    def paneSort(self):
        """A BAL HASÁB rendezése (#461/3) — a rácsétól FÜGGETLEN beállítás.

        Az eredeti Picasában a bal panel saját jobbklikk-menüje
        (`AlbumList`, ld. `ui-audit-context-menus.md` A.2) tartalmazta a
        „Rendezés dátum / név / méret / legutóbbi változtatás alapján"
        tételeket — vagyis az a HASÁBOT rendezte. A Mappa ▸ Rendezés ettől
        külön, a RÁCSOT állítja (#321). Két parancs, két cél."""
        return self._get_settings().value("view/paneSort", "date")

    @Property(bool, notify=_Signals.statusChanged)
    def paneSortReverse(self):
        value = self._get_settings().value("view/paneSortReverse", "false")
        return value in (True, "true", "1")

    @Slot(str)
    def setPaneSort(self, mode: str) -> None:
        """A bal hasáb rendezésének váltása (#461/3)."""
        if mode not in ("date", "changed", "size", "name"):
            return
        self._get_settings().setValue("view/paneSort", mode)
        self._reload_folders()

    @Slot()
    def togglePaneSortReverse(self) -> None:
        self._get_settings().setValue(
            "view/paneSortReverse", not self.paneSortReverse
        )
        self._reload_folders()

    @Slot(str)
    def setFolderSort(self, mode: str) -> None:
        """A MAPPA-BLOKKOK sorrendje a rácson (Mappa ▸ Rendezés):
        date / changed / size / name.

        ⚠️ #1759 — MÉRVE, mert a korábbi leírás félrevezetett. Ez a
        beállítás azt dönti el, milyen sorrendben követik egymást a
        MAPPÁK a rácson (`_feed_records` → `folder_order`). Nem rendezi
        át a mappán BELÜLI képeket, és nem a bal hasáb sorrendje.

        Három, egymástól FÜGGETLEN rendezés él a programban:

        | beállítás | mit rendez | honnan |
        |---|---|---|
        | `folderSort` (ez) | a mappa-blokkokat a RÁCSON | Mappa ▸ Rendezés |
        | kézi sorrend (#4890) | a mappa KÉPEIT, mappánként | mappa-jobbklikk |
        | `paneSort` (#461/3) | a BAL HASÁB sorait | a hasáb helyi menüje |

        A #1595 kutatása épp azért vont le téves következtetést, mert a
        korábbi docstring („a RÁCS rendezése") alapján úgy tűnt, hogy ez
        és a kézi sorrend ugyanaz kétféle felirattal — az összevonás
        egy működő szempontot („legutóbbi változtatások") vett volna el.

        #1454: a Nézet ▸ Mappanézet almenü — ahonnan ez korábban szintén
        hívható volt — nem rendez, hanem a bal hasáb szerkezetét állítja.
        """
        if mode not in ("date", "changed", "size", "name"):
            return
        self._get_settings().setValue("view/folderSort", mode)
        self._refresh_view()

    @Slot(int)
    def setThumbCellSize(self, cella_px: int) -> None:  # noqa: N802 — QML-stílus
        """A rács cellamérete → a bélyegkép-SZINT (#598).

        A QML a csúszka fokozatát adja át; a szintet a bélyegkép-tár dönti
        el (`72 · 144 · a maximum`). A felső szinten `None` megy a modellbe,
        hogy az URL bájtra a #598 előtti legyen — a meglévő gyorstár így
        érvényes marad.

        Egy szint több csúszka-fokozatot fed le, ezért a húzás nem kér újra
        minden bélyegképet, csak a szinthatár átlépése."""
        model = getattr(self, "photos", None)
        if model is None or cella_px <= 0:
            return
        szint = self._provider.level_for(cella_px)
        model.set_thumb_level(None if szint >= self._provider.top_level else szint)

    @Slot(int, int, bool, result=int)
    def prefetchThumbnails(  # noqa: N802 — QML-stílus
        self, start_row: int, count: int, reverse: bool = False
    ) -> int:
        """A rács görgetési irányában következő bélyegképek előtöltése (#4289).

        A modell URL-jeit használjuk, hogy a bélyegképszintet, a vágást és
        a többi URL-címkét ugyanaz a meglévő render-út kapja, mint a látható
        celláknál. A provider a munkákat alacsony prioritással sorolja be.
        """
        photos = self._photos.photos
        if start_row < 0 or count <= 0 or start_row >= len(photos):
            return 0
        stop = min(len(photos), start_row + count)
        rows = range(stop - 1, start_row - 1, -1) if reverse else range(
            start_row, stop
        )
        prefix = "image://thumbs/"
        photo_ids = []
        for row in rows:
            url = self._photos.thumbUrlAt(row)
            if url.startswith(prefix):
                photo_ids.append(url[len(prefix):])
        return self._provider.prefetch_images(photo_ids)

    @Slot(result=bool)
    def backgroundWorkRunning(self) -> bool:  # noqa: N802 — QML-stílus
        """Fut-e BÁRMELYIK vezérlő háttérmunkája (#671).

        A kilépés kérdéséhez kell (`Main.qml` `kilepes()`): az eredeti Picasa
        a kilépést nem blokkolja, de ha folyamatban van munka, RÁKÉRDEZ
        („Uploads are in progress. Would you like to exit now?", két gombbal).

        ⚠️ SZÁNDÉKOSAN a globális nyilvántartást kérdezi
        (`running_background_workers`), nem a saját mixinjét: a futó munka
        lehet a webexport, a kötegelt effekt vagy az arc-szkennelés
        vezérlőjében is, és a felhasználó számára az mind „még dolgozik".
        """
        from .worker_thread import running_background_workers

        return bool(running_background_workers())

    @Slot()
    def toggleFolderSortReverse(self) -> None:
        self._get_settings().setValue(
            "view/folderSortReverse", not self.folderSortReverse
        )
        self._reload_folders()
        self._refresh_view()  # a feed sorrendje követi a hasábot (#64)

    def _reload_folders(self) -> None:
        # #321 + #461/3: a bal hasábnak SAJÁT rendezése van — a Mappa ▸
        # Rendezés (folderSort) továbbra sem nyúl hozzá, azt csak a rács
        # követi. A hasáb sorrendjét a saját jobbklikk-menüje állítja
        # (`paneSort`), ahogy az eredeti Picasa `AlbumList` menüje tette.
        with open_index(self._db_path) as conn:
            self._folders.load(
                conn,
                self.paneSort,
                self.paneSortReverse,
                # #1637: a rejtett mappákat ugyanaz a kapcsoló hozza
                # vissza, ami a rejtett fotókat — nem külön beállítás
                include_hidden=self.showHidden,
                # #2031: a PROJEKT-mappák csak a Projektek alatt látszanak
                # (a `P2category` kizáró, #1033). Az útvonalak MÁR itt
                # vannak — a hasáb-gyűjtemények betöltése cache-eli őket —,
                # tehát nem kell újabb `.picasa.ini`-söprés.
                exclude_paths=[m.path for m in self._project_folders],
            )
        self.statusChanged.emit()

    # -- gyűjtemények a bal hasábon (#320) -----------------------------------

    @Slot(str, result=bool)
    def isCollectionCollapsed(self, name: str) -> bool:
        """Csukva van-e a gyűjtemény fejléce (perzisztens)."""
        if name not in COLLECTIONS:
            return False
        stored = self._get_settings().value(
            collection_setting_key(name), DEFAULT_COLLAPSED[name]
        )
        return stored in (True, "true", "1", 1)

    @Slot(str, bool)
    def setCollectionCollapsed(self, name: str, collapsed: bool) -> None:
        """A gyűjtemény-fejléc csukása/nyitása — ismeretlen nevet kihagy."""
        if name not in COLLECTIONS:
            return
        self._get_settings().setValue(collection_setting_key(name), bool(collapsed))
        self.statusChanged.emit()

    # -- bal oldali mappapanel szélessége (#322) -----------------------------

    @Property(int, notify=_Signals.statusChanged)
    def folderPaneWidth(self):
        """A mappapanel szélessége képpontban — perzisztens, határok közé
        szorítva. Olvashatatlan (kézzel elrontott) érték esetén az
        alapértelmezés jön vissza, nem hiba."""
        raw = self._get_settings().value(
            "view/folderPaneWidth", FOLDER_PANE_WIDTH_DEFAULT
        )
        try:
            width = int(raw)
        except (TypeError, ValueError):
            return FOLDER_PANE_WIDTH_DEFAULT
        return _clamp_folder_pane_width(width)

    @Slot(int)
    def setFolderPaneWidth(self, width: int) -> None:
        """A húzással beállított szélesség mentése (a QML a SplitView
        fogantyújának elengedésekor hívja)."""
        try:
            clamped = _clamp_folder_pane_width(int(width))
        except (TypeError, ValueError):
            return
        self._get_settings().setValue("view/folderPaneWidth", clamped)
        self.statusChanged.emit()

    @Property(str, notify=_Signals.statusChanged)
    def thumbCaptionMode(self):
        """Indexkép-felirat mód (Nézet → Indexkép felirata) — perzisztens."""
        return self._thumb_caption_mode

    @Slot(str)
    def setThumbCaptionMode(self, mode: str) -> None:
        """Indexkép-felirat mód beállítása (Nézet menü) — 5 kizáró opció."""
        if mode not in _THUMB_CAPTION_MODES:
            return
        self._thumb_caption_mode = mode
        self._get_settings().setValue("view/thumbCaption", mode)
        self.statusChanged.emit()

    # -- felirat-sáv láthatósága (#1816) -------------------------------------

    @Property(bool, notify=_Signals.statusChanged)
    def captionVisible(self):
        """Látszik-e a nagy kép alatti felirat-sáv.

        #1816: az eredetiben ez TARTÓS állapot, nem pillanatnyi kapcsoló —
        a `Preferences\\LastCaptionButton` őrzi, és a főablak-építő
        (`0x0040bf70`) induláskor visszaállítja. Ha egyszer elrejtetted, a
        Picasa legközelebb is elrejtve indul.

        Alapból LÁTSZIK: a felirat a Picasa egyik fő fogalma, az elrejtés a
        felhasználó külön döntése."""
        value = self._get_settings().value("view/captionVisible", "true")
        return value in (True, "true", "1")

    def setCaptionVisible(self, visible: bool) -> None:
        """A felirat-sáv láthatóságának beállítása.

        SZÁNDÉKOSAN nem `@Slot`: a QML-nek csak a BILLENTŐ-t kínáljuk (az
        eredeti `captionbutton` megfelelője). Egy felületről elérhetetlen
        slot a képesség-őr szerint szakadás — és joggal: néma ígéret."""
        self._get_settings().setValue("view/captionVisible", bool(visible))
        self.statusChanged.emit()

    @Slot()
    def toggleCaptionVisible(self) -> None:
        """A `captionbutton` („Show/Hide Caption") viselkedése."""
        self.setCaptionVisible(not self.captionVisible)
