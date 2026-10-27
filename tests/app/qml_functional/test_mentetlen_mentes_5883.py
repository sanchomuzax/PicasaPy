"""#5883: a Save csak mentetlen szerkesztési lánccal legyen engedélyezett."""

from __future__ import annotations

import os
from pathlib import Path

import cv2
import pytest
from PySide6.QtCore import QObject, QMetaObject, Qt
from PySide6.QtGui import QColor, QImage, QPainter
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem

from picasapy.ini import load_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._fomenu_4420_menu import _megnyit, _menupont
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    tetel_kattintasa,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    kattints,
    vizualis_bejaras,
)
from tests.support.qt_wait import wait_for_photo_op, wait_for_signal
from tests.support.varakozas import var_feltetelre

_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)
_FOTO_FORRAS = (
    Path(__file__).resolve().parents[2]
    / "fixtures"
    / "face_type_a_name_reference_en38.png"
)


def _kepeket(lib: Path) -> None:
    """Két valódi JPEG-fájlt készít ugyanabból a fotófixture-ből."""
    foto = cv2.imread(str(_FOTO_FORRAS), cv2.IMREAD_COLOR)
    assert foto is not None, f"nem olvasható a fotófixture: {_FOTO_FORRAS}"
    for nev in ("a.jpg", "b.jpg"):
        ok, kodolt = cv2.imencode(".jpg", foto, [cv2.IMWRITE_JPEG_QUALITY, 96])
        assert ok, f"nem kódolható a fotófixture: {nev}"
        (lib / nev).write_bytes(kodolt.tobytes())


@pytest.fixture
def mentetlen_app(qt_app, tmp_path):
    """A teljes alkalmazás két fotóval és a valódi bélyegkép-szolgáltatóval."""
    app = _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )
    window, controller, engine = next(app)
    # A menüsor Python-wrapperét a Qt a főablak tulajdonosaként kezeli;
    # tartsuk meg a fixture végéig (mint a #5833 tesztben).
    menu_bar = window.property("menuBar")
    assert menu_bar is not None
    try:
        yield window, controller, engine
    finally:
        del menu_bar
        next(app, None)


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _qml_igaz(root, kifejezes: str) -> bool:
    eredmeny, hiba = QQmlExpression(
        qmlContext(root), root, kifejezes
    ).evaluate()
    assert not hiba, f"a QML-kifejezés nem értékelhető ki: {kifejezes}"
    return bool(eredmeny)


def _valodi_belyegkepek_keszek(window) -> bool:
    allapotok = []
    for elem in vizualis_bejaras(window.contentItem()):
        if elem.objectName() != "thumbImage" or not elem.property("source"):
            continue
        kesz, hiba = QQmlExpression(
            qmlContext(elem), elem, "status === Image.Ready"
        ).evaluate()
        if not hiba:
            allapotok.append(bool(kesz))
    return len(allapotok) >= 2 and all(allapotok)


def _menu_tetel(menu, nev: str) -> QQuickItem:
    for index in range(int(menu.property("count"))):
        tetel = _menupont(menu, index)
        if tetel is not None and tetel.objectName() == nev:
            return tetel
    raise AssertionError(f"{nev} nem található a nyitott menüben")


def _filters(kep_ut: Path) -> str:
    szakasz = load_document(kep_ut.parent / ".picasa.ini").section(kep_ut.name)
    return (szakasz.get("filters") if szakasz is not None else None) or ""


def _file_menu_allapot(window, qt_app, *, kepet_ker=False):
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a felső menüsor hiányzik"
    menu = _megnyit(menu_bar, qt_app, "&File")
    save = _menu_tetel(menu, "menuFileSave")
    revert = _menu_tetel(menu, "menuFileRevert")
    _varj(
        qt_app,
        lambda: menu.property("opened") is True and save.isVisible(),
        "a nyitott File menü nem látható",
    )
    save_enabled = save.property("enabled")
    revert_enabled = revert.property("enabled")
    kep = window.grabWindow() if kepet_ker else None
    if kepet_ker:
        assert not kep.isNull(), "a nyitott File menü képernyőképe üres"
    QMetaObject.invokeMethod(menu, "close", Qt.ConnectionType.DirectConnection)
    qt_app.processEvents()
    return save_enabled, revert_enabled, kep


def _file_menu_save_kattintas(window, qt_app) -> None:
    menu_bar = window.property("menuBar")
    assert menu_bar is not None, "a felső menüsor hiányzik"
    menu = _megnyit(menu_bar, qt_app, "&File")
    save = _menu_tetel(menu, "menuFileSave")
    assert save.property("enabled") is True, "a File ▸ Save le van tiltva"
    kattints(window, qt_app, save)


def _megerosito_save_kattintas(window, qt_app) -> None:
    parbeszed = window.findChild(QObject, "saveConfirmDialog")
    assert parbeszed is not None and parbeszed.property("opened") is True
    footer = parbeszed.property("footer")
    ment_gomb = next(
        elem
        for elem in vizualis_bejaras(footer)
        if elem.isVisible()
        and elem.property("text") in {"Save", "Mentés"}
        and elem.property("enabled") is True
    )
    kattints(window, qt_app, ment_gomb)


def _osszefuz_kepeket(mentes_elott: QImage, mentes_utan: QImage, cel: Path) -> None:
    felirat_magassag = 34
    kep = QImage(
        mentes_elott.width() + mentes_utan.width(),
        max(mentes_elott.height(), mentes_utan.height()) + felirat_magassag,
        QImage.Format.Format_ARGB32,
    )
    kep.fill(QColor("white"))
    festo = QPainter(kep)
    festo.setPen(QColor("#202020"))
    festo.drawText(12, 23, "No unsaved edits")
    festo.drawText(mentes_elott.width() + 12, 23, "Unsaved edits (I'm Feeling Lucky)")
    festo.drawImage(0, felirat_magassag, mentes_elott)
    festo.drawImage(mentes_elott.width(), felirat_magassag, mentes_utan)
    festo.end()
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert kep.save(str(cel), "PNG"), f"a kiadáskép nem írható: {cel}"


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTERESEK)
def test_save_menu_lucky_utan_aktiv_mentes_utan_ismet_szurke(
    mentetlen_app, qt_app, tmp_path, magassag_elteres
):
    window, controller, _engine = mentetlen_app
    window.show()
    window.requestActivate()
    eredeti_magassag = int(window.height())
    kert_magassag = eredeti_magassag + magassag_elteres
    window.setHeight(kert_magassag)
    _varj(
        qt_app,
        lambda: int(window.height()) == kert_magassag,
        "a főablak nem vette fel a kért magasságot",
    )
    _varj(
        qt_app,
        lambda: controller.photos.rowCount() == 2,
        "a két fotó nem töltődött be",
    )
    _varj(
        qt_app,
        lambda: _valodi_belyegkepek_keszek(window),
        "a valódi fotó-bélyegképek nem töltődtek be",
    )

    thumb = next(
        elem
        for elem in vizualis_bejaras(window.contentItem())
        if elem.objectName() == "thumbMouseArea" and elem.isVisible()
    )
    kattints(window, qt_app, thumb)
    _varj(
        qt_app,
        lambda: window.property("selectedIndexes").toVariant() == [0],
        "a valódi fotóra kattintás nem jelölte ki az első képet",
    )

    fejléc_mentes = next(
        elem
        for elem in vizualis_bejaras(window.contentItem())
        if elem.objectName() == "headerSaveEditsButton"
    )
    kezdeti_save_engedelyezett, kezdeti_revert_engedelyezett, elotte = (
        _file_menu_allapot(
            window, qt_app, kepet_ker=magassag_elteres == 0
        )
    )
    assert kezdeti_save_engedelyezett is False, (
        "szerkesztetlen kijelölt képnél a File ▸ Save nem szürke"
    )
    assert kezdeti_revert_engedelyezett is False, (
        "a szerkesztetlen képnél a Revert eltért a mentett backup feltételétől"
    )
    assert fejléc_mentes.property("enabled") is False, (
        "szerkesztetlen kijelölésnél a mappa-fejléc Save gombja aktív"
    )
    assert not _qml_igaz(window, "shortcutSave.enabled"), (
        "szerkesztetlen kijelölésnél a Ctrl+S aktív"
    )

    kep_ut = Path(str(controller.photos.filePathAt(0)))
    wait_for_photo_op(
        controller,
        lambda: tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuBatchEnhance",
            almenu_utvonal=("menuPictureBatchEdit",),
        ),
        qt_app=qt_app,
    )
    _varj(
        qt_app,
        lambda: "enhance=1;" in _filters(kep_ut),
        "az I'm Feeling Lucky nem hozott létre filters szerkesztési láncot",
    )
    _varj(
        qt_app,
        lambda: fejléc_mentes.property("enabled") is True
        and _qml_igaz(window, "shortcutSave.enabled"),
        "az I'm Feeling Lucky után a mentési belépési pontok nem váltak aktívvá",
    )
    lucky_save_engedelyezett, _revert_enabled, utan = _file_menu_allapot(
        window, qt_app, kepet_ker=magassag_elteres == 0
    )
    assert lucky_save_engedelyezett is True, (
        "az I'm Feeling Lucky után a File ▸ Save nem vált engedélyezetté"
    )

    if magassag_elteres == 0:
        cel_nyers = os.environ.get("PICASAPY_5883_SCREENSHOT", "").strip()
        cel = (
            Path(cel_nyers)
            if cel_nyers
            else tmp_path / "5883-save-menu-states.png"
        )
        assert elotte is not None and utan is not None
        _osszefuz_kepeket(elotte, utan, cel)

    _file_menu_save_kattintas(window, qt_app)
    parbeszed = window.findChild(QObject, "saveConfirmDialog")
    _varj(
        qt_app,
        lambda: parbeszed is not None and parbeszed.property("opened") is True,
        "a File ▸ Save kattintás nem nyitotta meg a mentés-megerősítést",
    )
    wait_for_signal(
        controller.saveFinished,
        lambda: _megerosito_save_kattintas(window, qt_app),
        description="a File menü Save gombja",
        process_events_with=qt_app,
    )
    _varj(
        qt_app,
        lambda: controller.photos.itemAt(0)["hasEdits"] is False,
        "a lemezmentés után a modell még szerkesztést jelez",
    )
    save_engedelyezett, revert_engedelyezett, _kep = _file_menu_allapot(
        window, qt_app
    )
    assert save_engedelyezett is False, (
        "a mentés után a File ▸ Save aktív maradt"
    )
    assert fejléc_mentes.property("enabled") is False, (
        "a mentés után a mappa-fejléc Save gombja aktív maradt"
    )
    assert not _qml_igaz(window, "shortcutSave.enabled"), (
        "a mentés után a Ctrl+S aktív maradt"
    )
    assert revert_engedelyezett is True, (
        "a mentés utáni Revert engedélyezés eltér a mentett backup feltételétől"
    )
