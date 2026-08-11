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
    create_collection,
    delete_collection,
    move_folder_to_collection,
    parse_custom_collections,
    rename_collection,
    serialize_custom_collections,
    validate_collection_name,
)


class CustomCollectionsMixin:
    """Egyéni gyűjtemények: létrehozás, átnevezés, törlés, mappa-áthelyezés."""

    customCollectionsChanged = Signal()

    @Property("QVariant", notify=customCollectionsChanged)
    def customCollections(self) -> list[dict]:
        """A gyűjtemények QML-nek adott alakja: `[{name, folders}, ...]` —
        mindig `list`/`dict` (a projekt szabálya, sosem `tuple`)."""
        return [
            {"name": c.name, "folders": list(c.folders)}
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
