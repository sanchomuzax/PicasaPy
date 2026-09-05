"""#1977: a QML-ből hívott vezérlő-metódusok legyenek SLOTOK.

## A regresszió, amiből ez lett

A #2185 (a #1977 első köre) egy privát segítőt szúrt be KÖZVETLENÜL az
`exportMovie` `@Slot` dekorátora ALÁ. A dekorátor így a segítőre került, az
`exportMovie` pedig **kiesett a meta-objektumból** — a QML
`controller.exportMovie(…)` hívása nem érte el, és a Mozgófilm-párbeszéd OK
gombja **némán nem csinált semmit**.

Mérve a javítás előtt:

```
exportMovie                 -> ['exportMovieFull()']            (hiányzik!)
_alapertelmezett_film_cel   -> ['_alapertelmezett_film_cel(QVariantList,QString,int,double)']
```

## Amit ez az őr állít

Hogy minden `controller.<név>(` alakban HÍVOTT metódus tényleg ott van a
vezérlő meta-objektumában. A dekorátor elcsúszása így nem maradhat néma:
egy `@Slot` fölé beszúrt új metódus azonnal elbuktatja.

## Amit NEM állít

Nem méri a paraméter-típusokat, és nem fogja meg, ha egy hívás rossz
argumentumokkal megy. A cél a MEGHÍVHATÓSÁG.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app as app_csomag

_QML_GYOKER = Path(app_csomag.__file__).parent / "qml"

#: `controller.valami(` — a vezérlőn hívott metódusok.
_HIVAS = re.compile(r"\bcontroller\.([A-Za-z_]\w*)\s*\(")

#: Nem vezérlő-metódusok: QML-oldali segítők és beépített alakok.
_KIVETELEK = {"toString", "hasOwnProperty"}


def _qml_hivasok() -> set[str]:
    """A vezérlőn hívott nevek — a KOMMENTEK kihagyásával.

    A `//`-val kezdődő sorok gyakran hivatkoznak metódusnevekre
    magyarázatként (`… nem a controller._show() útján …`); azokat hívásnak
    venni téves leletet ad.
    """
    nevek: set[str] = set()
    for ut in _QML_GYOKER.rglob("*.qml"):
        for sor in ut.read_text(encoding="utf-8").splitlines():
            if sor.lstrip().startswith(("//", "*", "/*")):
                continue
            for m in _HIVAS.finditer(sor):
                nevek.add(m.group(1))
    return nevek - _KIVETELEK


def test_a_QML_bol_hivott_metodusok_meghivhatok(qt_app) -> None:
    from picasapy.app.controller import AppController

    mo = AppController.staticMetaObject
    meta = {
        mo.method(i).methodSignature().data().decode().split("(")[0]
        for i in range(mo.methodCount())
    }
    # a Property-k is elérhetők QML-ből, de nem metódusként hívódnak
    tulajdonsagok = {
        mo.property(i).name() for i in range(mo.propertyCount())
    }

    hivott = _qml_hivasok()
    assert len(hivott) > 40, (
        f"csak {len(hivott)} hívást találtam a QML-ben — a minta "
        "valószínűleg elromlott, az őr így semmit nem védene"
    )

    hianyzo = sorted(
        nev for nev in hivott
        if nev not in meta and nev not in tulajdonsagok
        and hasattr(AppController, nev)
    )
    assert not hianyzo, (
        "a QML hívja, de NINCS a meta-objektumban (hiányzó vagy elcsúszott "
        f"`@Slot`): {', '.join(hianyzo)}"
    )
