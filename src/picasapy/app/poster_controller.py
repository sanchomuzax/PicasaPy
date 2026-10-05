"""A Poszter készítése felületi vezérlője (#4268)."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

from PySide6.QtCore import QLocale, Qt, Signal, Slot

from .formatting import to_local_path
from .worker_thread import BackgroundWorkerMixin

_POSTER_PAPER_SIZE_KEY = "paper"
# Nagy képnél több tíz másodperc is kellhet; két perc után leállítjuk
# a beragadó natív műveletet.
_POSTER_WORKER_TIMEOUT_S = 120

# A csomagolt alkalmazás a launcher rejtett worker-módját, a forrásfa a modult indítja.
_futtato = sys


def _poster_worker_command(
    source_path: str,
    magnification_percent: int,
    paper_size: str,
    overlap: bool,
    result_path: str,
) -> list[str]:
    """A poszterlapokat előállító folyamat indítóparancsa."""
    if getattr(_futtato, "frozen", False):
        return [
            _futtato.executable,
            "--picasapy-poster",
            source_path,
            str(magnification_percent),
            paper_size,
            "1" if overlap else "0",
            result_path,
        ]
    return [
        _futtato.executable,
        "-m",
        "picasapy.printing.poster_worker",
        source_path,
        str(magnification_percent),
        paper_size,
        "1" if overlap else "0",
        result_path,
    ]


def _poster_worker_environment() -> dict[str, str]:
    """A forrásfából indított workerhez hozzáadja a csomag importgyökerét."""
    worker_env = os.environ.copy()
    worker_env["PYTHONIOENCODING"] = "utf-8"
    if not getattr(_futtato, "frozen", False):
        source_root = str(Path(__file__).resolve().parents[2])
        current_pythonpath = worker_env.get("PYTHONPATH", "")
        worker_env["PYTHONPATH"] = os.pathsep.join(
            value for value in (source_root, current_pythonpath) if value
        )
    return worker_env


class PosterMixin(BackgroundWorkerMixin):
    """A kiválasztott fotóból poszterlapokat készít háttérszálon."""

    posterFinished = Signal(list)
    posterFailed = Signal(str)
    _posterOutcome = Signal(object)

    def _ensure_poster_outcome_bridge(self) -> None:
        """A háttérmunka eredményét a vezérlő Qt-szálára sorolja."""
        if getattr(self, "_poster_outcome_bridge_ready", False):
            return
        self._posterOutcome.connect(
            self._on_poster_outcome, Qt.ConnectionType.QueuedConnection
        )
        self._poster_outcome_bridge_ready = True

    @Slot(object)
    def _on_poster_outcome(self, outcome: tuple[str, object]) -> None:
        """A nyilvános jelzéseket a vezérlő szálán bocsátja ki."""
        kind, payload = outcome
        if kind == "failed":
            self.posterFailed.emit(str(payload))
        else:
            self.posterFinished.emit(payload)

    @Slot(result=list)
    def posterPaperSizes(self) -> list[str]:  # noqa: N802
        """A rendszer területi beállításához tartozó két eredeti méret."""
        if QLocale().measurementSystem() == QLocale.MeasurementSystem.MetricSystem:
            return ["10x15", "20x25"]
        return ["4x6", "8.5x11"]

    @Slot(result=str)
    def posterPaperSize(self) -> str:  # noqa: N802
        """A régióban érvényes, legutóbb használt papírméret."""
        sizes = self.posterPaperSizes()
        stored = str(self._get_settings().value(_POSTER_PAPER_SIZE_KEY, sizes[0]))
        return stored if stored in sizes else sizes[0]

    @Slot(str)
    def setPosterPaperSize(self, paper_size: str) -> None:  # noqa: N802
        """A helyi méretkészletbe tartozó választás megőrzése."""
        if paper_size not in self.posterPaperSizes():
            return
        settings = self._get_settings()
        settings.setValue(_POSTER_PAPER_SIZE_KEY, paper_size)
        settings.sync()

    @Slot(str, int, str, bool)
    def createPoster(
        self,
        source_path: str,
        magnification_percent: int,
        paper_size: str,
        overlap: bool,
    ) -> None:  # noqa: N802
        """A kért poszterlapokat kiírja a forráskép mappájába."""
        local_path = to_local_path(source_path)
        if not local_path:
            self.posterFailed.emit("A kijelölt kép útvonala üres.")
            return

        self._ensure_poster_outcome_bridge()
        # A natív OpenCV-munkát külön, határidős folyamat végzi, hogy egy
        # beragadó dekódolás vagy kódolás ne akadályozza a felületet.
        worker_env = _poster_worker_environment()

        def work() -> None:
            try:
                with tempfile.TemporaryDirectory(
                    prefix="picasapy-poster-worker-"
                ) as worker_directory:
                    result_path = str(Path(worker_directory) / "result.json")
                    command = _poster_worker_command(
                        local_path,
                        magnification_percent,
                        paper_size,
                        overlap,
                        result_path,
                    )
                    completed = subprocess.run(
                        command,
                        capture_output=True,
                        text=True,
                        encoding="utf-8",
                        env=worker_env,
                        timeout=_POSTER_WORKER_TIMEOUT_S,
                        check=False,
                    )
                    try:
                        worker_result = json.loads(
                            Path(result_path).read_text(encoding="utf-8")
                        )
                    except (OSError, json.JSONDecodeError):
                        worker_result = None

                    if completed.returncode != 0:
                        worker_error = (
                            worker_result.get("error")
                            if isinstance(worker_result, dict)
                            else None
                        )
                        message = (
                            worker_error
                            or (completed.stderr or "").strip()
                            or "A poszterlapok készítése sikertelen."
                        )
                        self._posterOutcome.emit(("failed", message))
                        return

                    pages = (
                        worker_result.get("pages")
                        if isinstance(worker_result, dict)
                        else None
                    )
                    if not isinstance(pages, list) or not all(
                        isinstance(page, str) for page in pages
                    ):
                        raise ValueError(
                            "Érvénytelen válasz érkezett a poszterfolyamattól."
                        )
            except subprocess.TimeoutExpired:
                self._posterOutcome.emit(
                    (
                        "failed",
                        "A poszterlapok készítése időtúllépés miatt leállt.",
                    )
                )
                return
            except Exception as exc:  # noqa: BLE001 — a hibát a GUI-n jelezzük
                self._posterOutcome.emit(("failed", str(exc)))
                return
            self._posterOutcome.emit(("finished", pages))

        self._start_background(work, name="picasapy-poster")


__all__ = ["PosterMixin"]
