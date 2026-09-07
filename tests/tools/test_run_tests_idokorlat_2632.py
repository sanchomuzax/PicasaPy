"""#2632 — a NEM-app részfutás vészféke a MÉRT futásidőhöz van kötve.

## Miért van erre őr

A vészfék dolga a **befagyás** elkapása, nem a teljesítmény mérése. A
300 másodperces korlát a windows-lábon a mért futásidő **1,20-szerese**
volt, tehát nem tudta megkülönböztetni a lassú futót a beragadástól:

    2026-09-07 04:12  `6808 passed, 63 skipped … in 245.76s`
    2026-09-07 04:28  `6808 passed, 63 skipped … in 248.58s`

A 2026-09-06 21:20 óta indult **69 CI-futás 14 pirosából négy** pontosan
ezen a részfutáson lépett túl (`exit 124`) — ugyanaz a részfutás, ugyanaz
a láb, mindig ugyanaz az ok. Nem ingadozás: **következmény**.

⚠️ Ez az őr **nem** engedi a korlátot tetszés szerint emelni sem: a
felső határ is meg van adva. Egy órás vészfék már nem vészfék — egy
valódi befagyás annyi ideig blokkolná a CI-t, hogy a jelzés értéke
elvész.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "run_tests_2632", _GYOKER / "scripts" / "run_tests.py"
)
_MODUL = importlib.util.module_from_spec(_SPEC)
assert _SPEC.loader is not None
_SPEC.loader.exec_module(_MODUL)

#: Az alsó arány: a vészfék legalább kétszerese legyen a mért futásidőnek,
#: különben egy lassabb futó hamis pirosat ad (#2632).
MIN_ARANY = 2.0
#: A felső arány: egy vészfék, ami a normál futás ötszörösét is kivárja,
#: már nem jelez befagyást időben.
MAX_ARANY = 5.0


class TestANemAppVeszfek:
    def test_a_mert_futasido_ki_van_mondva(self):
        """A korlát csak akkor ellenőrizhető, ha a MÉRÉS is a forrásban van."""
        assert hasattr(_MODUL, "_NON_APP_MERT_FUTASIDO_S")
        assert 100 < _MODUL._NON_APP_MERT_FUTASIDO_S < 1000, (
            "a mért futásidő nem hihető — újramérve kell frissíteni"
        )

    def test_a_korlat_legalabb_KETSZERESE_a_mert_futasidonek(self):
        arany = _MODUL._NON_APP_TIMEOUT_S / _MODUL._NON_APP_MERT_FUTASIDO_S
        assert arany >= MIN_ARANY, (
            f"a vészfék a mért futásidő {arany:.2f}-szerese "
            f"({_MODUL._NON_APP_TIMEOUT_S} mp / "
            f"{_MODUL._NON_APP_MERT_FUTASIDO_S} mp) — a 300/249 = 1,20 "
            "pontosan ettől adott négy hamis pirosat (#2632)"
        )

    def test_a_korlat_nem_NO_TULSAGOSAN(self):
        """A másik irány: az emelés ne váljon a jelzés elnémításává."""
        arany = _MODUL._NON_APP_TIMEOUT_S / _MODUL._NON_APP_MERT_FUTASIDO_S
        assert arany <= MAX_ARANY, (
            f"a vészfék a mért futásidő {arany:.2f}-szerese — ennyi idő "
            "után a befagyás jelzése már késő"
        )

    def test_az_app_fajlok_korlatja_valtozatlan(self):
        """A #2632 CSAK a nem-app készletre szól; a fájlonkénti korlát a
        maga mérésén nyugszik (#155/#1030), azt nem mozdítjuk."""
        assert _MODUL._APP_FILE_TIMEOUT_S == 180
