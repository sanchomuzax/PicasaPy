"""Egyéni mappagyűjtemények beolvasása a `[Picasa] P2category` mezőből."""

from __future__ import annotations

from picasapy.ini import (
    IniDocument,
    is_custom_collection_category,
    read_folder_category,
)


class CustomCollectionFolderCollector:
    """A korpuszban talált egyéni gyűjtemények mappáit csoportosítja."""

    def __init__(self) -> None:
        self._folders: dict[str, list[str]] = {}

    def __call__(self, folder_path: str, document: IniDocument) -> None:
        category = read_folder_category(document)
        if not is_custom_collection_category(category):
            return
        self._folders.setdefault(category, []).append(folder_path)

    def result(self) -> tuple[tuple[str, tuple[str, ...]], ...]:
        """Stabil, immutable név → mappaútvonal csoportok."""
        return tuple(
            (
                name,
                tuple(sorted(paths, key=str.casefold)),
            )
            for name, paths in sorted(
                self._folders.items(), key=lambda item: item[0].casefold()
            )
        )


__all__ = ["CustomCollectionFolderCollector"]
