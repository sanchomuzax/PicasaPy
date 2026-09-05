"""#2142 — a duplikátum-kereső a Kísérleti almenübe való.

## A mérés (#1794, az Eszközök menü teljes szerkezete)

Az eredetiben a duplikátum-kereső **nem a felső szinten** áll, hanem a
**Kísérleti** almenü **második** helyén:

| kulcs | angol | magyar |
|---|---|---|
| `eMenuTools::ID_DUPES` | `Show Duplicate Files` | Fájlok másodpéldányainak megjelenítése |
| `eMenuTools::ID_MOVE_DATABASE` | `Choose database location...` | Adatbázis helyének kiválasztása... |

A mi „Move Database…" tételünk tehát **rossz feliratot** viselt, és a
Kísérleti almenü **8.** helyén áll az eredetiben.

## ⚠️ Az arckereső TUDATOS eltérés

A „Find Faces" felirat a **teljes szövegtárban nem szerepel** — az
eredetinek nincs ilyen menüparancsa. Mi a #1473 miatt tartjuk meg (a
duplikátum-keresővel azonos fajta munka: az egész könyvtárat végigolvasó,
megszakítható keresés saját ablakkal). Ez nem hiba, hanem döntés — a
kódban is ki van mondva.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app as app_csomag

_QML = (
    Path(app_csomag.__file__).parent / "qml" / "PicasaPy" / "PicasaMenuBar.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(app_csomag.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")


def _kiserleti_blokk() -> str:
    """A Kísérleti almenü teljes blokkja, kapcsos zárójel szerint vágva."""
    jel = 'title: qsTr("Experimental")'
    assert jel in _QML, "nincs Kísérleti almenü"
    kezd = _QML.rindex("PicasaMenu {", 0, _QML.index(jel))
    melyseg = 0
    for i in range(_QML.index("{", kezd), len(_QML)):
        if _QML[i] == "{":
            melyseg += 1
        elif _QML[i] == "}":
            melyseg -= 1
            if melyseg == 0:
                return _QML[kezd : i + 1]
    raise AssertionError("nem záródik a Kísérleti blokk")


class TestADuplikatumKereso:
    def test_a_KISERLETI_almenuben_van(self):
        assert 'objectName: "menuToolsDedup"' in _kiserleti_blokk(), (
            "a duplikátum-kereső még mindig a felső szinten áll — az "
            "eredetiben a Kísérleti almenü 2. tétele"
        )

    def test_a_MERT_feliratot_viseli(self):
        blokk = _kiserleti_blokk()
        kezd = blokk.index('objectName: "menuToolsDedup"')
        assert 'qsTr("Show Duplicate Files")' in blokk[kezd : kezd + 300], (
            "nem a mért felirat (`eMenuTools::ID_DUPES`)"
        )

    def test_a_MASODIK_helyen_all(self):
        blokk = _kiserleti_blokk()
        nevek = re.findall(r'objectName: "(menuTools\w+)"', blokk)
        assert len(nevek) >= 2 and nevek[1] == "menuToolsDedup", (
            f"a Kísérleti almenü sorrendje {nevek} — a duplikátum-kereső a "
            f"2. helyen áll az eredetiben"
        )

    def test_a_MAGYAR_alak_az_eredetie(self):
        assert "<source>Show Duplicate Files</source>" in _TS
        assert (
            "<translation>Fájlok másodpéldányainak megjelenítése</translation>"
            in _TS
        )


class TestAzAdatbazisHelye:
    def test_a_MERT_feliratot_viseli(self):
        blokk = _kiserleti_blokk()
        kezd = blokk.index('objectName: "menuToolsMoveDatabase"')
        assert 'qsTr("Choose database location...")' in blokk[kezd : kezd + 300], (
            "a felirat még mindig `Move Database...` — az eredetié "
            "`Choose database location...`"
        )

    def test_a_MAGYAR_alak_az_eredetie(self):
        assert "<source>Choose database location...</source>" in _TS
        assert (
            "<translation>Adatbázis helyének kiválasztása…</translation>" in _TS
        )


class TestAzArckeresoTUDATOSelteres:
    def test_a_felso_szinten_MARAD(self):
        """A #1473 döntése — nem hiba, hanem eltérés."""
        assert 'objectName: "menuToolsFaceScan"' in _QML
        assert 'objectName: "menuToolsFaceScan"' not in _kiserleti_blokk()

    def test_az_elteres_KI_VAN_MONDVA_a_kodban(self):
        kezd = _QML.index('objectName: "menuToolsFaceScan"')
        kornyek = _QML[max(0, kezd - 1600) : kezd]
        assert "#2142" in kornyek, (
            "az arckereső mellett nincs ott a #2142 leírása: az eredetiben "
            "NINCS ilyen menüparancs, ez tudatos eltérés"
        )
