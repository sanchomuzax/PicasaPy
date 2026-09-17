"""A mért `normalcursor 1` vezérlők NEM váltanak kéz-kurzorra (#885).

## A mérés

A `.tre`-ben **16 elemen** áll `Property normalcursor 1`: ezek gombok, de a
nyíl-kurzor marad rajtuk (`docs/specs/picasa-eger-es-kijeloles.md` 7.
szakasz). A listából nálunk **három** elemnek van megfelelője:

| eredeti | nálunk |
|---|---|
| `headerpanel/create_collage` | `headerCollageButton` |
| `headerpanel/select_star` | `headerSelectStarredButton` |
| `thumbui/folderviewpopup` | `toolbarFolderViewPopupButton` |

A többi tizenhárom vezérlő nálunk **nem létezik** (webalbum-szinkron,
`throttle`, `bigslider`, importálás/megosztás paneljeinek gombjai) — ezekre
a #885 táblázata ⛔-t ad.

## Miért ŐR, ha már most helyes

A `PicasaButton` nem állít `cursorShape`-et, tehát a nyíl marad — a mérés
tehát MA teljesül. Az őr azt védi, hogy ne csússzon be: a
`Qt.PointingHandCursor` egy `HoverHandler`/`MouseArea` egyetlen sorával
kerül be, és a felületen sok helyen JOGOS (verzió-hivatkozás, értesítő
kártyák). A próba a HÁROM mért elemet nézi, nem a felületet általában.

## Amit NEM állít

A LÁTVÁNYT (hogy a rendszer valóban milyen kurzort rajzol) — csak azt, hogy
a jelenet egyetlen része sem KÉRI a kéz-kurzort ezeken a vezérlőkön.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtCore import Qt as QtCore_Qt
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

#: `Qt.PointingHandCursor` — a QML-ben ugyanez a szám (13). A PySide
#: felsorolás-tagja nem `int`-esíthető közvetlenül, a `.value` adja a számot.
KEZ_KURZOR = QtCore_Qt.CursorShape.PointingHandCursor.value

#: A mért `normalcursor 1` listából a nálunk LÉTEZŐ vezérlők. A két
#: fejléc-gomb csak album-fejléccel együtt áll elő, ezért a fejlécet — a
#: #1823 tesztjének bejáratott módján — külön példányosítjuk.
FEJLEC_ELEMEK = ("headerCollageButton", "headerSelectStarredButton")
TALCA_ELEMEK = ("toolbarFolderViewPopupButton",)

_ELETBEN = []


def _fejlec(engine):
    komponens = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml")
        ),
    )
    _ELETBEN.append(komponens)
    fejlec = komponens.createWithInitialProperties({"folderName": "Nyaralás"})
    assert komponens.errors() == [], komponens.errors()
    assert fejlec is not None
    _ELETBEN.append(fejlec)
    return fejlec


def _szam(ertek) -> int:
    """A `cursorShape` értéke jöhet `int`-ként és felsorolás-tagként is."""
    return int(getattr(ertek, "value", ertek))


def _kez_kurzort_kero(gyoker) -> list[str]:
    """A `gyoker` és minden leszármazottja, ami kéz-kurzort kér."""
    talalt = []
    for objektum in [gyoker, *gyoker.findChildren(QObject)]:
        meta = objektum.metaObject()
        if meta.indexOfProperty("cursorShape") < 0:
            continue
        ertek = objektum.property("cursorShape")
        if ertek is not None and _szam(ertek) == KEZ_KURZOR:
            talalt.append(
                f"{objektum.objectName() or meta.className()}"
            )
    return talalt


class TestANyilKurzorMarad:
    @pytest.mark.parametrize("nev", TALCA_ELEMEK)
    def test_a_talca_vezerloje_nem_ker_kez_kurzort(self, nev, qml_app, qt_app):
        window, _controller, _engine = qml_app
        qt_app.processEvents()
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"a(z) {nev} nincs a jelenetben"

        kerok = _kez_kurzort_kero(elem)
        assert kerok == [], (
            f"a(z) {nev} kéz-kurzort kér ({', '.join(kerok)}) — a mért "
            "`normalcursor 1` szerint a nyíl-kurzor marad"
        )

    @pytest.mark.parametrize("nev", FEJLEC_ELEMEK)
    def test_a_fejlec_gombja_nem_ker_kez_kurzort(self, nev, qml_app, qt_app):
        _window, _controller, engine = qml_app
        qt_app.processEvents()
        elem = _fejlec(engine).findChild(QObject, nev)
        assert elem is not None, f"a(z) {nev} nincs a fejlécen"

        kerok = _kez_kurzort_kero(elem)
        assert kerok == [], (
            f"a(z) {nev} kéz-kurzort kér ({', '.join(kerok)}) — a mért "
            "`normalcursor 1` szerint a nyíl-kurzor marad"
        )

    def test_a_probaan_van_foga(self, qml_app, qt_app):
        """Ellenpróba: a kéz-kurzort KÉRŐ elemet a próba észreveszi.

        A verzió-felirat jogosan kér kéz-kurzort (hivatkozás GitHubra) — ha
        a fenti keresés őt sem látja, akkor a próba vakon zöld."""
        window, _controller, _engine = qml_app
        qt_app.processEvents()
        verzio = window.findChild(QObject, "versionCursor")
        assert verzio is not None, "a verzió-felirat HoverHandlere hiányzik"
        assert _szam(verzio.property("cursorShape")) == KEZ_KURZOR
