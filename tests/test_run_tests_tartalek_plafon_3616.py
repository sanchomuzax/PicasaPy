"""Tartalék memóriaplafon busz nélküli gépen (#3616).

2026-09-25, felhős Claude Code-munkamenet: a `run_tests.py` 3 mp alatt 1-es
kóddal kilépett, mert MINDEN részfutás `systemd-run --user --scope` alá
került (#2646), a konténerben viszont nincs felhasználói systemd-busz:
`Failed to connect to bus: No medium found`. A `systemd-run` bináris OTT
VOLT, tehát a régi `_which`-ellenőrzés nem vette észre, hogy nem működik.

A javítás két ág:

* **busz van** (RPi, helyi gép) — változatlanul a `systemd-run` scope fut,
  `MemoryMax` + `MemorySwapMax=0` (a #2646 indoka: swap-thrashing ellen);
* **busz nincs** — a részfutás egy apró Python-előtéten át indul, ami a
  GYEREKBEN `RLIMIT_AS`-t állít, és csak utána `exec`-eli a pytestet. Ezt a
  futtató egyetlen sorban kiírja: plafon nélkül nem fut, és nem hallgat el.
"""

from __future__ import annotations

import importlib.util
import subprocess
import sys
import types
from pathlib import Path

import pytest

_GYOKER = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_tests_3616", _GYOKER / "scripts" / "run_tests.py")
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)


@pytest.fixture(autouse=True)
def _linux_plafonnal(monkeypatch):
    """A környezet (vészkijárat, platform) ne döntse el a teszt zöldjét."""
    monkeypatch.setattr(rt, "_NINCS_MEMORIA_KORLAT", False)
    monkeypatch.setattr(rt, "_platform", lambda: "linux")
    monkeypatch.setattr(rt, "_SCOPE_ELERHETO", None)
    # #3636: Linuxot színlelünk, tehát a `resource` modult is — Windowson az `rt._resource` None
    monkeypatch.setattr(rt, "_resource", rt._resource or types.SimpleNamespace())


class _Eredmeny:
    def __init__(self, returncode: int) -> None:
        self.returncode = returncode


class TestBuszVan:
    def test_a_systemd_scope_fut_valtozatlanul(self, monkeypatch):
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_systemd_scope_elerheto", lambda: True)
        b = rt._memoria_burok()
        assert b[:4] == ["systemd-run", "--user", "--scope", "-q"]
        assert f"MemoryMax={rt._MEMORIA_PLAFON}" in b
        assert "MemorySwapMax=0" in b
        assert b[-1] == "--"

    def test_a_helyi_gepen_nincs_uj_kiiras(self, monkeypatch):
        """A helyi viselkedés változatlan — a kimenet sem lesz zajosabb."""
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_systemd_scope_elerheto", lambda: True)
        assert rt._plafon_sor() is None


class TestBuszNincs:
    @pytest.fixture(autouse=True)
    def _nincs_busz(self, monkeypatch):
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_systemd_scope_elerheto", lambda: False)

    def test_nem_a_systemd_run_fut(self):
        b = rt._memoria_burok()
        assert b, "busz nélkül PLAFON NÉLKÜL futna (#3616)"
        assert "systemd-run" not in b, (
            "a bináris ott van, de busz nélkül minden részfutás exit 1")

    def test_tartalek_elotet_cimter_korlattal(self):
        b = rt._memoria_burok()
        assert b[0] == sys.executable
        assert b[-1] == "--", "a `--` után jön a valódi parancs"
        assert str(rt._cimter_bajt()) in b
        assert "RLIMIT_AS" in " ".join(b)

    def test_egy_sorban_kiirja(self):
        sor = rt._plafon_sor()
        assert sor is not None, "a tartalék NÉMA — pont ez a hibaosztály"
        assert "\n" not in sor
        assert "RLIMIT_AS" in sor
        assert rt._CIMTER_PLAFON in sor

    def test_systemd_run_binaris_nelkul_is_tartalek(self, monkeypatch):
        """Busz nélküli gép, ahol a bináris sincs meg (pl. minimál konténer)."""
        monkeypatch.setattr(rt, "_which", lambda _: None)
        assert rt._memoria_burok()[0] == sys.executable

    def test_resource_nelkul_kimondja_hogy_nincs_plafon(self, monkeypatch):
        monkeypatch.setattr(rt, "_resource", None)
        assert rt._memoria_burok() == []
        sor = rt._plafon_sor() or ""
        assert "NINCS" in sor, "plafon nélküli futás NÉMA maradna"


@pytest.mark.skipif(not sys.platform.startswith("linux"),
                    reason="az RLIMIT_AS-előtét Linux-specifikus")
class TestAzEloteTenylegKorlatoz:
    """Valódi gyerekfolyamat: az előtét nem díszlet."""

    def _futtasd(self, monkeypatch, plafon: str, kod: str) -> int:
        monkeypatch.setattr(rt, "_which", lambda _: None)
        monkeypatch.setattr(rt, "_CIMTER_PLAFON", plafon)
        parancs = rt._memoria_burok() + [sys.executable, "-c", kod]
        return subprocess.run(parancs, capture_output=True, timeout=60).returncode

    def test_a_tullepo_meghal(self, monkeypatch):
        rc = self._futtasd(monkeypatch, "512M", "b = bytearray(1024 ** 3)")
        assert rc != 0, "1 GiB-os foglalás 512 MiB-os plafon alatt is átment"

    def test_a_plafon_alatti_fut(self, monkeypatch):
        rc = self._futtasd(monkeypatch, "512M", "b = bytearray(16 * 1024 ** 2)")
        assert rc == 0

    def test_a_korlat_a_GYEREKBEN_el_nem_a_szuloben(self, monkeypatch):
        elotte = rt._resource.getrlimit(rt._resource.RLIMIT_AS)
        self._futtasd(monkeypatch, "512M", "pass")
        assert rt._resource.getrlimit(rt._resource.RLIMIT_AS) == elotte


class TestSzondazas:
    def test_busz_nelkul_hamis(self, monkeypatch):
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_run", lambda *a, **k: _Eredmeny(1))
        assert rt._systemd_scope_elerheto() is False

    def test_mukodo_scope_igaz(self, monkeypatch):
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_run", lambda *a, **k: _Eredmeny(0))
        assert rt._systemd_scope_elerheto() is True

    def test_hiba_eseten_hamis(self, monkeypatch):
        def dob(*a, **k):
            raise subprocess.TimeoutExpired("systemd-run", 10)
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(rt, "_run", dob)
        assert rt._systemd_scope_elerheto() is False

    def test_binaris_nelkul_nem_is_probalja(self, monkeypatch):
        def tilos(*a, **k):
            raise AssertionError("nincs bináris, mégis indított")
        monkeypatch.setattr(rt, "_which", lambda _: None)
        monkeypatch.setattr(rt, "_run", tilos)
        assert rt._systemd_scope_elerheto() is False

    def test_futasonkent_egyszer_szondaz(self, monkeypatch):
        """Több száz részfutás — a szonda nem ismétlődhet mindegyiknél."""
        hivasok = []
        monkeypatch.setattr(rt, "_which", lambda _: "/usr/bin/systemd-run")
        monkeypatch.setattr(
            rt, "_run", lambda *a, **k: hivasok.append(a) or _Eredmeny(0))
        for _ in range(3):
            rt._systemd_scope_elerheto()
        assert len(hivasok) == 1


class TestMertekegyseg:
    @pytest.mark.parametrize("ertek, bajt", [
        ("512M", 512 * 1024 ** 2),
        ("8G", 8 * 1024 ** 3),
        ("1024K", 1024 ** 2),
        ("1048576", 1024 ** 2),
    ])
    def test_a_systemd_jeloleset_erti(self, monkeypatch, ertek, bajt):
        monkeypatch.setattr(rt, "_CIMTER_PLAFON", ertek)
        assert rt._cimter_bajt() == bajt
