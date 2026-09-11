"""#604: a vörösszem-keretre kattintva visszavonható az EGYES javítás.

Az eredeti eszköz **mindhárom** állapotüzenetében ott a mondat:

> „Megjegyzés: a keretbe kattintva visszavonhatja a változást."
> (`RedEye::AutoFixedMessage`, `::DragToSelectMessage`, `::AutoFixRedoMessage`)

Vagyis a keretek a szerkesztés alatt **egyedileg** törölhetők — nem csak az
utolsó („Undo") vagy mind („Reset"). A gyakorlati különbség: ha a program négy
szemet talált és a harmadik javítás rossz, eddig háromszor kellett
visszavonni.

⚠️ **Csak az Alkalmazás ELŐTT.** A javítás alkalmazáskor a mentett
képpontokba kerül, a keretek koordinátái pedig nem őrződnek meg — az eredeti
maga figyelmeztet rá (`IDS_CONFIRM_UNDO_REDEYE`). Ez az őr tehát a PUFFERT
méri, nem az alkalmazott képet.

Amit NEM mér: a kurzor tényleges alakját a képernyőn — csak azt, hogy a
felület a találat-vizsgálathoz kötötte.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from support.jpeg_factory import make_jpeg

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"
_NEZO = (_QML / "PhotoViewer.qml").read_text(encoding="utf-8")
_PANEL = (_QML / "EditorRedeyePanel.qml").read_text(encoding="utf-8")


def _huzo_blokk() -> str:
    """A vörösszem HÚZÓ-területe, két NEVESÍTETT horgony között.

    ⚠️ Szándékosan nem fix karakterszámú ablak: a rögzített méretű vágás
    minden jogos bővítésnél elcsúszik, és akkor az őr a saját ablakát méri,
    nem a kódot."""
    kezd = _NEZO.index('objectName: "redeyeDragArea"')
    veg = _NEZO.index('objectName: "textClickArea"', kezd)
    return _NEZO[kezd:veg]


@pytest.fixture
def controller(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditController(EditPreviewProvider())


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


class TestAKeretTorlese:
    """A vezérlő-oldal: melyik keret esik ki, és mi történik a pufferrel."""

    @pytest.fixture
    def eszkoz(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        return controller

    def test_a_keretre_kattintas_TORLI_azt_az_egyet(self, eszkoz):
        eszkoz.addRedeyeRegion(0.1, 0.1, 0.2, 0.2)
        eszkoz.addRedeyeRegion(0.6, 0.6, 0.2, 0.2)
        assert eszkoz.removeRedeyeRegionAt(0.15, 0.15) is True
        assert eszkoz.redeyeRegionCount == 1
        megmaradt = eszkoz.redeyeRegions[0]
        assert megmaradt["x"] == pytest.approx(0.6)

    def test_a_kereteken_KIVULI_kattintas_nem_tesz_semmit(self, eszkoz):
        eszkoz.addRedeyeRegion(0.1, 0.1, 0.2, 0.2)
        assert eszkoz.removeRedeyeRegionAt(0.9, 0.9) is False
        assert eszkoz.redeyeRegionCount == 1

    def test_ures_pufferen_nem_hibazik(self, eszkoz):
        assert eszkoz.removeRedeyeRegionAt(0.5, 0.5) is False
        assert eszkoz.redeyeRegionCount == 0

    def test_atfedo_kereteknel_a_LEGUTOBBI_esik_ki(self, eszkoz):
        """A felhasználó azt látja legfelül, arra kattint."""
        eszkoz.addRedeyeRegion(0.1, 0.1, 0.4, 0.4)
        eszkoz.addRedeyeRegion(0.2, 0.2, 0.4, 0.4)
        assert eszkoz.removeRedeyeRegionAt(0.3, 0.3) is True
        assert eszkoz.redeyeRegions[0]["x"] == pytest.approx(0.1)

    def test_a_torles_VISSZAVONHATO_az_Undo_gombbal(self, eszkoz):
        """A meglévő „Undo" a jegy 3. pontja szerint MARAD, és erre is áll."""
        eszkoz.addRedeyeRegion(0.1, 0.1, 0.2, 0.2)
        eszkoz.removeRedeyeRegionAt(0.15, 0.15)
        assert eszkoz.canUndoRedeyeRegion is True
        eszkoz.undoRedeyeRegion()
        assert eszkoz.redeyeRegionCount == 1

    def test_a_keret_SZELE_is_talalat(self, eszkoz):
        """A keret vonalára kattintás is a kereten van — a felhasználó a
        vonalat látja, nem a belsejét."""
        eszkoz.addRedeyeRegion(0.2, 0.2, 0.2, 0.2)
        assert eszkoz.removeRedeyeRegionAt(0.2, 0.3) is True

    def test_az_INI_nem_iródik_a_torlestol(self, eszkoz, photo):
        eszkoz.addRedeyeRegion(0.1, 0.1, 0.2, 0.2)
        eszkoz.removeRedeyeRegionAt(0.15, 0.15)
        ini = photo.parent / ".picasa.ini"
        assert not ini.exists() or "redeye" not in ini.read_text(encoding="utf-8")


class TestATalalatVizsgalat:
    @pytest.fixture
    def eszkoz(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterRedeyeTool()
        controller.addRedeyeRegion(0.2, 0.2, 0.2, 0.2)
        return controller

    def test_a_kereten_talalat(self, eszkoz):
        assert eszkoz.redeyeRegionHitAt(0.3, 0.3) is True

    def test_a_kereten_kivul_nincs(self, eszkoz):
        assert eszkoz.redeyeRegionHitAt(0.8, 0.8) is False

    def test_a_vizsgalat_NEM_valtoztat_allapotot(self, eszkoz):
        elozo = eszkoz.redeyeRegionCount
        eszkoz.redeyeRegionHitAt(0.3, 0.3)
        eszkoz.redeyeRegionHitAt(0.9, 0.9)
        assert eszkoz.redeyeRegionCount == elozo
        assert eszkoz.canUndoRedeyeRegion is True  # csak a hozzáadástól


class TestAFelulet:
    def test_a_puszta_kattintas_TORLESRE_megy(self):
        blokk = _huzo_blokk()
        assert "editController.removeRedeyeRegionAt(" in blokk
        #: a nulla méretű kijelölés a törlés kapuja — húzásnál marad a felvétel
        assert "if (selW <= 0 || selH <= 0)" in blokk
        assert "editController.addRedeyeRegion(" in blokk

    def test_a_kurzor_a_TALALATHOZ_van_kotve(self):
        blokk = _huzo_blokk()
        assert "Qt.PointingHandCursor" in blokk
        assert "redeyeRegionHitAt(" in blokk
        #: húzás közben marad a célkereszt, különben a kurzor váltogatna
        assert "!dragging && keretenAll" in blokk

    def test_a_HUZAS_valtozatlanul_uj_regiot_ad(self):
        """A törlés nem veheti el a felvételt: a jegy 3. pontja szerint a
        meglévő utak maradnak."""
        blokk = _huzo_blokk()
        assert blokk.index("if (selW <= 0 || selH <= 0)") < blokk.index(
            "editController.addRedeyeRegion("
        )

    def test_az_utmutato_kiegeszult_az_eredeti_mondataval(self):
        assert 'objectName: "redeyeFrameHintLabel"' in _PANEL
        assert "Note: click inside the box to undo the change." in _PANEL

    def test_a_meglevo_UTAK_megmaradtak(self):
        """A jegy 3. pontja: „Utolsó régió visszavonása" és „Alaphelyzet"
        maradjon — az eredetiben is mindkettő megvolt."""
        assert 'objectName: "redeyeUndoRegionButton"' in _PANEL
        assert 'objectName: "redeyeResetButton"' in _PANEL

    def test_az_AUTO_gomb_kezi_regiok_mellett_is_aktiv(self):
        """A jegy pontosítása: az eredeti szerint az „Automatikus" bármikor
        újrafuttatható. Nálunk ez úgy igaz, hogy a gombnak NINCS tiltó
        feltétele — a szomszédainak van (`buttonEnabled:`)."""
        kezd = _PANEL.index('objectName: "redeyeAutoButton"')
        blokk = _PANEL[kezd : kezd + 200]
        assert "buttonEnabled:" not in blokk
