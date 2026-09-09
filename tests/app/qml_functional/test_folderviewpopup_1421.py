"""#1421 — a `folderviewpopup` (▾) gomb az eszköztáron.

A #1421 „kihelyezés" csoportjának negyedik darabja (az `newalbum`, a
`timelinebutton` és a `flatview`/`folderview` pár után).

## A viselkedés MÉRVE, nem találgatva

A bináris kezelője (`0x005e2000`,
`docs/specs/picasa-konyvtar-eszkoztar-viselkedes.md` 4.) a **pár közös,
scope-kulcsos függvényét** hívja (`0x00575130`), a menü tételei pedig a
`Nézet ▸ Mappanézet` almenü tételei (spec 4/b, a menüépítő
`0x00559150` rekordtömbjéből feloldva).

⇒ A ▾ gomb **nem önálló beállítás-panel**, hanem ugyanaz a lenyíló menü.

## Ezért NEM készül új menü

A gomb a menüsor **meglévő** almenüjét nyitja meg
(`PicasaMenuBar.openFolderViewMenu`). Két menüdefiníció esetén a tételek
pipái szétcsúszhatnának a két belépési pont között — ez a #1454 mért
buktatójának (a `checked` imperatív átbillenése) a testvére lenne.

## Mért méret

22 × 22 (`konyvtar-ablak-meretek.md` 2.), a 60-as `hviewtoggle` csoport
mellett — a Row így 82 széles.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


class TestAGomb:
    def test_ott_van_a_par_MELLETT(self, qml_app, qt_app) -> None:
        window, _controller, _engine = qml_app
        gomb = _child(window, "toolbarFolderViewPopupButton")
        csoport = _child(window, "toolbarFolderViewToggle")
        assert gomb.property("visible") is True
        # ⚠️ A mérés szerint a ▾ ÖNÁLLÓ elem, nem a `hviewtoggle` 60 × 22-es
        # csoport része — a pár csoportja ezért marad 60 széles (a #1421
        # nézetváltó-próbája ezt a konstansot őrzi). A gomb a pár UTÁN áll.
        assert gomb.parentItem() is not csoport, (
            "a ▾ gomb a pár csoportjába került, és megnövelte annak mért "
            "szélességét (60 → 82)"
        )
        assert float(gomb.property("x")) >= float(csoport.property("x")), (
            "a ▾ gombnak a nézetváltó pár UTÁN kell állnia"
        )

    def test_a_MERT_meret(self, qml_app, qt_app) -> None:
        window, _controller, _engine = qml_app
        gomb = _child(window, "toolbarFolderViewPopupButton")
        assert (int(gomb.property("width")), int(gomb.property("height"))) == (22, 22)

    def test_a_par_csoportja_MARAD_60(self, qml_app, qt_app) -> None:
        """A `hviewtoggle` MÉRT szélessége 60 — a ▾ nem növelheti meg."""
        window, _controller, _engine = qml_app
        csoport = _child(window, "toolbarFolderViewToggle")
        assert int(csoport.property("width")) == 60, (
            f"a pár csoportja {csoport.property('width')} széles a mért 60 helyett"
        )


class TestAMenutNyitja:
    def test_a_kattintas_MEGNYITJA_a_Mappanezet_almenut(self, qml_app, qt_app) -> None:
        window, _controller, _engine = qml_app
        menu = _child(window, "menuViewFolderView")
        assert menu.property("visible") is False, "a menü alaphelyzetben zárt"

        gomb = _child(window, "toolbarFolderViewPopupButton")
        menusor = window.property("menuBar")
        assert menusor is not None, "nincs menüsor"
        menusor.openFolderViewMenu(gomb)
        qt_app.processEvents()

        assert menu.property("visible") is True, (
            "#1421: a ▾ gomb nem nyitotta meg a Mappanézet-almenüt"
        )
        menu.close()
        qt_app.processEvents()

    def test_NINCS_masodik_menudefinicio(self) -> None:
        """Egy definíció, két belépési pont: az eszköztár nem épít saját
        Mappanézet-menüt (különben a pipák szétcsúszhatnának)."""
        qml = (
            Path(__file__).resolve().parents[3]
            / "src/picasapy/app/qml/PicasaPy/MainToolbar.qml"
        ).read_text(encoding="utf-8")
        assert "menuViewFlatFolderView" not in qml, (
            "az eszköztár saját Mappanézet-tételeket definiál — a #1454 "
            "pipa-buktatójának testvére"
        )
        assert "folderViewMenuRequested" in qml, (
            "a gomb nem jelzésen át nyit menüt"
        )
