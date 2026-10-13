"""A tesztmodul életben tartott QML-burkainak elengedése a motorral együtt (#4880).

Sok QML-tesztfájl modulszintű `_KEEP_ALIVE` / `_KEEPALIVE` / `_KEEP_QML_OBJECTS`
listában tartja meg a QML-objektumok Python-burkait, mert a PySide6 menet
közben felszabadíthatná őket. A #4871 óta a `qml_app` lebontása valóban
megsemmisíti a motort; a listában maradt burok ezután elavult címre mutat, de a
PySide érvényesnek tartja. Ha a következő teszt objektuma ugyanarra a címre
kerül, a PySide a RÉGI, rossz típusú burkot adja vissza
(`'QMetaObject' object has no attribute 'findChild'`).

A lebontás ezért a motor törlése UTÁN a teszt saját moduljának `_KEEP…`
listáiban lévő burkokat érvényteleníti (`shiboken6.invalidate` — a C++
objektumhoz nem nyúl) és kiüríti a listát. A törlés ELŐTT semmilyen burokhoz
nem nyúl: egy korábbi, szülőláncot bejáró változat a #4882 CI-n SIGSEGV-t
okozott a DeferredDelete-ben.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path
import sys

_LISTA_ELOTAG = "_KEEP"
_TESZTEK_GYOKER = Path(__file__).resolve().parents[1]


def modul_listak(modul: object) -> list[list]:
    """A modul `_KEEP…` nevű, modulszintű listái."""
    try:
        tartalom = vars(modul)
    except TypeError:
        return []
    return [
        ertek for nev, ertek in list(tartalom.items())
        if nev.startswith(_LISTA_ELOTAG) and isinstance(ertek, list)
    ]


def modul_listait_elenged(modul: object) -> int:
    """Érvényteleníti és kiüríti a modul `_KEEP…` listáit; a darabszámot adja."""
    import shiboken6

    db = 0
    for lista in modul_listak(modul):
        for obj in list(lista):
            try:
                shiboken6.invalidate(obj)
            except (RuntimeError, TypeError):
                pass
            db += 1
        lista.clear()
    return db


def tesztmodulok_listait_elenged(modulok: Iterable[object] | None = None) -> int:
    """A betöltött teszt- és tesztsegédmodulok `_KEEP…` listáit üríti.

    A PySide-burkokat megosztó segédmodul saját listája is életben maradhat
    akkor, ha egy másik tesztmodul hívta meg. A QML-motor törlése után ezért
    minden, a `tests/` alatt betöltött modul listáját elengedjük, nem csak a
    fixture-t használó tesztmodulét.
    """
    if modulok is None:
        modulok = sys.modules.values()

    db = 0
    latott: set[int] = set()
    for modul in tuple(modulok):
        azon = id(modul)
        if azon in latott:
            continue
        latott.add(azon)

        try:
            fajl = vars(modul).get("__file__")
        except TypeError:
            continue
        if not fajl:
            continue
        utvonal = Path(fajl)
        if not utvonal.is_absolute():
            utvonal = Path.cwd() / utvonal
        try:
            utvonal.relative_to(_TESZTEK_GYOKER)
        except ValueError:
            continue

        db += modul_listait_elenged(modul)
    return db
