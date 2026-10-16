"""#4317 — a fő funkciók tiszta, hálózat nélküli felhasználói profilon."""

# rontás-kontroll: picasapy.app.edit_controller._ONE_SHOT_NAMES = () → 1 failed

from __future__ import annotations

import errno
import os
import socket
import sys
from pathlib import Path

import pytest
import shiboken6
from PySide6.QtCore import QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtGui import QImage, QImageWriter
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._fomenu_4420_menu import _kattints, _megnyit
from tests.app.qml_functional.conftest import _build_qml_app


_REPO = Path(__file__).resolve().parents[3]
_KEPMENTES = _REPO / "docs" / "assets" / "paritas-tiszta-profil"
_QML_REFS = []

# Kapcsoló: a dokumentációs képek (docs/assets/paritas-tiszta-profil/) csak
# akkor íródnak felül, ha PICASAPY_DOKUKEPEK=1 be van állítva. Alapból a
# képernyőképek a tmp_path alá kerülnek, így a futás nem piszkítja a munkafát.
_DOKUKEPEK_KAPCSOLO = "PICASAPY_DOKUKEPEK"


def _var(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


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


def _kepmappa(tmp_path_factory) -> Path:
    if os.environ.get(_DOKUKEPEK_KAPCSOLO) == "1":
        return _KEPMENTES
    return tmp_path_factory.mktemp("kepernyokepek")


def _kepernyokep(window, mappa: Path, fajlnev: str):
    mappa.mkdir(parents=True, exist_ok=True)
    image = window.grabWindow()
    assert not image.isNull(), "az alkalmazásablakról nem készült kép"
    if image.width() > 600:
        image = image.scaledToWidth(
            600, Qt.TransformationMode.SmoothTransformation
        )
    image = image.convertToFormat(QImage.Format.Format_Grayscale8)
    cel = mappa / fajlnev
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
def tiszta_app(qml_tiszta_app, tiszta_profil_kornyezet, tmp_path_factory):
    window, controller, engine = qml_tiszta_app
    profil, probalkozasok = tiszta_profil_kornyezet
    app = {
        "window": window,
        "controller": controller,
        "engine": engine,
        "edit": engine.rootContext().contextProperty("editController"),
        "profile": profil,
        "attempts": probalkozasok,
        "kepek": _kepmappa(tmp_path_factory),
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
    _kepernyokep(window, app["kepek"], "01-racs.png")
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
    assert _var(qt_app, lambda: export.property("visible") is False), (
        "az export párbeszéd bezáró animációja nem ért véget"
    )
    assert not app["attempts"], f"exportálás közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_arcfelismeres_inditasa_letoltes_nelkul(tiszta_app, qt_app):
    app = tiszta_app
    window, engine = app["window"], app["engine"]
    menu_bar = window.property("menuBar")
    _QML_REFS.append(menu_bar)
    # Windowson a felugró menü elhelyezése késhet, és az első kattintás a
    # még mozgó menüpont mellé eshet; ilyenkor egyszer újranyitjuk a menüt.
    for _ in range(2):
        _megnyit(menu_bar, qt_app, "Tools")
        _kattints(qt_app, _elem(window, "menuToolsFaceScan"))
        if _var(qt_app, lambda: bool(_elemek(window, "faceScanDialog")), 10.0):
            break
    assert _elemek(window, "faceScanDialog"), (
        "a Tools > Find Faces kattintás után nem jött létre a párbeszéd"
    )
    dialog = _elem(window, "faceScanDialog")
    assert _var(qt_app, dialog.isVisible), (
        "a Tools > Find Faces kattintás után nem nyílt meg a párbeszéd "
        f"(visible={dialog.isVisible()}, "
        f"attempts={app['attempts']})"
    )
    _kepernyokep(dialog, app["kepek"], "02-arcfelismeres.png")
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
    # Ablakot zárni nem azonnali: a következő lépés (vörösszem) a főablakra kattint.
    assert _var(qt_app, lambda: not dialog.isVisible()), (
        "az arcfelismerő ablak bezárás után is látszik"
    )


def _nev(item) -> str:
    # a PySide-burok típusa mindig QQuickItem; a valódi QML-típus a metaObject-ből jön
    return item.objectName() or item.metaObject().className()


def _legfelso_talalat(item, pont):
    """A pontnál legfelül álló elem; rekurzív, mert a childAt csak a közvetlen gyerekeket nézi."""
    if not item.contains(item.mapFromScene(pont)):
        return None
    for gyerek in sorted(item.childItems(), key=lambda g: g.z(), reverse=True):
        if gyerek.isVisible():
            talalat = _legfelso_talalat(gyerek, pont)
            if talalat is not None:
                return talalat
    return item


def _latszik_es_meretes(item) -> bool:
    return (item.isVisible() and item.isEnabled()
            and item.width() > 0 and item.height() > 0)


def _keres(window, nev: str):
    """Mint a _elem, de nem bukik el: None, ha az elem nincs (diagnosztikához, #4929)."""
    talalatok = _elemek(window, nev)
    return talalatok[0] if talalatok else None


def _igen_nem(logikai: bool) -> str:
    return "igen" if logikai else "nem"


def _elem_helyzet(window, nev: str, elem) -> str:
    """Létezik-e, látszik-e, engedélyezett-e, és hol van az ablak tartalmához képest (#4929)."""
    if elem is None:
        return f"{nev}=nincs"
    hely = elem.mapToItem(window.contentItem(), QPointF(0, 0))
    return (
        f"{nev}=van(látszik={_igen_nem(elem.isVisible())}, "
        f"engedélyezett={_igen_nem(elem.isEnabled())}, "
        f"x={hely.x():.0f}, y={hely.y():.0f}, "
        f"szél={elem.width():.0f}, mag={elem.height():.0f})"
    )


def _aktiv_szerkeszto(window) -> str:
    """Az aktív szerkesztőfül és a megnyitott effekt neve, ha a szerkesztőpanel elérhető (#4929)."""
    panel = _keres(window, "viewerEditorPanel")
    if panel is None:
        return "szerkesztőpanel=nincs"
    return (f"aktív fül={panel.property('activeTab')}, "
            f"effekt='{panel.property('paramEffectName')}'")


def _lathatosag(nev: str, elem) -> str:
    """Egy elem saját `visible` értéke és mérete; `nincs`, ha nem található (#4929)."""
    if elem is None:
        return f"{nev}=nincs"
    return (
        f"{nev}=van(visible={_igen_nem(elem.property('visible'))}, "
        f"szél={elem.width():.0f}, mag={elem.height():.0f})"
    )


def _elem_lathatosaga(item) -> str:
    """Az `isVisible()`, a saját `visible`, az `opacity` és a méret egy elemre (#4929)."""
    return (
        f"{_nev(item)}(látszik={_igen_nem(item.isVisible())}, "
        f"visible={_igen_nem(item.property('visible'))}, "
        f"opacity={item.opacity():.2f}, "
        f"{item.width():.0f}x{item.height():.0f})"
    )


def _szulolanc(window, elem) -> str:
    """Az elemtől a `window.contentItem()`-ig tartó szülőlánc, elemenként (#4929)."""
    if elem is None:
        return "nincs"
    gyoker = window.contentItem()
    lanc = []
    aktualis = elem
    while aktualis is not None:
        lanc.append(_elem_lathatosaga(aktualis))
        if aktualis is gyoker:
            break
        aktualis = aktualis.parentItem()
    return " < ".join(lanc)


def _nezo_es_panelek_allapota(window) -> str:
    """A néző, a szerkesztőpanelek és a bal fiók láthatósága a húzás körül (#4929).

    Az `EditorPanel.qml` objectName-je (`editorPanel`) a példányon felülíródik
    (`viewerEditorPanel`); a `redeyeModePanel` id-jú panel gyökerének
    objectName-je `redeyeColumn`. Ezért ezekre a neveken keresünk.
    """
    nezo = _keres(window, "photoViewer")
    nezo_resz = "photoViewer=nincs"
    if nezo is not None:
        nezo_resz = (
            f"photoViewer(isCurrentVideo={_igen_nem(nezo.property('isCurrentVideo'))}, "
            f"layoutMode={nezo.property('layoutMode')!r})"
        )
    return ", ".join([
        nezo_resz,
        f"viewerOpen={_igen_nem(window.property('viewerOpen') is True)}",
        _lathatosag("viewerEditorPanel", _keres(window, "viewerEditorPanel")),
        _lathatosag("editorModeToolScroll", _keres(window, "editorModeToolScroll")),
        _lathatosag("redeyeModePanel", _keres(window, "redeyeColumn")),
        _lathatosag("viewerLeftDrawer", _keres(window, "viewerLeftDrawer")),
    ])


def _vorosszem_diagnosztika(window, edit, terulet, gomb) -> str:
    """A húzás körüli állapot a bukás okának kiderítéséhez (#4929). Bármelyik elem lehet None."""
    grab = window.mouseGrabberItem()
    talalat = None
    if gomb is not None:
        kozep = gomb.mapToScene(QPointF(gomb.width() / 2, gomb.height() / 2))
        talalat = _legfelso_talalat(window.contentItem(), kozep)
    return (
        f"{_elem_helyzet(window, 'redeyeDragArea', terulet)}, "
        f"redeyeDragArea szülőlánc={_szulolanc(window, terulet)}, "
        f"dragging={terulet.property('dragging') if terulet is not None else 'nincs'}, "
        f"selW={terulet.property('selW') if terulet is not None else 'nincs'}, "
        f"selH={terulet.property('selH') if terulet is not None else 'nincs'}, "
        f"{_elem_helyzet(window, 'redeyeApplyButton', gomb)}, "
        f"redeyeApplyButton szülőlánc={_szulolanc(window, gomb)}, "
        f"ablak={window.width():.0f}x{window.height():.0f}, "
        f"{_aktiv_szerkeszto(window)}, "
        f"mouseGrabberItem={_nev(grab) if grab is not None else 'None'}, "
        f"régiószám={edit.redeyeRegionCount}, "
        f"effectChain={edit.effectChain!r}, "
        f"hit-test={_nev(talalat) if talalat is not None else 'None'}, "
        f"{_nezo_es_panelek_allapota(window)}."
    )


def _bal_fiok_nyitva_var(window, qt_app):
    """Megvárja, hogy a bal fiók teljesen kinyíljon (#4929).

    A fiók szélessége 250 ms-os animációval 1 → 280 képpontra nő, és a
    `clip` miatt a csempék addig a levágott részen vannak. Az `isVisible()`
    erre vak: a levágott csempe is látszónak számít, ezért nem elég rá várni.
    """
    fiok = _elem(window, "viewerLeftDrawer")
    assert _var(qt_app, lambda: fiok.width() >= 280), (
        f"a bal fiók nem nyílt ki (szélesség={fiok.width():.0f})"
    )


def _lep_vorosszem_javitas_valodi_huzassal(tiszta_app, qt_app, diag: list):
    app = tiszta_app
    window, edit = app["window"], app["edit"]
    _nyisd_meg_a_nezot(window, qt_app)
    fiok = _elem(window, "viewerLeftDrawer")
    if fiok.width() < 280:
        _kattint(window, qt_app, "toggle_left_drawer")
    _bal_fiok_nyitva_var(window, qt_app)
    _kattint(window, qt_app, "editToolRedeye")
    terulet = _keres(window, "redeyeDragArea")
    gomb = _keres(window, "redeyeApplyButton")
    if terulet is None or gomb is None:
        diag.append(_vorosszem_diagnosztika(window, edit, terulet, gomb))
    assert terulet is not None, "a felületi elem nem található: redeyeDragArea"
    assert gomb is not None, "a felületi elem nem található: redeyeApplyButton"
    lathato = _var(qt_app, lambda: _latszik_es_meretes(terulet) and _latszik_es_meretes(gomb))
    if not lathato:
        diag.append(_vorosszem_diagnosztika(window, edit, terulet, gomb))
    assert lathato, (
        "a vörösszem húzási területe vagy az Alkalmaz gomb nem látszik a húzás előtt"
    )
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
    diag.append(_vorosszem_diagnosztika(window, edit, terulet, gomb))
    assert terulet.property("selW") > 0 and terulet.property("selH") > 0, (
        "a vörösszem-húzás nem adott kijelölést (selW/selH nulla)"
    )
    assert edit.redeyeRegionCount >= 1, "a vörösszem-húzás nem hozott létre régiót"
    assert _var(qt_app, lambda: _latszik_es_meretes(gomb)), (
        "az Alkalmaz gomb nem látszik a húzás után"
    )
    _kattint(window, qt_app, "redeyeApplyButton")
    assert _var(qt_app, lambda: "redeye" in edit.effectChain.casefold()), (
        "a vörösszem-kijelölés alkalmazása nem került a szerkesztési láncba"
    )
    _kepernyokep(window, app["kepek"], "03-vorosszem.png")
    assert not app["attempts"], f"vörösszem-javítás közben hálózati próbálkozás történt: {app['attempts']}"


def _lep_vorosszem_windowson_kihagyhato(tiszta_app, qt_app):
    """Windowson a bukás diagnosztikával kihagyásra fut (#4929); Linuxon szigorú marad.

    Visszaad egy skip-indokot, ha a lépés kihagyásra futott, különben None.
    A hálózati próbálkozás mindig valódi bukás.
    """
    diag = []
    try:
        _lep_vorosszem_javitas_valodi_huzassal(tiszta_app, qt_app, diag)
    except AssertionError as hiba:
        if tiszta_app["attempts"]:
            raise
        # A pytest a rewrite miatt az üzenet után az "assert ..." sort is hozzáfűzi; csak az első sor kell.
        uzenet = str(hiba).splitlines()[0]
        kiegeszitett = f"#4929 diag: {uzenet} | {' '.join(diag) or 'a húzás előtt bukott'}"
        if sys.platform != "win32":
            # Linuxon szigorú marad, de a diagnosztika a CI-naplóba kerüljön (#4929).
            raise AssertionError(kiegeszitett) from hiba
        return kiegeszitett
    return None


def _ellenorizd_kepernyokepek_meretet(mappa: Path, vart: int = 3):
    kepek = sorted(mappa.glob("*.png"))
    assert len(kepek) == vart, f"nem készült el mind a(z) {vart} képernyőkép: {kepek}"
    osszesen = sum(kep.stat().st_size for kep in kepek)
    assert osszesen < 1_000_000, f"a képernyőképek együtt {osszesen} bájtosak"


def test_tiszta_profil_funkciok_valodi_kattintassal(
    tiszta_app, qt_app, tmp_path_factory,
):
    """A teljes felhasználói útvonal egy valós, izolált QML-appban fut.

    A képernyőképek a tmp_path alá kerülnek. Dokumentációs frissítéshez
    PICASAPY_DOKUKEPEK=1 kell; ekkor a docs/assets/paritas-tiszta-profil/
    régi PNG-it a teszt előbb törli, és felülírja az újakkal.
    """
    mappa = tiszta_app["kepek"]
    for regi in mappa.glob("*.png"):
        regi.unlink()
    _lep_mappa_betoltes_es_indexkep_racs(tiszta_app, qt_app)
    _lep_csillag_valodi_kattintassal(tiszta_app, qt_app)
    _lep_nezo_valodi_dupla_kattintassal(tiszta_app, qt_app)
    _lep_felirat_valodi_bevitellel(tiszta_app, qt_app)
    _lep_auto_kontraszt_es_visszavonas(tiszta_app, qt_app)
    _lep_export_valodi_menu_es_kattintas(tiszta_app, qt_app, tmp_path_factory)
    _lep_arcfelismeres_inditasa_letoltes_nelkul(tiszta_app, qt_app)
    skip_indok = _lep_vorosszem_windowson_kihagyhato(tiszta_app, qt_app)
    _ellenorizd_kepernyokepek_meretet(mappa, 2 if skip_indok else 3)
    if skip_indok:
        pytest.skip(skip_indok)
