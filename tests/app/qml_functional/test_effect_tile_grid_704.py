"""Az effekt-fülek csempe-rácsa az EREDETIT követi — #704.

**Miért kellett ez a készlet.** A `docs/specs/ui-audit-editor.md` a
fülrendszert, az effekt-LELTÁRT és a vágás-panelt írja le; a csempe-rács
MEGJELENÉSÉRŐL — fejléc van-e, jelvény, feliratszín — nem volt benne
szakasz, és teszt sem. Ezért nem derült ki egyik eltérés sem, amíg a
felhasználó ránézésre észre nem vette.

**Amit az eredetiről bizonyítottunk** (`editpanel.tre`, a Picasa saját
elrendezés-forrása):

- `editpanel/tabpanel3`-nak PONTOSAN EGY gyereke van, a rács konténere
  (`editpanel/fxthumbs`, `editpanel.tre:428`). Szekciócím, fejlécsáv,
  cím-felirat az `fx*` névtérben nincs. Vagyis a fülre váltva **azonnal a
  csempék jönnek**.
- A rács fix 12 fészkes (`fx1…fx12`), minden csempének három gyereke van:
  `fxpreviewN` (bélyegkép), `fxlabelN` (felirat, a csempe alsó 18 px-es
  sávjában) és `fxN_adorn` (jelvény).

A mérés a `test_editor_panel_rendered_651.py` mintáját követi: valódi
`QQuickView`, a VIZUÁLIS fa bejárása (a `GridLayout` gyerekeit a
`findChild` nem találja meg).
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import Property, QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

_KEEPALIVE: list[object] = []

#: A négy effekt-fül: (activeTab, a fül oszlopának objectName-je, a rácsé).
EFFEKT_FULEK = (
    (2, "effectsColumn", "effectsGrid"),
    (3, "effectsColumn2", "effectsGrid2"),
    (4, "effectsColumn3", "effectsGrid3"),
    (5, "effectsColumn4", "effectsGrid4"),
)

#: A korábbi fejlécsávok feliratai — ezek egyike sem jelenhet meg a
#: csempe-rács fölött (az eredetiben nincs szekciócím).
FEJLEC_FELIRATOK = ("Effects", "Creative", "Artistic", "More Effects",
                    "Legacy Effects")


class _EditControllerStub(QObject):
    """Bélyegképes csempék + a lánc-darabszámok a jelvényhez."""

    def __init__(self, chain: dict[str, int] | None = None) -> None:
        super().__init__()
        self._chain = chain or {}

    @Property(str, constant=True)
    def previewSource(self):
        return "image://editpreview/42?rev=1"

    @Property("QVariantList", constant=True)
    def legacyEffectsInChain(self):
        return []

    @Property("QVariant", constant=True)
    def effectChainCounts(self):
        return self._chain


_PANEL_QML = """
import QtQuick
import PicasaPy 1.0
Item {{
    objectName: "gyoker"
    EditorPanel {{
        objectName: "panel"
        anchors.fill: parent
        activeTab: {tab}
    }}
}}
"""


def _render(qt_app, tab: int, chain: dict[str, int] | None = None) -> QQuickItem:
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    stub = _EditControllerStub(chain)
    view.engine().rootContext().setContextProperty("editController", stub)
    view.engine().rootContext().setContextProperty("controller", None)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)

    component = QQmlComponent(view.engine())
    component.setData(_PANEL_QML.format(tab=tab).encode("utf-8"), QUrl())
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    root = component.create()
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(280, 900)
    root.setWidth(280)
    root.setHeight(900)
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((view, root, component, stub))
    view.show()
    qt_app.processEvents()
    return root


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


def _texts(item: QQuickItem) -> list[str]:
    """A részfa MINDEN szövegének listája (a `text` tulajdonságból)."""
    out = []
    for child in _walk(item):
        value = child.property("text")
        if isinstance(value, str) and value:
            out.append(value)
    return out


# ==========================================================================
# 1. Nincs fejlécsáv a rács fölött
# ==========================================================================
@pytest.mark.parametrize("tab,oszlop,racs", EFFEKT_FULEK)
class TestNincsFejlecsav:
    """#704/1. — `editpanel/tabpanel3` egyetlen gyereke a rács konténere."""

    def test_a_racs_a_ful_legelso_eleme(self, qt_app, tab, oszlop, racs) -> None:
        gyoker = _render(qt_app, tab)
        column = _child(gyoker, oszlop)
        grid = _child(gyoker, racs)

        assert grid.y() <= 0.5, (
            f"a(z) {racs} rács {grid.y():.0f} px-rel lejjebb kezdődik a fül "
            "tetejénél — valami (fejlécsáv?) van fölötte, az eredetiben "
            "viszont a fülre váltva azonnal a csempék jönnek (#704)"
        )
        assert column.childItems(), "üres fül"

    def test_nincs_szekciocim_a_fulon(self, qt_app, tab, oszlop, racs) -> None:
        gyoker = _render(qt_app, tab)
        column = _child(gyoker, oszlop)

        talalt = [t for t in _texts(column) if t in FEJLEC_FELIRATOK]

        assert talalt == [], (
            f"a(z) {oszlop} fülön szekciócím maradt: {talalt} — az "
            "`editpanel.tre` szerint az eredetiben nincs ilyen (#704)"
        )


# ==========================================================================
# 2. „Alkalmazva" jelvény
# ==========================================================================
class TestAlkalmazvaJelveny:
    """#704/2. — a rácsról látszania kell, mely effektek vannak a képen."""

    def test_nincs_jelveny_ures_lancon(self, qt_app) -> None:
        gyoker = _render(qt_app, 2, chain={})

        jelveny = _child(gyoker, "effectSepiaBadge")

        assert not jelveny.isVisible(), (
            "üres szerkesztési láncon is jelvényt mutat a Szépia csempéje"
        )

    def test_a_lancban_levo_effekt_jelvenyt_kap(self, qt_app) -> None:
        gyoker = _render(qt_app, 2, chain={"sepia": 1})

        jelveny = _child(gyoker, "effectSepiaBadge")

        assert jelveny.isVisible(), (
            "a láncban szereplő Szépia csempéje nem kap alkalmazva-"
            "jelvényt — a felhasználó a rácsról nem tudja megállapítani, "
            "mely effektek vannak már a képen (#704)"
        )

    def test_a_tobbi_csempe_jelvenytelen_marad(self, qt_app) -> None:
        gyoker = _render(qt_app, 2, chain={"sepia": 1})

        assert not _child(gyoker, "effectBwBadge").isVisible()

    def test_a_jelvenyen_szam_all(self, qt_app) -> None:
        """A jelvényen SZÁM van — de a szám JELENTÉSÉRE nem építünk.

        A spec 3.4 az egyik olvasatot cáfolja (nem lánc-sorszám: egy
        felvételen három csempén egyszerre áll „1"), a másikat sem igazolja
        (azon a felvételen a fotó szerkesztetlen). Amíg a `FUN_005d7c20`
        dekompilálása vagy a célzott képernyőkép-kérés nem dönt, ez az őr
        csak annyit rögzít, hogy a jelvény SZÁMOT mutat — a konkrét értékre
        semmilyen viselkedés nem épül."""
        gyoker = _render(qt_app, 2, chain={"sepia": 2, "warm": 1})

        for name in ("effectSepiaBadgeText", "effectWarmBadgeText"):
            szoveg = _child(gyoker, name).property("text")
            assert szoveg.isdigit() and int(szoveg) >= 1, (
                f"a(z) {name} jelvényén nem szám áll: {szoveg!r}"
            )

    def test_a_jelveny_a_belyegkep_jobb_also_sarkaban_ul(self, qt_app) -> None:
        """A hely az EREDETI erőforrásból egzakt (`ui-audit-editor.md` 3.3):
        `m_fxadorner` = jobb szél −6, alsó szél −19 a csempéhez képest —
        vagyis a BÉLYEGKÉP jobb alsó sarka, a feliratsáv fölött."""
        gyoker = _render(qt_app, 2, chain={"sepia": 1})

        belyegkep = _child(gyoker, "effectSepiaThumb")
        jelveny = _child(gyoker, "effectSepiaBadge")
        felirat = _child(gyoker, "effectSepiaLabel")

        jelveny_jobb = jelveny.mapToItem(None, jelveny.width(), 0).x()
        jelveny_alja = jelveny.mapToItem(None, 0, jelveny.height()).y()
        kep_jobb = belyegkep.mapToItem(None, belyegkep.width(), 0).x()
        kep_alja = belyegkep.mapToItem(None, 0, belyegkep.height()).y()
        felirat_teteje = felirat.mapToItem(None, 0, 0).y()

        assert abs(jelveny_jobb - kep_jobb) <= 1.5, (
            "a jelvény jobb széle nem simul a bélyegkép jobb szélére"
        )
        assert abs(jelveny_alja - kep_alja) <= 1.5, (
            "a jelvény alja nem simul a bélyegkép alsó élére"
        )
        assert jelveny_alja <= felirat_teteje + 0.5, (
            "a jelvény belelóg a feliratsávba"
        )

    def test_a_jelveny_merete_a_mert_ertek(self, qt_app) -> None:
        """13 × 12 px — az 1920×1080-as felvételen mérve (spec 3.3)."""
        gyoker = _render(qt_app, 2, chain={"sepia": 1})

        jelveny = _child(gyoker, "effectSepiaBadge")

        assert (jelveny.width(), jelveny.height()) == (13.0, 12.0)

    def test_a_masik_ket_effekt_fulon_is_mukodik(self, qt_app) -> None:
        """A jelvény nem az egyik fül egyedi kiegészítése."""
        gyoker = _render(qt_app, 3, chain={"lomo": 1})

        assert _child(gyoker, "effectLomoBadge").isVisible()


class TestAFulekCsempeszama:
    """#704 helyesbítés (2026-08-15, ▶KÉP): mindhárom effekt-fül 12 csempés.

    Korábban a 3–5. fül 12 · 12 · 11 gombot tartalmazott, a `Vignette`
    pedig a #422-es „További effektek" gyűjtőfülre került. A felvételek
    szerint a Vignetta az 5. fül 3. csempéje (a Lágyítás után, a
    Képpontnagyítás előtt).
    """

    @pytest.mark.parametrize("tab,oszlop,racs", EFFEKT_FULEK[:3])
    def test_tizenket_csempe_fulenkent(self, qt_app, tab, oszlop, racs) -> None:
        gyoker = _render(qt_app, tab)
        grid = _child(gyoker, racs)

        csempek = [
            child for child in grid.childItems()
            if child.objectName().startswith("effect")
        ]

        assert len(csempek) == 12, (
            f"a(z) {racs} rácsban {len(csempek)} csempe van — az eredetiben "
            "mindhárom effekt-fül 12 helyes (`ui-audit-editor.md` 3.2)"
        )

    def test_a_vignetta_az_otodik_fulon_van(self, qt_app) -> None:
        gyoker = _render(qt_app, 4)

        assert _child(gyoker, "effectVignette") is not None

    def test_a_vignetta_a_lagyitas_es_a_keppontnagyitas_kozott_all(
        self, qt_app
    ) -> None:
        gyoker = _render(qt_app, 4)
        grid = _child(gyoker, "effectsGrid3")

        nevek = [
            child.objectName() for child in grid.childItems()
            if child.objectName().startswith("effect")
        ]

        assert nevek[:4] == [
            "effectBoost", "effectSoften", "effectVignette", "effectPixelate",
        ], f"a fül eleje: {nevek[:4]}"


# ==========================================================================
# 3. Egységes feliratszín
# ==========================================================================
class TestEgysegesFeliratszin:
    """#704/3. — a bejelentő kék és narancs feliratokat látott.

    A kódban EGYETLEN feliratszín van (`PanelButton.qml`,
    `Theme.textDark`/`Theme.textGray`), effektenkénti szín nincs sehol. Ez
    az őr azt rögzíti, hogy ez így is maradjon: ha valaha bekerül egy
    csempe-egyedi szín, itt bukik el.
    """

    @pytest.mark.parametrize("tab,oszlop,racs", EFFEKT_FULEK)
    def test_egy_fulon_minden_felirat_azonos_szinu(
        self, qt_app, tab, oszlop, racs
    ) -> None:
        # a láncban lévő effektek jelvényén SZÁNDÉKOSAN más a szín (fehér
        # szám kék korongon), ezért csak a csempe-FELIRATOKAT nézzük
        gyoker = _render(qt_app, tab, chain={"sepia": 1, "lomo": 1})
        grid = _child(gyoker, racs)

        szinek = {
            child.property("color").name()
            for child in _walk(grid)
            if child.objectName().endswith("Label")
            and child.property("color") is not None
        }

        assert len(szinek) == 1, (
            f"a(z) {racs} rácsban {len(szinek)} különböző feliratszín van: "
            f"{sorted(szinek)} — az eredetiben a csempe-feliratok "
            "egységesen sötétek (#704)"
        )
