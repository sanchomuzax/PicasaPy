"""QML-funkcionális tesztek: EditorPanel ikonos fülei és a bélyegképes
effekt-gombok (#338 — "sima gombok vannak a legtöbb fülön. Nem tetszik.").

Két réteg, a test_editor_effects.py / test_effect_sliders.py mintáját
követve:
- `TestIconTabs*`/`TestPanelButtonThumbnail*`: az EditorPanel-t ÖNÁLLÓAN, a
  `PicasaPy 1.0` modulon át töltjük be — a #338 1. részének (ikonos fülek)
  és 2. részének (bélyegképes gomb-váz) QML-oldali logikáját ellenőrzi,
  Python-oldali FAKE editControllerrel vagy anélkül.
- `TestEffectThumbnailIntegration`: a TELJES app (`qml_app` fixture, valós
  EditController + valós, regisztrált `EffectThumbnailProvider`) — egy
  effekt-gomb bélyegképe ténylegesen megérkezik-e (async render).
"""

import re
import time
from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl, Property
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty

# a QML-ből létrehozott gyökér-objektumok élő Python-referencia nélkül a
# JS-motor tulajdonába kerülnek és a GC bármikor eltávolíthatja őket —
# CppOwnership-re váltva és itt megtartva éljük túl a teszt-futást
# (test_editor_effects.py mintája).
_KEEPALIVE = []

#: #496: a panel forrása több fájlra bomlott (effekt-fülek, vágás, retus,
#: szöveg) — az effekt-gombokat kereső őrök ezért a MODUL összes QML-jét
#: nézik, nem csak az `EditorPanel.qml`-t.
_QML_SOURCE = "\n".join(
    path.read_text(encoding="utf-8")
    for path in sorted(
        (
            Path(__file__).resolve().parents[3]
            / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
        ).glob("*.qml")
    )
)

_TAB_NAMES = (
    "editTabFixes",
    "editTabFinetune",
    "editTabEffects",
    "editTabEffects2",
    "editTabEffects3",
)


class _FakeEditController(QObject):
    """Csak a bélyegkép-URL-hez szükséges felület: `previewSource`."""

    def __init__(self, preview_source="", parent=None):
        super().__init__(parent)
        self._preview_source = preview_source

    @Property(str)
    def previewSource(self):
        return self._preview_source


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


def _load(engine, qml_source):
    """QML-forrás betöltése inline szövegként (nincs saját fájl-URL-je)."""
    component = QQmlComponent(engine)
    component.setData(qml_source.encode("utf-8"), QUrl())
    obj = component.create()
    errors = [e.toString() for e in component.errors()]
    assert errors == [], errors
    assert obj is not None, "a komponens betöltése sikertelen"
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(component)
    _KEEPALIVE.append(obj)
    return obj


def _make_panel(engine, fake_controller=None, active_tab=0):
    if fake_controller is not None:
        engine.rootContext().setContextProperty("editController", fake_controller)
        _KEEPALIVE.append(fake_controller)
    return _load(
        engine,
        "import QtQuick\nimport PicasaPy 1.0\n"
        f'EditorPanel {{ objectName: "panel"; activeTab: {active_tab} }}\n',
    )


class TestIconTabs:
    """#338 1. rész: a szöveges fülek helyett a csavarkulcs/nap/3× ecset
    ikon-készlet — az eredeti Picasa 5 fülének mintája
    (docs/specs/ui-audit-editor.md)."""

    def test_all_five_tabs_have_an_icon_child(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        for name in _TAB_NAMES:
            icon = panel.findChild(QObject, name + "Icon")
            assert icon is not None, f"{name}: hiányzik az ikon"

    @pytest.mark.parametrize(
        "name,expected_kind",
        [
            ("editTabFixes", "wrench"),
            ("editTabFinetune", "sun"),
            ("editTabEffects", "brush"),
            ("editTabEffects2", "brush"),
            ("editTabEffects3", "brush"),
        ],
    )
    def test_tab_icon_kind_matches_the_original_picasa_layout(
        self, qml_engine, qt_app, name, expected_kind
    ):
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        icon = panel.findChild(QObject, name + "Icon")
        assert icon.property("kind") == expected_kind

    def test_three_brush_tabs_have_pairwise_distinct_accent_colors(
        self, qml_engine, qt_app
    ):
        """Az eredeti Picasában a 3./4./5. fül mind ecset, de a 4-5. saját
        (zöld/kék) színmintával különül el a 3.-tól — az egygombos
        emoji-glyph ezt nem tudná, a saját Canvas-rajz igen."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        accents = [
            panel.findChild(QObject, name + "Icon").property("accentColor")
            for name in ("editTabEffects", "editTabEffects2", "editTabEffects3")
        ]
        assert accents[0] != accents[1]
        assert accents[0] != accents[2]
        assert accents[1] != accents[2]

    def test_active_tab_still_gets_a_highlighted_border(self, qml_engine, qt_app):
        """A meglévő kiemelés-logika (aktív fül = selectionBlue keret)
        megmaradt az ikonosításnál."""
        panel = _make_panel(qml_engine, active_tab=0)
        qt_app.processEvents()
        active = panel.findChild(QObject, "editTabFixes")
        inactive = panel.findChild(QObject, "editTabFinetune")
        active_border = QQmlProperty(active, "border.color").read()
        inactive_border = QQmlProperty(inactive, "border.color").read()
        assert active_border != inactive_border

    def test_tab_labels_still_present_but_hidden_and_unwrapped(
        self, qml_engine, qt_app
    ):
        """#318 kompatibilitás: a fülcímke Text VÁLTOZATLANUL létezik (más
        eszközök/tesztek erre támaszkodhatnak), csak már nem látható — a
        levágás elleni védelem (`truncated is False`) is megmaradt."""
        panel = _make_panel(qml_engine)
        qt_app.processEvents()
        for name in _TAB_NAMES:
            label = panel.findChild(QObject, name + "Label")
            assert label is not None, f"{name}: hiányzik a felirat-Text"
            assert label.property("visible") is False
            assert label.property("truncated") is False

    def test_five_tooltip_bindings_present_in_source(self):
        """Minden fülgombnak legyen ToolTip-je — a `MainToolbar.qml`
        mintáját követő `ToolTip.text`/`ToolTip.visible` attached
        property-pár (egyszer az `EditTabButton`-sablonban, de mind a
        hét példányra alkalmazva).

        #1857: a súgó szövege MÁR NEM a `tbtn.label`. A fül nevének
        megismétlése semmi újat nem mondott a felhasználónak; mostantól
        `description` áll ott, és a `label` csak a tartalék, ha egy
        hívóhely nem ad leírást. A leírások meglétét a
        `test_buboreksugok_1857.py` őrzi, fülről fülre."""
        assert "ToolTip.text: tbtn.description" in _QML_SOURCE
        assert "tbtn.label" in _QML_SOURCE, "a tartalék ág eltűnt"
        assert "ToolTip.visible: tabMouse.containsMouse" in _QML_SOURCE
        # mind az 5 EditTabButton-példány adja meg a `label`-t (a ToolTip
        # forrása) — ha ez az 5 nem lenne mind jelen, a ToolTip néma maradna
        assert _QML_SOURCE.count('label: qsTr(') >= 5


class TestEffectThumbSourceWiring:
    """#338 2. rész — a QML-oldali URL-építés (`effectThumbSource`)."""

    def test_no_controller_means_empty_thumb_source(self, qml_engine, qt_app):
        panel = _make_panel(qml_engine, fake_controller=None, active_tab=2)
        qt_app.processEvents()
        button = panel.findChild(QObject, "effectSepia")
        assert button.property("thumbSource") == ""

    def test_thumb_source_built_from_preview_source_photo_id(
        self, qml_engine, qt_app
    ):
        fake = _FakeEditController(preview_source="image://editpreview/42?rev=7")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=2)
        qt_app.processEvents()
        button = panel.findChild(QObject, "effectSepia")
        assert button.property("thumbSource") == "image://effectthumb/42/sepia"

    def test_thumb_source_ignores_revision_bumps(self, qml_engine, qt_app):
        """A bélyegkép csak a FOTÓTÓL függ, nem a szerkesztési revíziótól
        (#338: "effektenként csak egyszer" gyorsítótárazás) — két eltérő
        `rev=`-fel is ugyanazt az URL-t kell adnia."""
        fake_a = _FakeEditController(preview_source="image://editpreview/9?rev=1")
        panel_a = _make_panel(qml_engine, fake_controller=fake_a, active_tab=2)
        qt_app.processEvents()
        source_a = panel_a.findChild(QObject, "effectBw").property("thumbSource")

        fake_b = _FakeEditController(preview_source="image://editpreview/9?rev=55")
        panel_b = _make_panel(qml_engine, fake_controller=fake_b, active_tab=2)
        qt_app.processEvents()
        source_b = panel_b.findChild(QObject, "effectBw").property("thumbSource")

        assert source_a == source_b == "image://effectthumb/9/bw"

    def test_undo_redo_buttons_never_get_a_thumb_source(self, qml_engine, qt_app):
        """A nem-effekt gombok (Undo/Redo/…) a bélyegkép-mezőt sose kapják
        meg — a régi kinézetük érintetlen kell maradjon."""
        fake = _FakeEditController(preview_source="image://editpreview/1?rev=1")
        panel = _make_panel(qml_engine, fake_controller=fake, active_tab=2)
        qt_app.processEvents()
        # #464: a Visszavonás/Újra már GLOBÁLIS (a panel alján, egyetlen
        # példányban) — nem fülönként ismételve
        button = panel.findChild(QObject, "editUndoButton")
        assert button is not None, "a globális Visszavonás gomb hiányzik"
        assert button.property("thumbSource") == ""
        assert panel.findChild(QObject, "effectsUndoButton") is None

    def test_all_36_effect_buttons_reference_a_known_effect_key(self):
        """Regresszió-őr: a `panel.effectThumbSource("<kulcs>")` hívások
        kulcsai pontosan a Python-oldali `EFFECT_NAMES` katalógusban
        legyenek — ha az egyik oldal bővül a másik nélkül, ez buktatja.

        #405 bevezetett négy további hívást a "Gyakori javítások" fülön
        (Vörösszem/Jó napom van/Automatikus kontraszt/Automatikus szín) —
        a #411 ezt VISSZAVONTA (ld. test_editor_411.py): az a fül most
        saját SVG-ikonokat használ, `effectThumbSource()`-t egyáltalán nem
        hív. A Python-oldali `effect_thumbnails._TOOL_PREVIEW_NAMES` külön
        halmaz emiatt megmaradhat (a bélyegkép-provider szintjén továbbra
        is kiszolgálható kulcsok), de a QML-forrásban már nem jelenik meg —
        ezért a maradék 36 katalógus-effekttel pontos egyezést várunk."""
        from picasapy.app.effect_thumbnails import EFFECT_NAMES

        qml_keys = set(
            re.findall(r'panel\.effectThumbSource\("([a-z0-9_]+)"\)', _QML_SOURCE)
        )
        assert qml_keys == set(EFFECT_NAMES)


class TestPanelButtonThumbnailPlaceholder:
    """A helyi `PanelButton` sablon `thumbSource` kiterjesztése — a
    test_editor_effects.py `TestPanelButtonLabelWrapping` mintáját követve,
    önálló `PanelButton`-példányon (nem a teljes panelen át)."""

    def _make_button(self, engine, thumb_source="", label="Sepia", width=110):
        return _load(
            engine,
            "import QtQuick\nimport QtQuick.Layouts\nimport PicasaPy 1.0\n"
            f"ColumnLayout {{\n    width: {width}\n"
            # #496: a PanelButton önálló típus lett (kiemelve az EditorPanel.qml-ből)
            "    PanelButton {\n"
            '        id: btn\n'
            '        objectName: "btn"\n'
            "        Layout.fillWidth: true\n"
            f'        label: "{label}"\n'
            f'        thumbSource: "{thumb_source}"\n'
            "    }\n}\n",
        )

    def test_no_thumb_source_keeps_the_old_plain_look(self, qml_engine, qt_app):
        root = self._make_button(qml_engine, thumb_source="")
        qt_app.processEvents()
        thumb = root.findChild(QObject, "btnThumb")
        assert thumb is None or thumb.property("visible") is False
        button = root.findChild(QObject, "btn")
        label = root.findChild(QObject, "btnLabel")
        # a régi képlet: max(24, felirat-magasság + 10)
        assert button.property("height") == pytest.approx(
            max(24, label.property("implicitHeight") + 10), abs=1
        )

    def test_thumb_source_shows_a_never_blank_placeholder_until_ready(
        self, qml_engine, qt_app
    ):
        """Amíg a bélyegkép nem érkezik meg (itt SOSEM fog, mert az izolált
        motorban nincs regisztrálva az `effectthumb` provider), a gomb NEM
        lehet üres/villogó — a helyőrző-keret látszik, a felirat is megvan."""
        root = self._make_button(
            qml_engine, thumb_source="image://effectthumb/1/sepia"
        )
        qt_app.processEvents()
        button = root.findChild(QObject, "btn")
        thumb_img = root.findChild(QObject, "btnThumb")
        assert thumb_img is not None
        # nincs provider regisztrálva ebben az izolált engine-ben -> a kép
        # sose lesz Ready — a binding (`visible: status === Image.Ready`)
        # szerint az Image emiatt láthatatlan marad...
        assert thumb_img.property("visible") is False
        # ...DE a helyőrző-Rectangle helyette látszik: a gomb SOSE üres.
        placeholder = [
            c for c in thumb_img.parent().children()
            if c is not thumb_img and c.property("visible") is True
        ]
        assert placeholder, "nincs látható helyőrző a bélyegkép helyén"
        label = root.findChild(QObject, "btnLabel")
        assert label.property("text") == "Sepia"
        assert button.property("height") > 24

    def test_thumb_source_button_is_taller_than_plain_button(self, qml_engine, qt_app):
        plain = self._make_button(qml_engine, thumb_source="", label="Sepia")
        qt_app.processEvents()
        plain_height = plain.findChild(QObject, "btn").property("height")

        thumbed = self._make_button(
            qml_engine, thumb_source="image://effectthumb/1/sepia", label="Sepia"
        )
        qt_app.processEvents()
        thumbed_height = thumbed.findChild(QObject, "btn").property("height")

        assert thumbed_height > plain_height


class TestEffectThumbnailIntegration:
    """Teljes app (`qml_app` fixture), valós EditController + valós,
    regisztrált `EffectThumbnailProvider` — a bélyegkép ténylegesen
    megérkezik-e (aszinkron render, #338 kritikus teljesítmény-elvárása:
    a fül megnyitása NEM blokkol, a kép később, `finished`-del jön)."""

    def _open_effects_tab(self, window, qt_app):
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None
        panel.setProperty("activeTab", 2)
        qt_app.processEvents()
        return panel

    def test_effect_button_thumb_source_resolves_to_a_real_url(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        panel = self._open_effects_tab(window, qt_app)
        button = panel.findChild(QObject, "effectSepia")
        source = button.property("thumbSource")
        assert source.startswith("image://effectthumb/")
        assert source.endswith("/sepia")

    def test_thumbnail_arrives_asynchronously_without_blocking(
        self, qml_app, qt_app
    ):
        window, _controller, _engine = qml_app
        panel = self._open_effects_tab(window, qt_app)
        thumb_img = panel.findChild(QObject, "effectSepiaThumb")
        assert thumb_img is not None

        # a binding (`visible: status === Image.Ready`) szerint az Image
        # csak akkor látszik, ha a bélyegkép ténylegesen megérkezett —
        # ezt várjuk be, ismételt processEvents()-tel (a #316-os
        # debounce-teszt mintája), a QML-szál közben NEM akad meg.
        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and thumb_img.property("visible") is not True:
            qt_app.processEvents()
        assert thumb_img.property("visible") is True, "a bélyegkép nem érkezett meg"
        assert 0 < thumb_img.property("implicitWidth") <= 100
        assert 0 < thumb_img.property("implicitHeight") <= 100

    def test_two_different_effect_thumbnails_both_arrive(self, qml_app, qt_app):
        """Ugyanaz a fotó, két eltérő effekt-gomb — mindkettő KÉSZ (nem
        placeholder) bélyegképet kap a valós, regisztrált provideren át
        (a tényleges pixeltartalom-eltérést a Python-szintű
        `test_effect_thumbnails.py` bizonyítja szigorúbban)."""
        window, _controller, _engine = qml_app
        panel = self._open_effects_tab(window, qt_app)
        sepia_img = panel.findChild(QObject, "effectSepiaThumb")
        bw_img = panel.findChild(QObject, "effectBwThumb")

        deadline = time.monotonic() + 10.0
        while time.monotonic() < deadline and (
            sepia_img.property("visible") is not True
            or bw_img.property("visible") is not True
        ):
            qt_app.processEvents()
        assert sepia_img.property("visible") is True
        assert bw_img.property("visible") is True
        assert sepia_img.property("source") != bw_img.property("source")
