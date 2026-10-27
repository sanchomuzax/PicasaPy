"""Arc-lenyomatok számítása és csoportosítása."""

from __future__ import annotations

from .face_scan_controller_signals import FaceScanControllerSignalsMixin as _Signals
from .face_scan_controller_shared import (
    Property,
    Slot,
    _log,
    cluster_step_to_threshold,
    faces_missing_embedding,
    group_unnamed_faces,
    model_download,
    open_index,
    rescale_face_detection,
    step_to_threshold,
    store_embedding,
    threading,
)


class FaceScanControllerEmbeddingMixin:
    """Arc-lenyomatok számítása és csoportosítása."""


    @Property(int, notify=_Signals.sortingPercentChanged)
    def sortingPercent(self) -> int:  # noqa: N802 — QML-property-stílus
        """#4586: az arc-lenyomatok számításának haladása (0–100), −1 ha nem
        fut (`PeoplePanel::SortingData`)."""
        return self._sorting_percent


    def _set_sorting_percent(self, percent: int) -> None:
        if percent != self._sorting_percent:
            self._sorting_percent = percent
            self.sortingPercentChanged.emit()


    @Slot()
    def computeEmbeddings(self) -> None:
        """Lenyomat-számítás (SFace) a még lenyomat nélküli arcokon, majd a
        névtelen arcok inkrementális csoportosítása — KÜLÖN, a detektálásnál
        alacsonyabb prioritású sor. Ha az SFace a csomagból és a
        felhasználói modellmappából is hiányzik, elindítja a
        háttér-letöltést, majd automatikusan folytatja a csoportosítást."""
        grouping_options = self._csoportositasi_beallitasok()
        if not self._embedder.available:
            if any(
                spec.key == "embedder" for spec in model_download.missing_specs()
            ):
                self._embedding_after_download = True
                self._embedding_options_after_download = grouping_options
                self.downloadModels()
            else:
                self.embeddingModelUnavailable.emit()
            return
        self._start_embedding_worker(*grouping_options)


    def _csoportositasi_beallitasok(self) -> tuple[bool, int, int]:
        """A UI-szálról kiolvassa a csoportosító worker beállításait."""
        return (
            self.suggestionsEnabled(),
            self.suggestionThreshold(),
            self.clusterThreshold(),
        )


    def _start_embedding_worker(
        self, suggestions_enabled: bool, suggest_step: int, cluster_step: int
    ) -> None:
        """A betöltött SFace-szel, rögzített beállításokkal indítja a munkát."""
        self.cancelEmbedding()
        stop_event = threading.Event()
        self._embedding_stop_event = stop_event
        self.embeddingStarted.emit()
        self._start_background(
            self._run_embedding,
            args=(stop_event, suggestions_enabled, suggest_step, cluster_step),
            name="picasapy-face-embed",
        )


    @Slot()
    def cancelEmbedding(self) -> None:
        """A folyamatban lévő lenyomat-számítás megszakítása arc-határon —
        a már elmentett lenyomatok/csoportok az indexben maradnak."""
        if self._embedding_stop_event is not None:
            self._embedding_stop_event.set()


    def _run_embedding(
        self,
        stop_event: threading.Event,
        suggestions_enabled: bool,
        suggest_step: int,
        cluster_step: int,
    ) -> None:
        try:
            with open_index(self._db_path) as conn:
                pending = faces_missing_embedding(conn)
                total = len(pending)
                embedded = 0
                self._set_sorting_percent(0)
                for done, face in enumerate(pending, start=1):
                    if stop_event.is_set():
                        conn.commit()
                        self.embeddingCancelled.emit()
                        return
                    image = self._decode(face.photo_path)
                    detection = face.detection
                    if image is not None and face.photo_width and face.photo_height:
                        image_height, image_width = image.shape[:2]
                        detection = rescale_face_detection(
                            detection,
                            image_width / face.photo_width,
                            image_height / face.photo_height,
                        )
                    embedding = (
                        self._embedder.compute(image, detection)
                        if image is not None
                        else None
                    )
                    if embedding is not None:
                        store_embedding(conn, face.id, embedding)
                        embedded += 1
                    # Az SFace következő futása szintén a tranzakción kívül
                    # történjen.
                    conn.commit()
                    self._set_sorting_percent(round(100 * done / total))
                    self.embeddingProgress.emit(done, total)
                conn.commit()
                grouped = group_unnamed_faces(
                    conn,
                    suggest_threshold=step_to_threshold(suggest_step),
                    cluster_threshold=cluster_step_to_threshold(cluster_step),
                    named_centroids=None if suggestions_enabled else {},
                )
                conn.commit()
        except Exception as error:  # noqa: BLE001 — index-hiba se fagyassza a UI-t
            _log.exception("arc-lenyomat/csoportosítás hiba: %s", self._db_path)
            self.embeddingFailed.emit(str(error))
            return
        finally:
            if self._embedding_stop_event is stop_event:
                self._embedding_stop_event = None
            self._set_sorting_percent(-1)
        self.embeddingFinished.emit(embedded, grouped)
