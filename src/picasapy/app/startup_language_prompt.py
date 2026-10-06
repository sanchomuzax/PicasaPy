"""A rendszer-nyelv-felajánlás Quick ablakának induláskori kezelése (#4325)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QEventLoop, QTimer, QTranslator
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

_APP_DIR = Path(__file__).parent
_I18N_DIR = _APP_DIR / "i18n"


def ask_startup_language_prompt(
    system_language: str, *, timeout_ms: int | None = None
) -> bool:
    """A fő felület és végleges fordító betöltése előtt kérdez rá.

    QWidgetet igénylő QMessageBox helyett külön Quick ablakot használ, mert
    az alkalmazás QGuiApplicationnel fut. Ha a célnyelv fordítása elérhető,
    a kérdés idejére betölti, majd eltávolítja azt.

    A `timeout_ms` kizárólag határidős automatizált kattintáspróbához van;
    normál induláskor a felhasználó válaszáig megvárja a modális ablakot."""
    app = QGuiApplication.instance()
    if app is None:
        return False

    translator = QTranslator(app)
    installed = translator.load(f"picasapy_{system_language}", str(_I18N_DIR))
    if installed:
        app.installTranslator(translator)

    engine = QQmlApplicationEngine()
    loop = QEventLoop()
    answer: list[bool] = []
    window = None
    try:
        engine.load(str(_APP_DIR / "qml" / "PicasaPy" / "FirstRunLanguageDialog.qml"))
        roots = engine.rootObjects()
        if not roots:
            return False
        window = roots[0]

        def record_choice(accepted: bool) -> None:
            if not answer:
                answer.append(bool(accepted))
            if loop.isRunning():
                loop.quit()

        window.chosen.connect(record_choice)
        window.show()

        timer = None
        if timeout_ms is not None:
            timer = QTimer()
            timer.setSingleShot(True)
            timer.timeout.connect(loop.quit)
            timer.start(max(0, timeout_ms))
        if not answer:
            loop.exec()
        if timer is not None:
            timer.stop()
        if not answer:
            window.close()
        return answer[0] if answer else False
    finally:
        if window is not None:
            window.close()
        engine.deleteLater()
        app.processEvents()
        if installed:
            app.removeTranslator(translator)
