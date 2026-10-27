"""A főablak QML-állapotának lekérdezhető nézetei."""

from __future__ import annotations

from PySide6.QtCore import Property, Slot
from picasapy.ini import STAR_ALBUM_TOKEN
from .search_results import groups_to_qml
from .controller_signals import AppControllerSignalsMixin as _Signals

class AppControllerStateMixin:
    """A főablak QML-állapotának lekérdezhető nézetei."""

    def begin_quick_view(self, paths) -> bool:
        """Kizárólag a parancssorban megadott képeket tölti a viewerbe."""
        if self._quick_view_active:
            return False
        from .quick_view import quick_view_records

        try:
            records = quick_view_records(tuple(str(path) for path in paths or ()))
        except OSError:
            return False
        if not records:
            return False

        self._quick_view_photo_ids = tuple(str(record.id) for record in records)
        self._provider.register_additional_photos(records)
        self._photos.set_linear_navigation(True)
        self._photos.set_photos(records)
        self._current_folder = ""
        self._view_mode = ("quick", "")
        self._quick_view_active = True
        self.quickViewChanged.emit()
        return True

    @Slot()
    def returnToLibraryFromQuickView(self) -> None:  # noqa: N802 — QML-slot-stílus
        """Lezárja az ideiglenes listát, majd elindítja a rendes könyvtárat."""
        if not self._quick_view_active:
            return
        self._provider.unregister_additional_photos(self._quick_view_photo_ids)
        self._quick_view_photo_ids = ()
        self._photos.set_linear_navigation(False)
        self._photos.set_photos(())
        self._current_folder = ""
        self._view_mode = ("folder", "")
        self._quick_view_active = False
        self.quickViewChanged.emit()
        self.start()

    @Property(list, notify=_Signals.albumsChanged)
    def albums(self):
        """Albumlista a bal hasábnak (#9): {token, name, count} elemek —
        LISTA, nem tuple (#232, a QML-ben a tuple nem tömb). A névtelen
        albumnak is van megjelenítendő neve (a token rövidített alakja),
        hogy ne maradjon üres sor a hasábon."""
        return list(self._albums)

    @Property(str, notify=_Signals.statusChanged)
    def currentAlbumToken(self):
        """Az aktív album token-je (#9) — a bal hasáb kijelöléséhez."""
        mode, param = self._view_mode
        if mode == "starred_album":
            return STAR_ALBUM_TOKEN
        return param if mode == "album" else ""

    @Property(str, notify=_Signals.statusChanged)
    def statusText(self):
        return self._status

    @Property(str, notify=_Signals.statusChanged)
    def currentFolder(self):
        return self._current_folder

    @Property(str, notify=_Signals.statusChanged)
    def folderDateText(self):
        """A mappa-fejléc dátumsora (a legkorábbi felvétel hosszú dátuma)."""
        return self._folder_date

    @Property(str, notify=_Signals.statusChanged)
    def folderDescription(self):
        """A mappa leírása — Picasa-kompatibilis: `[Picasa]/description`
        kulcs a mappa `.picasa.ini`-jében."""
        return self._folder_description

    @Property(bool, notify=_Signals.statusChanged)
    def searchActive(self):
        """Aktív-e a keresés (#7): bal paneli sor + rács-csoportosítás."""
        return self._view_mode[0] in ("search", "search-folder")

    @Property(str, notify=_Signals.statusChanged)
    def searchQuery(self):
        mode, param = self._view_mode
        if mode == "search":
            return param
        if mode == "search-folder":
            return param[0]
        return ""

    @Property(int, notify=_Signals.statusChanged)
    def searchResultCount(self):
        """Az ÖSSZES találat (#7) — mappára szűkítve is, nem a részhalmaz."""
        return self._search_result_count

    @Property(list, notify=_Signals.statusChanged)
    def searchGroups(self):
        """A jelenleg látszó fotók mappánkénti csoportjai QML-nek (#7)."""
        return groups_to_qml(self._search_groups)

    @Property(bool, notify=_Signals.statusChanged)
    def filterActive(self):
        return self._filter_active

    @Property(str, notify=_Signals.statusChanged)
    def viewModeName(self):
        """A jelenlegi szűrt nézet neve (`folder` · `starred` · `videos` ·
        `album` · `search`…).

        #1830: a szűrő-gombok ebből tudják, hogy ŐK vannak-e bekapcsolva.
        A `filterActive` erre nem elég: az csak azt mondja, hogy szűrünk,
        azt nem, hogy MIVEL — két szűrő-gomb egyszerre látszana aktívnak."""
        return self._view_mode[0]

    @Property(bool, notify=_Signals.statusChanged)
    def canSaveSearch(self):
        """Menthető-e a jelenlegi nézet albumként (#1405) — a mag a
        `PhotoOpsMixin._mentheto_kereses`, a jelzés viszont itt lakik.

        A megerősítés küszöbéhez a felület a MÁR MEGLÉVŐ
        `searchResultCount`-ot olvassa (#7: az ÖSSZES találat, mappára
        szűkítve is) — nem építünk mellé másodikat."""
        return self._mentheto_kereses()

    @Property(str, notify=_Signals.statusChanged)
    def filterStatusText(self):
        """A zöld eredménysáv szövege (Picasa-minta)."""
        return self._filter_status

    @Property("QVariantList", notify=_Signals.feedChanged)
    def feedGroups(self):
        """A rács-feed mappa-csoportjai (#64): {path, name, start, count,
        dateText} — a QML ebből rajzol mappa-fejlécet és képfolyamot."""
        return [dict(group) for group in self._feed_groups]

    @Property(list, notify=_Signals.statusChanged)
    def watchedFolders(self):
        return list(self._roots)

    @Property(list, notify=_Signals.statusChanged)
    def faceExcludedFolders(self):
        """Az arcfelismerésből kizárt gyökér-mappák (#449) — a
        `FolderStatePanel.qml` ebből számolja (ős-mappákra is kiterjedő
        egyezéssel) a jelölőnégyzet állapotát, a `watchedFolders` mintáját
        követve."""
        return list(self._face_excluded_roots)
