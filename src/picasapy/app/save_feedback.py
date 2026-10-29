"""A lemezművelet utáni visszajelzés: a kész mentés, visszaállítás és az
utána frissülő nézet (indexfrissítés, szerkesztő-újratöltés)."""


from __future__ import annotations

import logging
import os
from pathlib import Path

from PySide6.QtCore import Property, Signal, Slot


class SaveFeedbackMixin:
    """A három lemezművelet (mentés, visszaállítás, visszavonás) végének jelzései."""

    #: (sikeres, sikertelen) - a művelet végén EGY összegzés
    saveFinished = Signal(int, int)
    revertFinished = Signal(int, int)
    undoSaveFinished = Signal(int, int)
    diskOperationSucceededPaths = Signal(list)

    def _ensure_disk_operation_feedback_wired(self) -> None:
        """A három lemezművelet végén a GUI-szál frissítse a nézetet."""
        if getattr(self, "_disk_operation_feedback_wired", False):
            return
        self._disk_operation_feedback_wired = True
        self.diskOperationSucceededPaths.connect(
            self._refresh_editors_for_disk_operation
        )
        self.saveFinished.connect(self._on_disk_operation_finished)
        self.revertFinished.connect(self._on_disk_operation_finished)
        self.undoSaveFinished.connect(self._on_disk_operation_finished)

    @Slot(list)
    def _refresh_editors_for_disk_operation(self, paths: list[str]) -> None:
        """A sikeresen módosított, éppen nyitott képek munkamenetét újratölti.

        A mentés/visszaállítás az ini-láncot is megváltoztatja, miközben a
        néző szerkesztője külön, memóriában tartott munkamenetet használ. A
        könyvtármodell frissítése önmagában nem érvényteleníti ezt az
        előnézetet, így a felhasználó továbbra is a lemezművelet előtti
        állapotot látná. Csak a ténylegesen módosított útvonalhoz tartozó,
        lemezről dolgozó szerkesztőket indítjuk újra; az „aa" mód memóriás
        második felét érintetlenül hagyjuk.
        """
        def normalizal(utvonal: str | Path) -> str:
            return os.path.normcase(
                os.path.normpath(str(Path(utvonal).resolve(strict=False)))
            )

        modosultak = {normalizal(path) for path in paths}
        if not modosultak:
            return
        for editor in getattr(self, "_edit_controllers", ()):
            utvonal = getattr(editor, "_image_path", None)
            foto_id = getattr(editor, "_photo_id", "")
            if (
                utvonal is None
                or not foto_id
                or getattr(editor, "_memory_only", False)
                or normalizal(utvonal) not in modosultak
            ):
                continue
            editor.beginEdit(foto_id, str(utvonal))

    #: #5206: a megőrzött eredetik léte változhatott (a „Visszaállítás" tétel)
    savedBackupChanged = Signal()
    _saved_backup_revision = 0

    @Property(int, notify=savedBackupChanged)
    def savedBackupRevision(self) -> int:  # noqa: N802 - QML-stílus
        """Léptetett számláló: egy befejezett mentés vagy visszaállítás után nő.

        A `hasSavedBackup` a lemezt nézi, a QML-kötés a Python-hívást nem
        látja. A kötés ezt a számlálót olvassa, így a befejezés után
        újraértékelődik (#5206).
        """
        return self._saved_backup_revision

    @Slot(int, int)
    def _on_disk_operation_finished(self, done: int, failed: int) -> None:
        """A jelzés után az aktuális nézetet a friss indexhez igazítja."""
        if done > 0 or failed > 0:
            self._refresh_view()
            self._saved_backup_revision += 1
            self.savedBackupChanged.emit()

    def _resync_disk_operation_folders(self, paths: list[Path]) -> None:
        """A sikeresen módosított képek mappáit indexelje újra egyszer."""
        folders = sorted({str(path.parent) for path in paths})
        if not folders:
            return
        from picasapy.index import open_index

        try:
            with open_index(self._db_path) as conn:
                for folder in folders:
                    self._sync_tree(conn, folder)
        except Exception as error:  # noqa: BLE001 - az írás már sikerült
            logging.getLogger(__name__).exception(
                "a mentés utáni indexfrissítés nem sikerült"
            )
            self.syncFailed.emit(str(error))

