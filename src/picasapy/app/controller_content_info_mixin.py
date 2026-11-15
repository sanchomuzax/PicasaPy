"""Mappaleírások és a kijelölt képek QML-információi."""

from __future__ import annotations

import logging
import threading

from PySide6.QtCore import QLocale, QMetaObject, Qt, Slot
from pathlib import Path
from picasapy.halozati_ut import halozati_gyoker
from picasapy.ini import load_or_empty
from picasapy.metadata import EMPTY_EXIF_DETAILS
from picasapy.metadata.reader import _cache_exif_details, _cached_exif_details
from picasapy.scanner import PICASA_INI_NAME
from . import formatting, formatting_properties
from .contact_names import central_contacts_path

_log = logging.getLogger(__name__)
_DESCRIPTION_RESULT_LOCK = threading.Lock()
_EXIF_WORK_LOCK = threading.Lock()

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
            if halozati_gyoker(folder_path) is None:
                self._descriptions[folder_path] = self._read_folder_description(
                    folder_path
                )
            else:
                self._descriptions[folder_path] = ""
                self._queue_network_folder_description(folder_path)
        return self._descriptions[folder_path]

    def _folder_description_for_open(self, folder_path: str) -> str:
        """Mappanyitáskor a helyi régi útvonalat, UNC-n az aszinkron cache-t használja."""
        if halozati_gyoker(folder_path) is None:
            return self._read_folder_description(folder_path)
        return self.folderDescriptionOf(folder_path)

    def _queue_network_folder_description(self, folder_path: str) -> None:
        """A hálózati mappa leírását egy worker tölti be egyszer."""
        pending = getattr(self, "_description_reads_pending", None)
        if pending is None:
            pending = set()
            self._description_reads_pending = pending
            self._description_read_results = {}
        with _DESCRIPTION_RESULT_LOCK:
            if folder_path in pending:
                return
            pending.add(folder_path)

        def worker() -> None:
            try:
                description = self._read_folder_description(folder_path)
            except OSError as error:
                _log.warning("A hálózati mappaleírás nem olvasható (%s): %s", folder_path, error)
                description = ""
            with _DESCRIPTION_RESULT_LOCK:
                self._description_read_results[folder_path] = description
            QMetaObject.invokeMethod(
                self,
                "_apply_network_folder_description",
                Qt.ConnectionType.QueuedConnection,
            )

        self._start_background(worker, name="picasapy-folder-description", busy=False)

    @Slot()
    def _apply_network_folder_description(self) -> None:
        """A worker eredményét átveszi, és frissíti a látható leírásokat."""
        with _DESCRIPTION_RESULT_LOCK:
            results = dict(self._description_read_results)
            self._description_read_results.clear()
            self._description_reads_pending.difference_update(results)
        self._descriptions.update(results)
        current = getattr(self, "_current_folder", "")
        if current in results:
            self._folder_description = results[current]
            self.statusChanged.emit()
        if results:
            self.feedChanged.emit()

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
        photo = photos[row]
        contacts = central_contacts_path(self._db_path)
        if halozati_gyoker(photo.folder_path) is not None and photo.kind == "photo":
            path = Path(photo.folder_path) / photo.name
            details = _cached_exif_details(path)
            if details is None:
                self._queue_network_exif_read(path)
                details = EMPTY_EXIF_DETAILS
            entries = formatting_properties._properties_entries_with_details(
                photo, QLocale(), formatting.fordit, contacts, details
            )
        else:
            entries = formatting.properties_entries(
                photo, QLocale(), formatting.fordit, contacts
            )
        return [{"label": label, "value": value} for label, value in entries]

    def _queue_network_exif_read(self, path: Path) -> None:
        """A panel EXIF-adatait egy worker tölti be, majd modelljelzéssel frissít."""
        pending = getattr(self, "_network_exif_reads_pending", None)
        if pending is None:
            pending = set()
            self._network_exif_reads_pending = pending
        key = str(path)
        with _EXIF_WORK_LOCK:
            if key in pending:
                return
            pending.add(key)

        def worker() -> None:
            try:
                details = formatting_properties.read_exif_details(path)
                _cache_exif_details(path, details)
            finally:
                with _EXIF_WORK_LOCK:
                    pending.discard(key)
                QMetaObject.invokeMethod(
                    self,
                    "_emit_network_properties_changed",
                    Qt.ConnectionType.QueuedConnection,
                )

        self._start_background(worker, name="picasapy-properties-exif", busy=False)

    @Slot()
    def _emit_network_properties_changed(self) -> None:
        """Az EXIF-cache változása újraértékelteti a panel meglévő kötését."""
        model = getattr(self, "_photos", None)
        if model is not None:
            model.revisionChanged.emit()

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
