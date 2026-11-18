"""Az importablak forrásválasztása VALÓDI kattintással (#7183).

A törlési mód csak olyan forrásnál él, amely a csatolt meghajtók listájából
jött, és a gyökerében `DCIM` mappa van. Az ide tartozó tesztek a csatolt
meghajtót a platformhatáron (`discover_mounted_sources`) helyettesítik egy
ideiglenes mappával, majd a legördülőt és annak sorát kattintással választják,
ahogy a felhasználó: a vezérlő függvényeit nem hívják közvetlenül.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.varakozas import var_feltetelre


def elem(gyoker, nev: str):
    talalat = gyoker.findChild(QObject, nev)
    assert talalat is not None, f"{nev} nem található"
    return talalat


def varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    if var_feltetelre(qt_app, feltetel, masodperc):
        return
    assert feltetel(), uzenet


def kattint(ablak, elem_, qt_app) -> None:
    """Valódi egérkattintás az elem megjelenített közepén."""
    assert elem_.property("enabled") is True, (
        f"{elem_.objectName()} le van tiltva"
    )
    assert elem_.width() > 0 and elem_.height() > 0, (
        f"{elem_.objectName()} nem kattintható"
    )
    kozep = elem_.mapToScene(QPointF(elem_.width() / 2, elem_.height() / 2))
    celablak = ablak.window() if isinstance(ablak, QQuickItem) else ablak
    QTest.mouseClick(
        celablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def kattint_letiltottra(ablak, elem_, qt_app) -> None:
    """Valódi kattintás egy LETILTOTT elemre: a felhasználó is megteheti."""
    assert elem_.property("enabled") is False, (
        f"{elem_.objectName()} nem tiltott"
    )
    kozep = elem_.mapToScene(QPointF(elem_.width() / 2, elem_.height() / 2))
    celablak = ablak.window() if isinstance(ablak, QQuickItem) else ablak
    QTest.mouseClick(
        celablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def datum_szerinti_bontas(ablak, qt_app) -> None:
    """A `Date Taken` rádió valódi kattintása: üres profilban a kézi cím az
    alapérték (#7183), a dátum szerinti bontást az import-tesztek így kérik."""
    kattint(ablak, elem(ablak, "importSourceNamingByDateRadio"), qt_app)
    assert ablak.property("namingMode") == "date"


def kattint_legordulo_sorra(ablak, qt_app, sor: int = 0) -> None:
    """A nyitott legördülő `sor`-adik sorára kattint."""
    hatar = time.monotonic() + 3.0
    lista = None
    while time.monotonic() < hatar:
        qt_app.processEvents()
        lista = next(
            (
                item
                for item in ablak.findChildren(QObject, "picasaComboList")
                if item.property("visible")
                and int(item.property("count")) > 0
                and float(item.property("contentHeight")) > 0
            ),
            None,
        )
        if lista is not None:
            break
        time.sleep(0.01)
    assert lista is not None, "a legördülő sorai nem épültek fel"
    sormagassag = float(lista.property("contentHeight")) / int(
        lista.property("count")
    )
    kozep = lista.mapToScene(
        QPointF(lista.width() / 2, sormagassag * (sor + 0.5))
    )
    celablak = ablak.window() if isinstance(ablak, QQuickItem) else ablak
    QTest.mouseClick(
        celablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(kozep.x()), round(kozep.y())),
    )
    qt_app.processEvents()


def _varj_beolvasasra(qt_app, ablak, darab: int | None) -> None:
    varj(
        qt_app,
        lambda: not ablak.property("scanning")
        and (darab is None or int(ablak.property("previewCount")) == darab),
        "a forrás beolvasása nem fejeződött be",
    )
    qt_app.processEvents()


def csatolt_kartya_kivalasztasa(
    ablak, vezerlo, qt_app, monkeypatch, utvonal: Path, nev: str = "Kartya",
    darab: int | None = None,
) -> None:
    """A csatolt meghajtók legördülőjéből VALÓDI kattintással választ."""
    from picasapy.app import import_source_controller as modul

    monkeypatch.setattr(
        modul,
        "discover_mounted_sources",
        lambda: [{"path": str(utvonal), "name": nev}],
        raising=False,
    )
    vezerlo.refreshMountedSources()
    qt_app.processEvents()
    doboz = elem(ablak, "importSourceMountedSourcesBox")
    varj(
        qt_app,
        lambda: int(doboz.property("count")) == 1,
        "a csatolt meghajtó nem jelent meg a listában",
    )
    kattint(ablak, doboz, qt_app)
    kattint_legordulo_sorra(ablak, qt_app)
    _varj_beolvasasra(qt_app, ablak, darab)


def elozmeny_forras_kivalasztasa(
    ablak, vezerlo, qt_app, utvonal: Path, darab: int | None = None
) -> None:
    """A korábbi források legördülőjéből VALÓDI kattintással választ."""
    vezerlo._remember_source(str(utvonal))
    qt_app.processEvents()
    doboz = elem(ablak, "importSourceRecentBox")
    varj(
        qt_app,
        lambda: doboz.property("visible") is True,
        "a korábbi források legördülője nem látszik",
    )
    kattint(ablak, doboz, qt_app)
    kattint_legordulo_sorra(ablak, qt_app)
    _varj_beolvasasra(qt_app, ablak, darab)
