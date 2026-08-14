"""A szerkesztő-panel elrendezésének szerződése — #628 (a #616 visszavonása).

**Előzmény.** A #422 a felhasználó nyomatékos kérésére LEVETTE a görgethető
keretet az effekt-fülekről. A #616 aztán — a gombsor kilógását orvosolva —
visszatette, és a saját tesztje (`test_content_taller_than_the_area_becomes
_scrollable`) épp a HIBÁS viselkedést rögzítette szerződésként: „a szűk
panelen a rácsnak görgethetőnek kell lennie". Emiatt lett zöld a visszaesés.

**A valódi ok** egy beégetett szám volt: a `PhotoViewer.qml` az
`EditorPanel`-nek fix 420 képpont magasságot adott, akármekkora az ablak.
A 3. fül 12 bélyegképes csempéje (3×4) ennél mindig magasabb — a görgetés
így nem szélsőséges eset volt, hanem az alapállapot.

**A most rögzített szerződés:**

1. a panel a rendelkezésre álló magasságot kapja (a forrásban nincs fix
   panelmagasság);
2. a fülek területe NEM vágott és NEM görgethető;
3. a panel `implicitHeight`-je elbírja a LEGMAGASABB fület is;
4. a Visszavonás/Újra sor a tartalmat követi — sosem kerül a fül tartalmára.

A mód-eszközök (`editorModeToolScroll`) és a csúszkás alpanel görgetése
MARAD: azok tartalma valóban változó hosszú, és nem csempe-rács (#464).
"""

import re
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE = []

#: a fülek indexe a `EditorTabBar` sorrendjében (7 fül: 5 eredeti + #422 + #571)
MINDEN_FUL = (0, 1, 2, 3, 4, 5, 6)

_QML_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml"
)


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _panel(engine, height, active_tab=2):
    """EditorPanel adott magassággal — a hiba a SZŰK panelen jelentkezik."""
    component = QQmlComponent(engine)
    component.setData(
        (
            "import QtQuick\nimport PicasaPy 1.0\n"
            f'EditorPanel {{ objectName: "panel"; width: 240; height: {height};'
            f" activeTab: {active_tab} }}\n"
        ).encode("utf-8"),
        QUrl(),
    )
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, obj))
    return obj


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _also(item) -> float:
    return item.property("y") + item.property("height")


def _qml_blokk(forras: str, fejlec: str) -> str:
    """Egy QML-elem törzse, ZÁRÓJEL-SZÁMLÁLÁSSAL.

    Regexszel a blokk vége nem határozható meg megbízhatóan (egy `.*?` a
    behúzásra hagyatkozva túlfut a következő testvér-elemre, és távoli
    sorokat hoz be a vizsgálatba). A számlálás nem tud túlfutni.
    """
    kezdet = forras.index(fejlec)
    melyseg = 0
    for vege, karakter in enumerate(forras[kezdet:], start=kezdet):
        if karakter == "{":
            melyseg += 1
        elif karakter == "}":
            melyseg -= 1
            if melyseg == 0:
                return forras[kezdet : vege + 1]
    raise AssertionError(f"nem záródik a blokk: {fejlec!r}")


class TestNincsGorgetesAzEffektFuleken:
    """#628 1–2. pont: a fülek területe nem vágott és nem görgethető."""

    def test_a_fulterulet_nem_vagott(self, qml_engine):
        panel = _panel(qml_engine, height=900)

        assert _child(panel, "editorTabArea").property("clip") is not True, (
            "a #422 kifejezetten levette a vágást az effekt-fülekről"
        )

    def test_a_fulterulet_nem_flickable(self, qml_engine):
        """Egy Flickable `contentHeight`-tel rendelkezik — a fülterületnek nem
        szabad annak lennie, különben visszatér a görgetősáv."""
        panel = _panel(qml_engine, height=900)

        area = _child(panel, "editorTabArea")

        assert area.property("contentHeight") is None, (
            "a fülterület újra Flickable lett — ez a #628 visszaesése"
        )

    def test_a_forrasban_nincs_gorgetosav_a_fuleken(self):
        """Forrás-őr: a `ScrollBar` a fülterületről végleg lekerült."""
        forras = (_QML_DIR / "PicasaPy" / "EditorPanel.qml").read_text(
            encoding="utf-8"
        )
        # a mód-eszközök és az alpanel görgetése MARAD, azokat nem bántjuk
        assert "editorTabScroll" not in forras, (
            "a fülek görgethető területe visszakerült (#616 visszaesése)"
        )
        assert "editorModeToolScroll" in forras, (
            "a mód-eszközök görgetésének maradnia kell (#464)"
        )


class TestNincsBeegetettPanelmagassag:
    """#628 1. pont: a panel az ablakkal együtt nő."""

    def test_a_nezoben_nincs_fix_panelmagassag(self):
        forras = (_QML_DIR / "PicasaPy" / "PhotoViewer.qml").read_text(
            encoding="utf-8"
        )
        blokk = _qml_blokk(forras, "EditorPanel {")
        assert not re.search(r"^\s*height:\s*\d+\s*$", blokk, re.M), (
            "a panelnek nem lehet beégetett magassága — az ablakét kell kapnia"
        )
        assert "anchors.bottom: parent.bottom" in blokk, (
            "a panelnek a rendelkezésre álló magasságot kell kitöltenie"
        )


class TestAPanelElbirjaALegmagasabbFulet:
    """#628 4. pont: az „mindig elfér" garancia."""

    @pytest.mark.parametrize("tab", MINDEN_FUL)
    def test_az_implicit_magassag_elfedi_a_ful_tartalmat(self, qml_engine, tab):
        panel = _panel(qml_engine, height=900, active_tab=tab)

        area = _child(panel, "editorTabArea")
        undo_row = _child(panel, "editorGlobalUndoRow")

        kell = area.property("y") + area.property("height") + undo_row.property(
            "height"
        )
        assert panel.property("implicitHeight") >= kell, (
            f"a(z) {tab}. fül tartalma nem fér el a panel implicit magasságában"
        )

    def test_a_leheto_legmagasabb_ful_szabja_meg(self, qml_engine):
        """Az implicitHeight nem a MOSTANI fülé, hanem a legmagasabbé — a
        panel magassága ne ugráljon fülváltáskor."""
        magassagok = {
            tab: _panel(qml_engine, height=900, active_tab=tab).property(
                "implicitHeight"
            )
            for tab in MINDEN_FUL
        }
        assert len(set(magassagok.values())) == 1, (
            f"fülenként más implicit magasság: {magassagok}"
        )


class TestAGombsorSosemKerulATartalomra:
    """#628 3. pont: a sor a tartalmat követi, nem fix helyen ül."""

    @pytest.mark.parametrize("tab", MINDEN_FUL)
    def test_a_gombsor_az_aktiv_ful_alatt_van(self, qml_engine, tab):
        panel = _panel(qml_engine, height=900, active_tab=tab)

        area = _child(panel, "editorTabArea")
        undo_row = _child(panel, "editorGlobalUndoRow")

        assert undo_row.property("y") >= _also(area) - 1, (
            f"a(z) {tab}. fülön a gombsor rálóg a tartalomra"
        )

    def test_szuk_panelen_a_sor_marad_lathato(self, qml_engine):
        """**#641-gyel MEGVÁLTOZOTT szerződés.**

        A #628 itt még azt állította, hogy szűk panelen a sor a tartalom ALÁ
        tolódik. Élesben ez azt eredményezte, hogy a sor kicsúszott a
        képernyőről, és a felhasználó egyáltalán nem látta a Visszavonás/Újra
        gombokat.

        Az új szabály: a sor a LÁTHATÓ terület alján marad, és szűkösnél a
        fül TARTALMA veszít. A visszavonás a szerkesztés visszacsinálásának
        egyetlen útja; egy levágott csempesor ennél sokkal kisebb baj."""
        panel = _panel(qml_engine, height=160, active_tab=2)

        undo_row = _child(panel, "editorGlobalUndoRow")

        assert _also(undo_row) <= 160, "a gombsor kilóg a panelből"
        assert undo_row.property("y") >= 0

    def test_bo_helyen_a_panel_aljan_ul(self, qml_engine):
        """Bő helyen az eredeti látványa: a sor a panel alján."""
        panel = _panel(qml_engine, height=900, active_tab=2)

        undo_row = _child(panel, "editorGlobalUndoRow")

        assert _also(undo_row) >= panel.property("height") - 20, (
            "bő helyen a gombsornak a panel alján kell ülnie"
        )


class TestParamPanelStaysUsable:
    """#616 mellékhatás-őr (VÁLTOZATLANUL érvényes): a csúszkás alpanel maga
    is Flickable, és egy Flickable implicit magassága 0 — ha a fülek területébe
    csomagolnánk, eltűnne. Ezért kívül marad, saját horgonnyal a gombsorig."""

    def _with_param_panel(self, qml_engine):
        # a `paramPanelActive` futásidőben kapcsolódik (a panel a
        # létrehozáskori értéket felülírja), ezért UTÓLAG állítjuk
        panel = _panel(qml_engine, height=600)
        panel.setProperty("paramEffectName", "sepia")
        panel.setProperty("paramPanelActive", True)
        return panel

    def test_the_param_panel_has_a_real_height(self, qml_engine):
        panel = self._with_param_panel(qml_engine)

        param = _child(panel, "editorEffectParamScroll")

        assert param.property("height") > 0, "az alpanel eltűnt"
        assert param.property("clip") is True

    def test_the_param_panel_replaces_the_tabs(self, qml_engine):
        """Az alpanel a fülek HELYETT jelenik meg, nem föléjük."""
        panel = self._with_param_panel(qml_engine)

        assert _child(panel, "editorTabArea").property("visible") is False

    def test_the_param_panel_stops_above_the_undo_row(self, qml_engine):
        panel = self._with_param_panel(qml_engine)

        param = _child(panel, "editorEffectParamScroll")
        undo_row = _child(panel, "editorGlobalUndoRow")

        assert _also(param) <= undo_row.property("y") + 1
