"""#3234 — az eszköz-sáv paraméter-csúszkája, a MÉRT geometriával.

A #3123 a kép fölé vitte a sávot; a sávnak azonban a `.tre` szerint egy
**csúszkája** is van. Ez a fájl a csúszka geometriáját, láthatóságát és a
bekötését őrzi.

## A mérés

```
#---Straighen Overlay ---------------------------------      (editpanel.tre:1038)
toolslider/thumb: toolslider/toolslider                      (:1040)
toolslider/toolslider: editpanel/tool_slider_container       (:1044)
editpanel/tool_slider_container: editpanel/tool_container    (:1049)
editpanel/tool_container: editpanel/preview                  (:1052)
```

| réteg (`respack.yt`) | méret |
|---|---|
| `tool_slider_container` | **267 × 28** |
| `toolslider/rect: toolslider` | **253 × 28**, x = 7 |
| `toolslider/thumb` | **16 × 24** |

⭐ **A sáv a KIEGYENESÍTÉS (Straighten) átfedése.** A `.tre`-ben a fenti
négy bejegyzést a `#---Straighen Overlay---` szakaszfejléc vezeti be, és
ezt megerősíti, hogy a többi eszköznek **saját** Alkalmaz/Mégse párja van
a saját paneljében: `cropapply`/`cropcancel` a `crop_well`-ben (:817, :805),
`retouchapply`/`retouchcancel` a `retouch_well`-ben (:894, :906),
`redeyeapply`/`redeyecancel` a `redeye_well`-ben (:722, :739).

⛔ **A retusálás ecsetmérete NEM ide tartozik** — a jegy törzse ezt
feltételezte, a mérés viszont az ellenkezőjét mondja:
`editpanel/brushslider_container: editpanel/retouch_well` (:869), és a
retusáló kezelője is a `brushslider/scaleslider`-re hivatkozik (:962).
Az ecsetméret-csúszka tehát a BAL panelben marad.

⚠️ Amit ez a fájl nem mér: a LÁTVÁNYT. A geometria, a láthatóság és a
bekötés van állítva, nem az, hogy a rajz képpontra egyezik.
"""

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine

_KEEPALIVE: list[object] = []

_SAV_QML = """
import QtQuick
import PicasaPy 1.0

Item {
    width: 600
    height: 200
    EditorToolBar {
        id: sav
        objectName: "azSav"
        tool: "tilt"
        csuszkaMin: -1
        csuszkaMax: 1
    }
}
"""


@pytest.fixture
def sav(qt_app):
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
    elem = obj.findChild(QObject, "azSav")
    assert elem is not None
    yield elem
    engine.deleteLater()


def _gyerek(szulo, nev):
    obj = szulo.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


class TestGeometria:
    def test_a_csuszka_kontenere_267x28(self, sav):
        doboz = _gyerek(sav, "toolSliderContainer")

        assert doboz.property("width") == 267
        assert doboz.property("height") == 28

    def test_a_sav_253x28_a_konteneren_belul_x7(self, sav):
        csuszka = _gyerek(sav, "tiltSlider")

        assert csuszka.property("width") == 253
        assert csuszka.property("height") == 28
        assert csuszka.property("x") == 7

    def test_a_fogantyu_16x24(self, sav):
        csuszka = _gyerek(sav, "tiltSlider")

        assert csuszka.property("handleWidth") == 16
        assert csuszka.property("handleHeight") == 24

    def test_a_sav_szelessege_a_csuszkaval_egyutt_no(self, sav):
        """267 (csúszka) + 4 (köz) + 82 + 4 + 82 (a két gomb)."""
        assert sav.property("width") == 267 + 4 + 82 + 4 + 82

    def test_a_sav_magassaga_valtozatlanul_28(self, sav):
        assert sav.property("height") == 28


class TestLathatosag:
    @pytest.mark.parametrize("eszkoz", ["crop", "retouch", "text", "redeye"])
    def test_parameter_nelkuli_eszkozon_nincs_csuszka(self, sav, eszkoz):
        """A jegy 3. pontja: ahol nincs paraméter, ott a csúszka nem
        látszik, és a sáv a két gombra szűkül."""
        sav.setProperty("tool", eszkoz)

        assert _gyerek(sav, "toolSliderContainer").property("visible") is False
        assert sav.property("width") == 82 + 4 + 82

    def test_a_kiegyenesitesen_latszik(self, sav):
        assert _gyerek(sav, "toolSliderContainer").property("visible") is True

    def test_az_objektumnev_az_ESZKOZT_koveti(self, sav):
        """A `tiltSlider` NÉV a mai bekötés horgonya (#72/#131) — a
        csúszka a sávba költözött, de ugyanazon a néven marad."""
        assert sav.findChild(QObject, "tiltSlider") is not None
        sav.setProperty("tool", "crop")
        assert sav.findChild(QObject, "cropSlider") is not None


class TestBekotes:
    def test_a_tartomany_a_hivotol_jon(self, sav):
        csuszka = _gyerek(sav, "tiltSlider")

        assert csuszka.property("from") == -1
        assert csuszka.property("to") == 1

    def test_az_ertekvaltas_jelzest_ad(self, sav, qt_app):
        latott = []
        sav.csuszkaMozgott.connect(lambda ertek: latott.append(round(ertek, 3)))

        _gyerek(sav, "tiltSlider").setProperty("value", 0.5)
        qt_app.processEvents()

        assert latott == [0.5]

    def test_az_elengedes_kulon_jelzest_ad(self, sav, qt_app):
        csuszka = _gyerek(sav, "tiltSlider")
        latott = []
        sav.csuszkaElengedve.connect(lambda ertek: latott.append(round(ertek, 3)))

        csuszka.setProperty("value", 0.25)
        csuszka.setProperty("pressed", True)
        qt_app.processEvents()
        assert latott == [], "lenyomáskor még nem véglegesítünk"

        csuszka.setProperty("pressed", False)
        qt_app.processEvents()

        assert latott == [0.25]


class TestForras:
    """Amit csak a forráson lehet mérni — kimondva, hogy ez a határa."""

    @property
    def nezo(self):
        return (
            Path(__file__).resolve().parents[2]
            / "src/picasapy/app/qml/PicasaPy/PhotoViewer.qml"
        ).read_text(encoding="utf-8")

    def test_a_dontes_csuszkaja_mar_nem_a_bal_panel_alatt_all(self):
        """A csúszka a sávba költözött: a nézőben nem maradhat egy másik,
        `tiltSlider` nevű vezérlő a panel alatt."""
        assert self.nezo.count('objectName: "tiltSlider"') == 0

    def test_a_kiegyenesites_a_sav_eszkoze_lett(self):
        """A sáv `tool`-ja a kiegyenesítést is felveszi — a korábbi
        láthatósági feltétellel együtt (`activeTab === 0`), hogy a sáv ne
        jelenjen meg egy másik fülön."""
        nezo = self.nezo

        assert "editorPanel.tiltActive" in nezo
        assert '? "tilt" : ""' in nezo
        assert "editorPanel.activeTab === 0) ? \"tilt\"" in nezo

    def test_a_retusalas_ecsetmerete_a_BAL_panelben_marad(self):
        """`editpanel/brushslider_container: editpanel/retouch_well` —
        ellenpróba a jegy téves premisszájára."""
        retus = (
            Path(__file__).resolve().parents[2]
            / "src/picasapy/app/qml/PicasaPy/EditorRetouchPanel.qml"
        ).read_text(encoding="utf-8")

        assert 'objectName: "retouchBrushSizeSlider"' in retus
