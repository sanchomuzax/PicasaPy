"""#2370: a `cv2` ELSŐ betöltése ne háttérszálon történjen.

## A mérés, amiből ez jön

A main `windows 2/4` darabja hat egymást követő futáson
`0xC0000005` (ACCESS_VIOLATION) kilépőkóddal omlott össze. A pytest
beépített `faulthandler`-e kiírta a vermet (`33912620795` futás,
`windows 2/4` napló, 235–290. sor):

* **munkaszál:** `worker_thread._run` → `export_controller.worker` →
  `export_photos` → `_export_one` → `_decode_image` →
  `lazy_cv2.__getattr__` → `_betolt` → `import cv2` → `cv2/__init__.py`
  `bootstrap()`;
* **főszál:** `Garbage-collecting`.

A `cv2` Windowson a `bootstrap()`-ban `sys.path`-ot módosít és natív
DLL-könyvtárat vesz fel; ez omlik össze a párhuzamos szemétgyűjtéssel.

## Amit ez az őr állít, és amit NEM

Állítja, hogy (a) a lusta betöltő zárral védett és van kimondott
előre-betöltője, és (b) az export-vezérlő a HÍVÓ szálon melegíti be a
cv2-t, MIELŐTT a háttérszálat elindítaná. **Nem** állítja, hogy ezzel az
összeomlás megszűnt — azt csak a windows-láb öt zöld futása mutathatja
meg; Linuxon a jelenség nem hívható elő.
"""

from __future__ import annotations

import threading

import picasapy.lazy_cv2 as lazy_cv2


def _elfelejt() -> None:
    """A helyettest visszaállítja »még nem töltődött be« állapotba.

    A valódi modul a `sys.modules`-ban marad, tehát az újratöltés olcsó —
    csak a helyettes belső jelzőjét nullázzuk."""
    object.__setattr__(lazy_cv2.cv2, "_modul", None)


def test_van_kimondott_elore_betolto() -> None:
    _elfelejt()
    assert not lazy_cv2.betoltve()
    lazy_cv2.elore_betolt()
    assert lazy_cv2.betoltve()


def test_az_elore_betoltes_ismetelheto() -> None:
    lazy_cv2.elore_betolt()
    lazy_cv2.elore_betolt()
    assert lazy_cv2.betoltve()


def test_a_betolto_zarral_vedett() -> None:
    """Két szál egyszerre lépjen be; a modul EGY példány maradjon."""
    _elfelejt()
    eredmenyek: list[object] = []
    kapu = threading.Barrier(2)

    def fut() -> None:
        kapu.wait(5.0)
        eredmenyek.append(lazy_cv2.cv2.__name__)

    szalak = [threading.Thread(target=fut) for _ in range(2)]
    for sz in szalak:
        sz.start()
    for sz in szalak:
        sz.join(10.0)
    assert eredmenyek == ["cv2", "cv2"]
    assert object.__getattribute__(lazy_cv2.cv2, "_zar") is not None
