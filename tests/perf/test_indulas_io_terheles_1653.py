"""#1653 ŐR: az indulás I/O-terhelése nem hízhat észrevétlenül.

## Miért NEM időt mér ez az őr

A jegy azt kéri, hogy „a szakasz-idők felső korláttal" őrizzék az
indulást a CI Windows-lábán. **Megmértük, és időalapú őr itt nem
lehetséges flaky-ség nélkül.** Ugyanaz a szakasz
(`Python- és PySide6-modulok betöltése`), ugyanaz a commit, ugyanaz a
`windows-latest` futó, négy mérés (33105401549 és a rá következő
újrafuttatás):

| futás | üres könyvtár | 1000 mappa |
|---|---:|---:|
| 1. minta | 688 ms | 2 244 ms |
| 2. minta | 490 ms | 3 679 ms |

**7,5-szeres szórás** — miközben az importlánc a fotókönyvtárral
bizonyíthatóan nem áll kapcsolatban (a `mark_from` a belépési ponttól a
`run()`-ig mér, oda egyetlen könyvtárolvasás sem esik). A különbség a
futó lapgyorstárának állapota: a „nagy" lábon a mérés előtt 2 000 fájlt
hoztunk létre. Egy időküszöb, ami ezt nem veri ki hamisan, ~10 s-nál
lenne — az pedig egy kétszeres lassulást már nem fogna meg.

## Amit helyette őriz

Az indulás **nem processzor-, hanem fájlbeolvasás-korlátos**, és éppen ez
magyarázza a tulajdonos gépét: bármi, ami a bájtonkénti költséget
megszorozza (valós idejű vírusvizsgálat, hálózati meghajtó, forgólemez,
hideg lapgyorstár), közvetlenül ennyivel szorozza az indulást. Az őr
tehát a **beolvasandó mennyiséget** rögzíti, ami determinisztikus: nincs
óra, nincs terhelésfüggés, nincs flaky-ség.

## A mérce és a mért értékek

Az állítás: *az indulási importlánc natív kódja nem több, mint amennyit a
`cv2` és a `PySide6.QtQuick` **együtt** behúz.* Vagyis ma az indulás natív
lábnyoma pontosan az OpenCV + a Qt Quick, és **harmadik nehézsúlyú
függőség nem szivároghat be** észrevétlenül.

MÉRVE (2026-08-27, három különböző telepítésen):

| telepítés | app natív | cv2 + QtQuick | hányad |
|---|---:|---:|---:|
| windows-latest (run 33106909777) | 249,1 MB | 246,8 MB | **1,01** |
| ubuntu-latest (run 33106909777) | 379,6 MB | 382,7 MB | **0,99** |
| RPi5, Debian-csomagolt cv2 | 506,4 MB | 574,7 MB | **0,88** |

A küszöb **1,25** — a mért maximum (1,01) fölött 24%-kal.

⚠️ **Az őr szándékosan durva, és ezt ki kell mondani.** A ráhagyás
Windowson ~59 MB, a RPi5-ön ~212 MB új natív kód: egy kisebb natív
függőség belefér. Nem finomhangoló eszköz, hanem az `import cv2`-osztályú
belépések ellen véd — pontosan az ellen, ami ma az indulás felét viszi.

A Python-oldal külön, szűkebb korláttal: a betöltött modulok száma
557 / 565 / 583 volt a három telepítésen; a plafon **700**.

## Mutációs bizonyíték — az őrnek VAN foga

Egyetlen sor került az `application.py` importjai közé
(`import matplotlib.pyplot`), majd az őr újra lefutott:

```
723 Python-modul (a plafon 700)  → BUKIK
540,6 MB natív / 574,7 MB alap = 0,94 (a plafon 1,25) → átmegy
```

A mutáció visszavonásával mindkét állítás zöld (557 modul, 0,88).

Ez a próba a lap fenti figyelmeztetését is IGAZOLJA: a bájt-alapú
állítás a `matplotlib` teljes fáját (+34 MB natív) **átengedte** a RPi5-ön
— a modulszám fogta meg. A két állítás ezért **együtt** kell; egyik sem
elég magában.

## Kötés

* mérőeszköz: `scripts/indulas_meres.py` (`--io-terheles`)
* jegyzőkönyv: `docs/benchmarks/2026-08-27-indulas-windows-1653.md`
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(_REPO / "scripts"))

#: A megengedett hányad: az indulási lánc natív bájtjai a `cv2` és a
#: `PySide6.QtQuick` natív bájtjainak ÖSSZEGÉHEZ mérve. Mérve 0,88–1,01.
_MEGENGEDETT_HANYAD = 1.25

#: A betöltött Python-modulok plafonja. Mérve 557 / 565 / 583.
_MODUL_PLAFON = 700

#: Egy-egy gyermekmérés időkorlátja. A `cv2` importja hideg gyorstárral a
#: leglassabb gépünkön is bőven ezen belül van; a korlát a BERAGADT
#: processz ellen szól, nem a lassú ellen.
_IDOKORLAT_MP = 600


def _leltar(modul: str) -> dict:
    """Egy import fájl- és bájtterhelése — külön processzben mérve."""
    env = dict(os.environ)
    env["PYTHONPATH"] = os.pathsep.join(
        [str(_REPO / "src"), os.environ.get("PYTHONPATH", "")]
    ).rstrip(os.pathsep)
    env["PYTHONUTF8"] = "1"
    proc = subprocess.run(
        [
            sys.executable,
            str(_REPO / "scripts" / "indulas_meres.py"),
            "--leltar",
            modul,
        ],
        cwd=str(_REPO),
        env=env,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=_IDOKORLAT_MP,
    )
    assert proc.returncode == 0, (
        f"a `{modul or '(semmi)'}` leltára elbukott "
        f"(kilépőkód {proc.returncode}):\n{proc.stderr[-2000:]}"
    )
    return json.loads(proc.stdout.strip().splitlines()[-1])


@pytest.fixture(scope="module")
def leltarak() -> dict[str, dict]:
    """A három mérés EGYSZER fut le a fájlra — mindegyik nehéz import."""
    return {
        modul: _leltar(modul)
        for modul in ("cv2", "PySide6.QtQuick", "picasapy.app.application")
    }


class TestIndulasiIoTerheles:
    def test_a_meres_nem_uresedett_ki(self, leltarak):
        """Az ÜRES mérés maga is hiba — különben az őr némán zöld lenne.

        A #1476/#1468 tanulsága: egy elgépelt útvonal vagy egy elbukó
        rendszerhívás nem „hibátlan" eredmény. Windowson pontosan ez
        történt egyszer (`EnumProcessModules` `argtypes` nélkül: 0 natív
        modul, 0,0 MB — méréseredménynek látszó nulla)."""
        for modul, adat in leltarak.items():
            assert adat["nativ_fajl"] > 0, f"{modul}: nulla natív modul"
            assert adat["nativ_bajt"] > 0, f"{modul}: nulla natív bájt"
            assert adat["python_fajl"] > 0, f"{modul}: nulla Python-modul"

    def test_nem_kerul_harmadik_nehezsulyu_fuggoseg_az_indulasba(
        self, leltarak
    ):
        app = leltarak["picasapy.app.application"]["nativ_bajt"]
        alap = (
            leltarak["cv2"]["nativ_bajt"]
            + leltarak["PySide6.QtQuick"]["nativ_bajt"]
        )
        hanyad = app / alap
        assert hanyad <= _MEGENGEDETT_HANYAD, (
            f"az indulási importlánc {app / 1_048_576:.1f} MB natív kódot "
            f"tölt be, miközben a `cv2` és a `PySide6.QtQuick` együtt csak "
            f"{alap / 1_048_576:.1f} MB-ot (hányad {hanyad:.2f}, a plafon "
            f"{_MEGENGEDETT_HANYAD}). Egy ÚJ nehézsúlyú natív függőség "
            f"került az indulási útra. Az indulás fájlbeolvasás-korlátos "
            f"(#1653): a tulajdonos gépén minden beolvasott bájt "
            f"vírusvizsgálaton és/vagy hálózati körön megy át, tehát ez a "
            f"növekmény ott sokszorosan jelentkezik."
        )

    def test_a_betoltott_python_modulok_szama_nem_hizik(self, leltarak):
        darab = leltarak["picasapy.app.application"]["python_fajl"]
        assert darab <= _MODUL_PLAFON, (
            f"az indulás {darab} Python-modult tölt be (a plafon "
            f"{_MODUL_PLAFON}; mérve 557–583 volt három telepítésen). Új "
            f"csomagfa került az indulási importláncba — a #1653 szerint az "
            f"indulás fájlonkénti költsége a tulajdonos gépén sokszoros."
        )
