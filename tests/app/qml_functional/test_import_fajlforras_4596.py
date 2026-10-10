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
from picasapy.scanner.filetypes import PHOTO_EXTENSIONS, VIDEO_EXTENSIONS

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
    QTest.mouseClick(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def test_a_fajlvalaszto_szuroje_a_felismert_halmazt_adja():
    """A „Picture and Movie Files" szűrő a `scanner/filetypes.py` halmaza."""
    szoveg = _QML.read_text(encoding="utf-8")
    blokk = szoveg[szoveg.index("id: sourceFilesDialog"):]
    blokk = blokk[: blokk.index("onAccepted")]
    kiterjesztesek = {m.lower() for m in re.findall(r"\*(\.[a-z0-9]+)", blokk)}
    assert kiterjesztesek == PHOTO_EXTENSIONS | VIDEO_EXTENSIONS


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

    valaszto = _elem(dialog, "importSourceFilesDialog")
    _kattint(dialog, _elem(dialog, "importSourceChooseFilesButton"), qt_app)
    _varj(qt_app, lambda: valaszto.property("visible") is True,
          "a fájlok gomb nem nyitotta meg a fájlválasztót")

    # a natív választó kijelölését a QML-függvénynek adjuk át (az `accepted`
    # ágon ez hívódik a `selectedFiles`-szal)
    urls = [QUrl.fromLocalFile(str(f)) for f in kijelolt]
    scan_done = []
    controller.sourceScanFinished.connect(lambda *_a: scan_done.append(True))
    assert QMetaObject.invokeMethod(
        dialog, "useSelectedFiles", Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", urls),
    )
    _varj(qt_app, lambda: bool(scan_done), "a fájlok beolvasása nem fejeződött be")
    assert int(dialog.property("previewCount")) == 2

    dialog.setProperty("destFolder", str(cel))
    kesz = []
    controller.importFinished.connect(lambda ok, hiba: kesz.append((ok, hiba)))
    _kattint(dialog, _elem(dialog, "importSourceStartButton"), qt_app)
    _varj(qt_app, lambda: bool(kesz), "a fájlok importja nem fejeződött be")

    assert kesz[-1] == (2, 0)
    assert (cel / "2024-03-05" / "a.jpg").is_file()
    assert (cel / "2024-03-05" / "b.jpg").is_file()
    assert not (cel / "2024-03-05" / "c.jpg").exists()
    assert kimaradt.is_file()
