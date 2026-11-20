"""Biztos kattintás a keresési javaslatlista egy sorára.

A javaslatlista a gépelés után többször is újraépülhet. Előfordul, hogy a
tartalma alapján megtalált sor már a helyes adatot hordozza, de a helye még
nem állt be: a régi helyén ilyenkor egy másik sor áll, és a kattintás arra
esik (a CI-n „ai8” a mappasor helyett, illetve elmaradt második kattintás a
#7253-as próbában). Ez a segéd addig vár, amíg a sor mérete nem nulla, a
helye két egymást követő mintavételnél azonos, és a kattintási pontot egyetlen
másik látható javaslatsor sem fedi. Csak utána kattint.
"""

from __future__ import annotations

from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from tests.support.varakozas import var_feltetelre

SOR_NEV = "suggestionRow"


def _bejar(item):
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _kozeppont(sor) -> QPointF:
    return sor.mapToScene(QPointF(sor.width() / 2, sor.height() / 2))


def _pont_csak_e_sore(gyoker, sor, pont: QPointF) -> bool:
    for masik in _bejar(gyoker):
        if masik is sor or masik.objectName() != SOR_NEV or not masik.isVisible():
            continue
        if masik.width() <= 0 or masik.height() <= 0:
            continue
        if masik.contains(masik.mapFromScene(pont)):
            return False
    return True


def kattints_a_javaslatsorra(window, gyoker, sor_kereso, qt_app) -> None:
    """A `sor_kereso()` által adott sorra kattint, ha a helye már nem mozog.

    A `sor_kereso` minden mintavételnél újra megkeresi a sort, mert a lista
    újraépülésekor a delegált elem is kicserélődhet."""
    elozo: list[tuple[float, float] | None] = [None]

    def _kesz() -> bool:
        sor = sor_kereso()
        if sor is None or not sor.isVisible() or sor.width() <= 0 or sor.height() <= 0:
            elozo[0] = None
            return False
        pont = _kozeppont(sor)
        most = (pont.x(), pont.y())
        stabil = elozo[0] == most
        elozo[0] = most
        return stabil and _pont_csak_e_sore(gyoker, sor, pont)

    assert var_feltetelre(qt_app, _kesz), "a javaslatsor helye nem állt be"
    pont = _kozeppont(sor_kereso())
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()
