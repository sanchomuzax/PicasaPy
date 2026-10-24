"""Felhasználói egyéni gyűjtemények — controller-szelet (#320, #4589).

Mixin-osztály (a `library_controller.LibraryMixin` és társai mintájára): a
végleges `AppController` örökli majd (a bekötés — az öröklés-lista bővítése
a `controller.py`-ban — forró fájl, az integrátor dolga, ld. issue).

A gyűjteménynevek, a csukott állapot és a jelszó-lenyomatok QSettings-ben
élnek. A mappák besorolása a `.picasa.ini` `[Picasa] P2category` kulcsából
olvasódik, és az írás/migráció az `ini/` csomag API-ján halad át."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot

from picasapy.ini import (
    FOLDERS_ON_DISK_CATEGORY,
    is_custom_collection_category,
    is_hidden_folders_category,
    read_folder_category,
    update_document,
    with_folder_category,
)
from picasapy.hidden_password import egyezik as jelszo_egyezik
from picasapy.hidden_password import picasa_lenyomat
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

    def _hidden_folder_paths(self) -> frozenset[str]:
        """A kiszűrendő rejtett mappák — az `AppController` felülírja (#4597)."""
        return frozenset()

    def _folder_is_hidden(self, folder_path: str) -> bool:
        """Rejtett-e a mappa — az `AppController` felülírja (#4597)."""
        return False

    @Property("QVariant", notify=customCollectionsChanged)
    def customCollections(self) -> list[dict]:
        """A gyűjtemények QML-nek adott alakja: `[{name, folders, closed}, ...]` —
        mindig `list`/`dict` (a projekt szabálya, sosem `tuple`)."""
        # #4597: az elrejtett mappa a rejtettek megjelenítése nélkül nem látszik
        hidden = self._hidden_folder_paths()
        return [
            {
                "name": c.name,
                "folders": (
                    []
                    if c.password_hash
                    and c.name not in self._unlocked_custom_collections
                    else [f for f in c.folders if f not in hidden]
                ),
                "closed": c.closed,
            }
            for c in self._load_custom_collections()
        ]

    def _init_custom_collections(self) -> None:
        """A konstruktorból hívandó; átveszi a korábbi QSettings-tagságot."""
        if not hasattr(self, "_unlocked_custom_collections"):
            self._unlocked_custom_collections: set[str] = set()
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

    def _collection_by_name(self, name: str) -> CustomCollection | None:
        return next(
            (
                collection
                for collection in self._load_custom_collections()
                if collection.name == name
            ),
            None,
        )

    def _store_collection_password(
        self, name: str, password_hash: str, *, authenticated: bool
    ) -> bool:
        collections = self._load_custom_collections()
        if not any(collection.name == name for collection in collections):
            return False
        updated = tuple(
            replace(collection, password_hash=password_hash)
            if collection.name == name
            else collection
            for collection in collections
        )
        if updated == collections:
            return False
        self._save_custom_collections(updated)
        if authenticated or not password_hash:
            self._unlocked_custom_collections.add(name)
        else:
            self._unlocked_custom_collections.discard(name)
        self.customCollectionsChanged.emit()
        self._refresh_custom_collection_password_view()
        return True

    def _refresh_custom_collection_password_view(self) -> None:
        refresh = getattr(self, "_refresh_view", None)
        if callable(refresh):
            refresh()

    @Slot(str, result=bool)
    def collectionPasswordSet(self, name: str) -> bool:  # noqa: N802
        """Van-e lenyomat a megnevezett felhasználói gyűjteményhez."""
        collection = self._collection_by_name(name)
        return bool(collection and collection.password_hash)

    def collectionPasswordLocked(self, name: str) -> bool:  # noqa: N802
        """A jelszavas gyűjtemény zárolt, amíg ebben a munkamenetben fel nem oldják.

        Python-oldali állapotlekérdezés a belső vezérlőhöz; a QML felület
        műveleteket kér a dedikált párbeszéden keresztül.
        """
        collection = self._collection_by_name(name)
        if collection is None or not collection.password_hash:
            return False
        self._init_custom_collections()
        return name not in self._unlocked_custom_collections

    @Slot(str, str, result=bool)
    def verifyCollectionPassword(  # noqa: N802
        self, name: str, password: str
    ) -> bool:
        """A gyűjtemény jelszavának ellenőrzése mellékhatás nélkül."""
        collection = self._collection_by_name(name)
        return bool(
            collection
            and collection.password_hash
            and jelszo_egyezik(collection.password_hash, password)
        )

    @Slot(str, str, result=bool)
    def unlockCollection(self, name: str, password: str) -> bool:  # noqa: N802
        """A megfelelő jelszó csak a megnevezett gyűjteményt oldja fel."""
        if not self.verifyCollectionPassword(name, password):
            return False
        self._init_custom_collections()
        self._unlocked_custom_collections.add(name)
        self.customCollectionsChanged.emit()
        self._refresh_custom_collection_password_view()
        return True

    @Slot(str, str, str, result=bool)
    def setCollectionPassword(  # noqa: N802
        self, name: str, password: str, verification: str
    ) -> bool:
        """Új jelszó beállítása; a nyílt jelszó nem kerül mentésre."""
        collection = self._collection_by_name(name)
        if (
            collection is None
            or collection.password_hash
            or not password
            or password != verification
        ):
            return False
        self._init_custom_collections()
        return self._store_collection_password(
            name, picasa_lenyomat(password), authenticated=False
        )

    @Slot(str, str, str, str, result=bool)
    def changeCollectionPassword(  # noqa: N802
        self, name: str, current_password: str, password: str, verification: str
    ) -> bool:
        """Jelszócsere csak az aktuális jelszó és az ismétlés egyezésekor."""
        if (
            not self.verifyCollectionPassword(name, current_password)
            or not password
            or password != verification
        ):
            return False
        return self._store_collection_password(
            name, picasa_lenyomat(password), authenticated=True
        )

    @Slot(str, str, result=bool)
    def clearCollectionPassword(  # noqa: N802
        self, name: str, current_password: str
    ) -> bool:
        """Jelszó eltávolítása az aktuális jelszó igazolása után."""
        if not self.verifyCollectionPassword(name, current_password):
            return False
        return self._store_collection_password(name, "", authenticated=True)

    def _locked_custom_collection_folders(self) -> frozenset[str]:
        """A még fel nem oldott jelszavas gyűjtemények útvonalai."""
        self._init_custom_collections()
        return frozenset(
            folder
            for collection in self._load_custom_collections()
            if collection.password_hash
            and collection.name not in self._unlocked_custom_collections
            for folder in collection.folders
        )

    def _save_custom_collections(
        self, collections: tuple[CustomCollection, ...]
    ) -> None:
        # A tagság az ini-ben él; a beállítás a nevek, a csukott állapot és
        # a jelszó-lenyomatok tárolója. Nyílt jelszót nem írunk ki.
        definitions = tuple(
            CustomCollection(
                name=c.name,
                closed=c.closed,
                password_hash=c.password_hash,
            )
            for c in collections
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
                effective = self._write_folder_category(folder, collection.name)
                if effective is not None:
                    self._set_cached_folder_category(folder, effective)
                else:
                    failed_paths.append(folder)
            migrated.append(
                CustomCollection(
                    name=collection.name,
                    folders=tuple(failed_paths),
                    closed=collection.closed,
                    password_hash=collection.password_hash,
                )
            )

        result = tuple(migrated)
        if result != current:
            settings.setValue(
                CUSTOM_COLLECTIONS_SETTING_KEY,
                serialize_custom_collections(result),
            )
            settings.sync()

    def _write_folder_category(
        self, folder_path: str, category: str, *, overwrite_hidden: bool = False
    ) -> str | None:
        """Egyetlen mappabesorolás mentése az ini round-trip API-ján át.

        Visszatérés: a ténylegesen érvényes besorolás, `None` írási hibánál.
        #4597: az elrejtett mappa `Hidden Folders` besorolását átnevezés,
        törlés vagy migráció nem írja felül (csak a kifejezett
        `overwrite_hidden=True`, a mappa gyűjteménybe mozgatása)."""
        effective = category

        def mutate(document):
            nonlocal effective
            current = read_folder_category(document)
            if not overwrite_hidden and is_hidden_folders_category(current):
                effective = current
                return document
            effective = category
            return with_folder_category(document, category)

        try:
            update_document(
                Path(folder_path) / PICASA_INI_NAME, mutate, backup=True
            )
        except (OSError, RuntimeError, ValueError):
            logger.warning(
                "nem sikerült a mappa gyűjtemény-besorolását menteni: %s",
                folder_path,
                exc_info=True,
            )
            return None
        return effective

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
                effective = self._write_folder_category(folder, new.name)
                if effective is not None:
                    self._set_cached_folder_category(folder, effective)
            if old_name in self._unlocked_custom_collections:
                self._unlocked_custom_collections.discard(old_name)
                self._unlocked_custom_collections.add(new.name)
        self._save_custom_collections(renamed)

    @Slot(str)
    def deleteCollection(self, name: str) -> None:
        """A gyűjtemény törlése — a benne volt mappák csak KIKERÜLNEK
        belőle (visszakerülnek a "Mappák" alap-nézetbe), nem törlődnek."""
        current = self._load_custom_collections()
        deleted = next((c for c in current if c.name == name), None)
        if deleted is not None:
            for folder in deleted.folders:
                effective = self._write_folder_category(
                    folder, FOLDERS_ON_DISK_CATEGORY
                )
                if effective is not None:
                    self._set_cached_folder_category(folder, effective)
        self._unlocked_custom_collections.discard(name)
        self._save_custom_collections(delete_collection(current, name))

    @Slot(str, str)
    def moveFolderToCollection(self, folder_path: str, collection_name: str) -> None:
        """A mappa egy gyűjteménybe sorolása (Picasa mappakezelő-minta):
        előbb kikerül minden meglévőből, aztán (nem üres célnál) beillesztjük
        az újba. Üres `collection_name` a "Mappák" alap-nézetbe helyezi
        vissza (kikerül minden egyéni gyűjteményből)."""
        if self._folder_is_hidden(folder_path):
            # #4597: rejtett mappa nem helyezhető át gyűjteménybe
            self.folderHideFailed.emit(folder_path, "hidden-move")
            return
        current = self._load_custom_collections()
        target = next(
            (c.name for c in current if c.name.casefold() == collection_name.casefold()),
            "",
        )
        category = target or FOLDERS_ON_DISK_CATEGORY
        if (
            self._write_folder_category(
                folder_path, category, overwrite_hidden=True
            )
            is None
        ):
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
        """A bezárt és még fel nem oldott gyűjtemények mappái."""
        return closed_collection_folders(self._load_custom_collections()) | (
            self._locked_custom_collection_folders()
        )
