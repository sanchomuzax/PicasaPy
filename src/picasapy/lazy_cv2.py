"""LUSTA `cv2` — az OpenCV csak az első tényleges használatkor töltődik be.

## Miért

A #1601 mérése szerint az `import picasapy.app.application` **2435 ms**
valódi OpenCV-vel és **876 ms** azonnali cv2-pótlékkal: a levehető
költség ~1,5 másodperc **minden induláskor**, akkor is, ha a felhasználó
egyetlen effektet vagy arckeresést sem használ. Az eredeti Picasa 0–2 s
alatt elindul; a mi 5,2 másodpercünk felét ez az egy tétel adja (#1611).

## Miért nem elég egy helyen javítani

A #1601 kipróbálta a kézenfekvő utat (egyetlen lusta import az
`index/__init__.py`-ban) és **nulla nyereséget** kapott: az indulási
láncban **több mint harminc modul** importálja a cv2-t felső szinten, és
elég EGY, hogy a teljes költség beessen. A megoldás ezért nem egyetlen
hely javítása, hanem **egyetlen minta harminc helyen**:

    import cv2                     ->  from picasapy.lazy_cv2 import cv2

A modul-szintű `cv2.X` hivatkozások ettől nem változnak, csak a betöltés
csúszik az első attribútum-olvasásig.

## Miért nem gyorstárazza az attribútumokat

A kézenfekvő gyorsítás az volna, hogy a megtalált nevet a helyettes a
saját szótárába teszi, és a további hivatkozások oda esnek. **Ezt
szándékosan NEM tesszük**: onnantól a valódi modul foltozása
(`monkeypatch.setattr(cv2, "imencode", …)`) NEM látszana a helyettesen
át, mert a régi, elmentett függvény jönne vissza. A tesztjeink élnek
ezzel, és élesben is csendes, nehezen felderíthető eltérés lenne.

A továbbítás ára egy `__getattr__` + egy `getattr` hívásonként —
nagyságrendekkel kevesebb, mint bármelyik OpenCV-művelet maga.

## ⚠️ Az első betöltés SZÁLA számít (#2370)

A betöltés oda csúszik, ahol az első attribútum-olvasás történik — és ez
lehet egy háttérszál. Mérve: a main `windows 2/4` darabja hat egymást
követő futáson `0xC0000005`-tel omlott össze, mert a `cv2/__init__.py`
`bootstrap()`-ja (Windowson `sys.path`-módosítás + natív DLL-könyvtár)
egy export-munkaszálon futott, miközben a főszál szemetet gyűjtött.

Ezért: aki háttérszálat indít KÉPET DEKÓDOLÓ munkára, a hívó (GUI-)
szálon előbb hívja az `elore_betolt()`-öt. A közös
`worker_thread._start_background`-ba tenni TILOS: az visszahozná a
#1601-ben lemért ~1,5 másodpercet olyan munkákra is (mappapásztázás),
amelyek sosem nyúlnak az OpenCV-hez.

## ⚠️ Amit ez NEM old meg

Ha egy modul BETÖLTÉSKOR meg is HÍVJA a cv2-t (nem csak importálja), ott
a helyettes sem segít — a hívás azonnal behozza az OpenCV-t. Az ilyen
helyeket egyenként kell halasztani (ld. `thumbs/cache.py`
`_ffmpeg_elerheto()`).
"""

from __future__ import annotations

import threading
from typing import Any

__all__ = ["cv2", "betoltve", "elore_betolt"]


class _LustaModul:
    """Attribútum-továbbító helyettes egyetlen modul elé."""

    def __init__(self, nev: str) -> None:
        # NEM `self.x = ...`: a `__setattr__` alapértelmezett, de a nevet
        # aláhúzással tartjuk, hogy soha ne ütközzön egy cv2-attribútummal.
        object.__setattr__(self, "_modul_neve", nev)
        object.__setattr__(self, "_modul", None)
        # #2370: a betöltés ellenőriz-majd-cselekszik volt, zár nélkül. Két
        # háttérszál egyszerre léphetett be és mindkettő futtatta az
        # importot; a `threading.RLock` azért R, mert a `cv2` betöltése
        # a mi kódunkon át visszahívhat (a helyettesre néző modul-szintű
        # hivatkozások miatt), és az önmagára záródás holtpont lenne.
        object.__setattr__(self, "_zar", threading.RLock())

    def _betolt(self) -> Any:
        modul = object.__getattribute__(self, "_modul")
        if modul is not None:
            return modul
        with object.__getattribute__(self, "_zar"):
            # a zár megszerzése közben egy másik szál végezhetett
            modul = object.__getattribute__(self, "_modul")
            if modul is None:
                import importlib

                modul = importlib.import_module(
                    object.__getattribute__(self, "_modul_neve")
                )
                object.__setattr__(self, "_modul", modul)
        return modul

    def __getattr__(self, nev: str) -> Any:
        # MINDIG továbbít (nem gyorstáraz) — ld. a modul docstringjét:
        # a gyorstár elrejtené a valódi modul foltozását.
        return getattr(self._betolt(), nev)

    def __dir__(self):
        return dir(self._betolt())

    def __repr__(self) -> str:
        allapot = (
            "betöltve"
            if object.__getattribute__(self, "_modul") is not None
            else "még nem töltődött be"
        )
        return f"<lusta {object.__getattribute__(self, '_modul_neve')} — {allapot}>"


#: A modulok ezt importálják `cv2` néven.
cv2 = _LustaModul("cv2")


def elore_betolt() -> None:
    """Behozza az OpenCV-t MOST, a hívó szálon (#2370).

    Kimondottan azért létezik, hogy a költséges és Windowson szálérzékeny
    első betöltés a GUI-szálon történjen, ne egy háttérszálon. Ismételhető:
    a másodszori hívás nem csinál semmit."""
    object.__getattribute__(cv2, "_betolt")()


def betoltve() -> bool:
    """Igaz, ha az OpenCV-t már tényleg behoztuk. **Csak mérésre/tesztre** —
    a működő kódnak nem szabad rá támaszkodnia."""
    return object.__getattribute__(cv2, "_modul") is not None
