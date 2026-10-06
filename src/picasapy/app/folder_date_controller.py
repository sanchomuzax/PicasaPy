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
    read_folder_music,
    update_document,
    with_folder_date_override,
    with_folder_music,
    without_folder_date_override,
)
from picasapy.scanner import PICASA_INI_NAME

from .photo_ops_controller import _WRITE_ERRORS
from . import formatting


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

    @Slot(str, result=bool)
    def folderMusicEnabled(self, folder_path: str) -> bool:  # noqa: N802
        if not folder_path:
            return False
        return read_folder_music(
            load_or_empty(Path(folder_path) / PICASA_INI_NAME)
        )[0]

    @Slot(str, result=str)
    def folderMusicFile(self, folder_path: str) -> str:  # noqa: N802
        if not folder_path:
            return ""
        return read_folder_music(
            load_or_empty(Path(folder_path) / PICASA_INI_NAME)
        )[1]

    @Slot(str, bool, str)
    def setFolderMusic(  # noqa: N802
        self, folder_path: str, use_music: bool, music_file: str
    ) -> None:
        """A mappa `usemusic`/`music` mezőinek mentése az ini API-val."""
        if not folder_path:
            return
        local_file = formatting.to_local_path(music_file)
        ini_path = Path(folder_path) / PICASA_INI_NAME
        if not self._ini_iras(
            ini_path,
            lambda document: with_folder_music(document, use_music, local_file),
        ):
            return
        changed = getattr(self, "statusChanged", None)
        if changed is not None:
            changed.emit()

    def folderMusicTrackUrls(self, folder_path: str) -> list:  # noqa: N802
        """A bekapcsolt mappazene URL-je a diavetítőnek."""
        enabled, music_file = read_folder_music(
            load_or_empty(Path(folder_path) / PICASA_INI_NAME)
        ) if folder_path else (False, "")
        if not enabled or not music_file:
            return []
        path = Path(music_file).expanduser()
        try:
            if not path.is_file():
                return []
            return [formatting.to_file_url(str(path.resolve()))]
        except OSError:
            return []

    @Slot(str, result=str)
    def localPathFromFileUrl(self, file_url: str) -> str:  # noqa: N802
        """A Qt fájlválasztó URL-jét helyi útvonallá alakítja."""
        return formatting.to_local_path(file_url)

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

        if not self._ini_iras(ini_path, mutate):
            return
        self._after_folder_date_write(folder_path)

    @Slot(str)
    def clearFolderDate(self, folder_path: str) -> None:
        """A kézi felülírás törlése — a mappa a legrégebbi kép dátumára áll
        vissza a következő szinkronnál."""
        if not folder_path:
            return
        ini_path = Path(folder_path) / PICASA_INI_NAME
        if not self._ini_iras(ini_path, without_folder_date_override):
            return
        self._after_folder_date_write(folder_path)

    def _ini_iras(self, ini_path: Path, mutate) -> bool:
        """Az ini-írás védve — `True`, ha tényleg kiment (#2506).

        Írásvédett mappán vagy tele lemezen a kivétel eddig a QML-slotból
        szökött ki, a bal hasáb pedig már az ÚJ dátumot mutatta volna: a
        felhasználó azt hitte, mentett. A projekt meglévő hibacsatornája ez
        (#459: `photoOpFailed` → `syncFailed` → `Main.qml` `errorBanner`).

        A `False` ágon SZÁNDÉKOSAN nem hívjuk az újraszinkront: a lemezen a
        RÉGI érték maradt, tehát a nézetnek sincs mit követnie.
        """
        try:
            update_document(ini_path, mutate, backup=True)
        except _WRITE_ERRORS as error:
            self.jelentsdAzIrasiHibat(error)
            return False
        return True

    def _after_folder_date_write(self, folder_path: str) -> None:
        # A bal hasáb év-szakaszolása az indexbeli `folders.date`-ből él —
        # a `resyncFolder` (LibraryMixin) frissíti azt ÉS a nézetet is.
        resync = getattr(self, "resyncFolder", None)
        if resync is not None:
            resync(folder_path)
