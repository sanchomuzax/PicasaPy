"""#6344/#6349: elérhetetlen NAS-megosztás nem tarthatja fel a fő szálat."""

from __future__ import annotations

import threading
import time

import pytest

from picasapy import halozati_ut


@pytest.fixture(autouse=True)
def _tiszta():
    halozati_ut._alaphelyzet()
    yield
    halozati_ut._alaphelyzet()


def test_a_gyoker_csak_unc_utvonalra():
    assert halozati_ut.halozati_gyoker(r"\\NAS\lemez\export\a") == "\\\\nas\\lemez\\"
    assert halozati_ut.halozati_gyoker("//NAS/lemez/x") == "\\\\nas\\lemez\\"
    assert halozati_ut.halozati_gyoker(r"C:\Képek\a") is None
    assert halozati_ut.halozati_gyoker("/mnt/nas/a") is None


def test_helyi_utvonalhoz_nem_nyul(monkeypatch):
    monkeypatch.setattr(halozati_ut, "_letezik", lambda _: pytest.fail("lemezművelet"))
    assert halozati_ut.elerheto(r"C:\Képek") is True


def test_a_nem_valaszolo_megosztas_az_idokorlaton_belul_hamis_es_megjegyzett(monkeypatch):
    elakadt = threading.Event()
    hivasok = []

    def lassu(ut):
        hivasok.append(ut)
        elakadt.wait(5)
        return False

    monkeypatch.setattr(halozati_ut, "_letezik", lassu)
    kezdet = time.monotonic()
    assert halozati_ut.elerheto(r"\\NAS\lemez\a", idokorlat_s=0.1) is False
    assert time.monotonic() - kezdet < 1.0
    # a második kérdés már várakozás és új próba nélkül felel
    kezdet = time.monotonic()
    assert halozati_ut.elerheto(r"\\NAS\lemez\b\c") is False
    assert time.monotonic() - kezdet < 0.05
    assert len(hivasok) == 1
    elakadt.set()


def test_az_elerheto_megosztas_igaz(monkeypatch):
    monkeypatch.setattr(halozati_ut, "_letezik", lambda _: True)
    assert halozati_ut.elerheto(r"\\NAS\lemez\a") is True


def test_az_ini_forras_az_elerhetetlen_megosztast_meg_sem_nezi(monkeypatch, tmp_path):
    """A hívóhely a próbát kérdezi: elérhetetlen megosztáson a létező fájl
    sem számít forrásnak — ugyanaz, amit az időkorlát lejárta adott volna."""
    from picasapy.ini import io

    ini = tmp_path / ".picasa.ini"
    ini.write_text("[x]\n", encoding="utf-8")
    assert io.ini_source_path(ini) == ini
    monkeypatch.setattr(io, "elerheto", lambda _ut: False)
    assert io.ini_source_path(ini) is None


def test_az_elerhetetlen_exportcel_kimarad_a_navigaciobol(monkeypatch, tmp_path):
    from picasapy.app import exported_folders

    assert exported_folders.existing_exported_folders([str(tmp_path)]) == [str(tmp_path)]
    monkeypatch.setattr(exported_folders, "elerheto", lambda _ut: False)
    assert exported_folders.existing_exported_folders([str(tmp_path)]) == []
