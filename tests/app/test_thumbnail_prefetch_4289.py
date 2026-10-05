"""#4289: a látható kérések előzzék meg a háttér-előtöltést."""

from __future__ import annotations

import threading

from PySide6.QtCore import QRunnable
from PySide6.QtGui import QImage

from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.thumbs import ThumbnailCache


class _PoolGate(QRunnable):
    """Egyetlen pool-szálat foglal, amíg mindkét munka sorba nem áll."""

    def __init__(self, entered: threading.Event, release: threading.Event):
        super().__init__()
        self.entered = entered
        self.release = release

    def run(self) -> None:
        self.entered.set()
        self.release.wait(5)


def test_visible_request_runs_before_queued_prefetch(qt_app, tmp_path):
    provider = ThumbnailProvider(
        ThumbnailCache(tmp_path / "thumbs", size=32), max_threads=1
    )
    entered = threading.Event()
    release = threading.Event()
    order: list[str] = []
    response = None

    def render(photo_id):
        order.append(photo_id)
        image = QImage(1, 1, QImage.Format.Format_RGB32)
        image.fill(0xFFFFFFFF)
        return image

    provider._render = render
    provider._pool.start(_PoolGate(entered, release))
    assert entered.wait(2), "a pool-foglaló munka nem indult el"

    try:
        provider.prefetch_images(["background"])
        response = provider.requestImageResponse("visible", None)
        release.set()

        assert response._done.wait(3), "a látható bélyegkép nem készült el"
        assert provider.wait_for_done(3000), "az előtöltés nem fejeződött be"
        assert order == ["visible", "background"]
    finally:
        release.set()
        provider.wait_for_done(5000)
        if response is not None:
            response.deleteLater()
            qt_app.processEvents()
