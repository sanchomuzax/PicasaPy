"""#1620/#1622: a `Windows.old` felderítése VALÓDI Windows-fájlrendszeren.

A tulajdonos érve (a #1620 kommentje): a GitHub windows-futója nem csak
„valós képeket" ad, hanem **valós platform-viselkedést** — és a #1622
útvonalait itt, Linuxon semmivel nem tudjuk előállítani:

```
C:\\Windows.old\\Documents and Settings\\$$\\Local Settings\\Application Data\\Google\\
C:\\Windows.old\\Users\\$$\\AppData\\Local\\Google\\
```

A meglévő `tests/app/test_korabbi_telepites_1622.py` a `windows_old`
paraméteren át mindkét lábon végigmegy a szerkezeten — ami itt hiányzott, az
a **fájlrendszer saját viselkedése**: a visszaperes elválasztó és a
kis-nagybetű-érzéketlenség.

⚠️ **Ez a fájl a windows-lábon FUT, az ubuntun kihagy** — és ez itt nem a
#1560 hibája (ott egy windowsra kötött ág ubuntun ÜRESEN maradt zölden).
A szerkezeti állításokat a fenti, mindkét lábon futó fájl méri; ide csak az
kerül, aminek Linuxon nincs is értelme. Amit tehát az ubuntu-láb NEM mér:
a visszaperes bemenet és a kisbetűs mappanév.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from picasapy.scanner.discovery import discover_installations

csak_windowson = pytest.mark.skipif(
    os.name != "nt", reason="valódi Windows-fájlrendszer kell hozzá (#1620)"
)


def _telepites(gyoker: Path, sablon: str, felhasznalo: str = "sancho") -> Path:
    appdata = gyoker / sablon.format(felhasznalo=felhasznalo)
    (appdata / "Google" / "Picasa2" / "db3").mkdir(parents=True, exist_ok=True)
    (appdata / "Google" / "Picasa2Albums").mkdir(parents=True, exist_ok=True)
    return appdata


@csak_windowson
class TestValodiWindowsFajlrendszer:
    def test_VISSZAPERES_bemenetre_is_megtalalja(self, tmp_path):
        """A felületről és a beállításokból natív, visszaperes útvonal jön."""
        gyoker = tmp_path / "Windows.old"
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local")
        visszaperes = str(gyoker).replace("/", "\\")
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=visszaperes
        )
        assert len(talalat) == 1, f"nem találta meg: {visszaperes}"

    def test_a_KISBETUS_mappanevet_is_megtalalja(self, tmp_path):
        """A Windows fájlrendszere kis-nagybetű-érzéketlen: aki `windows.old`
        néven kapta meg a mappát, ugyanúgy meg kell, hogy találja."""
        gyoker = tmp_path / "Windows.old"
        _telepites(gyoker, "Users/{felhasznalo}/AppData/Local")
        talalat = discover_installations(
            home=tmp_path / "nincs-home", windows_old=tmp_path / "windows.old"
        )
        assert len(talalat) == 1, "kisbetűs néven nem találta meg"

    def test_a_MEGHAJTOBETUS_gyoker_nem_szall_el(self, tmp_path):
        """A `C:/Windows.old` alapértelmezés akkor is legyen ártalmatlan, ha
        a gépen nincs ilyen mappa — ez az alapeset minden windowsos gépen."""
        talalat = discover_installations(home=tmp_path / "nincs-home")
        assert isinstance(talalat, tuple)
