"""#3279 — a felület-tesztek AZZAL a betűvel mérjenek, amit az app szállít.

## A lelet

A #656 túlcsordulás-őre a windows-lábon hét feliratot jelzett levágottnak,
és a magyarázat az volt, hogy „a windowsos rendszerbetű szélesebb". A
rendszerbetű viszont **nem a mi betűnk**: az app a csomagolt **Open
Sans**-t állítja be (#526, `application._install_ui_font`) — a QML-tesztek
fixture-je viszont ezt nem hívta meg, tehát a FUTTATÓ rendszerbetűjén
mért, gépenként máson.

⇒ A hét lelet olyan betűn született, amit a felhasználó soha nem lát.

## Amit ez a fájl őriz

Hogy a fixture tényleg beállítja az app betűjét. Enélkül minden
felirat-geometriát mérő őr némán a futtató gépének betűjét méri — és
mérve, ezen a gépen ez **megengedőbb** a valóságnál: a rendszer
alapértelmezése (Nunito Sans) minden érintett feliratnál keskenyebb az
Open Sansnál („Histogram and camera information" 182,6 → 196,8 képpont).

⚠️ Ez nem esztétikai kérdés: a doboz-méreteink a Picasa MÉRT
geometriájából jönnek, tehát a felirat-szélesség az egyetlen szabad
változó — és azt a betű dönti el.
"""

from __future__ import annotations

import picasapy.app.application as app_module
from PySide6.QtGui import QFontDatabase

#: A csomagolt család neve (`application._UI_FONT_FAMILY`).
CSALAD = "Open Sans"

class TestAFixtureBeallitja:
    def test_az_alkalmazas_betuje_a_csomagolt(self, qml_app, qt_app):
        """A `qml_app` fixture felállítása után az app betűje a miénk."""
        assert qt_app.font().family() == CSALAD

    def test_a_csalad_TENYLEG_betoltott(self, qml_app, qt_app):
        """Ellenpróba: a név önmagában kevés — a család legyen a
        betűtípus-adatbázisban is, különben a Qt némán helyettesít."""
        assert CSALAD in QFontDatabase.families()


#: ⛔ Ami SZÁNDÉKOSAN nincs itt: „a rendszerbetű MÁSKÉPP mér" próba.
#:
#: Az első változat a saját betűt egy üres családnevű (`setFamily("")`)
#: betűvel vetette össze, és azt várta, hogy a két szélesség különbözik.
#: A main windows-lába megbuktatta: ott az üres családnév ugyanazt adja
#: vissza, amit az alkalmazás betűje (`197.0 != 197.0`) — az „alapértelmezés"
#: platformonként mást jelent, tehát ez a kontroll a KÖRNYEZETET mérte, nem
#: a mi döntésünket.
#:
#: A „miért számít" bizonyíték a jegyen és a PR-ben áll, számokkal
#: (rendszerbetű ↔ Open Sans, hét feliratra). Egy próbának, ami
#: platformfüggő alapértelmezésre épül, nincs helye az őrök között.


class TestForras:
    def test_a_fixture_a_TERMEKKOD_fuggvenyet_hivja(self):
        """Ne másolat: ugyanaz a függvény állítsa be, mint éles indításkor
        — különben a kettő elsodródhat egymástól."""
        forras = (
            app_module._APP_DIR.parent.parent.parent
            / "tests" / "app" / "qml_functional" / "conftest.py"
        ).read_text(encoding="utf-8")

        assert "_install_ui_font" in forras
