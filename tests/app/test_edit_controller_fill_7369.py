"""#7369: a Gyakori javítások Derítőfény-csúszkája a `fill` réteget írja.

A kontroller két, egymástól független utat ad:

- `setFixesFill` / `previewFixesFill` / `fixesFillLight` a `fill=1,<érték>`
  rétegre (Gyakori javítások fül),
- `setFinetune` / `fillLight` a `finetune2` 1. paraméterére (Hangolás fül).

A Visszavonás-felirat az eredeti szövegtárból jön: a `fill` neve `Fill Light`
(`Derítőfény`), a `finetune2`-é `Tuning` (`Finomhangolás`).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QTranslator

from support.jpeg_factory import make_jpeg

_I18N_DIR = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app" / "i18n"


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


@pytest.fixture
def magyar(qt_app):
    translator = QTranslator(qt_app)
    assert translator.load("picasapy_hu", str(_I18N_DIR)), "a hu .qm nem tölthető be"
    qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


def _filters(photo: Path) -> str:
    from picasapy.ini import load_document

    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    section = load_document(ini).section("IMG_0001.jpg")
    return (section.get("filters") if section else None) or ""


class TestFixesFillIras:
    def test_a_mentes_fill_reteget_ir_finetune2_nelkul(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        assert _filters(photo) == "fill=1,0.500000;"
        assert "finetune2" not in _filters(photo)

    def test_a_tulajdonsag_a_mentett_fill_erteket_adja(self, controller, photo):
        controller.beginEdit("1", str(photo))
        assert controller.fixesFillLight == pytest.approx(0.0)
        controller.setFixesFill(0.3)
        assert controller.fixesFillLight == pytest.approx(0.3)

    def test_a_hangolas_tulajdonsag_a_fill_retegtol_fuggetlen(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.3)
        assert controller.fillLight == pytest.approx(0.0)
        assert controller.hasFinetune is False

    def test_egy_eredeti_picasa_fill_sora_betoltodik(self, controller, photo):
        (photo.parent / ".picasa.ini").write_text(
            "[IMG_0001.jpg]\nfilters=fill=1,0.5;\n", encoding="utf-8"
        )
        controller.beginEdit("1", str(photo))
        assert controller.fixesFillLight == pytest.approx(0.5)
        assert controller.fillLight == pytest.approx(0.0)

    def test_nullara_huzas_leveszi_a_fill_reteget(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        controller.setFixesFill(0.0)
        assert _filters(photo) == ""
        assert controller.fixesFillLight == pytest.approx(0.0)

    def test_az_elonezet_nem_ir_ini_be_es_nem_tol_undot(self, controller, photo):
        controller.beginEdit("1", str(photo))
        revision = controller.revision
        controller.previewFixesFill(0.6)
        assert controller.revision == revision + 1
        assert _filters(photo) == ""
        assert controller.canUndo is False

    def test_sok_elonezet_utan_is_egyetlen_fill_reteg_marad(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.previewFixesFill(0.2)
        controller.previewFixesFill(0.7)
        controller.setFixesFill(0.7)
        assert _filters(photo).count("fill=") == 1

    def test_a_visszavonas_leveszi_a_fill_reteget(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.4)
        assert controller.undoAction == "fill"
        controller.undo()
        assert controller.fixesFillLight == pytest.approx(0.0)
        assert _filters(photo) == ""


class TestHangolasMarad:
    def test_a_hangolas_a_finetune2_elso_parameteret_irja(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.5, 0.0, 0.0, 0.0)
        assert _filters(photo) == "finetune2=1,0.500000,0.000000,0.000000,00000000,0.000000;"
        assert controller.fillLight == pytest.approx(0.5)
        assert controller.fixesFillLight == pytest.approx(0.0)

    def test_a_hangolas_a_meglevo_fill_reteget_valtozatlanul_hagyja(
        self, controller, photo
    ):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        controller.setFinetune(0.9, 0.2, 0.0, 0.0)
        filters = _filters(photo)
        assert "fill=1,0.500000;" in filters
        assert filters.count("fill=1,0.500000") == 1
        assert "finetune2=1,0.900000" in filters
        assert controller.fixesFillLight == pytest.approx(0.5)
        assert controller.fillLight == pytest.approx(0.9)

    def test_a_nulla_hangolas_nem_viszi_el_a_fill_reteget(self, controller, photo):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        controller.setFinetune(0.9, 0.0, 0.0, 0.0)
        controller.setFinetune(0.0, 0.0, 0.0, 0.0)
        assert _filters(photo) == "fill=1,0.500000;"


class TestVisszavonasFelirat:
    def test_a_gyakori_javitasok_csuszka_utan_derítofeny(
        self, controller, photo, magyar
    ):
        controller.beginEdit("1", str(photo))
        controller.setFixesFill(0.5)
        assert controller.undoLabel == "Visszavonás: Derítőfény"

    def test_a_hangolas_utan_finomhangolas(self, controller, photo, magyar):
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.5, 0.0, 0.0, 0.0)
        assert controller.undoLabel == "Visszavonás: Finomhangolás"
