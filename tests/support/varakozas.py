"""Közös feltétel-várakozás a Qt-s teszteknek (#4970).

A tesztkészletben tucatnyi fájl saját `_var(qt_app, feltetel, masodperc=N)`
hurkot visz, és a korlátjuk sokszor 1-5 másodperc. A windowsos CI-futó
lassabb, így a rövid korlát időnként hamis bukást ad, miközben a termék jól
működik. Ez a segéd egyetlen helyen tartja a korlátot: a `masodperc` az
alapérték, és a `PICASAPY_TESZT_IDOSZORZO` környezeti változó szorozza.

Csak a feltételre várunk: ha a feltétel előbb teljesül, azonnal visszatér,
tehát a szorzó a zöld futást nem lassítja, csak a hamis bukást előzi meg.
"""

from __future__ import annotations

import math
import os
import time
from collections.abc import Callable

IDOSZORZO_ENV = "PICASAPY_TESZT_IDOSZORZO"
ALAP_MASODPERC = 10.0
_ALVAS_MASODPERC = 0.02


def idoszorzo() -> float:
    """A környezeti szorzó; hibás vagy hiányzó érték esetén 1.0.

    A hibás értéket csendben az alapra vesszük: a teszt így is fut, a
    beállítás hibáját pedig a korlát eredeti mérete jelzi, nem egy váratlan
    kivétel a várakozás közepén.
    """
    nyers = os.environ.get(IDOSZORZO_ENV, "").strip()
    try:
        ertek = float(nyers)
    except ValueError:
        return 1.0
    if not math.isfinite(ertek) or ertek <= 0:
        return 1.0
    return ertek


def var_feltetelre(
    qt_app,
    feltetel: Callable[[], bool],
    masodperc: float = ALAP_MASODPERC,
) -> bool:
    """Pörgeti az eseményhurkot, amíg a feltétel teljesül vagy lejár a korlát.

    Visszatérés: `True`, ha a feltétel teljesült; `False`, ha a (szorzóval
    növelt) korlát lejárt. A hívó dönt, hogy ez bukás-e.
    """
    hatarido = time.monotonic() + masodperc * idoszorzo()
    while True:
        qt_app.processEvents()
        if feltetel():
            return True
        if time.monotonic() >= hatarido:
            return False
        time.sleep(_ALVAS_MASODPERC)
