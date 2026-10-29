"""Összecsukott mappa-, album- és személytokenek a képtálcában."""

from __future__ import annotations

from PySide6.QtCore import Slot

from picasapy import tray
from picasapy.index import open_index, photos_in_folder
from picasapy.index.albums import album_photos
from picasapy.ini.albums import with_album

from .tray_state_controller import _TraySignalsMixin


class TrayAlbumMixin(_TraySignalsMixin):
    """A tálca összecsukott album- és személytoken-műveletei."""

    # -- összecsukott mappa-/album-token (#1919) ---------------------------
    #
    # Az eredetiben ez nem parancs: a `scratch/album` réteg állapot-
    # küldöttet kap (`0x00572ba4`), és annak `0x00563530` függvénye MINDEN
    # frissítéskor újraértékeli — a token akkor látszik, ha van
    # album-/mappa-kijelölés, annak van eleme, ÉS a kép-kijelölés üres.
    # A levezetés a `tray.with_album_token` docstringjében áll.
    #
    # #2741: a szabály BE VAN kötve, de csak az ALBUM-kijelölésre — a
    # `showSelectedAlbumToken` alatt áll a levezetés. A megnyitott mappára
    # szándékosan NEM: nálunk a „mappa-kijelölés" a megnyitott mappa, és a
    # szó szerinti átvétel a tálca MINDENNAPI kinézetét írná át (a
    # mappanézetben szinte mindig üres a kép-kijelölés).
    #
    # A kézi belépő (`collapseFolderIntoTray`) megmarad: az `held` tokent
    # tesz ki, amit a szabály nem söpörhet el.

    @Slot(str, result=bool)
    def collapseFolderIntoTray(self, folder_path: str) -> bool:
        """Egy egész mappát ÖSSZECSUKVA tesz a tálcára, egyetlen tokenként.

        A token a mappa fotóinak SZÁMÁT hordozza és az első fotóját
        borítóként (`scratch/albumcover`) — a felirat ebből épül fel a
        nézetben („Kiválasztott mappa - 82 fotó").

        A token MEGTARTOTT (`held=True`): egy egész mappa összecsukása
        szándékos gyűjtés, amit a következő kijelölés ne söpörjön el —
        ugyanaz az elv, mint a „Kijelölés megtartása" gombnál.

        `False`, ha a mappa nem szerepel az indexben vagy üres: üres
        tokent nem teszünk ki, mert az a felületen üres dobozként jelenne
        meg, és semmit nem mondana.
        """
        self._ensure_tray_wired()
        if not folder_path:
            return False
        try:
            with open_index(self._db_path) as conn:
                rekordok = photos_in_folder(conn, folder_path)
        except OSError as hiba:
            raise RuntimeError(
                f"a mappa fotói nem olvashatók az indexből: {folder_path}"
            ) from hiba
        if not rekordok:
            return False
        self._tray_apply(
            tray.with_album_token(
                self._tray,
                tray.TrayAlbumToken(
                    key=str(folder_path),
                    photo_count=len(rekordok),
                    cover_photo_id=int(rekordok[0].id),
                    held=True,
                ),
            )
        )
        return True

    @Slot(str, result=bool)
    def showSelectedAlbumToken(self, album_token: str) -> bool:
        """Az ALBUM-kijelölés tokenje — a mért szabály kimenete (#2741).

        A felület a mért feltétel két bemenetét figyeli (`TrayBar.qml`):
        a token akkor jár ki, ha **van album-kijelölés** ÉS a
        **kép-kijelölés üres**. Ez a slot a döntés EREDMÉNYÉT hajtja végre:

        * `album_token` üres → az automatikus token lekerül;
        * különben az adott album tokene kerül ki, a korábbi automatikus
          token HELYÉRE (két album-token egyszerre nem állhat kint).

        ⚠️ Az automatikus token **NEM `held`** — ettől söpri el a következő
        kép-kijelölés magától (`tray.with_selection`), pontosan úgy, ahogy
        az eredetiben a bélyegképek átveszik a helyét. A kézzel
        összecsukott mappa tokenje (`collapseFolderIntoTray`) ezzel szemben
        `held`, tehát azt sem ez a slot, sem a kijelölés nem viszi el.

        `False`, ha nem került ki token (üres kérés, vagy az album üres /
        ismeretlen — üres tokent nem teszünk ki, az a felületen üres
        dobozként jelenne meg).
        """
        self._ensure_tray_wired()
        allapot = self._tray_nelkul_auto_token()
        if not album_token:
            self._tray_apply(allapot)
            return False
        try:
            with open_index(self._db_path) as conn:
                rekordok = album_photos(conn, album_token)
        except OSError as hiba:
            raise RuntimeError(
                f"az album képei nem olvashatók az indexből: {album_token}"
            ) from hiba
        if not rekordok:
            self._tray_apply(allapot)
            return False
        self._tray_apply(
            tray.with_album_token(
                allapot,
                tray.TrayAlbumToken(
                    key=str(album_token),
                    photo_count=len(rekordok),
                    cover_photo_id=int(rekordok[0].id),
                    is_album=True,
                    held=False,
                ),
            )
        )
        return True

    @Slot(str, result=bool)
    def showSelectedPersonToken(self, person_name: str) -> bool:
        """A SZEMÉLY-album tokenje (#5331): ugyanaz a szabály, mint az
        albumnál (`showSelectedAlbumToken`), csak a fotókat a személy adja.

        A darabszám és a borító a bal sáv sorának adata (`_szemely_tokenadat`),
        így a két szám mindig egyezik. `False`, ha nem került ki token
        (üres név, vagy a személy nincs a listában).
        """
        self._ensure_tray_wired()
        allapot = self._tray_nelkul_auto_token()
        if not person_name:
            self._tray_apply(allapot)
            return False
        try:
            with open_index(self._db_path) as conn:
                darab, photo_id, rect = self._szemely_tokenadat(conn, person_name)
        except OSError as hiba:
            raise RuntimeError(
                f"a személy arcképe nem olvasható az indexből: {person_name}"
            ) from hiba
        if darab <= 0:
            self._tray_apply(allapot)
            return False
        self._tray_apply(
            tray.with_album_token(
                allapot,
                tray.TrayAlbumToken(
                    key=str(person_name),
                    photo_count=darab,
                    cover_photo_id=photo_id,
                    cover_rect=rect,
                    is_album=True,
                    held=False,
                ),
            )
        )
        return True

    def _tray_nelkul_auto_token(self):
        """A tálca állapota az AUTOMATIKUS album-tokenek nélkül (#2741).

        Az automatikus tokent a `held is False` ismeri fel — a kézi
        összecsukás (#1919) `held=True`-t tesz ki, azt tehát meghagyjuk."""
        allapot = self._tray
        for token in tray.album_tokens(allapot):
            if not token.held:
                allapot = tray.without_album_token(allapot, token.key)
        return allapot

    # Python-oldali modellművelet. Az eredeti tálca-token állapotból jelenik
    # meg, és a képkijelölés magától eltávolítja; nincs hozzá külön QML-akció.
    def expandFolderInTray(self, key: str) -> bool:
        """Az összecsukott token eltávolítása a tálcáról, kulcs szerint.

        `True`, ha tényleg volt ilyen token — így a hívó meg tudja
        különböztetni a „nem volt mit kivenni" esetet.
        """
        self._ensure_tray_wired()
        volt = any(
            token.key == key for token in tray.album_tokens(self._tray)
        )
        if volt:
            self._tray_apply(tray.without_album_token(self._tray, key))
        return volt

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

