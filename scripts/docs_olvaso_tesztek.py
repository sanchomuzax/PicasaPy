#!/usr/bin/env python3
"""Mely tesztek OLVASSÁK a `docs/` fát — mérve, nem felsorolva (#1863).

## A hibaosztály

A CI „Változás-elemzés" lépése a `docs/` egészét nem-kódnak veszi, tehát
egy csak-`docs/` PR-en a **teljes tesztmátrix kimarad**. Csakhogy a `docs/`
alatt **tesztadat** is van. Éles eset (2026-09-01, #1858): egy ilyen PR
zölden beolvadt, a bukó teszt **ki sem futott**, és a `main` pirosra
váltott — minden más PR-t blokkolva, amíg ki nem derült.

## Amit a MÉRÉS mondott — és amit a szemrevételezés nem

A #1863 jegy kilenc `docs/`-fájlt sorolt fel „tesztadatként", és a
javítást egy kilenc elemű kivétel-listaként képzelte el.

**Megmérve (`--mer`): 105 `docs/`-fájlt nyitnak meg a tesztek.** A
különbség oka, hogy két őr (`check_decision_links`, `check_protected_features`)
a TELJES fát bejárja — tehát gyakorlatilag BÁRMELY `docs/`-fájl
megváltoztatása hathat egy teszt eredményére. Egy kilenc elemű lista nem
javította volna ki a hibát, csak eltakarta volna.

**A jó hír ugyanabból a mérésből:** a 105 fájlt mindössze néhány
tesztfájl olvassa. Nem kell tehát a teljes mátrixot lefuttatni egy
dokumentációs PR-en — elég EZEKET. Ez a különbség percek és másodpercek
között; a fölösleges CI-kör a tulajdonos ideje.

## Miért baseline, és nem menet közbeni származtatás

A listát nem lehet a CI-ben kiszámolni: ahhoz le kellene futtatni a
teszteket, hogy eldöntsük, mely teszteket kell lefuttatni. A statikus
közelítés (a fájlnév előfordulása a `tests/` forrásaiban) MÉRVE túl tág:
61 fájlt jelölt meg olyat is, amit egy docstring csak EMLÍT.

Ezért — a projekt bevált mintája szerint (`dead_signals_baseline.txt`,
`kepesseg_or_baseline.txt`) — a lista **bevezetett alapállapot**, mellette
a MÉRŐVEL, amivel bármikor újraszámolható:

```
python3 scripts/docs_olvaso_tesztek.py --mer            # újramérés
python3 scripts/docs_olvaso_tesztek.py                  # a mai alapállapot
```

A mérés `sys.addaudithook`-kal minden VALÓDI fájlmegnyitást lát — nem
mintát illeszt, tehát a `read_text`, az `open` és a `glob`-bal bejárt fa
is beleszámít.
"""

from __future__ import annotations

import argparse
import os
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent

#: A `docs/` fát OLVASÓ tesztfájlok — mérve 2026-09-01-én (`--mer`).
#: Egy csak-dokumentációs PR-en a CI EZEKET futtatja le a kihagyott
#: mátrix helyett. Ha új őr kezd `docs/`-ot olvasni, a mérőt le kell
#: futtatni; a `tests/tools/test_docs_olvaso_tesztek_1863.py` legalább
#: azt észreveszi, ha egy itt felsorolt fájl eltűnik vagy átnevezik.
DOCS_OLVASO_TESZTEK: tuple[str, ...] = (
    "tests/app/qml_functional/test_sajat_funkcio_jeloles_1701.py",
    "tests/render/test_display_modes_1577_1578.py",
    "tests/test_index_leltar_szam_1512.py",
    "tests/test_ui_lefedettseg_megfeleltetes_707.py",
    "tests/tools/test_check_decision_links_1623.py",
    "tests/tools/test_check_protected_features_1187.py",
    "tests/tools/test_kepesseg_or_1476.py",
    "tests/tools/test_validation_kit_685.py",
)

#: ⚠️ A MÉRÉS HATÁRA — a `tests/app` fát nem futtattam végig audit-horoggal
#: (Qt-nehéz, több mint tíz perc). Ott előbb szűkítettem: azokat a fájlokat
#: kerestem, amelyek TÉNYLEGES útvonalat építenek a `docs/`-hoz
#: (`/ "docs"`, `"docs/….md"`, `SPEC_DIR`) — a 82 „docs" szót EMLÍTŐ
#: fájlból EGY ilyen volt —, és AZT mértem le. Ha egy `tests/app`-teszt
#: szokatlan módon rakja össze az útvonalat (pl. darabokból), a szűrés
#: kihagyhatta. A `tests/golden` alatt a szűrés semmit nem talált.


def _mer(pytest_argumentumok: list[str]) -> int:
    """A tesztek futtatása audit-horoggal: mely tesztfájl nyit `docs/`-ot."""
    import collections
    import json

    aktualis = {"fajl": "<gyűjtés>"}
    terkep: dict[str, set[str]] = collections.defaultdict(set)

    def horog(esemeny: str, argumentum) -> None:
        if esemeny != "open":
            return
        ut = argumentum[0]
        if not isinstance(ut, (str, bytes, os.PathLike)):
            return
        try:
            rel = pathlib.Path(os.fsdecode(ut)).resolve().relative_to(REPO)
        except (ValueError, OSError):
            return
        if rel.parts and rel.parts[0] == "docs" and rel.suffix:
            terkep[aktualis["fajl"]].add(str(rel))

    sys.path.insert(0, str(REPO))
    sys.addaudithook(horog)
    import pytest

    class Figyelo:
        def pytest_runtest_protocol(self, item, nextitem):  # noqa: ARG002
            aktualis["fajl"] = item.nodeid.split("::")[0]

    pytest.main(pytest_argumentumok, plugins=[Figyelo()])
    print("\n--- MÉRT eredmény ---")
    for fajl, lapok in sorted(terkep.items()):
        print(f"{len(lapok):5}  {fajl}")
    print("\nJSON:", json.dumps(sorted(terkep), ensure_ascii=False))
    return 0


def main(argv: list[str] | None = None) -> int:
    ertelmezo = argparse.ArgumentParser(description=__doc__)
    ertelmezo.add_argument(
        "--mer", action="store_true", help="újramérés (a maradék argumentum a pytesté)"
    )
    ismert, tovabbi = ertelmezo.parse_known_args(argv)
    if ismert.mer:
        return _mer(tovabbi or ["tests", "-q"])
    print("\n".join(DOCS_OLVASO_TESZTEK))
    return 0


if __name__ == "__main__":
    sys.exit(main())
