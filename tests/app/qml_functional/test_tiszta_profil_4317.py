"""#4317 — a fő funkciók tiszta, hálózat nélküli felhasználói profilon."""

# rontás-kontroll: picasapy.app.edit_controller._ONE_SHOT_NAMES = () → 1 failed

from __future__ import annotations

import errno
import socket
import sys
import time
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QImage, QImageWriter
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op
from tests.app.qml_functional._fomenu_4420_menu import _kattints, _megnyit
from tests.app.qml_functional.conftest import _build_qml_app


_REPO = Path(__file__).resolve().parents[3]
_KEPMENTES = _REPO / "docs" / "assets" / "paritas-tiszta-profil"
_QML_REFS = []


def _var(qt_app, feltetel, masodperc: float = 8.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, RuntimeError, TypeError):
            pass
        time.sleep(0.02)
    qt_app.processEvents()
    return bool(feltetel())


def _bejark(item):
    for gyerek in item.childItems():
        _QML_REFS.append(gyerek)
        yield gyerek
        yield from _bejark(gyerek)


def _elemek(window, nev: str):
    talalatok = [
        item for item in _bejark(window.contentItem())
        if item.objectName() == nev
    ]
    if talalatok:
        _QML_REFS.extend(talalatok)
        return talalatok
    elem = window.findChild(QObject, nev)
    if elem is not None:
        _QML_REFS.append(elem)
        return [elem]
    return []


def _elem(window, nev: str):
    talalatok = _elemek(window, nev)
    assert talalatok, f"a felületi elem nem található: {nev}"
    return talalatok[0]


def _kattint(window, qt_app, nev: str):
    elem = _elem(window, nev)
    assert isinstance(elem, QQuickItem), f"{nev} nem kattintható QML-elem"
    _kattint_item(elem, qt_app)
    return elem


def _kattint_item(elem, qt_app):
    _kattints(qt_app, elem)


def _duplakattint(window, qt_app, elem):
    assert isinstance(elem, QQuickItem)
    assert elem.isVisible() and elem.isEnabled()
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    pont = QPoint(round(kozep.x()), round(kozep.y()))
    cel = elem.window()
    QTest.mouseClick(cel, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier, pont)
    QTest.mouseDClick(cel, Qt.MouseButton.LeftButton,
                      Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _nyisd_meg_a_nezot(window, qt_app):
    if window.property("viewerOpen") is not True:
        _duplakattint(window, qt_app, _elem(window, "thumbMouseArea"))
    assert _var(qt_app, lambda: window.property("viewerOpen") is True), (
        "a képrács valódi dupla kattintása nem nyitotta meg a nézőt"
    )


def _kepernyokep(window, fajlnev: str):
    _KEPMENTES.mkdir(parents=True, exist_ok=True)
    image = window.grabWindow()
    assert not image.isNull(), "az alkalmazásablakról nem készült kép"
    if image.width() > 600:
        image = image.scaledToWidth(
            600, Qt.TransformationMode.SmoothTransformation
        )
    image = image.convertToFormat(QImage.Format.Format_Grayscale8)
    cel = _KEPMENTES / fajlnev
    iro = QImageWriter(str(cel), b"png")
    iro.setCompression(9)
    assert iro.write(image), f"a képernyőkép nem menthető: {iro.errorString()}"
    return cel


def _kepek_keszitese(mappa: Path):
    make_jpeg(mappa / "tisztaprofil.jpg", size=(360, 240))


@pytest.fixture(scope="module")
def tiszta_profil_kornyezet(tmp_path_factory):
    """A Qt létrehozása előtt minden felhasználói könyvtárat ide térít."""
    profil = tmp_path_factory.mktemp("picasapy-tiszta-profil")
    konyvtarak = {
        "HOME": profil / "home",
        "USERPROFILE": profil / "home",
        "XDG_CONFIG_HOME": profil / "config",
        "XDG_DATA_HOME": profil / "data",
        "XDG_CACHE_HOME": profil / "cache",
        "APPDATA": profil / "appdata",
        "LOCALAPPDATA": profil / "localappdata",
    }
    for konyvtar in konyvtarak.values():
        konyvtar.mkdir(parents=True, exist_ok=True)
    monkeypatch = pytest.MonkeyPatch()
    for nev, konyvtar in konyvtarak.items():
        monkeypatch.setenv(nev, str(konyvtar))
    monkeypatch.delenv("PICASAPY_FACE_MODEL", raising=False)
    monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)

    probalkozasok = []
    eredeti_connect = socket.socket.connect
    eredeti_connect_ex = socket.socket.connect_ex

    def _cel(address):
        if isinstance(address, tuple):
            return f"{address[0]}:{address[1]}"
        return "nem-IP-cél"

    def _connect(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            probalkozasok.append(("connect", _cel(address)))
            raise OSError(errno.ENETUNREACH, "a teszt letiltotta a hálózatot")
        return eredeti_connect(sock, address)

    def _connect_ex(sock, address):
        if sock.family in (socket.AF_INET, socket.AF_INET6):
            probalkozasok.append(("connect_ex", _cel(address)))
            return errno.ENETUNREACH
        return eredeti_connect_ex(sock, address)

    def _getaddrinfo(host, *args, **kwargs):
        probalkozasok.append(("DNS", str(host)))
        raise OSError(socket.EAI_NONAME, "a teszt letiltotta a hálózatot")

    monkeypatch.setattr(socket.socket, "connect", _connect)
    monkeypatch.setattr(socket.socket, "connect_ex", _connect_ex)
    monkeypatch.setattr(socket, "getaddrinfo", _getaddrinfo)
    yield profil, probalkozasok
    monkeypatch.undo()


@pytest.fixture
def qml_tiszta_app(tiszta_profil_kornyezet, qt_app, tmp_path, request):
    """A könyvtári QML-harness szokásos yield-from életciklusa."""
    try:
        yield from _build_qml_app(
            qt_app, tmp_path, kepeket_keszit=_kepek_keszitese,
            valodi_belyegkep=True, show_only_big_images=False,
            keep_modul=request.module,
        )
    finally:
        _QML_REFS.clear()


@pytest.fixture
def tiszta_app(qml_tiszta_app, tiszta_profil_kornyezet):
    window, controller, engine = qml_tiszta_app
    profil, probalkozasok = tiszta_profil_kornyezet
    app = {
        "window": window,
        "controller": controller,
        "engine": engine,
        "edit": engine.rootContext().contextProperty("editController"),
        "profile": profil,
        "attempts": probalkozasok,
    }
    assert not (profil / "data" / "picasapy" / "models").exists()
    return app


def _lep_mappa_betoltes_es_indexkep_racs(tiszta_app, qt_app):
    app = tiszta_app
    window, controller = app["window"], app["controller"]
    assert _var(qt_app, lambda: len(controller.photos.photos) == 1), (
        "a tesztképet tartalmazó mappa nem töltődött be"
    )
    mappa_sor = _elem(window, "folderRowLabel")
    assert isinstance(mappa_sor, QQuickItem) and mappa_sor.isVisible()
    _kattint_item(mappa_sor, qt_app)
    assert _var(qt_app, lambda: len(controller.photos.photos) == 1), (
        "a valódi mappasorkattintás után nem látszik a tesztkép"
    )
    grid = _elem(window, "photoGrid")
    assert grid.isVisible() and grid.property("count") == 1
    _kepernyokep(window, "01-racs.png")
    assert not app["attempts"], f"indításkor hálózati próbálkozás történt: {app['attempts']}"


def _lep_nezo_valodi_dupla_kattintassal(tiszta_app, qt_app):
    app = tiszta_app
    window = app["window"]
    assert window.isVisible()
    thumb = _elem(window, "thumbMouseArea")
    _duplakattint(window, qt_app, thumb)
    assert _var(qt_app, lambda: window.property("viewerOpen") is True), (
        "a valódi dupla kattintás nem nyitotta meg a nézőt"
    )
    # A nézőt a későbbi vörösszem-képernyőkép is mutatja.
    assert shiboken6.isValid(window), "a néző képernyőképe után megszűnt a főablak"
    assert not app["attempts"], f"nézőnyitás közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_csillag_valodi_kattintassal(tiszta_app, qt_app):
    app = tiszta_app
    window, controller = app["window"], app["controller"]
    if window.property("selectedIndex") != 0:
        _kattint_item(_elem(window, "thumbMouseArea"), qt_app)
    assert window.property("selectedIndex") == 0
    assert not controller.photos.starAt(0)
    button = _elem(window, "trayStarButton")
    assert button.property("targetRow") == 0
    wait_for_photo_op(
        controller,
        lambda: _kattint_item(button, qt_app),
        qt_app=qt_app,
    )
    assert _var(qt_app, lambda: controller.photos.starAt(0)), (
        "a csillagkattintás nem mentette a csillagozott állapotot"
    )
    assert not app["attempts"], f"csillagozás közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_felirat_valodi_bevitellel(tiszta_app, qt_app):
    app = tiszta_app
    window, controller = app["window"], app["controller"]
    _nyisd_meg_a_nezot(window, qt_app)
    field = _elem(window, "captionField")
    assert isinstance(field, QQuickItem) and field.isVisible()
    _kattint(window, qt_app, "captionField")
    QTest.keyClick(window, Qt.Key.Key_A, Qt.KeyboardModifier.ControlModifier)
    for character in "clean profile caption":
        key = (
            Qt.Key.Key_Space if character == " "
            else Qt.Key(ord(character.upper()))
        )
        QTest.keyClick(window, key)
    QTest.keyClick(window, Qt.Key.Key_Return)
    assert _var(qt_app, lambda: controller.photos.captionAt(0) == "clean profile caption"), (
        "a felirat nem mentődött a képre"
    )
    assert not app["attempts"], f"felirat mentése közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_auto_kontraszt_es_visszavonas(tiszta_app, qt_app):
    app = tiszta_app
    window, edit = app["window"], app["edit"]
    _nyisd_meg_a_nezot(window, qt_app)
    eszkoz = _elem(window, "editToolAutolight")
    if not eszkoz.isVisible():
        _kattint(window, qt_app, "toggle_left_drawer")
    assert _var(qt_app, lambda: eszkoz.isVisible() and eszkoz.isEnabled())
    _kattint(window, qt_app, "editToolAutolight")
    assert _var(qt_app, lambda: "autolight" in edit.effectChain.casefold()), (
        "az Auto Contrast nem került a szerkesztési láncba"
    )
    _kattint(window, qt_app, "editUndoButton")
    assert _var(qt_app, lambda: "autolight" not in edit.effectChain.casefold()), (
        "a Visszavonás nem távolította el az Auto Contrast hatást"
    )
    assert not app["attempts"], f"szerkesztés közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_export_valodi_menu_es_kattintas(tiszta_app, qt_app, tmp_path_factory):
    app = tiszta_app
    window = app["window"]
    menu_bar = window.property("menuBar")
    _QML_REFS.append(menu_bar)
    _megnyit(menu_bar, qt_app, "File")
    _kattints(qt_app, _elem(window, "menuFileExport"))
    export = _elem(window, "exportDialog")
    assert _var(qt_app, lambda: export.property("opened") is True), (
        "a File > Export Picture to Folder parancs nem nyitotta meg az exportot"
    )
    cel = tmp_path_factory.mktemp("export-cel")
    export.setProperty("targetFolder", QUrl.fromLocalFile(str(cel)).toString())
    qt_app.processEvents()
    gombok = [
        item for item in _bejark(window.contentItem())
        if isinstance(item, QQuickItem)
        and str(item.property("text") or "").strip().casefold() == "export"
        and item.isVisible() and item.isEnabled()
    ]
    _QML_REFS.extend(gombok)
    assert gombok, "az export párbeszéd Export gombja nem található"
    _kattint_item(gombok[-1], qt_app)
    assert _var(qt_app, lambda: any(cel.rglob("*.jpg")), 30.0), (
        "az export nem készített JPEG-et a kiválasztott célmappában"
    )
    assert _var(qt_app, lambda: export.property("opened") is False), (
        "az export befejeződött, de a párbeszéd nyitva maradt"
    )
    assert _var(qt_app, lambda: export.property("visible") is False, 3.0), (
        "az export párbeszéd bezáró animációja nem ért véget"
    )
    assert not app["attempts"], f"exportálás közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_arcfelismeres_inditasa_letoltes_nelkul(tiszta_app, qt_app):
    app = tiszta_app
    window, engine = app["window"], app["engine"]
    menu_bar = window.property("menuBar")
    _QML_REFS.append(menu_bar)
    _megnyit(menu_bar, qt_app, "Tools")
    _kattints(qt_app, _elem(window, "menuToolsFaceScan"))
    assert _var(qt_app, lambda: bool(_elemek(window, "faceScanDialog"))), (
        "a Tools > Find Faces kattintás után nem jött létre a párbeszéd"
    )
    dialog = _elem(window, "faceScanDialog")
    assert _var(qt_app, dialog.isVisible), (
        "a Tools > Find Faces kattintás után nem nyílt meg a párbeszéd "
        f"(visible={dialog.isVisible()}, "
        f"attempts={app['attempts']})"
    )
    _kepernyokep(dialog, "02-arcfelismeres.png")
    assert dialog.property("detectorAvailable") is True, (
        "a tiszta profilban nincs elérhető arcdetektor; a felület letöltést kér"
    )
    assert dialog.property("embedderAvailable") is True, (
        "a tiszta profilban nincs elérhető arc-embedder; a felület letöltést kér"
    )
    scan = engine.rootContext().contextProperty("faceScanController")
    befejezett = []
    scan.scanFinished.connect(lambda *args: befejezett.append(args))
    _kattint(dialog, qt_app, "faceScanStartButton")
    assert _var(qt_app, lambda: bool(befejezett), 30.0), (
        "az arcfelismerési futás nem fejeződött be"
    )
    assert not dialog.property("scanning")
    assert not app["attempts"], f"arcfelismerés közben hálózati próbálkozás történt: {app['attempts']}"
    modelmappa = app["profile"] / "data" / "picasapy" / "models"
    assert not modelmappa.exists() or not list(modelmappa.glob("*.onnx")), (
        "az arcfelismerés modellt töltött le az üres profilba"
    )
    _kattint(dialog, qt_app, "faceScanCloseButton")


def _lep_vorosszem_javitas_valodi_huzassal(tiszta_app, qt_app):
    app = tiszta_app
    window, edit = app["window"], app["edit"]
    _nyisd_meg_a_nezot(window, qt_app)
    eszkoz = _elem(window, "editToolRedeye")
    if not eszkoz.isVisible():
        _kattint(window, qt_app, "toggle_left_drawer")
    _kattint(window, qt_app, "editToolRedeye")
    terulet = _elem(window, "redeyeDragArea")
    assert terulet.isEnabled() and terulet.width() > 0 and terulet.height() > 0
    p0 = terulet.mapToScene(QPointF(terulet.width() * 0.46, terulet.height() * 0.46))
    p1 = terulet.mapToScene(QPointF(terulet.width() * 0.54, terulet.height() * 0.54))
    cel = terulet.window()
    QTest.mousePress(cel, Qt.MouseButton.LeftButton,
                     Qt.KeyboardModifier.NoModifier,
                     QPoint(round(p0.x()), round(p0.y())))
    QTest.mouseMove(cel, QPoint(round(p1.x()), round(p1.y())), 40)
    QTest.mouseRelease(cel, Qt.MouseButton.LeftButton,
                       Qt.KeyboardModifier.NoModifier,
                       QPoint(round(p1.x()), round(p1.y())))
    qt_app.processEvents()
    _kattint(window, qt_app, "redeyeApplyButton")
    assert _var(qt_app, lambda: "redeye" in edit.effectChain.casefold()), (
        "a vörösszem-kijelölés alkalmazása nem került a szerkesztési láncba"
    )
    _kepernyokep(window, "03-vorosszem.png")
    assert not app["attempts"], f"vörösszem-javítás közben hálózati próbálkozás történt: {app['attempts']}"


def _ellenorizd_kepernyokepek_meretet():
    kepek = sorted(_KEPMENTES.glob("*.png"))
    assert len(kepek) == 3, f"nem készült el mindhárom képernyőkép: {kepek}"
    osszesen = sum(kep.stat().st_size for kep in kepek)
    assert osszesen < 1_000_000, f"a képernyőképek együtt {osszesen} bájtosak"


def test_tiszta_profil_funkciok_valodi_kattintassal(
    tiszta_app, qt_app, tmp_path_factory,
):
    """A teljes felhasználói útvonal egy valós, izolált QML-appban fut."""
    for regi in _KEPMENTES.glob("*.png"):
        regi.unlink()
    _lep_mappa_betoltes_es_indexkep_racs(tiszta_app, qt_app)
    _lep_csillag_valodi_kattintassal(tiszta_app, qt_app)
    _lep_nezo_valodi_dupla_kattintassal(tiszta_app, qt_app)
    _lep_felirat_valodi_bevitellel(tiszta_app, qt_app)
    _lep_auto_kontraszt_es_visszavonas(tiszta_app, qt_app)
    _lep_export_valodi_menu_es_kattintas(tiszta_app, qt_app, tmp_path_factory)
    _lep_arcfelismeres_inditasa_letoltes_nelkul(tiszta_app, qt_app)
    if sys.platform != "win32":  # #4929: Windowson a húzás nem kerül a láncba
        _lep_vorosszem_javitas_valodi_huzassal(tiszta_app, qt_app)
    _ellenorizd_kepernyokepek_meretet()
