"""Felhasználói egyéni gyűjtemények — controller-szelet (#320, #4589).

Mixin-osztály (a `library_controller.LibraryMixin` és társai mintájára): a
végleges `AppController` örökli majd (a bekötés — az öröklés-lista bővítése
a `controller.py`-ban — forró fájl, az integrátor dolga, ld. issue).

A gyűjteménynevek és a csukott állapot QSettings-ben élnek. A mappák
besorolása a `.picasa.ini` `[Picasa] P2category` kulcsából olvasódik, és az
írás/migráció az `ini/` csomag API-ján halad át."""

from __future__ import annotations

import logging
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.ini import (
    FOLDERS_ON_DISK_CATEGORY,
    is_custom_collection_category,
    update_document,
    with_folder_category,
)
from picasapy.scanner import PICASA_INI_NAME

from .custom_collections import (
    CUSTOM_COLLECTIONS_SETTING_KEY,
    CustomCollection,
    closed_collection_folders,
    create_collection,
    delete_collection,
    merge_custom_collections,
    parse_custom_collections,
    rename_collection,
    serialize_custom_collections,
    set_collection_closed,
    validate_collection_name,
)

logger = logging.getLogger(__name__)


class CustomCollectionsMixin:
    """Egyéni gyűjtemények: létrehozás, átnevezés, törlés, mappa-áthelyezés."""

    customCollectionsChanged = Signal()

    @Property("QVariant", notify=customCollectionsChanged)
    def customCollections(self) -> list[dict]:
        """A gyűjtemények QML-nek adott alakja: `[{name, folders, closed}, ...]` —
        mindig `list`/`dict` (a projekt szabálya, sosem `tuple`)."""
        return [
            {"name": c.name, "folders": list(c.folders), "closed": c.closed}
            for c in self._load_custom_collections()
        ]

    def _init_custom_collections(self) -> None:
        """A konstruktorból hívandó; átveszi a korábbi QSettings-tagságot."""
        if hasattr(self, "_custom_collection_categories"):
            return
        self._custom_collection_categories: dict[str, tuple[str, ...]] = {}
        self._pending_custom_category_paths: dict[str, str] = {}
        self._migrate_legacy_collection_folders()

    def _apply_custom_collection_folders(
        self, category_folders: tuple[tuple[str, tuple[str, ...]], ...]
    ) -> None:
        """Az index egyetlen ini-söprését átveszi, a friss írásokat megőrzi."""
        categories = {name: list(folders) for name, folders in category_folders}
        for folder, category in self._pending_custom_category_paths.items():
            for paths in categories.values():
                while folder in paths:
                    paths.remove(folder)
            if is_custom_collection_category(category):
                categories.setdefault(category, []).append(folder)
        self._custom_collection_categories = {
            name: tuple(sorted(set(folders), key=str.casefold))
            for name, folders in categories.items()
            if folders
        }
        self._pending_custom_category_paths.clear()
        self.customCollectionsChanged.emit()

    def _load_custom_collections(self) -> tuple[CustomCollection, ...]:
        self._init_custom_collections()
        raw = self._get_settings().value(CUSTOM_COLLECTIONS_SETTING_KEY)
        return merge_custom_collections(
            parse_custom_collections(raw),
            tuple(self._custom_collection_categories.items()),
        )

    def _save_custom_collections(
        self, collections: tuple[CustomCollection, ...]
    ) -> None:
        # A tagság az ini-ben él; a beállításban csak a nevek és a csukott
        # állapot marad. A korábbi JSON-alakot a migráció külön kezeli.
        definitions = tuple(
            CustomCollection(name=c.name, closed=c.closed) for c in collections
        )
        self._get_settings().setValue(
            CUSTOM_COLLECTIONS_SETTING_KEY, serialize_custom_collections(definitions)
        )
        self._get_settings().sync()
        self.customCollectionsChanged.emit()

    def _migrate_legacy_collection_folders(self) -> None:
        """A régi QSettings-tagságokat egyszer az ini-fájlokba írja át.

        A sikeres utak kikerülnek a régi JSON-ból; írási hiba esetén a régi
        tagság megmarad tartaléknak, és a következő betöltés újrapróbálja.
        Már nem létező mappát nem tartunk meg a gyűjteményben.
        """
        settings = self._get_settings()
        current = parse_custom_collections(
            settings.value(CUSTOM_COLLECTIONS_SETTING_KEY)
        )
        if not any(collection.folders for collection in current):
            return

        migrated: list[CustomCollection] = []
        for collection in current:
            failed_paths: list[str] = []
            for folder in collection.folders:
                if not Path(folder).is_dir():
                    continue
                if self._write_folder_category(folder, collection.name):
                    self._set_cached_folder_category(folder, collection.name)
                else:
                    failed_paths.append(folder)
            migrated.append(
                CustomCollection(
                    name=collection.name,
                    folders=tuple(failed_paths),
                    closed=collection.closed,
                )
            )

        result = tuple(migrated)
        if result != current:
            settings.setValue(
                CUSTOM_COLLECTIONS_SETTING_KEY,
                serialize_custom_collections(result),
            )
            settings.sync()

    def _write_folder_category(self, folder_path: str, category: str) -> bool:
        """Egyetlen mappabesorolás mentése az ini round-trip API-ján át."""
        try:
            update_document(
                Path(folder_path) / PICASA_INI_NAME,
                lambda document: with_folder_category(document, category),
                backup=True,
            )
        except (OSError, RuntimeError, ValueError):
            logger.warning(
                "nem sikerült a mappa gyűjtemény-besorolását menteni: %s",
                folder_path,
                exc_info=True,
            )
            return False
        return True

    def _set_cached_folder_category(self, folder_path: str, category: str) -> None:
        """A lokális ini-pillanatképet az imént sikeres íráshoz igazítja."""
        categories = {
            name: [path for path in paths if path != folder_path]
            for name, paths in self._custom_collection_categories.items()
        }
        categories = {name: paths for name, paths in categories.items() if paths}
        if is_custom_collection_category(category):
            categories.setdefault(category, []).append(folder_path)
        self._custom_collection_categories = {
            name: tuple(sorted(paths, key=str.casefold))
            for name, paths in categories.items()
        }
        self._pending_custom_category_paths[folder_path] = category

    @Slot(str, str, result=str)
    def validateCollectionName(  # noqa: N802 — QML-stílusú név
        self, name: str, existing_name: str = ""
    ) -> str:
        """`""` = rendben; `"invalid"` / `"duplicate"` = a két Picasa-hiba.

        #461: a névbekérő ezt kérdezi meg, mielőtt elfogadná a nevet — a
        csendes elutasítás helyett a felhasználó megkapja az eredeti
        üzenetet.
        """
        return validate_collection_name(
            self._load_custom_collections(), name, existing_name=existing_name
        )

    @Slot(str)
    def createCollection(self, name: str) -> None:
        """Új, üres gyűjtemény — üres/duplikált nevet csendben elutasítja
        (ld. `custom_collections.create_collection`)."""
        current = self._load_custom_collections()
        self._save_custom_collections(create_collection(current, name))

    @Slot(str, str)
    def renameCollection(self, old_name: str, new_name: str) -> None:
        current = self._load_custom_collections()
        renamed = rename_collection(current, old_name, new_name)
        if renamed == current:
            return
        old = next((c for c in current if c.name == old_name), None)
        new = next((c for c in renamed if c.name == new_name.strip()), None)
        if old is not None and new is not None:
            for folder in old.folders:
                if self._write_folder_category(folder, new.name):
                    self._set_cached_folder_category(folder, new.name)
        self._save_custom_collections(renamed)

    @Slot(str)
    def deleteCollection(self, name: str) -> None:
        """A gyűjtemény törlése — a benne volt mappák csak KIKERÜLNEK
        belőle (visszakerülnek a "Mappák" alap-nézetbe), nem törlődnek."""
        current = self._load_custom_collections()
        deleted = next((c for c in current if c.name == name), None)
        if deleted is not None:
            for folder in deleted.folders:
                if self._write_folder_category(folder, FOLDERS_ON_DISK_CATEGORY):
                    self._set_cached_folder_category(
                        folder, FOLDERS_ON_DISK_CATEGORY
                    )
        self._save_custom_collections(delete_collection(current, name))

    @Slot(str, str)
    def moveFolderToCollection(self, folder_path: str, collection_name: str) -> None:
        """A mappa egy gyűjteménybe sorolása (Picasa mappakezelő-minta):
        előbb kikerül minden meglévőből, aztán (nem üres célnál) beillesztjük
        az újba. Üres `collection_name` a "Mappák" alap-nézetbe helyezi
        vissza (kikerül minden egyéni gyűjteményből)."""
        current = self._load_custom_collections()
        target = next(
            (c.name for c in current if c.name.casefold() == collection_name.casefold()),
            "",
        )
        category = target or FOLDERS_ON_DISK_CATEGORY
        if not self._write_folder_category(folder_path, category):
            return
        self._set_cached_folder_category(folder_path, category)
        self._save_custom_collections(current)

    # -- #461: bezárás/megnyitás -------------------------------------------

    @Slot(str, bool)
    def setCollectionClosed(self, name: str, closed: bool) -> None:
        """A gyűjtemény bezárása/megnyitása.

        A bezárás nem törlés és nem összecsukás: a tagmappák maradnak, de a
        képeik eltűnnek a rácsból és a keresésből is — ahogy az eredeti
        figyelmeztetése mondja. A mentés után a nézetet is frissítjük, hogy
        a változás azonnal látszódjon."""
        current = self._load_custom_collections()
        self._save_custom_collections(set_collection_closed(current, name, closed))
        self._refresh_view()

    @Slot(str, result=bool)
    def closingHidesEverything(self, name: str) -> bool:
        """Igaz, ha a gyűjtemény bezárása után egyetlen kép sem maradna a
        rácsban (#461).

        Az eredeti ilyenkor figyelmeztet: „Az utolsó gyűjteményének
        bezárására készül. Az indexképek területén egyetlen kép sem lesz
        látható." A hívó UI ezt a kérdést teszi fel, mielőtt bezárná."""
        collections = self._load_custom_collections()
        if not any(c.name == name and not c.closed for c in collections):
            return False  # már zárt, vagy nincs ilyen — nincs mit kérdezni
        utana = closed_collection_folders(
            set_collection_closed(collections, name, True)
        )
        jelenlegi = self._photos.photos
        maradna = [r for r in jelenlegi if r.folder_path not in utana]
        return bool(jelenlegi) and not maradna

    def _closed_collection_folders(self) -> frozenset[str]:
        """A bezárt gyűjtemények mappái — a nézet-szűrés bemenete (#461)."""
        return closed_collection_folders(self._load_custom_collections())
