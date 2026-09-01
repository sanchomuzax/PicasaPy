"""#1904: a válogatótálca TÖRDEL és ÁTMÉRETEZ — nem vág le némán.

## Mit mért az eredeti

Húsz referencia-felvétel (`research/Picasa3-also-talca-ikonok-viselkedese/`),
ugyanabban az 1920×1080-as ablakméretben:

| kijelölt | sorok | bélyegkép-magasság |
|---|---|---|
| 15 kép | 1 sor | ~55 képpont |
| 67 kép | 3 sor | ~22 képpont |

A doboz KÜLSŐ mérete közben nem változik. Tehát nem görgetősáv és nem
levágás: **átméretezés + tördelés**.

## Mit adott a mi tálcánk

Egyetlen `Row`, `clip: true` — a dobozba be nem férő bélyegképek egyszerűen
ELTŰNTEK. Hatvanhét kijelölt képből a felhasználó nyolcat látott, és semmi
nem jelezte, hogy a többi is a tálcában van. A kék infó-csík közben 67-et
írt: a felület önmagának mondott ellent.

## Amit ez az őr állít

1. a doboz magassága FIX (81 képpont), akárhány kép van benne;
2. **minden** bélyegkép a dobozon BELÜL van — se vízszintesen, se
   függőlegesen nem lóg ki (ez a levágás foga);
3. sok képnél TÖBB SOR keletkezik, és a bélyegképek kisebbek lesznek.

⚠️ A képpontos geometria (a magasság KÉPLETE a darabszámból) a #1904-ben
nyitott kérdés: két mért pontunk van, a levezetés nincs meg. Ez az őr
ezért a VISELKEDÉST rögzíti (fix doboz · semmi nem lóg ki · több sor),
nem a konkrét képpontszámot — azt a mérés majd szigorítja.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg


def _walk(item: QQuickItem):
    """A VIZUÁLIS fa bejárása — a `Repeater` elemei csak itt látszanak."""
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _elemek(window, nev: str) -> list[QQuickItem]:
    return [
        item
        for item in _walk(window.contentItem())
        if item.objectName() == nev
    ]


def _elem(window, nev: str) -> QQuickItem:
    talalt = _elemek(window, nev)
    assert talalt, f"a(z) {nev} nincs a kirajzolt jelenetben"
    return talalt[0]


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _kepekkel(qml_app, qt_app, darab: int):
    """`darab` kép a könyvtárban, mind kijelölve."""
    window, controller, _engine = qml_app
    lib = Path(controller.watchedFolders[0])
    for i in range(darab):
        make_jpeg(lib / f"t{i:03d}.jpg", size=(80, 60))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()
    sorok = list(range(min(darab, controller.photos.rowCount())))
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    qt_app.processEvents()
    assert _var(qt_app, lambda: len(_elemek(window, "trayPreviewThumb")) >= len(sorok))
    return window, len(sorok)


def _bélyegképek(window):
    return _elemek(window, "trayPreviewThumb")


class TestFixDoboz:
    def test_a_doboz_magassaga_valtozatlan_sok_kepnel(self, qml_app, qt_app):
        window, _ = _kepekkel(qml_app, qt_app, 40)
        assert _elem(window, "trayScratchBack").height() == 81


class TestSemmiNemLogKi:
    """A levágás foga: MINDEN bélyegkép a sávon belül van."""

    def _ellenoriz(self, window, darab: int) -> None:
        sav = _elem(window, "trayScratchStrip")
        kilogo = [
            (item.x(), item.y(), item.width(), item.height())
            for item in _bélyegképek(window)
            if item.x() < -0.5
            or item.y() < -0.5
            or item.x() + item.width() > sav.width() + 0.5
            or item.y() + item.height() > sav.height() + 0.5
        ]
        assert not kilogo, (
            f"{darab} képből {len(kilogo)} lóg ki a "
            f"{sav.width():.0f}×{sav.height():.0f}-es sávból: {kilogo[:3]}"
        )

    def test_kevés_kepnel(self, qml_app, qt_app):
        window, darab = _kepekkel(qml_app, qt_app, 5)
        self._ellenoriz(window, darab)

    def test_sok_kepnel(self, qml_app, qt_app):
        window, darab = _kepekkel(qml_app, qt_app, 40)
        self._ellenoriz(window, darab)


class TestTordeles:
    def test_sok_kepnel_tobb_sor_es_kisebb_belyegkep(self, qml_app, qt_app):
        window, _ = _kepekkel(qml_app, qt_app, 5)
        kevés = _bélyegképek(window)[0].height()
        sorok_kevés = {round(item.y()) for item in _bélyegképek(window)}

        window, _ = _kepekkel(qml_app, qt_app, 40)
        sok = _bélyegképek(window)[0].height()
        sorok_sok = {round(item.y()) for item in _bélyegképek(window)}

        assert len(sorok_kevés) == 1, "öt kép egyetlen sorba fér"
        assert len(sorok_sok) > 1, "negyven kép nem fér egyetlen sorba"
        assert sok < kevés, "több sornál a bélyegképnek zsugorodnia kell"
