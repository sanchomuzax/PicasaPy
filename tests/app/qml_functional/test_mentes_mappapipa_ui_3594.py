"""#3594/#3681 — a mentés 2. lépésének SZÖVEGEI a kiadás-panelen.

Az eredeti mentés-üzemmód 2. lépése (`backuprect2`, `biztonsagi-mentes.md`
10.3):

```
Mappák és albumok kijelölése biztonsági másolat készítéséhez
A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban nem
készült biztonsági másolat.
Jelölje ki azokat a mappákat, … vagy »Az összes kijelölése« …
[Az összes kijelölése] [Az összes kijelölés megszüntetése]
```

⚠️ #3681: a mappánkénti PIPÁS LISTA — korábban a panel fölötti
`BackupFolderStrip` sávban — a KÖNYVTÁRBA (`FolderPane`/
`FolderHierarchyView`, `mentesSzuroAktiv` szerződés) költözött, az eredeti
Picasa `backuptext2`/`backuptext3` viselkedését követve. Az ottani
kattintásos tesztek: `test_mentes_konyvtar_szuro_3681.py`. A mentés-
üzemmód BACKEND-logikája (mappánkénti mentetlen-lista, terv, futtatás)
változatlan — azt a `test_mentes_mappak_vezerlo_3594.py` méri, nem ez a
fájl. Ez a fájl csak a PANEL (`PublishPanel.qml`) mért szövegeit nézi.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml"
_PANEL = (_QML / "PicasaPy" / "PublishPanel.qml").read_text(encoding="utf-8")


class TestAMertSzovegek:
    @pytest.mark.parametrize("szoveg", [
        "Choose folders & albums to back up",
        "Picasa is now showing the files you have not previously backed up.",
        "Check the folders you want to back up, or choose 'Select All' to "
        "choose everything.",
        "Select All",
        "Select None",
    ])
    def test_a_mert_felirat_ott_van(self, szoveg):
        assert szoveg in _PANEL, szoveg


class TestAMagyarFelirat:
    @pytest.mark.parametrize("forras, magyar", [
        ("Choose folders & albums to back up",
         "Mappák és albumok kijelölése biztonsági másolat készítéséhez"),
        ("Picasa is now showing the files you have not previously backed up.",
         "A Picasa most azokat a fájlokat jeleníti meg, amelyekről korábban "
         "nem készült biztonsági másolat."),
        ("Select All", "Az összes kijelölése"),
        ("Select None", "Az összes kijelölés megszüntetése"),
    ])
    def test_a_hivatalos_magyar_a_qm_bol_jon(self, qt_app, forras, magyar):
        from PySide6.QtCore import QTranslator

        fordito = QTranslator()
        assert fordito.load("picasapy_hu", str(_QML.parent / "i18n"))
        assert fordito.translate("PublishPanel", forras) == magyar
