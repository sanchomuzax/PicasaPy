"""Az előnézeti arány: a munkavászon és a teljes felbontású kép szélességének
aránya (#3377).

Az eredeti `BorderImageOperation` (`0x00bbe430`) a két VASTAGSÁGOT
`imageWidth / fullResImageWidth` tényezővel szorozza, majd csonkítja — a
feliratsávot és a sarok-rádiuszt NEM (`docs/specs/filterdesc-registry.md`,
„A `Border` négy attribútumának EGYSÉGE", C és F szakasz). Teljes
felbontáson a tényező 1; kicsinyített előnézeten kisebb, így a keret a
mentett képpel arányos marad.

A lánc kezelőinek aláírása `(kép, op)`, ezért az arány környezeti értékként
jut el hozzájuk: a hívó (a szerkesztő előnézete) az `elonezeti_arany()`
blokkban futtatja a láncot, a kezelők a `jelenlegi_arany()`-t olvassák. A
`ContextVar` szálanként külön él, tehát a háttér-render (#546) sem látja a
GUI-szál értékét.

#3846: ugyanígy él a GYORS ÉLŐ-ELŐNÉZET jelzője. A szerkesztő a Kiegyenesítés
csúszkájának HÚZÁSA közben (`EditController.previewTilt`) a `gyors_elonezet()`
blokkban renderel; ilyenkor a tilt a natív fixpontos mintavevő helyett az
OpenCV bilineárisával fut (ugyanazzal a képpontközepes mátrixszal). Mentés,
export, bélyegkép és az elengedés utáni kép a blokkon KÍVÜL fut, tehát natív.

#3862: a `EditController.previewEffect` (az effekt-csúszkák — pl. a Polaroid
Rotate-ja — közös húzás közbeni előnézeti útja) ugyanide kötve nyitja a
blokkot, tehát a Polaroid forgatása is a gyors mintavevőre vált húzás közben
(`glimmer_frame_ops.rotate_with_pad(..., gyors=...)`); az Alkalmaz gomb
(`applyEffectWithParams`) már a blokkon kívül, natívan renderel.
"""

from __future__ import annotations

import math
from collections.abc import Iterator
from contextlib import contextmanager
from contextvars import ContextVar

_ARANY: ContextVar[float] = ContextVar("elonezeti_arany", default=1.0)
_GYORS: ContextVar[bool] = ContextVar("gyors_elonezet", default=False)


def jelenlegi_arany() -> float:
    """A futó lánc előnézeti aránya — blokkon kívül 1 (teljes felbontás)."""
    return _ARANY.get()


@contextmanager
def elonezeti_arany(arany: float) -> Iterator[None]:
    """A blokkban futó láncok ezzel az aránnyal skálázzák a keret-vastagságot.

    Érvénytelen (nem pozitív vagy nem véges) aránynál 1 marad érvényben —
    egy hibás méret-lekérdezés ne tüntesse el a keretet."""
    ervenyes = arany if math.isfinite(arany) and arany > 0 else 1.0
    token = _ARANY.set(ervenyes)
    try:
        yield
    finally:
        _ARANY.reset(token)


def skalazott_vastagsag(vastagsag: float) -> int:
    """A keret-vastagság a munkavászonra: `× arány`, majd csonkítás (az
    eredeti `fldcw`-vel váltott kerekítési módja)."""
    return max(0, math.trunc(vastagsag * jelenlegi_arany()))


def gyors_elonezet_aktiv() -> bool:
    """Csúszka-húzás közbeni gyors előnézet fut-e (#3846) — blokkon kívül nem."""
    return _GYORS.get()


@contextmanager
def gyors_elonezet() -> Iterator[None]:
    """A blokkban futó láncok a gyors előnézeti utat választhatják (#3846)."""
    token = _GYORS.set(True)
    try:
        yield
    finally:
        _GYORS.reset(token)
