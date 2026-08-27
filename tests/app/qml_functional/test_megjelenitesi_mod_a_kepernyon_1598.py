"""A megjelenítési mód a KIRAJZOLT képen — #1598 (felhasználói jelentés).

⚠️ Ez a fájl SZÁNDÉKOSAN többet mér, mint a #1576 tesztje. Ott a
`provider.requestImage(...)` visszaadott képét nézzük — vagyis azt, hogy a
szolgáltató jól dolgozik-e. A felhasználó viszont nem a szolgáltatót látja,
hanem a **kirajzolt ablakot**. A #1598-ban pontosan ez a különbség vált
kérdéssé: a mag bizonyítottan jó volt, a tulajdonos mégis azt jelentette,
hogy „egyáltalán nem működik egyik sem".

Ezért itt a `window.grabWindow()` felvételének képpontjait olvassuk vissza:
a lánc MINDEN ízülete benne van — menütétel → vezérlő → szolgáltató →
`previewSource` cache-buster → QML `Image` újratöltés → kirajzolás.

## Miért folt, és nem az egész ablak?

A felület krómja (keretek, élsimított szegélyek) az egész ablakon néhány
tucat képpontot ad minden szürkeárnyalathoz — mérve: az 1280×800-as
tesztablakban 11 db `(171, 171, 171)` már alaphelyzetben is van. Egész
ablakos számlálásnál ezért csak küszöbös állítást lehetne írni. A
`viewerImage` kirajzolt téglalapjából vett folt viszont **egyetlen színű**
(mérve), így az állítások pontosak: a folt minden képpontja a várt szín.

## A várt színek KIÍRT LITERÁLOK

Nem a termék konstansaiból olvasva — a spec egész-aritmetikájából
kiszámolva, hogy a konstans elrontása is bukást okozzon:

* Projektor mód: `200 · 220 >> 8 = 171`
* Túlcsordulás:  `(255, 255, 255) → (255, 127, 127)`

## A visszaesési ág (a fájl második osztálya)

A `PhotoViewer.qml` fotó-`Image`-e csak akkor kéri a képet az `editpreview`
szolgáltatóból, ha `editCtl.previewSource !== ""`; egyébként a NYERS fájl
URL-jére esik vissza, amin a mód nem látszik — mérve (#1598): a váltás
ilyenkor némán elveszik. A `beginEdit` a néző megnyitásakor lefut, tehát a
visszaesés a rendes úton nem áll elő; a munkamenet viszont kívülről
(`endEdit`) megszüntethető, és a felhasználó ilyenkor is a menüből vált
módot. Az őr ezt az állapotot ELŐÁLLÍTJA, és megköveteli, hogy a mód így is
a képernyőre jusson.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

#: A menütételek `objectName`-jei (a #1575 névsorából).
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
TETEL_TULCSORDULAS = "menuViewDisplayModeOverflow"
TETEL_24BIT = "menuViewDisplayModeNormal"

#: A próbakép egyenletes háttere és a felső, tisztán fehér sávja.
HATTER = (200, 200, 200)
FEHER = (255, 255, 255)
#: `200 · 220 >> 8` — KIÍRVA, nem a `PROJECTOR_MULTIPLIER`-ből számolva.
PROJEKTOROS_HATTER = (171, 171, 171)
#: A túlcsordulás-jelölő (`0xFFFF7F7F`) — KIÍRVA.
JELOLO = (255, 127, 127)

#: Meddig várunk arra, hogy a kirajzolt kép felvegye a várt színt. A
#: háttérszálas előnézet-renderelés terhelt, négymagos gépen lassabb, mint a
#: kattintás; a puszta „két egymást követő azonos felvétel" figyelés TÚL
#: KORÁN áll meg (a még nem frissült kép is stabil). A határidő lejárta után
#: a hívó ugyanúgy állít — az őr foga nem vész el, csak a türelme fogy el.
HATARIDO = 10.0


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _kattint(root, name):
    """A menütétel aktiválása — a valódi kattintás mindkét lépése (#1575)."""
    item = _child(root, name)
    if item.property("checkable"):
        QMetaObject.invokeMethod(item, "toggle", Qt.ConnectionType.DirectConnection)
    QMetaObject.invokeMethod(item, "triggered", Qt.ConnectionType.DirectConnection)


def _tombbe(image: QImage) -> np.ndarray:
    converted = image.convertToFormat(QImage.Format.Format_RGB888)
    width, height = converted.width(), converted.height()
    raw = np.frombuffer(bytes(converted.constBits()), dtype=np.uint8)
    raw = raw.reshape((height, converted.bytesPerLine()))
    return raw[:, : width * 3].reshape((height, width, 3)).copy()


def _foto_teglalap(window) -> tuple[int, int, int, int]:
    """A `viewerImage` ténylegesen KIRAJZOLT téglalapja az ablakban.

    A `PreserveAspectFit` miatt a kirajzolt kép kisebb a befoglaló doboznál
    (letterbox), ezért a `paintedWidth`/`paintedHeight` a mérvadó — a
    `cropOverlay`/`facesOverlay` ugyanezt a geometriát használja.
    """
    item = _child(window, "viewerImage")
    doboz_szeles = float(item.property("width"))
    doboz_magas = float(item.property("height"))
    szeles = float(item.property("paintedWidth"))
    magas = float(item.property("paintedHeight"))
    assert szeles > 0 and magas > 0, "a néző nem rajzol ki képet"
    bal_felso = item.mapToScene(
        QPointF((doboz_szeles - szeles) / 2, (doboz_magas - magas) / 2)
    )
    return int(bal_felso.x()), int(bal_felso.y()), int(szeles), int(magas)


def _folt(tomb: np.ndarray, teglalap, felul: float, alul: float) -> np.ndarray:
    """Vízszintesen a középső 60 %, függőlegesen a megadott sáv."""
    x, y, szeles, magas = teglalap
    return tomb[
        y + int(magas * felul) : y + int(magas * alul),
        x + int(szeles * 0.2) : x + int(szeles * 0.8),
    ]


#: A próbakép felső negyede tisztán fehér — a jelölés ott látszik.
FEHER_SAV = (0.05, 0.20)
#: A kép alsó kétharmada egyenletes háttér — a sötétítés ott látszik.
HATTER_SAV = (0.45, 0.90)


def _szinek(folt: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in np.unique(folt.reshape(-1, 3), axis=0)}


def _varva_szinek(window, qt_app, teglalap, sav, vart) -> set:
    """A folt színhalmaza — legfeljebb `HATARIDO`-ig várva a `vart` alakra.

    A `vart` csak a várakozás LEÁLLÍTÁSÁRA szolgál; az állítást a hívó
    végzi a visszaadott halmazon. Így a határidő lejárta nem hallgat el
    semmit: a hívó a tényleges (rossz) színhalmazt kapja meg.
    """
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        szinek = _szinek(_folt(_tombbe(window.grabWindow()), teglalap, *sav))
        if szinek == vart or time.monotonic() > hatarido:
            return szinek
        time.sleep(0.02)


@pytest.fixture
def nyitott_nezo(qml_app, qt_app, tmp_path):
    """Nyitott nagy néző egy egyenletes, ELLENŐRZÖTT próbaképen.

    A könyvtár `a.jpg`-jét felülírjuk: 200-as háttér + felső, tisztán fehér
    sáv. Így mindkét mért mód hatásának van hova látszania — a sötétítésnek
    a háttéren, a túlcsordulás-jelölésnek a fehér sávon.
    """
    window, controller, engine = qml_app
    edit_controller = engine.rootContext().contextProperty("editController")
    assert edit_controller is not None, "az editController nincs a QML-kontextusban"

    kep = np.full((160, 320, 3), 200, dtype=np.uint8)
    kep[:40, :] = 255
    assert cv2.imwrite(
        str(tmp_path / "kepek" / "a.jpg"), kep, [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    )

    window.setProperty("viewerOpen", True)
    viewer = _child(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    # a fotóterület geometriája csak a tördelés után áll be
    teglalap = None
    hatarido = time.monotonic() + HATARIDO
    while teglalap is None and time.monotonic() < hatarido:
        qt_app.processEvents()
        QTest.qWait(20)
        if float(_child(window, "viewerImage").property("paintedWidth")) > 0:
            teglalap = _foto_teglalap(window)
    assert teglalap is not None, "a néző nem rajzolt ki képet"
    return window, controller, edit_controller, teglalap


class TestKirajzoltKep:
    """A menüből váltott mód a KIRAJZOLT ablak képpontjain."""

    def test_a_nezo_az_editpreview_bol_rajzol(self, nyitott_nezo):
        """Előfeltétel: nyitott nézőben a fotó forrása a szolgáltató URL-je.

        Ha ez `file://`-ra vált, a mód a képernyőre SEM jut el — a #1598
        GY-2 gyanúja pontosan ez volt.
        """
        window, _controller, _edit, _teglalap = nyitott_nezo
        forras = str(_child(window, "viewerImage").property("source"))
        assert "image://editpreview/" in forras, forras

    def test_alaphelyzetben_nincs_atalakitas(self, nyitott_nezo, qt_app):
        window, controller, _edit, teglalap = nyitott_nezo
        assert controller.property("displayMode") == "auto"
        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {HATTER}
        ) == {HATTER}
        assert _varva_szinek(
            window, qt_app, teglalap, FEHER_SAV, {FEHER}
        ) == {FEHER}

    def test_projektor_mod_sotetit_a_kepernyon(self, nyitott_nezo, qt_app):
        window, controller, _edit, teglalap = nyitott_nezo
        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {HATTER}
        ) == {HATTER}

        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "projector"

        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {PROJEKTOROS_HATTER}
        ) == {PROJEKTOROS_HATTER}, (
            "a Projektor módra kattintva a KIRAJZOLT kép nem sötétedett — a "
            "lánc a szolgáltató és a képernyő között szakadt meg"
        )

    def test_tulcsordulas_jelolodik_a_kepernyon(self, nyitott_nezo, qt_app):
        window, controller, _edit, teglalap = nyitott_nezo
        _kattint(window, TETEL_TULCSORDULAS)
        qt_app.processEvents()
        assert controller.property("displayMode") == "overflow"

        assert _varva_szinek(
            window, qt_app, teglalap, FEHER_SAV, {JELOLO}
        ) == {JELOLO}, (
            "a Túlcsordult képpontok módra kattintva a KIRAJZOLT képen nem "
            "jelent meg a jelölőszín"
        )
        # a nem telített háttér érintetlen — nincs tűrés, nincs mellékhatás
        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {HATTER}
        ) == {HATTER}

    def test_a_modot_elhagyva_visszaall_a_kep(self, nyitott_nezo, qt_app):
        window, _controller, _edit, teglalap = nyitott_nezo
        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {PROJEKTOROS_HATTER}
        ) == {PROJEKTOROS_HATTER}

        _kattint(window, TETEL_24BIT)
        qt_app.processEvents()
        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {HATTER}
        ) == {HATTER}, "a mód elhagyása után a sötétítés a képen maradt"


class TestVisszaesesiAg:
    """Szerkesztési munkamenet nélkül sem nyelheti el a néző a módot (#1598).

    Az állapotot ELŐÁLLÍTJUK (`endEdit()`), mert a rendes úton — a néző
    megnyitása mindig `beginEdit`-tel jár — Linuxon nem sikerült elérni.
    Az őr így is valódi: a `PhotoViewer.qml` visszaesési ága LÉTEZIK, és
    mérve (#1598) a nyers fájlt rajzolja ki, amin a mód nem látszik.
    """

    def test_szerkesztes_nelkul_is_latszik_a_mod(self, nyitott_nezo, qt_app):
        window, controller, edit, teglalap = nyitott_nezo
        edit.endEdit()
        qt_app.processEvents()
        assert edit.property("previewSource") == "", (
            "a próba előfeltétele nem áll fenn: a munkamenet nem zárult le"
        )

        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "projector"

        assert _varva_szinek(
            window, qt_app, teglalap, HATTER_SAV, {PROJEKTOROS_HATTER}
        ) == {PROJEKTOROS_HATTER}, (
            "a néző szerkesztési munkamenet nélkül a NYERS fájlt rajzolta ki, "
            "és némán elnyelte a megjelenítési módot"
        )
