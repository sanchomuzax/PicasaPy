"""#3178 — a futtató core dumpot engedélyez, és összeomlásnál KIÍRJA a C++ vermet.

A jegy mérése szerint a ritka `exit -11` (SIGSEGV) a `tests/app` alatt a
fixture-felállás közben történik, és a `faulthandler` csak a PYTHON-szálakat
mutatja — a hibás keret a C++ (Qt) oldalon van, tehát a mai naplóból az ok
nem állapítható meg.

Ez a fájl azt méri, amit a futtató oldaláról meg lehet tenni (a
`.github/workflows/*` írásához a botnak nincs joga):

* a futtató **felemeli** a core-fájl korlátját, tehát a részfutások
  összeomlása core-t hagy;
* összeomlás után a futtató **megkeresi** a core-t, és ha van `gdb`,
  kiírja a natív veremképet a naplóba;
* ha nincs core vagy nincs `gdb`, azt **kimondja, okkal** — a jelzés
  elnémítása súlyosabb hiba lenne, mint a hiányzó veremkép.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402


class HamisResource:
    """A `resource` modul helyettesítője — a MODULSZINTŰ fogantyún át (#1375).

    A globális `resource`-t tilos átírni: minden más modulra átszivárogna,
    amíg a teszt fut. A futtató ezért a saját `_resource` nevét használja.
    """

    RLIMIT_CORE = 4
    RLIM_INFINITY = -1

    def __init__(self, puha: int, kemeny: int) -> None:
        self._korlat = (puha, kemeny)
        self.beallitva: list[tuple] = []

    def getrlimit(self, _mit: int) -> tuple[int, int]:
        return self._korlat

    def setrlimit(self, mit: int, ertek: tuple[int, int]) -> None:
        self.beallitva.append((mit, ertek))


class TestCoreKorlat:
    def test_felemeli_a_core_korlatot(self, monkeypatch) -> None:
        """A puha korlát a keményre megy — a gyerekek ezt öröklik."""
        hamis = HamisResource(0, HamisResource.RLIM_INFINITY)
        monkeypatch.setattr(run_tests, "_resource", hamis)
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")
        assert run_tests._engedd_a_core_dumpot() is True
        assert hamis.beallitva == [
            (HamisResource.RLIMIT_CORE,
             (HamisResource.RLIM_INFINITY, HamisResource.RLIM_INFINITY))
        ]

    def test_ha_a_kemeny_korlat_nulla_nem_hazudik(self, monkeypatch) -> None:
        """Nulla kemény korláttal nincs mit emelni — `False`, nem kivétel."""
        hamis = HamisResource(0, 0)
        monkeypatch.setattr(run_tests, "_resource", hamis)
        monkeypatch.setattr(run_tests, "_platform", lambda: "linux")
        assert run_tests._engedd_a_core_dumpot() is False
        assert hamis.beallitva == []

    def test_windowson_nem_probalkozik(self, monkeypatch) -> None:
        monkeypatch.setattr(run_tests, "_platform", lambda: "win32")
        monkeypatch.setattr(run_tests, "_resource", HamisResource(0, -1))
        assert run_tests._engedd_a_core_dumpot() is False


class TestNativVeremkep:
    def test_a_talalt_core_bol_gdb_vel_veremkepet_ir(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        core = tmp_path / "core.12345"
        core.write_bytes(b"nem igazi core")
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_which", lambda nev: "/usr/bin/gdb")

        hivasok: list[list[str]] = []

        class Eredmeny:
            returncode = 0
            stdout = "#0 QObject::~QObject()\n#1 qt_something()\n"
            stderr = ""

        def hamis_run(parancs, **_kw):
            hivasok.append(parancs)
            return Eredmeny()

        monkeypatch.setattr(run_tests, "_run", hamis_run)

        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is True
        kimenet = capsys.readouterr().out
        assert "QObject::~QObject" in kimenet
        assert any("gdb" in " ".join(h) for h in hivasok)
        assert str(core) in " ".join(hivasok[0])

    def test_core_nelkul_kimondja_az_okot(self, monkeypatch, tmp_path, capsys) -> None:
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_which", lambda nev: "/usr/bin/gdb")
        #: ⚠️ A próba NEM olvashatja a gép VALÓDI `core_pattern`-jét: a
        #: fejlesztői gépen az `core`, a CI-futtatón viszont
        #: `|/usr/lib/systemd/systemd-coredump …` — ott a kezelős ág futna, és
        #: a próba a hosszal együtt az ágat is eltévesztené (mérve: a #3240
        #: első futásán épp ez bukott el).
        monkeypatch.setattr(run_tests, "_core_minta", lambda: "core")
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is False
        kimenet = capsys.readouterr().out
        assert "nincs core" in kimenet.lower()
        # az OK is ott van: a rendszer core-mintája
        assert "core_pattern" in kimenet

    def test_gdb_nelkul_kimondja_hogy_nincs_gdb(
        self, monkeypatch, tmp_path, capsys
    ) -> None:
        (tmp_path / "core.1").write_bytes(b"x")
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_which", lambda nev: None)
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is False
        assert "gdb" in capsys.readouterr().out.lower()

    def test_a_gdb_hibaja_sem_nemul_el(self, monkeypatch, tmp_path, capsys) -> None:
        (tmp_path / "core.1").write_bytes(b"x")
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_which", lambda nev: "/usr/bin/gdb")

        class Eredmeny:
            returncode = 1
            stdout = ""
            stderr = "nem sikerült megnyitni"

        monkeypatch.setattr(run_tests, "_run", lambda *_a, **_k: Eredmeny())
        assert run_tests._ird_ki_a_nativ_veremkepet("tests/app/x.py") is False
        assert "nem sikerült megnyitni" in capsys.readouterr().out


class TestBekotes:
    def test_az_osszeomlas_nyoma_a_nativ_vermet_is_kerdezi(
        self, monkeypatch, capsys
    ) -> None:
        """A meglévő összeomlás-jelentés hívja az új lépést (#3178)."""
        hivva: list[str] = []
        monkeypatch.setattr(
            run_tests,
            "_ird_ki_a_nativ_veremkepet",
            lambda relative: hivva.append(relative) or False,
        )
        run_tests._ird_ki_az_osszeomlas_nyomat("tests/app/x.py", -11)
        assert hivva == ["tests/app/x.py"]
        assert "ÖSSZEOMLÁS NYOMA" in capsys.readouterr().out

    def test_tesztbukasnal_nem_keres_core_t(self, monkeypatch, capsys) -> None:
        """A `-11`-en KÍVÜL nincs mit keresni: a tesztbukás nem hagy core-t."""
        hivva: list[str] = []
        monkeypatch.setattr(
            run_tests,
            "_ird_ki_a_nativ_veremkepet",
            lambda relative: hivva.append(relative) or False,
        )
        run_tests._ird_ki_az_osszeomlas_nyomat("tests/app/x.py", 1)
        assert hivva == []
