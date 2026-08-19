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

import concurrent.futures
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_NON_APP_TIMEOUT_S = 300
_APP_FILE_TIMEOUT_S = 180

#: Hány `tests/app`-fájl fusson EGYSZERRE (#1030). A fájlok külön processzben
#: futnak (#53), a párhuzamosítás tehát nem gyengíti az izolációt — csak
#: kihasználja a gép magjait, ahelyett hogy egyetlenegyen sorakoznának.
#:
#: Mért indok (RPi5, 4 mag): fájlonként 0,7 mp a puszta processzindulás, az
#: átlagos fájl 5,4 mp — vagyis NEM az indítgatás a fő tétel, hanem az, hogy
#: minden egyetlen magon fut. 30 fájlos mintán a négyszálas futás 163 mp
#: helyett 68 mp volt (2,4×).
#:
#: `PICASAPY_TESZT_PARHUZAM=1` visszaadja a korábbi, soros viselkedést.
_PARHUZAM = max(
    1,
    int(os.environ.get("PICASAPY_TESZT_PARHUZAM") or 0) or min(4, os.cpu_count() or 1),
)

#: A saját ideiglenes könyvtáraink gyökere és előtagja (#677). Az előtag azért
#: kell, hogy a takarítás CSAK a sajátunkhoz nyúljon.
_TEMP_GYOKER = Path(tempfile.gettempdir())
_TEMP_ELOTAG = "picasapy-tests-"

#: Ennél régebbi saját maradékot takarítunk induláskor. Kor szerint szűrünk,
#: mert egy PÁRHUZAMOS munkamenet friss könyvtárát elvinni rosszabb, mint
#: helyet pazarolni.
_MARADEK_KOR_S = 3 * 3600


#: A csendes (párhuzamos) részfutások összegyűjtött kimenete; kulcs a pytest
#: argumentumsora. Minden szál a SAJÁT kulcsára ír, a főszál olvassa.
_KIMENET: dict[str, str] = {}


def _szoveggé(kimenet: bytes | str | None) -> str:
    """A timeout-kivétel kimenete lehet bytes, str vagy semmi."""
    if kimenet is None:
        return "(nincs kimenet)"
    if isinstance(kimenet, bytes):
        return kimenet.decode("utf-8", "replace")
    return kimenet


def _reszfutas_kornyezete(sajat: Path) -> dict[str, str]:
    """Részfutásonként KÜLÖN alkalmazás-adatmappák (#1030).

    Az index-SQLite és a bélyegkép-gyorstár helyét az `XDG_DATA_HOME` /
    `XDG_CACHE_HOME` adja (`app/application.py` `_data_dir`/`_cache_dir`) —
    minden platformon, mert a kód közvetlenül ezeket a változókat olvassa.
    Közös mappán a párhuzamos részfutások UGYANABBA az adatbázisfájlba
    dolgoznának: méréskor pontosan ez történt, négy teszt bukott el
    `unable to open database file`-lal, ami sorosan zöld volt.

    A `HOME`-ot SZÁNDÉKOSAN nem írjuk felül, pedig kézenfekvő lenne: a
    Python-csomagok a felhasználói site-packages-ben laknak, és felülírt
    HOME-mal MINDEN részfutás `No module named pytest`-tel halt meg (mérve).
    """
    kornyezet = dict(os.environ)
    for valtozo, alkonyvtar in (
        ("XDG_DATA_HOME", "adat"),
        ("XDG_CACHE_HOME", "gyorstar"),
        ("XDG_CONFIG_HOME", "beallitas"),
        ("XDG_STATE_HOME", "allapot"),
    ):
        ut = sajat / alkonyvtar
        ut.mkdir(parents=True, exist_ok=True)
        kornyezet[valtozo] = str(ut)
    return kornyezet


def _run_pytest(
    args: list[str], timeout_s: int, *, cov: bool, basetemp: Path,
    kornyezet: dict[str, str] | None = None, csendben: bool = False,
) -> int:
    """Egy pytest-részfutás saját processzben; timeoutnál 124-gyel tér vissza.

    cov=True esetén a pytest a `coverage run -p` alá fut (ld. a modul
    docstringjét).

    A `basetemp`-ről (#677 + #1030): soros futásnál minden részfutás UGYANAZT
    kapja, mert a pytest a könyvtárat induláskor kiüríti — így az előző helye
    felszabadul, és nem gyűlik tucatnyi könyvtár egymás mellé. Párhuzamos
    futásnál viszont épp ezért kell részfutásonként KÜLÖN könyvtár (különben a
    másik szál ideiglenes fájljait törölnék), a hívó pedig a részfutás végén
    azonnal takarít — így a csúcsigény a szálak számával arányos, nem a
    fájlokéval.

    `csendben=True` esetén a kimenetet elnyeljük és `_KIMENET`-be tesszük: a
    párhuzamos részfutások kiírásai összekeverednének."""
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
    if not csendben:
        print(f"$ {' '.join(command)}", flush=True)
    try:
        if not csendben:
            return subprocess.run(
                command, cwd=_ROOT, timeout=timeout_s, env=kornyezet
            ).returncode
        eredmeny = subprocess.run(
            command, cwd=_ROOT, timeout=timeout_s, env=kornyezet,
            capture_output=True, text=True, errors="replace",
        )
        _KIMENET[" ".join(args)] = (eredmeny.stdout or "") + (eredmeny.stderr or "")
        return eredmeny.returncode
    except subprocess.TimeoutExpired as kivetel:
        if csendben:
            _KIMENET[" ".join(args)] = _szoveggé(kivetel.stdout)
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
    if _PARHUZAM > 1:
        failures += _app_fajlok_parhuzamosan(app_test_files, cov=cov, basetemp=basetemp)
    else:
        failures += _app_fajlok_sorosan(app_test_files, cov=cov, basetemp=basetemp)

    if cov:
        _report_coverage()

    if failures:
        print("\nHIBÁS RÉSZFUTÁSOK:", flush=True)
        for name, returncode in failures:
            print(f"  {name}: exit {returncode}", flush=True)
        return 1

    print("\nMinden részfutás zöld.", flush=True)
    return 0


def _app_fajlok_sorosan(
    app_test_files: list[Path], *, cov: bool, basetemp: Path
) -> list[tuple[str, int]]:
    """A korábbi (2026-08-19 előtti) viselkedés — `PICASAPY_TESZT_PARHUZAM=1`."""
    failures: list[tuple[str, int]] = []
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
    return failures


def _app_fajlok_parhuzamosan(
    app_test_files: list[Path], *, cov: bool, basetemp: Path
) -> list[tuple[str, int]]:
    """Ugyanaz, `_PARHUZAM` fájllal egyszerre (#1030).

    Minden fájl SAJÁT mappát kap (ideiglenes fájlok + alkalmazás-adatmappák),
    amit a részfutás végén azonnal törlünk — a csúcsigény így a szálak
    számával arányos, nem a fájlokéval (#677).
    """
    failures: list[tuple[str, int]] = []

    def egy_fajl(test_file: Path) -> tuple[str, int]:
        relative = str(test_file.relative_to(_ROOT))
        sajat = basetemp / test_file.stem
        try:
            kornyezet = _reszfutas_kornyezete(sajat)
            returncode = _run_pytest(
                [relative], _APP_FILE_TIMEOUT_S, cov=cov,
                basetemp=sajat / "pytest", kornyezet=kornyezet, csendben=True,
            )
            if returncode == 124:
                # alkalmi beragadás (#53): egyszeri újrapróbálás friss processzben
                print(f"ÚJRAPRÓBÁLÁS (timeout után): {relative}", flush=True)
                returncode = _run_pytest(
                    [relative], _APP_FILE_TIMEOUT_S, cov=cov,
                    basetemp=sajat / "pytest", kornyezet=kornyezet, csendben=True,
                )
            return relative, returncode
        finally:
            shutil.rmtree(sajat, ignore_errors=True)

    print(f"\n$ tests/app: {len(app_test_files)} fájl, "
          f"{_PARHUZAM} egyszerre", flush=True)
    with concurrent.futures.ThreadPoolExecutor(max_workers=_PARHUZAM) as pool:
        for relative, returncode in pool.map(egy_fajl, app_test_files):
            if returncode == 0:
                print(f"  ✓ {relative}", flush=True)
                continue
            failures.append((relative, returncode))
            print(f"  ✗ {relative}: exit {returncode}", flush=True)
            # a bukott részfutás teljes kimenete — soros futásnál ez amúgy is
            # a képernyőn lenne, itt gyűjtve kerül ki, egyben
            print(_KIMENET.get(relative, "(nincs kimenet)"), flush=True)
    return failures


if __name__ == "__main__":
    sys.exit(main())
