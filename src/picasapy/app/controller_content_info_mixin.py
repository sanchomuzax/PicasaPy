"""Mappaleírások és a kijelölt képek QML-információi."""

from __future__ import annotations

from PySide6.QtCore import QLocale, Slot
from pathlib import Path
from picasapy.ini import load_or_empty
from picasapy.scanner import PICASA_INI_NAME
from . import formatting
from .contact_names import central_contacts_path

class ContentInfoMixin:
    """Mappaleírások és a kijelölt képek QML-információi."""

    @staticmethod
    def _read_folder_description(folder_path: str) -> str:
        """A mappa `[Picasa]/description` kulcsának beolvasása az ini-ből."""
        ini_path = Path(folder_path) / PICASA_INI_NAME
        section = load_or_empty(ini_path).section("Picasa")
        return (section.get("description") if section else None) or ""

    @Slot(str, result=str)
    def folderDescriptionOf(self, folder_path: str) -> str:
        """Mappa-leírás a feed-fejlécnek (#64) — ini-olvasás kis cache-sel,
        hogy NAS-on se olvassunk fejléc-megjelenésenként fájlt."""
        if folder_path not in self._descriptions:
            self._descriptions[folder_path] = self._read_folder_description(
                folder_path
            )
        return self._descriptions[folder_path]

    # -- infó-szövegek (formázás: formatting.py) -----------------------------

    @Slot(int, result=str)
    def photoInfo(self, row: int) -> str:
        """A kék infó-sáv kijelöléskori tartalma, Picasa-stílusban:
        `név   dátum   SZxM képpont   méret`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        return formatting.photo_info_text(photos[row], QLocale(), formatting.fordit)

    @Slot("QVariantList", result=str)
    def selectionInfo(self, rows) -> str:
        """A kék sáv szövege TÖBB kijelölt képnél (#1189).

        Az eredetiben ezt a `GetSelectionInfo` (`0x0056fbc0`) állítja elő,
        és a KIJELÖLÉSRŐL ír: darabszám, dátum(tartomány), összméret
        (`il_GetSelectionInfo::3/4/5`). Valódi Picasa-képernyőképpel
        megerősítve: „25 képek   2026. január 2., péntek-2026. május 18.,
        hétfő   37,5 MB a lemezen".

        Ugyanaz a formázó fut, mint a mappa-összesítésre (`statusText`) —
        csak a KIJELÖLT rekordokon. Érvénytelen/ismétlődő sorindexek
        kiszűrve, hogy egy elszállt QML-tömb ne torzítsa az összeget.
        """
        photos = self._photos.photos
        latott: set[int] = set()
        kijelolt = []
        for nyers in rows or ():
            try:
                row = int(nyers)
            except (TypeError, ValueError):
                continue
            if 0 <= row < len(photos) and row not in latott:
                latott.add(row)
                kijelolt.append(photos[row])
        if not kijelolt:
            return self._status
        return formatting.status_text(
            kijelolt, QLocale(), formatting.fordit, self.tr
        )

    @Slot(int, result="QVariantList")
    def propertiesOf(self, row: int) -> list:
        """A Tulajdonságok-panel (#13) sorai: {label, value} párok."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return []
        entries = formatting.properties_entries(
            photos[row],
            QLocale(),
            formatting.fordit,
            central_contacts_path(self._db_path),
        )
        return [{"label": label, "value": value} for label, value in entries]

    @Slot(int, result=str)
    def viewerInfo(self, row: int) -> str:
        """A néző sávja: `mappa > név   dátum   felbontás   méret   (N / i)   címkék`."""
        photos = self._photos.photos
        if not 0 <= row < len(photos):
            return ""
        photo = photos[row]
        folder = formatting.PATH_TAIL.split(photo.folder_path)[-1]
        # #2587: a SZÁMLÁLÓ visszakerült a MÉRT helyére — a fájlméret UTÁN
        # és a címkék ELŐTT (`picasa3-felirat-bekapcsolva. 223224.jpg`,
        # teljes szélességű ablak: `… 807 KB   (82 / 3)   Címkék: AI image`).
        # A #2565 körében tévesen kivettük: az akkori felvételen a Picasa
        # FÉL SZÉLESSÉGŰ ablakban állt, a sáv szövege le volt vágva, és a
        # levágást olvastuk hiánynak.
        alap = formatting.photo_info_text(
            photo,
            QLocale(),
            formatting.fordit,
            self.szamlalo_szoveg(row + 1, len(photos)),
        )
        return alap.replace(photo.name, f"{folder} > {photo.name}", 1)
