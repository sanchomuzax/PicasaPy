"""A szín-varázspálca: a viszonyítási színt a program választja — #551.

A mérés kimondta, hogy a pálca NEM külön szűrő: ugyanabba a `finetune2` p4
mezőbe ír, mint a kézi pipetta — a Picasa saját `.picasa.ini`-je bizonyítja
(`filters=finetune2=1,0.000000,0.000000,0.000000,006b8088,0.000000;`). A
színt a kevéssé telített képpontok átlagából becsüljük, a zöldre normálva.
"""

import numpy as np
import pytest

from picasapy.render.tone import (
    NEUTRAL_GREEN_ANCHOR,
    apply_neutral_pipette,
    estimate_neutral_color,
)
from support.jpeg_factory import make_jpeg


class TestEstimateNeutralColor:
    def test_a_zold_mindig_a_viszonyitasi_alap(self):
        image = np.random.default_rng(7).integers(
            0, 256, size=(32, 32, 3), dtype=np.uint8
        )
        assert estimate_neutral_color(image)[1] == NEUTRAL_GREEN_ANCHOR

    def test_semleges_kep_semleges_szint_ad(self):
        image = np.full((16, 16, 3), 120, dtype=np.uint8)
        assert estimate_neutral_color(image) == (128, 128, 128)

    def test_kekes_kepre_a_kek_bajt_no(self):
        # kékes színezet → a viszonyítási szín kékebb, tehát a KORREKCIÓ a
        # kéket húzza vissza (k_B = 128 / p4_B < 1)
        image = np.full((16, 16, 3), (100, 110, 130), dtype=np.uint8)
        red, _, blue = estimate_neutral_color(image)
        assert blue > NEUTRAL_GREEN_ANCHOR > red

    def test_a_telitett_keppontok_nem_szamitanak(self):
        # egy telített vörös folt nem téríti el a becslést a semlegestől
        image = np.full((32, 32, 3), 120, dtype=np.uint8)
        image[:8, :8] = (255, 0, 0)
        assert estimate_neutral_color(image) == (128, 128, 128)

    def test_fekete_kep_semleges(self):
        image = np.zeros((8, 8, 3), dtype=np.uint8)
        assert estimate_neutral_color(image) == (128, 128, 128)

    def test_a_becsult_szin_semlegesit(self):
        # a becsült színnel elvégzett korrekció a színezetet KIVESZI
        image = np.full((16, 16, 3), (100, 110, 130), dtype=np.uint8)
        corrected = apply_neutral_pipette(image, estimate_neutral_color(image))
        spread_before = int(image[0, 0].max()) - int(image[0, 0].min())
        spread_after = int(corrected[0, 0].max()) - int(corrected[0, 0].min())
        assert spread_after < spread_before


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


def _filters(photo):
    from picasapy.ini import load_document

    ini = photo.parent / ".picasa.ini"
    if not ini.exists():
        return ""
    section = load_document(ini).section(photo.name)
    return (section.get("filters") if section else None) or ""


class TestControllerSlot:
    def test_a_palca_a_finetune2_p4_mezojebe_ir(self, controller, tmp_path):
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(16, 12))
        controller.beginEdit("1", str(photo))

        assert controller.applyColorWand() is True

        chain = _filters(photo)
        assert chain.startswith("finetune2=1,")
        # a p4 a lánc ÖTÖDIK mezője (1 + négy paraméter után), AARRGGBB alak
        p4 = chain.rstrip(";").split(",")[4]
        assert len(p4) == 8 and p4.startswith("ff")
        assert p4[4:6] == "80"  # a zöld bájt mindig 0x80 = 128

    def test_a_palca_visszavonhato(self, controller, tmp_path):
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(16, 12))
        controller.beginEdit("1", str(photo))
        controller.applyColorWand()

        assert controller.undoAction == "finetune"
        controller.undo()
        assert _filters(photo) == ""

    def test_aktiv_szerkesztes_nelkul_hibat_jelez(self, controller):
        with pytest.raises(ValueError):
            controller.applyColorWand()

    def test_a_csuszkak_erteket_nem_bantja(self, controller, tmp_path):
        photo = make_jpeg(tmp_path / "IMG_0001.jpg", size=(16, 12))
        controller.beginEdit("1", str(photo))
        controller.setFinetune(0.2, 0.1, 0.05, 0.0)

        controller.applyColorWand()

        fields = _filters(photo).rstrip(";").split(",")
        assert fields[1] == "0.200000"  # Derítőfény
        assert fields[2] == "0.100000"  # Kiemelések
        assert fields[3] == "0.050000"  # Árnyékok
