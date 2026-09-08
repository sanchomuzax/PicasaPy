"""#2423 — a #2419 alakja a `test_save_controller._wait`-ben is megvolt.

## Mit all ez a fajl

Ket kulon allitas, mindketto DETERMINISZTIKUS (nem idozitesre epul):

1. **A sorrend.** A segito eloszor KOT BE, es csak azutan INDIT. A
   `_AzonnalJelzo` mar a hivas alatt, szinkron modon jelez: a regi
   sorrenddel (elobb inditas, aztan bekotes) ez a jelzes garantaltan
   elveszne, es a varakozas a teljes idokorlatot kiulve bukna.

2. **A szinkron ag nem pazarol idot.** A `QEventLoop.quit()` a `exec()`
   ELOTT kiadva ELVESZIK — ezen a gepen merve: egy `quit()` utan inditott
   hurok tovabbra is kiulte a teljes 2 mp-es idozitot. A #2422 helyes
   sorrendu segitoje emiatt HELYES eredmenyt adott, de a ket ora
   7,28 mp-et evett. Ha tehat a jelzes mar az `inditas()` alatt megjott,
   a hurokba be sem szabad lepni. Az itteni or ezt meri: a szinkron ag
   futasa az idokorlat toredeke.

A meres, ami a jegyet eldontotte: a `test_save_controller.py` ot
hivashelye koze tett 0,6 mp-es szunettel a fajl 2,74 mp helyett
77,65 mp alatt futott le, ot bukassal — mindegyik a 15 mp-es idokorlatot
kiulve. A javitas utan a szunet mar nem szamit, mert a bekotes elobb all.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QObject, Signal

from tests.app.test_regi_originals_a_feluleten_1425 import _wait as _wait_1425
from tests.app.test_save_controller import _wait as _wait_mentes

#: A ket segito ugyanazt a szerzodest teljesiti, ezert ugyanazok az orok
#: futnak rajuk. A `_wait_1425` a jelzes ARGUMENTUMAIT adja vissza, a
#: `_wait_mentes` a `done`/`failed` parost — az orok csak a sorrendet es az
#: idot merik, a visszaadott alakot nem.
SEGITOK = pytest.mark.parametrize(
    "varakozo", [_wait_1425, _wait_mentes], ids=["1425", "mentes"]
)

#: Boven a szinkron ut fole, de nagysagrendekkel az idokorlat alatt: ha a
#: hurok megis elindul, a mert ido az idokorlathoz all, nem ehhez.
FELSO_HATAR_MP = 0.5
IDOKORLAT_MS = 3000


class _AzonnalJelzo(QObject):
    """Olyan muvelet, amely mar a hivas alatt kesz — ez a legrosszabb eset."""

    kesz = Signal(int, int)

    def inditas(self) -> None:
        self.kesz.emit(3, 0)


@SEGITOK
def test_a_bekotes_a_kivaltas_elott_tortenik(qt_app, varakozo):
    """Nem az eredmenyt, hanem a SORRENDET allitja."""
    jelzo = _AzonnalJelzo()
    naplo: list[str] = []
    jelzo.kesz.connect(lambda *_: naplo.append("jelzes"))

    def inditas() -> None:
        naplo.append("inditas")
        jelzo.inditas()

    varakozo(jelzo.kesz, qt_app, inditas, timeout_ms=IDOKORLAT_MS)

    assert naplo == ["inditas", "jelzes"], (
        "a jelzesnek az inditas UTAN kell jonnie, de a bekotesnek MAR "
        f"allnia kellett — naplo: {naplo}"
    )


@SEGITOK
def test_a_szinkron_ag_nem_uli_ki_az_idokorlatot(qt_app, varakozo):
    """A hurokba be sem szabad lepni, ha a jelzes mar megjott."""
    jelzo = _AzonnalJelzo()

    kezdet = time.perf_counter()
    varakozo(jelzo.kesz, qt_app, jelzo.inditas, timeout_ms=IDOKORLAT_MS)
    eltelt = time.perf_counter() - kezdet

    assert eltelt < FELSO_HATAR_MP, (
        f"a szinkron ag {eltelt:.2f} mp-et vett el a {IDOKORLAT_MS} ms-os "
        "idokorlatbol — a segito belepett az esemenyhurokba, pedig a jelzes "
        "mar megvolt (a `quit()` a `exec()` elott elveszik)"
    )
