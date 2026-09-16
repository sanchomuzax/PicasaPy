"""#3247 — a szerkesztő-fülek lapja BELEFÉR a mért 277 képpontba.

## A mért szám

Az eredeti Picasa szerkesztő-paneljének fül-lapja (`editpanel/tabpanel1`)
**273 × 277** képpont (`docs/specs/ui-audit-editor.md`, a `respack.yt`-ből
képpontról képpontra mérve).

## Miért ez a panel EGÉSZÉNEK kérdése

A panel magasság-igénye (`implicitHeight`) a `chromeHeight` + a fül lapjának
MÉRT magassága (`mertTabPanelHeight` = 277). Ez a #3247 második lépése: eddig a
LEGMAGASABB fülünk tartalma adta a számot, tehát egyetlen túl magas fül az
EGÉSZ panelt megnövelte, és a néző ezt kapta alsó korlátként.

Mérve 2026-09-16-án: a legmagasabb fül a **saját, az eredetiben nem létező**
„örökölt szűrők" füle volt (#571), **298** képponttal — a mért 277 helyett. A
többi fül belefér (a legmagasabb eredeti-megfelelő a Finomhangolás, 272).

## Amit ez az őr állít

- **egyetlen** fül `implicitHeight`-je sem lépi túl a mért 277-et;
- a panel `implicitHeight`-je ennek megfelelően a króm + legfeljebb 277.

## Amit NEM állít

A LÁTVÁNYT: hogy a 277 képponton belül a fülek tartalma hova kerül. A
vágás-logika változatlanul a LÁTHATÓ fülből dolgozik (`tabContentHeight`), tehát
ha egy fül mégis túlnő, a `tabContentTruncated` jelzi — nem némán vágódik le.
"""

from __future__ import annotations

from PySide6.QtCore import QObject

#: `editpanel/tabpanel1` — a fül lapjának MÉRT magassága.
MERT_LAP_MAGASSAG = 277

#: A hét fül gyökérelemének objectName-je.
FULEK = (
    "toolsColumn",
    "finetuneColumn",
    "effectsColumn",
    "effectsColumn2",
    "effectsColumn3",
    "effectsColumn4",
    "legacyEffectsColumn",
)


def _fulek(window) -> dict[str, float]:
    ki: dict[str, float] = {}
    for nev in FULEK:
        elem = window.findChild(QObject, nev)
        assert elem is not None, f"a(z) {nev} fül nincs a jelenetben"
        ki[nev] = float(elem.property("implicitHeight") or 0.0)
    return ki


class TestAFulekBelefernek:
    def test_egyetlen_ful_sem_lepi_tul_a_mert_277_et(self, qml_app, qt_app):
        window = qml_app[0]
        qt_app.processEvents()
        tulsok = {
            nev: h for nev, h in _fulek(window).items() if h > MERT_LAP_MAGASSAG
        }
        assert not tulsok, (
            "a mért `editpanel/tabpanel1` = 277 képpontot túllépő fül(ek): "
            + " · ".join(f"{n} = {h:.0f}" for n, h in sorted(tulsok.items()))
            + " — egyetlen ilyen fül az EGÉSZ panelt megnöveli (#703)"
        )

    def test_a_panel_igenye_a_krom_plusz_a_MERT_lap(self, qml_app, qt_app):
        """A panel magassága a KRÓM + a MÉRT 277 — nem a mi tartalmunk maximuma.

        Így a #703 szerződése („ne ugráljon") erősebben teljesül, a paritás is
        javul, és a fülek halaszthatóvá válnak (#3244).
        """
        window = qml_app[0]
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        assert float(panel.property("mertTabPanelHeight")) == MERT_LAP_MAGASSAG
        krom = float(panel.property("chromeHeight"))
        assert float(panel.property("implicitHeight")) == krom + MERT_LAP_MAGASSAG

    def test_a_magassag_nem_a_fulek_maximumabol_jon(self, qml_app, qt_app):
        """Mutáció-próba: ha valaki visszaírja a fülek maximumát, ez bukik.

        A legmagasabb fülünk 274, a mért lap 277 — a kettő KÜLÖNBÖZIK, tehát
        a próba tényleg a mért számot állítja, nem véletlen egyezést.
        """
        window = qml_app[0]
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        legmagasabb = max(_fulek(window).values())
        assert legmagasabb < MERT_LAP_MAGASSAG, (
            f"a legmagasabb fül {legmagasabb} — a mért 277-cel egyezve a "
            "fenti próba nem tudná megkülönböztetni a két modellt"
        )
        assert float(panel.property("implicitHeight")) != (
            float(panel.property("chromeHeight")) + legmagasabb
        )

    def test_a_ful_magassaga_fulvaltaskor_nem_valtozik(self, qml_app, qt_app):
        """A #703 lényege: a panel magassága nem ugrál a fülek között."""
        window = qml_app[0]
        panel = window.findChild(QObject, "viewerEditorPanel")
        elotte = float(panel.property("implicitHeight"))
        for lap in range(7):
            panel.setProperty("activeTab", lap)
            qt_app.processEvents()
            assert float(panel.property("implicitHeight")) == elotte, (
                f"a panel magassága a {lap}. fülön {panel.property('implicitHeight')}, "
                f"a kezdeti {elotte} helyett"
            )


class TestAzOrokoltFulSzovege:
    """A rövidítés nem veszítheti el a KÉT állítást, amit a #571 kért."""

    def test_a_bevezeto_ket_allitast_mond(self):
        import picasapy.app.application as app_module

        forras = (
            app_module._APP_DIR / "qml" / "PicasaPy" / "EditorLegacyTab.qml"
        ).read_text(encoding="utf-8")
        kezd = forras.index('objectName: "legacyEffectsIntro"')
        blokk = forras[kezd : kezd + 600]
        assert "older Picasa versions" in blokk, "eltűnt: HONNAN jönnek"
        assert "only recognises them" in blokk, "eltűnt: a mai Picasa csak FELISMERI"
