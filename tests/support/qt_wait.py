"""Közös várakozó-segédek háttérszálas Qt-műveletekhez (#475).

## Miért kell

A csillagozás/felirat/forgatás háttérszálon fut (NAS-írás + célzott
index-UPDATE), ezért a teszt a `photoOpFinished` jelzésre vár. A korábbi,
fájlonként lemásolt minta így nézett ki:

```python
loop = QEventLoop()
controller.photoOpFinished.connect(loop.quit)
action()
QTimer.singleShot(2000, loop.quit)   # vészfék
loop.exec()
```

A **vészfék csendben** engedte tovább a tesztet: ha a 2 másodperc alatt nem
jött meg a jelzés (lassú CI-runner!), a hurok kilépett, a művelet még nem
fejeződött be, és a teszt nem időtúllépést jelentett, hanem egy KÉSŐBBI
állítás bukott el rossz értékkel — ami teljesen elfedte a valódi okot.
Így bukott a `test_selection.py` a windows-lábon: „a csillag fehér, nem
arany", holott a csillagozás egyszerűen még nem futott le (#475).

## Mit csinál helyette

Ez a segéd a vészféket **hangossá** teszi: ha a jelzés nem érkezik meg,
beszédes `AssertionError`-t dob, és az időkorlát bőkezűbb (a lassú CI-hez
szabva). A hívónak így soha nem kell találgatnia, mi romlott el.
"""

from __future__ import annotations

from collections.abc import Callable

# A régi 2 másodperc a fejlesztői gépre volt szabva. A CI-runner (különösen
# a windows-láb, coverage alatt) lényegesen lassabb — a bő időkorlát nem
# lassítja a zöld futást (a jelzés érkezésekor azonnal továbblép), csak a
# hamis bukást előzi meg.
DEFAULT_TIMEOUT_MS = 15000


def wait_for_signal(
    signal,
    action: Callable[[], object] | None = None,
    *,
    timeout_ms: int = DEFAULT_TIMEOUT_MS,
    description: str = "a háttérművelet",
    process_events_with=None,
) -> None:
    """Elindítja az `action`-t, és megvárja a `signal` megérkezését.

    A jelzésre azonnal továbblép. Ha az időkorlát alatt NEM jön meg,
    `AssertionError`-t dob — nem engedi tovább csendben a tesztet.

    `process_events_with`: opcionális `QGuiApplication`; ha meg van adva, a
    jelzés után lefuttat egy `processEvents()`-et, hogy a QML-kötések is
    frissüljenek (a QML-funkcionális tesztek igénye)."""
    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    arrived: list[bool] = []

    def _on_signal(*_args):
        arrived.append(True)
        loop.quit()

    signal.connect(_on_signal)
    # a vészfék-timer a hurok GYERMEKE: a hurokkal együtt megsemmisül, így
    # nem marad árva, később elsülő timer a processzben
    timer = QTimer(loop)
    timer.setSingleShot(True)
    timer.timeout.connect(loop.quit)
    timer.start(timeout_ms)

    if action is not None:
        action()
    loop.exec()
    timer.stop()
    signal.disconnect(_on_signal)

    assert arrived, (
        f"{description} nem fejeződött be {timeout_ms / 1000:g} másodperc "
        f"alatt (a várt jelzés nem érkezett meg). Ez NEM tartalmi hiba: a "
        f"művelet lassabb volt az időkorlátnál — ld. #475."
    )
    if process_events_with is not None:
        process_events_with.processEvents()


def wait_for_photo_op(controller, action, *, qt_app=None) -> None:
    """A `photoOpFinished`-re várakozás rövidítése (csillag/felirat/
    forgatás). A korábbi, fájlonként másolt `_do_photo_op` utódja."""
    wait_for_signal(
        controller.photoOpFinished,
        action,
        description="a kép-művelet (photoOpFinished)",
        process_events_with=qt_app,
    )


def varj_kollazs_jelzesre(signal, action, timeout_ms: int = 20000):
    """Kollázs-háttérmunkát indító művelet bevárása — **GC-szünettel**.

    A kollázs-tesztek `_wait` segédjének közös alakja. Két dolgot tesz a
    beágyazott eseményhurkon felül, és mindkettő KÜLÖN állítás, külön
    bizonyítékkal (#988):

    1. **A várakozás idejére kikapcsolja a szemétgyűjtőt.** A CI-n
       visszatérő `exit -11` (SIGSEGV) veremkiíratása ezt mutatta:

       ```
       Thread (háttér):  picasa_render._canvas ← collage_save._render_worker
       Current thread:   Garbage-collecting ← _wait ← a teszt
       ```

       A főszál épp GC-t futtat a beágyazott hurokban, miközben a
       háttérszál — egy sima `threading.Thread` — Qt-jelzést marsall a
       PySide-burkolókon. A GC időzítése dönti el, hogy elszáll-e; ezért
       nem reprodukálható terhelés nélkül, és ezért látszik
       párhuzamosság-függőnek.

    2. **A végén bontja a kapcsolatot.** Enélkül hívásonként egy holt,
       lokális függvényre mutató kapcsolat és egy `QEventLoop` marad a
       jelzésen — pont az, amit később a szemétgyűjtő takarítana.

    Mindkettő a `finally`-ben: egy elszálló teszt sem hagyhatja
    kikapcsolva a gyűjtőt a többinek.

    **Hol van a hiba — MÉRVE (2026-08-23).** Sokáig az volt a magyarázat,
    hogy a versenyhelyzet a TERMÉKBEN van, és a valódi javítás a worker
    Qt-natívvá tétele (`QThread`) lenne. **Ezt a mérés megcáfolta:** a
    kollázs-mentés 96 egymást követő futásban hibátlanul lefutott úgy,
    hogy a főszál 0 ms-onként teljes szemétgyűjtést végzett közben
    (`tests/app/test_kollazs_gc_verseny_988.py` őrzi ezt). A #1112 óta a
    háttérszál nem ír állapotot és nem bocsát ki nyilvános jelzést, a
    rajzolás pedig tiszta numpy — Qt-objektumhoz nem nyúl.

    Ami tehát elszállt, az a TESZT oldalán keletkezett: a bontatlan
    kapcsolatok és az árván maradt `QEventLoop`-ok, amiket a szemétgyűjtő
    egy tetszőleges pillanatban takarított. Ezért elég — és ezért helyes —
    itt kezelni.

    Returns:
        `(megjott, args)` — a jelzés megérkezett-e, és a paraméterei.
    """
    import gc

    from PySide6.QtCore import QEventLoop, QTimer

    loop = QEventLoop()
    received: dict[str, tuple] = {}

    def _on(*args):
        received.setdefault("args", args)
        loop.quit()

    signal.connect(_on)
    gc.disable()
    try:
        action()
        if "args" not in received:
            QTimer.singleShot(timeout_ms, loop.quit)
            loop.exec()
    finally:
        gc.enable()
        signal.disconnect(_on)
    return ("args" in received, received.get("args", ()))
