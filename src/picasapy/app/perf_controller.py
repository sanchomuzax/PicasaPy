"""Kapcsolható teljesítmény-monitor (#211) — az AppController vezérlő-
szelete (`library_controller.py` mintájára, ld. #150).

KIKAPCSOLT állapotban (alapértelmezés) semmi nem fut: sem a
`picasapy.perf.PerfCollector` háttérszála, sem a GUI-akadás-őr
QTimer-je, sem a sync-haladás követő kapcsolat — a `setPerfMonitorEnabled`
csak a be- és kikapcsoláskor indít/állít le bármit is."""

from __future__ import annotations

import platform
import subprocess
from pathlib import Path

from PySide6.QtCore import Property, QElapsedTimer, QTimer, Signal, Slot, qVersion

from picasapy.fileops import reveal_in_file_manager
from picasapy.perf.collector import PerfCollector, PerfSample
from picasapy.perf.logwriter import PerfLogWriter
from picasapy.version import version_string

# A mintavétel ütemezése (~1 Hz, #211 elvárt viselkedés).
_SAMPLE_INTERVAL_S = 1.0
# A GUI-akadás-őr ellenőrzési köre (mp) — QTimer-elcsúszás mérése: az
# elvárt intervallumnál hosszabb tényleges kör az event loop késleltetését
# jelzi (más munka foglalta a főszálat).
_GUI_STALL_CHECK_S = 0.2


class PerfMonitorMixin:
    """`perfMonitorEnabled` kapcsoló + élő terhelés-property-k + menthető
    diagnosztikai JSONL-log (`saveDiagnostics`)."""

    perfMonitorChanged = Signal()
    perfSampleChanged = Signal()
    # #217: a diagnosztika-mappa megnyitása sikertelen — emberi nyelvű
    # hibaüzenet a QML-nek, a syncFailed/photoOpFailed mintája szerint.
    diagnosticsFolderOpenFailed = Signal(str)
    # A PerfCollector SAJÁT (nem-Qt) háttérszáláról emittálva — a fogadó
    # (self) a GUI-szálon él, ezért a Qt automatikusan queued kézbesítéssel
    # juttatja a főszálra (ld. ThumbnailProvider.activeCountChanged minta).
    _perfSampleReady = Signal(float, int, int, str, int, int, float)

    def _init_perf_monitor(self) -> None:
        """Az AppController.__init__ hívja — a mixinek nem definiálnak
        saját __init__-et, az attribútumok itt egy dedikált inicializáló-
        metódusban jönnek létre (a konvenció a repóban)."""
        self._perf_enabled = False
        self._perf_collector: PerfCollector | None = None
        self._perf_writer = PerfLogWriter(
            app_version=version_string(), qt_version=qVersion() or ""
        )
        self._perf_cpu = 0.0
        self._perf_rss = 0
        self._perf_top = ""
        self._perf_gui_timer: QTimer | None = None
        self._perf_gui_elapsed: QElapsedTimer | None = None
        self._perf_gui_stall_ms = 0.0
        self._perf_sync_folder = ""
        self._perf_sync_done = 0
        self._perf_sync_total = 0
        self._perf_sync_connection = None
        self._perfSampleReady.connect(self._apply_perf_sample)

    # -- QML-nek kitett property-k -------------------------------------------

    @Property(bool, notify=perfMonitorChanged)
    def perfMonitorEnabled(self):
        return self._perf_enabled

    @Property(float, notify=perfSampleChanged)
    def perfCpuPercent(self):
        """A processz CPU%-a (a rendelkezésre álló magok számával
        normálva — egy egymagos 100%-os terhelés is 100%-ot mutat)."""
        return round(self._perf_cpu, 1)

    @Property(float, notify=perfSampleChanged)
    def perfRssMb(self):
        return round(self._perf_rss / (1024 * 1024), 1)

    @Property(str, notify=perfSampleChanged)
    def perfTopActivity(self):
        """Picasa-stílusú „mivel van elfoglalva" szöveg a panelnek."""
        return self._perf_top

    # -- kapcsoló -------------------------------------------------------------

    @Slot()
    def togglePerfMonitor(self) -> None:
        self.setPerfMonitorEnabled(not self._perf_enabled)

    @Slot(bool)
    def setPerfMonitorEnabled(self, enabled: bool) -> None:
        enabled = bool(enabled)
        if enabled == self._perf_enabled:
            return
        self._perf_enabled = enabled
        if enabled:
            self._start_perf_monitor()
        else:
            self._stop_perf_monitor()
        self.perfMonitorChanged.emit()

    def _start_perf_monitor(self) -> None:
        self._perf_writer.clear()
        self._perf_sync_folder = ""
        self._perf_sync_done = 0
        self._perf_sync_total = 0
        self._perf_gui_stall_ms = 0.0
        # a sync-haladást CSAK bekapcsolt állapotban követjük — kikapcsolva
        # nincs extra kapcsolat, nincs extra hook (#211 DoD). A connection-
        # objektumot tartjuk meg (nem a bound methodot) — a PySide6
        # disconnect(slot) néha nem ismeri fel ugyanazt a bound methodot.
        self._perf_sync_connection = self.syncProgress.connect(
            self._on_perf_sync_progress
        )
        self._perf_gui_elapsed = QElapsedTimer()
        self._perf_gui_elapsed.start()
        self._perf_gui_timer = QTimer(self)
        self._perf_gui_timer.setInterval(int(_GUI_STALL_CHECK_S * 1000))
        self._perf_gui_timer.timeout.connect(self._on_perf_gui_tick)
        self._perf_gui_timer.start()
        self._perf_collector = PerfCollector(
            interval=_SAMPLE_INTERVAL_S,
            activity_fn=self._perf_activity_snapshot,
            on_sample=self._on_perf_sample,
        )
        self._perf_collector.start()

    def _stop_perf_monitor(self) -> None:
        if self._perf_collector is not None:
            self._perf_collector.stop()
            self._perf_collector = None
        if self._perf_gui_timer is not None:
            self._perf_gui_timer.stop()
            self._perf_gui_timer = None
        self._perf_gui_elapsed = None
        if self._perf_sync_connection is not None:
            try:
                self.syncProgress.disconnect(self._perf_sync_connection)
            except (RuntimeError, TypeError):
                pass  # a kapcsolat már megszűnt — ártalmatlan
            self._perf_sync_connection = None
        self._perf_cpu = 0.0
        self._perf_rss = 0
        self._perf_top = ""
        self.perfSampleChanged.emit()

    # -- adatgyűjtő-hookok ------------------------------------------------

    @Slot(str, int, int, int)
    def _on_perf_sync_progress(self, folder, done, total, new_photos) -> None:
        """A meglévő `syncProgress` jelzésből (#209) — csak a mappa NEVÉT
        tartjuk meg, nem a teljes útvonalat (adatvédelem, #211 DoD).

        A top-tevékenység szövege AZONNAL frissül (nem várja meg a
        következő ~1 Hz-es mintavételt) — a szinkron-haladás így élőben
        látszik a panelen."""
        self._perf_sync_folder = Path(folder).name if folder else ""
        self._perf_sync_done = done
        self._perf_sync_total = total
        self._perf_top = self._format_top_activity(
            self._perf_sync_folder,
            self._perf_sync_done,
            self._perf_sync_total,
            getattr(self, "_thumb_active", 0),
        )
        self.perfSampleChanged.emit()

    def _on_perf_gui_tick(self) -> None:
        """GUI-akadás-őr: a QTimer elcsúszása az elvárt intervallumhoz
        képest — ha az event loop foglalt volt, a tényleges kör hosszabb
        a beállított intervallumnál."""
        if self._perf_gui_elapsed is None:
            return
        elapsed_ms = self._perf_gui_elapsed.restart()
        expected_ms = _GUI_STALL_CHECK_S * 1000
        self._perf_gui_stall_ms = max(0.0, elapsed_ms - expected_ms)

    def _perf_activity_snapshot(self) -> dict:
        """A PerfCollector SAJÁT száláról hívva: csak egyszerű attribútum-
        olvasás (int/str/float) — a GIL ezt biztonságossá teszi zár
        nélkül is, Qt-hívás itt nem történhet (nem a GUI-szál)."""
        return {
            "thumb_active": getattr(self, "_thumb_active", 0),
            # a QThreadPool nem tesz közzé várakozási sor-mélységet — az
            # aktív kérésszám az egyetlen olcsón elérhető proxy jelenleg
            "thumb_queue": 0,
            "sync_folder": self._perf_sync_folder,
            "sync_done": self._perf_sync_done,
            "sync_total": self._perf_sync_total,
            "gui_stall_ms": self._perf_gui_stall_ms,
        }

    def _on_perf_sample(self, sample: PerfSample) -> None:
        """A PerfCollector SAJÁT száláról hívva (worker) — a naplózás
        szálbiztos (a `deque` GIL alatt), a Qt-jelzés queued kézbesítéssel
        jut a GUI-szálra (`_apply_perf_sample`)."""
        self._perf_writer.record(sample)
        self._perfSampleReady.emit(
            sample.cpu_percent,
            sample.rss_bytes,
            sample.thumb_active,
            sample.sync_folder,
            sample.sync_done,
            sample.sync_total,
            sample.gui_stall_ms,
        )

    @Slot(float, int, int, str, int, int, float)
    def _apply_perf_sample(
        self, cpu_percent, rss_bytes, thumb_active, sync_folder,
        sync_done, sync_total, gui_stall_ms,
    ) -> None:
        """A GUI-szálon (queued) fut — csak itt szabad property-jelzést
        kibocsátani."""
        self._perf_cpu = cpu_percent
        self._perf_rss = rss_bytes
        self._perf_top = self._format_top_activity(
            sync_folder, sync_done, sync_total, thumb_active
        )
        self.perfSampleChanged.emit()

    @staticmethod
    def _format_top_activity(sync_folder, sync_done, sync_total, thumb_active) -> str:
        """Picasa-stílusú, ember-olvasható „mivel van elfoglalva" szöveg."""
        if sync_folder and sync_done < sync_total:
            return f"Szinkronizálás: {sync_folder} ({sync_done}/{sync_total})"
        if thumb_active > 0:
            return f"Indexkép-generálás: {thumb_active} folyamatban"
        return "Tétlen"

    # -- diagnosztika mentése -------------------------------------------------

    @Slot(result=str)
    def saveDiagnostics(self) -> str:
        """JSONL-mentés (`~/.cache/picasapy/perf/`) — a visszaadott
        útvonalat a QML jeleníti meg (#211 DoD)."""
        path = self._perf_writer.save()
        return str(path)

    @Slot(str)
    def openDiagnosticsFolder(self, path: str) -> None:
        """A mentett diagnosztika-napló mappájának megnyitása a rendszer
        fájlkezelőjében (#217) — a felhasználónak ne kelljen kézzel
        kikeresnie a `~/.cache/picasapy/perf/` utat, amikor a fájlt
        issue-hoz csatolná.

        Windowson az Intéző a fájlt kijelölve nyitja meg
        (`explorer /select,<út>`) — az Intéző ilyenkor is gyakran
        nemnulla kilépési kóddal tér vissza sikeres megnyitás esetén is,
        ezért ott csak a bináris hiányát (OSError) tekintjük hibának.
        Linuxon a #112-es mintát (`reveal_in_file_manager`, azaz
        `xdg-open` a szülőmappára) hasznosítja újra. Hiba esetén emberi
        nyelvű üzenetet jelez a `diagnosticsFolderOpenFailed` jelzésen —
        nem hal el némán."""
        if not path:
            self.diagnosticsFolderOpenFailed.emit(
                "Nincs elérhető naplófájl — előbb mentsd a diagnosztikát."
            )
            return
        try:
            if platform.system() == "Windows":
                subprocess.run(["explorer", f"/select,{path}"], check=False)
            else:
                reveal_in_file_manager(Path(path))
        except OSError as error:
            self.diagnosticsFolderOpenFailed.emit(str(error))

    # -- életciklus ------------------------------------------------------

    def shutdown(self) -> None:
        """Kilépéskor a futó monitor szálát/időzítőjét is le kell
        állítani, mielőtt a lánc (LibraryMixin.shutdown) lezárja a
        figyelőt/időzítőt — ld. az AppController öröklés-sorrendjét."""
        self._stop_perf_monitor()
        super().shutdown()
