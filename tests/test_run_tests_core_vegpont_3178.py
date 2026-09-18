"""#3178 — a natív veremkép lánca VÉGPONTTÓL VÉGPONTIG, valódi összeomláson.

A futtató core-diagnosztikája (core-korlát emelése → core megkeresése →
`gdb` → veremkép a naplóba) eddig **kizárólag hamisított** `resource`- és
`gdb`-fogantyúkkal volt lefedve. Az ilyen őr zöld marad akkor is, ha az
igazi lánc sosem futott le — és a #3178 épp arra vár, hogy a KÖVETKEZŐ
ritka SIGSEGV-nél tényleg legyen veremkép. Ha a lánc csendben törött,
azt a következő előfordulás elvesztésével tudnánk meg.

Ez a fájl ezért **igazi SIGSEGV-et** vált ki egy gyerekfolyamatban
(`ctypes.string_at(0)`), és a futtató SAJÁT függvényeivel kéri el a
veremképet.

## Amit állít

1. a gyerek tényleg jelre hal (`exit -11`), és **core-fájlt hagy**, ha a
   rendszer fájlos mintát használ;
2. a `_core_fajlok()` megtalálja azt a fájlt;
3. az `_ird_ki_a_nativ_veremkepet()` a naplóba írja a **C++ keretet** —
   `SIGSEGV`-vel és legalább egy szálképpel;
4. a függvény akkor sem hallgat, ha nincs core: kimondja az okot.

## Amit NEM állít

A CI-beli környezetet. A GitHub-futtatón a core-t a `systemd-coredump`
kapja meg (`|`-es `core_pattern`), ott a `coredumpctl`-ág az út (#3240) —
azt ez a fájl nem tudja kiváltani. Ezért a 3. pont csak **fájlos
mintán** fut le; máshol a 4. pont (a kimondott ok) marad a mérce.

⚠️ A core-fájl mérete mérve **5,3 MB** egy csupasz Python-gyerekre, és a
teszt saját `tmp_path`-ba írja — nem terheli a `/tmp`-et tartósan.
"""

from __future__ import annotations

import os
import resource
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402

#: A gyerek, ami BIZTOSAN SIGSEGV-vel hal: null-mutatóról olvas.
_OMLASZTO = "import ctypes; ctypes.string_at(0)"


def _kemeny_core_korlat() -> int:
    return resource.getrlimit(resource.RLIMIT_CORE)[1]


#: A rendszer beállításai eldöntik, meg tud-e egyáltalán születni a core.
#: A `skipif` OKA mindig látszik — a #3178 szabálya, hogy a hiányzó
#: veremkép magyarázatot kapjon, ne csendes kihagyást.
_NINCS_CORE_LEHETOSEG = (
    sys.platform.startswith("win")
    or _kemeny_core_korlat() == 0
    or run_tests._kezelo_kapja_a_core_t(run_tests._core_minta())
)
_OK = (
    "ezen a rendszeren nem keletkezik core-FÁJL "
    f"(core_pattern: {run_tests._core_minta()!r}, "
    f"kemény korlát: {_kemeny_core_korlat()})"
)


def _omlassz(munkakonyvtar: Path) -> int:
    """Valódi SIGSEGV egy gyerekfolyamatban, a megadott könyvtárban.

    A core-korlátot a GYEREKBEN emeljük (`preexec_fn`), pontosan úgy, ahogy
    a futtató teszi a részfutásokkal: a puha korlát öröklődik."""

    def elokeszit() -> None:  # pragma: no cover — a gyerekben fut
        resource.setrlimit(
            resource.RLIMIT_CORE,
            (resource.RLIM_INFINITY, resource.RLIM_INFINITY),
        )

    return subprocess.run(
        [sys.executable, "-c", _OMLASZTO],
        cwd=munkakonyvtar,
        preexec_fn=elokeszit,
        capture_output=True,
        check=False,
    ).returncode


@pytest.mark.skipif(_NINCS_CORE_LEHETOSEG, reason=_OK)
class TestValodiOsszeomlas:
    def test_a_gyerek_JELRE_hal_es_core_t_hagy(self, tmp_path) -> None:
        kilepokod = _omlassz(tmp_path)

        assert run_tests._osszeomlas(kilepokod), kilepokod
        magok = sorted(tmp_path.glob("core*"))
        assert magok, f"nincs core a(z) {tmp_path} alatt: {os.listdir(tmp_path)}"

    def test_a_futtato_MEGTALALJA_a_core_t(self, tmp_path, monkeypatch) -> None:
        """A `_core_fajlok()` a futtató gyökerében keres — a teszt ezt a
        gyökeret tereli a saját könyvtárába."""
        _omlassz(tmp_path)
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)

        talalt = run_tests._core_fajlok()

        assert talalt, os.listdir(tmp_path)
        assert talalt[0].stat().st_size > 0

    @pytest.mark.skipif(run_tests._which("gdb") is None, reason="nincs `gdb`")
    def test_a_NATIV_veremkep_tenyleg_megszuletik(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        """A lánc lényege: a naplóban ott a C++ keret és a jel neve.

        Ez az az állítás, amit a hamisított `gdb` SOHA nem tudott
        bizonyítani — a mai teszt-készlet minden más pontja megvolt."""
        _omlassz(tmp_path)
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)

        siker = run_tests._ird_ki_a_nativ_veremkepet("proba.py")

        kimenet = capsys.readouterr().out
        assert siker, kimenet
        assert "NATÍV VEREMKÉP" in kimenet
        assert "SIGSEGV" in kimenet, kimenet[:800]
        assert "Thread 1" in kimenet, kimenet[:800]
        assert "a natív veremkép vége" in kimenet


class TestMindenKornyezetben:
    """⚠️ A fenti osztály a CI-n KIMARAD (ott a `systemd-coredump` kapja a
    core-t), a környezetfüggő skip pedig nem őr: ami mindig kimarad, az
    nem fog meg semmit. Ez az osztály ezért MINDENHOL fut.

    Amit mindenhol állítani lehet: a futtató egy valódi összeomlás után
    **nem hallgat**. Vagy veremképet ad, vagy megnevezi az okot — a
    kettő közül az egyik mindig ott van a naplóban.
    """

    def test_valodi_osszeomlas_utan_sem_nema(
        self, tmp_path, monkeypatch, capsys
    ) -> None:
        _omlassz(tmp_path)
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)

        run_tests._ird_ki_a_nativ_veremkepet("proba.py")

        kimenet = capsys.readouterr().out
        assert kimenet.strip(), "a futtató némán ment tovább egy SIGSEGV után"
        beszedes = (
            "NATÍV VEREMKÉP" in kimenet          # megvan a C++ keret
            or "nincs core-fájl" in kimenet      # fájlos minta, de nincs core
            or "coredump" in kimenet.lower()     # a kezelős ág (#3240)
            or "gdb" in kimenet.lower()          # a gdb hiánya vagy hibája
        )
        assert beszedes, kimenet[:800]


class TestNemHallgat:
    """Core nélkül sem marad néma — ez a #3178 kimondott szabálya."""

    def test_core_nelkul_kiirja_az_okot(self, tmp_path, monkeypatch, capsys) -> None:
        monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
        monkeypatch.setattr(run_tests, "_core_minta", lambda: "core")

        siker = run_tests._ird_ki_a_nativ_veremkepet("proba.py")

        kimenet = capsys.readouterr().out
        assert siker is False
        assert "nincs core-fájl" in kimenet
        assert "core_pattern" in kimenet


class TestAProbaMaganak:
    """A mérő mérése: az omlasztó tényleg omlaszt, nem csak hibát ad.

    Enélkül a fenti osztály egy SIKERES gyerekre is zöld maradna, ha a
    `skipif` közben elnémítaná — ezért ez a próba NEM kihagyható."""

    def test_az_omlaszto_kifejezes_SIGSEGV_et_ad(self, tmp_path) -> None:
        kilepokod = subprocess.run(
            [sys.executable, "-c", _OMLASZTO],
            cwd=tmp_path, capture_output=True, check=False,
        ).returncode

        assert kilepokod < 0, f"nem jelre halt: {kilepokod}"
        assert abs(kilepokod) == 11, kilepokod
