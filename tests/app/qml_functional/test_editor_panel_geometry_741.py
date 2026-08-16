"""A szerkesztő bal paneljének MÉRT geometriája — #741.

Miért ez a fájl létezik: a `docs/specs/szerkeszto-panel-meretek.md` normatív
lapja a Picasa saját erőforráscsomagjából (`respack.yt` rétegtéglalapjai)
adja meg a panel minden méretét. Ezek nem képernyőkép-becslések, tehát
állíthatók — de csak a KIRAJZOLT fán: a `GridLayout`/`RowLayout` gyerekeinek
tényleges méretét egyetlen property sem mondja meg előre.

A mérés a `test_editor_panel_rendered_651.py` mintáját követi: valódi
`QQuickView`, a VIZUÁLIS fa bejárása (a layout-gyerekeket a `findChild` nem
mindig találja meg), és a geometria a PANEL koordinátarendszerében.

Mit állítunk és mit nem — a spec 0. szakasza szerint:

* **méret, osztásköz, hézag, egymáshoz képesti eltolás**: KÖTELEZŐ, itt
  állítjuk;
* **abszolút `y` a panel tetejétől**: tervezővászon-érték, NEM állítjuk.

Az egyetlen tudatos eltérés az eredetitől a fülek SZÁMA (hét öt helyett, a
tulajdonos döntése: `docs/decisions/szerkeszto-bal-panel.md`); a fülsáv
magassága és a hézagmentes kitöltés erre is érvényes.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

_KEEPALIVE: list[object] = []

#: A panel névleges szélessége (`respack.yt`: a képnézet x = 280-nál kezdődik).
PANEL_SZELESSEG = 280
#: A tartalom-oszlop (`editcontrols`/`edittabbase`/`fxthumbs`), x 3..279.
TARTALOM_SZELESSEG = 276
#: A hét fül szélessége — `276 / 7` egészre osztva, a maradék hátulról
#: elosztva (spec 2. szakasz).
FUL_SZELESSEGEK = (39, 39, 40, 39, 40, 39, 40)

FULEK = (
    "editTabFixes", "editTabFinetune", "editTabEffects", "editTabEffects2",
    "editTabEffects3", "editTabEffects4", "editTabLegacy",
)

#: Az 1. fül nyolc eszközcsempéje, sorfolytonosan (spec 3. szakasz).
CSEMPEK = (
    "editToolCrop", "editToolTilt", "editToolRedeye",
    "editToolEnhance", "editToolAutolight", "editToolAutocolor",
    "editToolRetouch", "editToolText",
)


class _EditControllerStub(QObject):
    """Bélyegképes csempék — enélkül az effekt-rács hamisan alacsony."""

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []

    @Property("QVariant", constant=True)
    def effectChainCounts(self):
        return {}


_PANEL_QML = """
import QtQuick
import PicasaPy 1.0
Item {{
    objectName: "gyoker"
    EditorPanel {{
        objectName: "panel"
        anchors.left: parent.left
        anchors.top: parent.top
        anchors.bottom: parent.bottom
        width: {szelesseg}
        activeTab: {tab}
    }}
}}
"""


def _render(qt_app, tab: int = 0, *, mod: str | None = None) -> QQuickItem:
    """A panel valódi ablakban, `mod` = a bekapcsolt eszköz-mód property-je."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub()
    view.engine().rootContext().setContextProperty("editController", stub)
    view.engine().rootContext().setContextProperty("controller", None)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    qml = _PANEL_QML.format(tab=tab, szelesseg=PANEL_SZELESSEG)
    component.setData(qml.encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(PANEL_SZELESSEG, 900)
    root.setWidth(PANEL_SZELESSEG)
    root.setHeight(900)
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((view, root, component, stub))
    view.show()
    qt_app.processEvents()
    panel = _child(root, "panel")
    if mod is not None:
        panel.setProperty(mod, True)
        qt_app.processEvents()
    return panel


def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _child(root: QQuickItem, name: str) -> QQuickItem:
    for item in _walk(root):
        if item.objectName() == name:
            return item
    found = root.findChild(QObject, name)
    assert found is not None, f"{name} nem található a kirajzolt fában"
    return found


def _kozok(ertekek: list[float]) -> list[float]:
    """Szomszédos értékek különbsége — ez az osztásköz, illetve a hézag."""
    return [b - a for a, b in zip(ertekek, ertekek[1:], strict=False)]


def _doboz(panel: QQuickItem, item: QQuickItem) -> tuple[float, float, float, float]:
    """(x, y, szélesség, magasság) a PANEL koordinátarendszerében."""
    bal_felso = item.mapToItem(panel, 0, 0)
    return (bal_felso.x(), bal_felso.y(), item.width(), item.height())


# ==========================================================================
# 1. A panel váza (spec 1. szakasz)
# ==========================================================================
class TestAPanelVaza:
    def test_a_panel_280_kepont_szeles(self, qt_app) -> None:
        panel = _render(qt_app)

        assert panel.property("implicitWidth") == PANEL_SZELESSEG

    def test_a_fulsav_a_276_kepontos_tartalom_oszlopot_toltile(
        self, qt_app
    ) -> None:
        """A fülsáv (`tabs`) x 3..279 — a tartalom-oszloppal azonos."""
        panel = _render(qt_app)

        x, _, szelesseg, _ = _doboz(panel, _child(panel, "editTabBar"))

        assert abs(szelesseg - TARTALOM_SZELESSEG) <= 1, (
            f"a fülsáv {szelesseg:.0f} px széles a 276 helyett — a tartalom-"
            "oszlop nem az eredeti szélességű (spec 1.)"
        )
        assert abs(x - 3) <= 1, f"a fülsáv x = {x:.0f}, az eredetiben 3"

    def test_a_fulsav_25_kepont_magas(self, qt_app) -> None:
        panel = _render(qt_app)

        _, _, _, magassag = _doboz(panel, _child(panel, "editTabBar"))

        assert abs(magassag - 25) <= 0.5, (
            f"a fülsáv {magassag:.0f} px magas a 25 helyett (spec 1.)"
        )


# ==========================================================================
# 2. A hét fül (spec 2. szakasz — a tulajdonosi kivétel számszerűsítve)
# ==========================================================================
class TestAHetFul:
    def test_a_fulek_szelessege_a_spec_szerinti(self, qt_app) -> None:
        panel = _render(qt_app)

        szelessegek = [
            round(_doboz(panel, _child(panel, nev))[2]) for nev in FULEK
        ]

        assert szelessegek == list(FUL_SZELESSEGEK), (
            f"a fülek szélessége {szelessegek}, az elvárt "
            f"{list(FUL_SZELESSEGEK)} — 39·39·40·39·40·39·40 = 276 (spec 2.)"
        )

    def test_a_fulek_kozott_nincs_hezag(self, qt_app) -> None:
        panel = _render(qt_app)

        dobozok = [_doboz(panel, _child(panel, nev)) for nev in FULEK]

        # minden fül BAL széle pontosan az előző JOBB szélén kezdődik
        bal_szelek = [doboz[0] for doboz in dobozok[1:]]
        jobb_szelek = [doboz[0] + doboz[2] for doboz in dobozok[:-1]]
        for jobb, bal in zip(jobb_szelek, bal_szelek, strict=True):
            hezag = bal - jobb
            assert abs(hezag) <= 0.5, (
                f"{hezag:.1f} px hézag két fül között — az eredetiben a "
                "fülek hézag nélkül töltik ki az oszlopot (spec 2.)"
            )

    def test_a_fulek_pontosan_kitoltik_a_tartalom_oszlopot(self, qt_app) -> None:
        panel = _render(qt_app)

        elso = _doboz(panel, _child(panel, FULEK[0]))
        utolso = _doboz(panel, _child(panel, FULEK[-1]))

        teljes = (utolso[0] + utolso[2]) - elso[0]
        assert abs(teljes - TARTALOM_SZELESSEG) <= 1, (
            f"a hét fül együtt {teljes:.0f} px-t foglal a 276 helyett"
        )

    @pytest.mark.parametrize("nev", FULEK)
    def test_a_fulikonok_16_es_19_kepont_kozott_magasak(self, qt_app, nev) -> None:
        """`y 49..68` a 25 px-es sávban — a mai 22 × 22 túl nagy (spec 1.)."""
        panel = _render(qt_app)

        ikon = _child(panel, nev + "Icon")

        assert 16 <= ikon.height() <= 19, (
            f"a(z) {nev} ikonja {ikon.height():.0f} px magas — az eredetiben "
            "16–19 px (spec 1.)"
        )


# ==========================================================================
# 3. Az 1. fül csempe-rácsa (spec 3. szakasz) — a #741 FŐ oka
# ==========================================================================
class TestAzElsoFulCsempeRacsa:
    def test_a_csempek_44x30_kepontosak(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        meretek = {
            nev: (
                round(_child(panel, nev + "Icon").width()),
                round(_child(panel, nev + "Icon").height()),
            )
            for nev in CSEMPEK
        }

        rossz = {nev: m for nev, m in meretek.items() if m != (44, 30)}
        assert rossz == {}, (
            f"nem 44 × 30-as csempeképek: {rossz} (spec 3.)"
        )

    def test_az_oszlopkoz_81_kepont(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        xek = [
            _doboz(panel, _child(panel, nev + "Icon"))[0]
            for nev in CSEMPEK[:3]
        ]

        kozok = _kozok(xek)
        for koz in kozok:
            assert abs(koz - 81) <= 1.5, (
                f"az oszlopköz {koz:.1f} px a 81 helyett (spec 3.)"
            )

    def test_a_sorkoz_64_kepont(self, qt_app) -> None:
        """A #741 FŐ oka: ma 104 px (94-es cella + 10 rowSpacing)."""
        panel = _render(qt_app, tab=0)

        yok = [
            _doboz(panel, _child(panel, nev + "Icon"))[1]
            for nev in ("editToolCrop", "editToolEnhance", "editToolRetouch")
        ]

        kozok = _kozok(yok)
        for koz in kozok:
            assert abs(koz - 64) <= 1.5, (
                f"a csempe-sorköz {koz:.1f} px a 64 helyett — három sor × "
                "~40 px többlet tolja le a panel alját (#741, spec 3.)"
            )

    @pytest.mark.parametrize("nev", CSEMPEK)
    def test_a_felirat_a_csempe_alatt_kozepre_zarva_all(self, qt_app, nev) -> None:
        panel = _render(qt_app, tab=0)

        kep = _doboz(panel, _child(panel, nev + "Icon"))
        felirat = _doboz(panel, _child(panel, nev + "Label"))

        assert felirat[1] >= kep[1] + kep[3] - 0.5, (
            f"a(z) {nev} felirata nem a csempekép ALATT van (spec 3.)"
        )
        kep_kozep = kep[0] + kep[2] / 2
        felirat_kozep = felirat[0] + felirat[2] / 2
        assert abs(kep_kozep - felirat_kozep) <= 1.5, (
            f"a(z) {nev} felirata nincs a csempeképpel egy középvonalon"
        )


# ==========================================================================
# 4. A Derítőfény-sor (spec 3. szakasz vége)
# ==========================================================================
class TestADeritofenySor:
    def test_a_kis_kep_44x30_es_a_racs_elso_oszlopaval_egy_vonalban_all(
        self, qt_app
    ) -> None:
        panel = _render(qt_app, tab=0)

        ikon = _doboz(panel, _child(panel, "fixesFillLightIcon"))
        elso_oszlop = _doboz(panel, _child(panel, "editToolCropIcon"))

        assert (round(ikon[2]), round(ikon[3])) == (44, 30), (
            f"a Derítőfény kis képe {ikon[2]:.0f} × {ikon[3]:.0f}, "
            "az eredetiben 44 × 30 (spec 3.)"
        )
        assert abs(ikon[0] - elso_oszlop[0]) <= 1.5, (
            f"a kis kép x = {ikon[0]:.0f}, a csempe-rács 1. oszlopa "
            f"x = {elso_oszlop[0]:.0f} — az eredetiben AZONOS (x 37)"
        )

    def test_a_csuszka_127x27(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        _, _, szelesseg, magassag = _doboz(
            panel, _child(panel, "fixesFillSlider")
        )

        assert abs(szelesseg - 127) <= 1, (
            f"a Derítőfény-csúszka {szelesseg:.0f} px széles a 127 helyett"
        )
        assert abs(magassag - 27) <= 1, (
            f"a Derítőfény-csúszka {magassag:.0f} px magas a 27 helyett"
        )

    def test_a_felirat_a_csuszka_folott_all(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        csuszka = _doboz(panel, _child(panel, "fixesFillSlider"))
        felirat = _doboz(panel, _child(panel, "fixesFillLightLabel"))

        assert felirat[1] + felirat[3] <= csuszka[1] + 3, (
            "a Derítőfény felirata nem a csúszka FÖLÖTT van (spec 3.)"
        )


# ==========================================================================
# 5. A Visszavonás/Újra sor (spec 1. szakasz)
# ==========================================================================
class TestAVisszavonasUjraSor:
    def test_a_ket_gomb_132x28(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        for nev in ("editUndoButton", "editRedoButton"):
            _, _, szelesseg, magassag = _doboz(panel, _child(panel, nev))
            assert abs(szelesseg - 132) <= 1, (
                f"{nev} {szelesseg:.0f} px széles a 132 helyett (spec 1.)"
            )
            assert abs(magassag - 28) <= 1, (
                f"{nev} {magassag:.0f} px magas a 28 helyett (spec 1.)"
            )

    def test_a_ket_gomb_kozott_5_kepont_hezag(self, qt_app) -> None:
        panel = _render(qt_app, tab=0)

        bal = _doboz(panel, _child(panel, "editUndoButton"))
        jobb = _doboz(panel, _child(panel, "editRedoButton"))

        hezag = jobb[0] - (bal[0] + bal[2])
        assert abs(hezag - 5) <= 0.5, (
            f"{hezag:.1f} px hézag a Visszavonás és az Újra között az 5 "
            "helyett (spec 1.)"
        )

    def test_a_sor_a_tartalom_alatt_marad_616(self, qt_app) -> None:
        """#616: a sor a TARTALOM alatt ül, nem a panel aljára szegezve.

        A #741 méretei ezt a szerződést NEM írják felül: nagy ablakban a
        gombsor több száz képponttal a tartalom alatt, üres mező túloldalán
        jelenne meg — a felhasználó joggal hitte, hogy nincsenek is ott.
        """
        panel = _render(qt_app, tab=0)

        sor = _doboz(panel, _child(panel, "editorGlobalUndoRow"))
        also_csempe = _doboz(panel, _child(panel, "fixesFillSlider"))

        assert sor[1] < also_csempe[1] + 200, (
            f"a gombsor y = {sor[1]:.0f}, a fül tartalma "
            f"y = {also_csempe[1]:.0f}-nél ér véget — a sor elszakadt a "
            "tartalomtól (#616)"
        )


# ==========================================================================
# 6. Finomhangolás (spec 4. szakasz)
# ==========================================================================
class TestAFinomhangolasCsuszkai:
    CSUSZKAK = (
        "finetuneFillSlider", "finetuneHighlightsSlider",
        "finetuneShadowsSlider", "finetuneTempSlider",
    )

    @pytest.mark.parametrize("nev", CSUSZKAK)
    def test_a_csuszka_191x27(self, qt_app, nev) -> None:
        panel = _render(qt_app, tab=1)

        _, _, szelesseg, magassag = _doboz(panel, _child(panel, nev))

        assert abs(szelesseg - 191) <= 1.5, (
            f"{nev} {szelesseg:.0f} px széles a 191 helyett (spec 4.)"
        )
        assert abs(magassag - 27) <= 1, (
            f"{nev} {magassag:.0f} px magas a 27 helyett (spec 4.)"
        )

    def test_a_csuszkak_osztaskoze_kb_53_kepont(self, qt_app) -> None:
        panel = _render(qt_app, tab=1)

        yok = [_doboz(panel, _child(panel, nev))[1] for nev in self.CSUSZKAK]

        kozok = _kozok(yok)
        for koz in kozok:
            assert 48 <= koz <= 58, (
                f"a csúszkák osztásköze {koz:.0f} px — az eredetiben "
                "53 · 54 · 52 (spec 4.)"
            )

    def test_a_csuszkak_azonos_x_en_allnak(self, qt_app) -> None:
        panel = _render(qt_app, tab=1)

        xek = [_doboz(panel, _child(panel, nev))[0] for nev in self.CSUSZKAK]

        assert max(xek) - min(xek) <= 1.5, (
            f"a négy csúszka x-e szétesik: {[round(x) for x in xek]} — az "
            "eredetiben mind a négy x 30-on áll (spec 4.)"
        )


# ==========================================================================
# 7. Az effekt-rács (spec 5.) — ez ma már JÓ, ez csak visszalépés-őr
# ==========================================================================
class TestAzEffektRacs:
    def test_az_oszlopkoz_88_kepont_marad(self, qt_app) -> None:
        """#704 eredménye — a #741 méretei nem ronthatják el."""
        panel = _render(qt_app, tab=2)

        xek = [
            _doboz(panel, _child(panel, nev))[0]
            for nev in ("effectUnsharp", "effectSepia", "effectBw")
        ]

        kozok = _kozok(xek)
        for koz in kozok:
            assert abs(koz - 88) <= 1.5, (
                f"az effekt-rács oszlopköze {koz:.1f} px a 88 helyett — a "
                "#704 mért geometriája elromlott (spec 5.)"
            )


# ==========================================================================
# 8. Visszatérő gombméretek (spec 7. szakasz)
# ==========================================================================
class TestAVisszateroGombmeretek:
    #: (mód-property, a párban álló gombok) — mind 98 × 28
    PAROK = (
        ("cropActive", ("cropApplyButton", "cropCancelButton")),
        ("cropActive", ("cropRotateButton", "cropPreviewButton")),
        ("redeyeActive", ("redeyeApplyButton", "redeyeCancelButton")),
        ("textActive", ("textApplyButton", "textCancelButton")),
    )

    @pytest.mark.parametrize("mod,gombok", PAROK)
    def test_a_parban_allo_gombok_98x28(self, qt_app, mod, gombok) -> None:
        panel = _render(qt_app, mod=mod)

        for nev in gombok:
            _, _, szelesseg, magassag = _doboz(panel, _child(panel, nev))
            assert abs(szelesseg - 98) <= 1.5, (
                f"{nev} {szelesseg:.0f} px széles a 98 helyett (spec 7.)"
            )
            assert abs(magassag - 28) <= 1.5, (
                f"{nev} {magassag:.0f} px magas a 28 helyett (spec 7.)"
            )

    @pytest.mark.parametrize("nev", (
        "retouchUndoPatchButton", "retouchRedoPatchButton",
        "retouchResetButton", "retouchApplyButton", "retouchCancelButton",
    ))
    def test_a_retusalas_gombjai_118x28(self, qt_app, nev) -> None:
        """A retusálás gombjai 118 px szélesek, nem 98 (spec 6.3/7.)."""
        panel = _render(qt_app, mod="retouchActive")

        _, _, szelesseg, magassag = _doboz(panel, _child(panel, nev))

        assert abs(szelesseg - 118) <= 1.5, (
            f"{nev} {szelesseg:.0f} px széles a 118 helyett (spec 7.)"
        )
        assert abs(magassag - 28) <= 1.5, (
            f"{nev} {magassag:.0f} px magas a 28 helyett (spec 7.)"
        )

    def test_a_kepara_legordulo_21_kepont_magas(self, qt_app) -> None:
        panel = _render(qt_app, mod="cropActive")

        _, _, _, magassag = _doboz(panel, _child(panel, "cropAspectCombo"))

        assert abs(magassag - 21) <= 0.5, (
            f"a képarány-legördülő {magassag:.0f} px magas a 21 helyett "
            "(spec 6.1/7.)"
        )

    @pytest.mark.parametrize(
        "nev", ("textFontFamilyBox", "textFontSizeBox")
    )
    def test_a_szoveg_eszkoz_legordulei_21_kepont_magasak(
        self, qt_app, nev
    ) -> None:
        panel = _render(qt_app, mod="textActive")

        _, _, _, magassag = _doboz(panel, _child(panel, nev))

        assert abs(magassag - 21) <= 0.5, (
            f"a(z) {nev} {magassag:.0f} px magas a 21 helyett (spec 6.4/7.)"
        )
