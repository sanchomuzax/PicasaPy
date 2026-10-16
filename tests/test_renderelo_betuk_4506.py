"""A szövegrajzoló próbák betűpótlása üres Qt-adatbázisnál (#4506).

A windowsos offscreen Qt a rendszerbetűket nem látja; a #4870 ezt globális
`QT_QPA_FONTDIR`-rel oldotta, ami MINDEN próba rajzolását megváltoztatta (a
main windows-lábának mind a négy darabja bukott). A pótlás ezért csak üres
adatbázisnál lép, és csak a kért próbákra (`renderelo_betuk` fixture).
"""

from __future__ import annotations

from pathlib import Path

from support.betucsalad import betufajlok_regisztralasa, potlando_betufajlok

_A = Path("C:/Windows/Fonts/arial.ttf")
_B = Path("C:/Windows/Fonts/arialbd.ttf")


def test_ures_adatbazisnal_a_jeloltek_regisztralandok():
    assert potlando_betufajlok([], [_A, _B]) == [_A, _B]


def test_csak_alnevek_es_probabetuk_mellett_is_potol():
    csaladok = ["Monospace", "Sans Serif", "Serif", "Open Sans", "Open Sanz"]
    assert potlando_betufajlok(csaladok, [_A]) == [_A]


def test_rendes_adatbazisnal_semmit_nem_potol():
    assert potlando_betufajlok(["DejaVu Sans", "Liberation Serif"], [_A, _B]) == []
    assert potlando_betufajlok(["Sans Serif", "Arial"], [_A]) == []


def test_a_hianyzo_es_ismetlodo_jelolteket_elhagyja():
    assert potlando_betufajlok([], [None, _A, _A, None, _B]) == [_A, _B]


def test_a_regisztralas_a_sikertelen_azonositot_elhagyja():
    hivasok: list[str] = []

    def hozzaad(ut: str) -> int:
        hivasok.append(ut)
        return -1 if ut.endswith("arialbd.ttf") else len(hivasok)

    assert betufajlok_regisztralasa([_A, _B], hozzaad) == {_A: 1}
    assert hivasok == [str(_A), str(_B)]


def test_a_globalis_betukonyvtar_beallitas_nem_tert_vissza():
    """A #4870-es globális `QT_QPA_FONTDIR` nem kerülhet vissza a conftestbe."""
    forras = (Path(__file__).parent / "conftest.py").read_text(encoding="utf-8")
    assert "QT_QPA_FONTDIR" not in forras
