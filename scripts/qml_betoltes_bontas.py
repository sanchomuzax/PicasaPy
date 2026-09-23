#!/usr/bin/env python3
"""#3383 mérőkocsi: a `Main.qml` betöltése FORDÍTÁSRA és PÉLDÁNYOSÍTÁSRA bontva.

**Miért kell.** A #3253 kimutatta, hogy a QML-szakasz egyetlen osztatlan
létrehozási menet, és QML-oldali jelölővel nem bontható. A Qt saját
QML-profilere (`qmldbg_profiler`) ezen a gépen **nincs telepítve** (a
Qt-bővítmények között nincs `qmltooling`), ezért ez a mérő a Qt nyilvános
API-jával választja szét a két lépést:

* **fordítás** — `QQmlComponent(engine, url, PreferSynchronous)`, amíg
  `Ready` lesz (a teljes típusfa betöltése, a Qt lemez-gyorsítótárával vagy
  anélkül);
* **példányosítás** — `component.create(rootContext)` (a teljes fa
  létrehozása a `Component.onCompleted` kezelőkkel együtt).

A valódi `application.run()` fut (minden vezérlő, kontextus-tulajdonság és
képszolgáltató a helyén); csak a `QQmlApplicationEngine.load` helyére kerül
egy mérő, ami kiírja az eredményt és kilép — az ablak eseményciklusa el sem
indul.

**Három üzemmód:** `hideg` (üres gyorsítótár — az első indítás egy frissítés
után), `meleg` (ugyanaz a gyorsítótár újra — minden további indítás) és
`load` (az eredeti `engine.load` egyben, összevetésnek).

⚠️ Amit NEM mér: elemenkénti bontást (ahhoz a profiler-bővítmény kell), és a
`load` meg a `fordítás + példányosítás` közti különbséget sem bontja tovább
(ld. `docs/benchmarks/2026-09-23-qml-forditas-peldanyositas-3383.md`).

Használat::

    python scripts/qml_betoltes_bontas.py --ismetles 6

Ez **mérőeszköz, nem termékkód**: a `src/`-t nem módosítja.
"""

from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent
_SRC = _REPO / "src"
_PLAFON = ["systemd-run", "--user", "--scope", "-q", "-p", "MemoryMax=2400M",
           "-p", "MemorySwapMax=0", "--"]


def _gyermek(kimenet: str, mod: str) -> None:
    """A mért folyamat: a `load` helyére a mérő kerül, a többi valódi."""
    from PySide6.QtCore import QUrl
    from PySide6.QtQml import QQmlApplicationEngine, QQmlComponent

    eredeti = QQmlApplicationEngine.load

    def kiir(adat: dict) -> None:
        Path(kimenet).write_text(json.dumps(adat), encoding="utf-8")
        os._exit(0)

    def bontva(self, url):
        cim = url if isinstance(url, QUrl) else QUrl.fromLocalFile(str(url))
        t0 = time.perf_counter()
        comp = QQmlComponent(self, cim, QQmlComponent.CompilationMode.PreferSynchronous)
        t1 = time.perf_counter()
        obj = comp.create(self.rootContext()) if comp.isReady() else None
        t2 = time.perf_counter()
        kiir({"forditas_ms": (t1 - t0) * 1000, "peldanyositas_ms": (t2 - t1) * 1000,
              "letrejott": obj is not None,
              "hibak": [e.toString() for e in comp.errors()][:5]})

    def egyben(self, url):
        t0 = time.perf_counter()
        eredeti(self, url)
        kiir({"load_ms": (time.perf_counter() - t0) * 1000,
              "letrejott": bool(self.rootObjects())})

    QQmlApplicationEngine.load = egyben if mod == "load" else bontva
    sys.path.insert(0, str(_SRC))
    from picasapy.app import application

    sys.exit(application.run([sys.argv[0]]))


def _futas(munka: Path, gyorstar: Path, mod: str, cimke: str) -> dict:
    kimenet = munka / f"{cimke}.json"
    env = dict(os.environ, QT_QPA_PLATFORM="offscreen", PYTHONPATH=str(_SRC),
               XDG_DATA_HOME=str(munka / "data"), XDG_CONFIG_HOME=str(munka / "config"),
               XDG_CACHE_HOME=str(gyorstar))
    parancs = [sys.executable, __file__, "--gyermek", str(kimenet), mod]
    if sys.platform.startswith("linux"):
        parancs = _PLAFON + parancs
    subprocess.run(parancs, env=env, cwd=_REPO, timeout=180,
                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=False)
    if not kimenet.exists():
        raise RuntimeError(f"a(z) {cimke} futás nem adott eredményt")
    adat = json.loads(kimenet.read_text(encoding="utf-8"))
    if not adat.get("letrejott"):
        raise RuntimeError(f"a(z) {cimke} futásban nem jött létre a fa: {adat}")
    return adat


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--ismetles", type=int, default=3)
    parser.add_argument("--gyermek", nargs=2, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if args.gyermek:
        _gyermek(*args.gyermek)
        return 0

    sorok: dict[str, list[float]] = {}

    def tesz(kulcs: str, ertek: float) -> None:
        sorok.setdefault(kulcs, []).append(ertek)

    with tempfile.TemporaryDirectory(prefix="qml-bontas-") as tmp:
        munka = Path(tmp)
        for i in range(1, args.ismetles + 1):
            gyorstar = munka / f"cache{i}"
            hideg = _futas(munka, gyorstar, "bontas", f"hideg{i}")
            tesz("hideg fordítás", hideg["forditas_ms"])
            tesz("hideg példányosítás", hideg["peldanyositas_ms"])
            meleg = _futas(munka, gyorstar, "bontas", f"meleg{i}")
            tesz("meleg fordítás", meleg["forditas_ms"])
            tesz("meleg példányosítás", meleg["peldanyositas_ms"])
            tesz("meleg engine.load egyben", _futas(munka, gyorstar, "load", f"load{i}")["load_ms"])
            print(f"{i}. kör kész", flush=True)

    print(f"\n{'tétel':<28}{'medián ms':>11}   egyedi értékek")
    for kulcs, ertekek in sorok.items():
        egyedi = " · ".join(f"{e:.0f}" for e in ertekek)
        print(f"{kulcs:<28}{statistics.median(ertekek):>11.1f}   {egyedi}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
