"""#4596: valódi kattintással a fájlválasztó útja — két kijelölt fájl importja.

A natív fájlválasztó offscreen nem ad kattintható ablakot, ezért a
kijelölést és az `accepted` jelet a Qt Quick Dialogs bevett mintájával
adjuk meg (ld. `test_import_destination_beallitas_4450.py`); a gomb
megnyomása, a beolvasás, az előnézet és az import a valódi úton fut.
Amit ez NEM mér: a natív választó megjelenését és szűrőinek működését.
"""

from __future__ import annotations

import re
import time
from pathlib import Path

from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt, QUrl
from PySide6.QtTest import QTest

import picasapy.app
from picasapy.scanner.filetypes import PHOTO_EXTENSIONS, RAW_EXTENSIONS, VIDEO_EXTENSIONS

from support.jpeg_factory import make_jpeg

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy" / "ImportSourceDialog.qml"


def _elem(root, name: str):
    result = root.findChild(QObject, name)
    assert result is not None, f"{name} nem található"
    return result


def _varj(qt_app, condition, message: str, seconds: float = 5.0) -> None:
    deadline = time.monotonic() + seconds
    while time.monotonic() < deadline:
        qt_app.processEvents()
        if condition():
            return
        time.sleep(0.01)
    qt_app.processEvents()
    assert condition(), message


def _kattint(window, item, qt_app) -> None:
    assert item.isEnabled() and item.width() > 0 and item.height() > 0
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    # A kattintás csak az ablakon BELÜL ér célba — kisebb CI-képernyőn ez
    # nem magától értetődő, ezért kimondjuk.
    assert 0 <= center.x() < window.width() and 0 <= center.y() < window.height(), (
        f"a kattintás helye ({center.x():.0f},{center.y():.0f}) kívül esik "
        f"az ablakon ({window.width()}x{window.height()})"
    )
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _globok(szoveg: str, nev: str) -> set[str]:
    """A `nev` nevű QML-tulajdonság értékének kiterjesztései."""
    kezdet = szoveg.index(f"readonly property string {nev}:")
    veg = min(
        i for i in (
            szoveg.find("readonly property", kezdet + 10),
            szoveg.find("nameFilters", kezdet),
        ) if i > 0
    )
    return {m.lower() for m in re.findall(r"\*(\.[a-z0-9]+)", szoveg[kezdet:veg])}


def test_a_fajlvalaszto_szurobe_a_felismert_halmaz_kerul():
    """„Képek és filmek” = fotó + RAW + videó, „Képek” = fotó + RAW (mint a
    beolvasás `_FILTER_KINDS`-e); a hivatalos szűrőcímekkel."""
    szoveg = _QML.read_text(encoding="utf-8")
    kepek = _globok(szoveg, "pictureGlobs")
    filmek = _globok(szoveg, "movieGlobs")
    assert kepek == PHOTO_EXTENSIONS | RAW_EXTENSIONS
    assert filmek == VIDEO_EXTENSIONS
    for felirat in ('qsTr("Picture and Movie Files")', 'qsTr("Picture Files")',
                    'qsTr("All Files")'):
        assert felirat in szoveg


def test_kijelolt_fajlok_kattintassal_forraskent_importalodnak(
    qml_app, qt_app, tmp_path
):
    main_window, _app, engine = qml_app
    controller = engine.rootContext().contextProperty("importSourceController")
    assert controller is not None

    forras = tmp_path / "forras"
    forras.mkdir()
    kijelolt = [forras / "a.jpg", forras / "b.jpg"]
    kimaradt = forras / "c.jpg"
    for fajl in (*kijelolt, kimaradt):
        make_jpeg(fajl, taken_at="2024:03:05 10:00:00")
    cel = tmp_path / "cel"
    cel.mkdir()

    _kattint(main_window, _elem(main_window, "toolbarImportButton"), qt_app)
    _varj(qt_app, lambda: main_window.findChild(QObject, "importSourceDialog") is not None,
          "az Import gomb nem hozta létre a párbeszédet")
    dialog = _elem(main_window, "importSourceDialog")
    _varj(qt_app, lambda: bool(dialog.property("visible")), "az importablak nem nyílt meg")
    # rögzített, a teljes tartalomnak elég ablakméret — a CI képernyője kisebb
    dialog.setProperty("width", 640)
    dialog.setProperty("height", 860)
    qt_app.processEvents()

    valaszto = _elem(dialog, "importSourceFilesDialog")
    _kattint(dialog, _elem(dialog, "importSourceChooseSourceButton"), qt_app)
    menu = _elem(dialog, "importSourceChooseMenu")
    _varj(qt_app, lambda: menu.property("visible") is True,
          "a Tallózás gomb nem nyitotta meg a menüt")
    _varj(qt_app, lambda: _elem(dialog, "importSourceChooseFilesItem").width() > 0,
          "a menü tételei nem épültek fel")
    _kattint(dialog, _elem(dialog, "importSourceChooseFilesItem"), qt_app)
    _varj(qt_app, lambda: valaszto.property("visible") is True,
          "a Fájlok… menüpont nem nyitotta meg a fájlválasztót")

    # a natív választó offscreen nem kattintható: a kijelölést `selectedFile`
    # adja, és az `accepted` jel az `onAccepted` kötést futtatja (az `accept()`
    # offscreen kiüríti a kijelölést, ezért azt nem használjuk)
    scan_done = []
    controller.sourceScanFinished.connect(lambda *_a: scan_done.append(True))
    valaszto.setProperty("selectedFile", QUrl.fromLocalFile(str(kijelolt[0])))
    assert QMetaObject.invokeMethod(valaszto, "accepted", Qt.ConnectionType.DirectConnection)
    # A kiváltott `accepted` jel nem zárja be a választót; nem natív (Qt Quick)
    # párbeszédnél a nyitva maradt ablak a további kattintásokat elnyelné —
    # a valódi elfogadás bezárja, tehát itt is be kell zárni.
    assert QMetaObject.invokeMethod(valaszto, "close", Qt.ConnectionType.DirectConnection)
    _varj(qt_app, lambda: valaszto.property("visible") is not True, "a fájlválasztó nem zárult be")
    _varj(qt_app, lambda: bool(scan_done), "az onAccepted nem indította a beolvasást")
    assert int(dialog.property("previewCount")) == 1
    assert dialog.property("sourceFiles").toVariant() == [QUrl.fromLocalFile(str(kijelolt[0])).toString()]
    scan_done.clear()

    # a többfájlos kijelölés a `useSelectedFiles` függvényen át (a
    # `selectedFiles` csak olvasható)
    urls = [QUrl.fromLocalFile(str(f)) for f in kijelolt]
    assert QMetaObject.invokeMethod(
        dialog, "useSelectedFiles", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", urls),
    )
    _varj(qt_app, lambda: bool(scan_done), "a fájlok beolvasása nem fejeződött be")
    assert int(dialog.property("previewCount")) == 2

    dialog.setProperty("destFolder", str(cel))
    kesz = []
    indult = []
    controller.importFinished.connect(lambda ok, hiba: kesz.append((ok, hiba)))
    controller.importStarted.connect(lambda *a: indult.append(a))
    _kattint(dialog, _elem(dialog, "importSourceStartButton"), qt_app)
    _varj(qt_app, lambda: bool(indult), "az Importálás gomb kattintása nem indította el az importot")
    _varj(qt_app, lambda: bool(kesz), "a fájlok importja nem fejeződött be", seconds=30.0)

    assert kesz[-1] == (2, 0)
    assert (cel / "2024-03-05" / "a.jpg").is_file()
    assert (cel / "2024-03-05" / "b.jpg").is_file()
    assert not (cel / "2024-03-05" / "c.jpg").exists()
    assert kimaradt.is_file()

    # fájlforrás után mappaválasztás: a fájllista törlődik, a mappa teljes
    # tartalma (3 kép) beolvasódik
    mappa_valaszto = _elem(dialog, "importSourceFolderDialog")
    scan_done.clear()
    _kattint(dialog, _elem(dialog, "importSourceChooseSourceButton"), qt_app)
    _varj(qt_app, lambda: _elem(dialog, "importSourceChooseFolderItem").width() > 0,
          "a menü nem nyílt meg újra")
    _kattint(dialog, _elem(dialog, "importSourceChooseFolderItem"), qt_app)
    _varj(qt_app, lambda: mappa_valaszto.property("visible") is True,
          "a Mappa… menüpont nem nyitotta meg a mappaválasztót")
    mappa_valaszto.setProperty("selectedFolder", QUrl.fromLocalFile(str(forras)))
    assert QMetaObject.invokeMethod(
        mappa_valaszto, "accepted", Qt.ConnectionType.DirectConnection
    )
    _varj(qt_app, lambda: bool(scan_done), "a mappa beolvasása nem indult")
    assert dialog.property("sourceFiles").toVariant() == []
    assert int(dialog.property("previewCount")) == 3
