"""#3729 — az alsó sáv nagyító-csúszkája a MÉRT `scaleslider` geometriával.

A #3709 (PR #3724) képes összevetése a tulajdonos 1920 px-es
képernyőképével a hatókörön kívül ezt találta: a `traySizeSlider` (könyvtár
mód) és a `zoomSlider` (néző mód) a `PicasaSlider` ALAPÉRTÉKÉVEL rajzol (4
képpontos sín, kerek 14×14 fogantyú), miközben a `respack.yt`
`scaleslider/sliderbase` 9 képpont vastag, a `scaleslider/thumb` pedig álló
16×22-es (`docs/specs/ui-audit-editor.md` 7.5, és az `EditorSlider.qml`
`scaleCsalad` ága, ami ugyanezt a mérést már alkalmazza a szerkesztő
paneljein).

Mindkét csúszka a `TrayBar.qml` `trayZoomGroup`-jának a TARTALMA — egy sáv,
módonként cserélt tartalommal (ld. a `TrayBar.qml` #2564 kommentjét), tehát
a két módnak UGYANAZT a geometriát kell mutatnia, különben a néző
megnyitásakor/bezárásakor a fogantyú láthatóan ugrana.
"""

from __future__ import annotations

import time

from PySide6.QtCore import QObject


def _elem(window, nev: str) -> QObject:
    obj = window.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található a kirajzolt fában"
    return obj


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        if feltetel():
            return True
        qt_app.processEvents()
        time.sleep(0.005)
    return False


class TestAKonyvtariCsuszkaGeometriaja:
    """`traySizeSlider` — a könyvtár-mód bélyegkép-mérete csúszkája."""

    def test_a_sav_9_kepponton_a_fogantyu_16x22(self, qml_app_module, qt_app):
        window, _, _ = qml_app_module
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.property("grooveThickness") == 9
        assert csuszka.property("handleWidth") == 16
        assert csuszka.property("handleHeight") == 22
        assert csuszka.property("handleRadius") == 3

    def test_a_foglalat_szelessege_valtozatlan_127(self, qml_app_module, qt_app):
        """A javításnak a #3709/#3602 mért réseit NEM szabad elmozdítania."""
        window, _, _ = qml_app_module
        csuszka = _elem(window, "traySizeSlider")
        assert csuszka.property("width") == 127
        assert csuszka.property("grooveInset") == 3


class TestANezoCsuszkaGeometriaja:
    """`zoomSlider` — a néző-mód nagyítás-hármasának csúszkája.

    Ugyanaz a `scaleslider` család, mint a könyvtári csúszkáé (mindkettő a
    `respack.yt` `scaleslider/sliderbase`+`thumb` párjára mutat vissza) —
    a fogantyúnak a két mód közt NEM szabad ugrálnia.
    """

    def test_a_sav_9_kepponton_a_fogantyu_16x22(self, qml_app, qt_app):
        window, _, _ = qml_app
        window.setProperty("viewerOpen", True)
        nezo = _elem(window, "photoViewer")
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()
        assert _var(
            qt_app, lambda: _elem(window, "zoomSlider").property("visible")
        )
        csuszka = _elem(window, "zoomSlider")
        assert csuszka.property("grooveThickness") == 9
        assert csuszka.property("handleWidth") == 16
        assert csuszka.property("handleHeight") == 22
        assert csuszka.property("handleRadius") == 3
