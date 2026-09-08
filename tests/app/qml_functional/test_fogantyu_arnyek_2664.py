"""A fogantyú RAJZA kisebb a rétegnél — a különbség az árnyék (#2664).

## A lelet

A `respack.yt` mindkét fogantyú-rétege 2 képponttal szélesebb és 3-mal
magasabb, mint a benne álló TÖMÖR rajz:

| réteg | a réteg | a tömör rajz |
|---|---|---|
| `scaleslider/thumb` | 16 × 22 | **14 × 19** |
| `editslider/thumb` | 16 × 26 | **14 × 23** |

A különbség a lágy ÁRNYÉK, jobbra és lefelé. A mi fogantyúnk eddig a TELJES
réteg-dobozt kifestette, tehát 2 képponttal szélesebb és 3-mal magasabb tömör
foltot adott az eredetinél.

## A döntés (a jegy két útja közül az 1.)

**A doboz marad** a réteg mérete (a Layout helye, tehát a környező elrendezés
mért állandói — #1345/#1367 — érintetlenek), és a RAJZ húzódik be. Így a
geometria egyezik az eredetivel, és a vésés a RAJZ közepére kerül (a #2641
mérése: x = 6 és 7 a 14 széles rajzban) — nem a dobozéra.

⚠️ **MÉRT az árnyék KITERJEDÉSE** (2 és 3 képpont); a lágyulás profilja NINCS
mérve — a három, egyre halványabb réteg a MI rajzunk.
"""

from __future__ import annotations

import pytest

from tests.app.qml_functional.test_csuszka_veset_2641 import (
    ARNYEK_ALUL,
    ARNYEK_JOBB,
    FOGANTYU_MAGAS,
    FOGANTYU_SZELES,
    _rajzol,
    _vilagossag,
)

#: A #2656 mért sarokértékei (a RAJZ négy sarka, világosság).
MERT_SARKOK = {"bal-fent": 245, "bal-lent": 225, "jobb-fent": 234, "jobb-lent": 211}

#: A sarok-mérés tűrése: a kerekítés és a keret 1 képpontos élsimítása miatt.
TURES = 6


@pytest.fixture(scope="module")
def rajz(qt_app):
    return _rajzol(qt_app, FOGANTYU_SZELES, FOGANTYU_MAGAS)


def _sarok_ertekek(kep, doboz):
    """A RAJZ négy sarka, a kerettől 2 képponttal beljebb."""
    x, y, szeles, magas = doboz
    jobb = int(x) + szeles - ARNYEK_JOBB - 3
    also = int(y) + magas - ARNYEK_ALUL - 3
    return {
        "bal-fent": _vilagossag(kep, int(x) + 2, int(y) + 2),
        "bal-lent": _vilagossag(kep, int(x) + 2, also),
        "jobb-fent": _vilagossag(kep, jobb, int(y) + 2),
        "jobb-lent": _vilagossag(kep, jobb, also),
    }


def test_a_rajz_negy_sarka_a_mert_ertekek_kozeleben_van(rajz):
    kep, doboz = rajz
    kapott = _sarok_ertekek(kep, doboz)
    elteres = {
        nev: (round(ertek, 1), MERT_SARKOK[nev])
        for nev, ertek in kapott.items()
        if abs(ertek - MERT_SARKOK[nev]) > TURES
    }
    assert not elteres, f"a rajz sarkai eltérnek a mérttől (kapott/várt): {elteres}"


def test_a_doboz_JOBB_szele_ARNYEK_es_nem_a_tomor_rajz(rajz):
    """A réteg jobb szélső 2 oszlopa az ÁRNYÉKÉ: sötétebb a HÁTTÉRNÉL (tehát
    rajzolunk oda valamit), de világosabb a rajz kereténél (tehát nem a tömör
    fogantyú áll ott, ahogy eddig)."""
    kep, doboz = rajz
    x, y, szeles, magas = doboz
    kozep_y = int(y) + (magas - ARNYEK_ALUL) // 2
    keret = _vilagossag(kep, int(x) + szeles - ARNYEK_JOBB - 1, kozep_y)
    arnyek = _vilagossag(kep, int(x) + szeles - 1, kozep_y)
    hatter = _vilagossag(kep, int(x) + szeles + 4, kozep_y)
    assert arnyek < hatter, (
        f"a doboz jobb szélén ({arnyek:.1f}) nincs árnyék — a háttér {hatter:.1f}"
    )
    assert arnyek > keret, (
        f"a doboz jobb szélén ({arnyek:.1f}) még a tömör rajz áll (a keret "
        f"{keret:.1f}) — a rajznak 2 képponttal beljebb kell érnie"
    )


def test_a_doboz_ALSO_szele_ARNYEK_es_nem_a_tomor_rajz(rajz):
    """Ugyanez lefelé: az alsó 3 sor az árnyéké."""
    kep, doboz = rajz
    x, y, szeles, magas = doboz
    kozep_x = int(x) + (szeles - ARNYEK_JOBB) // 2
    keret = _vilagossag(kep, kozep_x, int(y) + magas - ARNYEK_ALUL - 1)
    arnyek = _vilagossag(kep, kozep_x, int(y) + magas - 1)
    hatter = _vilagossag(kep, kozep_x, int(y) + magas + 2)
    assert arnyek < hatter, (
        f"a doboz alján ({arnyek:.1f}) nincs árnyék — a háttér {hatter:.1f}"
    )
    assert arnyek > keret, (
        f"a doboz alján ({arnyek:.1f}) még a tömör rajz áll (a keret "
        f"{keret:.1f}) — a rajznak 3 képponttal feljebb kell érnie"
    )


def test_az_arnyek_HALVANYUL(rajz):
    """Az árnyék nem tömör folt: a doboz szélén halványabb, mint közvetlenül
    a rajz mellett. (A kiterjedés mért, a lágyulás a mi rajzunk — ez az őr
    csak azt köti meg, hogy tényleg lágy legyen.)"""
    kep, doboz = rajz
    x, y, szeles, magas = doboz
    kozep_x = int(x) + (szeles - ARNYEK_JOBB) // 2
    also_belso = _vilagossag(kep, kozep_x, int(y) + magas - ARNYEK_ALUL)
    also_kulso = _vilagossag(kep, kozep_x, int(y) + magas - 1)
    assert also_belso < also_kulso, (
        f"az árnyék nem halványul kifelé (belül {also_belso:.1f}, kívül "
        f"{also_kulso:.1f})"
    )
