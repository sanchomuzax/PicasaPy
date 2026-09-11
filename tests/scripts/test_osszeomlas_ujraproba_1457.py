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
        # #2264: a bukás-jelentés külön függvénybe került
        # (`jelentsd_a_bukasokat`), hogy olcsón mérhető legyen. Ezért a
        # sorrendet a `main()` TÖRZSÉN belül nézzük — a nyers forrásbeli
        # pozíció a függvény-kiemeléstől elcsúszna, pedig a kimenet
        # sorrendje változatlan.
        forras = (_ROOT / "scripts" / "run_tests.py").read_text(encoding="utf-8")
        torzs = forras[forras.index("def main("):]
        lista = torzs.find("ELSŐRE ÖSSZEOMLOTT, MÁSODJÁRA ZÖLD")
        bukasok = torzs.find("jelentsd_a_bukasokat(")
        assert lista != -1, "a `main()`-ből eltűnt az összeomlás-lista"
        assert bukasok != -1, "a `main()`-ből eltűnt a bukás-jelentés hívása"
        assert lista < bukasok, (
            "az összeomlás-lista a bukás-jelentés UTÁN áll — a napló végén "
            "a bukások zaja alá kerülne"
        )


class TestAzOsszeomlasNYOMAmegmarad:
    """#1457: az összeomlott részfutás KIMENETE is kell, nem csak a ténye.

    Mérve (2026-09-11, CI-napló): a `34561332733` futás windows-lábán a
    `test_projekt_mappa_figyeles_1123.py` `exit 3221226505`-tel omlott
    össze, a napló viszont CSAK az „ÚJRAPRÓBÁLÁS" sort tartalmazta. A
    részfutás `stderr`-je — benne a `faulthandler` veremképével, amit a
    futtató külön ezért kapcsol be — a `_KIMENET`-ben ült, és az
    újrapróbálás felülírta. A sikeres retry után tehát a nyom ELVESZETT,
    és a következő összeomlás megint vakon elemzendő.

    Ez a próba a párhuzamos ágat méri, mert a CI ott fut.
    """

    def _fajl(self, modul):
        return modul._ROOT / "tests" / "app" / "test_kitalalt_1457.py"

    def test_az_osszeomlott_reszfutas_kimenete_KIMEGY(self, tmp_path, capsys):
        modul = _run_tests_modul()
        fajl = self._fajl(modul)
        relative = str(fajl.relative_to(modul._ROOT))
        hivasok = []

        def hamis_run_pytest(args, timeout_s, **kwargs):
            hivasok.append(args)
            if len(hivasok) == 1:
                modul._KIMENET[relative] = (
                    "Fatal Python error: Segmentation fault\n"
                    "Current thread 0x00007f...:\n"
                    '  File "tests/app/test_kitalalt_1457.py", line 12 in test_x\n'
                )
                return -11
            modul._KIMENET[relative] = "1 passed"
            return 0

        modul._run_pytest = hamis_run_pytest
        modul._OSSZEOMLAS_UJRAPROBA.clear()
        bukasok = modul._app_fajlok_parhuzamosan(
            [fajl], cov=False, basetemp=tmp_path
        )
        kimenet = capsys.readouterr().out

        assert bukasok == [], "a sikeres újrapróbálás után nincs bukás"
        assert "Fatal Python error" in kimenet, (
            "az összeomlott részfutás kimenete nem került a naplóba — a "
            "faulthandler veremképe elveszett az újrapróbálással"
        )
        assert relative in modul._OSSZEOMLAS_UJRAPROBA

    def test_a_kimenet_az_UJRAPROBALAS_elott_all(self, tmp_path, capsys):
        """A naplóban a nyom a retry-sor ELŐTT legyen: így a két sor
        egymás mellett olvasható, és nem keveredik a retry kimenetével."""
        modul = _run_tests_modul()
        fajl = self._fajl(modul)
        relative = str(fajl.relative_to(modul._ROOT))

        hivasok = []

        def hamis_run_pytest(args, timeout_s, **kwargs):
            hivasok.append(args)
            modul._KIMENET[relative] = (
                "Fatal Python error: Segmentation fault"
                if len(hivasok) == 1
                else "1 passed"
            )
            return -11 if len(hivasok) == 1 else 0

        modul._run_pytest = hamis_run_pytest
        modul._OSSZEOMLAS_UJRAPROBA.clear()
        modul._app_fajlok_parhuzamosan([fajl], cov=False, basetemp=tmp_path)
        kimenet = capsys.readouterr().out
        assert kimenet.index("Fatal Python error") < kimenet.index("ÚJRAPRÓBÁLÁS")

    def test_a_SOROS_ag_is_kiirja(self, tmp_path, capsys):
        """A soros ág kimenete nem gyűjtött (`csendben=False`), tehát ott a
        nyom magától a képernyőre megy — de a JELÖLÉSNEK ott is látszania
        kell, hogy a napló olvasója tudja, mi tartozik az összeomláshoz."""
        modul = _run_tests_modul()
        fajl = self._fajl(modul)
        hivasok = []

        def hamis_run_pytest(args, timeout_s, **kwargs):
            hivasok.append(args)
            return -11 if len(hivasok) == 1 else 0

        modul._run_pytest = hamis_run_pytest
        modul._OSSZEOMLAS_UJRAPROBA.clear()
        modul._app_fajlok_sorosan([fajl], cov=False, basetemp=tmp_path)
        kimenet = capsys.readouterr().out
        assert "ÖSSZEOMLÁS" in kimenet, (
            "a soros ág nem jelöli meg, hol kezdődik az összeomlás nyoma"
        )
