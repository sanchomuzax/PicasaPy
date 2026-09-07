"""A tesztfutások memóriaplafonja és az indulási gát (#2646).

2026-09-07 08:48, RPi5: az `earlyoom` SIGTERM-mel leállította a Claude
Desktop fő rendererét (VmRSS 3579 MiB) egy **1031 MiB-os QML-teszt
helyett**. Az earlyoom a legnagyobb RSS-t öli, tehát az áldozat
strukturálisan sosem a tettes — a rendszerszintű védelem képtelen a
tesztet célozni.

A javítás a **forrásnál** korlátoz: `systemd-run --user --scope
-p MemoryMax=… -p MemorySwapMax=0`. Így a túllépő részfutás EGYEDÜL hal
meg, determinisztikusan (mérve ezen a gépen: 300 MiB-os plafonnál a
próbafolyamat 270 MiB-nál elszállt, exit 137).

A `MemorySwapMax=0` nem díszítés: swapba lógva a folyamat nem hal meg,
csak a gépet fojtja — a 2 GiB zram aznap ~100%-on állt.
"""

from __future__ import annotations

import importlib.util
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_tests_2646", _GYOKER / "scripts" / "run_tests.py")
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)


class TestMemoriaBurok:
    def test_a_burok_plafont_es_swaptiltast_ad(self, monkeypatch):
        monkeypatch.setattr(rt, "_NINCS_MEMORIA_KORLAT", False)
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_platform", lambda: "linux")
        b = rt._memoria_burok()
        assert b[0] == "systemd-run"
        assert any(t.startswith("MemoryMax=") for t in b), "nincs plafon"
        assert "MemorySwapMax=0" in b, (
            "swap nélkül a folyamat nem hal meg, csak fojtja a gépet")
        assert b[-1] == "--", "a `--` nélkül a pytest kapcsolói a systemd-runé"

    def test_systemd_run_nelkul_ures(self, monkeypatch):
        """Fail-open: hiányzó eszköz nem akaszthatja meg a munkát."""
        monkeypatch.setattr(rt, "_NINCS_MEMORIA_KORLAT", False)
        monkeypatch.setattr(rt, "_which", lambda _: None)
        monkeypatch.setattr(rt, "_platform", lambda: "linux")
        assert rt._memoria_burok() == []

    def test_veszkijarat(self, monkeypatch):
        monkeypatch.setattr(rt, "_NINCS_MEMORIA_KORLAT", True)
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        assert rt._memoria_burok() == []


class TestSzabadMemoria:
    def test_a_meminfobol_olvas(self, tmp_path, monkeypatch):
        falso = tmp_path / "meminfo"
        falso.write_text("MemTotal: 8000000 kB\nMemAvailable: 2560000 kB\n")
        monkeypatch.setattr(rt, "_MEMINFO", falso)
        assert rt._szabad_memoria_mib() == 2500

    def test_olvashatatlan_meminfo_None(self, tmp_path, monkeypatch):
        """Nem Linuxon nincs `/proc/meminfo` — a gát ilyenkor ne tiltson."""
        monkeypatch.setattr(rt, "_MEMINFO", tmp_path / "nincs")
        assert rt._szabad_memoria_mib() is None


class TestIndulasiGat:
    """A hely önmagában kevés: az egyedi ~1 GiB ártalmatlan, a csúcsot a
    PÁRHUZAMOSSÁG csinálja."""

    @pytest.fixture(autouse=True)
    def _gat_bekapcsolva(self, monkeypatch):
        """A gát állapota KÖRNYEZETI VÁLTOZÓBÓL jön, importáláskor.

        Enélkül a készlet zöldje attól függ, hogy a futtató környezetében
        épp be van-e állítva a vészkijárat — a teszt némán semmit sem
        mérne. (Élesben megtörtént: egy mérőfutás
        `PICASAPY_TESZT_NINCS_MEMORIA=1`-gyel indult, és ez a három teszt
        emiatt bukott.)
        """
        monkeypatch.setattr(rt, "_NINCS_MEMORIA_KORLAT", False)

    def test_kevés_memorianal_nem_indul(self):
        assert rt._varj_eleg_memoriara(
            varakozas_s=0.0, alvo=lambda _: None,
            szabad_mem=lambda: 1477,               # a 09-07-i mért érték
        ) is False, "kevés memóriánál is elindult volna"

    def test_eleg_memorianal_indul(self):
        assert rt._varj_eleg_memoriara(
            varakozas_s=0.0, alvo=lambda _: None, szabad_mem=lambda: 4602)

    def test_a_memoria_felszabadulasa_utan_bejut(self):
        """Ellenpróba: a gát VÁR, nem véglegesen tilt."""
        ertekek = iter([1200, 1300, 5000, 5000])
        assert rt._varj_eleg_memoriara(
            varakozas_s=999.0, alvo=lambda _: None,
            szabad_mem=lambda: next(ertekek))

    def test_a_hely_tesztjei_NEM_fuggnek_a_memoriatol(self):
        """Ellenpróba: a hely-várakoztató ne kérdezze a memóriát.

        Ha a két dolog egy függvényben lenne, a #1360 foglalási tesztjei az
        ÉLŐ gépállapottól függenének. Élesben megtörtént: a teljes készleten
        két foglalási teszt bukott el emiatt, mert a mérés közben 2,5 GiB alá
        ment a szabad memória.
        """
        import inspect
        forras = inspect.getsource(rt._varj_szabad_helyre)
        assert "memoria" not in forras.lower(), (
            "a hely-várakoztató memóriát mér — ettől a foglalási tesztek "
            "élő gépállapottól függenek")

    def test_nem_merheto_memoria_nem_tilt(self):
        """`None` (nem Linux) esetén a gát nem szólhat bele."""
        assert rt._varj_eleg_memoriara(
            varakozas_s=0.0, alvo=lambda _: None, szabad_mem=lambda: None)
