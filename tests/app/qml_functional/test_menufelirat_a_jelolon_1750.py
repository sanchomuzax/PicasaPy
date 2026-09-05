"""#1750: a jelölhető menütétel felirata a szomszédjaival EGY VONALBAN.

## A mérés

A tulajdonos képernyőmentése (v0.8.146) a felirat és a jelölőnégyzet
átfedését mutatta. Végigmérve a futó ablak MINDEN jelölhető menütételén
(58 db), a felirat tényleges kezdete (`contentItem.x +
contentItem.leftPadding`) szerint:

```
53 sima MenuItem      -> 26,0
 5 PicasaMenuItem     ->  6,0     <- ezek lógtak rá a jelölőre
   Recent &changes / Show Editing Controls / Test Mode (…) /
   Thumbnails Only / Use Color Management
```

Az ok: a `PicasaMenuItem` saját `contentItem`-et ad (`IconLabel`, #757 —
az `&`-mnemonik miatt kell), és ezzel elveszik a stílus alapértelmezett
bal térköze, ami a jelölőnek hagy helyet.

## ⚠️ Miért RELATÍV az állítás, és nem abszolút geometria

Az első változatom a jelölő jobb szélét hasonlította a felirat
kezdetéhez — és **a windows-lábon mind a 41 tételre elbukott**: ott a Qt
stílusa más számokat ad (jelölő vége 24, felirat 10), és a `contentItem`
belső elrendezése is más. A metrika tehát a STÍLUST mérte, nem a hibát.

Ezért az őr most azt állítja, ami platformfüggetlenül igaz és a
felhasználó számára is ez a lényeg: **minden jelölhető menütétel felirata
ugyanott kezdődik**. A `PicasaMenuItem` nem csúszhat el a szomszédos sima
`MenuItem`-ektől — se befelé (átfedés), se kifelé (behúzás).

Az őr a FUTÓ ablakon mér, nem a forráson — így egy későbbi
`contentItem`-csere is elbukna rajta.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _felirat_kezdetek(window) -> dict[str, float]:
    """Menütétel-felirat → a felirat tényleges vízszintes kezdete.

    Csak jelölhető, jelölővel ÉS tartalommal rendelkező tételek; a
    `leftPadding` a `contentItem` sajátja, tehát a felirat valódi
    kezdetéhez hozzá kell adni a `contentItem` x-éhez.
    """
    kezdetek: dict[str, float] = {}
    for objektum in window.findChildren(QObject):
        try:
            felirat = objektum.property("text")
            jelolheto = objektum.property("checkable")
        except (RuntimeError, TypeError):
            continue
        if not felirat or jelolheto is not True:
            continue
        jelolo = objektum.property("indicator")
        tartalom = objektum.property("contentItem")
        if jelolo is None or tartalom is None:
            continue
        kezdetek[str(felirat)] = (tartalom.property("x") or 0) + (
            tartalom.property("leftPadding") or 0
        )
    return kezdetek


def test_minden_jelolheto_felirat_ugyanott_kezdodik(qml_app, qt_app):
    window, _controller, _engine = qml_app
    kezdetek = _felirat_kezdetek(window)

    assert len(kezdetek) > 20, (
        f"csak {len(kezdetek)} jelölhető tételt találtam — a mérés nem "
        "járta be a menüsort, az állítás így semmit nem érne"
    )

    csoportok: dict[float, list[str]] = {}
    for felirat, x in kezdetek.items():
        csoportok.setdefault(x, []).append(felirat)

    assert len(csoportok) == 1, (
        "a jelölhető tételek feliratai nem egy vonalban kezdődnek — "
        + "; ".join(
            f"x={x}: {len(nevek)} db ({', '.join(sorted(nevek)[:3])}…)"
            for x, nevek in sorted(csoportok.items())
        )
    )
