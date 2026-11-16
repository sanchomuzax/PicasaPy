"""#7030: a nézőben és a szerkesztőben a Másolás KÉPET tesz a vágólapra.

## A lelet a binárisból

Az eredeti Picasa 3.9 a szerkesztőben (egyképes nézetben) a Másolás
paranccsal a szerkesztésekkel együtt kiszámolt képet teszi a vágólapra,
valódi képadatként: a `0x00a706f0` a `0x00a70776`-nál `push 2`
(`CF_BITMAP`) után hívja a `SetClipboardData`-t (hívó: `0x0069b000`, ld.
`docs/specs/paritas-ellenorzes.md`, #7028). A kép így más programba
közvetlenül képként illeszthető be.

## Mit mér ez a fájl

A `EditController.copyRenderedImageToClipboard` a szolgáltató MEGJELENÍTETT
(szerkesztésekkel renderelt) előnézetét teszi fel QImage-ként. Nem a
rendszervágólapot olvassuk (az fejlesztői gépen és CI-n a munkamenet-
kezelőtől függ, fej nélkül pedig a Qt-vágólap szegmenshibát okozott), hanem
azt a képet, AMIT feltennénk, ugyanúgy, ahogy a fájl-vágólap őre is teszi
(`test_fajl_vagolap_1526.py`).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider

# rontás-kontroll: a `copyRenderedImageToClipboard` a nyers fájlt tölti be a
# renderelt előnézet helyett -> a színtelenségi és az egyezési próba bukik


def _szines_foto(path: Path) -> Path:
    """Telített, képpontonként eltérő kép: a fekete-fehér átalakítás látszik."""
    y, x = np.indices((60, 80))
    rgb = np.stack(
        ((x * 3 + y) % 256, (y * 5 + x) % 256, (x + y * 2) % 256), axis=2
    ).astype(np.uint8)
    Image.fromarray(rgb).save(path)
    return path


def _qimage_tomb(kep) -> np.ndarray:
    """QImage -> (H, W, 3) uint8, platformfüggetlenül (RGB888-ra váltva)."""
    from PySide6.QtGui import QImage

    rgb = kep.convertToFormat(QImage.Format.Format_RGB888)
    sorhossz = rgb.bytesPerLine()
    nyers = np.frombuffer(rgb.constBits(), dtype=np.uint8, count=sorhossz * rgb.height())
    return nyers.reshape(rgb.height(), sorhossz)[:, : rgb.width() * 3].reshape(
        rgb.height(), rgb.width(), 3
    ).copy()


def _kesz_elonezet(vezerlo, qt_app) -> None:
    assert vezerlo.waitForBackgroundWorkers(10.0)
    qt_app.processEvents()


@pytest.fixture
def szerkesztett(qt_app, tmp_path):
    """Nyitott munkamenet egy színes képen, fekete-fehér effekttel."""
    foto = _szines_foto(tmp_path / "szines.png")
    szolgaltato = EditPreviewProvider()
    vezerlo = EditController(szolgaltato)
    vezerlo.beginEdit("fotoA", str(foto))
    vezerlo.applyEffect("bw")
    _kesz_elonezet(vezerlo, qt_app)
    return vezerlo, szolgaltato, foto


class TestASzolgaltatoMegadjaAKepet:
    def test_a_renderelt_kep_masolatkent_adhato_ki(self, szerkesztett):
        vezerlo, szolgaltato, _foto = szerkesztett

        kep = szolgaltato.rendered_image(vezerlo._kulcs)

        assert kep is not None and not kep.isNull()
        tarolt = szolgaltato.requestImage(vezerlo._kulcs, None, None)
        assert (kep.width(), kep.height()) == (tarolt.width(), tarolt.height())
        # önálló példány: a kimásolt kép átírása nem nyúlhat a szolgáltató képéhez
        elotte = _qimage_tomb(tarolt)
        kep.fill(0)
        utana = _qimage_tomb(szolgaltato.requestImage(vezerlo._kulcs, None, None))
        assert np.array_equal(elotte, utana)

    def test_ismeretlen_azonositora_nincs_kep(self):
        assert EditPreviewProvider().rendered_image("nincs-ilyen") is None


class TestAMasolasKepetTesz:
    def test_a_vagolap_a_szerkesztett_elonezet_kepe(self, szerkesztett, qt_app):
        vezerlo, szolgaltato, foto = szerkesztett

        assert vezerlo.copyRenderedImageToClipboard("fotoA") is True

        vagolapon = vezerlo._vagolap_kepe()
        assert vagolapon is not None and not vagolapon.isNull(), "nem került kép a vágólapra"
        elonezet = szolgaltato.requestImage(vezerlo._kulcs, None, None)
        assert (vagolapon.width(), vagolapon.height()) == (
            elonezet.width(),
            elonezet.height(),
        ), "a vágólap-kép mérete eltér a megjelenített előnézetétől"
        felvett = _qimage_tomb(vagolapon)
        mutatott = _qimage_tomb(elonezet)
        for sor, oszlop in ((0, 0), (0, 79), (30, 40), (59, 0), (59, 79), (17, 63)):
            assert felvett[sor, oszlop].tolist() == mutatott[sor, oszlop].tolist(), (
                f"a ({oszlop}, {sor}) képpont nem egyezik az előnézettel"
            )

    def test_a_vagolap_kep_a_szerkesztest_is_tartalmazza(self, szerkesztett):
        """A fekete-fehér effekt után a kép színtelen; a nyers fájl nem az."""
        vezerlo, _szolgaltato, foto = szerkesztett
        assert vezerlo.copyRenderedImageToClipboard("fotoA") is True

        felvett = _qimage_tomb(vezerlo._vagolap_kepe()).astype(int)
        szinkulonbseg = np.abs(felvett[..., 0] - felvett[..., 1]).max()
        assert szinkulonbseg <= 2, f"a vágólap-kép nem fekete-fehér (max eltérés {szinkulonbseg})"

        nyers = np.asarray(Image.open(foto).convert("RGB")).astype(int)
        assert np.abs(nyers[..., 0] - nyers[..., 1]).max() > 20, "a próbakép nem színes"

    def test_masik_foto_azonositojara_nem_ir_a_vagolapra(self, szerkesztett):
        """Elavult kérés (a néző már másik képen áll) nem vihet át rossz képet."""
        vezerlo, _szolgaltato, _foto = szerkesztett
        assert vezerlo.copyRenderedImageToClipboard("fotoB") is False
        assert vezerlo._vagolap_kepe() is None or vezerlo._vagolap_kepe().isNull()

    def test_munkamenet_nelkul_nem_ir_a_vagolapra(self, qt_app):
        vezerlo = EditController(EditPreviewProvider())
        assert vezerlo.copyRenderedImageToClipboard("fotoA") is False
        assert vezerlo.copyRenderedImageToClipboard("") is False

    def test_a_sikertelen_masolas_nem_uriti_ki_a_korabbi_kepet(self, szerkesztett):
        vezerlo, _szolgaltato, _foto = szerkesztett
        assert vezerlo.copyRenderedImageToClipboard("fotoA") is True
        elozo = _qimage_tomb(vezerlo._vagolap_kepe())

        assert vezerlo.copyRenderedImageToClipboard("fotoB") is False

        assert np.array_equal(_qimage_tomb(vezerlo._vagolap_kepe()), elozo)
