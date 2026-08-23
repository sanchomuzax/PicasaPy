"""#988: a kollázs-mentés túléli a főszál agresszív szemétgyűjtését.

## Miért van ez a teszt

A CI-n visszatérő `exit -11` (SIGSEGV) veremkiíratása ezt mutatta:

```
Thread (háttér):  picasa_render._canvas ← collage_save._render_worker
Current thread:   Garbage-collecting ← _wait ← a teszt
```

Ebből az a MAGYARÁZAT született, hogy a versenyhelyzet a TERMÉKBEN van: a
háttérmunkás egy sima `threading.Thread`, ami Qt-jelzést marsall,
miközben a főszál gyűjthet — és hogy a valódi javítás a munkás
Qt-natívvá tétele (`QThread`) lenne.

**Ezt a magyarázatot a mérés megcáfolta** (2026-08-23): a mentés
*kifejezetten* agresszív GC mellett is hibátlanul lefut. A #1112 óta a
háttérszál már NEM ír állapotot és nem bocsát ki nyilvános jelzést — csak
két belső, SORBA ÁLLÍTOTT híd-jelzést (`_ensure_worker_bridge`), a
rajzolás maga pedig tiszta numpy, Qt-objektumhoz nem nyúl.

Ez a teszt ezt a tulajdonságot ŐRZI. Ha valaki a jövőben állapotírást
vagy Qt-objektum-használatot tesz vissza a háttérszálra, ez a teszt az,
aminek el kell buknia — nem a CI-nek, három hét múlva, egy másik jegy
ágán.

⚠️ A teszt SZÁNDÉKOSAN nem használja a `varj_kollazs_jelzesre` GC-szünetes
segédjét: itt épp a szemétgyűjtés a vizsgálat tárgya.
"""

from __future__ import annotations

import gc

import pytest
from PySide6.QtCore import QEventLoop, QObject, QSettings, QTimer

from support.jpeg_factory import make_jpeg


class _Photo:
    def __init__(self, folder_path, name, caption=None, width=400, height=300):
        self.folder_path = folder_path
        self.name = name
        self.caption = caption
        self.width = width
        self.height = height


class _Photos:
    def __init__(self, photos):
        self.photos = list(photos)


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "Nyaralas"
    root.mkdir()
    for name in ("a.jpg", "b.jpg", "c.jpg"):
        make_jpeg(root / name, size=(80, 60))
    return root


@pytest.fixture
def settings(tmp_path):
    from picasapy.app.collage_controller import COLLAGE_OUTPUT_DIR_KEY

    beallitasok = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    beallitasok.setValue(COLLAGE_OUTPUT_DIR_KEY, str(tmp_path / "Kollazsok"))
    return beallitasok


def _uj_host(settings, library):
    from picasapy.app.collage_controller import CollageMixin

    class _Host(CollageMixin, QObject):
        def __init__(self):
            super().__init__()
            self._settings = settings
            self._photos = _Photos(
                [
                    _Photo(str(library), "a.jpg", "Alma"),
                    _Photo(str(library), "b.jpg", None, 300, 400),
                    _Photo(str(library), "c.jpg", "Cica", 200, 200),
                ]
            )

        def _get_settings(self):
            return self._settings

        def _screen_ratio(self):
            return 9 / 16

        def _collage_output_width(self):
            # kicsi vászon: itt a szálak együttállása a vizsgálat tárgya,
            # nem a rajz minősége
            return 240

    return _Host()


@pytest.mark.parametrize("kor", range(3))
def test_a_mentes_tulel_agressziv_szemetgyujtest(qt_app, settings, library, kor):
    """A mentés fut, a főszál közben FOLYAMATOSAN gyűjt szemetet.

    A `QTimer` 0 ms-os időköze azt jelenti, hogy az eseményhurok minden
    körfordulásában teljes gyűjtés fut — pontosan az az együttállás,
    amit a veremkiíratás mutatott, csak nem véletlenszerűen, hanem
    kikényszerítve."""
    host = _uj_host(settings, library)
    host.openCollage([0, 1, 2])

    loop = QEventLoop()
    kesz = {}

    def _on(*args):
        kesz.setdefault("args", args)
        loop.quit()

    host.collageDone.connect(_on)
    kalapacs = QTimer()
    kalapacs.setInterval(0)
    kalapacs.timeout.connect(gc.collect)
    kalapacs.start()
    try:
        host.createCollage(False)
        if "args" not in kesz:
            QTimer.singleShot(20000, loop.quit)
            loop.exec()
    finally:
        kalapacs.stop()
        host.collageDone.disconnect(_on)

    assert "args" in kesz, "a mentés nem fejeződött be az agresszív GC mellett"
    assert host.waitForBackgroundWorkers(30.0), "a kollázs-szál nem állt le"
