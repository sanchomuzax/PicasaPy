"""Az összeomlás ne legyen újra vaktában elemzendő (#1457).

## A baj

2026-08-25-én **öt** részfutás halt meg jel nélkül (`-11` / `0xC0000005`),
**négy különböző tesztfájlban, két platformon**. A folyamat nem állításon
bukott: egyszerűen eltűnt, és a naplóban semmi nem mutatta, HOL járt.
Helyben, egyesével a fájlok zölden futottak — tehát a következő bukást is
csak akkor lehet elemezni, ha a futó MAGA hagy nyomot.

A jegy zárófeltétele ezért kimondja: ha a gyökérok nem rekonstruálható,
„a CI kapjon core dump / faulthandler kimenetet, hogy a következő bukás ne
legyen újra vaktában elemzendő".

## Amit ez őriz

1. **`PYTHONFAULTHANDLER=1` minden részfutás környezetében.** A CPython
   `faulthandler`-e ettől `SIGSEGV`/`SIGABRT`/`SIGFPE`/`SIGBUS` esetén a
   `stderr`-re dobja MINDEN szál Python-veremét — épp azt, ami eddig
   hiányzott. Nem lassít (csak a jelkezelőket teszi fel), és a natív
   (Qt/C++) keret ugyan nem látszik, de a HÍVÁSI HELY igen: melyik teszt,
   melyik QML-hívás.
2. **`faulthandler_timeout` a részfutás parancssorán.** Beragadásnál (nem
   összeomlásnál) a pytest maga dobja ki a veremképeket, mielőtt a futtató
   `timeout`-ja megölné a processzt. A `_APP_FILE_TIMEOUT_S`-nél KISEBB
   értéknek kell lennie, különben a futtató előbb lő, és nincs kimenet.

   ⚠️ A beállítás a FUTTATÓBAN áll, nem a `pyproject.toml`-ban: azt a
   CHANGELOG-őr (#1340) a felhasználóhoz eljutó fájlnak tekinti (verzió,
   csomaglista), és joggal kérne hozzá kiadási mondatot — egy futtató-belső
   hibakeresési beállításhoz viszont nincs mit írni a felhasználónak. Mérve:
   a #2779 első köre pontosan ezen bukott el.

⚠️ A `faulthandler` a natív hívási láncot nem adja meg — az csak core
dumpból jönne. Ez a kör tudatosan a Python-oldali nyomot állítja be: az
mindkét platformon, külön eszköz nélkül működik, és a bukó teszt nevét
azonnal megadja.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_GYOKER = Path(__file__).resolve().parents[1]
_spec = importlib.util.spec_from_file_location(
    "run_tests_1457", _GYOKER / "scripts" / "run_tests.py"
)
rt = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(rt)


class _Eredmeny:
    returncode = 0
    stdout = ""
    stderr = ""


class TestFaulthandlerKornyezet:
    def _elkapott_env(self, monkeypatch, **kwargs) -> dict[str, str]:
        elkapott: dict[str, dict[str, str] | None] = {}

        def hamis_run(command, **kw):
            elkapott["env"] = kw.get("env")
            return _Eredmeny()

        monkeypatch.setattr(rt, "_run", hamis_run)
        monkeypatch.setattr(rt, "_memoria_burok", lambda: [])
        rt._run_pytest(
            ["tests/valami.py"], 60, cov=False, basetemp=Path("/tmp/bt"), **kwargs
        )
        env = elkapott["env"]
        assert env is not None, (
            "#1457: a részfutás a szülő környezetét ÖRÖKÖLTE (env=None) — így a "
            "faulthandler bekapcsolása nem garantált"
        )
        return env

    def test_a_reszfutas_faulthandlerrel_indul(self, monkeypatch) -> None:
        env = self._elkapott_env(monkeypatch)
        assert env.get("PYTHONFAULTHANDLER") == "1", (
            "#1457: a részfutás faulthandler NÉLKÜL indult — a következő "
            "SIGSEGV-nél megint nem tudjuk, hol járt a folyamat"
        )

    def test_a_hivo_kornyezete_sem_veszti_el(self, monkeypatch) -> None:
        """A párhuzamos ág SAJÁT környezetet ad (külön XDG-mappák, #1030) — a
        faulthandlernek ott is be kell kerülnie, és a kapott értékek nem
        tűnhetnek el."""
        env = self._elkapott_env(
            monkeypatch, kornyezet={"XDG_DATA_HOME": "/tmp/sajat", "PATH": "/x"}
        )
        assert env["XDG_DATA_HOME"] == "/tmp/sajat", "a hívó beállítása elveszett"
        assert env["PATH"] == "/x"
        assert env["PYTHONFAULTHANDLER"] == "1"

    def test_a_parhuzamos_kornyezet_is_tartalmazza(self, tmp_path: Path) -> None:
        kornyezet = rt._reszfutas_kornyezete(tmp_path)
        assert kornyezet["PYTHONFAULTHANDLER"] == "1"


class TestPytestFaulthandlerTimeout:
    def test_a_reszfutas_parancssoran_ott_van(self, monkeypatch) -> None:
        elkapott: dict[str, list[str]] = {}

        def hamis_run(command, **kw):
            elkapott["command"] = list(command)
            return _Eredmeny()

        monkeypatch.setattr(rt, "_run", hamis_run)
        monkeypatch.setattr(rt, "_memoria_burok", lambda: [])
        rt._run_pytest(["tests/valami.py"], 60, cov=False, basetemp=Path("/tmp/bt"))
        command = elkapott["command"]
        assert f"faulthandler_timeout={rt._FAULTHANDLER_TIMEOUT_S}" in command, (
            "#1457: beragadásnál a pytest nem ír veremképet, tehát a futtató "
            f"timeoutja után csak annyit tudunk, hogy »beragadt«: {command}"
        )

    def test_a_timeout_a_futtatoe_ALATT_van(self) -> None:
        assert rt._FAULTHANDLER_TIMEOUT_S < rt._APP_FILE_TIMEOUT_S, (
            "a pytest veremkép-időkorlátja NEM lehet nagyobb a futtató "
            f"fájl-timeoutjánál ({rt._APP_FILE_TIMEOUT_S}s), különben a futtató "
            "előbb lő, és nincs kimenet"
        )


class TestAFaulthandlerTENYLEG_ir(object):
    """Ismert pozitív: a beállítás csak akkor ér valamit, ha a jelre TÉNYLEG
    kiírja a vermet. Ezt egy szándékosan összeomló gyerekfolyamattal mérjük."""

    def test_a_sigsegv_verme_a_stderrre_kerul(self, tmp_path: Path) -> None:
        import subprocess

        szkript = tmp_path / "omlik.py"
        szkript.write_text(
            "import ctypes\n"
            "def melyen():\n"
            "    ctypes.string_at(0)   # szándékos szegmentálási hiba\n"
            "melyen()\n",
            encoding="utf-8",
        )
        eredmeny = subprocess.run(
            [sys.executable, str(szkript)],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
            env={"PYTHONFAULTHANDLER": "1", "PATH": "/usr/bin:/bin"},
        )
        assert eredmeny.returncode != 0
        assert "melyen" in eredmeny.stderr, (
            "a faulthandler nem írta ki a hívási láncot — enélkül a #1457 "
            f"osztályú bukás megint néma lenne. stderr: {eredmeny.stderr!r}"
        )
