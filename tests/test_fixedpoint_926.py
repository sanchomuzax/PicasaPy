"""A C egész-osztás szemantikájának őrei (#926).

A natívból portolt osztásoknál a Python `//` PADLÓZ, a C `/` (x86 `idiv`)
viszont NULLA felé csonkol — negatív számlálónál pontosan 1 az eltérés.
A közös segédfüggvény a `picasapy.fixedpoint.c_int_div`.
"""

from __future__ import annotations

import ast
from pathlib import Path

import numpy as np
import pytest

from picasapy.fixedpoint import c_int_div

SRC_ROOT = Path(__file__).resolve().parents[1] / "src" / "picasapy"


def _abszolut_ertek_hanyadosok(gyoker: Path, kivetel: str | None) -> list[str]:
    """`abs(...) // ...` alakú osztások a fában — a csonkoló ág ujjlenyoma.

    Pontosan azt a szerkezetet keresi, amit a három megtalált másolat
    használt: egy `abs` vagy `np.abs` hívás egy `//` BAL oldalán. Ez elég
    szűk ahhoz, hogy ne jelezzen ártatlan `//`-t, és elég tág ahhoz, hogy
    a segédfüggvény nevétől függetlenül fogjon.
    """
    talalatok: list[str] = []
    for forras in sorted(gyoker.rglob("*.py")):
        if kivetel is not None and forras.name == kivetel:
            continue
        fa = ast.parse(forras.read_text(encoding="utf-8"))
        szulo_neve = {}
        for fuggveny in ast.walk(fa):
            if isinstance(fuggveny, ast.FunctionDef):
                for leszarmazott in ast.walk(fuggveny):
                    szulo_neve.setdefault(id(leszarmazott), fuggveny.name)
        for csomopont in ast.walk(fa):
            if not isinstance(csomopont, ast.BinOp):
                continue
            if not isinstance(csomopont.op, ast.FloorDiv):
                continue
            if not _abszolut_ertek_hivas(csomopont.left):
                continue
            hely = szulo_neve.get(id(csomopont), "<modulszint>")
            talalatok.append(f"{forras.name}:{hely}")
    return talalatok


def _abszolut_ertek_hivas(csomopont: ast.expr) -> bool:
    """Igaz, ha a kifejezés `abs(...)` vagy `np.abs(...)` hívás."""
    if not isinstance(csomopont, ast.Call):
        return False
    fuggveny = csomopont.func
    if isinstance(fuggveny, ast.Name):
        return fuggveny.id == "abs"
    return isinstance(fuggveny, ast.Attribute) and fuggveny.attr == "abs"


class TestSkalarAlak:
    """A jegyben nevesített skalár esetek."""

    @pytest.mark.parametrize(
        ("szamlalo", "oszto", "vart"),
        [
            (-7, 2, -3),  # a `//` -4-et adna
            (7, -2, -3),  # a `//` -4-et adna
            (-8, 2, -4),  # osztható: a két szemantika egybeesik
            (7, 2, 3),
            (-7, -2, 3),
            (0, 5, 0),
            (-1, 2, 0),  # a `//` -1-et adna
            (1, -2, 0),
        ],
    )
    def test_nulla_fele_csonkol(self, szamlalo: int, oszto: int, vart: int) -> None:
        assert c_int_div(szamlalo, oszto) == vart

    def test_skalarra_python_int_jon_vissza(self) -> None:
        eredmeny = c_int_div(-7, 2)
        assert isinstance(eredmeny, int)
        assert not isinstance(eredmeny, np.ndarray)

    def test_egyezik_a_fuggetlen_referenciaval(self) -> None:
        """Független mérce: a lebegőpontos hányados nulla felé vágva.

        A tartomány elég kicsi ahhoz, hogy az `int(a / b)` pontosan a C
        `idiv` eredményét adja, tehát nem a megvalósítást ismétli meg.
        """
        for szamlalo in range(-40, 41):
            for oszto in range(-9, 10):
                if oszto == 0:
                    continue
                assert c_int_div(szamlalo, oszto) == int(szamlalo / oszto)


class TestTombosAlak:
    """Ugyanaz numpy-tömbre — ez hiányzott a modul-lokális változatból."""

    def test_tombre_elemenkent_csonkol(self) -> None:
        szamlalok = np.array([-7, 7, -8, 7, -1], dtype=np.int64)
        eredmeny = c_int_div(szamlalok, 2)
        assert isinstance(eredmeny, np.ndarray)
        np.testing.assert_array_equal(eredmeny, np.array([-3, 3, -4, 3, 0]))

    def test_negativ_oszto_tombben_is(self) -> None:
        osztok = np.array([-2, 2, -2, 2], dtype=np.int64)
        eredmeny = c_int_div(np.array([7, 7, -7, -7], dtype=np.int64), osztok)
        np.testing.assert_array_equal(eredmeny, np.array([-3, 3, 3, -3]))

    def test_ketdimenzios_alak_megmarad(self) -> None:
        szamlalok = np.array([[-7, 7], [-8, 9]], dtype=np.int64)
        eredmeny = c_int_div(szamlalok, 2)
        assert eredmeny.shape == (2, 2)
        np.testing.assert_array_equal(eredmeny, np.array([[-3, 3], [-4, 4]]))

    def test_a_bemenet_nem_valtozik(self) -> None:
        szamlalok = np.array([-7, 7], dtype=np.int64)
        masolat = szamlalok.copy()
        c_int_div(szamlalok, 2)
        np.testing.assert_array_equal(szamlalok, masolat)

    def test_a_tombos_es_a_skalar_ag_egyezik(self) -> None:
        szamlalok = np.arange(-40, 41, dtype=np.int64)
        for oszto in (-9, -2, -1, 1, 2, 9):
            tombos = c_int_div(szamlalok, oszto)
            skalaris = [c_int_div(int(n), oszto) for n in szamlalok]
            np.testing.assert_array_equal(tombos, np.array(skalaris))


class TestNincsTobbMasolat:
    """KAPU: a csonkoló osztásból EGY megvalósítás lehet a fában.

    A #926 három egymástól független másolatot talált (`linear_blur`,
    `autocolor_matrix`, `color/classify`) — az egyik közülük az osztó
    előjelét nem is kezelte. A kapu azt méri, hogy nem születik negyedik.
    """

    def test_csak_a_fixedpoint_valositja_meg(self) -> None:
        gyanus = _abszolut_ertek_hanyadosok(SRC_ROOT, kivetel="fixedpoint.py")
        assert gyanus == [], (
            "Csonkoló egész-osztás saját megvalósítása a fixedpoint.py-n kívül: "
            + ", ".join(gyanus)
        )

    def test_a_kapunak_van_foga(self) -> None:
        """A minta ISMERT pozitívot is felismer — különben vak lenne."""
        talalatok = _abszolut_ertek_hanyadosok(SRC_ROOT, kivetel=None)
        assert "fixedpoint.py:_tombos_osztas" in talalatok
