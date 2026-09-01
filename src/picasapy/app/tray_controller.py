"""Kép-tálca (Picture Tray, #455) — az AppController VÉKONY szelete.

Az állapot és minden szabály a felület-független magban él
(`picasapy.tray`); ez a szelet csak **fordít**: rács-sorból fotó-azonosító,
fotó-azonosítóból útvonal/bélyegkép, és a QML felé jelzés a változásról.

## Miért van külön mag

Mert két felület ül rajta: a főablak alsó sávjának képtálcája
(`TrayBar.qml`) és — a #1276 után — a kollázs-szerkesztő „Klipek" lapja.
A Picasa saját szövegforrása mondja ki, hogy a kettő ugyanaz: a
`collagepanel/deleteclips` súgója *„Remove selected clips from the
**tray**"*, a filmszalag neve `Unused Pictures`. A „felhasználtság" ezért
az ADATMODELLBEN van (`TrayItem.used`), nem a nézetben — a Klipek lapnak
elég a `trayItems` fel nem használt részét kirajzolnia.

Döntési lap: `docs/decisions/keptalca-modell.md`.

## A névhasználat, hogy ne legyen félreérthető

- **`heldCount` / `heldPaths` / `trayItems`** — a tálca EGÉSZE. A tálca
  alapból a kijelölés tükre (`syncSelection`), tehát ez kijelöléskor sem
  nulla.
- **`isHeldAt`** — az elem RÖGZÍTETT-e („Kijelölés megtartása"). A rácsbeli
  jelvény (`holdadorner`) ezt mutatja: azt, amit a következő kijelölés már
  nem söpör el — nem azt, ami épp ki van jelölve.

## Ami NINCS benne (szándékosan)

- **Tartósság.** A tálca a program bezárásával elvész — három független
  ellenőrzés mondta ki (`docs/specs/picasa-keptalca.md` 1.). A megőrzés
  eltérés lenne, nem javítás.
- **Az `il_ClearFromTray` felkínált takarítás felülete.** A SZABÁLYA
  megvan és tesztelt a magban (`needs_old_items_prompt` — darabszám-
  növekedés, nem kor), de hogy az eredeti melyik pillanatban kérdez, nincs
  kimérve; kitalálni nem akarjuk.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy import tray
from picasapy.index import open_index, photo_by_id
from picasapy.ini.albums import with_album
from picasapy.app import formatting
from picasapy.app.models import _thumb_url


class TrayMixin:
    """A képtálca (`scratch`) vezérlő-szelete — fotó-id-k, mappától
    függetlenül."""

    heldChanged = Signal()

    def _ensure_tray_wired(self) -> None:
        """Lusta, egyszeri állapot-inicializálás (a `PhotoOpsMixin.
        _ensure_photo_ops_wired` mintája) — a controller.py (forró fájl)
        `__init__`-jét emiatt nem kell módosítani."""
        if getattr(self, "_tray_wired", False):
            return
        self._tray_wired = True
        self._tray: tray.TrayState = tray.EMPTY
        #: a RÖGZÍTETT azonosítók halmaza — az `isHeldAt` a rács MINDEN
        #: látható cellájára lefut, a kijelölés minden változásakor
        #: (lasszózás közben másodpercenként sokszor); lineáris keresés
        #: helyett ezért halmaz
        self._tray_held: frozenset[int] = frozenset()
        #: a tálca változásainak számlálója — a rekord-gyorstár kulcsa
        self._tray_revision = 0
        #: a MÁS mappából tartott képek rekordjai (a jelenlegi mappa
        #: rekordjai mindig a friss modellből jönnek, ld. `_tray_records`)
        self._tray_foreign: dict[int, object] = {}
        self._tray_records_cache: tuple[int, list] | None = None

    # -- belső segédek ----------------------------------------------------

    def _tray_apply(self, state: tray.TrayState) -> None:
        """Az új állapot beállítása — jelzéssel, ha tényleg változott."""
        if state == self._tray:
            return
        self._tray = state
        self._tray_held = frozenset(tray.held_ids(state))
        self._tray_revision += 1
        self._tray_records_cache = None
        self.heldChanged.emit()

    def _tray_ids_of_rows(self, rows) -> list[int]:
        """Rács-sorokból fotó-azonosítók. A QML-tömb elemei `QVariant`-ok,
        és egy leépülő nézet érvénytelen sort is küldhet — az ilyet némán
        kihagyjuk (a `selectionInfo` mintája), mert ez a felület
        határa, nem programhiba."""
        ids: list[int] = []
        for nyers in rows or ():
            try:
                row = int(nyers)
            except (TypeError, ValueError):
                continue
            photo_id = self._photos.idAt(row)
            if photo_id:
                ids.append(int(photo_id))
        return ids

    @staticmethod
    def _tray_ids_of_values(values) -> list[int]:
        """QML-tömbből fotó-azonosítók (a Klipek lap felől jönnek így)."""
        ids: list[int] = []
        for nyers in values or ():
            try:
                photo_id = int(nyers)
            except (TypeError, ValueError):
                continue
            if photo_id > 0:
                ids.append(photo_id)
        return ids

    def _tray_records(self) -> list:
        """A tálca elemeinek fotó-rekordjai, beszúrási sorrendben.

        A jelenlegi mappa képei a MEMÓRIÁBAN lévő modellből jönnek (nulla
        adatbázis-hívás — a tálca a kijelölést tükrözi, tehát ez a gyakori
        eset, és lasszózás közben másodpercenként sokszor lefut). Csak a
        más mappából tartott képekért nyúlunk az indexhez, azokat is
        egyetlen kapcsolatban, és megjegyezve.

        Az időközben eltűnt (törölt/áthelyezett) kép egyszerűen kimarad.
        """
        self._ensure_tray_wired()
        gyorstar = self._tray_records_cache
        if gyorstar is not None and gyorstar[0] == self._tray_revision:
            return gyorstar[1]
        ids = tray.photo_ids(self._tray)
        aktualis = {photo.id: photo for photo in self._photos.photos}
        hianyzo = [
            photo_id
            for photo_id in ids
            if photo_id not in aktualis and photo_id not in self._tray_foreign
        ]
        if hianyzo:
            with open_index(self._db_path) as conn:
                for photo_id in hianyzo:
                    record = photo_by_id(conn, photo_id)
                    if record is not None:
                        self._tray_foreign[photo_id] = record
        rekordok = [
            aktualis.get(photo_id) or self._tray_foreign.get(photo_id)
            for photo_id in ids
        ]
        rekordok = [record for record in rekordok if record is not None]
        self._tray_records_cache = (self._tray_revision, rekordok)
        return rekordok

    # -- lekérdezések a felület felé --------------------------------------

    @Property(int, notify=heldChanged)
    def heldCount(self) -> int:
        """A tálca elemszáma (a rögzített ÉS a kijelölésből tükrözött)."""
        self._ensure_tray_wired()
        return len(self._tray.items)

    @Property(int, notify=heldChanged)
    def trayUnusedCount(self) -> int:
        """A FEL NEM HASZNÁLT elemek száma — ez lesz a kollázs „Klipek (N)"
        fülfeliratának száma (`collageUI::tab2_title`), és ugyanezt a
        jelölőt kérdezi az eredeti számláló hurka is."""
        self._ensure_tray_wired()
        return len(tray.unused_ids(self._tray))

    @Slot(int, result=bool)
    def isHeldAt(self, row: int) -> bool:
        """Jelvényhez (rács): a `row` fotója RÖGZÍTETT-e a tálcán.

        Szándékosan nem a puszta tálcán-létet mutatja: a tálca alapból a
        kijelölés tükre, és minden kijelölt képre kitett jelvény csak a
        kijelölés-keretet ismételné meg.
        """
        self._ensure_tray_wired()
        photo_id = self._photos.idAt(row)
        if not photo_id:
            return False
        return int(photo_id) in self._tray_held

    @Property("QVariant", notify=heldChanged)
    def heldPaths(self):
        """A tálcán lévő képek fájl-útvonalai, beszúrási sorrendben.

        **Ez a #455 lényegi pontja (3. teendő):** a tálca alatti műveletsor
        (nyomtatás · e-mail · exportálás · kollázs · film · feltöltés) az
        eredetiben a TÁLCA TARTALMÁN dolgozott — a bináris `trayexec`
        hatóköre is ezt mondja. Útvonalat adunk vissza (nem rács-sort),
        mert a tartott kép nem feltétlenül a nyitott mappában van.
        """
        return [
            str(Path(record.folder_path) / record.name)
            for record in self._tray_records()
        ]

    @Property("QVariant", notify=heldChanged)
    def trayItems(self):
        """A tálca teljes tartalma a nézeteknek — EZ a Klipek lap bemenete.

        Minden elem: `photoId`, `path`, `thumbUrl`, `name`, `used`, `held`.
        A Klipek lap a `used === false` elemeket rajzolja ki („Unused
        Pictures"), a főablak tálcája mindet.
        """
        self._ensure_tray_wired()
        allapotok = {item.photo_id: item for item in self._tray.items}
        elemek = []
        for record in self._tray_records():
            item = allapotok.get(record.id)
            elemek.append(
                {
                    "photoId": record.id,
                    "path": str(Path(record.folder_path) / record.name),
                    "thumbUrl": _thumb_url(record),
                    "name": record.name,
                    "used": bool(item and item.used),
                    "held": bool(item and item.held),
                }
            )
        return elemek

    @Slot(int, result=str)
    def heldThumbUrlAt(self, index: int) -> str:
        """A tálca-előnézet `index`. elemének thumb-URL-je."""
        rekordok = self._tray_records()
        if not 0 <= index < len(rekordok):
            return ""
        return _thumb_url(rekordok[index])

    @Slot(result=str)
    def trayInfo(self) -> str:
        """A kék infó-sáv szövege a TÁLCA tartalmáról (`il_GetSelectionInfo`).

        Ugyanaz a formázó fut, mint a kijelölésre (`selectionInfo`) — csak
        a forrás más: a tálca mappákon átnyúlik, tehát a darabszám, a
        dátumtartomány és az összméret a máshonnan tartott képeket is
        beleszámítja. Üres tálcánál üres sztring: a hívó ilyenkor a mai
        (mappa-összesítő) ágra esik vissza.
        """
        rekordok = self._tray_records()
        if not rekordok:
            return ""
        locale = QLocale()
        if len(rekordok) == 1:
            return formatting.photo_info_text(rekordok[0], locale, self.tr)
        return formatting.status_text(rekordok, locale, self.tr, self.tr)

    # -- műveletek --------------------------------------------------------

    @Slot("QVariantList")
    def syncSelection(self, rows) -> None:
        """A kijelölés automatikusan a tálcába kerül (#455).

        A Picasa tálcája **a kijelölés meghosszabbítása** volt, nem külön
        kosár: alapból a kijelölést mutatta, a „Hold" pedig befagyasztotta,
        hogy másik mappából is lehessen hozzátenni. Ezt a hívást a felület
        minden kijelölés-változásra elküldi.
        """
        self._ensure_tray_wired()
        self._tray_apply(
            tray.with_selection(self._tray, self._tray_ids_of_rows(rows))
        )

    @Slot(list)
    def holdRows(self, rows: list) -> None:
        """„Kijelölés megtartása" (`Tray::ID_PICTURE_HOLDINPICTURETRAY`):
        a megadott sorok fotói RÖGZÜLNEK — a következő kijelölés nem söpri
        el őket. Ettől lesz a tálca mappákon átnyúló gyűjtő."""
        self._ensure_tray_wired()
        self._tray_apply(
            tray.with_hold(self._tray, self._tray_ids_of_rows(rows))
        )

    @Slot(list)
    def removeHeldRows(self, rows: list) -> None:
        """„Kijelölés eltávolítása" (`Tray::ID_REMOVE_SELECTION`), és a
        Klipek lap „–" gombjának magja (*Remove selected clips from the
        tray*)."""
        self._ensure_tray_wired()
        self._tray_apply(
            tray.without(self._tray, self._tray_ids_of_rows(rows))
        )

    @Slot("QVariantList", bool)
    def setTrayUsedRows(self, rows, used: bool = True) -> None:
        """Ugyanaz, mint a `setTrayUsed`, csak RÁCS-SOROKKAL.

        A Klipek lap „+" gombja a KÖNYVTÁR kijelölését kapja meg, az pedig
        rács-sorokból áll (`librarySelection`) — nem fotó-azonosítókból. A
        `setTrayUsed` azonosítót vár, és a `0.` sort némán eldobná
        (`photo_id > 0`), vagyis az első kép felvétele nyom nélkül maradna
        (#1276).
        """
        self._set_tray_used_ids(self._tray_ids_of_rows(rows), used=used)

    @Slot("QVariantList")
    def removeTrayItems(self, photo_ids) -> None:
        """A Klipek lap „–" gombjának magja: a megadott FOTÓ-AZONOSÍTÓKAT
        veszi ki a tálcából (*Remove the selected pictures from the tray*).

        Miért nem a `removeHeldRows`: az rács-SOROKAT vár, mert a főablak
        tálca-sávja felől a kijelölés onnan érkezik. A Klipek lap viszont
        magukat a tálca-elemeket listázza — ott nincs rács-sor, és a
        tartott kép akár másik mappából is jöhet, tehát sor nem is
        rendelhető hozzá. Ezért kap a lap saját, azonosító-alapú belépőt
        (#1276).
        """
        self._ensure_tray_wired()
        self._tray_apply(
            tray.without(self._tray, self._tray_ids_of_values(photo_ids))
        )

    @Slot()
    def clearHeld(self) -> None:
        """A tálca teljes ürítése (`IDS_CLEARTRAY`). A felület KÉRDEZ előtte
        — a megerősítés a `TrayBar.qml`-ben él, nem itt."""
        self._ensure_tray_wired()
        self._tray_apply(tray.cleared(self._tray))

    def _set_tray_used_ids(self, photo_ids, used: bool = True) -> None:
        """A tálca-elemek FELHASZNÁLTSÁGA, fotó-azonosítók szerint.

        `used=True`: a kép a tálcán MARAD, csak az „Unused Pictures"
        listából esik ki (ez a Klipek lap „+" gombjának hatása).
        `used=False` a visszavonás — a kollázsról levett kép újra
        választható.

        #1276: ez a tag SZÁNDÉKOSAN nem `@Slot`. A felület egyetlen
        belépője a `setTrayUsedRows`, mert a „+" a könyvtár RÁCS-SORAIT
        kapja; azonosító-alapú QML-hívó ma nincs, egy bekötetlen slot
        pedig néma lánc-szakadás lenne (`scripts/kepesseg_or.py`). Ha a
        visszavonás egyszer a kollázs felől érkezik, ott azonosító lesz —
        akkor kap ez a mag saját slotot, hívóval együtt.
        """
        self._ensure_tray_wired()
        self._tray_apply(
            tray.with_used(
                self._tray,
                self._tray_ids_of_values(photo_ids),
                used=bool(used),
            )
        )

    @Slot(str, result=bool)
    def addHeldToAlbum(self, token: str) -> bool:
        """„Add to" (#455): a TÁLCA TARTALMA egy meglévő albumba.

        Az eredetiben a tálcán külön gomb kínálta ezt (`addtobuttcon`,
        *Add selected items to an Album*). A tálca mappákon átnyúlik, ezért
        az `addRowsToAlbum` (rács-sor alapú) útja itt nem járható: a
        rekordokat a tálcából oldjuk fel, és mappánként egyetlen
        ini-írással írjuk (ugyanaz a `_write_album_batch`).

        Üres tálcánál/tokennél `False` (nincs mit tenni).
        """
        self._ensure_tray_wired()
        token = (token or "").strip()
        photos = self._tray_records()
        if not token or not photos:
            return False
        return self._write_album_batch(
            photos, lambda document, photo: with_album(document, photo.name, token)
        )
