"""Az album-műveletek actions reszmixinje (#6273)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Slot

from picasapy.index import open_index, photos_with_keyword


class PhotoOpsAlbumActionsMixin:
    @Slot(int, result=bool)
    def setPhotoAsDesktopBackground(self, row: int) -> bool:  # noqa: N802
        """A kijelölt kép asztali háttérképnek (`eMenuCreate::ID_WALLPAPER`).

        Az eredeti (mérve, `0x0057aa10`, 1143 b) **másolatot** ír:
        `picasabackground.bmp` a `Picasa/Backgrounds` mappába — NEM az eredeti
        fájlra mutat —, majd középre teszi (`WallpaperStyle=0`,
        `TileWallpaper=0`). A másolat azért fontos, mert így a kép átnevezése
        vagy törlése nem viszi el az asztal hátterét.

        A motor közös a kollázs-ágéval (`app/wallpaper.py`, #1005): ugyanaz a
        BMP-írás, ugyanaz a beállító lánc, és ugyanaz a két visszajelzés
        (`desktopBackgroundApplied` / `desktopBackgroundFailed`) — egy hely,
        egy viselkedés.

        Visszatérés: elindult-e a művelet. Érvénytelen sorra `False`, és a
        hívó ebből tud üzenetet adni."""
        from . import collage_output as output
        from . import collage_prefs, wallpaper

        fotok = self._photos.photos
        if not 0 <= int(row) < len(fotok):
            return False
        foto = fotok[int(row)]
        forras = Path(foto.folder_path) / foto.name
        try:
            mappa = wallpaper.backgrounds_dir(
                output.output_dir(
                    self._get_settings().value(collage_prefs.OUTPUT_DIR_KEY)
                ),
                output._felulet_nyelve(),
            )
            bmp = wallpaper.write_background_bmp(forras, mappa)
        except OSError as hiba:
            self.photoOpFailed.emit(str(hiba))
            return False
        eszkoz = wallpaper.set_desktop_background(bmp)
        if eszkoz:
            self.desktopBackgroundApplied.emit(eszkoz)
        else:
            self.desktopBackgroundFailed.emit(str(bmp))
        return True

    @Slot(str, result=str)
    def showTagAsAlbum(self, tag: str) -> str:
        """Egy CÍMKE tartalmából rendes album (#1406, `ID_SEARCHTOKEN`).

        Az eredeti a színkeresés FORDÍTOTTJA: ott a menüpont a keresőmezőbe
        ír (#1399), itt a felhasználó megad egy címkét, és abból **rendes
        album** lesz — nem élő szűrő.

        A címkét tételenként egyeztetjük (`index.photos_with_keyword`), tehát
        a „nyár" címke nem húzza be a „nyaralás"-t. Üres címkére és találat
        nélküli címkére üres stringgel térünk vissza — a felület ebből tud
        üzenetet adni (néma hatástalanság helyett)."""
        cimke = (tag or "").strip()
        if not cimke:
            return ""
        with open_index(self._db_path) as conn:
            fotok = photos_with_keyword(conn, cimke)
        return self._albumot_keszit(cimke, list(fotok))

    #: figyelmeztetés.
    SAVE_SEARCH_CONFIRM_OVER = 1000

    def _mentheto_kereses(self) -> bool:
        """Menthető-e a jelenlegi nézet albumként (a `canSaveSearch` magja).

        Csak KERESÉSI nézetben él (az eredeti parancsa is az aktív keresés
        találatát mentette), és csak ha van találat — üres keresésből album
        sem lesz. A property a fővezérlőben áll, mert a `notify` jelzései
        (`statusChanged`, `feedChanged`) ott élnek.
        """
        return self._view_mode[0] in ("search", "search-folder") and bool(
            self._photos.photos
        )

    @Slot(result=str)
    def saveSearchAsAlbum(self) -> str:
        """A keresés TELJES találata új albumba (#1405).

        Az album neve a keresés szövege. ⚠️ Ez a MI döntésünk: az eredeti
        menüfelirat három pontra végződik („Save &search results..."), ami
        párbeszédet sejtet, a mért kezelő (`0x005d86a0`, 362 bájt) viszont
        CSAK az 1000 fölötti megerősítést tartalmazza — névkérő párbeszédnek
        nincs nyoma benne. A keresés szövege a legkézenfekvőbb név, és a
        felhasználó az albumot bármikor átnevezheti.

        A megerősítést a FELÜLET kéri (a küszöb fölött), mert az eredeti is
        ott kérdez; ez a slot már a döntés utáni munkát végzi. Visszatérés: az
        új album tokenje, üres stringgel jelezve, hogy nem jött létre."""
        if not self._mentheto_kereses():
            return ""
        mode, param = self._view_mode
        nev = param if isinstance(param, str) else str(param[0])
        return self.createAlbum(nev, list(range(len(self._photos.photos))))
