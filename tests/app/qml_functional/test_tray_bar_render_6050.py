"""A TrayBar komponensbontás előtti és utáni képpontjai (#6050).

Az aranyképek a bontás előtti, offscreen/software renderből készülnek.
Az összevetés a feliratokat és négy képpontos környezetüket maszkolja, mert
a futtató gépek betűi eltérnek. A képtálca és a menük összes többi képpontja
változatlan kell maradjon.

Aranykép frissítéséhez kizárólag a jelen jegy külön rögzítő kapcsolója
használható: `PICASAPY_6050_RECORD=1`. A normál teszt csak olvas.
"""

from __future__ import annotations

import math
import os
import sys
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QSignalSpy, QTest

from picasapy.app import formatting
from support.jpeg_factory import make_minta_jpeg
from support.render_test_helpers import is_text_item
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre


_GOLDEN = Path(__file__).parent / "golden" / "tray_bar_6050"
#: A goldenek rögzítésének napja (#6085). A fejléc a képek dátumát írja ki;
#: a futás napjától függő szöveg hossza a goldenben kilógna a feliratmaszkból.
_ROGZITETT_NAP = "2026-10-27"
_ALLAPOTOK = (
    "ures",
    "keves_kijelolt",
    "megtartott_kepek",
    "album_lenyilo",
    "talca_helyi_menu",
)
_ABLAKMAGASSAG_ELTOLASOK = (-5, 0, 5)
_ROVID_UI_HATARIDO_MASODPERC = 3.0
_MUTETI_HATARIDO_MASODPERC = 5.0


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _elem(window, nev: str) -> QQuickItem:
    elem = window.findChild(QObject, nev)
    assert isinstance(elem, QQuickItem), f"a(z) {nev} nem található a QML-fában"
    return elem


def _kepadat(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    sorhossz = rgba.bytesPerLine()
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return adat.reshape(rgba.height(), sorhossz)[:, : rgba.width() * 4].reshape(
        rgba.height(), rgba.width(), 4
    ).copy()


def _hibakori_kepmentes(kep: QImage, allapot: str, ablakmagassag: int) -> None:
    kimeneti_mappa = os.environ.get("PICASAPY_RENDER_FAILURE_DIR")
    if not kimeneti_mappa:
        return
    kimenet = Path(kimeneti_mappa) / "tray"
    kimenet.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(kimenet / f"{allapot}-{ablakmagassag}.png"), "PNG")


def test_kepadat_a_qimage_elettartamatol_fuggetlen_tombot_ad():
    kep = QImage(2, 2, QImage.Format.Format_RGBA8888)
    assert _kepadat(kep).flags.owndata


def _talca_kivagas(window, menu=None) -> tuple[QImage, int, int]:
    info = _elem(window, "trayInfoBar")
    fo_sav = _elem(window, "trayMainBar")
    info_pont = info.mapToScene(QPointF(0, 0))
    sav_bal = fo_sav.mapToScene(QPointF(0, 0))
    sav_alj = fo_sav.mapToScene(QPointF(0, fo_sav.height()))

    bal = max(0, math.floor(min(info_pont.x(), sav_bal.x())))
    felso = max(0, math.floor(info_pont.y()))
    jobb = min(window.width(), math.ceil(max(
        info_pont.x() + info.width(), sav_bal.x() + fo_sav.width()
    )))
    also = min(window.height(), math.ceil(sav_alj.y()))

    # A Qt Quick Controls Popup gyökere nem mindig QQuickItem (`popupItem`
    # null lehet); a `parent` + x/y viszont a valós nyitott menü téglalapját
    # adja meg. Az albumlenyílót a tálcával együtt, a jobbklikk-menüt önálló
    # képként rögzítjük, mert az eredeti elhelyezése a sáv fölötti ablakrészt
    # is elfoglalja.
    if menu is not None:
        popup_parent = menu.property("parent")
        if isinstance(popup_parent, QQuickItem):
            szulo_pont = popup_parent.mapToScene(QPointF(0, 0))
            popup_bal = round(szulo_pont.x() + float(menu.property("x")))
            popup_felso = round(szulo_pont.y() + float(menu.property("y")))
            popup_jobb = round(popup_bal + float(menu.property("width")))
            popup_also = round(popup_felso + float(menu.property("height")))
            if menu.objectName() == "trayContextMenu":
                bal, felso, jobb, also = (
                    popup_bal, popup_felso, popup_jobb, popup_also
                )
            else:
                bal = max(0, min(bal, popup_bal))
                felso = max(0, min(felso, popup_felso))
                jobb = min(window.width(), max(jobb, popup_jobb))
                also = min(window.height(), max(also, popup_also))

    teljes = window.grabWindow()
    assert not teljes.isNull(), "a főablakról nem készült képkocka"
    kep = teljes.copy(bal, felso, jobb - bal, also - felso)
    assert not kep.isNull(), "a tálca képkivágása üres"
    return kep, bal, felso


def _szovegdobozok_maszkolasa(window, kep: QImage, bal: int, felso: int) -> np.ndarray:
    ervenyes = np.ones((kep.height(), kep.width()), dtype=bool)
    for objektum in window.findChildren(QObject):
        if not isinstance(objektum, QQuickItem) or not is_text_item(objektum):
            continue
        if not objektum.isVisible() or objektum.width() <= 0 or objektum.height() <= 0:
            continue
        pont = objektum.mapToScene(QPointF(0, 0))
        bal_szoveg = max(0, math.floor(pont.x()) - bal - 4)
        felso_szoveg = max(0, math.floor(pont.y()) - felso - 4)
        jobb_szoveg = min(
            kep.width(), math.ceil(pont.x() + objektum.width()) - bal + 4
        )
        also_szoveg = min(
            kep.height(), math.ceil(pont.y() + objektum.height()) - felso + 4
        )
        if bal_szoveg < jobb_szoveg and felso_szoveg < also_szoveg:
            ervenyes[felso_szoveg:also_szoveg, bal_szoveg:jobb_szoveg] = False
    return ervenyes


def _kepet_rogzit_vagy_osszevet(
    window, allapot: str, qt_app, menu=None, hibak: list[str] | None = None
) -> None:
    """Ha `hibak` lista, az eltérést gyűjti, és a menet a többi állapottal
    folytatódik: a CI így minden állapot képét feltölti (#6085)."""
    try:
        _rogzit_es_osszevet(window, allapot, qt_app, menu)
    except AssertionError as hiba:
        if hibak is None:
            raise
        hibak.append(str(hiba))


def _rogzit_es_osszevet(window, allapot: str, qt_app, menu=None) -> None:
    frissult = QSignalSpy(window.frameSwapped)
    window.update()
    assert _var(qt_app, lambda: frissult.count() > 0, _ROVID_UI_HATARIDO_MASODPERC), (
        f"a(z) {allapot} állapot nem rajzolódott ki határidőn belül"
    )
    aktualis, bal, felso = _talca_kivagas(window, menu)
    _hibakori_kepmentes(aktualis, allapot, window.height())

    kimenet = Path.cwd() / ".tmp" / "tray-bar-6050" / allapot
    kimenet.mkdir(parents=True, exist_ok=True)
    assert aktualis.save(str(kimenet / "aktualis.png"), "PNG")

    referencia = _GOLDEN / f"{allapot}.png"
    if os.environ.get("PICASAPY_6050_RECORD") == "1":
        _GOLDEN.mkdir(parents=True, exist_ok=True)
        assert aktualis.save(str(referencia), "PNG")
        return

    elvart = QImage(str(referencia))
    assert not elvart.isNull(), f"hiányzik a bontás előtti referencia: {referencia}"
    assert abs(aktualis.width() - elvart.width()) <= 3, (
        f"{allapot}: a kivágás szélessége {aktualis.width()} px, "
        f"a referencia {elvart.width()} px"
    )
    assert abs(aktualis.height() - elvart.height()) <= 3, (
        f"{allapot}: a kivágás magassága {aktualis.height()} px, "
        f"a referencia {elvart.height()} px"
    )
    if not sys.platform.startswith("linux"):
        # A Linuxon rögzített képpont-referenciát más rendszer raszterezője
        # nem tudja bitre egyezően kirajzolni (#6150); ott a fenti méret-őr
        # fut, a képpont-összevetés Linuxon. A gépfüggetlen rajzolás: #6148.
        return
    szelesseg = min(aktualis.width(), elvart.width())
    magassag = min(aktualis.height(), elvart.height())
    aktualis_pixelek = _kepadat(aktualis)[:magassag, :szelesseg]
    elvart_pixelek = _kepadat(elvart)[:magassag, :szelesseg]
    ervenyes = _szovegdobozok_maszkolasa(
        window, aktualis, bal, felso
    )[:magassag, :szelesseg]
    elteres = np.any(aktualis_pixelek != elvart_pixelek, axis=2) & ervenyes
    eltero_db = int(np.count_nonzero(elteres))
    assert eltero_db == 0, (
        f"{allapot}: {eltero_db} feliratoktól független képpont eltér "
        f"az összevetett {szelesseg}×{magassag} képkockán"
    )


def _kattints(window, item: QQuickItem, qt_app, gomb=Qt.MouseButton.LeftButton):
    assert _var(qt_app, lambda: item.isVisible() and item.width() > 0 and item.height() > 0), (
        f"a(z) {item.objectName()} nem kattintható"
    )
    pont = item.mapToScene(item.boundingRect().center())
    QTest.mouseClick(
        window,
        gomb,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _kijelol(window, qt_app, sorok: list[int]) -> None:
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0] if sorok else -1)
    assert _var(
        qt_app,
        lambda: list(window.property("selectedIndexes")) == sorok,
        _ROVID_UI_HATARIDO_MASODPERC,
    ), "a főablak nem vette át a próbában megadott kijelölést"


def _fotok_feltoltese(controller, qt_app, tmp_path) -> None:
    konyvtar = Path(controller.watchedFolders[0])
    for index in range(3):
        make_minta_jpeg(konyvtar / f"6050-{index}.jpg", size=(96, 72), seed=index + 1)
    controller.rescan()
    assert _var(qt_app, lambda: controller.photos.rowCount() >= 5, 10.0), (
        "a tálcához készített próbaképek nem kerültek az indexbe"
    )


def _tartalom_menet(qml_app, qt_app, tmp_path, ablakmagassag_eltolas: int) -> None:
    hibak: list[str] = []
    window, controller, _engine = qml_app
    window.show()
    assert _var(qt_app, lambda: window.isExposed(), 10.0), "a főablak nem jelent meg"
    alapmagassag = window.height()
    celmagassag = alapmagassag + ablakmagassag_eltolas
    window.resize(window.width(), celmagassag)
    assert _var(
        qt_app,
        lambda: window.height() == celmagassag,
        _MUTETI_HATARIDO_MASODPERC,
    )

    assert controller.heldCount == 0
    _kijelol(window, qt_app, [])
    _kepet_rogzit_vagy_osszevet(window, "ures", qt_app, hibak=hibak)

    _fotok_feltoltese(controller, qt_app, tmp_path)
    _kijelol(window, qt_app, [0, 1, 2])
    assert _var(qt_app, lambda: controller.heldCount == 3, _MUTETI_HATARIDO_MASODPERC)
    _kepet_rogzit_vagy_osszevet(window, "keves_kijelolt", qt_app, hibak=hibak)

    hold = _elem(window, "trayHoldButton")
    _kattints(window, hold, qt_app)
    assert _var(
        qt_app,
        lambda: all(controller.isHeldAt(i) for i in range(3)),
        _MUTETI_HATARIDO_MASODPERC,
    ), (
        "a kijelölt próbaképek rögzítése nem fejeződött be"
    )
    _kijelol(window, qt_app, [])
    assert _var(qt_app, lambda: controller.heldCount == 3, _MUTETI_HATARIDO_MASODPERC)
    _kepet_rogzit_vagy_osszevet(window, "megtartott_kepek", qt_app, hibak=hibak)

    album_gomb = _elem(window, "trayAddToButton")
    _kattints(window, album_gomb, qt_app)
    album_menu = window.findChild(QObject, "trayAddToMenu")
    assert album_menu is not None
    assert _var(
        qt_app,
        lambda: album_menu.property("opened") is True,
        _ROVID_UI_HATARIDO_MASODPERC,
    ), (
        "a tálca albumválasztó menüje nem nyílt ki"
    )
    _kepet_rogzit_vagy_osszevet(window, "album_lenyilo", qt_app, album_menu, hibak)
    album_menu.close()
    assert _var(
        qt_app,
        lambda: album_menu.property("opened") is False,
        _ROVID_UI_HATARIDO_MASODPERC,
    )

    talca = _elem(window, "trayScratchStrip")
    _kattints(window, talca, qt_app, Qt.MouseButton.RightButton)
    helyi_menu = window.findChild(QObject, "trayContextMenu")
    assert helyi_menu is not None
    assert _var(
        qt_app,
        lambda: helyi_menu.property("opened") is True
        or helyi_menu.property("visible") is True,
        _ROVID_UI_HATARIDO_MASODPERC,
    ), (
        "a tálca jobb gombos menüje nem nyílt ki"
    )
    _kepet_rogzit_vagy_osszevet(window, "talca_helyi_menu", qt_app, helyi_menu, hibak)
    helyi_menu.close()
    assert not hibak, "\n".join(hibak)


@pytest.fixture
def rogzitett_datum(monkeypatch):
    """A `qml_app` ELŐTT kell futnia: az induláskori fejléc is ezt használja."""
    eredeti = formatting.long_date
    monkeypatch.setattr(
        formatting, "long_date", lambda _iso, locale: eredeti(_ROGZITETT_NAP, locale)
    )


@pytest.mark.parametrize("ablakmagassag_eltolas", _ABLAKMAGASSAG_ELTOLASOK)
def test_a_talca_fobb_allapotai_keppontra_megmaradnak(
    ablakmagassag_eltolas,
    rogzitett_datum,
    rogzitett_betu,
    qml_app,
    qt_app,
    tmp_path,
):
    """A rögzített tálcaállapotok `-5/0/+5` ablakmagasságnál is egyeznek."""
    _tartalom_menet(qml_app, qt_app, tmp_path, ablakmagassag_eltolas)
