"""Felhasználói egyéni gyűjtemények — controller-szelet (#320).

Mixin-osztály (a `library_controller.LibraryMixin` és társai mintájára): a
végleges `AppController` örökli majd (a bekötés — az öröklés-lista bővítése
a `controller.py`-ban — forró fájl, az integrátor dolga, ld. issue).

A mixin a host `self._get_settings()`-jét használja (minden AppController-
példányon elérhető, ld. `controller.py`) — a tényleges gyűjtemény-adatok a
`custom_collections` modul tiszta függvényein át, egyetlen JSON-szerializált
QSettings-kulcs alatt élnek (ld. ott a tárolási döntés indoklását)."""

from __future__ import annotations

from PySide6.QtCore import Property, Signal, Slot

from .custom_collections import (
    CUSTOM_COLLECTIONS_SETTING_KEY,
    CustomCollection,
    closed_collection_folders,
    create_collection,
    delete_collection,
    move_folder_to_collection,
    parse_custom_collections,
    rename_collection,
    serialize_custom_collections,
    set_collection_closed,
    validate_collection_name,
)


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

    def _load_custom_collections(self) -> tuple[CustomCollection, ...]:
        raw = self._get_settings().value(CUSTOM_COLLECTIONS_SETTING_KEY)
        return parse_custom_collections(raw)

    def _save_custom_collections(
        self, collections: tuple[CustomCollection, ...]
    ) -> None:
        self._get_settings().setValue(
            CUSTOM_COLLECTIONS_SETTING_KEY, serialize_custom_collections(collections)
        )
        self.customCollectionsChanged.emit()

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
        self._save_custom_collections(
            rename_collection(current, old_name, new_name)
        )

    @Slot(str)
    def deleteCollection(self, name: str) -> None:
        """A gyűjtemény törlése — a benne volt mappák csak KIKERÜLNEK
        belőle (visszakerülnek a "Mappák" alap-nézetbe), nem törlődnek."""
        current = self._load_custom_collections()
        self._save_custom_collections(delete_collection(current, name))

    @Slot(str, str)
    def moveFolderToCollection(self, folder_path: str, collection_name: str) -> None:
        """A mappa egy gyűjteménybe sorolása (Picasa mappakezelő-minta):
        előbb kikerül minden meglévőből, aztán (nem üres célnál) beillesztjük
        az újba. Üres `collection_name` a "Mappák" alap-nézetbe helyezi
        vissza (kikerül minden egyéni gyűjteményből)."""
        current = self._load_custom_collections()
        self._save_custom_collections(
            move_folder_to_collection(current, folder_path, collection_name)
        )

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
