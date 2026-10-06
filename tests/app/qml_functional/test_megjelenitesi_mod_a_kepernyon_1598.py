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
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSize, Qt, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlComponent, qmlEngine
from PySide6.QtTest import QTest

from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_kettos_nezet_gombsor_helye_3663 import (
    _ab_modba,
    _kep_teglalap,
)

#: A menütételek `objectName`-jei (a #1575 névsorából).
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
TETEL_TULCSORDULAS = "menuViewDisplayModeOverflow"
TETEL_24BIT = "menuViewDisplayModeNormal"
TETEL_16BIT = "menuViewDisplayMode16Bit"

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


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _lathato_elem(window, feltetel):
    sor = [window.contentItem().parentItem() or window.contentItem()]
    while sor:
        elem = sor.pop()
        if elem.isVisible() and feltetel(elem):
            return elem
        sor.extend(elem.childItems())
    return None


def _valodi_modkattintas(window, qt_app, nev: str) -> None:
    """A Nézet menün át, QTest egéreseménnyel választja ki a megadott módot."""

    def kattints(elem) -> None:
        assert elem is not None and elem.width() > 0 and elem.height() > 0
        pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
        QTest.mouseClick(
            window,
            Qt.MouseButton.LeftButton,
            Qt.KeyboardModifier.NoModifier,
            QPoint(round(pont.x()), round(pont.y())),
        )
        qt_app.processEvents()

    nezet_fejlec = _lathato_elem(
        window,
        lambda elem: "MenuBarItem" in elem.metaObject().className()
        and elem.property("text") == "&View",
    )
    assert nezet_fejlec is not None, "a Nézet menü fejléce nem látható"
    kattints(nezet_fejlec)

    display_menu = _lathato_elem(
        window,
        lambda elem: elem.property("text") == "&Display Mode",
    )
    assert display_menu is not None, "a Megjelenítési mód almenü nem jelent meg"
    kattints(display_menu)

    mode_item = None

    def mode_lathato() -> bool:
        nonlocal mode_item
        mode_item = _lathato_elem(
            window,
            lambda elem: elem.property("text") == "&16-bit (dithered)",
        )
        return mode_item is not None

    assert _varj(qt_app, mode_lathato), f"a(z) {nev} menüpont nem jelent meg"
    kattints(mode_item)


def _dict_folt(tomb: np.ndarray, teglalap: dict, felul: float, alul: float) -> np.ndarray:
    """Mint `_folt`, csak a `_kep_teglalap` (bal/fent/jobb/lent kulcsos)
    alakján — a kettős nézet két fele ezt a formát adja vissza (#3837)."""
    bal, fent, jobb, lent = (
        teglalap["bal"],
        teglalap["fent"],
        teglalap["jobb"],
        teglalap["lent"],
    )
    szeles = jobb - bal
    magas = lent - fent
    return tomb[
        int(fent + magas * felul) : int(fent + magas * alul),
        int(bal + szeles * 0.2) : int(bal + szeles * 0.8),
    ]


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


def _foto_teglalap(window) -> tuple[float, float, float, float]:
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
    return bal_felso.x(), bal_felso.y(), szeles, magas


def _folt(tomb: np.ndarray, teglalap, felul: float, alul: float) -> np.ndarray:
    """Vízszintesen a középső 60 %, függőlegesen a megadott sáv."""
    x, y, szeles, magas = teglalap
    return tomb[
        int(y + magas * felul) : int(y + magas * alul),
        int(x + szeles * 0.2) : int(x + szeles * 0.8),
    ]


#: A próbakép felső negyede tisztán fehér — a jelölés ott látszik.
FEHER_SAV = (0.05, 0.20)
#: A kép alsó kétharmada egyenletes háttér — a sötétítés ott látszik.
HATTER_SAV = (0.45, 0.90)


def _szinek(folt: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in np.unique(folt.reshape(-1, 3), axis=0)}


def _spec_szemcsezes(rgb: np.ndarray) -> np.ndarray:
    """Független, egyszerű referencia a spec 5.3 + 5.3/b képleteire."""
    allapot = [0] * 624
    allapot[0] = 0x80AE2D6C
    for index in range(1, 624):
        elozo = allapot[index - 1]
        allapot[index] = (0x0019660D * (elozo ^ (elozo >> 30)) + index) & 0xFFFFFFFF
    index = 624
    eredmeny = rgb.copy()

    for y in range(rgb.shape[0]):
        for x in range(rgb.shape[1]):
            if index == 624:
                for i in range(624):
                    osszefuzes = (allapot[i] & 0x80000000) | (
                        allapot[(i + 1) % 624] & 0x7FFFFFFF
                    )
                    allapot[i] = (
                        allapot[(i + 397) % 624]
                        ^ (osszefuzes >> 1)
                        ^ (0x9908B0DF if osszefuzes & 1 else 0)
                    ) & 0xFFFFFFFF
                index = 0

            tempered = allapot[index]
            index += 1
            tempered ^= tempered >> 11
            tempered = (tempered ^ ((tempered & 0xFF3A58AD) << 7)) & 0xFFFFFFFF
            tempered = (tempered ^ ((tempered & 0xFFFFDF8C) << 15)) & 0xFFFFFFFF
            tempered ^= tempered >> 18

            eredmeny[y, x, 0] = min(255, int(rgb[y, x, 0]) + ((tempered >> 16) & 7))
            eredmeny[y, x, 1] = min(255, int(rgb[y, x, 1]) + ((tempered >> 8) & 3))
            eredmeny[y, x, 2] = min(255, int(rgb[y, x, 2]) + (tempered & 7))
    return eredmeny


def _varhato_szemcse_kepernyo(
    window, forras_ut: str
) -> QImage:
    """A provider kimenetének független, képpontos specifikációs referenciája.

    A provider a forrást a QML Image tényleges `sourceSize`-ába méretezi,
    majd a módot a méretezett képre alkalmazza.
    """
    fromas = QImage(forras_ut)
    item = _child(window, "viewerImage")
    kert_meret = item.property("sourceSize")
    doboz = fromas.scaled(
        QSize(kert_meret.width(), kert_meret.height()),
        Qt.AspectRatioMode.KeepAspectRatio,
        Qt.TransformationMode.SmoothTransformation,
    )
    szemcsezett = _spec_szemcsezes(_tombbe(doboz))
    eredmeny = QImage(
        szemcsezett.data,
        szemcsezett.shape[1],
        szemcsezett.shape[0],
        szemcsezett.strides[0],
        QImage.Format.Format_RGB888,
    ).copy()
    assert np.any(szemcsezett != _tombbe(doboz)), "a próbakép nem mutatja a szemcsézés hatását"
    return eredmeny


def _referencia_image(window, kep: QImage, tmp_path, qt_app):
    """Ugyanazon a QML Image-útvonalon rajzolja ki a független referenciát."""
    ut = tmp_path / "dither16-spec.png"
    assert kep.save(str(ut), "PNG")
    eredeti = _child(window, "viewerImage")
    engine = qmlEngine(eredeti)
    assert engine is not None
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
Item {
    objectName: "dither16ReferenceRoot"
    Image {
        objectName: "dither16ReferenceImage"
        anchors.fill: parent
        fillMode: Image.PreserveAspectFit
        asynchronous: false
        autoTransform: true
    }
}""",
        QUrl(),
    )
    root = component.create(engine.rootContext())
    assert root is not None, "a referencia-QML Image nem jött létre: " + str(component.errors())
    root.setParent(window)
    root.setParentItem(eredeti.parentItem())
    root.setProperty("x", eredeti.property("x"))
    root.setProperty("y", eredeti.property("y"))
    root.setProperty("width", eredeti.property("width"))
    root.setProperty("height", eredeti.property("height"))
    root.setProperty("z", eredeti.property("z"))
    referencia = root.findChild(QObject, "dither16ReferenceImage")
    assert referencia is not None
    referencia.setProperty("source", QUrl.fromLocalFile(str(ut)))
    referencia.setProperty("visible", False)

    hatarido = time.monotonic() + HATARIDO
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if float(referencia.property("implicitWidth")) > 0:
            break
        time.sleep(0.02)
    assert float(referencia.property("implicitWidth")) > 0, "a referencia-kép nem töltődött be"
    return root, referencia


def _kirajzolt_szemcse_hibak(window, referencia) -> tuple[int, int]:
    """A kattintás utáni képet azonos QML-kirajzolású specifikációs képpel veti össze."""
    eredeti = _child(window, "viewerImage")
    gyoker, kep = referencia
    eredeti.setProperty("visible", True)
    kep.setProperty("visible", False)
    elvart_ablak = _tombbe(window.grabWindow())
    eredeti.setProperty("visible", False)
    gyoker.setProperty("visible", True)
    kep.setProperty("visible", True)
    tenyleges_ablak = _tombbe(window.grabWindow())
    gyoker.setProperty("visible", False)
    eredeti.setProperty("visible", True)

    x, y, painted_width, painted_height = _foto_teglalap(window)
    meret_x = tenyleges_ablak.shape[1] / float(window.width())
    meret_y = tenyleges_ablak.shape[0] / float(window.height())
    bal, jobb = int((x + painted_width * 0.1) * meret_x), int(
        (x + painted_width * 0.9) * meret_x
    )
    fent, lent = int((y + painted_height * 0.45) * meret_y), int(
        (y + painted_height * 0.75) * meret_y
    )
    tenyleges = tenyleges_ablak[fent:lent, bal:jobb].astype(np.int16)
    vart = elvart_ablak[fent:lent, bal:jobb].astype(np.int16)
    assert tenyleges.shape == vart.shape, "a képernyőreferenciák mérete eltér"
    elteres = np.abs(tenyleges - vart)
    hibas_pixelek = np.any(elteres > 3, axis=2)
    return int(np.count_nonzero(hibas_pixelek)), int(elteres.max(initial=0))


def _varja_a_kirajzolt_szemcset(window, qt_app, referencia) -> tuple[int, int]:
    """Határidővel vár a tényleges képernyőképpontokra, fix várakozás nélkül."""
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        hibak = _kirajzolt_szemcse_hibak(window, referencia)
        if hibak[0] == 0 or time.monotonic() >= hatarido:
            return hibak
        time.sleep(0.02)


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

    @pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
    def test_16_bites_kattintasra_a_nezo_kepet_szemcsezi(
        self, nyitott_nezo, qt_app, tmp_path, magassag_elteres
    ):
        window, controller, _edit, _teglalap = nyitott_nezo
        window.setHeight(window.height() + magassag_elteres)
        hatarido = time.monotonic() + HATARIDO
        while time.monotonic() < hatarido:
            qt_app.processEvents()
            if _child(window, "viewerImage").property("paintedWidth"):
                break

        _valodi_modkattintas(window, qt_app, TETEL_16BIT)
        qt_app.processEvents()
        assert controller.property("displayMode") == "dither16"

        vart = _varhato_szemcse_kepernyo(
            window, str(tmp_path / "kepek" / "a.jpg")
        )
        referencia = _referencia_image(window, vart, tmp_path, qt_app)

        hibas_pixelek, legnagyobb_elteres = _varja_a_kirajzolt_szemcset(
            window, qt_app, referencia
        )
        referencia[0].deleteLater()
        assert hibas_pixelek == 0, (
            "a valódi menükattintás után a néző kirajzolt képe nem követi a "
            "spec MT19937 + telítő összeadás képletét; "
            f"hibás pixelek: {hibas_pixelek}, legnagyobb eltérés: "
            f"{legnagyobb_elteres} (a várt érték ±3 px)"
        )

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


def _egyenletes_ab_kepek(lib) -> None:
    """Két AZONOS tartalmú próbakép (`nyitott_nezo` mintája) — a kettős
    nézet mindkét fele ugyanazt a HATTER/FEHER mintát mutatja, így a
    projektor-mód hatása mindkét oldalon UGYANAZZAL a várt színnel
    ellenőrizhető (#3837)."""
    kep = np.full((160, 320, 3), 200, dtype=np.uint8)
    kep[:40, :] = 255
    for nev in ("a.jpg", "b.jpg"):
        assert cv2.imwrite(
            str(lib / nev), kep, [int(cv2.IMWRITE_JPEG_QUALITY), 100]
        )


@pytest.fixture
def ab_nezet_ket_egyenletes_kep(qt_app, tmp_path):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_egyenletes_ab_kepek)
    yield next(gen)
    try:
        next(gen)
    except StopIteration:
        pass


def _varva_szinek_dict(window, qt_app, elem_nev: str, sav, vart) -> set:
    """Mint `_varva_szinek`, de a téglalapot MINDEN körben újra méri a
    `_kep_teglalap`-pal — a kettős nézet két Image-eleméhez ez a segéd
    tartozik (#3837)."""
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        teglalap = _kep_teglalap(_child(window, elem_nev))
        szinek = _szinek(_dict_folt(_tombbe(window.grabWindow()), teglalap, *sav))
        if szinek == vart or time.monotonic() > hatarido:
            return szinek
        time.sleep(0.02)


class TestKettosNezetMindketFelFrissul:
    """#3837: „ab" kettős nézetben a `wire_display_mode` MINDKÉT
    `EditController`-t frissítse módváltáskor, ne csak az elsőt.

    A bal fél (`viewerImageElotte`) a fő `edit_controller`-ből rajzol, a
    jobb (`viewerImage`) a második, `@masodik` rekeszes vezérlőből
    (`edit_controller_masodik`, `test_masodik_elonezet_ab_3187.py`). A
    `wire_display_mode` (`display_mode_controller.py`) eddig csak az
    ELSŐ vezérlő `refresh_displayed_image()`-ét hívta — a szolgáltató
    (`edit_preview`) módja közös, de a QML `Image` URL-cache-e a MÁSODIK
    fél `previewSource`-ának bumpolása nélkül a régi (jelöletlen) képet
    tartja meg. Ez az őr a KIRAJZOLT ablakon, mindkét fél KÖZEPÉN mér —
    a `test_megjelenitesi_mod_a_kepernyon_1598.py` fájl módszerével
    (`grabWindow`), a kettős nézet geometriájához a `_kep_teglalap`-pal
    (`test_kettos_nezet_gombsor_helye_3663.py`).
    """

    def test_projektor_mod_mindket_felen_sotetit(
        self, ab_nezet_ket_egyenletes_kep, qt_app
    ):
        window, controller, _engine = ab_nezet_ket_egyenletes_kep
        _ab_modba(window, qt_app)

        assert _varva_szinek_dict(
            window, qt_app, "viewerImageElotte", HATTER_SAV, {HATTER}
        ) == {HATTER}
        assert _varva_szinek_dict(
            window, qt_app, "viewerImage", HATTER_SAV, {HATTER}
        ) == {HATTER}

        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "projector"

        assert _varva_szinek_dict(
            window, qt_app, "viewerImageElotte", HATTER_SAV, {PROJEKTOROS_HATTER}
        ) == {PROJEKTOROS_HATTER}, (
            "a kettős nézet BAL (fő) fele módváltáskor nem sötétedett"
        )
        assert _varva_szinek_dict(
            window, qt_app, "viewerImage", HATTER_SAV, {PROJEKTOROS_HATTER}
        ) == {PROJEKTOROS_HATTER}, (
            "a kettős nézet MÁSODIK (jobb) fele módváltáskor nem sötétedett — "
            "a wire_display_mode csak az első edit_controllert frissíti"
        )
