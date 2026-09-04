"""#1750: a jelölhető menütétel felirata ne lógjon rá a jelölőnégyzetre.

## A mérés

A tulajdonos képernyőmentése (v0.8.146) a felirat és a jelölő átfedését
mutatta. Végigmérve a futó ablak MINDEN jelölhető menütételén
(`checkable === true`, a jelölő jobb széle vs. a felirat tényleges
kezdete = `contentItem.x + contentItem.leftPadding`):

```
jelölhető tétel összesen: 58     ÁTFEDŐ: 5
  Recent &changes                    jelölő vége=20.0   felirat=6.0
  Show Editing Controls              jelölő vége=20.0   felirat=6.0
  Test Mode (logs the next startup)  jelölő vége=20.0   felirat=6.0
  Thumbnails Only                    jelölő vége=20.0   felirat=6.0
  Use Color Management               jelölő vége=20.0   felirat=6.0
```

Mind az öt `PicasaMenuItem`. Az ok: a `PicasaMenuItem` saját
`contentItem`-et ad (`IconLabel`, #757 — az `&`-mnemonik miatt), és ezzel
elveszik a stílus alapértelmezett `leftPadding`-je, ami a jelölőnek
helyet hagy. A sima `MenuItem`-ek (53 db) helyesen 26-nál kezdik a
feliratot.

## Amit ez az őr állít

Egyetlen jelölhető menütétel felirata sem kezdődhet a jelölő jobb széle
előtt. Az őr a FUTÓ ablakon mér, nem a forráson — így egy későbbi
`contentItem`-csere is elbukna rajta.
"""

from __future__ import annotations

from PySide6.QtCore import QObject


def _jelolheto_tetelek(window):
    """(felirat, a jelölő jobb széle, a felirat kezdete) minden
    jelölhető, jelölővel és tartalommal rendelkező menütételre."""
    tetelek = {}
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
        jelolo_vege = (jelolo.property("x") or 0) + (jelolo.property("width") or 0)
        felirat_x = (
            (tartalom.property("x") or 0)
            + (tartalom.property("leftPadding") or 0)
        )
        tetelek[str(felirat)] = (jelolo_vege, felirat_x)
    return tetelek


def test_a_felirat_nem_log_ra_a_jelolore(qml_app, qt_app):
    window, _controller, _engine = qml_app
    tetelek = _jelolheto_tetelek(window)
    assert len(tetelek) > 20, (
        f"csak {len(tetelek)} jelölhető tételt találtam — a mérés nem "
        "járta be a menüsort, az állítás így semmit nem érne"
    )
    atfedok = {
        felirat: (vege, kezdet)
        for felirat, (vege, kezdet) in tetelek.items()
        if kezdet < vege
    }
    assert not atfedok, (
        "a felirat a jelölőnégyzetre lóg (felirat-kezdet < jelölő-vég): "
        + "; ".join(
            f"{f!r} jelölő={v} felirat={k}" for f, (v, k) in sorted(atfedok.items())
        )
    )


def test_a_javitott_tetelek_a_szomszedaikkal_egy_vonalban_allnak(qml_app, qt_app):
    """A hiány pótlása ne csak megszüntesse az átfedést, IGAZÍTSON is.

    Az első javításom a `jelölő.x`-et is beleszámolta a térközbe, és
    26 helyett 32-t adott: átfedés nem volt, de az öt tétel felirata
    beljebb csúszott volna a szomszédjainál. A menüben ez ugyanolyan
    feltűnő, mint az átfedés — ezért kap saját állítást.
    """
    window, _controller, _engine = qml_app
    kezdetek = {kezdet for _vege, kezdet in _jelolheto_tetelek(window).values()}
    assert len(kezdetek) == 1, (
        "a jelölhető tételek feliratai nem egy vonalban kezdődnek: "
        f"{sorted(kezdetek)}"
    )
