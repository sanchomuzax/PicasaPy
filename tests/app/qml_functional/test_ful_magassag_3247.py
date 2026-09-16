"""#3247 — a szerkesztő-fülek lapja BELEFÉR a mért 277 képpontba.

## A mért szám

Az eredeti Picasa szerkesztő-paneljének fül-lapja (`editpanel/tabpanel1`)
**273 × 277** képpont (`docs/specs/ui-audit-editor.md`, a `respack.yt`-ből
képpontról képpontra mérve).

## Miért ez a panel EGÉSZÉNEK kérdése

A panel magasság-igénye (`implicitHeight`) a `chromeHeight` + a LEGMAGASABB fül
(`tallestTabHeight`) — szándékosan nem az aktív fülé, hogy a panel fülváltáskor
ne ugráljon (#703). Egyetlen túl magas fül tehát az EGÉSZ panelt megnöveli, és
a néző ezt kapja alsó korlátként.

Mérve 2026-09-16-án: a legmagasabb fül a **saját, az eredetiben nem létező**
„örökölt szűrők" füle volt (#571), **298** képponttal — a mért 277 helyett. A
többi fül belefér (a legmagasabb eredeti-megfelelő a Finomhangolás, 272).

## Amit ez az őr állít

- **egyetlen** fül `implicitHeight`-je sem lépi túl a mért 277-et;
- a panel `implicitHeight`-je ennek megfelelően a króm + legfeljebb 277.

## Amit NEM állít

Hogy a panel magassága PONTOSAN a mért 277-tel egyezik. Ahhoz a
`tallestTabHeight` helyére a mért állandó kellene, az viszont a vágás-logikát
is érinti (`tabContentTruncated`, a #703 stub-őre a valódi legmagasabb fület
méri) — külön szelet, a jegyen megnevezve.
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

    def test_a_panel_igenye_a_krom_plusz_a_legmagasabb_ful(self, qml_app, qt_app):
        """A #703 szerződése él tovább: a panel a KRÓM + a legmagasabb fül."""
        window = qml_app[0]
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        krom = float(panel.property("chromeHeight"))
        legmagasabb = float(panel.property("tallestTabHeight"))
        assert legmagasabb == max(_fulek(window).values())
        assert float(panel.property("implicitHeight")) == krom + legmagasabb
        assert legmagasabb <= MERT_LAP_MAGASSAG

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
