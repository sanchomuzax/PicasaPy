"""#1032: a futtató mondja meg, hány szálon fut — és ne éheztesse a gépet.

Egy CPU-éhezésben született bukás a naplóban UGYANÚGY néz ki, mint egy valódi.
A #914-es jegyet emiatt diagnosztizálta félre egy munkamenet: két teljes
tesztfutás osztozott négy magon, a bukást pedig a teszt számlájára írta.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class TestParhuzamDontes:
    """A kért érték nyer; automatikus visszalépés csak kérés hiányában van."""

    def test_kert_ertek_akkor_is_nyer_ha_masik_futas_van(self):
        """Aki explicit kér, tudja, mit csinál — nem írjuk felül."""
        assert run_tests._dontsd_el_a_parhuzamot("4", 4, masik_fut=True) == (
            4,
            "kérésre (PICASAPY_TESZT_PARHUZAM=4)",
        )

    def test_masik_futas_eseten_sorosra_valt(self):
        parhuzam, indok = run_tests._dontsd_el_a_parhuzamot(None, 4, masik_fut=True)
        assert parhuzam == 1
        assert "MÁSIK" in indok

    def test_egyedul_marad_az_alapertelmezes(self):
        assert run_tests._dontsd_el_a_parhuzamot(None, 4, masik_fut=False) == (
            4,
            "alapértelmezés",
        )

    def test_soros_alapertelmezes_nem_valt_semmire(self):
        """Ha amúgy is egy szálon futunk, nincs mit visszavenni."""
        assert run_tests._dontsd_el_a_parhuzamot(None, 1, masik_fut=True) == (
            1,
            "alapértelmezés",
        )


class TestEmlitesVsFuttatas:
    """A puszta névegyezés kevés — különben a fejlesztés maga riaszt.

    Élesben előfordult: a `ruff check scripts/run_tests.py ...` parancsot futtató
    SHELL parancssorában is ott volt a fájlnév, és az észlelés ettől azt hitte,
    hogy egy másik tesztfutás dolgozik.
    """

    def test_valodi_futtatas_felismerese(self):
        assert run_tests._futtatja_a_futtatot(
            "/usr/bin/python3\0scripts/run_tests.py\0--cov"
        )

    def test_abszolut_uttal_is(self):
        assert run_tests._futtatja_a_futtatot(
            "python3\0/home/valaki/PicasaPy/scripts/run_tests.py"
        )

    def test_shell_amelyik_csak_emliti(self):
        assert not run_tests._futtatja_a_futtatot(
            "/bin/bash\0-c\0ruff check scripts/run_tests.py tests/"
        )

    def test_lint_amelyik_csak_vizsgalja(self):
        assert not run_tests._futtatja_a_futtatot("ruff\0check\0scripts/run_tests.py")

    def test_hasonlo_nevu_tesztfajl_nem_szamit(self):
        assert not run_tests._futtatja_a_futtatot(
            "/usr/bin/python3\0-m\0pytest\0tests/test_run_tests_tmp_677.py"
        )

    def test_ures_parancssor(self):
        assert not run_tests._futtatja_a_futtatot("")


class TestMasikFutasEszlelese:
    def test_a_sajat_processzt_nem_szamolja_masiknak(self):
        """A futó teszt maga is `run_tests.py`-t importál — ne magára ijedjen."""
        assert run_tests.os.getpid() not in run_tests._masik_futas_pidjei()

    def test_nem_linuxon_ures_listat_ad(self, monkeypatch, tmp_path):
        """Windowson nincs /proc — ilyenkor nem tippelünk, hanem nem szólunk."""
        monkeypatch.setattr(run_tests, "Path", lambda *a, **k: tmp_path / "nincs-proc")
        assert run_tests._masik_futas_pidjei() == []


class TestBejelentkezes:
    def test_kiirja_a_szalszamot_es_a_magszamot(self, monkeypatch, capsys):
        monkeypatch.setattr(run_tests, "_masik_futas_pidjei", lambda: [])
        monkeypatch.setattr(run_tests, "_PARHUZAM", 4)
        monkeypatch.delenv("PICASAPY_TESZT_PARHUZAM", raising=False)

        run_tests._bejelentkezes()

        kimenet = capsys.readouterr().out
        assert "párhuzamos részfutás" in kimenet
        assert "mag" in kimenet

    def test_masik_futasnal_figyelmeztet_es_kiirja_a_pidet(self, monkeypatch, capsys):
        monkeypatch.setattr(run_tests, "_masik_futas_pidjei", lambda: [4242])
        monkeypatch.setattr(run_tests, "_PARHUZAM", 4)
        monkeypatch.delenv("PICASAPY_TESZT_PARHUZAM", raising=False)

        run_tests._bejelentkezes()

        kimenet = capsys.readouterr().out
        assert "FIGYELEM" in kimenet
        assert "4242" in kimenet
        assert "CPU-éhezés" in kimenet
        assert run_tests._PARHUZAM == 1, "másik futás mellett sorosra kell váltani"
