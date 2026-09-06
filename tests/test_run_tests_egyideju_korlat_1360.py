"""Helyben legfeljebb KETTŐ egyidejű tesztfutás (#1360, #2532).

## A tulajdonos szava

    2026-09-06 reggel: „Tilos egynél több helyi CI tesztet futtatni az RPi-n."
    2026-09-06 este:   „Addig kérlek, állítsd be a 2-t az 1 helyett."

    (eredetileg, #1360: „Lokális (RPi-n futó) teszt egyszerre max 2 futhat.
     Ezt mindig elfelejti a developer agent.")

A szigorítás azért maradhatott el, mert közben a foglaló megbízhatóvá vált:
CSAK a dolgozó futás foglal, a várakozó nem (korábban két várakozó üres gépen
is kizárta egymást).

A gép négymagos, és a futtató maga is párhuzamosít. Két egyidejű teljes kör
CPU-éhezést okoz, amitől a fájlonkénti időkorlátba **valódi hiba nélkül** is
bele lehet futni — a bukás pedig „ingadozó tesztnek" látszik, és félrevezeti a
következő munkamenetet (#914).

A korlát **egyetlen szám** (`_EGYIDEJU_ALAP`, futásidőben a
`PICASAPY_TESZT_EGYIDEJU`): a foglaló tetszőleges N helyet kezel, tehát ha a
gép egyszer elbírna kettőt, egy szám átírása elég — kódot nem kell írni hozzá.
Az utolsó osztály (`TestKettoreAllithato`) pontosan ezt őrzi.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class TestSzabadHely:
    def test_helyet_kapva_azonnal_indul(self) -> None:
        alvasok: list[float] = []
        assert (
            run_tests._varj_szabad_helyre(
                korlat=1,
                varakozas_s=600,
                foglalo=lambda: Path("/hely"),
                alvo=alvasok.append,
            )
            is not None
        )
        assert alvasok == [], "fölöslegesen várt"

    def test_foglalt_gepen_VAR_amig_fel_nem_szabadul(self) -> None:
        """Nem indulhat el — de nem is bukhat el azonnal."""
        allapotok = iter([None, None, Path("/hely")])
        alvasok: list[float] = []
        assert (
            run_tests._varj_szabad_helyre(
                korlat=1,
                varakozas_s=600,
                foglalo=lambda: next(allapotok),
                alvo=alvasok.append,
            )
            is not None
        )
        assert len(alvasok) == 2, "nem várta ki a helyet"

    def test_idotullepes_eseten_NEM_indul_el(self) -> None:
        alvasok: list[float] = []
        assert (
            run_tests._varj_szabad_helyre(
                korlat=1,
                varakozas_s=30,
                foglalo=lambda: None,
                alvo=alvasok.append,
            )
            is None
        )
        assert sum(alvasok) >= 30, "a türelmi idő letelte előtt adta fel"

    def test_a_varakozas_LATHATO(self, capsys, monkeypatch) -> None:
        """Néma fagyás helyett mondja meg, kire vár."""
        allapotok = iter([None, Path("/hely")])
        monkeypatch.setattr(run_tests, "_hely_gazdai", lambda: [11, 22])
        run_tests._varj_szabad_helyre(
            korlat=2,
            varakozas_s=600,
            foglalo=lambda: next(allapotok),
            alvo=lambda _: None,
        )
        kimenet = capsys.readouterr().out
        assert "11" in kimenet and "22" in kimenet, "nem mondja meg, ki fut"

    def test_kikapcsolhato(self) -> None:
        assert (
            run_tests._varj_szabad_helyre(
                korlat=0, varakozas_s=600, foglalo=lambda: None, alvo=lambda _: None
            )
            is not None
        )


class TestHelyFoglalas:
    """#2532: a hely foglalása ATOMI, és CSAK a dolgozó futás foglal.

    A korábbi kapu a `/proc` parancssorát nézte, tehát a VÁRAKOZÓT is
    foglalónak számolta. Mérve 2026-09-06-án: két várakozó ÜRES gépen is
    kizárta egymást, és mindkettő 75-tel lépett ki — pedig dolgozhattak volna.
    """

    def test_ket_kerobol_pontosan_egy_kap_helyet(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        assert run_tests._foglalj_helyet(1) is not None, "az első nem kapott helyet"
        assert run_tests._foglalj_helyet(1) is None, "a második is bejutott"

    def test_a_felszabadult_hely_ujra_kiadhato(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        elso = run_tests._foglalj_helyet(1)
        run_tests._engedd_el_a_helyet(elso)
        assert run_tests._foglalj_helyet(1) is not None, "a hely nem szabadult fel"

    def test_a_halott_futas_helye_nem_blokkol(self, tmp_path, monkeypatch) -> None:
        """Megszakított kör (kill, áramszünet) nem zárhat ki örökre másokat."""
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        run_tests._foglalj_helyet(1)
        monkeypatch.setattr(run_tests, "_el_e_a_futas", lambda hely: False)
        assert run_tests._foglalj_helyet(1) is not None, "a halott hely blokkolt"

    def test_az_ELO_futas_helye_blokkol(self, tmp_path, monkeypatch) -> None:
        """Az ellenpróba: élő gazdával a hely NEM vehető el."""
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        run_tests._foglalj_helyet(1)
        monkeypatch.setattr(run_tests, "_el_e_a_futas", lambda hely: True)
        assert run_tests._foglalj_helyet(1) is None, "elvette az élő futás helyét"

    def test_a_varakozo_NEM_foglal_helyet(self, tmp_path, monkeypatch) -> None:
        """A lényeg: aki vár, az nem vesz el helyet a többiektől."""
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        dolgozo = run_tests._foglalj_helyet(1)
        allapot = {"fut": True}

        def alvo(_):
            allapot["fut"] = False
            run_tests._engedd_el_a_helyet(dolgozo)

        hely = run_tests._varj_szabad_helyre(
            korlat=1,
            varakozas_s=600,
            foglalo=lambda: None if allapot["fut"] else run_tests._foglalj_helyet(1),
            alvo=alvo,
        )
        assert hely is not None, "a felszabadulás után sem indult el"


class TestWindowsNemKerdezPidet:
    """#2543: Windowson az `os.kill(pid, 0)` **Ctrl+C-t küld**, nem kérdez.

    A `0` ott a `CTRL_C_EVENT`. 2026-09-06-án a foglaló saját, duplikált
    életjel-függvénye emiatt ölte meg a windows-lábat: a tesztek lefutottak
    (6115 zöld), majd a futtatót `KeyboardInterrupt` állította le, és a főág
    pirosra váltott. Ez az őr LINUXON is fut — nem környezetfüggő kihagyás.
    """

    def test_windowson_nem_hivunk_os_kill_t(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        monkeypatch.setattr(run_tests, "_platform", lambda: "win32")

        def tilos(*a, **k):
            raise AssertionError("os.kill hívás Windowson — ez Ctrl+C-t küldene")

        monkeypatch.setattr(run_tests, "_kill", tilos)
        hely = run_tests._foglalj_helyet(1)
        assert hely is not None
        # a második kérő ugyanezen az ágon megy végig — nem szabad kérdeznie
        assert run_tests._foglalj_helyet(1) is None
        assert run_tests._elhagyott_hely(hely) is False, "frisset elhagyottnak vette"


class TestKettoreAllithato:
    """Ha a gép egyszer elbírna kettőt: EGY szám átírása legyen elég (#2532)."""

    def test_ket_hely_eseten_ketto_fer_be(self, tmp_path, monkeypatch) -> None:
        monkeypatch.setattr(run_tests, "_HELYEK_GYOKER", tmp_path / "helyek")
        assert run_tests._foglalj_helyet(2) is not None
        assert run_tests._foglalj_helyet(2) is not None, "a második nem fért be"
        assert run_tests._foglalj_helyet(2) is None, "a harmadik is bejutott"

    def test_a_kornyezeti_valtozo_egy_szoval_atallitja(self, monkeypatch) -> None:
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setenv("PICASAPY_TESZT_EGYIDEJU", "2")
        assert run_tests._egyideju_korlat() == 2


class TestCIVedelem:
    def test_a_CI_t_SOHA_nem_foghatja_meg(self, monkeypatch) -> None:
        """⚠️ A CI-ben minden job saját gépen fut; ott a korlát értelmetlen,
        és ha egyszer megfogná, a főág pirosra váltana."""
        monkeypatch.setenv("CI", "true")
        assert run_tests._egyideju_korlat() == 0

    def test_helyben_KETTO_az_alapertelmezes(self, monkeypatch) -> None:
        """A tulajdonos döntése 2026-09-06 estéjén: kettő.

        Aznap reggel egyre szigorítottuk; miután a foglaló megbízhatóvá vált
        (csak a DOLGOZÓ futás foglal), a korlát visszaállt kettőre."""
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("PICASAPY_TESZT_EGYIDEJU", raising=False)
        assert run_tests._egyideju_korlat() == 2


class TestKilepes:
    def test_a_kilepes_kimondja_hogy_NEM_a_tesztek_buktak(
        self, monkeypatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Enélkül az éjszakai műszak tesztbukásnak hiszi, és „javítani"
        kezdi azt, ami nem romlott el."""
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)
        monkeypatch.setattr(run_tests, "_bejelentkezes", lambda: None)
        monkeypatch.setattr(run_tests, "_varj_szabad_helyre", lambda **k: None)
        monkeypatch.setattr(
            run_tests, "_futtat", lambda *a, **k: pytest.fail("nem indulhatott volna")
        )

        kod = run_tests.main([])

        assert kod == run_tests._NINCS_HELY_KOD
        kimenet = capsys.readouterr().out
        assert "NEM a tesztek" in kimenet
