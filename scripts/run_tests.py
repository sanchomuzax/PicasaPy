#!/usr/bin/env python3
"""Darabolt tesztfuttató (#53-as deadlock-osztály ellen).

A teljes tesztkészlet EGY pytest-processzben futtatva Qt/GIL-deadlockra
hajlamos — a Windows-runneren rendszeresen beragadt (2026-07-20-án a main
utolsó hat CI-futása mind így halt meg), és a felhő-konténerben is
reprodukálható. Ezért a futás darabolva történik:

1. a nem-Qt tesztek (`tests` a `tests/app` nélkül) egyetlen processzben;
2. a `tests/app` (és az alatta lévő `tests/app/qml_functional/`) fájlonként,
   külön-külön processzben, kemény timeouttal.

Egy beragadó részfutás így csak a saját timeoutját veszíti el, a többi
eredménye megmarad, és a hibás fájl neve azonnal látszik.

#155: a korábbi `tests/app/test_qml_functional.py` (~68 teszt EGY fájlban)
egyetlen processzben ~68 QML-engine/ablak-életciklust futtatott le — ez volt
a Windows-deadlock (#53) egyik fő forrása, ezért Windowson korábban ki volt
hagyva a futásból. A megoldás: a fájl felbontása több kisebb fájlra a
`tests/app/qml_functional/` alatt, amelyeket ez a szkript KÜLÖN-KÜLÖN
processzben futtat — processzenként lényegesen kevesebb az
engine-életciklus, ezért a Windows-kizárás megszűnt, minden fájl minden
platformon lefut.

#300: opcionális `--cov` kapcsoló a lefedettség méréséhez. Mivel minden
részfutás külön processz, a `pytest-cov` sima `--cov` kapcsolója önmagában
nem összesítene — helyette minden részfutás `coverage run -p` alá kerül
(ez processzenként egyedi nevű `.coverage.*` adatfájlt ír), a végén pedig
egy `coverage combine` + `coverage report` fésüli össze és írja ki az
eredményt. A `--cov` NÉLKÜLI viselkedés változatlan.

#677: minden részfutás UGYANAZT a, futásonként egyedi `--basetemp`-et kapja.
A pytest a „tartsd meg az utolsó hármat" takarítást basetemp-enként végzi —
részfutásonként külön könyvtárral egyetlen teljes futás tucatnyit hagyott
maga után (mérve 4,2 GB egy 8 GB-os tmpfs-en). Közös basetemppel a következő
részfutás induláskor felszabadítja az előzőét, tehát a csúcsigény egyetlen
részfutásnyi; a futás végén az egész eltűnik. A kár nem is a futásé volt: a
betelt tmpfs a PÁRHUZAMOSAN futó másik munkamenet parancsait törte el, némán,
félrevezető ENOSPC-hibával."""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_NON_APP_TIMEOUT_S = 300
_APP_FILE_TIMEOUT_S = 180

#: A saját ideiglenes könyvtáraink gyökere és előtagja (#677). Az előtag azért
#: kell, hogy a takarítás CSAK a sajátunkhoz nyúljon.
_TEMP_GYOKER = Path(tempfile.gettempdir())
_TEMP_ELOTAG = "picasapy-tests-"

#: Ennél régebbi saját maradékot takarítunk induláskor. Kor szerint szűrünk,
#: mert egy PÁRHUZAMOS munkamenet friss könyvtárát elvinni rosszabb, mint
#: helyet pazarolni.
_MARADEK_KOR_S = 3 * 3600


def _run_pytest(
    args: list[str], timeout_s: int, *, cov: bool, basetemp: Path
) -> int:
    """Egy pytest-részfutás saját processzben; timeoutnál 124-gyel tér vissza.

    cov=True esetén a pytest a `coverage run -p` alá fut (ld. a modul
    docstringjét). A `basetemp` minden részfutásra AZONOS (#677): a pytest a
    könyvtárat induláskor kiüríti, így az előző részfutás helye felszabadul,
    és nem gyűlik tucatnyi könyvtár egymás mellé."""
    pytest_args = [
        "-m",
        "pytest",
        "-q",
        "--tb=short",
        # #664: a KIHAGYÁS SOSE LEGYEN NÉMA. A `-q` önmagában csak egy `s`
        # betűt ír a kimaradt tesztre. Ha valami a gépen hiányzó Qt-modul,
        # képformátum-bővítmény vagy ismert összeomlás miatt marad ki, azt a
        # futtatónak LÁTNIA kell — különben a „minden részfutás zöld" hamis
        # biztonság. A `-rs` a záró összegzésbe kiírja a kihagyás INDOKÁT is.
        "-rs",
        "-p",
        "no:cacheprovider",
        f"--basetemp={basetemp}",
        *args,
    ]
    if cov:
        command = [sys.executable, "-m", "coverage", "run", "-p", *pytest_args]
    else:
        command = [sys.executable, *pytest_args]
    print(f"$ {' '.join(command)}", flush=True)
    try:
        return subprocess.run(command, cwd=_ROOT, timeout=timeout_s).returncode
    except subprocess.TimeoutExpired:
        print(f"TIMEOUT ({timeout_s}s): {' '.join(args)}", flush=True)
        return 124


def _takarits_regi_maradekot() -> None:
    """Korábbi (megszakadt) futások saját maradékainak eltakarítása.

    KOR SZERINT szűrünk, és CSAK a saját előtagunkra: egy párhuzamosan futó
    munkamenet friss könyvtárát elvinni rosszabb, mint helyet pazarolni.
    """
    hatarido = time.time() - _MARADEK_KOR_S
    for konyvtar in _TEMP_GYOKER.glob(f"{_TEMP_ELOTAG}*"):
        if not konyvtar.is_dir():
            continue
        try:
            if konyvtar.stat().st_mtime > hatarido:
                continue
            shutil.rmtree(konyvtar, ignore_errors=True)
        except OSError:
            # más munkamenet épp törli, vagy nincs jogunk — nem baj
            continue


def _report_coverage() -> None:
    """A darabolt `coverage run -p` adatfájljainak összefésülése és a
    lefedettségi összesítő kiírása. Tájékoztató jellegű (#300): küszöb
    (`--fail-under`) egyelőre nincs bekötve, ez külön döntés."""
    print("\n$ coverage combine", flush=True)
    subprocess.run(
        [sys.executable, "-m", "coverage", "combine"], cwd=_ROOT, check=False
    )
    print("$ coverage report", flush=True)
    subprocess.run(
        [sys.executable, "-m", "coverage", "report"], cwd=_ROOT, check=False
    )


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cov = "--cov" in argv

    if cov:
        # tiszta lap: egy korábbi (pl. megszakadt) --cov futásból maradt
        # .coverage.* adatfájlok ne keveredjenek a mostani mérésbe.
        subprocess.run(
            [sys.executable, "-m", "coverage", "erase"], cwd=_ROOT, check=False
        )

    _takarits_regi_maradekot()
    basetemp = Path(tempfile.mkdtemp(prefix=_TEMP_ELOTAG, dir=_TEMP_GYOKER))
    try:
        return _futtat(cov, basetemp)
    finally:
        # a takarítás nem függhet attól, zöld volt-e a futás, és attól sem,
        # hogy megszakították-e (#677)
        shutil.rmtree(basetemp, ignore_errors=True)


def _futtat(cov: bool, basetemp: Path) -> int:
    """A tényleges részfutás-sorozat; a basetemp életciklusa a hívóé."""
    failures: list[tuple[str, int]] = []

    returncode = _run_pytest(
        ["tests", "--ignore=tests/app"], _NON_APP_TIMEOUT_S, cov=cov, basetemp=basetemp
    )
    if returncode != 0:
        failures.append(("tests (tests/app nélkül)", returncode))

    # a tests/app közvetlen fájljai + a tests/app/qml_functional/ alattiak
    # (#155: a korábbi test_qml_functional.py szétbontásából) — mindegyik
    # KÜLÖN processzben, hogy egy fájlon belüli sok engine-életciklus se
    # torlódjon egyetlen processzbe.
    app_dir = _ROOT / "tests" / "app"
    app_test_files = sorted(app_dir.glob("test_*.py")) + sorted(
        (app_dir / "qml_functional").glob("test_*.py")
    )
    for test_file in app_test_files:
        relative = test_file.relative_to(_ROOT)
        returncode = _run_pytest(
            [str(relative)], _APP_FILE_TIMEOUT_S, cov=cov, basetemp=basetemp
        )
        if returncode == 124:
            # alkalmi beragadás (#53): egyszeri újrapróbálás friss
            # processzben — a tartósan beragadó fájl így is kibukik
            print(f"ÚJRAPRÓBÁLÁS (timeout után): {relative}", flush=True)
            returncode = _run_pytest(
                [str(relative)], _APP_FILE_TIMEOUT_S, cov=cov, basetemp=basetemp
            )
        if returncode != 0:
            failures.append((str(relative), returncode))

    if cov:
        _report_coverage()

    if failures:
        print("\nHIBÁS RÉSZFUTÁSOK:", flush=True)
        for name, returncode in failures:
            print(f"  {name}: exit {returncode}", flush=True)
        return 1

    print("\nMinden részfutás zöld.", flush=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
