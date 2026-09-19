"""A core-lánc ÉLESBEN: valódi összeomlás → core → `gdb` → natív verem (#3178).

## Miért kell ez a próba

A #3178 eszköze (core-korlát emelés, `core_pattern` átállítás, `gdb`
telepítés, veremkép-kiírás) megvan, de **egyetlen valódi összeomláson sem
futott végig**: a jelenség ritka (15 CI-körből 1), és a meglévő próbák
mindent kigúnyolnak (`monkeypatch`). A projekt saját tanulsága szerint a
sosem futott ellenőrzés nem őr, csak remény.

Ez a fájl ezért **szándékosan összeomlaszt** egy gyerekfolyamatot
(`SIGSEGV` a C oldalról), és végigméri a láncot azon a gépen, ahol fut.

## Mit mér

1. a gyerek tényleg `-11`-gyel hal meg (a jelenség előállítható);
2. a futtató core-korlát-emelése után a korlát **nem nulla**;
3. ahol a kernel FÁJLBA írja a core-t, ott a `_core_fajlok()` **megtalálja**;
4. ahol `gdb` is van, ott a natív veremkép **tartalmazza a jelet**.

## Amit NEM mér — és miért nem hallgat el

A 3. és 4. pont **környezetfüggő**: ha a `core_pattern` egy kezelőnek adja
át a core-t (`|/usr/lib/systemd/systemd-coredump …`), fájl nem keletkezik,
és ha nincs `gdb`, nincs veremkép. A kihagyás OKA ilyenkor
`pytest.skip(...)`-ként **látszik a naplóban**: a futtató `-rs`-sel indít,
tehát a rövid jelentés kiírja az indokot.

⚠️ A `print` ERRE NEM JÓ — a pytest elnyeli az ÁTMENŐ próbák kimenetét,
tehát a CI-n se a lefutás, se a kihagyás nem látszana. *(Mérve: a #3372
első CI-körének naplójában a `print`-es alak semmit nem hagyott.)*

⚠️ A kihagyás **nem mentesít**: ahol a lánc futhatna (fájlos `core_pattern`
és `gdb`), ott a próba a TELJES utat megköveteli.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest

resource = pytest.importorskip(
    "resource", reason="POSIX-only: a core-korlát Windowson nem létezik")

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import run_tests  # noqa: E402

#: A gyerek, ami a C oldalról omlik össze — nem `os.abort()` (az SIGABRT),
#: hanem NULL-dereferencia, vagyis pontosan SIGSEGV, mint a mért eset.
_OSSZEOMLO = "import ctypes; ctypes.string_at(0)"


@pytest.fixture()
def munkakonyvtar(tmp_path, monkeypatch):
    """A core a SAJÁT könyvtárunkba essen, ne a repó gyökerébe."""
    monkeypatch.setattr(run_tests, "_ROOT", tmp_path)
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _omlassz_ossze(hova: Path) -> int:
    """A gyerek korlátja a KEMÉNY korlát — így hagyhat core-t."""
    def elokeszites() -> None:  # pragma: no cover — a gyerekben fut
        _, kemeny = resource.getrlimit(resource.RLIMIT_CORE)
        resource.setrlimit(resource.RLIMIT_CORE, (kemeny, kemeny))

    kesz = subprocess.run(
        [sys.executable, "-c", _OSSZEOMLO],
        cwd=hova, preexec_fn=elokeszites, capture_output=True,
    )
    return kesz.returncode


def test_a_jelenseg_eloallithato(munkakonyvtar) -> None:
    """A mért `exit -11` — enélkül a többi állítás vakon állna."""
    assert _omlassz_ossze(munkakonyvtar) == -11


def test_a_futtato_korlatemelese_nem_nullat_hagy() -> None:
    """A `_engedd_a_core_dumpot` után a PUHA korlát a keményre áll."""
    eredeti = resource.getrlimit(resource.RLIMIT_CORE)
    try:
        engedve = run_tests._engedd_a_core_dumpot()
        puha, kemeny = resource.getrlimit(resource.RLIMIT_CORE)
        if kemeny == 0:
            #: a rendszer TILTJA a core-t — ez legitim, de mondjuk ki
            assert engedve is False
            pytest.skip("a kemény korlát 0: ezen a gépen nincs core dump")
        assert engedve is True
        assert puha == kemeny
    finally:
        resource.setrlimit(resource.RLIMIT_CORE, eredeti)


def test_a_lanc_vegigmegy_ahol_a_kernel_fajlba_ir(munkakonyvtar, capsys) -> None:
    """A TELJES út: összeomlás → `_core_fajlok()` → `gdb` → veremkép."""
    minta = run_tests._core_minta()
    _, kemeny = resource.getrlimit(resource.RLIMIT_CORE)
    if kemeny == 0:
        pytest.skip("a rendszer kemény core-korlátja 0 — nincs core dump")
    if run_tests._kezelo_kapja_a_core_t(minta):
        pytest.skip(f"a core-t KEZELŐ kapja meg (core_pattern: {minta})")
    if os.path.sep in minta.strip() and not minta.strip().startswith("core"):
        pytest.skip(f"a core máshova kerül (core_pattern: {minta})")

    assert _omlassz_ossze(munkakonyvtar) == -11
    magok = run_tests._core_fajlok()
    assert magok, (
        f"a kernel core_pattern-je {minta!r}, mégsem találtunk core-t a "
        f"{munkakonyvtar} alatt: "
        f"{sorted(ut.name for ut in munkakonyvtar.iterdir())}")

    if run_tests._which("gdb") is None:
        pytest.skip("nincs `gdb` ezen a gépen — a natív veremkép kimarad")
    assert run_tests._ird_ki_a_nativ_veremkepet("proba.py") is True
    kimenet = capsys.readouterr().out
    assert "NATÍV VEREMKÉP" in kimenet
    assert "proba.py" in kimenet


def test_a_hiany_OKAT_mindig_kimondja(munkakonyvtar, capsys) -> None:
    """Core nélkül sem hallgat — ez a #3178 kimondott követelménye."""
    assert run_tests._ird_ki_a_nativ_veremkepet("proba.py") is False
    kimenet = capsys.readouterr().out
    assert "proba.py" in kimenet
    assert "core_pattern" in kimenet or "coredumpctl" in kimenet
