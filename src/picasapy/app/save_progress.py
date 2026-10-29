"""A mentési folyamatjelző állapota: a futó művelet készültsége, és hogy a
visszaállítás szövegét kell-e mutatni a lebegő panelen."""


from __future__ import annotations

from PySide6.QtCore import Property, Signal


class SaveProgressMixin:
    """A közös mentés-folyamatjelző állapota és jelzései."""

    #: a lebegő folyamat-panel állapota változott
    saveProgressChanged = Signal()
    #: háttérszálból jövő haladás - Qt sorolja a GUI-szálra
    _saveProgressTick = Signal(int, int, int)  # (kész, összes, aktív?)

    def _ensure_save_progress(self) -> None:
        """Lusta állapot-inicializálás (a `BatchEffectMixin` mintája)."""
        if getattr(self, "_save_progress_wired", False):
            return
        self._save_progress_wired = True
        self._save_progress_done = 0
        self._save_progress_total = 0
        self._save_progress_active = False
        self._save_progress_reverting = False
        self._saveProgressTick.connect(self._on_save_progress_tick)
        # ⚠️ A fájl kiírása MÉG NEM láthatóság: a másolat addig nem jelenik
        # meg a rácsban, amíg az index nem tud róla, a `selectFolder` pedig
        # kizárólag az indexből olvas.
        #
        # #1539: az INDEX helyessége innentől NEM ezen a kötésen múlik. A
        # célmappát a `_save_copies` workere jelenti be fájlonként
        # (`noteOutputWritten`), a TÉNYLEGES célútvonallal.
        #
        # Miért kellett ez: a lenti kötés a LÁTOTT mappát olvassa újra. A
        # „Másolat mentése" mellett az történetesen a célmappa is, tehát
        # véletlenül jó volt - a #1527-tel érkezett „Mentés másként…"
        # viszont a fájlválasztóból BÁRHOVA mutathat, és ott a program a
        # rossz mappát frissítette. Mérve (figyelő nélkül): a más mappába
        # mentett másolat 25 s alatt sem jelent meg.
        #
        # A kötés mégis MEGMARAD, két okból: ez frissíti a felhasználó által
        # ÉPP NÉZETT mappa nézetét a művelet végén (a #1527 szándéka), és ez
        # a `saveCopyFinished` egyetlen fogyasztója - QML-oldali kezelője
        # NINCS, tehát elhagyva néma jelzés lenne belőle (#1003). Hogy a
        # befejezésnek van-e FELÜLETI visszajelzése, az önálló kérdés.
        self._ensure_output_resync_wired()
        poll = getattr(self, "_poll_current_folder", None)
        if poll is not None:
            self.saveCopyFinished.connect(lambda _done, _failed: poll())

    def _on_save_progress_tick(self, done: int, total: int, active: int) -> None:
        self._save_progress_done = done
        self._save_progress_total = total
        self._save_progress_active = bool(active)
        if not active:
            self._save_progress_reverting = False
        self.saveProgressChanged.emit()

    @Property(bool, notify=saveProgressChanged)
    def saveProgressActive(self) -> bool:  # noqa: N802 - QML-stílus
        """Látszódjon-e a mentés folyamat-panelje."""
        self._ensure_save_progress()
        return self._save_progress_active

    @Property(int, notify=saveProgressChanged)
    def saveProgressFileCount(self) -> int:  # noqa: N802 - QML-stílus
        """Hány fájlt ment a futó művelet - ettől függ, hogy a felület az
        egyes vagy a többes számú hivatalos mondatot mutatja
        (`progfile` / `progfiles`)."""
        self._ensure_save_progress()
        return self._save_progress_total

    @Property(bool, notify=saveProgressChanged)
    def saveProgressIsReverting(self) -> bool:  # noqa: N802 - QML-stílus
        """A közös folyamatjelző a fájl-visszaállítás szövegét mutassa-e."""
        self._ensure_save_progress()
        return self._save_progress_reverting

    @Property(float, notify=saveProgressChanged)
    def saveProgressPercent(self) -> float:  # noqa: N802 - QML-stílus
        """A készültség százalékban.

        ⚠️ A hivatalos formátum `%.1f%%` - EGY tizedesjegy (a #1527 jegy
        „századpontos" megfogalmazása a `%.1f`-fel nem egyezik; a
        formátumsztring az erősebb bizonyíték, azt követjük). A
        kerekítést a felület végzi, itt a nyers arány áll."""
        self._ensure_save_progress()
        if self._save_progress_total <= 0:
            return 0.0
        return 100.0 * self._save_progress_done / self._save_progress_total

