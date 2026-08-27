"""`Nézet ▸ Megjelenítési mód ▸ Túlcsordult képpontok` — a MENÜBŐL — #1576.

A képpont-szabályt a `tests/render/test_display_modes_1576.py`, a
szolgáltató-oldali szerződéseket a
`tests/app/test_display_mode_overflow_1576.py` őrzi. Ez a fájl a
**bekötést** méri: a felhasználó a menütételre kattint, és a megjelenített
kép ettől — és csak ettől — kap jelölést.

⚠️ Miért a menüből, és miért nem a `setDisplayMode()` közvetlen hívásával?
Mert a lánc három ízülete közül bármelyik szétcsúszhat úgy, hogy a
vezérlő-szintű teszt zöld marad: (1) a menütétel nem hívja a beállítót,
(2) a beállító változása nem jut el a kép-szolgáltatóig
(`wire_display_mode` elmaradt az `application.py`-ból vagy a conftestből),
(3) a szolgáltató megkapja, de a QML nem kéri újra a képet, mert a
`previewSource` URL-je nem változott. A #1454 pontosan a (2)-es ízületen
bukott meg — beégetett érték és regisztrálatlan vezérlő között két „kész"
végpont.

A kattintás a #1575 tesztjének mintája: `toggle()` + `triggered` — a puszta
`triggered` épp a `checked` imperatív átbillentését hagyná méretlenül.
"""

from __future__ import annotations

import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, Qt
from PySide6.QtGui import QImage

from picasapy.render.display_modes import OVERFLOW_MARK_RGB

#: A jelölőszín KIÍRVA, a specből (`0xFFFF7F7F`) — nem a termék-konstansról
#: olvasva, hogy annak elrontása is bukást okozzon.
JELOLO = (255, 127, 127)

#: A menütétel `objectName`-je (a #1575 névsorából).
TETEL = "menuViewDisplayModeOverflow"
#: Kontroll: egy másik, képpontot NEM mozdító mód. SZÁNDÉKOSAN a 24 bites
#: (spec 5.1: nincs átalakító) — a korábbi „Projektor mód" a #1577 óta
#: sötétít, tehát kontrollnak alkalmatlan lett.
MASIK_TETEL = "menuViewDisplayModeNormal"
MASIK_MOD = "normal"

FEHER = (255, 255, 255)


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
def kifeheredett(qml_app, qt_app, tmp_path):
    """Valódi, kifehéredett foltot tartalmazó kép nyitott szerkesztésben.

    Visszaadja: `(window, controller, edit_controller, provider, keres())`.
    A szolgáltatót a bekötött `EditController`-től kérjük el, nem külön
    példányosítjuk — épp az a kérdés, hogy a MOTORBA kötött lánc működik-e.
    """
    import cv2

    window, controller, engine = qml_app
    edit_controller = engine.rootContext().contextProperty("editController")
    assert edit_controller is not None, "az editController nincs a QML-kontextusban"
    provider = edit_controller._provider

    path = tmp_path / "kifeheredett.png"
    kep = np.zeros((4, 6, 3), dtype=np.uint8)
    kep[0, :] = 255   # kiégett sor
    kep[1, :] = 254   # majdnem fehér — kontroll a tűrés hiányára
    assert cv2.imwrite(str(path), kep)

    edit_controller.beginEdit("kif", str(path))
    qt_app.processEvents()

    def keres() -> set[tuple[int, int, int]]:
        return _szinek(_kep_tombbe(provider.requestImage("kif", None, None)))

    return window, controller, edit_controller, provider, keres


class TestMenubolVezerelve:
    def test_a_termek_konstansa_a_speces_szin(self, qml_app):
        assert OVERFLOW_MARK_RGB == JELOLO

    def test_kattintas_elott_nincs_jeloles(self, kifeheredett):
        _window, controller, _edit, _provider, keres = kifeheredett
        assert controller.property("displayMode") == "auto"
        szinek = keres()
        assert FEHER in szinek
        assert JELOLO not in szinek

    def test_a_menupontra_kattintva_jelolodik_a_kep(self, kifeheredett, qt_app):
        window, controller, _edit, _provider, keres = kifeheredett
        _kattint(window, TETEL)
        qt_app.processEvents()
        assert controller.property("displayMode") == "overflow"
        szinek = keres()
        assert JELOLO in szinek, (
            "a menüpontra kattintva a kép jelöletlen maradt — a lánc "
            "(menü → vezérlő → kép-szolgáltató) valahol megszakadt"
        )
        assert FEHER not in szinek
        assert (254, 254, 254) in szinek, "a 254-es sor is átfestődött"

    def test_a_kattintas_ujrakerteti_a_kepet_a_qmllel(self, kifeheredett, qt_app):
        """A `previewSource` cache-bustere lép — enélkül a QML a régi képet
        tartaná meg, és a felhasználó semmit nem látna a váltásból."""
        window, _controller, edit, _provider, _keres = kifeheredett
        elotte = edit.property("previewSource")
        _kattint(window, TETEL)
        qt_app.processEvents()
        assert edit.property("previewSource") != elotte

    def test_masik_modra_valtva_eltunik_a_jeloles(self, kifeheredett, qt_app):
        """A kikapcsolás azonnal visszaadja az eredeti nézetet."""
        window, controller, _edit, _provider, keres = kifeheredett
        _kattint(window, TETEL)
        qt_app.processEvents()
        assert JELOLO in keres()

        _kattint(window, MASIK_TETEL)
        qt_app.processEvents()
        assert controller.property("displayMode") == MASIK_MOD
        szinek = keres()
        assert JELOLO not in szinek, (
            "a jelölés a mód elhagyása után is a képen maradt"
        )
        assert FEHER in szinek

    def test_a_szomszedos_menupont_nem_jelol(self, kifeheredett, qt_app):
        """Kontroll: nem MINDEN mód fest — a jelölés a tételhez kötött."""
        window, _controller, _edit, _provider, keres = kifeheredett
        _kattint(window, MASIK_TETEL)
        qt_app.processEvents()
        assert JELOLO not in keres()
