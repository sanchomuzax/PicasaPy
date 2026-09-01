"""#1611 — az OpenCV NE töltődjön be az induláskor.

## A lelet

`import picasapy.app.application` importidejének **1 639 ms**-át a `cv2`
betöltése vitte el (`python3 -X importtime`, RPi5). Ez minden induláskor
lefutott, akkor is, ha a felhasználó egyetlen effektet, mentést vagy
arckeresést sem használt.

## Miért nem volt elég egy helyen javítani

Az indulási modullista és a `cv2`-t importáló modulok metszete **33
modul** volt. Ha egyetlen láncot halasztunk, a `cv2`-t a következő modul
behúzza — ez a #1601 nulla nyereségének oka, és ezért kellett MIND a 33-at
átvezetni a `picasapy.cv` homlokzatra.

## Az őr

Két állítás, két irányból:

1. **Szerkezeti**: egyetlen `picasapy` modul se importálja közvetlenül a
   `cv2`-t modul-szinten (a homlokzatot kivéve).
2. **Viselkedési**: `import picasapy.app.application` UTÁN a `cv2` NE
   legyen a `sys.modules`-ban — ez az, ami a felhasználónak számít.

A 2. önmagában is elég lenne, de a szerkezeti állítás **megnevezi a
bűnöst**: egy új `import cv2` sor azonnal látszik, nem csak az, hogy „a
mérés megint rossz".
"""

from __future__ import annotations

import ast
import os
import subprocess
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parents[1] / "src"
_CSOMAG = _SRC / "picasapy"

#: A homlokzat maga — ő IMPORTÁLHATJA a valódi cv2-t (lustán, függvényben).
_HOMLOKZAT = "picasapy/cv.py"


def _modul_szintu_cv2_importok() -> list[str]:
    """Azok a modulok, amelyek MODUL-SZINTEN importálják a `cv2`-t.

    A függvénytörzsben lévő `import cv2` rendben van: az csak híváskor
    fut le. (Az első AST-mérésem ezt összemosta — a `def` is modul-szintű
    csomópont —, és 33-at jelentett 7 helyett.)"""
    talalt: list[str] = []
    for ut in sorted(_CSOMAG.rglob("*.py")):
        relativ = str(ut.relative_to(_SRC))
        if relativ == _HOMLOKZAT:
            continue
        for csomopont in ast.parse(ut.read_text(encoding="utf-8")).body:
            if isinstance(csomopont, ast.Import) and any(
                alias.name == "cv2" for alias in csomopont.names
            ):
                talalt.append(f"{relativ}:{csomopont.lineno}")
            elif isinstance(csomopont, ast.ImportFrom) and (
                csomopont.module == "cv2"
            ):
                talalt.append(f"{relativ}:{csomopont.lineno}")
            elif isinstance(csomopont, ast.Try):
                # a régi `try: import cv2 / except ImportError` alak
                for al in ast.walk(csomopont):
                    if isinstance(al, ast.Import) and any(
                        a.name == "cv2" for a in al.names
                    ):
                        talalt.append(f"{relativ}:{al.lineno}")
    return talalt


def _alprocessz(kod: str) -> str:
    """A kód futtatása FRISS processzben, a mai forrással.

    A környezetet ÖRÖKÖLJÜK, és csak a szükségeset írjuk felül: csupasz
    env-vel a felhasználói `site-packages` sem látszana (a `watchdog` ott
    él), és a próba a rossz okra bukna."""
    eredmeny = subprocess.run(
        [sys.executable, "-c", kod],
        capture_output=True,
        text=True,
        env={
            **os.environ,
            "PYTHONPATH": str(_SRC),
            "QT_QPA_PLATFORM": "offscreen",
        },
        timeout=300,
        check=False,
    )
    assert eredmeny.returncode == 0, eredmeny.stderr[-800:]
    return eredmeny.stdout.strip()


class TestASzerkezet:
    def test_egyetlen_modul_sem_importalja_kozvetlenul(self):
        talalt = _modul_szintu_cv2_importok()
        assert talalt == [], (
            "ezek a modulok MODUL-SZINTEN importálják a cv2-t, tehát "
            f"behúzzák az induláskor: {talalt}. Használd a lusta "
            "homlokzatot: `from picasapy import cv as cv2` (#1611)."
        )

    def test_a_homlokzat_letezik_es_lusta(self):
        """Üres őr elleni próba: ha a homlokzat eltűnne, a fenti állítás
        üresen is teljesülne.

        ⚠️ KÜLÖN PROCESSZBEN. Az első változatom a futó folyamatban
        vizsgálta a `sys.modules`-t, és a TELJES készletben elbukott: egy
        korábbi teszt már betöltötte a cv2-t, tehát a próba nem a
        homlokzatot mérte, hanem a futási sorrendet. Ez ugyanaz a hiba,
        amit a jegy másoknál keres — a mérés önmagát igazolta volna."""
        kod = (
            "from picasapy import cv\n"
            "elotte = cv.betoltve()\n"
            "_ = cv.COLOR_BGR2RGB\n"
            "print(elotte, cv.betoltve())"
        )
        eredmeny = _alprocessz(kod)
        assert eredmeny == "False True", (
            f"a homlokzat nem lusta vagy nem továbbít: {eredmeny!r}"
        )


class TestAViselkedes:
    def test_az_alkalmazas_importja_NEM_tolti_be_a_cv2_t(self):
        """A felhasználónak ez számít. KÜLÖN processzben mérjük: ha a
        tesztkészlet máshol már betöltötte a cv2-t, a `sys.modules`
        vizsgálata itt hamis képet adna."""
        kod = (
            "import sys; import picasapy.app.application; "
            "print('cv2' in sys.modules)"
        )
        assert _alprocessz(kod) == "False", (
            "a cv2 betöltődött az alkalmazás importjakor — az indulás "
            "1,6 másodperccel hosszabb minden felhasználónál (#1611)"
        )
