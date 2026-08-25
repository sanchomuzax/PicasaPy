"""A fő ablak sávjai és a bal panel — KIRAJZOLVA, a valódi Main.qml-ben (#587).

## Honnan jönnek a számok

Nem képernyőkép-mintavételből: a Picasa **saját elrendezés-forrásfájljaiból**
(`respack.yt` → 140 `.tre`). A normatív lap
`docs/specs/konyvtar-ablak-meretek.md`, a levezetés
`docs/specs/picasa-fo-ablak-elrendezes.md`:

| forrás | konstans / elem | érték |
|---|---|---|
| `thumbui.tre` | `searchtop` | **35** — a felső sáv magassága |
| `thumbui.tre` | `HLISTOFFSET2` | **240** — a bal panel szélessége, FIX |
| `respack.yt` | `importbutton` | **111 × 22** |
| `respack.yt` | `searchcontainer` | **388 × 30** |

## Miért KIRAJZOLT

A komponenst izoláltan betöltő, property-t olvasó teszt nem látja a
szülő elrendezését: a felső sáv a `Main.qml` `header:`-e, a bal panel egy
`SplitView` gyereke — mindkettő a szülőtől kapja a végleges geometriáját.
Ez a fájl ezért a TELJES alkalmazást tölti be (`qml_app_module`), és több
ablakszélességen mér.

## Melyik állítás beégetett és melyik relatív — és miért

- **Beégetett** a három SÁV- és DOBOZMÉRET (35, 111 × 22, 388 × 30). Ezek
  a QML-ben literálként állnak, betűtől és platformtól függetlenek: a
  `Layout.preferredWidth`/`preferredHeight` nem a felirat méretéből
  származik. Beégetett szám itt tehát nem platformfüggő.
- **Relatív** minden, ami a FELIRAT szélességén múlik: hogy az
  „Importálás" gomb felirata elfér-e a 111 × 22-es dobozban, azt nem
  képpontban mérjük, hanem abból, hogy a `PicasaButton` `Text.Fit`-je
  NEM kényszerült zsugorításra (`font.pixelSize` a névleges maradt). Ez a
  csapda ma reggel élesben is elsült: a betűszélesség a fejlesztői gépen
  és az ubuntu-futón különbözik.
- **Relatív** a bal panel viselkedés-állítása is: nem azt mondjuk ki, hogy
  hány képpont, hanem hogy három különböző ablakszélességen UGYANANNYI —
  ez a forrás szerinti „nem skálázódik arányosan" invariáns.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

# a névleges felületi betűméret (`Theme.fontSize`) — a felirat-zsugorodás
# hiányát ehhez mérjük
_NEVLEGES_BETU = 12


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _szelesseg(window, qt_app, szelesseg: int) -> None:
    window.setProperty("width", szelesseg)
    qt_app.processEvents()


class TestFelsoSav:
    """A felső sáv magassága a `searchtop` = 35, minden ablakszélességen."""

    @pytest.mark.parametrize("ablak", [1280, 1600, 1920])
    def test_a_sav_35_kepont_magas(self, qml_app_module, qt_app, ablak):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, ablak)
        toolbar = _elem(window, "mainToolbar")
        assert toolbar.property("height") == 35, (
            f"a felső sáv {toolbar.property('height')} képpont "
            f"{ablak}px-es ablaknál — a `thumbui.tre` `searchtop`-ja 35"
        )
        # a sáv a teljes ablakszélességet átéri (nem tördelt, nem szűkített)
        assert toolbar.property("width") == window.property("width")


class TestFelsoSavElemei:
    """`importbutton` 111 × 22, `searchcontainer` 388 × 30."""

    def test_import_gomb_merete(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "toolbarImportButton")
        assert gomb.property("width") == 111
        assert gomb.property("height") == 22

    def test_import_gomb_felirata_zsugoritas_nelkul_elfer(
        self, qml_app_module, qt_app
    ):
        """RELATÍV: a felirat szélessége platformfüggő, ezért nem
        képpontot mérünk, hanem azt, hogy a `Text.Fit` nem lépett
        működésbe — a felirat a névleges betűmérettel maradt."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        gomb = _elem(window, "toolbarImportButton")
        felirat = gomb.property("contentItem")
        assert felirat is not None
        assert felirat.property("font").pixelSize() == _NEVLEGES_BETU, (
            "az Importálás felirata zsugorodni kényszerült a 111 × 22-es "
            "gombban — a doboz vagy a fordítás nem fér össze"
        )

    def test_kereso_teljes_merete_szeles_ablaknal(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 1920)
        kereso = _elem(window, "toolbarSearchBox")
        assert kereso.property("width") == 388
        assert kereso.property("height") == 30

    def test_kereso_padloja_szuk_ablaknal(self, qml_app_module, qt_app):
        """RELATÍV padló: szűk ablaknál a mező zsugorodhat (#423
        zsugorodási sorrend), de a 120px-es padló alá nem mehet, és a
        magassága nem változik."""
        window, _, _ = qml_app_module
        _szelesseg(window, qt_app, 760)
        kereso = _elem(window, "toolbarSearchBox")
        assert 120 <= kereso.property("width") <= 388
        assert kereso.property("height") == 30


class TestBalPanelNemSkalazodik:
    """A forrás szerint a bal panel FIX szélességű: az ablak növelésekor a
    rács nő, a panel marad. Ez az állítás RELATÍV (három mérés viszonya),
    nem képpontszám — épp ezért akkor is fog, ha a #587 integrátori
    lépése az alapértéket 240-re viszi."""

    def test_a_panel_szelessege_nem_koveti_az_ablakot(
        self, qml_app_module, qt_app
    ):
        window, _, _ = qml_app_module
        meresek = []
        for ablak in (1280, 1600, 1920):
            _szelesseg(window, qt_app, ablak)
            meresek.append(_elem(window, "folderPane").property("width"))
        assert len(set(meresek)) == 1, (
            f"a bal panel az ablakkal együtt változott: {meresek} — a "
            "forrás szerint FIX (`HLISTOFFSET2`, húzható elválasztóval)"
        )

    def test_a_panel_a_controller_erteket_veszi_fel(
        self, qml_app_module, qt_app
    ):
        window, controller, _ = qml_app_module
        _szelesseg(window, qt_app, 1280)
        panel = _elem(window, "folderPane")
        assert panel.property("width") == controller.folderPaneWidth


@pytest.mark.xfail(
    reason=(
        "#587 INTEGRÁTORI LÉPÉS: a `HLISTOFFSET2` = 240 alapérték a "
        "`FOLDER_PANE_WIDTH_DEFAULT`-ban (app/controller.py) és a "
        "`Main.qml` tartalék-értékében él — mindkét fájl tiltott volt "
        "ebben a körben. Ha a bekötés megtörtént, ez a teszt XPASS lesz: "
        "akkor a jelölőt le kell venni róla."
    ),
    strict=False,
)
def test_bal_panel_alapertelmezese_240(qml_app_module, qt_app):
    window, controller, _ = qml_app_module
    _szelesseg(window, qt_app, 1280)
    assert controller.folderPaneWidth == 240
    assert _elem(window, "folderPane").property("width") == 240
