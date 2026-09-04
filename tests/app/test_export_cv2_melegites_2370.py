"""#2370: az export-vezérlő a HÍVÓ szálon melegítse be a cv2-t.

Az őr a sorrendet állítja: az `elore_betolt()` a `_start_background`
ELŐTT fut. Ez az a sorrend, aminek a hiánya a windows-lábon
ACCESS_VIOLATION-t adott (a mérés a #2370-en áll).

**Nem** állítja, hogy az összeomlás megszűnt — azt csak a windows-láb
zöld futásai mutathatják meg; Linuxon a jelenség nem hívható elő.
"""

from __future__ import annotations

import pytest

from picasapy.app import export_controller
from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    root.mkdir()
    make_jpeg(root / "IMG_0001.jpg")
    return root


@pytest.fixture
def vezerlo(qt_app, tmp_path, library):
    """Ugyanaz a felépítés, mint a #459 tesztjeiben — a valódi
    `AppController`-en mérünk, mert a `_export_items` a vezérlő
    nyilvántartásaira és jelzéseire támaszkodik."""
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    beallitas = QSettings(str(tmp_path / "s.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=beallitas,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0)


def test_a_cv2_melegites_megelozi_a_szalinditast(vezerlo, tmp_path, monkeypatch):
    naplo: list[str] = []
    monkeypatch.setattr(
        export_controller, "elore_betolt", lambda: naplo.append("cv2")
    )
    monkeypatch.setattr(
        type(vezerlo),
        "_start_background",
        lambda self, *a, **k: naplo.append("szal"),
    )
    # a lemezhely-ellenőrzés ne álljon az útba: a SORRENDET mérjük
    monkeypatch.setattr(
        export_controller, "has_enough_free_space", lambda *a, **k: True
    )
    vezerlo.exportRows([0], str(tmp_path / "cel"), 0, 85)

    assert naplo == ["cv2", "szal"], (
        "a cv2 betöltésének a szálindítás ELŐTT kell megtörténnie"
    )
