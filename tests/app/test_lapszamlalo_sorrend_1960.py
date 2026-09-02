"""A lapszámláló sorrendje NYELVFÜGGŐ (#1960).

## A lelet

A magyar Picasa **felcseréli** a két számot: ahol az angol
`%1$d of %2$d`-t ír (aktuális / összes), ott a magyar `%2$d / %1$d`-t —
azaz **(összes / aktuális)**.

| forrás | angol | magyar |
|---|---|---|
| `ThumbUIPrint::PrintCount` (`stringres` 2287) | `%1$d of %2$d` | `%2$d / %1$d` |
| `il_BurnPanel::BackupCopy::1` (`stringres` 3023) | `Copying (%1$d/%2$d) files` | `Fájlok másolása (%2$d/%1$d)` |

Élesben: a tulajdonos felvételén az előnézet lapozója **`8 / 1`**,
miközben az **első** lapon állunk nyolcból; az ötképes mappa kék sávja a
**harmadik** képnél **`(5 / 3)`**.

## Amit ebből NEM szabad csinálni

Beégetni a magyar sorrendet. A sorrend a FORDÍTÁSÉ: a kódnak
pozíció-argumentumos, fordítható sablont kell átadnia, és a `.ts`-ben áll,
melyik nyelv melyik sorrendet kéri. Ezért ez a fájl **mindkét** oldalt
állítja: a sablon meglétét ÉS a magyar fordítás sorrendjét.
"""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest

_SRC = Path(__file__).resolve().parents[2] / "src" / "picasapy"
_I18N_DIR = _SRC / "app" / "i18n"

#: a néző kék infó-sávja
SAV_SABLON = "({current} / {total})"
#: a nyomtatás-előnézet lapozója
LAPOZO_SABLON = "%1 / %2"


def _forditas(kontextus: str, forras: str) -> str | None:
    gyoker = ET.parse(_I18N_DIR / "picasapy_hu.ts").getroot()
    for ctx in gyoker.iter("context"):
        nev = ctx.findtext("name")
        if nev != kontextus:
            continue
        for uzenet in ctx.iter("message"):
            if uzenet.findtext("source") == forras:
                return uzenet.findtext("translation")
    return None


class TestASablonokLETEZNEK:
    """Összefűzés helyett fordítható sablon — enélkül a sorrend beégne."""

    def test_a_kek_sav_sablont_hasznal(self):
        forras = (_SRC / "app" / "controller.py").read_text(encoding="utf-8")
        kod = "\n".join(
            sor for sor in forras.splitlines()
            if not sor.lstrip().startswith("#")
        )
        assert SAV_SABLON in kod, (
            "a kék sáv számlálója nem fordítható sablonból áll össze"
        )

    def test_a_lapozo_sablont_hasznal(self):
        forras = (
            _SRC / "app" / "qml" / "PicasaPy" / "PrintDialog.qml"
        ).read_text(encoding="utf-8")
        assert f'qsTr("{LAPOZO_SABLON}")' in forras, (
            "a nyomtatás-előnézet lapozója nem fordítható sablonból áll össze"
        )


class TestAMagyarSorrendFORDITOTT:
    def test_a_kek_sav_forditasa(self):
        forditas = _forditas("AppController", SAV_SABLON)
        assert forditas == "({total} / {current})", (
            f"a kék sáv magyar sablonja {forditas!r} — a mért eredeti "
            "(összes / aktuális) sorrendet kéri"
        )

    def test_a_lapozo_forditasa(self):
        forditas = _forditas("PrintDialog", LAPOZO_SABLON)
        assert forditas == "%2 / %1", (
            f"a lapozó magyar sablonja {forditas!r} — a mért eredeti "
            "(összes / aktuális) sorrendet kéri"
        )


class TestAzElotFordítvaLatja:
    """A lánc két vége külön-külön zöld lehet úgy is, hogy a felhasználó
    a rossz sorrendet látja — ezért TELEPÍTETT fordítóval mérünk."""

    @pytest.fixture
    def magyarul(self):
        from PySide6.QtCore import QCoreApplication, QTranslator

        app = QCoreApplication.instance() or QCoreApplication([])
        forditó = QTranslator()
        assert forditó.load("picasapy_hu", str(_I18N_DIR)), (
            "a picasapy_hu.qm nem tölthető be"
        )
        app.installTranslator(forditó)
        yield
        app.removeTranslator(forditó)

    def test_ot_kepbol_a_harmadik_5_per_3(self, magyarul):
        """A jegy szó szerinti esete: ötképes mappa, harmadik kép."""
        from picasapy.app.controller import AppController

        assert AppController.szamlalo_szoveg(3, 5) == "(5 / 3)"

    def test_angolul_a_megszokott_sorrend(self):
        from picasapy.app.controller import AppController

        assert AppController.szamlalo_szoveg(3, 5) == "(3 / 5)"
