"""A rejtett mappák láthatósága és jelszavas védelme."""

from __future__ import annotations

import logging
from pathlib import Path
from PySide6.QtCore import Property, Slot
from picasapy.hidden_password import egyezik as jelszo_egyezik
from picasapy.hidden_password import modern_lenyomat, picasa_lenyomat
from picasapy.index import (
    hidden_folders, is_folder_hidden, open_index, set_folder_hidden,
    set_hidden_folders_visible,
)
from picasapy.ini import (
    FOLDERS_ON_DISK_CATEGORY, HIDDEN_FOLDERS_CATEGORY, load_or_empty,
)
from picasapy.index.people import FaceDataCollector
from picasapy.scanner import PICASA_INI_NAME
from . import small_picture_filter
from .confirm_settings import is_confirm_suppressed
from .contact_names import central_contacts_path
from .small_picture_filter import (
    SHOW_ONLY_BIG_IMAGES_KEY, coerce_show_only_big_images,
)
from .controller_signals import AppControllerSignalsMixin as _Signals

_log = logging.getLogger("picasapy.app.controller")


def _mappaban_megnevezett_arc(path: str, central_path=None) -> bool:
    """Van-e a mappa ini-jében megnevezett arc (#4887) — EGY ini olvasása,
    hogy a mappa elrejtése ne indítson fölöslegesen teljes Emberek-söprést."""
    gyujto = FaceDataCollector(central_path)
    try:
        gyujto(path, load_or_empty(Path(path) / PICASA_INI_NAME))
    except (OSError, ValueError):
        return True  # bizonytalan: inkább frissítsünk
    return bool(gyujto.rows)

class HiddenFoldersMixin:
    """A rejtett mappák láthatósága és jelszavas védelme."""

    @Slot(str, result=bool)
    def isFolderHidden(self, path: str) -> bool:
        """Rejtett-e a mappa — a menütétel felirata ebből vált."""
        if not path:
            return False
        with open_index(self._db_path) as conn:
            return is_folder_hidden(conn, path)

    @Slot(str)
    def toggleFolderHidden(self, path: str) -> None:
        """A „Mappa elrejtése / Megjelenítés" menütétel.

        A LEMEZEN semmit nem mozgat — csak jelöl. Elrejtés után a mappa
        eltűnik a bal hasábról, és a Nézet ▸ Rejtett képek kapcsolóval jön
        vissza (ugyanaz az út, mint a rejtett fotóknál); rejtett
        állapotban a kijelölés a mappáról lekerül, hogy ne maradjon egy
        láthatatlan mappa tartalma a rácsban."""
        if not path:
            return
        with open_index(self._db_path) as conn:
            rejtve = is_folder_hidden(conn, path)
            van_mappa = Path(path).is_dir()
            if rejtve and not van_mappa:
                # Offline mappa ini-je nem írható: a megjelenítés nem
                # engedett (a rejtett mappa nem válhat láthatóvá úgy, hogy
                # az ini még „Hidden Folders" — a Picasa újra elrejtené).
                self.folderHideFailed.emit(path, "offline-unhide")
                return
            # #4597: az igazságforrás a mappa ini-je (P2category) — előbb az
            # ini. Elrejtésnél írási hibára a mappa AZONNAL rejtett (2-es
            # jelölés, a szinkron pótolja); megjelenítésnél hibára rejtett
            # marad, és a felület jelzést kap.
            try:
                if van_mappa:
                    self._set_folder_hidden_in_ini(path, not rejtve)
            except (OSError, RuntimeError, ValueError):
                _log.warning("A mappa rejtése nem írható az ini-be: %s", path, exc_info=True)
                if rejtve:
                    self.folderHideFailed.emit(path, "write-failed-unhide")
                    return
                set_folder_hidden(conn, path, True, ini_pending=True)
                self.folderHideFailed.emit(path, "write-failed-hide")
            else:
                # Offline mappánál a rejtés az indexben vár (2), a mappa
                # visszatérésekor a szinkron beírja az ini-be.
                set_folder_hidden(
                    conn, path, not rejtve, ini_pending=not van_mappa
                )
                if van_mappa:
                    self._init_custom_collections()
                    self._set_cached_folder_category(
                        path,
                        FOLDERS_ON_DISK_CATEGORY if rejtve else HIDDEN_FOLDERS_CATEGORY,
                    )
        if not rejtve and not self.showHidden and self._current_folder == path:
            self._current_folder = ""
            self._view_mode = ("folder", "")
            self._show(())
        # #4887: a mappa képei a többi nézetből (feed, szűrők, Emberek) is
        # azonnal tűnjenek el / térjenek vissza. Az Emberek-lista teljes
        # ini-söprést kér (NAS-on drága) — csak akkor, ha a mappában van
        # megnevezett arc, tehát a darabszám egyáltalán változhat.
        self._rejtett_lathatosag_valtozott(
            emberek=_mappaban_megnevezett_arc(
                path, central_contacts_path(self._db_path)
            )
        )
        # #5704: a kérdés csak az elrejtés után jelenik meg. A felfedés és a
        # Nézet → Rejtett képek kapcsoló nem indítja el ezt az ajánlatot.
        if (
            not rejtve
            and not self.hiddenPasswordSet
            and not is_confirm_suppressed(
                self._get_settings(), "DoNotConfirmHiddenPwd"
            )
        ):
            self.hiddenPasswordOfferRequested.emit()

    def _rejtett_lathatosag_kozlese(self) -> None:
        """#4887: a tényleges `showHidden` közlése az indexszel — EZ az egy
        pont, ahonnan a rejtett mappák képeinek láthatósága minden
        lekérdezéshez eljut (keresés, szűrők, Emberek, idővonal, albumok,
        térkép, diavetítés, képernyővédő; ld. `index/hidden_scope.py`)."""
        set_hidden_folders_visible(self._db_path, self.showHidden)

    def _rejtett_lathatosag_valtozott(self, *, emberek: bool = True) -> None:
        """A tényleges `showHidden` (kapcsoló, jelszó, feloldás) változása
        után: közlés az indexszel, majd minden ebből élő nézet frissítése."""
        self._rejtett_lathatosag_kozlese()
        self._refresh_view()
        self._reload_folders()
        self._gyujtemenyek_ujrarajzolasa()
        # Az Emberek névsor-darabszámai is a láthatóságot követik
        if emberek:
            with open_index(self._db_path) as conn:
                self._load_people(conn)
        # A tálca a más mappából tartott képeket gyorstárazza — ürüljön,
        # hogy a rejtett mappa képe az exportba/kollázsba se jusson be
        if getattr(self, "_tray_wired", False):
            self._tray_photos_changed()
        self.statusChanged.emit()

    def _hidden_folder_paths(self) -> frozenset[str]:
        """A hasábokból kiszűrendő rejtett mappák (#4597): üres, ha a
        rejtettek megjelenítése be van kapcsolva."""
        if self.showHidden:
            return frozenset()
        with open_index(self._db_path) as conn:
            return frozenset(hidden_folders(conn))

    def _folder_is_hidden(self, folder_path: str) -> bool:
        with open_index(self._db_path) as conn:
            return is_folder_hidden(conn, folder_path)

    def _gyujtemenyek_ujrarajzolasa(self) -> None:
        """Az egyéni gyűjtemények és a Projektek listája is a rejtettséget
        követi — mindkettő a `folders.hidden`-ből szűr."""
        self.customCollectionsChanged.emit()
        self.projectFoldersChanged.emit()

    # -- rejtett képek (#17) -------------------------------------------------

    # -- a rejtettek JELSZÓ-kapuja (#1637) -----------------------------------
    #
    # A tulajdonos döntése (2026-09-03): a Picasa-kompatibilis (hex MD5) és a
    # modern (sózott PBKDF2) alak EGYÜTT él, az ellenőrzés mindkettőt
    # elfogadja — így egy Picasában beállított jelszó nem zárja ki a
    # felhasználót, és az átállás fokozatos lehet.
    #
    # ⚠️ Ez a kapu a MEGJELENÍTÉST zárja, nem a fájlokat: a rejtett mappák a
    # lemezen változatlanul ott vannak. A felület ezt mondja ki.

    _HIDDEN_PWD_KEY = "view/hiddenPasswordHash"

    # #1476: SIMA Python-tulajdonság, nem `Property` — a QML-nek a
    # `hiddenPasswordSet` logikai válasza kell, a LENYOMAT maga nem való a
    # felületre. Qt-Propertyként a képesség-őr joggal jelezné szakadásnak.
    @property
    def hiddenPasswordHash(self) -> str:
        """A tárolt lenyomat (sosem a nyílt jelszó); üres, ha nincs jelszó."""
        return str(self._get_settings().value(self._HIDDEN_PWD_KEY, "") or "")

    @Property(bool, notify=_Signals.statusChanged)
    def hiddenPasswordSet(self) -> bool:
        """Van-e egyáltalán beállított jelszó."""
        return bool(self.hiddenPasswordHash)

    # #1476: nem `Slot` — a felület a `setHiddenPassword`-öt hívja, ez a
    # NYERS lenyomat útja (átvétel, teszt). A QML-nek nincs dolga vele.
    def adoptHiddenPasswordHash(self, hash_value: str) -> None:
        """Picasából átvett lenyomat (#4597): csak ha még nincs jelszónk —
        a meglévőt az átvétel sosem írja felül."""
        if not self.hiddenPasswordHash:
            self.setHiddenPasswordHash(hash_value)

    def setHiddenPasswordHash(self, hash_value: str) -> None:
        """A LENYOMAT közvetlen beállítása (import, teszt). A feloldás
        állapotát nullázza — új jelszó után újra kérni kell."""
        self._get_settings().setValue(self._HIDDEN_PWD_KEY, str(hash_value))
        self.lockHidden()

    @Slot(str, bool, result=bool)
    def setHiddenPassword(self, password: str, modern: bool = False) -> bool:
        """Jelszó beállítása a választott alakban.

        Args:
            password: a nyílt jelszó — NEM tárolódik, csak a lenyomata.
            modern: `True`-nál sózott PBKDF2 (a windowsos Picasa nem nyitja),
                `False`-nál a Picasa-kompatibilis hex MD5.
        """
        if self.hiddenPasswordSet or not password:
            return False
        keszit = modern_lenyomat if modern else picasa_lenyomat
        self.setHiddenPasswordHash(keszit(password))
        return True

    @Slot(str, result=bool)
    def verifyHiddenPassword(self, password: str) -> bool:  # noqa: N802
        """A Rejtett mappák jelszavának ellenőrzése mellékhatás nélkül."""
        return jelszo_egyezik(self.hiddenPasswordHash, password)

    @Slot(str, str, bool, result=bool)
    def changeHiddenPassword(  # noqa: N802
        self,
        current_password: str,
        password: str,
        modern: bool = False,
    ) -> bool:
        """A rejtettmappa-jelszó cseréje csak a jelenlegi jelszóval."""
        if not self.verifyHiddenPassword(current_password) or not password:
            return False
        keszit = modern_lenyomat if modern else picasa_lenyomat
        self.setHiddenPasswordHash(keszit(password))
        return True

    @Slot(str, result=bool)
    def clearHiddenPassword(self, current_password: str = "") -> bool:
        """Jelszó törlése; beállított védelemhez a jelenlegi jelszó kell."""
        if self.hiddenPasswordSet and not self.verifyHiddenPassword(current_password):
            return False
        self._get_settings().remove(self._HIDDEN_PWD_KEY)
        self.lockHidden()
        return True

    @Slot(str, result=bool)
    def unlockHidden(self, password: str) -> bool:
        """Feloldás a beírt jelszóval. Csak a munkamenetre szól."""
        if jelszo_egyezik(self.hiddenPasswordHash, password):
            elotte = self.showHidden
            self._hidden_unlocked = True
            # #4887: ha a kapcsoló már be volt kapcsolva, a feloldás azonnal
            # láthatóvá teszi a rejtett mappák képeit
            if self.showHidden != elotte:
                self._rejtett_lathatosag_valtozott()
            else:
                self.statusChanged.emit()
            return True
        return False

    # #1476: nem `Slot` — a visszazárást a jelszó beállítása és törlése
    # végzi, magától. A felületről NEM hívható, mert az eredeti Picasában
    # sincs „zárd vissza most" parancs; ha egyszer mérve lesz, kaphat.
    def lockHidden(self) -> None:
        """Visszazárás: a kapcsoló is visszaáll, hogy a rejtettek eltűnjenek."""
        elotte = self.showHidden
        self._hidden_unlocked = False
        if self._show_hidden_setting():
            self._get_settings().setValue("view/showHidden", False)
        if elotte:
            self._rejtett_lathatosag_valtozott()
            return
        self._rejtett_lathatosag_kozlese()
        self._gyujtemenyek_ujrarajzolasa()
        self.statusChanged.emit()

    @Property(bool, notify=_Signals.statusChanged)
    def hiddenUnlocked(self) -> bool:
        """Fel van-e oldva EBBEN a munkamenetben."""
        return bool(getattr(self, "_hidden_unlocked", False))

    def _show_hidden_setting(self) -> bool:
        """A TÁROLT kapcsoló (újraindítás után is megmarad)."""
        value = self._get_settings().value("view/showHidden", "false")
        return value in (True, "true", "1")

    @Property(bool, notify=_Signals.statusChanged)
    def showHidden(self):
        """Nézet → Rejtett képek: látszanak-e a rejtettek (halványítva).

        TÉNYLEGES érték (#4597): a tárolt kapcsoló csak akkor számít, ha nincs
        jelszó, vagy ebben a munkamenetben fel van oldva — a feloldás nem
        marad meg újraindítás után, a kapcsoló viszont igen."""
        return self._show_hidden_setting() and (
            not self.hiddenPasswordSet or self.hiddenUnlocked
        )

    @Property(bool, notify=_Signals.statusChanged)
    def showOnlyBigImages(self):  # noqa: N802 — QML-konvenció
        """A könyvtári rács csak a Picasa szerint nagy képeket mutassa-e."""
        value = self._get_settings().value(
            SHOW_ONLY_BIG_IMAGES_KEY, small_picture_filter.DEFAULT_SHOW_ONLY_BIG_IMAGES
        )
        return coerce_show_only_big_images(value)

    @Slot(bool)
    def setShowOnlyBigImages(self, show: bool) -> None:  # noqa: N802
        """A `Show only big images` választás mentése és a rács frissítése."""
        show = bool(show)
        if show == self.showOnlyBigImages:
            return
        self._get_settings().setValue(SHOW_ONLY_BIG_IMAGES_KEY, show)
        self._refresh_view()
        self.statusChanged.emit()

    @Slot(bool)
    def setShowHidden(self, show: bool) -> None:
        # #1637/2: a bal hasábot IS újra kell tölteni. A #1637 első köre a
        # rejtett MAPPÁKAT is erre a kapcsolóra bízta, de itt csak a rács
        # frissült — a mappa így csak egy későbbi, más okból kiváltott
        # újratöltéskor bukkant elő. A kapcsoló látszólag működött (a
        # rejtett KÉPEK azonnal megjelentek), ezért maradt észrevétlen.
        # #1637: ha van beállított jelszó, a bekapcsolás CSAK feloldás után
        # mehet — enélkül a kapu csak látszólag zárna.
        if show and self.hiddenPasswordSet and not self.hiddenUnlocked:
            self.statusChanged.emit()
            return
        self._get_settings().setValue("view/showHidden", bool(show))
        self._rejtett_lathatosag_valtozott()

    @Slot()
    def toggleShowHidden(self) -> None:
        self.setShowHidden(not self.showHidden)
