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
