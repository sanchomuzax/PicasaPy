"""#3123 — az eszköz-sáv: az Alkalmaz/Mégse pár a KÉP FÖLÖTT lebeg.

A mérés (`respack.yt` + `editpanel.tre`):

```
editpanel/tool_container: editpanel/preview   ← a szülő a KÉP, nem a panel
m_centerX                                     ← vízszintesen középre
YConstraint 1, 1, -10                         ← 10 px-re a kép aljától
m_hidden                                      ← alapból rejtett

layer:editpanel/button(APPLY):  tool_ok       82 × 28
layer:editpanel/button(CANCEL): tool_cancel   82 × 28
  kitöltés #505050 alfa 229 · keret #CBCACA alfa 229
m_buttontypecolor3 = FFFFFFFF · CCFFFFFF · FFFFFFFF
```

#4029: a #69 felvételén a két 229-es alfa hatásos értéke 206
(round(229²/255)); a renderelt minták 111 / 70 / 210.

#4035: ugyanazon a felvételen a gombkeret 2 képpont, a sarok sugara 7
#képpont. A próba a sugárt a QML-objektumon, a keret vastagságát és a
#sarok kontúrját pedig renderelt képpontokon ellenőrzi.

#4037: a sávban nincs EditorActionBadge; a felirat APPLY/CANCEL. A renderelt
#69-mérés a gomb jobb szélső 21 pixelén egyszínű kitöltést mutat, és a két
#gomb között 5 háttérpixel látszik.

⚠️ A teljes nézőképet ez a fájl nem veti össze a Picasa felvételével.
A #4029-es próba viszont a gombok renderelt mintapontjait hasonlítja a #69
felvétel számaihoz; a többi próba a geometriát, állapotokat és bekötést méri.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickView

_KEEPALIVE = []

_SAV_QML = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 400
    height: 200
    EditorToolBar {
        id: sav
        objectName: "azSav"
        tool: "crop"
    }
}
"""

_TILT_SAV_QML = _SAV_QML.replace('tool: "crop"', 'tool: "tilt"')

_RENDER_QML = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 400
    height: 200
    Rectangle {
        anchors.fill: parent
        color: "#f0f0f0"
    }
    Rectangle {
        x: 87
        width: 82
        height: 28
        color: "#1e1e1e"
    }
    EditorToolBar {
        objectName: "kirajzoltSav"
        tool: "crop"
    }
}
"""


@pytest.fixture
def betoltott(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(engine)
    component.setData(_SAV_QML.encode("utf-8"), QUrl())
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([component, obj])
    sav = obj.findChild(QObject, "azSav")
    assert sav is not None
    yield sav
    engine.deleteLater()


@pytest.fixture
def betoltott_tilt(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(engine)
    component.setData(_TILT_SAV_QML.encode("utf-8"), QUrl())
    obj = component.create()
    assert [e.toString() for e in component.errors()] == []
    assert obj is not None
    QQmlEngine.setObjectOwnership(obj, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend([component, obj])
    sav = obj.findChild(QObject, "azSav")
    assert sav is not None
    yield sav
    engine.deleteLater()


@pytest.fixture
def kirajzolt_gombok(qt_app):
    """Két különböző tónusú háttérre kirajzolt gombok képpontjai."""
    import picasapy.app.application as app_module

    view = QQuickView()
    view.engine().addImportPath(str(app_module._APP_DIR / "qml"))
    component = QQmlComponent(view.engine())
    component.setData(_RENDER_QML.encode("utf-8"), QUrl())
    root = component.create()
    assert [error.toString() for error in component.errors()] == []
    assert root is not None
    root.setParentItem(view.contentItem())
    view.resize(400, 200)
    view.show()
    for _ in range(5):
        qt_app.processEvents()
    image = view.grabWindow()
    assert not image.isNull(), "az eszköz-sáv QML-je nem rajzolódott ki"
    _KEEPALIVE.extend((view, component, root))
    yield image
    view.close()


def _gomb(sav, nev):
    obj = sav.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _assert_rgb_kozel(image, x, y, expected):
    actual = image.pixelColor(x, y)
    kapott = (actual.red(), actual.green(), actual.blue())
    assert all(abs(a - b) <= 2 for a, b in zip(kapott, expected, strict=True)), (
        f"a kirajzolt ({x}, {y}) képpont RGB-je {kapott}, "
        f"a #69 mérés szerint {expected} (±2)"
    )


class TestGeometria:
    def test_a_gombok_merete_82x28(self, betoltott):
        for nev in ("cropApplyButton", "cropCancelButton"):
            gomb = _gomb(betoltott, nev)
            assert gomb.property("width") == 82
            assert gomb.property("height") == 28

    def test_a_gomb_sarkanak_sugara_a_69_felvetelen_merve_7(self, betoltott):
        gomb = _gomb(betoltott, "cropApplyButton")
        assert gomb.property("radius") == 7

    def test_a_sav_magassaga_a_gombe(self, betoltott):
        assert betoltott.property("height") == 28

    def test_a_sav_szelessege_ket_gomb_es_a_koz(self, betoltott):
        assert betoltott.property("width") == 82 + 5 + 82

    def test_tiltnel_az_alkalmaz_balra_a_megse_jobbra_all(
        self, betoltott_tilt
    ):
        """A #69 felvétel sorrendje és 5 px-es gombköze maradjon."""
        apply = _gomb(betoltott_tilt, "tiltApplyButton")
        cancel = _gomb(betoltott_tilt, "tiltCancelButton")

        assert apply.property("x") == 267 + 5
        assert cancel.property("x") == 267 + 5 + 82 + 5


class TestSzinek:
    def test_a_kitoltes_es_a_keret_a_MERT_ertek(self, betoltott):
        gomb = _gomb(betoltott, "cropApplyButton")
        kitoltes = QColor(gomb.property("color"))
        #: a keretet a SÁV tulajdonságából olvassuk: a `border` aloobjektum
        #: (`QQuickPen`) a QObject-property-n nem konvertálható, a
        #: "border.color" út pedig feketét ad — mérve.
        keret = QColor(betoltott.property("keretSzin"))
        assert QColor(betoltott.property("kitoltesSzin")) == kitoltes
        assert (kitoltes.red(), kitoltes.green(), kitoltes.blue()) == (0x50, 0x50, 0x50)
        # #4029, a #69 renderelt mintái: a 229-es alfa kétszeri hatása
        # 229²/255 = 205,65, tehát a QML-ben mért hatásos alfa 206.
        assert kitoltes.alpha() == round(229 * 229 / 255) == 206
        assert (keret.red(), keret.green(), keret.blue()) == (0xCB, 0xCA, 0xCA)
        assert keret.alpha() == round(229 * 229 / 255) == 206

    def test_a_renderelt_gomb_a_69_felvetel_mintaihoz_egyezik(self, kirajzolt_gombok):
        """A #4029 #69 mintái: kitöltés 111/70, keret 210 (±2 szint)."""
        kep = kirajzolt_gombok
        _assert_rgb_kozel(kep, 20, 14, (111, 111, 111))
        _assert_rgb_kozel(kep, 160, 14, (70, 70, 70))
        _assert_rgb_kozel(kep, 41, 0, (210, 209, 209))

    def test_a_renderelt_keret_ket_keppont_vastag(self, kirajzolt_gombok):
        """A #69-en az első két sor a keret, a harmadik már kitöltés."""
        kep = kirajzolt_gombok
        _assert_rgb_kozel(kep, 41, 1, (210, 209, 209))
        _assert_rgb_kozel(kep, 41, 2, (111, 111, 111))

    def test_a_renderelt_sarok_konturja_a_69_meresehez_egyezik(
        self, kirajzolt_gombok
    ):
        """A #69-en a bal felső sarok (0,0), (7,0), (0,7) mintái."""
        kep = kirajzolt_gombok
        _assert_rgb_kozel(kep, 0, 0, (240, 240, 240))
        _assert_rgb_kozel(kep, 7, 0, (210, 209, 209))
        _assert_rgb_kozel(kep, 0, 7, (210, 209, 209))

    def test_a_gombok_jobb_szeli_21_pixele_csak_kitoltes(self, kirajzolt_gombok):
        """A #69 középső mintasorán az APPLY x=893–913 között végig 111."""
        kep = kirajzolt_gombok
        for bal, eltol, szelesseg, vart, turelem in (
            (0, 58, 21, (111, 111, 111), 0),
            (87, 63, 15, (70, 70, 70), 2),
        ):
            for x in range(bal + eltol, bal + eltol + szelesseg):
                y = 14
                kapott = kep.pixelColor(x, y)
                rgb = (kapott.red(), kapott.green(), kapott.blue())
                assert all(
                    abs(a - b) <= turelem
                    for a, b in zip(rgb, vart, strict=True)
                ), (
                    f"a {bal}px-nél álló gomb jobb szélső mintasorában "
                    f"({x}, {y}) {rgb} jelent meg a kitöltés helyett ({vart})"
                )

    def test_a_felirat_lathato_pixeleinek_doboza_kozepen_all(
        self, kirajzolt_gombok
    ):
        """A megjelenő felirat befoglaló dobozának közepe ±1 px-en belül van."""
        kep = kirajzolt_gombok
        for bal in (0, 87):
            pixelek = [
                (x, y)
                for y in range(2, 26)
                for x in range(bal + 2, bal + 80)
                if all(
                    csatorna >= 170
                    for csatorna in (
                        kep.pixelColor(x, y).red(),
                        kep.pixelColor(x, y).green(),
                        kep.pixelColor(x, y).blue(),
                    )
                )
            ]
            assert pixelek, f"a {bal}px-nél álló gomb felirata nem rajzolódott ki"
            bal_x = min(x for x, _y in pixelek)
            jobb_x = max(x for x, _y in pixelek)
            felirat_kozepe = (bal_x + jobb_x) / 2
            gomb_kozepe = bal + (82 - 1) / 2
            assert abs(felirat_kozepe - gomb_kozepe) <= 1, (
                f"a {bal}px-nél álló gomb feliratdobozának közepe "
                f"{felirat_kozepe:.1f}px, a gombé {gomb_kozepe:.1f}px"
            )


class TestAllapotok:
    def test_eszkoz_nelkul_rejtve(self, betoltott):
        betoltott.setProperty("tool", "")
        assert betoltott.property("visible") is False

    def test_az_objektumnevek_az_ESZKOZT_koveti(self, betoltott):
        betoltott.setProperty("tool", "retouch")
        assert betoltott.findChild(QObject, "retouchApplyButton") is not None
        assert betoltott.findChild(QObject, "retouchCancelButton") is not None
        assert betoltott.findChild(QObject, "cropApplyButton") is None

    def test_a_tiltott_alkalmaz_nem_enged_kattintast(self, betoltott, qt_app):
        betoltott.setProperty("applyEnabled", False)
        qt_app.processEvents()
        gomb = _gomb(betoltott, "cropApplyButton")
        assert gomb.property("enabled") is False
        assert gomb.property("opacity") < 1.0

    def test_a_ket_gomb_a_sav_jelzeset_suti_el(self, betoltott, qt_app):
        latott = []
        betoltott.applyClicked.connect(lambda: latott.append("apply"))
        betoltott.cancelClicked.connect(lambda: latott.append("cancel"))
        for nev in ("cropApplyButton", "cropCancelButton"):
            QMetaObject.invokeMethod(
                _gomb(betoltott, nev),
                "buttonClicked",
                Qt.ConnectionType.DirectConnection,
            )
        qt_app.processEvents()
        assert latott == ["apply", "cancel"]


class TestForras:
    """Amit csak a forráson lehet mérni — kimondva, hogy ez a határa."""

    @property
    def forras(self):
        return (
            Path(__file__).resolve().parents[2]
            / "src/picasapy/app/qml/PicasaPy/EditorToolBar.qml"
        ).read_text(encoding="utf-8")

    def test_az_Esc_a_megse_gombot_suti_el(self):
        """`Property escapekey 1` a `tool_cancel`-en — a vágásnál viszont a
        `CropOverlay` maga kezeli az Esc-et, tehát ott nem duplázunk."""
        f = self.forras
        assert 'sequence: "Escape"' in f
        #: #3320: a vágás-kivétel eltűnt — a sáv már csak a kiegyenesítésé
        assert 'sav.tool !== "crop"' not in f
        assert "enabled: sav.visible" in f
        assert "onActivated: sav.cancelClicked()" in f

    def test_az_eger_alatt_CSAK_a_felirat_halvanyodik(self):
        """A csomagban nincs `_n`/`_h`/`_p` változat: egyetlen rajz van."""
        assert "containsMouse && gomb.buttonEnabled ? 0.8 : 1.0" in self.forras

    def test_a_sav_felirata_nagybetus_es_jel_nelkuli(self):
        assert 'qsTr("APPLY")' in self.forras
        assert 'qsTr("CANCEL")' in self.forras
        assert "font.weight: Font.DemiBold" in self.forras
        assert "font.letterSpacing: -1" in self.forras
        assert "EditorActionBadge {" not in self.forras


class TestAKepFolott:
    """A sáv a TELJES ablakban: a helye a kirajzolt képhez van kötve."""

    def test_a_sav_a_kep_fole_kerul_10_keppontra(self, qml_app, qt_app):
        window, _controller, _lib, _engine = qml_app
        sav = window.findChild(QObject, "editorToolBar")
        assert sav is not None, "az eszköz-sáv nincs bekötve a PhotoViewerbe"
        # eszköz-mód nélkül rejtve
        assert sav.property("visible") is False

    def test_kiegyenesitesben_a_kep_alja_folott_all(self, qml_app, qt_app):
        """A LEKÉPEZETT geometria: a sáv alja 10 képponttal a kirajzolt kép
        alja fölött van, és vízszintesen középen — nem a forrásban, hanem az
        élő ablakban mérve.

        #3320: a mérés a KIEGYENESÍTÉSSEL megy, mert a sáv már csak azé (a
        `.tre` a `#---Straighen Overlay---` alá teszi); a másik négy eszköz
        párja a saját paneljében ül.
        """
        window, _controller, _lib, _engine = qml_app
        window.setProperty("viewerOpen", True)
        nezo = window.findChild(QObject, "photoViewer")
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        panel.setProperty("activeTab", 0)
        panel.setProperty("tiltActive", True)
        qt_app.processEvents()

        sav = window.findChild(QObject, "editorToolBar")
        assert sav.property("visible") is True
        assert sav.findChild(QObject, "tiltApplyButton") is not None

        #: ⚠️ `sav.parent()` NEM a kép: a QML `parent:` a LÁTVÁNY-szülőt
        #: állítja, a QObject-szülő a létrehozás helye marad
        #: (`viewerPhotoArea`). A képet a nevén kell megkeresni.
        kep = window.findChild(QObject, "viewerImage")
        assert kep is not None
        #: ⚠️ A környezetfüggő skip TILOS (a CI-n mindig kimaradna): a
        #: kötést akkor is mérjük, ha a kép ebben a környezetben nem
        #: rajzolódott ki — a `paintedHeight` ilyenkor 0, és a képlet
        #: ugyanúgy ellenőrizhető. Amit így NEM mérünk, az a valódi kép
        #: fölötti LÁTVÁNY; azt a jegy kimondja.
        alja = sav.property("y") + sav.property("height")
        rajzolt_magassag = kep.property("paintedHeight")
        assert rajzolt_magassag, "a kép nem rajzolódott ki — a mérés alapja hiányzik"
        kep_alja = (kep.property("height") + rajzolt_magassag) / 2
        assert abs(kep_alja - alja - 10) <= 0.5, (
            f"a sáv alja {kep_alja - alja:.1f} px-re van a kép aljától a "
            "mért 10 helyett"
        )
        kozep = sav.property("x") + sav.property("width") / 2
        assert abs(kozep - kep.property("width") / 2) <= 0.5

    def test_a_forras_a_MERT_kenyszereket_koveti(self):
        f = (
            Path(__file__).resolve().parents[2]
            / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
        ).read_text(encoding="utf-8")
        # középre (m_centerX) és 10 képponttal a kirajzolt kép alja fölé —
        # #3741: a mérce a `photo` helyett a `photoArea.fokuszKep`-hez
        # igazodik. A sáv sibling a forgatatlan photoArea-rétegen, ezért a
        # mért helyi középpontot mapToItem/mapFromItem viszi át, majd a kép
        # transzformációját külön örökli; az élő geometriai próbák ezt mérik.
        assert "(photoArea.fokuszKep.width - width) / 2" in f
        assert "(photoArea.fokuszKep.height" in f
        assert "+ photoArea.fokuszKep.paintedHeight) / 2" in f
        assert "- height - 10" in f
        assert "var cel = kep.mapToItem(" in f
        assert "parent.mapFromItem(" in f
        assert "rotation: photoArea.fokuszKep.rotation" in f
        assert "scale: photoArea.fokuszKep.scale" in f
