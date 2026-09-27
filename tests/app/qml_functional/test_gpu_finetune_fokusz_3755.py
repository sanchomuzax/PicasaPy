"""#3755: kettős nézetben a finomhangoló GPU élő-előnézete a FÓKUSZBAN lévő
félre illeszkedjen, ne fixen a jobb (`photo`) képre.

A hiba (mérve a #3741 (PR #3750) átnézésekor): a `GpuPointFilterPreview`
geometriája (`PhotoViewer.qml` ~2346) fixen a `photoKeret`/`photo`-hoz volt
kötve — bal fókusznál (`photoArea.fokuszKep === photoElotte`) a húzás alatt
ezért a NEM kijelölt jobb képre rajzolt volna, mihelyt a futtatókörnyezet
GPU-képes.

GPU-képtelen (offscreen/software) futtatókörnyezetben a réteg SOSEM válik
láthatóvá (ld. `test_gpu_finetune_preview.py`), tehát pixelszínnel nem
mérhető — a próbák ezért a KIRAJZOLT geometria-kötéseket nézik: a réteg
`x`/`y`/`width`/`height`/`rotation`/`scale` tulajdonságait a fókuszban lévő
fél SAJÁT elemeiből (`viewerImageElotte`/`viewerImageElotteKeret`, illetve
`viewerImage`/`viewerImageKeret`) számítjuk ki — FÜGGETLENÜL a vizsgált
implementáció `fokuszKep`/`fokuszKeret` aliasától.
"""

from __future__ import annotations

import pytest

from tests.app.qml_functional.test_kettos_nezet_fokusz_nagyitas_3741 import (
    _bal_fokusz,
    _jobb_fokusz,
    ket_kep,  # noqa: F401 — pytest-fixture
)
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import _gyerek


def _sajat_geometria(kep, keret) -> dict[str, float]:
    """A `photo`/`photoElotte` + a keretük abszolút geometriája a
    `photoArea` koordinátarendszerében — ugyanaz a képlet, mint a
    `GpuPointFilterPreview` implementációja, de a `fokuszKep`/`fokuszKeret`
    alias NÉLKÜL, közvetlenül a névvel elért elemekből."""
    szel = kep.property("width")
    mag = kep.property("height")
    pszel = kep.property("paintedWidth")
    pmag = kep.property("paintedHeight")
    return {
        "x": keret.property("x") + kep.property("x") + (szel - pszel) / 2,
        "y": keret.property("y") + kep.property("y") + (mag - pmag) / 2,
        "width": pszel,
        "height": pmag,
        "rotation": kep.property("rotation"),
        "scale": kep.property("scale"),
    }


def _gpu_geometria(window) -> dict[str, float]:
    reteg = _gyerek(window, "gpuFinetunePreview")
    return {kulcs: reteg.property(kulcs)
            for kulcs in ("x", "y", "width", "height", "rotation", "scale")}


class TestAGpuElonezetAFokuszbanLevoFelen:
    def test_bal_fokusznal_a_bal_kepre_illeszkedik(self, ket_kep, qt_app):  # noqa: F811
        window, _c, _e = ket_kep
        _bal_fokusz(window, qt_app)
        vart = _sajat_geometria(
            _gyerek(window, "viewerImageElotte"),
            _gyerek(window, "viewerImageElotteKeret"),
        )
        mert = _gpu_geometria(window)
        for kulcs in vart:
            assert mert[kulcs] == pytest.approx(vart[kulcs], abs=0.5), (
                f"{kulcs}: mért={mert[kulcs]} várt={vart[kulcs]} (bal fókusz)"
            )

    def test_jobb_fokusznal_a_jobb_kepre_illeszkedik(self, ket_kep, qt_app):  # noqa: F811
        window, _c, _e = ket_kep
        _jobb_fokusz(window, qt_app)
        vart = _sajat_geometria(
            _gyerek(window, "viewerImage"),
            _gyerek(window, "viewerImageKeret"),
        )
        mert = _gpu_geometria(window)
        for kulcs in vart:
            assert mert[kulcs] == pytest.approx(vart[kulcs], abs=0.5), (
                f"{kulcs}: mért={mert[kulcs]} várt={vart[kulcs]} (jobb fókusz)"
            )

    def test_bal_fokusznal_nagyitva_a_reteg_a_nagyitast_koveti(
        self, ket_kep, qt_app  # noqa: F811
    ):
        """A hiba tiszta jele: a réteg `scale`-je a fixen kötött `photo`
        (bal fókusznál mindig 1,0) helyett a TÉNYLEGESEN nagyított bal
        képet (`photoElotte`) kövesse."""
        window, _c, _e = ket_kep
        nezo = _bal_fokusz(window, qt_app)
        nezo.setProperty("zoomValue", 0.8)
        qt_app.processEvents()
        elotte = _gyerek(window, "viewerImageElotte")
        assert elotte.property("scale") > 1.05
        reteg = _gyerek(window, "gpuFinetunePreview")
        assert reteg.property("scale") == pytest.approx(
            elotte.property("scale"), abs=0.01
        )
