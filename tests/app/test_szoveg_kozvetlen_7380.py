"""#7380: a szöveg KÖZVETLENÜL a képre gépelhető (controller-oldal).

Az eredeti Szöveg eszközben nincs szövegmező a panelben: a kattintás helyén
jelölt hely van, a begépelt szöveg a képen jelenik meg. A QML-doboz ezért
két controller-adatot kér:

* `textEditPlacement` - HOL áll a szerkesztett doboz (a kattintott pont,
  vagy a kijelölt mentett felirat helye);
* `setTextInlineEditing` - a QML-doboz maga rajzolja a szerkesztett szöveget,
  ezért az előnézeti raszter azt a blokkot NEM rajzolja (különben a doboz
  szövege és a raszter szövege egymásra csúszna).
"""

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))


def _mentett_felirat(controller, content: str, x: float, y: float) -> None:
    controller.enterTextTool()
    controller.setTextDraft(content)
    controller.previewNewTextPlacement(x, y)
    controller.applyText()
    assert controller.waitForBackgroundWorkers(30.0)


class TestSzerkesztettHelye:
    def test_kattintas_elott_nincs_szerkesztesi_hely(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        assert controller.textEditPlacement == {}

    def test_kattintott_pont_a_szerkesztes_helye(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.previewNewTextPlacement(0.25, 0.4)
        hely = controller.textEditPlacement
        assert hely["x"] == pytest.approx(0.25)
        assert hely["y"] == pytest.approx(0.4)

    def test_kijelolt_mentett_felirat_helye(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _mentett_felirat(controller, "Nyaralás", 0.3, 0.6)
        controller.enterTextTool()  # a mentett felirat kijelölődik
        hely = controller.textEditPlacement
        assert hely["x"] == pytest.approx(0.3)
        assert hely["y"] == pytest.approx(0.6)

    def test_az_uj_kattintas_felulirja_a_mentett_helyet(self, controller, photo):
        controller.beginEdit("1", str(photo))
        _mentett_felirat(controller, "Nyaralás", 0.3, 0.6)
        controller.enterTextTool()
        controller.previewNewTextPlacement(0.7, 0.2)
        hely = controller.textEditPlacement
        assert hely["x"] == pytest.approx(0.7)
        assert hely["y"] == pytest.approx(0.2)

    def test_kilepes_utan_nincs_szerkesztesi_hely(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.previewNewTextPlacement(0.25, 0.4)
        controller.exitTextTool()
        assert controller.textEditPlacement == {}


class TestBeagyazottSzerkesztes:
    def test_alapbol_a_piszkozat_a_raszteren_is_latszik(self, controller, photo):
        """A jelző nélkül a régi viselkedés marad: a Python-oldali hívók
        (és a meglévő próbák) változatlanul a raszteren látják a piszkozatot."""
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Piszkozat")
        controller.previewNewTextPlacement(0.2, 0.3)
        specs = controller._current_text_spec()
        assert specs is not None
        assert [s.content for s in specs] == ["Piszkozat"]

    def test_beagyazott_szerkesztesnel_az_uj_piszkozat_nem_kerul_a_rasztere(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextInlineEditing(True)
        controller.setTextDraft("Piszkozat")
        controller.previewNewTextPlacement(0.2, 0.3)
        assert controller._current_text_spec() is None

    def test_beagyazott_szerkesztesnel_a_kijelolt_mentett_blokk_kimarad(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        _mentett_felirat(controller, "Első", 0.2, 0.3)
        _mentett_felirat(controller, "Második", 0.7, 0.8)
        controller.enterTextTool()  # az első blokk kijelölve
        controller.setTextInlineEditing(True)
        specs = controller._current_text_spec()
        assert specs is not None
        assert [s.content for s in specs] == ["Második"]

    def test_a_jelzo_kikapcsolasa_visszahozza_a_rasztert(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.enterTextTool()
        controller.setTextInlineEditing(True)
        controller.setTextDraft("Piszkozat")
        controller.previewNewTextPlacement(0.2, 0.3)
        controller.setTextInlineEditing(False)
        specs = controller._current_text_spec()
        assert specs is not None
        assert [s.content for s in specs] == ["Piszkozat"]

    def test_uj_szerkesztesi_munkamenet_alaphelyzetbe_allitja_a_jelzot(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.setTextInlineEditing(True)
        controller.endEdit()
        controller.beginEdit("2", str(photo))
        controller.enterTextTool()
        controller.setTextDraft("Piszkozat")
        controller.previewNewTextPlacement(0.2, 0.3)
        assert controller._current_text_spec() is not None
