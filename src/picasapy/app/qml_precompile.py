"""A telepített QML-fájlok előfordítása a felhasználói gyorsítótárba (#6374)."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import threading
import time

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from .application_location import _qml_import_path

#: Haladásnapló: minden fájl a betöltése ELŐTT ide kerül, így elakadáskor a
#: napló utolsó sora megmondja, hol állt meg (a csomagolt, ablakos exe-nek
#: nincs szabványos kimenete).
NAPLO_ENV = "PICASAPY_QML_ELOFORDIT_NAPLO"
#: Belső határidő: a telepítő (`waituntilterminated`) és az önfrissítés vár
#: rá, ezért elakadás esetén magától kilép.
HATARIDO_ENV = "PICASAPY_QML_ELOFORDIT_HATARIDO"
ALAP_HATARIDO_MP = 120.0
HATARIDO_KOD = 3
_kilepes = os._exit


def _naplozz(sor: str) -> None:
    ut = os.environ.get(NAPLO_ENV)
    if not ut:
        return
    try:
        with open(ut, "a", encoding="utf-8") as naplo:
            naplo.write(sor + "\n")
    except OSError:
        pass


def _hatarido_lejart() -> None:
    _naplozz("időtúllépés: az előfordítás nem fejeződött be, kilépés")
    _kilepes(HATARIDO_KOD)


def _inditsd_a_hataridot() -> None:
    try:
        mp = float(os.environ.get(HATARIDO_ENV, ALAP_HATARIDO_MP))
    except ValueError:
        mp = ALAP_HATARIDO_MP
    idozito = threading.Timer(mp, _hatarido_lejart)
    idozito.daemon = True
    idozito.start()


def _qml_konyvtar() -> Path:
    """A telepített alkalmazáshoz csomagolt QML-fa."""
    return Path(__file__).resolve().parent / "qml"


def _forditsd_le(engine: QQmlEngine, fajlok: list[Path]) -> int:
    hibas = 0
    for fajl in fajlok:
        _naplozz(f"fordítás: {fajl}")
        komponens = QQmlComponent(engine)
        komponens.loadUrl(
            QUrl.fromLocalFile(str(fajl)),
            QQmlComponent.CompilationMode.PreferSynchronous,
        )
        if komponens.status() == QQmlComponent.Status.Loading:
            komponens.waitForDone()
        if komponens.status() == QQmlComponent.Status.Error:
            hibas += 1
    return hibas


def main() -> int:
    """Fordítja a QML-fájlokat, a hibákat összesíti és sikeres kóddal kilép."""
    _inditsd_a_hataridot()
    _naplozz("előfordítás indul")
    os.environ["QT_QPA_PLATFORM"] = "offscreen"
    os.environ.setdefault("QT_QUICK_BACKEND", "software")
    os.environ["QT_QPA_PLATFORMTHEME"] = "generic"

    QCoreApplication.setOrganizationName("PicasaPy")
    QCoreApplication.setApplicationName("PicasaPy")
    app = QGuiApplication([sys.argv[0]])
    app.setApplicationName("PicasaPy")
    app.setOrganizationName("PicasaPy")

    qml_root = _qml_konyvtar()
    engine = QQmlEngine()
    engine.addImportPath(_qml_import_path())
    fajlok = sorted(qml_root.rglob("*.qml"))
    started = time.perf_counter()
    hibas = _forditsd_le(engine, fajlok)
    eltelt = time.perf_counter() - started
    osszegzes = f"QML-előfordítás: {len(fajlok)} fájl, {hibas} hibás, {eltelt:.2f} s"
    _naplozz(osszegzes)
    print(osszegzes, flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
