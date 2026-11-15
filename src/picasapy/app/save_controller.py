"""Mentés a lemezre / Visszaállítás / Utolsó mentés visszavonása (#444).

A nem-destruktív modell magja (`picasapy.edit.save`) régóta megvan és
tesztelt - de a felületen **nem volt elérhető**: a Fájl menü „Mentés",
„Visszaállítás" pontjai helyfoglalók voltak. Ez a szelet köti be őket.

A Picasa NÉGY külön műveletet ismer (a jegy szerint, a bináris
sztringjeiből):

| művelet | mire hat |
|---|---|
| **Mentés** | a lemezen lévő fájlra - előtte biztonsági másolat készül |
| **Visszaállítás** | a lemezen lévő fájlra - az eredeti jön vissza, a szerkesztések ELVESZNEK |
| **Utolsó mentés visszavonása** | csak az utolsó lemezre írásra - a szerkesztések MEGMARADNAK |
| **Összes szerkesztés visszavonása** | csak a `filters=` láncra (ez a #465-ben már megvan) |

**A #484-es rangsor kiemelt pontja:** a mentés **véglegesen eldobja** azt a
láncelemet, amit nem tudunk renderelni - a beégetett képbe az nem kerül
bele. A teljes lánc az eredeti-mappa ini-jében megmarad az „Undo Save"
művelethez. Ezért a mentés előtt a hívó a
`unrenderableFiltersIn()`-nel megkérdezheti, van-e ilyen, és
figyelmeztetheti a felhasználót. Ez NEM elméleti kockázat: a „Régi
effektek" fülön (#571) ma is látszanak olyan nevek, amikhez nincs
renderelőnk, és egy régi `.picasa.ini` bármikor hozhat ilyet.
"""


# A régi importútvonal (`from picasapy.app.save_controller import ...`) marad
# érvényes: a nevek itt vannak akkor is, ha ez a modul maga nem használja őket.
# ruff: noqa: F401
from __future__ import annotations

import logging
import os
import threading
import time
from pathlib import Path

from picasapy.lazy_cv2 import cv2
import numpy as np
from PySide6.QtCore import Property, QMetaObject, Qt, Signal, Slot, QUrl

from picasapy.cvimage import read_image_bytes
from picasapy.edit.save import SaveError, revert, save_edited, undo_save
from picasapy.edit.save_copy import (
    FileNameCollisionError,
    next_copy_path,
    save_copy,
)
from picasapy.edit.session import EditSession
from picasapy.ini import IniConflictError, IniSaveError, PhotoCropReader
from picasapy.lazy_import import lazy_callable
from picasapy.halozati_ut import halozati_gyoker
from picasapy.scanner import PICASA_INI_NAME

from .paint_mask import maszk_vonasokbol, van_mentett_ecsetvonas
from .save_error_kind import save_error_code, save_error_kind
from .worker_thread import BackgroundWorkerMixin
from .save_as_copy import SaveCopyMixin
from .save_errors import _FAILED_DETAILS_LIMIT, _SAVE_ERRORS, SaveErrorMixin
from .save_external_change import SaveExternalChangeMixin
from .save_feedback import SaveFeedbackMixin
from .save_progress import SaveProgressMixin
from .save_render import _CROP_READER, _render_for_save
from .save_restore import SaveRestoreMixin
from .save_rows import SaveRowsMixin

# #6688: a render csomag az első mentésig nem töltődik be; a nevek a régi
# importútvonalon (és a tesztek foltozásához) megmaradnak.
apply_filters = lazy_callable("picasapy.render.chain", "apply_filters")
can_render_filter = lazy_callable("picasapy.render.chain", "can_render_filter")
normalize_crop_ops = lazy_callable("picasapy.render.chain", "normalize_crop_ops")
apply_flip = lazy_callable("picasapy.render.flip", "apply_flip")

_BACKUP_CACHE_TTL_S = 2.0
_BACKUP_CACHE_LOCK = threading.Lock()


def _konyvtar_tartalma(konyvtar: Path) -> list[Path]:
    """Az eredeti-mappa egyszeri listázása - külön függvény, hogy a teszt
    MEGSZÁMOLHASSA (#1146), a globális `Path.glob` átírása nélkül (#1375).

    A `monkeypatch.setattr(Path, "glob", figyelo)` alak a `pathlib.Path`
    OSZTÁLYT írja át: a számláló a teszt idejére a folyamat MINDEN
    mappalistázását felvenné, tehát a „100 képre egy listázás" állítás nem
    is csak erről a vezérlőről szólna."""
    return list(konyvtar.glob("*"))


class SaveMixin(
    SaveFeedbackMixin,
    SaveProgressMixin,
    SaveErrorMixin,
    SaveRowsMixin,
    SaveCopyMixin,
    SaveRestoreMixin,
    SaveExternalChangeMixin,
    BackgroundWorkerMixin,
):
    """A Fájl menü mentés-műveletei a kijelölt képekre.

    A részek a `save_*.py` modulokban élnek; ez az osztály köti össze őket, és
    ezt a nevet importálja a `controller.py`.
    """

    @Slot(list, result=bool)
    def hasSavedBackup(self, rows) -> bool:  # noqa: N802 - QML-stílus
        """Van-e a kijelölésben olyan kép, amit MÁR mentettünk egyszer.

        Ettől függ, hogy a „Visszaállítás" és az „Utolsó mentés
        visszavonása" egyáltalán értelmes-e (mentetlen képnél nincs mit
        visszaállítani) - a menü ezzel tiltja a pontjait. A mentés-előtti
        másolat KÉT mappanév alatt lehet (`.picasaoriginals`, `Originals`);
        ld. `picasapy.edit.save` „Két mappanév" szakaszát (#1425).
        """
        from picasapy.edit.save import ORIGINALS_DIR_NAMES

        # ⚠️ #1146: MAPPÁNKÉNT nézünk a lemezre, nem képenként. A régi ág
        # soronként hívott `is_dir()`-t ÉS `glob()`-ot - 2 002 soros
        # kijelölésnél 10 010 `stat()` EGYETLEN billentyűleütésre. A
        # tulajdonos gyűjteménye hálózati megosztáson van, ahol minden
        # `stat()` egy hálózati kör: ott ez nem lassulás, hanem fagyás.
        #
        # Egy mappa eredeti-mappáit elég EGYSZER kilistázni; a tőnevek
        # halmazából utána memóriából válaszolunk.
        #
        # #1425: MINDKÉT mappanevet nézzük - a mai `.picasaoriginals`-t és a
        # 2009 előtti, látható `Originals`-t. A régi név a tulajdonos
        # gyűjteményében 127 mappában előfordul; enélkül a „Visszaállítás"
        # menütétel ott szürke maradna, magyarázat nélkül.
        tovek: dict[str, set[str]] = {}
        remote: dict[str, list[str]] = {}
        for record in self._selected_records(rows):
            mappa = str(record.folder_path)
            if halozati_gyoker(mappa) is not None:
                remote.setdefault(mappa, []).append(str(record.name))
                continue
            if mappa not in tovek:
                nevek: set[str] = set()
                for dir_name in ORIGINALS_DIR_NAMES:
                    konyvtar = Path(mappa) / dir_name
                    if konyvtar.is_dir():
                        nevek.update(
                            utvonal.name
                            for utvonal in _konyvtar_tartalma(konyvtar)
                        )
                tovek[mappa] = nevek
            to = Path(record.name).stem
            if any(nev.startswith(to) for nev in tovek[mappa]):
                return True

        if not remote:
            return False
        cache = getattr(self, "_network_backup_cache", None)
        if cache is None:
            cache = {}
            self._network_backup_cache = cache
            self._network_backup_pending = set()
        now = time.monotonic()
        result = False
        refresh = []
        with _BACKUP_CACHE_LOCK:
            for folder, photo_names in remote.items():
                cached = cache.get(folder)
                if cached is None or now - cached[1] >= _BACKUP_CACHE_TTL_S:
                    refresh.append(folder)
                if cached is not None:
                    names = cached[0]
                    if any(
                        any(name.startswith(Path(photo_name).stem) for name in names)
                        for photo_name in photo_names
                    ):
                        result = True
            refresh = [
                folder for folder in refresh
                if folder not in self._network_backup_pending
            ]
            self._network_backup_pending.update(refresh)

        if refresh:
            def worker() -> None:
                updates = {}
                for folder in refresh:
                    names: set[str] = set()
                    try:
                        for dir_name in ORIGINALS_DIR_NAMES:
                            originals = Path(folder) / dir_name
                            if originals.is_dir():
                                names.update(
                                    path.name for path in _konyvtar_tartalma(originals)
                                )
                    except OSError:
                        # Nem elérhető megosztásnál az eredmény üres marad;
                        # a rövid cache TTL után a következő QML-kérés újrapróbálja.
                        pass
                    updates[folder] = (frozenset(names), time.monotonic())
                with _BACKUP_CACHE_LOCK:
                    self._network_backup_cache.update(updates)
                    self._network_backup_pending.difference_update(refresh)
                QMetaObject.invokeMethod(
                    self,
                    "_notify_network_backup_cache_changed",
                    Qt.ConnectionType.QueuedConnection,
                )

            self._start_background(worker, name="picasapy-backup-check", busy=False)
        return result

    @Slot()
    def _notify_network_backup_cache_changed(self) -> None:
        """A hálózati eredeti-mappák újraolvasása után frissíti a QML-kötéseket."""
        self._saved_backup_revision += 1
        self.savedBackupChanged.emit()

    @Slot(list)
    def saveRowsToDisk(self, rows) -> None:  # noqa: N802 - QML-stílus
        """„Mentés" (Ctrl+S): a szerkesztések BEÉGETÉSE a fájlokba.

        Minden mentés előtt biztonsági másolat készül (az eredeti a
        `.picasaoriginals`-ba, plusz mentésenként egy sorszámozott
        pillanatkép az „Utolsó mentés visszavonása" számára).

        A `save_edited` itt, ezen a modulon át kapja meg a háttérszál: a
        tesztek így pótolhatják (#4440).
        """
        self._start_row_save(rows, save_edited)

    @Slot(list)
    def revertRowsToOriginal(self, rows) -> None:  # noqa: N802 - QML-stílus
        """„Visszaállítás": az eredeti visszamásolása a biztonsági
        mentésből - a szerkesztések ELVESZNEK (a felület ezért kérdez rá az
        eredeti szövegével)."""
        self._run_restore(
            rows, revert, self.revertFinished, show_restore_progress=True
        )

    @Slot(list)
    def undoLastSave(self, rows) -> None:  # noqa: N802 - QML-stílus
        """„Utolsó mentés visszavonása": a legutóbbi lemezre írás előtti
        állapot jön vissza, de a **szerkesztések megmaradnak** - ez a Picasa
        köztes fokozata a Mentés és a Visszaállítás között."""
        self._run_restore(rows, undo_save, self.undoSaveFinished)
