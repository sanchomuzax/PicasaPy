"""`Nézet ▸ Megjelenítési mód ▸ Projektor / LCD / Lineáris gamma` — a
MENÜBŐL — #1577 és #1578.

A képpont-szabályt a `tests/render/test_display_modes_1577_1578.py`, a
szolgáltató-oldali szerződéseket a
`tests/app/test_display_mode_sotetites_gamma_1577_1578.py` őrzi. Ez a fájl
a **bekötést** méri: a felhasználó a menütételre kattint, és a
megjelenített kép ettől — és csak ettől — változik meg.

⚠️ Miért a menüből, és miért nem a `setDisplayMode()` közvetlen hívásával?
Mert a lánc három ízülete közül bármelyik szétcsúszhat úgy, hogy a
vezérlő-szintű teszt zöld marad: (1) a menütétel nem hívja a beállítót,
(2) a beállító változása nem jut el a kép-szolgáltatóig, (3) a szolgáltató
megkapja, de a QML nem kéri újra a képet. A #1454 a (2)-esen bukott meg.

A kattintás a #1575/#1576 tesztjének mintája: `toggle()` + `triggered` — a
puszta `triggered` épp a `checked` imperatív átbillentését hagyná
méretlenül (a „checkable + kötött checked" rádió-csapda, #1464/#1468).
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtGui import QImage

#: A menütételek `objectName`-jei (a #1575 névsorából).
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
TETEL_LCD = "menuViewDisplayModeLcd"
TETEL_LINEAR = "menuViewDisplayModeLinearGamma"
#: Kontroll: a 24 bites mód SOHA nem mozdít képpontot (spec 5.1).
TETEL_NORMAL = "menuViewDisplayModeNormal"

FEHER = (255, 255, 255)
KOZEPSZURKE = (128, 128, 128)
FEKETE = (0, 0, 0)

#: A várt színhalmazok KIÍRVA — nem a termék konstansaiból számolva.
#: projektor `(c·220)>>8`: 255→219, 128→110, 0→0
VART_PROJEKTOR = {(219, 219, 219), (110, 110, 110), (0, 0, 0)}
#: lcd `(c·246)>>8`: 255→245, 128→123, 0→0
VART_LCD = {(245, 245, 245), (123, 123, 123), (0, 0, 0)}
#: lineáris gamma, a spec 5.9 táblájából: 255→255, 128→158, 0→0
VART_LINEAR = {(255, 255, 255), (158, 158, 158), (0, 0, 0)}

ESETEK = (
    (TETEL_PROJEKTOR, "projector", VART_PROJEKTOR),
    (TETEL_LCD, "lcd", VART_LCD),
    (TETEL_LINEAR, "linear", VART_LINEAR),
)


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _kattint(root, name):
    """A menütétel aktiválása — a VALÓDI kattintás mindkét lépése."""
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _kep_tombbe(image) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    stride = converted.bytesPerLine()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, stride))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _szinek(tomb: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in tomb.reshape(-1, 3)}


@pytest.fixture
def savos(qml_app, qt_app, tmp_path):
    """Három sávos (fehér/középszürke/fekete) kép nyitott szerkesztésben.

    Visszaadja: `(window, controller, edit_controller, keres())`. A
    szolgáltatót a bekötött `EditController`-től kérjük el, nem külön
    példányosítjuk — épp az a kérdés, hogy a MOTORBA kötött lánc működik-e.
    """
    import cv2

    window, controller, engine = qml_app
    edit_controller = engine.rootContext().contextProperty("editController")
    assert edit_controller is not None, "az editController nincs a QML-kontextusban"
    provider = edit_controller._provider

    path = tmp_path / "savok.png"
    kep = np.zeros((4, 6, 3), dtype=np.uint8)
    kep[0, :] = 255
    kep[1, :] = 128
    assert cv2.imwrite(str(path), kep)

    edit_controller.beginEdit("sav", str(path))
    qt_app.processEvents()

    def keres() -> set[tuple[int, int, int]]:
        return _szinek(_kep_tombbe(provider.requestImage("sav", None, None)))

    return window, controller, edit_controller, keres


class TestMenubolVezerelve:
    def test_kattintas_elott_erintetlen(self, savos):
        _window, controller, _edit, keres = savos
        assert controller.property("displayMode") == "auto"
        assert keres() == {FEHER, KOZEPSZURKE, FEKETE}

    @pytest.mark.parametrize("tetel,mod,vart", ESETEK)
    def test_a_menupontra_kattintva_valtozik_a_kep(
        self, savos, qt_app, tetel, mod, vart
    ):
        window, controller, _edit, keres = savos
        _kattint(window, tetel)
        qt_app.processEvents()
        assert controller.property("displayMode") == mod
        assert keres() == vart, (
            f"a(z) {tetel!r} menüpontra kattintva a kép nem a mért szabály "
            "szerint változott — a lánc (menü → vezérlő → kép-szolgáltató) "
            "valahol megszakadt"
        )

    @pytest.mark.parametrize("tetel,mod,_vart", ESETEK)
    def test_a_kattintas_ujrakerteti_a_kepet_a_qmllel(
        self, savos, qt_app, tetel, mod, _vart
    ):
        """A `previewSource` cache-bustere lép — enélkül a QML a régi képet
        tartaná meg, és a felhasználó semmit nem látna a váltásból."""
        window, _controller, edit, _keres = savos
        elotte = edit.property("previewSource")
        _kattint(window, tetel)
        qt_app.processEvents()
        assert edit.property("previewSource") != elotte

    @pytest.mark.parametrize("tetel,mod,_vart", ESETEK)
    def test_a_24_bitesre_visszavaltva_eltunik_a_hatas(
        self, savos, qt_app, tetel, mod, _vart
    ):
        """A kikapcsolás azonnal visszaadja az eredeti nézetet."""
        window, controller, _edit, keres = savos
        _kattint(window, tetel)
        qt_app.processEvents()
        assert keres() != {FEHER, KOZEPSZURKE, FEKETE}

        _kattint(window, TETEL_NORMAL)
        qt_app.processEvents()
        assert controller.property("displayMode") == "normal"
        assert keres() == {FEHER, KOZEPSZURKE, FEKETE}, (
            f"a(z) {mod!r} hatása a mód elhagyása után is a képen maradt"
        )

    def test_a_modok_kizarjak_egymast_a_menubol(self, savos, qt_app):
        """Kattintással váltva a hatás CSERÉLŐDIK, nem halmozódik."""
        window, controller, _edit, keres = savos
        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert keres() == VART_PROJEKTOR

        _kattint(window, TETEL_LINEAR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "linear"
        assert keres() == VART_LINEAR, (
            "a gamma a sötétített képre rakódott rá — a menütételek nem "
            "kizáró csoportként viselkednek a képpont-úton"
        )

        _kattint(window, TETEL_LCD)
        qt_app.processEvents()
        assert keres() == VART_LCD

    def test_a_24_bites_menupont_nem_mozdit_keppontot(self, savos, qt_app):
        """Kontroll: nem MINDEN mód hat — a hatás a tételhez kötött."""
        window, _controller, _edit, keres = savos
        _kattint(window, TETEL_NORMAL)
        qt_app.processEvents()
        assert keres() == {FEHER, KOZEPSZURKE, FEKETE}
