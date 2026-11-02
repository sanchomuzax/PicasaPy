"""A telepített QML-fájlok előfordítása a felhasználói gyorsítótárba (#6374)."""

from __future__ import annotations

import os
from pathlib import Path
import sys
import time

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent, QQmlEngine

from .application_location import _qml_import_path


def _qml_konyvtar() -> Path:
    """A telepített alkalmazáshoz csomagolt QML-fa."""
    return Path(__file__).resolve().parent / "qml"


def _forditsd_le(engine: QQmlEngine, fajlok: list[Path]) -> int:
    hibas = 0
    for fajl in fajlok:
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
    print(
        f"QML-előfordítás: {len(fajlok)} fájl, {hibas} hibás, {eltelt:.2f} s",
        flush=True,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
