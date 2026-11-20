"""#7316 - a kész poszterlapok indexelését a vezérlő kéri, a sikerjelzés előtt.

A szerkesztő az utolsó lapot a rácsmodell sorindexével nyitja meg, ezért a
lapoknak be kell kerülniük az indexbe. A poszter eddig a mappafigyelőre bízta
ezt; a kollázs, a film és a másolat kimenetéhez hasonlóan (#1539) most a
`noteOutputWritten` kéri a célzott újraolvasást.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from support.jpeg_factory import make_jpeg
from support.qt_wait import varj_feltetelre


@pytest.fixture
def controller(qt_app, tmp_path):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", size=(80, 80))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, root)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db", (str(root),), provider, settings=settings
    )
    ctl.selectFolder(str(root / "nyaralas"))
    assert varj_feltetelre(
        qt_app, lambda: not ctl.backgroundWorkersRunning(), 10.0
    ), "az indulási háttérmunka nem fejeződött be"
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "a poszter-szál nem állt le"


def _hamis_folyamat(pages: list[str] | None, error: str | None = None):
    """A worker helyett: a megadott eredményt írja, nem ír lapfájlt."""

    def futtat(command, **kwargs):
        if error is not None:
            Path(command[-1]).write_text(json.dumps({"error": error}), encoding="utf-8")
            return subprocess.CompletedProcess(command, 1, stdout="", stderr="")
        Path(command[-1]).write_text(json.dumps({"pages": pages}), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0, stdout="", stderr="")

    return futtat


def _esemenyek_rogzitese(controller, monkeypatch) -> list[tuple[str, object]]:
    esemenyek: list[tuple[str, object]] = []
    monkeypatch.setattr(
        controller,
        "noteOutputWritten",
        lambda path: esemenyek.append(("indexeles", str(path))),
    )
    controller.posterFinished.connect(
        lambda pages: esemenyek.append(("kesz", list(pages)))
    )
    controller.posterFailed.connect(lambda msg: esemenyek.append(("hiba", str(msg))))
    return esemenyek


def test_sikeres_poszter_utan_az_utolso_lap_indexelese_kert_a_sikerjelzes_elott(
    controller, qt_app, tmp_path, monkeypatch
):
    from picasapy.app import poster_controller

    forras = tmp_path / "kepek" / "nyaralas" / "IMG_0001.jpg"
    lapok = [
        str(forras.with_name(f"{oszlop}-{sor}-IMG_0001.jpg"))
        for sor in range(2)
        for oszlop in range(2)
    ]
    monkeypatch.setattr(poster_controller, "_run", _hamis_folyamat(lapok))
    esemenyek = _esemenyek_rogzitese(controller, monkeypatch)

    controller.createPoster(str(forras), 200, "4x6", False)
    assert varj_feltetelre(
        qt_app, lambda: any(kind == "kesz" for kind, _ in esemenyek), 20.0
    ), "a poszter nem jelzett befejezést"

    assert esemenyek == [("indexeles", lapok[-1]), ("kesz", lapok)], (
        "az indexelés kérése a sikerjelzés előtt, egyszer, az utolsó lapra kell"
    )


def test_hibas_poszter_nem_kerj_indexelest(controller, qt_app, tmp_path, monkeypatch):
    from picasapy.app import poster_controller

    forras = tmp_path / "kepek" / "nyaralas" / "IMG_0001.jpg"
    monkeypatch.setattr(
        poster_controller, "_run", _hamis_folyamat(None, error="szintetikus hiba")
    )
    esemenyek = _esemenyek_rogzitese(controller, monkeypatch)

    controller.createPoster(str(forras), 200, "4x6", False)
    assert varj_feltetelre(
        qt_app, lambda: any(kind == "hiba" for kind, _ in esemenyek), 20.0
    ), "a poszter nem jelzett hibát"

    assert esemenyek == [("hiba", "szintetikus hiba")]
