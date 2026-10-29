"""A képtálca képeinek állapota, lekérdezése és kijelölése."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Property, QLocale, Signal, Slot

from picasapy import tray
from picasapy.index import open_index, photo_by_id
from picasapy.app import formatting
from picasapy.app.models import _thumb_url


class _TraySignalsMixin:
    heldChanged = Signal()
    #: #5976: Google Photos hitelesítés és tálcafeltöltés állapota.
    googlePhotosChanged = Signal()
    photosUploadChanged = Signal()
    googlePhotosProgressReported = Signal(str, int, int)
    googlePhotosCurrentFileReported = Signal(str)
    googlePhotosUploadResultReported = Signal(str, bool, int)
    googlePhotosAuthResultReported = Signal(str, str)



heldChanged = _TraySignalsMixin.heldChanged
googlePhotosChanged = _TraySignalsMixin.googlePhotosChanged
photosUploadChanged = _TraySignalsMixin.photosUploadChanged
googlePhotosProgressReported = _TraySignalsMixin.googlePhotosProgressReported
googlePhotosCurrentFileReported = _TraySignalsMixin.googlePhotosCurrentFileReported
googlePhotosUploadResultReported = _TraySignalsMixin.googlePhotosUploadResultReported
googlePhotosAuthResultReported = _TraySignalsMixin.googlePhotosAuthResultReported


class TrayStateMixin(_TraySignalsMixin):
    """A képtálca képeinek állapotát és nézeti API-ját adja."""

    #: #2039: a tálca SAJÁT kijelölése változott (nem a rácsé).
    traySelectionChanged = Signal()

    @Slot("QVariant", result=str)
    def fileUriList(self, paths) -> str:  # noqa: N802 — QML API
        """Lokális fájlútvonalak Qt-kompatibilis `text/uri-list` alakja.

        A QML `Drag.mimeData` a `text/uri-list` szöveget CRLF mentén bontja
        fel, majd a Qt `QMimeData::setUrls` útján adja át. Az URL-eket a
        közös formázó készíti, hogy az ékezetes, szóközös és `#`-es nevek
        Windowson is helyes `CF_HDROP` útvonalakká alakuljanak.
        """
        if hasattr(paths, "toVariant"):
            paths = paths.toVariant()
        urlek = []
        for path in paths or ():
            url = formatting.to_file_url(str(path or ""))
            if url.isValid() and url.isLocalFile():
                urlek.append(url.toString())
        return "\r\n".join(urlek)

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
        self._tray_records_cache: tuple[tuple[int, int], list] | None = None
        #: #1153: a tálca rekordjai a RÁCS modelljéből jönnek, de eddig
        #: csak a tálca SAJÁT változására frissültek. Egy szerkesztés (vagy
        #: bármely külső felülírás) új `mtime_ns`-t ad, tehát új
        #: bélyegkép-URL-t is — csakhogy senki nem kérte el: a `trayItems`
        #: értesítője a `heldChanged`, ami ilyenkor nem szól.
        #: Eredmény: a Klipek lapon és a tálcán a RÉGI kép maradt.
        #: ⚠️ Defenzív kötés: a QML-próbák és a komponens-tesztek
        #: teszt-kettőse (`_Photos`) nem Qt-objektum, nincs rajta jelzés.
        #: A #1227 tanulsága: az új láncszem beékelése elronthatja a régi
        #: utat, ha a kettős nem ismeri. A VALÓDI modellen a jelzés mindig
        #: megvan — a #1153 tesztje élő `AppController`-rel méri, tehát a
        #: hiánya nem maradhat észrevétlen.
        jelzes = getattr(self._photos, "revisionChanged", None)
        if jelzes is not None:
            jelzes.connect(self._tray_photos_changed)

    def _tray_photos_changed(self) -> None:
        """A rács rekordjai kicserélődtek — a tálca nézete is elavult (#1153).

        A rekord-gyorstár ürül, és jelzünk, hogy a QML-kötések újra
        kiolvassák a `trayItems`-t. ÜRES tálcánál nem jelzünk: ott nincs
        mit frissíteni, a fölösleges jelzés viszont minden háttér-szinkronnál
        újraköttetné a tálca-sávot.
        """
        if not tray.photo_ids(self._tray):
            return
        self._tray_records_cache = None
        self._tray_foreign.clear()
        self.googlePhotosChanged.emit()
        self.heldChanged.emit()

    # -- belső segédek ----------------------------------------------------

    def _tray_apply(self, state: tray.TrayState) -> None:
        """Az új állapot beállítása — jelzéssel, ha tényleg változott."""
        if state == self._tray:
            return
        self._tray = state
        self._tray_held = frozenset(tray.held_ids(state))
        self._tray_revision += 1
        self._tray_records_cache = None
        self.googlePhotosChanged.emit()
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
        cache_key = (
            self._tray_revision,
            int(getattr(self._photos, "revision", 0)),
        )
        if gyorstar is not None and gyorstar[0] == cache_key:
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
        self._tray_records_cache = (cache_key, rekordok)
        return rekordok

    # -- lekérdezések a felület felé --------------------------------------

    @Property(int, notify=heldChanged)
    def heldCount(self) -> int:
        """A tálca KÉP-elemeinek száma (a rögzített ÉS a kijelölésből
        tükrözött).

        #1919 óta a tálca összecsukott mappa-/album-tokent is tarthat; azt
        ez a szám NEM tartalmazza, mert a bélyegkép-sor ebből számol, a
        tokennek pedig saját rajza van (`trayAlbumTokens`).
        """
        self._ensure_tray_wired()
        return len(tray.photo_ids(self._tray))

    @Property("QVariant", notify=heldChanged)
    def trayAlbumTokens(self):
        """Az ÖSSZECSUKOTT mappa-/album-tokenek a nézetnek (#1919).

        Minden elem: `key`, `photoCount`, `isAlbum`, `coverThumbUrl`,
        `held`, `used`. A FELIRAT szándékosan nincs benne: azt a QML
        rakja össze `qsTr()`-rel (`TrayAlbumToken.qml`), mert a
        `CThumbUI::UpdateAlbumCover` formátum három honosított darabból
        áll össze.
        """
        self._ensure_tray_wired()
        return [
            {
                "key": token.key,
                "photoCount": token.photo_count,
                "isAlbum": token.is_album,
                "coverThumbUrl": self._tray_cover_url(
                    token.cover_photo_id, token.cover_rect
                ),
                "held": token.held,
                "used": token.used,
            }
            for token in tray.album_tokens(self._tray)
        ]

    def _tray_cover_url(self, photo_id: int | None, arc=None) -> str:
        """A token borítóképének thumb-URL-je — üres sztring, ha nincs.

        Előbb a MEMÓRIÁBAN lévő rács-modellből (nulla adatbázis-hívás),
        aztán a más mappából tartott elemek gyorstárából, és csak
        legvégül az indexből; a megtalált rekord ugyanabba a gyorstárba
        kerül, mint a máshonnan tartott képeké. Az `arc` a személy
        arcképe (#5331): ugyanaz a kivágás, mint a bal sáv sorában.
        """
        if not photo_id:
            return ""
        for record in self._photos.photos:
            if record.id == photo_id:
                return _thumb_url(record, arc=arc)
        record = self._tray_foreign.get(photo_id)
        if record is None:
            with open_index(self._db_path) as conn:
                record = photo_by_id(conn, photo_id)
            if record is None:
                return ""
            self._tray_foreign[photo_id] = record
        return _thumb_url(record, arc=arc)

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

        Csak a KÉP-elemek jelzőit gyűjti: a #1919 összecsukott
        mappa-/album-tokenje nem fotó, nincs `photos.id`-ja, azt a
        `trayAlbumTokens` kérdezi le. A szűrés nem óvatosság — nélküle a
        szótár-építés `AttributeError`-t dobott, amint token került a
        tálcára, és a Klipek lap QML-kötése futásidőben elhasalt rajta.
        """
        self._ensure_tray_wired()
        allapotok = {
            item.photo_id: item
            for item in self._tray.items
            if isinstance(item, tray.TrayItem)
        }
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

    @Slot(int, result=bool)
    def heldAtTrayIndex(self, index: int) -> bool:
        """MEGTARTOTT-e a tálca-előnézet `index`. eleme? (#1918)

        Az eredeti Picasa a megtartott képekre a `thumbui/#holdadorner`
        jelvényt rajzolja — ugyanabból az adorner-CSALÁDBÓL, mint a csillag,
        a geocímke vagy az arcfelismerés jelvénye (a `0x007145c0`-on épülő
        gyorsítótár első eleme, `0x00cad36c`).

        Nálunk a megtartás eddig CSAK SZÁMKÉNT létezett (`heldCount`), a
        képen semmi nem jelezte. A rács-cellán már megvolt a jelvény
        (#455, `holdMark`); a tálca bélyegképein nem.
        """
        rekordok = self._tray_records()
        if not 0 <= index < len(rekordok):
            return False
        return int(rekordok[index].id) in self._tray_held

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
            return formatting.photo_info_text(rekordok[0], locale, formatting.fordit)
        return formatting.status_text(rekordok, locale, formatting.fordit, self.tr)

    # -- műveletek --------------------------------------------------------

    # -- a tálca SAJÁT kijelölése (#2039) ----------------------------------
    #
    # Az eredetiben a tálca ugyanolyan `CSelectionNode`, mint a rács
    # (`picasa-keptalca.md` 13., `[ebx+0xea4]`), és a csomópont ELEMENKÉNTI
    # állapotot tárol (`+0x32c` elemtömb, elemenként `[elem+0x59]` kijelölt);
    # a tálca számlálója (`0x00716cb0`) épp ezt a jelzőt olvassa. Nálunk a
    # tálca eddig tükör volt, és a „Kijelölés eltávolítása" a RÁCSRA hatott.
    #
    # Az indexek a `trayItems` sorrendjére vonatkoznak — az a tálca saját
    # rendje, nem rács-sorindex.

    def _tray_selection_state(self) -> tuple[list[int], int | None]:
        if not hasattr(self, "_tray_selected"):
            self._tray_selected: list[int] = []
            self._tray_anchor: int | None = None
        return self._tray_selected, self._tray_anchor

    def _tray_item_count(self) -> int:
        self._ensure_tray_wired()
        return len(self._tray_records())

    def _set_tray_selection(self, kijelolt, horgony: int | None) -> None:
        db = self._tray_item_count()
        tiszta = sorted({i for i in kijelolt if 0 <= i < db})
        self._tray_selected = tiszta
        self._tray_anchor = horgony if horgony is not None and 0 <= horgony < db else None
        self.traySelectionChanged.emit()

    @Property("QVariant", notify=traySelectionChanged)
    def traySelectedIndexes(self):
        """A tálcán kijelölt elemek indexei (a `trayItems` sorrendjében)."""
        kijelolt, _ = self._tray_selection_state()
        db = self._tray_item_count()
        return [i for i in kijelolt if 0 <= i < db]

    @Slot(int, bool, bool)
    def selectTrayIndex(self, index: int, ctrl: bool = False, shift: bool = False) -> None:
        """Kattintás a tálca egy elemére.

        Args:
            index: a `trayItems` indexe.
            ctrl: hozzáad/elvesz (a rács `Ctrl`-jével azonos).
            shift: tartomány a horgonytól (a rács `Shift`-jével azonos).
        """
        db = self._tray_item_count()
        if not 0 <= index < db:
            return
        kijelolt, horgony = self._tray_selection_state()
        if shift and horgony is not None:
            eleje, vege = sorted((horgony, index))
            self._set_tray_selection(range(eleje, vege + 1), horgony)
            return
        if ctrl:
            uj = set(kijelolt)
            uj.symmetric_difference_update({index})
            self._set_tray_selection(uj, index)
            return
        self._set_tray_selection({index}, index)

    @Slot()
    def removeTraySelected(self) -> None:
        """„Kijelölés eltávolítása" (`Tray::ID_REMOVE_SELECTION`) — a
        TÁLCÁN kijelölt elemekre.

        Üres kijelöléssel nem tesz semmit: az eredetiben sincs mit
        eltávolítani, és a tálca kiürítése ennél sokkal drágább tévedés
        volna, mint a néma no-op.
        """
        self._ensure_tray_wired()
        indexek = list(self.traySelectedIndexes)
        if not indexek:
            return
        rekordok = self._tray_records()
        azonositok = [rekordok[i].id for i in indexek if 0 <= i < len(rekordok)]
        if not azonositok:
            return
        self._tray_apply(tray.without(self._tray, azonositok))
        self._set_tray_selection((), None)

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
