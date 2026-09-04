"""#2262: a `qt_app` fixture lebontása várja meg a `threading.Thread`
háttérmunkákat is, ne csak a `QThreadPool`-t.

GYÖKÉROK. A `BackgroundWorkerMixin._start_background` sima
`threading.Thread(daemon=True)`-t indít, nem `QRunnable`-t — a globális
`QThreadPool.waitForDone()` tehát SEMMIT nem tud róla. Ha egy csak
`qt_app`-ot használó tesztfájl (pl. `test_effect_color_params_717.py`)
elindít egy előnézet-renderelő szálat, a szál a részfutás vége után is él,
és a `finally`-ben `AppBusyRegistry.end()`-et hív. Addigra a Qt-oldali
objektum megsemmisült, tehát az `emit()` `RuntimeError`-t dob egy
Python-szál törzséből — a CI-n ez `terminate called without an active
exception` / `exit -6`.

A mérce ezért nem a `QThreadPool`, hanem a `worker_thread` saját
nyilvántartása: a lebontás után NEM maradhat élő háttérmunka.
"""

from __future__ import annotations

import threading

from picasapy.app.worker_thread import running_background_workers


def test_a_lebontas_bevarja_a_threading_szalakat(qt_app) -> None:
    """Lassú háttérszál indul, majd a fixture lebontó függvénye lefut —
    utána a nyilvántartásban nem lehet élő munka."""
    from tests.app.conftest import _vard_meg_a_hatterszalakat

    from picasapy.app.worker_thread import BackgroundWorkerMixin

    elindult = threading.Event()

    class Munkas(BackgroundWorkerMixin):
        pass

    munkas = Munkas()

    def lassu() -> None:
        elindult.set()
        # Elég hosszú ahhoz, hogy a teszt teste biztosan előbb érjen véget,
        # de a lebontás keretidejét (5 mp) messze ne merítse ki.
        threading.Event().wait(1.5)

    munkas._start_background(lassu, name="picasapy-teszt-2262")
    assert elindult.wait(5.0), "a háttérszál el sem indult"
    assert "picasapy-teszt-2262" in running_background_workers()

    _vard_meg_a_hatterszalakat(qt_app)

    assert running_background_workers() == (), (
        "a lebontás után is fut háttérmunka: "
        f"{running_background_workers()} — a #2262 gyökéroka"
    )
