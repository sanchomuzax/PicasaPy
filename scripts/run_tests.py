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
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from collections.abc import Callable
from pathlib import Path

#: A `subprocess.run` és az `os.kill` MODULSZINTŰ fogantyúja (#1375) — a
#: teszt EZEKET cserélje: `monkeypatch.setattr(run_tests, "_run", …)`.
#:
#: A `monkeypatch.setattr(run_tests.subprocess, "run", …)` alak a GLOBÁLIS
#: `subprocess`-t írja át. Itt ez különösen kellemetlen: a futtató saját
#: tesztjei épp a részfutások indítását némítják el, és a csere közben
#: minden más modul folyamatindítása is a hamis felvevőbe futna.
_run = subprocess.run
_kill = os.kill

# ⚠️ A windowsos konzol alapértelmezett kódlapja (cp1252) NEM ismeri a
# magyar `ő` és `ű` betűket — egy `print()` rajtuk `UnicodeEncodeError`-rel
# elhasal, és a JOB azonnal elbukik, még mielőtt egyetlen teszt elindulna.
# (#1127: pontosan ez buktatta el mind a négy windows-darabot.)
#
# A megoldás nem a betűk kerülése — az minden jövőbeli magyar sorra
# ráterhelné a szerzőt —, hanem az UTF-8 kimenet. Az `errors="replace"`
# a végső védőháló: kiírni akkor is tudjunk, ha a cél mégsem bírja.
for _folyam in (sys.stdout, sys.stderr):
    if hasattr(_folyam, "reconfigure"):
        _folyam.reconfigure(encoding="utf-8", errors="replace")

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
#: 2026-08-19: az ALAPÉRTELMEZÉS visszaáll SOROSRA, a párhuzamosság kérésre
#: kapcsolható (`PICASAPY_TESZT_PARHUZAM=4`). Ok: alapból bekapcsolva a főág
#: CI-ja két egymást követő futáson elbukott —
#:   * ubuntu: `tests/app/test_tray_export.py` (a teszt 15 mp-et vár egy
#:     exportra; CPU-éhezésben ez kevés, a várt érték None marad),
#:   * windows: `test_folder_pane_projects_1029.py` hozzáférési hibával
#:     (0xC0000005) omlott össze.
#: A gyorsulás valódi (ubuntu 22 → 6 perc), de piros főág mellett semmit nem ér:
#: a felhasználó e-mailt kap róla, és a többi munkamenet nem tudja megmondani,
#: valódi-e a bukás. A visszakapcsolás feltétele a két hiba megértése és a
#: háromszori ismételt futás — ld. a hozzá tartozó jegyet.
_PARHUZAM = max(1, int(os.environ.get("PICASAPY_TESZT_PARHUZAM") or 0) or 1)


def _masik_futas_pidjei() -> list[int]:
    """Fut-e MÁSIK teljes tesztfuttatás ezen a gépen (csak Linuxon látható).

    A fejlesztői gép négymagos, és egyetlen párhuzamos futás már közel
    telíti. Kettő egyszerre CPU-éhezést okoz, amitől a fájlonkénti korlátba
    VALÓDI HIBA NÉLKÜL is bele lehet futni — a bukás pedig „ingadozó
    tesztnek" látszik. Pontosan ez vezetett félre egy másik munkamenetet
    (#914): a bukást a teszt számlájára írta, holott két egyidejű futás
    éheztette a gépet.
    """
    proc = Path("/proc")
    if not proc.is_dir():  # nem Linux (pl. a Windows-runner) — nem látjuk
        return []
    sajat = {os.getpid(), os.getppid()}
    talalatok: list[int] = []
    for konyvtar in proc.glob("[0-9]*"):
        try:
            pid = int(konyvtar.name)
            if pid in sajat:
                continue
            parancssor = (konyvtar / "cmdline").read_bytes().decode("utf-8", "replace")
        except (OSError, ValueError):
            continue  # a processz épp megszűnt, vagy nincs jogunk megnézni
        if _futtatja_a_futtatot(parancssor):
            talalatok.append(pid)
    return talalatok


#: Ennyi teljes tesztfutás mehet EGYSZERRE ezen a gépen (#1360). A
#: tulajdonos szava: „Lokális (RPi-n futó) teszt egyszerre max 2 futhat. Ezt
#: mindig elfelejti a developer agent." A felismerés eddig is megvolt
#: (`_masik_futas_pidjei`), a KORLÁT nem: akárhány session indíthatott kört,
#: mindegyik szabályosan sorosra váltott, és a négymagos gép mégis térdre
#: ment. Egy szabály, amit be kell tartatni, nem szabály: kapu.
_EGYIDEJU_ALAP = 2

#: Meddig várunk szabad helyre, mielőtt feladjuk.
_VARAKOZAS_S = 45 * 60

#: Két ellenőrzés közti szünet.
_VARAKOZAS_LEPES_S = 20.0

#: Kilépési kód, ha nem kaptunk helyet. SZÁNDÉKOSAN nem 1: az a
#: tesztbukásé. Az éjszakai műszak ebből tudja, hogy nincs mit javítania.
_NINCS_HELY_KOD = 75


def _egyideju_korlat() -> int:
    """Hány teljes futás mehet egyszerre; 0 = nincs korlát.

    ⚠️ A CI-t SOHA nem foghatja meg: ott minden job SAJÁT gépen fut, a
    korlát értelmetlen lenne — és ha egyszer megfogná, a főág pirosra
    váltana, amiről a tulajdonos e-mailt kap."""
    if os.environ.get("CI"):
        return 0
    try:
        return max(0, int(os.environ.get("PICASAPY_TESZT_EGYIDEJU") or _EGYIDEJU_ALAP))
    except ValueError:
        return _EGYIDEJU_ALAP


def _varj_szabad_helyre(
    *,
    korlat: int,
    varakozas_s: float,
    pidek: Callable[[], list[int]] | None = None,
    alvo: Callable[[float], None] = time.sleep,
) -> bool:
    """Vár, amíg felszabadul egy hely; `False`, ha lejárt a türelmi idő.

    A várakozás LÁTHATÓ: kiírja, kire vár. Néma fagyásból a következő
    munkamenet nem tudja megmondani, mi történik — és pont a némaság az,
    amiből a projektben eddig is a legtöbb félreértés lett."""
    if korlat <= 0:
        return True
    kerdez = pidek or _masik_futas_pidjei
    eltelt = 0.0
    jelentve = False
    while True:
        masok = kerdez()
        if len(masok) < korlat:
            if jelentve:
                print("Felszabadult egy hely — indulok.", flush=True)
            return True
        if not jelentve:
            print(
                f"MÁR {len(masok)} tesztfutás dolgozik ezen a gépen "
                f"(PID: {', '.join(str(p) for p in masok)}), a korlát {korlat}. "
                f"Várok szabad helyre — a gép négymagos, és a túlterhelésből "
                f"VALÓDI HIBA NÉLKÜLI bukások lesznek (#914, #1360).",
                flush=True,
            )
            jelentve = True
        if eltelt >= varakozas_s:
            return False
        alvo(_VARAKOZAS_LEPES_S)
        eltelt += _VARAKOZAS_LEPES_S


def _futtatja_a_futtatot(parancssor: str) -> bool:
    """A parancssor FUTTATJA a `run_tests.py`-t, vagy csak EMLÍTI?

    A puszta névegyezés kevés: a shell, a szerkesztő, a `ruff` és a `grep`
    parancssorában is ott a fájlnév — a fejlesztés közben ez folyamatosan
    téves riasztást adna. (Ugyanez a hibaosztály tegnap a kiadás-kaput is
    megvezette: ott a commit-üzenet EMLÍTETTE a tiltott parancsot.)

    Ezért két feltétel kell: a processz python-értelmező legyen, ÉS legyen
    olyan argumentuma, ami a futtatóra végződik.
    """
    reszek = [r for r in parancssor.split("\0") if r]
    if not reszek:
        return False
    program = Path(reszek[0]).name.lower()
    if not program.startswith("python"):
        return False
    return any(r.endswith("run_tests.py") for r in reszek[1:])


def _dontsd_el_a_parhuzamot(
    kert: str | None, alap: int, masik_fut: bool
) -> tuple[int, str]:
    """Hány szálon fussunk, és MIÉRT — naplózható indoklással.

    A kért érték (környezeti változó) mindig nyer: aki explicit beállítja,
    tudja, mit csinál. Automatikus visszalépés csak akkor van, ha nem kértek
    semmit, és közben fut egy másik futás.
    """
    if kert:
        return alap, f"kérésre (PICASAPY_TESZT_PARHUZAM={kert})"
    if masik_fut and alap > 1:
        return 1, "MÁSIK tesztfuttatás is dolgozik a gépen — sorosra váltok"
    return alap, "alapértelmezés"


#: A saját ideiglenes könyvtáraink gyökere és előtagja (#677). Az előtag azért
#: kell, hogy a takarítás CSAK a sajátunkhoz nyúljon.
_TEMP_GYOKER = Path(tempfile.gettempdir())
_TEMP_ELOTAG = "picasapy-tests-"

#: Ennél régebbi saját maradékot takarítunk mindenképpen. A kor a VÉGSŐ háló:
#: életjel nélküli maradékra és PID-újrahasznosításra is ez a válasz.
_MARADEK_KOR_S = 3 * 3600

#: A futás életjele a saját basetempjében (#1358). Enélkül a takarítás csak a
#: koron múlt: 2026-08-24-én négy megszakadt kör ~1,5 GB-ot hagyott a
#: `/tmp`-en, mindegyik fiatalabb a küszöbnél, miközben a folyamatuk rég
#: halott volt. A tulajdonosnak kellett szólnia.
_PID_FAJL = ".futas.pid"


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
            return _run(
                command, cwd=_ROOT, timeout=timeout_s, env=kornyezet
            ).returncode
        eredmeny = _run(
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


def _jelold_a_futast(basetemp: Path) -> None:
    """Életjel a basetempbe: melyik folyamat dolgozik itt (#1358).

    A kiírás bukása SOHA nem foghatja meg a tesztfutást — a takarítás
    kényelme nem előzheti meg magát a munkát."""
    try:
        (basetemp / _PID_FAJL).write_text(str(os.getpid()), encoding="utf-8")
    except OSError:
        pass


def _platform() -> str:
    """A futó platform — külön függvény, hogy a teszt helyettesíthesse (#1217).

    ⚠️ A windowsos ágat korábban `os.name` adta, és a tesztje a GLOBÁLIS
    `os.name`-et írta át (`monkeypatch.setattr(run_tests.os, "name", "nt")`).
    Az `os` itt MAGA a standard modul: a rögzítés a teszt teljes idejére
    minden más kódra is hatott. A fogantyú cseréje viszont csak ezt az
    egy döntést mozdítja."""
    return sys.platform


def _el_e_a_futas(konyvtar: Path) -> bool | None:
    """Él-e még a könyvtárhoz tartozó folyamat?

    `True` él, `False` halott, `None` **nem tudjuk** — és a három nem
    keverhető: a tudatlanságból nem lehet törlési döntés.

    ⚠️ A PID-kérdés kizárólag POSIX-on futhat. A CPython `os.kill(pid, 0)`
    Windowson nem életjel-kérdés, hanem `TerminateProcess` — MEGÖLNÉ a
    folyamatot. Ott `None`-t adunk, és marad a kor-szabály."""
    if _platform().startswith("win"):
        return None
    try:
        pid = int((konyvtar / _PID_FAJL).read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return None
    try:
        _kill(pid, 0)
    except ProcessLookupError:
        return False
    except OSError:
        # létezik, de nem a miénk (vagy nem kérdezhető) — ne töröljünk
        return True
    return True


def _takarits_regi_maradekot() -> None:
    """Korábbi (megszakadt) futások saját maradékainak eltakarítása.

    CSAK a saját előtagunkra nyúlunk, és két lépcsőben döntünk:

    1. **életjel** — ha a könyvtárhoz tartozó folyamat bizonyítottan halott,
       a maradék mehet, kortól függetlenül (#1358);
    2. **kor** — végső háló az életjel nélküli maradékra, a Windowsra és a
       PID-újrahasznosításra.

    Élő futás könyvtárához SOHA nem nyúlunk: azt elvinni rosszabb, mint
    helyet pazarolni."""
    hatarido = time.time() - _MARADEK_KOR_S
    for konyvtar in _TEMP_GYOKER.glob(f"{_TEMP_ELOTAG}*"):
        if not konyvtar.is_dir():
            continue
        try:
            regi = konyvtar.stat().st_mtime <= hatarido
            if not regi and _el_e_a_futas(konyvtar) is not False:
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
    _run(
        [sys.executable, "-m", "coverage", "combine"], cwd=_ROOT, check=False
    )
    print("$ coverage report", flush=True)
    _run(
        [sys.executable, "-m", "coverage", "report"], cwd=_ROOT, check=False
    )


def _bejelentkezes() -> None:
    """Kiírja, hány szálon és hány magon futunk — és ha kell, sorosra vált.

    Miért kell ez a sor: egy CPU-éhezésben született bukás a naplóban
    UGYANÚGY néz ki, mint egy valódi. A #914-es jegyet emiatt diagnosztizálta
    félre egy másik munkamenet — a napló nem árulta el, hogy két teljes futás
    osztozott négy magon. Ez az egy sor utólag eldönthetővé teszi.
    """
    global _PARHUZAM
    masik = _masik_futas_pidjei()
    _PARHUZAM, indok = _dontsd_el_a_parhuzamot(
        os.environ.get("PICASAPY_TESZT_PARHUZAM"), _PARHUZAM, bool(masik)
    )
    print(
        f"Futtatás: {_PARHUZAM} párhuzamos részfutás / {os.cpu_count()} mag "
        f"({indok}).",
        flush=True,
    )
    if masik:
        print(
            f"FIGYELEM: másik tesztfuttatás is fut (PID: "
            f"{', '.join(str(p) for p in masik)}). Egy bukás ilyenkor lehet "
            "puszta CPU-éhezés is — a jegynyitás előtt futtasd újra tiszta gépen.",
            flush=True,
        )


def _shard_parameter(argv: list[str]) -> tuple[int, int]:
    """A `--shard i/N` értelmezése; hiányában `(1, 1)` = a teljes készlet.

    ⚠️ Ez NEM a gépen belüli párhuzamosítás (#1030/#1031: az CPU-éhezésben
    pirosra vitte a főágat, vissza kellett venni). Itt minden darab SAJÁT
    futtatón fut, magában — a fájlonkénti izoláció (#53) és a `/tmp`-korlát
    (#677) garanciái érintetlenek."""
    for i, arg in enumerate(argv):
        ertek = None
        if arg == "--shard" and i + 1 < len(argv):
            ertek = argv[i + 1]
        elif arg.startswith("--shard="):
            ertek = arg.split("=", 1)[1]
        if ertek is None:
            continue
        sorszam, _, darab = ertek.partition("/")
        try:
            sorszam_i, darab_i = int(sorszam), int(darab)
        except ValueError:
            raise SystemExit(f"Hibás --shard érték: {ertek!r} (várt: i/N)") from None
        if not (1 <= sorszam_i <= darab_i):
            raise SystemExit(f"Hibás --shard tartomány: {ertek!r}")
        return sorszam_i, darab_i
    return 1, 1


def _kiegyensulyozott_darab(
    egysegek: list[str], sorszam: int, darab: int
) -> set[str]:
    """A `sorszam.` darabhoz tartozó egységek — MÉRT idők szerint kiosztva.

    Mohó kiosztás: a leghosszabb egység megy mindig a legkevésbé terhelt
    darabba. Enélkül a darabok egyenetlenek, és a leglassabb határozza meg a
    kör végét — a felosztás fele haszna elveszne.

    Ismeretlen egységre a MEDIÁN időt vesszük, nem nullát: egy új tesztfájl
    így nem torzítja a kiosztást azzal, hogy „ingyen van"."""
    if darab <= 1:
        return set(egysegek)
    idok = _mert_idok()
    ismert = sorted(idok[nev] for nev in egysegek if nev in idok)
    median = ismert[len(ismert) // 2] if ismert else 1.0
    terhelés = [0.0] * darab
    kiosztas: list[list[str]] = [[] for _ in range(darab)]
    for nev in sorted(egysegek, key=lambda n: -idok.get(n, median)):
        cel = min(range(darab), key=lambda i: terhelés[i])
        kiosztas[cel].append(nev)
        terhelés[cel] += idok.get(nev, median)
    return set(kiosztas[sorszam - 1])


def _mert_idok() -> dict[str, float]:
    """A commitolt futásidő-térkép; hiányában üres (minden egység medián)."""
    ut = _ROOT / "scripts" / "teszt_idok.json"
    try:
        return json.loads(ut.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    cov = "--cov" in argv

    if cov:
        # tiszta lap: egy korábbi (pl. megszakadt) --cov futásból maradt
        # .coverage.* adatfájlok ne keveredjenek a mostani mérésbe.
        _run(
            [sys.executable, "-m", "coverage", "erase"], cwd=_ROOT, check=False
        )

    if "--csak-takaritas" in argv:
        # A munkamenet-indító ezt hívja (#1358): minden új session rendet
        # rak, tesztfuttatás nélkül is. Aki csak fejleszt vagy kutat, eddig
        # sosem takarított.
        _takarits_regi_maradekot()
        return 0

    _bejelentkezes()
    _takarits_regi_maradekot()

    # #1360: a harmadik egyidejű futás VÁRJON, ne induljon el. A gép
    # négymagos; a túlterhelésből valódi hiba nélküli bukások lesznek.
    if not _varj_szabad_helyre(
        korlat=_egyideju_korlat(), varakozas_s=_VARAKOZAS_S
    ):
        print(
            "\nNEM INDULOK EL: nem szabadult fel hely a türelmi idő alatt.\n"
            "⚠️ Ez NEM a tesztek bukása — nincs mit javítani rajtuk. Várd meg,\n"
            "amíg a másik két futás befejeződik, és indítsd újra.",
            flush=True,
        )
        return _NINCS_HELY_KOD
    sorszam, darab = _shard_parameter(argv)
    basetemp = Path(tempfile.mkdtemp(prefix=_TEMP_ELOTAG, dir=_TEMP_GYOKER))
    _jelold_a_futast(basetemp)
    try:
        return _futtat(cov, basetemp, sorszam=sorszam, darab=darab)
    finally:
        # a takarítás nem függhet attól, zöld volt-e a futás, és attól sem,
        # hogy megszakították-e (#677)
        shutil.rmtree(basetemp, ignore_errors=True)


#: A nem-app készlet egyetlen egységként szerepel a kiosztásban.
_NEM_APP = "tests --ignore=tests/app"


def _futtat(
    cov: bool, basetemp: Path, *, sorszam: int = 1, darab: int = 1
) -> int:
    """A tényleges részfutás-sorozat; a basetemp életciklusa a hívóé.

    `darab > 1` esetén CSAK a `sorszam.` darabhoz kiosztott egységek futnak
    — a többi darabot másik futtató viszi (#1127)."""
    failures: list[tuple[str, int]] = []

    app_dir = _ROOT / "tests" / "app"
    app_test_files = sorted(app_dir.glob("test_*.py")) + sorted(
        (app_dir / "qml_functional").glob("test_*.py")
    )
    egysegek = [_NEM_APP] + [str(p.relative_to(_ROOT)) for p in app_test_files]
    enyem = _kiegyensulyozott_darab(egysegek, sorszam, darab)
    if darab > 1:
        print(
            f"Darab {sorszam}/{darab}: {len(enyem)} egység a {len(egysegek)}-ből.",
            flush=True,
        )

    if _NEM_APP in enyem:
        returncode = _run_pytest(
            ["tests", "--ignore=tests/app"],
            _NON_APP_TIMEOUT_S,
            cov=cov,
            basetemp=basetemp,
        )
        if returncode != 0:
            failures.append(("tests (tests/app nélkül)", returncode))

    # a tests/app közvetlen fájljai + a tests/app/qml_functional/ alattiak
    # (#155: a korábbi test_qml_functional.py szétbontásából) — mindegyik
    # KÜLÖN processzben, hogy egy fájlon belüli sok engine-életciklus se
    # torlódjon egyetlen processzbe.
    app_test_files = [
        p for p in app_test_files if str(p.relative_to(_ROOT)) in enyem
    ]
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
            # Csak ASCII jelölés: a Windows-runner konzolja cp1252-ben ír, és
            # a pipálás-karakter `UnicodeEncodeError`-ral MEGÖLTE a futást
            # (mérve, #1030 első köre) — a kimenet díszítése nem érhet ennyit.
            if returncode == 0:
                print(f"  ok   {relative}", flush=True)
                continue
            failures.append((relative, returncode))
            print(f"  HIBA {relative}: exit {returncode}", flush=True)
            # a bukott részfutás teljes kimenete — soros futásnál ez amúgy is
            # a képernyőn lenne, itt gyűjtve kerül ki, egyben
            print(_KIMENET.get(relative, "(nincs kimenet)"), flush=True)
    return failures


if __name__ == "__main__":
    sys.exit(main())
