r"""A kollázs háttérszála NEM ír állapotot és NEM emitál nyilvánosat (#988).

## A lelet — veremkiíratásból, nem feltevésből

A `test_collage_controller_943.py` szegmentálási hibával állt le a CI-ben.
A teljes veremkiíratás két szálat mutatott:

```
Thread (háttér):  picasa_render._canvas … collage_save._render_worker
Current thread:   Garbage-collecting … test_…_943.py:114 _wait
```

Vagyis a **főszál szemetet gyűjtött** (egy beágyazott `QEventLoop`-ban),
miközben a **háttérszál** dolgozott — és a háttérszál közben Qt-jelzést
emitált (`collageProgress`, `collageDone`, …), `tr()`-t hívott, és
megosztott állapotot írt (`_collage_panel_percent`). Ez a #430-as
SIGSEGV-osztály: PySide-burkolók piszkálása idegen szálról, miközben a
GUI-szálon GC fut.

## A javítás alakja

A projekt saját, már bevált mintája (`busy_registry.py`): a szálhatárt
**egy belső jelzés** lépi át, sorba állított kapcsolattal, és minden
tényleges munka — állapotírás, fordítás, nyilvános jelzés — a **fogadó**
szálon történik.

## Mit állít ez a fájl

⚠️ **Nem azt, hogy a SIGSEGV megszűnt** — azt egyetlen zöld futás sem
bizonyítja, mert a hiba a GC időzítésén múlik. Azt állítja, ami
determinisztikusan eldönthető: **a háttérszál nem nyúl a fogadó
állapotához**, és a munka a fogadó szálán fut le. A veremkiíratás szerint
pontosan ez a különbség számít.
"""

from __future__ import annotations

import inspect
import threading

import pytest
from PySide6.QtCore import QObject, QThread

from picasapy.app.collage_save import CollageSaveMixin


@pytest.fixture
def host(qt_app):
    """A legkisebb gazda, ami a hídhoz kell — nincs szükség teljes appra."""

    class _Host(CollageSaveMixin, QObject):
        def __init__(self) -> None:
            super().__init__()
            self._collage_panel_percent = 0
            # a folyamat-szöveghez kell; a téma itt lényegtelen
            self._collage_panel_theme = "picturepile"

    return _Host()


class TestASzalhatarEgyJelzes:
    """A háttérszálról indított jelzés a FOGADÓ szálon dolgozódik fel."""

    def test_a_post_progress_nem_ir_allapotot_a_hivo_szalon(self, qt_app, host):
        """A lényeg: a szálról hívva a `_collage_panel_percent` NEM változik
        azonnal — a sorba állított kapcsolat a fogadó szálra viszi."""
        host._ensure_worker_bridge()
        host._collage_panel_percent = 0

        kesz = threading.Event()

        def szalrol():
            host._post_progress(42, host._PROGRESS_INITIALIZING)
            kesz.set()

        threading.Thread(target=szalrol, daemon=True).start()
        kesz.wait(5.0)

        assert host._collage_panel_percent == 0, (
            "a háttérszál hívása AZONNAL írta az állapotot — nem sorba állított"
        )

        qt_app.processEvents()

        assert host._collage_panel_percent == 42

    def test_a_feldolgozas_a_fogado_szalan_fut(self, qt_app, host):
        host._ensure_worker_bridge()
        futott_szalon: list[QThread] = []
        host.collageProgress.connect(
            lambda *_: futott_szalon.append(QThread.currentThread())
        )
        kesz = threading.Event()

        def szalrol():
            host._post_progress(7, host._PROGRESS_INITIALIZING)
            kesz.set()

        threading.Thread(target=szalrol, daemon=True).start()
        kesz.wait(5.0)
        qt_app.processEvents()

        assert futott_szalon, "a jelzés nem ért célba"
        assert futott_szalon[0] is host.thread(), (
            "a nyilvános jelzés NEM a fogadó szálán futott"
        )


class TestAWorkerNemNyulSemmihez:
    """Forrás-őr: a `_render_worker` törzse ne térhessen vissza a régihez."""

    #: Amit a háttérszál törzsében tilos használni — mindhárom a
    #: PySide-burkolókat piszkálja, és a #988 veremkiíratása szerint ez öl.
    TILTOTT = ("self.tr(", "self._collage_panel_percent =", "self._emit_progress(")

    def test_a_worker_torzse_tiszta(self):
        forras = inspect.getsource(CollageSaveMixin._render_worker)

        talalatok = [minta for minta in self.TILTOTT if minta in forras]

        assert not talalatok, (
            "a háttérszál törzse megosztott állapothoz/fordításhoz nyúl "
            "(#988): " + ", ".join(talalatok)
        )

    def test_a_worker_csak_belso_jelzest_emital(self):
        """Nyilvános `collage*` jelzés a szálról: pont ez omlasztott."""
        forras = inspect.getsource(CollageSaveMixin._render_worker)

        nyilvanos = [
            sor.strip()
            for sor in forras.splitlines()
            if ".emit(" in sor and "_worker" not in sor
        ]

        assert not nyilvanos, (
            "a háttérszál NYILVÁNOS jelzést emitál (#988): " + " | ".join(nyilvanos)
        )
