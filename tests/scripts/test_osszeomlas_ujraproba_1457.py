"""Az összeomlott részfutás egyszeri újrapróbálása — és a hangos elszámolás.

## Miért

2026-08-25-én a QML-tesztek VÁLTOZÓ fájlokban omlottak össze a CI-ben
(`exit -11` Linuxon, `0xC0000005` Windowson) — öt bukás, öt különböző
fájl, egyetlen nap alatt (#1457). Helyben egyik sem reprodukálható. A
gyökérok felderítéséig a kiadási lánc teljesen megállt: minden futásban
volt egy véletlen összeomlás.

## Mit szabad és mit nem

Az időtúllépésre (`124`) MÁR VOLT egyszeri újrapróbálás (#53) — ez a
változás ugyanazt terjeszti ki a JELRE meghaló részfutásra. Amit
kifejezetten NEM szabad újrapróbálni: a tesztbukást (`1`) és a gyűjtési
hibát (`2..5`). Azok determinisztikusak; elfedni őket hazugság lenne.

És a legfontosabb: az összeomlás **akkor sem tűnhet el nyomtalanul**, ha
másodjára zöld. A futás végén tételes lista megy ki róla — enélkül a
retry pontosan azt a hamis biztonságot adná, ami ellen a #1457 nyílt.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]


def _run_tests_modul():
    utvonal = _ROOT / "scripts" / "run_tests.py"
    spec = importlib.util.spec_from_file_location("_run_tests_1457", utvonal)
    assert spec is not None and spec.loader is not None
    modul = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = modul
    spec.loader.exec_module(modul)
    return modul


class TestMitSzamitOsszeomlasnak:
    """A határok pontosan ott legyenek, ahol a szándék."""

    def test_a_jelre_halas_az(self):
        modul = _run_tests_modul()
        # POSIX: a subprocess a jelet negatív kódként adja vissza
        assert modul._osszeomlas(-11) is True, "SIGSEGV (-11)"
        assert modul._osszeomlas(-6) is True, "SIGABRT (-6)"
        # Windows NTSTATUS
        assert modul._osszeomlas(0xC0000005) is True, "ACCESS_VIOLATION"
        assert modul._osszeomlas(0xC0000374) is True, "heap-sérülés"

    def test_a_TESZTBUKAS_NEM_az(self):
        """Ha ez elromlik, az újrapróbálás valódi hibát fedne el."""
        modul = _run_tests_modul()
        assert modul._osszeomlas(1) is False, (
            "a tesztbukást SOHA nem szabad újrapróbálni — determinisztikus"
        )
        assert modul._osszeomlas(2) is False, "gyűjtési hiba"
        assert modul._osszeomlas(5) is False, "nem futott egyetlen teszt sem"
        assert modul._osszeomlas(124) is False, (
            "az időtúllépésnek SAJÁT ága van (#53), nem ezen keresztül megy"
        )
        assert modul._osszeomlas(0) is False, "a zöld futás nem összeomlás"


class TestAzElszamolasNemNema:
    """A retry akkor ér valamit, ha a tény nem tűnik el vele együtt."""

    def test_a_futtato_kiirja_az_elsore_osszeomlott_fajlokat(self):
        forras = (_ROOT / "scripts" / "run_tests.py").read_text(encoding="utf-8")

        assert "_OSSZEOMLAS_UJRAPROBA" in forras, (
            "nincs nyilvántartás arról, mi omlott össze elsőre"
        )
        assert "ELSŐRE ÖSSZEOMLOTT, MÁSODJÁRA ZÖLD" in forras, (
            "az összeomlás némán eltűnik, ha másodjára zöld lett — pont ez "
            "az a hamis biztonság, ami ellen a #1457 nyílt"
        )
        assert "#1457" in forras, "a jegyszám nélkül a lista nem vezet sehova"

    def test_a_lista_a_bukas_jelentese_ELOTT_megy_ki(self):
        """Sorrend: előbb az összeomlás-lista, aztán a bukások.

        Fordítva a bukások zaja elnyelné — a CI-naplót a végéről olvassuk."""
        forras = (_ROOT / "scripts" / "run_tests.py").read_text(encoding="utf-8")
        lista = forras.find("ELSŐRE ÖSSZEOMLOTT, MÁSODJÁRA ZÖLD")
        bukasok = forras.find('print("\\nHIBÁS RÉSZFUTÁSOK:"')
        assert lista != -1 and bukasok != -1
        assert lista < bukasok, (
            "az összeomlás-lista a bukás-jelentés UTÁN áll — a napló végén "
            "a bukások zaja alá kerülne"
        )
