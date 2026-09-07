"""#1486 — az arcfelismerés-kizárás szabálya KÉT helyen él; ne csússzon szét.

## A lelet (a #1476 gépi őre mérte)

A `controller.faceDetectionEnabledFor` bekötetlen: a QML a saját,
párhuzamos tükrét számolja (`FolderManagerDialog.qml` `facesExcludedFor`).
Két megvalósítás ugyanarra a szabályra.

## MIÉRT MARAD KÉT HELYEN — mérve, nem kényelemből

A jegy két utat kínált: a felület hívja a vezérlőt, VAGY a másolásnak
legyen kimondott oka és őre. A vezérlő hívása **mérhetően drága**:

* `scanner/exclude.py::is_excluded` minden hívásnál `Path(...).resolve()`-t
  futtat — a vizsgált útvonalra ÉS minden kizárt gyökérre. Ez
  fájlrendszer-művelet;
* a mappafa jelvénye **soronként** hívja, minden újrarajzoláskor, tehát
  `sorok × gyökerek` `resolve()` egyetlen görgetésre;
* a tulajdonos gyűjteménye **hálózati megosztáson** él (`/mnt/photo`), ahol
  ez a memórialap szerint tiltott mintázat („NAS: diagnosztika se járja
  be").

⇒ A QML-oldali, tisztán szöveges előtag-egyezés marad. **De nem csúszhat
szét a Pythonétól**, és pontosan ezt méri ez a fájl: a QML függvény
**forrásszövegét** kiveszi a `.qml`-ből, `QJSEngine`-nel lefuttatja, és
egy korpuszon összeveti a Python szabállyal.

## Amit a két szabály SZÁNDÉKOSAN másképp csinál

A QML ismeri a **még el nem mentett** (`pendingFaces`) változtatásokat is —
a Python nem tudhat róluk. Az összevetés ezért `pendingFaces = {}` mellett
történik: üres függőben lévő halmazzal a kettőnek EGYEZNIE kell.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtQml import QJSEngine

from picasapy.scanner.exclude import is_excluded
from tests.support.qml_blokk import blokk_horgony_utan

_QML = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "FolderManagerDialog.qml"
).read_text(encoding="utf-8")

#: A korpusz: (vizsgált útvonal, kizárt gyökerek). Minden eset OK-kal.
KORPUSZ: tuple[tuple[str, tuple[str, ...], str], ...] = (
    ("/a/b", (), "nincs kizárás"),
    ("/a/b", ("/a/b",), "maga a gyökér"),
    ("/a/b/c", ("/a/b",), "alfa"),
    ("/a/bc", ("/a/b",), "TESTVÉR, nem alfa — a puszta előtag csapdája"),
    ("/a", ("/a/b",), "az ŐS nincs kizárva"),
    ("/x/y", ("/a/b", "/x",), "több gyökér, a másodikra illeszkedik"),
    ("/a/b/c/d/e", ("/a/b",), "mély alfa"),
    ("", ("/a/b",), "üres útvonal"),
)


def _js_szabaly(motor: QJSEngine) -> object:
    """A QML `facesExcludedFor` FORRÁSSZÖVEGE, futtathatóan.

    Nem másolat: a `.qml`-ből vesszük ki minden futáskor. Ha valaki
    átírja a QML szabályt, ez a próba a MEGVÁLTOZOTT szabályt méri.
    """
    keret = """
    (function (path, roots) {
      var controller = { faceExcludedFolders: roots };
      var folderManagerWindow = { pendingFaces: {} };
      function _isAtOrBelow(path, root) %s
      function facesExcludedFor(path) %s
      return facesExcludedFor(path);
    })
    """ % (
        blokk_horgony_utan(_QML, "function _isAtOrBelow(path, root)"),
        blokk_horgony_utan(_QML, "function facesExcludedFor(path)"),
    )
    fuggveny = motor.evaluate(keret)
    assert not fuggveny.isError(), fuggveny.toString()
    return fuggveny


class TestAKetSzabalyEGYEZIK:
    @pytest.mark.parametrize(
        ("ut", "gyokerek", "eset"), KORPUSZ, ids=[e[2] for e in KORPUSZ]
    )
    def test_ugyanazt_mondja(self, qt_app, ut, gyokerek, eset):
        """⚠️ A `qt_app` KELL: a `QJSEngine` `QCoreApplication` nélkül
        SIGSEGV-vel áll meg (mérve 2026-09-07)."""
        del qt_app
        motor = QJSEngine()
        fuggveny = _js_szabaly(motor)
        qml_kizart = fuggveny.call(
            [motor.toScriptValue(ut), motor.toScriptValue(list(gyokerek))]
        ).toBool()
        python_kizart = bool(ut) and is_excluded(ut, gyokerek)
        assert qml_kizart == python_kizart, (
            f"{eset}: a QML szerint {qml_kizart}, a Python szerint "
            f"{python_kizart} — a két szabály szétcsúszott (#1486). "
            f"út={ut!r} gyökerek={gyokerek!r}"
        )

    def test_a_korpusz_MINDKET_valaszt_tartalmazza(self):
        """Egy csupa-`False` korpuszon bármelyik hibás szabály átmenne."""
        valaszok = {
            bool(ut) and is_excluded(ut, gy) for ut, gy, _ in KORPUSZ
        }
        assert valaszok == {True, False}


class TestAKivonasMAGA_is_mukodik:
    """Ha a QML függvény neve vagy alakja változik, ez bukjon — ne az
    legyen, hogy az őr némán üres szabályt futtat."""

    def test_a_ket_fuggveny_kivehato(self):
        assert "indexOf" in blokk_horgony_utan(
            _QML, "function _isAtOrBelow(path, root)"
        )
        assert "faceExcludedFolders" in blokk_horgony_utan(
            _QML, "function facesExcludedFor(path)"
        )

    def test_a_python_oldal_a_KOZOS_fuggvenyt_hasznalja(self):
        """A vezérlő ne írja újra a szabályt — a `scanner/exclude.py` az
        igazságforrás."""
        vezerlo = (
            Path(picasapy.app.__file__).parent / "library_controller.py"
        ).read_text(encoding="utf-8")
        assert "is_excluded(" in vezerlo


class TestAMASOLAS_INDOKA_ki_van_mondva:
    """A jegy kikötése: ha a másolás marad, a kód NEVEZZE MEG az okot."""

    def test_a_qml_kimondja_miert_nem_a_vezerlot_hivja(self):
        blokk = blokk_horgony_utan(_QML, "function facesExcludedFor(path)")
        # a kommentek a függvény FÖLÖTT állnak, ezért a teljes forrásban nézzük
        hely = _QML.index("function facesExcludedFor(path)")
        elotte = _QML[max(0, hely - 1200):hely]
        assert "#1486" in elotte, (
            "a QML-ben nincs kimondva, miért él itt külön szabály (#1486)"
        )
        assert "resolve" in elotte or "fájlrendszer" in elotte, (
            "az indoklás nem nevezi meg a valódi okot (a Python szabály "
            "fájlrendszert érint)"
        )
        del blokk
