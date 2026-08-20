"""A csempe képének URL-je a MODELLBŐL jön, nem kézi fűzésből (#1019).

## A lelet

A #1009 kiderítette, hogy a kézzel fűzött fájl-URL **Windowson érvénytelen
URL-t ad**: a meghajtóbetű PORTNAK látszik, a `QUrl` üresre normalizál, és
a QML `Image.source` **némán soha nem rajzol ki képet**.

```
QUrl("file://" + "C:\\Users\\...\\a.jpg")
  isValid() = False   host = 'c'   hiba: "Invalid port or port number out of range"
```

A `"file:"` (egy kettőspont) alak Windowson véletlenül érvényes marad —
**de `#`-et tartalmazó fájlnévnél platformtól függetlenül elvágja a nevet**,
mert az URL-ben a `#` töredékjel.

Két hely maradt kézi fűzéssel: a vászon csempéje (`CollageNode.qml`) és a
Klipek lap miniatűrje (`CollageClipsTab.qml`). Mindkettő a
`CollageNodeModel`-ből olvas, ezért egy MODELL-SZEREP mindkettőt megoldja
— és a szabályt nem a felület találja ki platformonként.

⚠️ Ez a hibaosztály **néma**: nincs hibaüzenet, nincs kivétel, csak egy
üres kép. Ezért kell rá teszt, és nem elég „ránézni".
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QUrl

from picasapy.app.collage_model import CollageNode, CollageNodeModel


def _modell(*utak: str) -> CollageNodeModel:
    modell = CollageNodeModel()
    modell.set_nodes(
        [
            CollageNode(
                path=ut,
                center_x=512.0,
                center_y=384.0,
                width=200.0,
                height=200.0,
                theta=0.0,
            )
            for ut in utak
        ]
    )
    return modell


def _url(modell: CollageNodeModel, sor: int):
    index = modell.index(sor, 0)
    return modell.data(index, CollageNodeModel.FileUrlRole)


def _azonos_ut(a: str, b: str) -> bool:
    """Útvonal-egyezés NORMALIZÁLVA.

    ⚠️ Windowson a `QUrl.toLocalFile()` ELŐRE dőlő perjelet ad
    (`C:/Users/...`), a `Path`-ból épített szöveg viszont hátra dőlőt
    (`C:\\Users\\...`). A nyers egyenlőség ezért a windows-lábon
    elbukik — a `models.py::rowOfPath` ugyanezt a csapdát már
    dokumentálja, csak ez a teszt nem vette át."""
    return os.path.normcase(os.path.normpath(a)) == os.path.normcase(
        os.path.normpath(b)
    )


class TestASzerepLetezik:
    def test_a_szerep_neve_fileUrl(self):
        nevek = {
            bytes(nev).decode() for nev in CollageNodeModel().roleNames().values()
        }

        assert "fileUrl" in nevek


class TestAzUrlHelyes:
    """A `QUrl.fromLocalFile` szabályát nem mi találjuk ki platformonként."""

    def test_egyszeru_utvonalra_a_Qt_alakjat_adja(self, tmp_path):
        ut = str(tmp_path / "a.jpg")

        assert _url(_modell(ut), 0) == QUrl.fromLocalFile(ut)

    def test_KETTOSKERESZTES_fajlnevre_sem_vag_le(self, tmp_path):
        """⚠️ Ez a kézi fűzés néma bukása LINUXON is: a `#` töredékjel."""
        ut = str(tmp_path / "kép #1.jpg")

        url = _url(_modell(ut), 0)

        assert _azonos_ut(url.toLocalFile(), ut)
        assert url.toLocalFile().endswith("#1.jpg")

    def test_ekezetes_szokozos_mappara_is_jo(self, tmp_path):
        mappa = tmp_path / "Nyaralás 2026"
        mappa.mkdir()
        ut = str(mappa / "árvíztűrő.jpg")

        assert _azonos_ut(_url(_modell(ut), 0).toLocalFile(), ut)

    def test_a_kezi_fuzes_ELBUKNA_ugyanezen(self, tmp_path):
        """A jegy bizonyítéka, tesztként: a régi alak elvágja a nevet.

        Ha ez az állítás egyszer megfordul (a Qt máshogy kezeli a `#`-et),
        akkor a jegy indoklása is elavult — ezért áll itt, és nem csak a
        docstringben."""
        ut = str(tmp_path / "kép #1.jpg")

        kezi = QUrl("file:" + ut)

        assert not _azonos_ut(kezi.toLocalFile(), ut)

    def test_ures_utvonalra_ures_URL(self):
        assert _url(_modell(""), 0) == QUrl()


class TestNincsTobbKeziFuzes:
    """A jegy harmadik pontja: nézzük végig, maradt-e MÁS kézi fűzés."""

    @pytest.mark.parametrize("fajl", ["CollageNode.qml", "CollageClipsTab.qml"])
    def test_a_ket_javitott_helyen_nincs_kezi_url(self, fajl):
        import picasapy.app

        forras = (
            Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / fajl
        ).read_text(encoding="utf-8")
        kodsorok = [
            sor
            for sor in forras.splitlines()
            if not sor.lstrip().startswith(("//", "/*", "*"))
        ]

        assert not [sor for sor in kodsorok if '"file:' in sor]

    def test_a_teljes_QML_faban_sincs_kezi_url(self):
        """Olcsó keresés, néma hibaosztály — a jegy külön kéri."""
        import picasapy.app

        gyoker = Path(picasapy.app.__file__).parent / "qml"
        talalatok = []
        for ut in gyoker.rglob("*.qml"):
            for szam, sor in enumerate(
                ut.read_text(encoding="utf-8").splitlines(), start=1
            ):
                if sor.lstrip().startswith(("//", "/*", "*")):
                    continue
                if '"file:' in sor:
                    talalatok.append(f"{ut.name}:{szam}")

        assert not talalatok, "kézi fájl-URL maradt: " + ", ".join(talalatok)
