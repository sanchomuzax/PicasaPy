"""Mappa-dátum kézi felülírása — controller-szelet (#320).

Mixin-osztály (a `library_controller.LibraryMixin` mintájára): a végleges
`AppController` örökli majd (a bekötés — az öröklés-lista bővítése a
`controller.py`-ban — forró fájl, az integrátor dolga, ld. issue).

A `.picasa.ini` `[Picasa]` `date=` kulcsán át ír/olvas (PicasaPy-
kiterjesztés, ld. `picasapy.ini.folder_date`); írás után a mappa
újraszinkronját kéri (`self.resyncFolder`, a `LibraryMixin` szelete —
mindkét mixin ugyanazon `AppController`-be kerül, ld. issue), hogy a bal
hasáb év-szakaszolása (`models._with_year_separators`) azonnal a friss
`folders.date`-et lássa."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.ini import (
    is_valid_folder_date,
    load_or_empty,
    read_folder_date_override,
    update_document,
    with_folder_date_override,
    without_folder_date_override,
)
from picasapy.scanner import PICASA_INI_NAME


class FolderDateMixin:
    """Mappa-dátum lekérdezése/felülírása a `.picasa.ini`-n át."""

    @Slot(str, result=str)
    def folderDateOverride(self, folder_path: str) -> str:
        """A mappa kézi dátum-felülírása, ISO-alakban; üres string, ha
        nincs (a mappa a legrégebbi kép dátumát használja)."""
        if not folder_path:
            return ""
        document = load_or_empty(Path(folder_path) / PICASA_INI_NAME)
        return read_folder_date_override(document) or ""

    @Slot(str, str)
    def setFolderDate(self, folder_path: str, iso_date: str) -> None:
        """Kézi dátum-felülírás mentése — érvénytelen (nem ISO-formátumú)
        `iso_date`-nál csendben nem csinál semmit (a QML-dialógus az Ok
        gombot már tiltja hibás formátumnál, ez a réteg saját védelme)."""
        if not folder_path or not is_valid_folder_date(iso_date):
            return
        stripped = iso_date.strip()
        ini_path = Path(folder_path) / PICASA_INI_NAME

        def mutate(document):
            return with_folder_date_override(document, stripped)

        update_document(ini_path, mutate, backup=True)
        self._after_folder_date_write(folder_path)

    @Slot(str)
    def clearFolderDate(self, folder_path: str) -> None:
        """A kézi felülírás törlése — a mappa a legrégebbi kép dátumára áll
        vissza a következő szinkronnál."""
        if not folder_path:
            return
        ini_path = Path(folder_path) / PICASA_INI_NAME
        update_document(ini_path, without_folder_date_override, backup=True)
        self._after_folder_date_write(folder_path)

    def _after_folder_date_write(self, folder_path: str) -> None:
        # A bal hasáb év-szakaszolása az indexbeli `folders.date`-ből él —
        # a `resyncFolder` (LibraryMixin) frissíti azt ÉS a nézetet is.
        resync = getattr(self, "resyncFolder", None)
        if resync is not None:
            resync(folder_path)
