"""#3399 — a görgetés-szinkronpont nem fogadhatja el a KIINDULÁSI platót.

A `test_qml_navigation._wait_for_scroll_settled` azt várta, hogy a `contentY`
két egymást követő lekérdezésben ne változzon. Ez akkor is teljesül, ha a
görgetés **még el sem indult** — a terhelt CI-futón a helper ilyenkor azonnal
„kész"-nek mondta a lépést, és a main ubuntu 3/4 darabja pirosra ment
(`assert 597.0 <= 1`, `TestArrowMinimalScroll::test_down_scrolls_just_enough`).

Ez a fájl magát a SEGÍTŐT méri, valódi rácsot nem: egy bábu, amelynek a
`contentY`-ja csak a harmadik lekérdezésre mozdul, pontosan azt az esetet
állítja elő, ami a CI-n előfordult.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, Property, Slot

from test_qml_navigation import _wait_for_scroll_settled


class _KesleltetettRacs(QObject):
    """Bábu-rács: a `contentY` az első `keses` lekérdezésig áll, majd mozdul.

    A `forceLayout` slot azért kell, mert a segítő `QMetaObject.invokeMethod`-dal
    hívja — bábun is léteznie kell, különben a mérés mást mérne.
    """

    def __init__(self, keses: int, cel: float = 120.0) -> None:
        super().__init__()
        self._keresesek = 0
        self._keses = keses
        self._cel = cel

    @Property(float)
    def contentY(self) -> float:  # noqa: N802 — a QML név
        self._keresesek += 1
        return 0.0 if self._keresesek <= self._keses else self._cel

    @Slot()
    def forceLayout(self) -> None:  # noqa: N802 — a QML név
        return None


class TestAKiindulasiPlatoNemMegallapodas:
    def test_a_meg_el_sem_indult_gorgetest_NEM_mondja_kesznek(self, qt_app):
        racs = _KesleltetettRacs(keses=4)
        # a kiindulás ismeretében a segítő kivárja a mozdulást
        assert _wait_for_scroll_settled(qt_app, racs, kiindulas=0.0) == 120.0

    def test_kiindulas_NELKUL_a_platot_elfogadja_ez_volt_a_hiba(self, qt_app):
        """Kontroll: enélkül a segítő a 0-s platóval tér vissza.

        Ez nem elvárás, hanem a HIBA rögzítése: aki a `kiindulas`-t elhagyja,
        ugyanazt a csapdát kapja, ami a mainet pirosra vitte. A navigációs
        tesztek ezért adják át, ahol a lépésnek mozdulnia kell.
        """
        racs = _KesleltetettRacs(keses=4)
        assert _wait_for_scroll_settled(qt_app, racs) == 0.0

    def test_ha_egyaltalan_nem_mozdul_akkor_MEGALL_es_kimondja(self, qt_app):
        racs = _KesleltetettRacs(keses=10**6)
        with pytest.raises(AssertionError, match="el sem indult"):
            _wait_for_scroll_settled(qt_app, racs, timeout_ms=120, kiindulas=0.0)

    def test_a_mozdulas_UTANI_megallapodast_varja_ki(self, qt_app):
        """A mozdulás után is két azonos lekérdezés kell — nem elég az első."""
        racs = _KesleltetettRacs(keses=1)
        assert _wait_for_scroll_settled(qt_app, racs, kiindulas=0.0) == 120.0
        # legalább három lekérdezés történt: a plató, a mozdulás, a megerősítés
        assert racs._keresesek >= 3
