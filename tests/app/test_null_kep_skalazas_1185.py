"""Null képet ne próbáljunk átméretezni (#1185).

## A tulajdonos konzolnaplója (v0.8.29, Windows)

```
QImage::scaleWidth: Image is a null image
```

## A forrás

`edit_preview.py` `requestImage`: a `gpuprefix=1` / `gpulut=1` kérésekre a
placeholder-tartalék SZÁNDÉKOSAN nem vonatkozik (a QML-oldali
`GpuPointFilterPreview` ilyenkor egyszerűen nem kap forrást). Ha viszont
a kért kulcs még nincs a tárban, a `image` NULL marad — és a kód mégis
ráhívott a `scaledToWidth`-re, amit a Qt figyelmeztetéssel nyugtáz.

A figyelmeztetés magában ártalmatlan, de zajos: minden ilyen kérésnél
kiírja, és elfedi a valódi hibákat a naplóban.
"""

from PySide6.QtCore import QSize, qInstallMessageHandler
from PySide6.QtGui import QImage


def _figyelmeztetesek(hivas):
    """A Qt C++-oldali figyelmeztetéseit gyűjti a hívás idejére."""
    uzenetek: list[str] = []

    def kezelo(_tipus, _ctx, uzenet):
        uzenetek.append(uzenet)

    elozo = qInstallMessageHandler(kezelo)
    try:
        eredmeny = hivas()
    finally:
        qInstallMessageHandler(elozo)
    return eredmeny, uzenetek


class TestNullKep:
    def test_a_gpu_elonezet_null_kepe_nem_skalazodik(self, qt_app):
        from picasapy.app.edit_preview import EditPreviewProvider

        provider = EditPreviewProvider()
        kep, uzenetek = _figyelmeztetesek(
            lambda: provider.requestImage(
                "nincs-ilyen?gpuprefix=1", None, QSize(320, 0)
            )
        )
        assert isinstance(kep, QImage)
        assert kep.isNull(), "üres tárnál null képnek kell visszajönnie"
        assert not [u for u in uzenetek if "null image" in u], (
            "a Qt null képre panaszkodott: " + "; ".join(uzenetek)
        )

    def test_a_rendes_keres_tovabbra_is_placeholdert_kap(self, qt_app):
        """Megőrző: a NEM gpu-jelzős kérés placeholderre esik vissza, és
        azt szabályosan át is méretezi."""
        from picasapy.app.edit_preview import EditPreviewProvider

        provider = EditPreviewProvider()
        kep = provider.requestImage("nincs-ilyen", None, QSize(64, 0))
        assert not kep.isNull()
        assert kep.width() == 64
