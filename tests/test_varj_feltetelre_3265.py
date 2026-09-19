"""A közös, GC-szünetes várakozó (#3265).

A #3178 veremképe szerint a szegmentálás a FŐ SZÁL bevárás-hurkában, a
szemétgyűjtés közben történt, miközben egy háttérszál élt. Ez a segéd a
mért triggert szünetelteti — a modul már ugyanezt teszi a kollázs-jelzésnél
(#988/#1112).

⚠️ A próbasor NEM azt állítja, hogy a gyökér megvan: a `gc.disable()` csak a
ciklikus gyűjtőt állítja meg. Azt méri, hogy a segéd **be- és visszakapcsol**
— elszálló feltétel esetén is —, és hogy a várakozás viselkedése azonos a
fájlonkénti `_var` hurkokkal.
"""

from __future__ import annotations

import gc
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tests"))

from support.qt_wait import varj_feltetelre  # noqa: E402


class HamisApp:
    """`processEvents()`-et számoló, Qt nélküli helyettes."""

    def __init__(self) -> None:
        self.korok = 0

    def processEvents(self) -> None:  # noqa: N802 — Qt-névtan
        self.korok += 1


def test_igaz_feltetelre_azonnal_visszater() -> None:
    app = HamisApp()
    assert varj_feltetelre(app, lambda: True, 1.0) is True
    assert app.korok == 0, "az azonnal teljesülő feltétel ne pörgessen"


def test_a_feltetel_kesobb_teljesul() -> None:
    app = HamisApp()
    allapot = {"n": 0}

    def feltetel() -> bool:
        allapot["n"] += 1
        return allapot["n"] > 3

    assert varj_feltetelre(app, feltetel, 5.0) is True
    assert app.korok >= 3


def test_idotullepesnel_hamis() -> None:
    app = HamisApp()
    assert varj_feltetelre(app, lambda: False, 0.1) is False


def test_a_hurok_elnyeli_a_lebontas_kivetelet() -> None:
    """A fájlonkénti `_var` mintája: a lebontott Qt-objektum
    `RuntimeError`-ja nem bukás, hanem „még nem teljesült"."""
    app = HamisApp()

    def feltetel() -> bool:
        raise RuntimeError("Internal C++ object already deleted")

    assert varj_feltetelre(app, feltetel, 0.1) is False


class TestAGCSzunet:
    def test_a_varakozas_KOZBEN_szunetel(self) -> None:
        app = HamisApp()
        latott: list[bool] = []

        def feltetel() -> bool:
            latott.append(gc.isenabled())
            return len(latott) > 2

        assert gc.isenabled(), "a próba előfeltétele: a gyűjtő be van kapcsolva"
        varj_feltetelre(app, feltetel, 5.0)
        assert latott and not any(latott), (
            f"a gyűjtő nem szünetelt a bevárás közben: {latott}")

    def test_a_vegen_VISSZAKAPCSOL(self) -> None:
        app = HamisApp()
        assert gc.isenabled()
        varj_feltetelre(app, lambda: True, 1.0)
        assert gc.isenabled(), "a gyűjtő kikapcsolva maradt"

    def test_kivetel_eseten_is_visszakapcsol(self) -> None:
        """Egy elszálló teszt sem hagyhatja kikapcsolva a gyűjtőt."""
        app = HamisApp()

        def feltetel() -> bool:
            raise KeyboardInterrupt("a hívó elszállt")

        with pytest.raises(KeyboardInterrupt):
            varj_feltetelre(app, feltetel, 1.0)
        assert gc.isenabled(), "a gyűjtő kikapcsolva maradt a kivétel után"

    def test_kikapcsolhato(self) -> None:
        """A szünet kérésre elhagyható — mérő tesztek ezt igényelhetik."""
        app = HamisApp()
        latott: list[bool] = []

        def feltetel() -> bool:
            latott.append(gc.isenabled())
            return True

        varj_feltetelre(app, feltetel, 1.0, gc_szunet=False)
        assert latott == [True]

    def test_mar_kikapcsolt_gyujtot_nem_kapcsol_be(self) -> None:
        """Ha a hívó szándékosan kikapcsolta, a segéd ne írja felül."""
        app = HamisApp()
        gc.disable()
        try:
            varj_feltetelre(app, lambda: True, 1.0)
            assert not gc.isenabled(), (
                "a segéd bekapcsolta a hívó által kikapcsolt gyűjtőt")
        finally:
            gc.enable()
