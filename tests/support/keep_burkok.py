"""A tesztek életben tartott QML-burkainak elengedése a motorral együtt (#4880).

Sok QML-tesztfájl modulszintű `_KEEP_ALIVE` / `_KEEPALIVE` / `_KEEP_QML_OBJECTS`
listában tartja meg a QML-objektumok Python-burkait, mert a PySide6 menet
közben felszabadíthatná őket. A #4871 óta a `qml_app` lebontása valóban
megsemmisíti a motort; a listában maradt burok ezután elavult címre mutat, de a
PySide érvényesnek tartja. Ha a következő teszt objektuma ugyanarra a címre
kerül, a PySide a RÉGI, rossz típusú burkot adja vissza
(`'QMetaObject' object has no attribute 'findChild'`).

A lebontás ezért a motor törlése ELŐTT kigyűjti az ehhez a motorhoz tartozó
burkokat, a törlés UTÁN kiveszi őket a listából, és érvényteleníti őket.
Más motorhoz (modulszintű fixtúra) tartozó burokhoz nem nyúl.
"""

from __future__ import annotations

import sys
from collections.abc import Iterable

_LISTA_ELOTAG = "_KEEP"


def keep_listak(modulok: Iterable[object] | None = None) -> list[list]:
    """A betöltött modulok `_KEEP…` nevű, modulszintű listái."""
    modulok = list(sys.modules.values()) if modulok is None else modulok
    listak = []
    for modul in modulok:
        try:
            tartalom = vars(modul)
        except TypeError:
            continue
        for nev, ertek in list(tartalom.items()):
            if nev.startswith(_LISTA_ELOTAG) and isinstance(ertek, list):
                listak.append(ertek)
    return listak


def motorhoz_tartozik(obj: object, gyokerek: tuple[object, ...]) -> bool:
    """Az objektum a megadott motor / ablak alá tartozik-e (szülőlánc vagy ablak)."""
    import shiboken6
    from PySide6.QtCore import QObject

    if not isinstance(obj, QObject) or not shiboken6.isValid(obj):
        return False
    ablak = getattr(obj, "window", None)
    if callable(ablak):
        try:
            if ablak() in gyokerek:
                return True
        except (RuntimeError, TypeError):
            pass
    aktualis = obj
    for _ in range(64):
        if aktualis is None:
            return False
        if aktualis in gyokerek:
            return True
        try:
            aktualis = aktualis.parent()
        except (RuntimeError, TypeError):
            return False
    return False


def kigyujt(gyokerek: tuple[object, ...], modulok: Iterable[object] | None = None) -> list[tuple[list, object]]:
    """A motor törlése ELŐTT: a hozzá tartozó, listában tartott burkok."""
    return [
        (lista, obj)
        for lista in keep_listak(modulok)
        for obj in list(lista)
        if motorhoz_tartozik(obj, gyokerek)
    ]


def elenged(talalatok: list[tuple[list, object]]) -> int:
    """A motor törlése UTÁN: kivétel a listából + érvénytelenítés."""
    import shiboken6

    db = 0
    for lista, obj in talalatok:
        while obj in lista:
            lista.remove(obj)
        try:
            shiboken6.invalidate(obj)
        except (RuntimeError, TypeError):
            pass
        db += 1
    return db
