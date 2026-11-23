"""#7407: a Szöveg eszköz Clear All gombja eszközön belüli piszkozat, amelyet a Cancel visszahoz.

Specifikáció és jegy: #7407.
(1) meglévő szövegnél Clear All, Cancel, újranyitás után a szöveg és az ini azonos a megnyitásival;
(2) Clear All, Apply után a kép a szöveg nélküli, az ini-ben nincs text= és textactive=,
    az Undo és Redo tiltott;
(3) Clear All után az eszköz nyitva, Apply aktív, Clear All tiltott.
"""

from __future__ import annotations

from pathlib import Path
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


def _ini_tartalom(photo: Path) -> str:
    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    return ini.read_text(encoding="utf-8")


def _elokeszitett_kep_szoveggel(controller, photo: Path, szoveg: str = "PicasaCancelProba") -> None:
    controller.beginEdit("1", str(photo))
    controller.enterTextTool()
    controller.setTextDraft(szoveg)
    controller.previewTextPlacement(0.316, 0.145)
    controller.applyText()
    controller.exitTextTool()


class TestSzovegClearAllCancel7407:
    def test_clear_all_piszkozatbol_torol_de_ini_valtozatlan(self, controller, photo):
        """A Clear All leveszi a szöveget a piszkozatból, de az inibe NEM ír."""
        _elokeszitett_kep_szoveggel(controller, photo, "PicasaCancelProba")
        kezdo_ini = _ini_tartalom(photo)
        assert "text=" in kezdo_ini
        assert "textactive=1" in kezdo_ini

        controller.enterTextTool()
        assert controller.hasTextOverlay is True
        assert controller.textDraft == "PicasaCancelProba"

        controller.clearText()

        # 1. Az iniben még változatlanul ott kell lennie a szövegnek
        mostani_ini = _ini_tartalom(photo)
        assert mostani_ini == kezdo_ini, "A Clear All nem írhat az inibe!"

        # 2. A piszkozatból viszont lekerült a felirat
        assert controller.hasTextOverlay is False
        assert controller.textDraft == ""
        assert controller.textCleared is True
        assert controller._current_text_spec() is None

    def test_cancel_visszahozza_a_megnyitaskori_szoveget_es_init(self, controller, photo):
        """(1) meglévő szövegnél Clear All, Cancel, újranyitás után a szöveg és az ini azonos."""
        _elokeszitett_kep_szoveggel(controller, photo, "PicasaCancelProba")
        kezdo_ini = _ini_tartalom(photo)

        controller.enterTextTool()
        assert controller.textDraft == "PicasaCancelProba"

        controller.clearText()
        assert controller._current_text_spec() is None

        # Cancel (exitTextTool)
        controller.exitTextTool()

        # Az ini továbbra is változatlan
        assert _ini_tartalom(photo) == kezdo_ini

        # Újranyitás után a szöveg a képen, azonos a megnyitásival
        controller.enterTextTool()
        assert controller.hasTextOverlay is True
        assert controller.textDraft == "PicasaCancelProba"
        assert controller.textCleared is False
        spec = controller._current_text_spec()
        assert spec is not None
        assert any(s.content == "PicasaCancelProba" for s in spec)

    def test_apply_utan_torlodik_az_inibol_es_undo_redo_tiltott(self, controller, photo):
        """(2) Clear All, Apply után a kép szöveg nélküli, az ini-ben nincs text=/textactive=."""
        _elokeszitett_kep_szoveggel(controller, photo, "PicasaCancelProba")
        assert "text=" in _ini_tartalom(photo)

        controller.enterTextTool()
        controller.clearText()
        assert controller.textCleared is True

        # Apply véglegesíti a törlést
        controller.applyText()
        controller.exitTextTool()

        zarult_ini = _ini_tartalom(photo)
        assert "text=" not in zarult_ini
        assert "textactive=" not in zarult_ini
        assert controller.hasTextOverlay is False
        assert controller._current_text_spec() is None
        assert controller.canUndo is False
        assert controller.canRedo is False
