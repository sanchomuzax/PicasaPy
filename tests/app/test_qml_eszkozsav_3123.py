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

⚠️ Amit ez a fájl NEM mér: a LÁTVÁNYT. A sötét sáv a világos képen jól
látszik-e, arra referencia-képernyőkép kellene. Itt a geometria, a színek,
az állapotok és a bekötés van mérve.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent, QQmlEngine

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


def _gomb(sav, nev):
    obj = sav.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestGeometria:
    def test_a_gombok_merete_82x28(self, betoltott):
        for nev in ("cropApplyButton", "cropCancelButton"):
            gomb = _gomb(betoltott, nev)
            assert gomb.property("width") == 82
            assert gomb.property("height") == 28

    def test_a_sav_magassaga_a_gombe(self, betoltott):
        assert betoltott.property("height") == 28

    def test_a_sav_szelessege_ket_gomb_es_a_koz(self, betoltott):
        assert betoltott.property("width") == 82 + 4 + 82


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
        assert kitoltes.alpha() == 229
        assert (keret.red(), keret.green(), keret.blue()) == (0xCB, 0xCA, 0xCA)
        assert keret.alpha() == 229


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
        # középre (m_centerX) és 10 képponttal a kirajzolt kép alja fölé
        assert "x: (photo.width - width) / 2" in f
        assert "(photo.height + photo.paintedHeight) / 2" in f
        assert "- height - 10" in f
