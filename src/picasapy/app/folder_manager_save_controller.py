"""A Mappakezelő OK-jának mentési szelete (#1334) — a vezérlő oldala.

Mixin-osztály: a `LibraryMixin` őse, így a slotok a végső `AppController`
meta-objektumába regisztrálódnak (a `search_controller.py` mintájára).

Az eredetiben az OK EGYETLEN mentő függvényt hív (`0x005cef20`), és az
kötött sorrendben dolgozik: `watchedfolders.txt` → `]album:removed`
sírkövek → (kapuzva) `frexcludefolders.txt` → záró lépés. Nálunk a
párbeszéd tételenként hívja a vezérlőt (mappa hozzáadása, eltávolítása,
arc-kapcsoló), és eddig MINDEN hívás azonnal írt: három mappaváltás
háromszor írta a figyelt mappák fájlját, tetszőleges sorrendben.

Ezért a párbeszéd OK-ja ZÁRÓJELBE teszi a tételes hívásokat
(`beginFolderManagerSave` … `commitFolderManagerSave`): a zárójelen belül
a fájlírások és a sírkövek nem futnak le azonnal, hanem piszkozatba
gyűlnek, és a végén EGYSZER, a mért sorrendben íródnak ki. A zárójelen
kívüli hívások (első indítás, importálás, helyi menü) viselkedése
változatlan: ott továbbra is azonnali az írás.

⚠️ A `scanlist.txt`-hez a mentési út nem nyúl (a spec 17.2 negatív
eredménye) — nálunk ez a háromállapotú választó tárhelye, amit a
`setFolderManagerState` ír, a mentési úttól függetlenül.

A magát a sorrendet és a kaput a Qt-mentes `folder_manager_save.py`
tartja; ez a fájl csak a vezérlő állapotához köti.
"""

from __future__ import annotations

import logging
import sqlite3

from PySide6.QtCore import Slot

from picasapy.index import add_removed_folder, open_index
from picasapy.scanner import write_exclude_folders, write_watched_folders

from .folder_manager_save import FolderManagerSaveDraft, save_folder_manager

logger = logging.getLogger(__name__)


class FolderManagerSaveMixin:
    """A Mappakezelő OK-fázisa: piszkozat + egyetlen, sorrendtartó mentés."""

    def _folder_manager_draft(self) -> FolderManagerSaveDraft | None:
        """A folyamatban lévő OK-mentés piszkozata (`None`, ha nincs)."""
        return getattr(self, "_fm_draft", None)

    @Slot()
    def beginFolderManagerSave(self) -> None:  # noqa: N802 — QML-konvenció
        """A Mappakezelő OK-fázisának kezdete: az írások felfüggesztése.

        Újbóli hívás (pl. két egymásba futó OK) nem nyitja meg még egyszer
        a zárójelet — a piszkozat marad, különben az első kör szándékai
        elvesznének."""
        if self._folder_manager_draft() is None:
            self._fm_draft = FolderManagerSaveDraft()

    @Slot(result="QVariantList")
    def commitFolderManagerSave(self) -> list:  # noqa: N802 — QML-konvenció
        """Az OK-fázis lezárása: EGY mentés, a mért sorrendben.

        A visszatérési érték a ténylegesen lefutott lépések neve — erre áll
        a sorrend-őr (a QML nem használja, de a `_fm_last_steps` őrzi az
        utolsó mentést). Zárójel nélküli hívás üres listát ad."""
        draft = self._folder_manager_draft()
        if draft is None:
            return []
        self._fm_draft = None
        plan = draft.to_plan(
            watched=tuple(self._roots),
            faces_excluded=tuple(self._face_excluded_roots),
        )
        try:
            steps = save_folder_manager(
                plan,
                write_watched=self._save_watched_file,
                write_tombstones=self._save_tombstones,
                write_faces=self._save_exclude_file,
                finish=self._finish_folder_manager_save,
            )
        except (OSError, sqlite3.Error) as error:
            # A mentés nem maradhat néma: a felhasználó beállítása így
            # tűnne el nyomtalanul (#1207 tanulsága).
            logger.exception("#1334: a Mappakezelő mentése megszakadt")
            self.syncFailed.emit(str(error))
            self._fm_last_steps = []
            return []
        self._fm_last_steps = list(steps)
        return self._fm_last_steps

    def _save_watched_file(self, folders: tuple[str, ...]) -> None:
        """1. lépés (`0x005cf49b`): `watchedfolders.txt`.

        Az eredeti nem kapuzza: az OK mindig kiírja a figyelt mappákat."""
        if self._watched_file is not None:
            write_watched_folders(self._watched_file, folders)

    def _save_tombstones(self, folders: tuple[str, ...]) -> None:
        """2. lépés (`0x005cf500`): a `]album:removed` sírkövek."""
        if not folders:
            return
        with open_index(self._db_path) as conn:
            for folder in folders:
                add_removed_folder(conn, folder)

    def _save_exclude_file(self, folders: tuple[str, ...]) -> None:
        """3. lépés (`0x005cf529`): `frexcludefolders.txt` — KAPUZVA.

        Ide csak akkor jutunk el, ha a hozzáadandó vagy az eltávolítandó
        lista nem üres (a kapu a `save_folder_manager`-ben van)."""
        if self._exclude_file is not None:
            write_exclude_folders(self._exclude_file, folders)

    def _finish_folder_manager_save(self) -> None:
        """4. lépés (`0x005cf535`): záró lépés — a nézet frissítése."""
        self._reload()
        self.statusChanged.emit()

    def _add_tombstone(self, path: str) -> None:
        """Sírkő egy mappára: OK-fázisban a piszkozatba, egyébként azonnal."""
        draft = self._folder_manager_draft()
        if draft is not None:
            self._fm_draft = draft.with_tombstone(path)
            return
        with open_index(self._db_path) as conn:
            add_removed_folder(conn, path)
