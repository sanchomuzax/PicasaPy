"""A megjelenítési mód a KIRAJZOLT diavetítésen (#1640).

A #2798 a láncot ízületenként mérte (szolgáltató-képpontok + modell-URL +
QML-kötés). A jegy „Kész, ha" listája viszont azt kérte, hogy a **kirajzolt**
diavetítés-képpontokat mérjük — a #1598 mintájára, mert a felhasználó nem a
szolgáltatót látja, hanem az ablakot. Ez a fájl azt teszi.

## Miért nem elég az ízületenkénti mérés

A #1598 pontosan ezt tanította: a mag bizonyítottan jó volt, a tulajdonos
mégis azt jelentette, hogy „egyáltalán nem működik egyik sem" — a szakadás a
QML-kötésben volt. A `grabWindow()` felvétele a lánc MINDEN ízületét
tartalmazza: menütétel → vezérlő → modell-URL → szolgáltató → `Image`
újratöltés → kirajzolás.

## A várt szín KIÍRT LITERÁL

Nem a termék konstansából olvasva: a spec egész-aritmetikájából
(`200 · 220 >> 8 = 171`), hogy a konstans elrontása is bukást okozzon.

## Mutációs bizonyíték

A jegy kérte („a javítás visszavonásakor az őr bukik"). Mérve: a
`SlideshowView.qml` `displayUrlAt` hívását `fileUrlAt`-ra visszaírva ez a
próba elbukik — a folt 200-as marad, mert a nyers fájlon a mód nem látszik.
"""

from __future__ import annotations

import time

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QMetaObject, QObject, QPointF, Q_ARG, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest

#: A projektor mód mért, egész-aritmetikás eredménye a 200-as szürkén.
PROJEKTOROS_HATTER = (171, 171, 171)
#: A menütétel objectName-je (a #1598-cal azonos).
TETEL_PROJEKTOR = "menuViewDisplayModeProjector"
#: A kirajzolásra szánt türelem — a #1598-cal azonos.
HATARIDO = 10.0


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _kattint(root, name):
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


def _dia_teglalap(window) -> tuple[int, int, int, int]:
    """A `slideshowImage` ténylegesen KIRAJZOLT téglalapja az ablakban."""
    item = _child(window, "slideshowImage")
    doboz_szeles = float(item.property("width"))
    doboz_magas = float(item.property("height"))
    szeles = float(item.property("paintedWidth"))
    magas = float(item.property("paintedHeight"))
    assert szeles > 0 and magas > 0, "a diavetítés nem rajzol ki képet"
    bal_felso = item.mapToScene(
        QPointF((doboz_szeles - szeles) / 2, (doboz_magas - magas) / 2)
    )
    return int(bal_felso.x()), int(bal_felso.y()), int(szeles), int(magas)


def _folt(tomb: np.ndarray, teglalap) -> np.ndarray:
    """A kép közepéből vett folt — a próbaképen egyetlen színű."""
    x, y, szeles, magas = teglalap
    return tomb[
        y + int(magas * 0.35) : y + int(magas * 0.65),
        x + int(szeles * 0.25) : x + int(szeles * 0.75),
    ]


def _szinek(folt: np.ndarray) -> set[tuple[int, int, int]]:
    return {tuple(int(c) for c in p) for p in np.unique(folt.reshape(-1, 3), axis=0)}


def _varva_szinek(window, qt_app, teglalap, vart) -> set:
    """A folt színhalmaza — legfeljebb `HATARIDO`-ig várva a `vart` alakra.

    A `vart` csak a várakozás LEÁLLÍTÁSÁRA szolgál; az állítást a hívó végzi
    a visszaadott halmazon, tehát a határidő lejárta nem hallgat el semmit.
    """
    for _ in range(5):
        qt_app.processEvents()
        QTest.qWait(20)
    hatarido = time.monotonic() + HATARIDO
    while True:
        qt_app.processEvents()
        szinek = _szinek(_folt(_tombbe(window.grabWindow()), teglalap))
        if szinek == vart or time.monotonic() > hatarido:
            return szinek
        time.sleep(0.02)


@pytest.fixture
def futo_diavetites(qml_app, qt_app, tmp_path):
    """Elindított diavetítés egy egyenletes, 200-as próbaképen."""
    window, controller, engine = qml_app
    kep = np.full((160, 320, 3), 200, dtype=np.uint8)
    assert cv2.imwrite(
        str(tmp_path / "kepek" / "a.jpg"), kep, [int(cv2.IMWRITE_JPEG_QUALITY), 100]
    )

    window.setProperty("selectedIndex", 0)
    # a `startSlideshow` KÖTELEZŐ argumentumot vár (a kezdő index; -1 = a
    # kijelöléstől) — argumentum nélkül a hívás csendben nem talál metódust,
    # és a próba „nem indult el"-t jelentene egy nem létező hibára
    QMetaObject.invokeMethod(
        window,
        "startSlideshow",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", -1),
    )
    qt_app.processEvents()
    show = _child(window, "slideshowView")
    assert show.property("visible") is True, "a diavetítés nem indult el"

    teglalap = None
    hatarido = time.monotonic() + HATARIDO
    while teglalap is None and time.monotonic() < hatarido:
        qt_app.processEvents()
        QTest.qWait(20)
        if float(_child(window, "slideshowImage").property("paintedWidth")) > 0:
            teglalap = _dia_teglalap(window)
    assert teglalap is not None, "a diavetítés nem rajzolt ki képet"
    return window, controller, show, teglalap


class TestAKirajzoltDia:
    def test_alaphelyzetben_nincs_atalakitas(self, futo_diavetites, qt_app) -> None:
        window, _controller, _show, teglalap = futo_diavetites
        szinek = _varva_szinek(window, qt_app, teglalap, {(200, 200, 200)})
        assert szinek == {(200, 200, 200)}, (
            f"a próbakép nem egyenletes 200-as a kirajzoláson: {sorted(szinek)[:4]}"
        )

    def test_a_projektor_mod_sotetit_a_kepernyon(self, futo_diavetites, qt_app) -> None:
        window, controller, _show, teglalap = futo_diavetites
        _kattint(window, TETEL_PROJEKTOR)
        qt_app.processEvents()
        assert controller.property("displayMode") == "projector"

        szinek = _varva_szinek(window, qt_app, teglalap, {PROJEKTOROS_HATTER})
        assert szinek == {PROJEKTOROS_HATTER}, (
            "#1640: a diavetítés a NYERS fájlt rajzolta ki, és némán elnyelte a "
            f"megjelenítési módot — a folt színe: {sorted(szinek)[:4]}"
        )

    def test_a_modot_elhagyva_visszaall_a_kep(self, futo_diavetites, qt_app) -> None:
        window, controller, _show, teglalap = futo_diavetites
        _kattint(window, TETEL_PROJEKTOR)
        assert (
            _varva_szinek(window, qt_app, teglalap, {PROJEKTOROS_HATTER})
            == {PROJEKTOROS_HATTER}
        ), "az előfeltétel nem áll: a mód nem jutott a képernyőre"

        _kattint(window, "menuViewDisplayModeAuto")
        qt_app.processEvents()
        assert controller.property("displayMode") in ("", "auto")
        szinek = _varva_szinek(window, qt_app, teglalap, {(200, 200, 200)})
        assert szinek == {(200, 200, 200)}, (
            "a módból kilépve a festetlen képnek kell visszajönnie: "
            f"{sorted(szinek)[:4]}"
        )


# -- #3832: a futó diavetítés forrásmérete ------------------------------------
#
# A betöltött `sourceSize` és a kapott kép (`implicitWidth/Height`) a VALÓDI
# képméretből: a 2560-as dobozba illő, legfeljebb natív méret. A valódi GPU-s
# párja (a textúra a V3D-n + a kirajzolt szín): `test_gpu_finetune_fokusz_3755
# .TestValodiGpuDiavetites`.
#
# rontás-kontroll: a `forrasMeret`-ből az oldalcserét kivéve mód nélkül az
# EXIF-es kép BUKIK (1440×2560 helyett 2560×4551); a `_betolt`-ból a forrás
# előzetes ürítését kivéve a `test_lepeskor_nincs_rossz_paru_betoltes` BUKIK
# (1440×1080 és 168×300 is szerepel a kérések között); az elő-betöltő
# `fillMode`-ja nélkül ugyanez BUKIK (a képek újra kérve). A szolgáltatóban a
# `QImageReader` helyett `QImage(út)`-tal a `test_az_EXIF_orientaciot_alkalmazza`
# BUKIK. Lefuttatva 2026-09-28-án.

#: név → (a fájlban tárolt méret, EXIF-állás)
_FORRAS_KEPEK = {
    "a.jpg": ((400, 300), None),
    "b.jpg": ((1440, 2560), None),
    "c.jpg": ((3000, 5333), None),
    "d.jpg": ((5333, 3000), 6),  # megjelenítve 3000×5333
}
#: a megjelenített, 2560-as dobozba illő, natívnál nem nagyobb kép
_FORRAS_VART = {
    "a.jpg": (400, 300),
    "b.jpg": (1440, 2560),
    "c.jpg": (1440, 2560),
    "d.jpg": (1440, 2560),
}


def _forras_kepek(lib) -> None:
    from PIL import Image as PilImage

    for nev, ((szel, mag), allas) in _FORRAS_KEPEK.items():
        exif = PilImage.Exif()
        if allas:
            exif[0x0112] = allas
        PilImage.new("RGB", (szel, mag), (200, 200, 200)).save(
            lib / nev, quality=90, exif=exif.tobytes()
        )


@pytest.fixture
def forras_diavetites(qt_app, tmp_path, monkeypatch):
    """Négy különböző méretű kép + a `displayphoto` szolgáltató kéréseinek
    naplója (a kapott, még festetlen kép mérete)."""
    import picasapy.app.display_photo_provider as szolgaltato
    from tests.app.qml_functional.conftest import _build_qml_app

    naplo = []
    eredeti = szolgaltato.apply_display_mode_to_qimage

    def _naplozo(kep, mod):
        naplo.append((kep.width(), kep.height()))
        return eredeti(kep, mod)

    monkeypatch.setattr(szolgaltato, "apply_display_mode_to_qimage", _naplozo)
    for window, _controller, _engine in _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_forras_kepek
    ):
        yield window, naplo


def _indit_es_meri(window, qt_app, mod: str) -> dict:
    if mod:
        _kattint(window, mod)
        qt_app.processEvents()
    QMetaObject.invokeMethod(
        window, "startSlideshow", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", 0),
    )
    show = _child(window, "slideshowView")
    show.setProperty("playing", False)
    modell = show.property("photosModel")
    dia = _child(window, "slideshowImage")
    mert = {}
    for nev in _FORRAS_KEPEK:
        sor = next(i for i in range(modell.rowCount())
                   if modell.filePathAt(i).endswith("/" + nev))
        show.setProperty("currentIndex", sor)
        qt_app.processEvents()
        mert[nev] = (int(dia.property("implicitWidth")),
                     int(dia.property("implicitHeight")))
    return mert


class TestAForrasmeret:
    @pytest.mark.parametrize("mod", ["", TETEL_PROJEKTOR])
    def test_a_dobozba_illo_nativnal_nem_nagyobb(
        self, forras_diavetites, qt_app, mod
    ) -> None:
        window, _naplo = forras_diavetites
        mert = _indit_es_meri(window, qt_app, mod)
        assert mert == _FORRAS_VART, f"{mod or 'mód nélkül'}: {mert}"

    def test_lepeskor_nincs_rossz_paru_betoltes(
        self, forras_diavetites, qt_app
    ) -> None:
        """A dia forrását és forrásméretét EGYÜTT írjuk: két külön kötésnél
        a Qt lépéskor a rossz párral is betöltött (a régi kép az új mérettel
        vagy fordítva), és az elő-betöltő eltérő `fillMode`-ja miatt a
        gyorstár sem talált."""
        window, naplo = forras_diavetites
        _indit_es_meri(window, qt_app, TETEL_PROJEKTOR)
        rossz = [m for m in naplo if m not in _FORRAS_VART.values()]
        assert not rossz, f"rossz párú betöltés: {naplo}"
        # az első kép + képenként legfeljebb egy (elő-)betöltés
        assert len(naplo) <= len(_FORRAS_KEPEK) + 1, naplo
