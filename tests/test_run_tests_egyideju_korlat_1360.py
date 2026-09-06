"""Helyben legfeljebb EGY egyidejű tesztfutás (#1360, szigorítva: #2532).

## A lelet — a tulajdonos jelentette

    2026-09-06: „Tilos egynél több helyi CI tesztet futtatni az RPi-n."

    (korábban, #1360: „Lokális (RPi-n futó) teszt egyszerre max 2 futhat.
     Ezt mindig elfelejti a developer agent.")

A gép négymagos. Három-négy egyidejű teljes kör CPU-éhezést okoz, amitől a
fájlonkénti időkorlátba **valódi hiba nélkül** is bele lehet futni — a bukás
pedig „ingadozó tesztnek" látszik, és félrevezeti a következő munkamenetet
(#914).

A felismerés MEGVOLT (`_masik_futas_pidjei`), a korlát nem: akárhány session
indíthatott egyszerre kört, mindegyik szabályosan sorosra váltott, és a gép
mégis térdre ment. Egy szabály, amit betartatni kell, nem szabály: kapu.
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class TestSzabadHely:
    def test_korlat_alatt_azonnal_indul(self) -> None:
        """Üres gépen (nincs másik futás) azonnal indul."""
        alvasok: list[float] = []
        assert run_tests._varj_szabad_helyre(
            korlat=1,
            varakozas_s=600,
            pidek=lambda: [],
            alvo=alvasok.append,
        )
        assert alvasok == [], "fölöslegesen várt"

    def test_EGY_futas_mellett_a_masodik_MAR_var(self) -> None:
        """#2532: egyetlen dolgozó futás mellett a második nem indulhat.

        Ez az őr foga: a korábbi korlát (2) mellett ez a hívás AZONNAL
        elindult volna — a szám csökkentése nélkül a teszt megbukik."""
        alvasok: list[float] = []
        allapotok = iter([[11], [11], []])
        assert run_tests._varj_szabad_helyre(
            korlat=run_tests._EGYIDEJU_ALAP,
            varakozas_s=600,
            pidek=lambda: next(allapotok),
            alvo=alvasok.append,
        )
        assert len(alvasok) == 2, "nem várta ki a helyet a másik futás mellett"

    def test_korlaton_VAR_amig_fel_nem_szabadul(self) -> None:
        """A korlát fölötti futás nem indulhat el — de nem is bukhat el azonnal."""
        allapotok = iter([[11, 22], [11, 22], [11]])
        alvasok: list[float] = []
        assert run_tests._varj_szabad_helyre(
            korlat=2,
            varakozas_s=600,
            pidek=lambda: next(allapotok),
            alvo=alvasok.append,
        )
        assert len(alvasok) == 2, "nem várta ki a helyet"

    def test_idotullepes_eseten_NEM_indul_el(self) -> None:
        alvasok: list[float] = []
        assert not run_tests._varj_szabad_helyre(
            korlat=2,
            varakozas_s=30,
            pidek=lambda: [11, 22],
            alvo=alvasok.append,
        )
        assert sum(alvasok) >= 30, "a türelmi idő letelte előtt adta fel"

    def test_a_varakozas_LATHATO(self, capsys: pytest.CaptureFixture[str]) -> None:
        """Néma fagyás helyett mondja meg, kire vár."""
        allapotok = iter([[11, 22], [11]])
        run_tests._varj_szabad_helyre(
            korlat=2,
            varakozas_s=600,
            pidek=lambda: next(allapotok),
            alvo=lambda _: None,
        )
        kimenet = capsys.readouterr().out
        assert "11" in kimenet and "22" in kimenet, "nem mondja meg, ki fut"

    def test_kikapcsolhato(self) -> None:
        assert run_tests._varj_szabad_helyre(
            korlat=0, varakozas_s=600, pidek=lambda: [1, 2, 3, 4], alvo=lambda _: None
        )


class TestCIVedelem:
    def test_a_CI_t_SOHA_nem_foghatja_meg(self, monkeypatch) -> None:
        """⚠️ A CI-ben minden job saját gépen fut; ott a korlát értelmetlen,
        és ha egyszer megfogná, a főág pirosra váltana."""
        monkeypatch.setenv("CI", "true")
        assert run_tests._egyideju_korlat() == 0

    def test_helyben_EGY_az_alapertelmezes(self, monkeypatch) -> None:
        """#2532: a tulajdonos szabálya — egynél több helyi futás tilos."""
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.delenv("PICASAPY_TESZT_EGYIDEJU", raising=False)
        assert run_tests._egyideju_korlat() == 1

    def test_kornyezeti_valtozoval_felulirhato(self, monkeypatch) -> None:
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setenv("PICASAPY_TESZT_EGYIDEJU", "3")
        assert run_tests._egyideju_korlat() == 3


class TestKilepes:
    def test_a_kilepes_kimondja_hogy_NEM_a_tesztek_buktak(
        self, monkeypatch, capsys: pytest.CaptureFixture[str]
    ) -> None:
        """Enélkül az éjszakai műszak tesztbukásnak hiszi, és „javítani"
        kezdi azt, ami nem romlott el."""
        monkeypatch.delenv("CI", raising=False)
        monkeypatch.setattr(run_tests, "_takarits_regi_maradekot", lambda: None)
        monkeypatch.setattr(run_tests, "_bejelentkezes", lambda: None)
        monkeypatch.setattr(
            run_tests, "_varj_szabad_helyre", lambda **k: False
        )
        monkeypatch.setattr(
            run_tests, "_futtat", lambda *a, **k: pytest.fail("nem indulhatott volna")
        )

        kod = run_tests.main([])

        assert kod == run_tests._NINCS_HELY_KOD
        kimenet = capsys.readouterr().out
        assert "NEM a tesztek" in kimenet
