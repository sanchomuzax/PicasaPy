#!/usr/bin/env python3
"""#1653 mérőkocsi: az indulási idővonal felvétele CI-futón, platformonként.

**Miért kell.** A tulajdonos Windowson **33 s** (második indításnál 25 s)
indulást jelentett, miközben a fejlesztői gépen (Linux, RPi5) **5,18 s**
a mérés (`docs/benchmarks/2026-08-27-indulasi-ido-1601.md`). Van tehát egy
~6x-os, **Windows-specifikus** tényező, amit soha nem mértünk. A
tulajdonost nem szabad méréssel terhelni (nem fejlesztő), ezért a mérésnek
magától kell megtörténnie — a GitHub `windows-latest` futóján.

**Mit csinál.** Elindítja a programot alprocesszként, bekapcsolt indulási
idővonallal (`PICASAPY_STARTUP_TIMELINE=1`,
`src/picasapy/perf/startup_timeline.py`), megvárja, amíg a jelentés
kiíródik, kiírja, majd leállítja a processzt. Ugyanez lefuttatható üres és
szintetikusan generált, nagy könyvtárral — a kettő KÜLÖNBSÉGE mondja meg,
méretfüggő-e az indulás.

**Miért fájlból olvassuk a jelentést, nem a `stderr`-ből.** A jelentés a
`stderr`-re IS megy, de Windowson a Python csővezetékre írva a rendszer
kódlapját (cp1252) használja, és a magyar ékezetes szöveg ott
`UnicodeEncodeError`-t adna — az `application.py` pedig (helyesen) elnyeli
a diagnosztika hibáját. A fájl viszont mindig UTF-8. A `PYTHONIOENCODING`-ot
ettől függetlenül beállítjuk, hogy a `stderr` is olvasható maradjon.

**Izolált környezet.** Minden futás saját adat-/gyorstár-/konfigkönyvtárat
kap (`XDG_*` Linuxon, `APPDATA`/`LOCALAPPDATA` Windowson —
`app/platform_storage.py`), a `XDG_CACHE_HOME`-ot pedig MINDKÉT platformon
beállítjuk, mert a `perf/logwriter.default_log_dir()` azt olvassa. Így egy
futás nem viszi el a másik indexét, és a jelentés kiszámítható helyre kerül.

Használat::

    python scripts/indulas_meres.py --mappa-szam 0    --cimke "üres"
    python scripts/indulas_meres.py --mappa-szam 1000 --cimke "nagy"
    python scripts/indulas_meres.py --importtime

Ez **mérőeszköz, nem termékkód**: a `scripts/` alatt él, a `src/`-t nem
módosítja, és semmilyen CI-ellenőrzés nem függ tőle.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path

#: A repó gyökere és a forrásfa — a program a forrásból fut (nem telepítve),
#: ugyanúgy, ahogy a tesztek (`pythonpath = ["src"]`).
_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"

#: Szekció ini-nként. A valódi korpusz aránya (18 801 szekció / 859 ini),
#: ugyanaz a szám, amit a `tests/app/test_indulas_or_1601.py` használ —
#: enélkül az ini-k olyan könnyűek lennének, hogy a mérésnek nincs foga.
_SZEKCIO_PER_INI = 22

_ROY = "b8e4117cf1d6615b"
_ANNA = "a1a2a3a4a5a6a7a8"
_RECT = "3f840000c3509f84"

#: Meddig várunk a jelentésre. A tulajdonos gépén 33 s az indulás; a
#: windowsos CI-futó ennél lassabb is lehet, a nagy könyvtár beolvasása
#: pedig ráadás. Bőven fölé lőve, hogy a mérés ne a korlátba fusson.
_ALAP_IDOKORLAT_MP = 600.0


def _minta_jpeg(cel: Path) -> bytes:
    """Egyetlen kis JPEG bájtjai — a többi mappába ez másolódik.

    A képet EGYSZER állítjuk elő, utána bájtmásolat: a könyvtár felépítése
    így nem viszi el a mérés idejét (a `test_indulas_or_1601.py` mintája)."""
    from PIL import Image

    Image.new("RGB", (32, 24), (120, 140, 160)).save(cel, "JPEG", quality=60)
    return cel.read_bytes()


def _szintetikus_konyvtar(gyoker: Path, mappa_szam: int) -> None:
    """`mappa_szam` mappa, mindegyikben egy kép és egy valósághű súlyú ini.

    `mappa_szam == 0` esetén a gyökér üres marad — ez a méretfüggés
    kontrollja."""
    gyoker.mkdir(parents=True, exist_ok=True)
    if mappa_szam <= 0:
        return
    minta = gyoker / "minta.jpg"
    blob = _minta_jpeg(minta)
    minta.unlink()
    szekciok = "".join(
        f"[IMG_{n:04d}.JPG]\n"
        f"faces=rect64({_RECT}),{_ROY};rect64({_RECT}),{_ANNA};\n"
        f"filters=enhance=1;\n"
        for n in range(_SZEKCIO_PER_INI)
    )
    ini = (
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n{_ANNA}=Anna Kis;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n" + szekciok
    )
    for i in range(mappa_szam):
        mappa = gyoker / f"{2000 + i % 20}" / f"{i:04d}"
        mappa.mkdir(parents=True, exist_ok=True)
        (mappa / "a.jpg").write_bytes(blob)
        (mappa / ".picasa.ini").write_text(ini, encoding="utf-8")


def _izolalt_kornyezet(alap: Path) -> dict[str, str]:
    """Saját adat-/gyorstár-/konfigkönyvtár a futásnak, mindkét platformon.

    A `platform_storage.default_storage_paths` Windowson a
    `LOCALAPPDATA`/`APPDATA`-t, máshol az `XDG_*`-ot olvassa; a
    `perf/logwriter.default_log_dir()` viszont MINDENHOL az
    `XDG_CACHE_HOME`-ot — ezért mindhármat beállítjuk."""
    env = dict(os.environ)
    for nev in ("data", "cache", "config", "appdata", "local"):
        (alap / nev).mkdir(parents=True, exist_ok=True)
    env.update(
        {
            "PICASAPY_STARTUP_TIMELINE": "1",
            "QT_QPA_PLATFORM": "offscreen",
            # a jelentés ékezetes; cső mögött a Windows cp1252-t választana
            "PYTHONIOENCODING": "utf-8",
            "PYTHONUTF8": "1",
            "XDG_DATA_HOME": str(alap / "data"),
            "XDG_CACHE_HOME": str(alap / "cache"),
            "XDG_CONFIG_HOME": str(alap / "config"),
            # ⚠️ A `HOME`/`USERPROFILE` SZÁNDÉKOSAN marad a valódi: a
            # Python felhasználói csomagkönyvtára (`~/.local/lib/...`)
            # onnan oldódik fel, és átírva a program `ModuleNotFoundError`-ral
            # el sem indul (mérve, első nekifutás). Nincs is rá szükség: a
            # tárhely útjait a `platform_storage` az alábbi változókból
            # olvassa, a naplóét pedig az `XDG_CACHE_HOME`-ból.
            "APPDATA": str(alap / "appdata"),
            "LOCALAPPDATA": str(alap / "local"),
            "PYTHONPATH": os.pathsep.join(
                [str(_SRC), os.environ.get("PYTHONPATH", "")]
            ).rstrip(os.pathsep),
        }
    )
    return env


_SZAKASZ_SOR = re.compile(r"^\s*([0-9]+(?:\.[0-9]+)?)\s\s+(\S.*)$")


def _szakaszok(jelentes: str) -> list[tuple[str, float]]:
    """A kiírt táblázat visszafejtése `(címke, ms)` párokra.

    Az összegző sorokat (`a mért szakaszok összege`, `ÖSSZESEN`) és a
    „három leglassabb" blokkot kihagyja — azok származtatottak."""
    talalt: list[tuple[str, float]] = []
    for sor in jelentes.splitlines():
        if sor.startswith("A három leglassabb"):
            break
        egyezes = _SZAKASZ_SOR.match(sor)
        if egyezes is None:
            continue
        cimke = egyezes.group(2).strip()
        if cimke.startswith("a mért szakaszok") or cimke.startswith("ÖSSZESEN"):
            continue
        talalt.append((cimke, float(egyezes.group(1))))
    return talalt


def _osszesen_ms(jelentes: str) -> float:
    """Az `ÖSSZESEN` sor értéke — a teljes indulás."""
    for sor in jelentes.splitlines():
        egyezes = _SZAKASZ_SOR.match(sor)
        if egyezes is not None and egyezes.group(2).startswith("ÖSSZESEN"):
            return float(egyezes.group(1))
    return 0.0


def _egy_futas(
    gyoker: Path, alap: Path, idokorlat: float
) -> tuple[str, float]:
    """Egy indítás; a jelentés szövegét és a valós faliórai időt adja.

    A visszaadott másodperc a processz INDÍTÁSÁTÓL a jelentés
    megjelenéséig telik — ez tartalmazza az értelmező indulását is,
    tehát összemérhető azzal, amit a felhasználó „vár"."""
    env = _izolalt_kornyezet(alap)
    naplo_konyvtar = Path(env["XDG_CACHE_HOME"]) / "picasapy" / "perf"
    # ⚠️ A KORÁBBI futások jelentéseit számon kell tartani. Az adat- és
    # gyorstárkönyvtár szándékosan MEGMARAD a futások között (a 2. indítás
    # így lát meleg indexet), és a jelentések is ugyanoda gyűlnek. Az első
    # változat egyszerűen a legfrissebb `indulas-*.txt`-t vette — mérve
    # (33105116153) a 2. indítás az 1. jelentését olvasta vissza: azonos
    # szakaszok, 0,0 mp faliórai idő. Csak ÚJ fájlt fogadunk el.
    mar_volt = set(naplo_konyvtar.glob("indulas-*.txt"))
    kimenet = alap / "kimenet.txt"
    indult = time.monotonic()
    with kimenet.open("wb") as ki:
        proc = subprocess.Popen(
            [sys.executable, "-m", "picasapy.app", str(gyoker)],
            cwd=str(_REPO),
            env=env,
            stdout=ki,
            stderr=subprocess.STDOUT,
        )
        try:
            hatarido = indult + idokorlat
            jelentes_fajl: Path | None = None
            while time.monotonic() < hatarido:
                talalt = sorted(
                    set(naplo_konyvtar.glob("indulas-*.txt")) - mar_volt
                )
                if talalt:
                    jelentes_fajl = talalt[-1]
                    break
                if proc.poll() is not None:
                    break
                time.sleep(0.2)
            eltelt = time.monotonic() - indult
        finally:
            if proc.poll() is None:
                proc.terminate()
                try:
                    proc.wait(timeout=20)
                except subprocess.TimeoutExpired:
                    proc.kill()
                    proc.wait(timeout=20)
    if jelentes_fajl is None:
        naplo = kimenet.read_text(encoding="utf-8", errors="replace")
        raise RuntimeError(
            "nem született indulási jelentés "
            f"{idokorlat:.0f} mp alatt. A processz kimenete:\n{naplo}"
        )
    # A fájl írása és a glob között lehet fél sor — rövid ideig újraolvassuk.
    for _ in range(20):
        szoveg = jelentes_fajl.read_text(encoding="utf-8", errors="replace")
        if "ÖSSZESEN" in szoveg:
            return szoveg, eltelt
        time.sleep(0.1)
    return szoveg, eltelt


def _importtime() -> str:
    """`python -X importtime` az indulási importláncra, rendezett kivonattal.

    Ez az egyetlen mód, amivel az idővonal első — és Linuxon a legnagyobb —
    szakasza (`Python- és PySide6-modulok betöltése`) FELBONTHATÓ, anélkül
    hogy a termékkódba mérőpontot kellene tenni."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_SRC), os.environ.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            "-X",
            "importtime",
            "-c",
            "import picasapy.app.application",
        ],
        cwd=str(_REPO),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=600,
    )
    sorok: list[tuple[float, int, str]] = []
    for sor in proc.stderr.splitlines():
        if not sor.startswith("import time:"):
            continue
        reszek = sor.split("|")
        if len(reszek) != 3 or "cumulative" in reszek[1]:
            continue
        try:
            kumulalt_us = float(reszek[1].strip())
        except ValueError:
            continue
        nev = reszek[2]
        melyseg = (len(nev) - len(nev.lstrip())) // 2
        sorok.append((kumulalt_us / 1000.0, melyseg, nev.strip()))
    sorok.sort(key=lambda tetel: -tetel[0])
    fej = ["", "== importtime (kumulált, a 30 legdrágább modul) ==", ""]
    for ms, melyseg, nev in sorok[:30]:
        fej.append(f"{ms:9.1f} ms  [mélység {melyseg}]  {nev}")
    return "\n".join(fej)


def _utf8_kimenet() -> None:
    """A saját `stdout`/`stderr` UTF-8-ra állítása.

    ⚠️ Windowson a Python a cső mögött a rendszer kódlapját (cp1252)
    választja, és a jelentés magyar szövege ott `UnicodeEncodeError`-t ad —
    a mérés a KIÍRÁSNÁL bukik el, miután már lefutott (mérve: 33105116153,
    `'\\u0151' ... maps to <undefined>`). A munkafolyamat `PYTHONUTF8`-a
    kevés: ez a szkript helyben, saját magának is garantálja."""
    for folyam in (sys.stdout, sys.stderr):
        rekonfiguralas = getattr(folyam, "reconfigure", None)
        if rekonfiguralas is not None:
            rekonfiguralas(encoding="utf-8", errors="replace")


def main(argv: list[str] | None = None) -> int:
    _utf8_kimenet()
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument(
        "--mappa-szam",
        type=int,
        default=0,
        help="a szintetikus könyvtár mappáinak száma (0 = üres könyvtár)",
    )
    ertelmezo.add_argument(
        "--futasok",
        type=int,
        default=2,
        help="hány indítás (az 1. hideg indexszel, a többi melegen)",
    )
    ertelmezo.add_argument(
        "--cimke", default="", help="a futás neve a kimenetben"
    )
    ertelmezo.add_argument(
        "--idokorlat",
        type=float,
        default=_ALAP_IDOKORLAT_MP,
        help="meddig várjuk a jelentést, másodpercben",
    )
    ertelmezo.add_argument(
        "--importtime",
        action="store_true",
        help="csak az importlánc bontása (a program nem indul el)",
    )
    args = ertelmezo.parse_args(argv)

    if args.importtime:
        print(_importtime(), flush=True)
        return 0

    cimke = args.cimke or f"{args.mappa_szam} mappa"
    munka = Path(tempfile.mkdtemp(prefix="indulas-meres-"))
    try:
        gyoker = munka / "kepek"
        epult = time.monotonic()
        _szintetikus_konyvtar(gyoker, args.mappa_szam)
        print(
            f"== {cimke} == könyvtár: {args.mappa_szam} mappa, felépítés "
            f"{time.monotonic() - epult:.1f} mp · platform {sys.platform}",
            flush=True,
        )
        osszes: list[dict] = []
        for futas in range(1, args.futasok + 1):
            # Az adat-/gyorstárkönyvtár futások közt MEGMARAD (ugyanaz az
            # `alap`): a 2. indítás így valóban meleg indexet lát, ahogy a
            # tulajdonos „második indítás 25 mp" esete.
            alap = munka / "kornyezet"
            jelentes, eltelt = _egy_futas(gyoker, alap, args.idokorlat)
            print(f"\n---- {cimke} · {futas}. indítás ----", flush=True)
            print(jelentes, flush=True)
            print(
                f"faliórai idő az indítástól a jelentésig: {eltelt:.1f} mp",
                flush=True,
            )
            osszes.append(
                {
                    "cimke": cimke,
                    "platform": sys.platform,
                    "mappa_szam": args.mappa_szam,
                    "futas": futas,
                    "osszesen_ms": _osszesen_ms(jelentes),
                    "faliora_mp": round(eltelt, 2),
                    "szakaszok": _szakaszok(jelentes),
                }
            )
        # Egyetlen soros, gépi kivonat — a CI-naplóból ez emelhető ki.
        print("#1653-JSON " + json.dumps(osszes, ensure_ascii=False), flush=True)
    finally:
        shutil.rmtree(munka, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
