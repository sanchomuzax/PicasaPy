"""Az importforrás-vezérlő beállításai és előnézeti állapota."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QSettings, QStandardPaths, QUrl, Signal, Slot
from picasapy.importsource import (
    ATMERETEZES_EREDETI,
    ATMERETEZES_OPCIOK,
    NAMING_BY_DATE,
    NAMING_MANUAL,
    NAMING_TODAY,
)


# a soronkénti importálási hibákból ennyit mutatunk a UI-nak (az
# `ExportMixin._EXPORT_FAILED_DETAILS_LIMIT` mintája) — tömeges hibánál a
# teljes lista inkább zavaró, mint hasznos
_IMPORT_FAILED_DETAILS_LIMIT = 5

# -- #441: "After Copying:" HÁROM állapota -----------------------------
AFTER_COPY_LEAVE = "leave"  # "Leave card alone" (alapértelmezés)
AFTER_COPY_DELETE_COPIED = "delete_copied"  # "Delete only copied photos"
AFTER_COPY_DELETE_ALL = "delete_all"  # "Delete everything on card"

_VALID_NAMING_MODES = (NAMING_MANUAL, NAMING_BY_DATE, NAMING_TODAY)
_VALID_AFTER_COPYING = (AFTER_COPY_LEAVE, AFTER_COPY_DELETE_COPIED, AFTER_COPY_DELETE_ALL)

# #441: "Exclude Duplicates" - QSettings-kulcs (a jegy szövege szerint
# "autoexclude", a Picasa eredeti `options.fen`/`General` lapjának
# megfelelő beállítás-nevét követve, ld. `docs/specs/picasa-fen-dialogs.md`).
# #5473: az eredeti alapértéke 1 (bekapcsolva); ez érvényes, ha a kulcs még
# nincs mentve. A mentett érték mindig felülírja.
AUTOEXCLUDE_SETTINGS_KEY = "import/autoexclude"
AUTOEXCLUDE_DEFAULT = "true"

# #441: a forrásválasztó legördülőjében az eredeti a KORÁBBI importok
# listáját kínálta (`LastImport…`) a „Choose…" mellett — így a rendszeresen
# használt kártya/mappa egy kattintással újra elérhető. A lista a
# legutóbbi elöl, ismétlés nélkül; ennél többet nem tartunk meg, hogy a
# legördülő ne hízzon el.
RECENT_SOURCES_SETTINGS_KEY = "import/recentsources"
MAX_RECENT_SOURCES = 8

# #1785: az eredeti a CÉLMAPPÁKAT is megjegyzi — `Preferences\LastImport%x`
# indexelt kulcsokkal (0x00516180) —, és háromszakaszos menüben kínálja:
# korábbi importok · alapértelmezett hely · „Choose…". Nálunk a forráséval
# AZONOS legördülő adja ugyanezt; a három szakaszból a „Tallózás…" külön
# gombként már megvolt.
#
# A megőrzött célok maximális száma az eredetiben NINCS kimérve; nyolcat
# tartunk, ugyanannyit, mint a forrásokból — a legördülő így nem hízik el.
RECENT_DESTINATIONS_SETTINGS_KEY = "import/recentdestinations"
MAX_RECENT_DESTINATIONS = 8
DEFAULT_DESTINATION_SETTINGS_KEY = "import/defaultdestination"

# #1555: az importálás átméretezési beállítása. ⚠️ KÉPPONT-értéket
# tárolunk, nem sorszámot — ahogy az eredeti is (egyetlen egész mező,
# `[+0x74c]`); ettől egy új méret felvétele nem töri el a meglévő
# beállításokat. A `0` jelentése „EREDETI MÉRET", nem „nincs beállítva".
RESIZE_SETTINGS_KEY = "import/resizeLimit"

def _controller_module():
    """A régi modulon keresztül feloldott függőségek a monkeypatch-célpontokhoz."""
    from . import import_source_controller

    return import_source_controller



class ImportSourceControllerStateMixin:
    """Beállítások, korábbi célok és a kiválasztott forrás állapota."""

    autoExcludeChanged = Signal()
    mediaFilterChanged = Signal()
    mountedSourcesChanged = Signal()
    recentSourcesChanged = Signal()
    recentDestinationsChanged = Signal()
    defaultDestinationChanged = Signal()
    resizeLimitChanged = Signal()

    def _get_settings(self) -> QSettings:
        if self._settings is None:
            self._settings = _controller_module().QSettings("PicasaPy", "PicasaPy")
        return self._settings

    def _read_auto_exclude(self) -> bool:
        value = self._get_settings().value(
            AUTOEXCLUDE_SETTINGS_KEY, AUTOEXCLUDE_DEFAULT
        )
        if isinstance(value, bool):
            return value
        return str(value).strip().lower() in ("true", "1")

    # -- #441: "Exclude Duplicates" ----------------------------------------

    @Property(bool, notify=autoExcludeChanged)
    def autoExclude(self) -> bool:  # noqa: N802 — QML property-konvenció
        """"Exclude Duplicates" — "Exclude photos that are already
        imported into Picasa"."""
        return self._auto_exclude

    @Property("QVariant", notify=recentSourcesChanged)
    def recentSources(self):  # noqa: N802 — QML property-konvenció
        """A korábbi import-források (#441), a legutóbbi elöl.

        A `LastImport…` legördülő adata: a felhasználó egy kattintással
        visszatérhet a rendszeresen használt kártyához/mappához."""
        return self._read_recent_sources()

    @Property("QVariant", notify=mountedSourcesChanged)
    def mountedSources(self):  # noqa: N802 — QML property-konvenció
        """A jelenleg elérhető, cserélhető importforrások."""
        return [dict(source) for source in self._mounted_sources]

    @Slot()
    def refreshMountedSources(self) -> None:  # noqa: N802 — QML property-konvenció
        """Frissíti a csatolt kártyák és USB-meghajtók listáját."""
        sources = _controller_module().discover_mounted_sources()
        if sources == self._mounted_sources:
            return
        self._mounted_sources = sources
        self.mountedSourcesChanged.emit()

    def _read_recent_sources(self) -> list[str]:
        stored = self._get_settings().value(RECENT_SOURCES_SETTINGS_KEY, [])
        if isinstance(stored, str):
            stored = [stored] if stored else []
        return [str(item) for item in (stored or [])]

    def _remember_source(self, folder: str) -> None:
        """A most beolvasott forrás a lista ELEJÉRE; ismétlés nélkül."""
        if not folder:
            return
        recent = [item for item in self._read_recent_sources() if item != folder]
        recent.insert(0, folder)
        self._get_settings().setValue(
            RECENT_SOURCES_SETTINGS_KEY, recent[:MAX_RECENT_SOURCES]
        )
        self.recentSourcesChanged.emit()

    # -- #1785: korábbi CÉLMAPPÁK -------------------------------------------

    @Property("QVariant", notify=recentDestinationsChanged)
    def recentDestinations(self):  # noqa: N802 — QML property-konvenció
        """A korábbi import-célmappák, a legutóbbi elöl (#1785).

        ⚠️ A MÁR NEM LÉTEZŐ mappa KIMARAD a listából. A döntést a jegy a
        megvalósítóra bízta („kihagyjuk vagy jelöljük"); a kihagyás mellett
        az szól, hogy a legördülőben minden tétel egy KATTINTHATÓ cél — egy
        letűnt kártyát felkínálni és hibával elutasítani rosszabb, mint meg
        sem mutatni. A tárolt lista nem csonkul: ha a mappa visszakerül (pl.
        felcsatolt hálózati meghajtó), magától újra megjelenik.
        """
        return [
            item for item in self._read_recent_destinations()
            if Path(item).is_dir()
        ]

    @Property(str, notify=defaultDestinationChanged)
    def defaultDestination(self) -> str:  # noqa: N802
        """A felhasználó alapértelmezett importcélja.

        Első használatkor közvetlenül a képek rendszermappája (a
        `QStandardPaths.PicturesLocation`), vagy ennek hiányában a saját
        mappa. A választás a `QSettings`-be kerül, az import párbeszéd ezt
        ajánlja fel induló célként."""
        tarolt = self._get_settings().value(DEFAULT_DESTINATION_SETTINGS_KEY, "")
        if tarolt:
            return str(tarolt)
        kepek = _controller_module().QStandardPaths.writableLocation(
            QStandardPaths.StandardLocation.PicturesLocation
        )
        if not kepek:
            kepek = str(Path.home())
        return str(Path(kepek))

    @Property(QUrl, notify=defaultDestinationChanged)
    def defaultDestinationUrl(self) -> QUrl:  # noqa: N802
        """A beállított mappa `FolderDialog`-hoz alakított URL-je."""
        return _controller_module().to_file_url(self.defaultDestination)

    @Slot(str)
    def setDefaultDestination(self, path: str) -> None:  # noqa: N802
        """Elmenti a létező, felhasználó által kiválasztott importcélt."""
        local_path = _controller_module().to_local_path(path)
        if not local_path:
            return
        folder = Path(local_path).expanduser()
        try:
            if not folder.is_dir():
                return
            normalized = str(folder.resolve())
        except OSError:
            return
        if normalized == self.defaultDestination:
            return
        self._get_settings().setValue(DEFAULT_DESTINATION_SETTINGS_KEY, normalized)
        self.defaultDestinationChanged.emit()

    def _read_recent_destinations(self) -> list[str]:
        stored = self._get_settings().value(
            RECENT_DESTINATIONS_SETTINGS_KEY, []
        )
        if isinstance(stored, str):
            stored = [stored] if stored else []
        return [str(item) for item in (stored or [])]

    def _remember_destination(self, folder: str) -> None:
        """A most használt cél a lista ELEJÉRE; ismétlés nélkül.

        A forrás mintája (`_remember_source`), egy különbséggel: a célt a
        SIKERES másolás után jegyezzük meg, mert a cél létezését csak
        akkor tudjuk."""
        if not folder:
            return
        recent = [
            item for item in self._read_recent_destinations() if item != folder
        ]
        recent.insert(0, folder)
        self._get_settings().setValue(
            RECENT_DESTINATIONS_SETTINGS_KEY, recent[:MAX_RECENT_DESTINATIONS]
        )
        self.recentDestinationsChanged.emit()

    # -- #1555: átméretezés importáláskor ------------------------------------

    @Property("QVariant", notify=resizeLimitChanged)
    def resizeOptions(self):  # noqa: N802 — QML property-konvenció
        """Az öt mért méret-opció, KÉPPONTBAN (`0` = eredeti méret)."""
        return list(ATMERETEZES_OPCIOK)

    @Property(int, notify=resizeLimitChanged)
    def resizeLimit(self) -> int:  # noqa: N802 — QML property-konvenció
        """A megjegyzett átméretezési határ képpontban; `0` = eredeti.

        Az ISMERETLEN tárolt érték (kézzel írt beállításfájl, jövőbeli
        verzió) az EREDETI méretre esik vissza: inkább ne méretezzünk át,
        mint hogy egy félreértett számra vágjunk le képeket."""
        tarolt = self._get_settings().value(RESIZE_SETTINGS_KEY, 0)
        try:
            ertek = int(tarolt)
        except (TypeError, ValueError):
            return ATMERETEZES_EREDETI
        return ertek if ertek in ATMERETEZES_OPCIOK else ATMERETEZES_EREDETI

    @Slot(int)
    def setResizeLimit(self, value: int) -> None:  # noqa: N802
        """A méret-opció választása. Ismeretlen értékre nem ír."""
        try:
            ertek = int(value)
        except (TypeError, ValueError):
            return
        if ertek not in ATMERETEZES_OPCIOK:
            return
        self._get_settings().setValue(RESIZE_SETTINGS_KEY, ertek)
        self.resizeLimitChanged.emit()

    @Property(str, notify=mediaFilterChanged)
    def mediaFilter(self) -> str:  # noqa: N802 — QML property-konvenció
        """A forrás-beolvasás fájltípus-szűrője (#441) — az eredeti
        tallózó három fokozatának megfelelője."""
        return self._media_filter

    @Slot(str)
    def setMediaFilter(self, value: str) -> None:  # noqa: N802
        """A szűrő beállítása; a következő beolvasásra érvényes."""
        if value == self._media_filter:
            return
        self._media_filter = value
        self.mediaFilterChanged.emit()

    @Slot(bool)
    def setAutoExclude(self, value: bool) -> None:  # noqa: N802
        value = bool(value)
        if value == self._auto_exclude:
            return
        self._auto_exclude = value
        self._get_settings().setValue(
            AUTOEXCLUDE_SETTINGS_KEY, "true" if value else "false"
        )
        if value:
            self._excluded_paths |= {str(path) for path in self._duplicate_paths}
        else:
            self._excluded_paths -= {str(path) for path in self._duplicate_paths}
        self.autoExcludeChanged.emit()
        self.selectionChanged.emit(self._preview_items())

    # -- #441: egyenkénti válogatás -----------------------------------------

    # -- #441: forgatás és csillagozás MÁR AZ IMPORT ELŐTT ------------------
    #
    # Az eredeti import-képernyőn az előnézeti képen ott volt a „Rotate
    # Right"/„Rotate Left" gomb és a csillagozás (`startoggle`) — a
    # felhasználó még a bemásolás előtt kiegyenesíthette és megjelölhette a
    # képeket. Nálunk ugyanez: az állapotot forrás-útvonalanként tartjuk, és
    # a MÁSOLAT `.picasa.ini`-jébe írjuk (nem a kártyán lévő eredetibe —
    # az érintetlen marad, ahogy a „Leave card alone" ág elvárja).

    @Slot(str, int)
    def rotateFile(self, path: str, delta: int) -> None:  # noqa: N802
        """Az adott jelölt forgatása negyed fordulatokkal (+1 jobbra, −1
        balra). Az érték 0..3 között körbeér; 0 = nincs forgatás."""
        if path not in {str(c.path) for c in self._candidates}:
            return
        self._rotations[path] = (self._rotations.get(path, 0) + int(delta)) % 4
        self.selectionChanged.emit(self._preview_items())

    @Slot(str)
    def toggleStar(self, path: str) -> None:  # noqa: N802
        """Csillagozás ki/be az adott jelöltre (`startoggle`)."""
        if path not in {str(c.path) for c in self._candidates}:
            return
        if path in self._starred:
            self._starred.discard(path)
        else:
            self._starred.add(path)
        self.selectionChanged.emit(self._preview_items())

    def _mark_imported(self, target: Path, source_path: str) -> None:
        """A jelölt import ELŐTT beállított forgatása/csillaga a másolatra."""
        _controller_module()._mark_imported_ini(
            target,
            self._rotations.get(source_path, 0),
            source_path in self._starred,
        )

    @Slot(str)
    def excludeFile(self, path: str) -> None:
        self._excluded_paths.add(path)
        self.selectionChanged.emit(self._preview_items())

    @Slot(str)
    def includeFile(self, path: str) -> None:
        self._excluded_paths.discard(path)
        self.selectionChanged.emit(self._preview_items())

    @Slot()
    def excludeAll(self) -> None:  # noqa: N802
        self._excluded_paths = {str(candidate.path) for candidate in self._candidates}
        self.selectionChanged.emit(self._preview_items())

    @Slot()
    def includeAll(self) -> None:  # noqa: N802
        self._excluded_paths.clear()
        self.selectionChanged.emit(self._preview_items())

    def _preview_items(self) -> list[dict]:
        """A jelenlegi jelöltlista QML-nek adható alakja — a
        `sourceScanFinished` és a `selectionChanged` is ezt küldi, hogy a
        QML-oldal egyetlen kódúton frissítse a rácsot."""
        items = []
        for index, candidate in enumerate(self._candidates):
            path_text = str(candidate.path)
            items.append(
                {
                    "path": path_text,
                    "thumbUrl": _controller_module()._thumb_url(-(index + 1))
                    if self._provider is not None
                    else "",
                    "duplicate": candidate.path in self._duplicate_paths,
                    "excluded": path_text in self._excluded_paths,
                    # #441: import előtti forgatás/csillagozás
                    "rotation": self._rotations.get(path_text, 0),
                    "starred": path_text in self._starred,
                }
            )
        return items
