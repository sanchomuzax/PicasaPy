"""QML-funkcionális tesztek: SplashScreen.qml (#189).

A splash komponenst önállóan (QQmlComponent) töltjük — a Main.qml-be kötést
az integrátor végzi (ld. docs/notes/splash-bekotes.md), a viselkedés viszont
itt, a komponens szintjén ellenőrizhető: megjelenik, a statusText változása
látszik, és `ready=true`-ra kifakulva eltűnik.
"""

from PySide6.QtCore import QElapsedTimer, QObject, QUrl
from PySide6.QtQml import QQmlComponent

import picasapy.app.application as app_module

# A létrehozott QQmlComponent-eket életben kell tartani a teszt végéig: ha a
# komponens felszabadul (a segédfüggvényből kilépve), a belőle létrehozott
# QQuickItem C++ oldala is törlődik, és a property-lekérdezés „already
# deleted"-tel esik el.
_KEEP_ALIVE: list = []


def _make_splash(engine, **props):
    comp = QQmlComponent(
        engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "SplashScreen.qml")
        ),
    )
    _KEEP_ALIVE.append(comp)
    base = {"version": "v0.4.31 (test)", "statusText": "Indulás…", "ready": False}
    base.update(props)
    splash = comp.createWithInitialProperties(base)
    assert comp.errors() == [], comp.errors()
    assert splash is not None
    _KEEP_ALIVE.append(splash)
    return splash


def _wait_until(qt_app, predicate, timeout_ms=2000):
    """Valós idő-alapú várakozás: addig pörgeti az eseményhurkot, amíg a
    feltétel teljesül vagy lejár az idő (az opacity-Behavior animációhoz)."""
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < timeout_ms:
        qt_app.processEvents()
        if predicate():
            return True
    return False


class TestSplashScreen:
    def test_appears_with_version_and_status(self, qml_app, qt_app):
        _, _, _, engine = qml_app
        splash = _make_splash(engine)
        assert splash.property("visible") is True
        assert splash.property("busy") is True

        version = splash.findChild(QObject, "splashVersionLabel")
        assert version is not None, "splashVersionLabel nem található"
        assert "v0.4.31 (test)" in version.property("text")

        status = splash.findChild(QObject, "splashStatusText")
        assert status is not None, "splashStatusText nem található"
        assert status.property("text") == "Indulás…"

    def test_status_text_change_is_reflected(self, qml_app, qt_app):
        _, _, _, engine = qml_app
        splash = _make_splash(engine)
        status = splash.findChild(QObject, "splashStatusText")
        splash.setProperty("statusText", "Mappák beolvasása…")
        qt_app.processEvents()
        assert status.property("text") == "Mappák beolvasása…"

    def test_busy_bar_and_sweep_present_while_busy(self, qml_app, qt_app):
        _, _, _, engine = qml_app
        splash = _make_splash(engine)
        bar = splash.findChild(QObject, "splashBusyBar")
        sweep = splash.findChild(QObject, "splashSweep")
        assert bar is not None and sweep is not None
        # a sáv 12–14 px magas, a fénycsík fut (busy)
        assert 12 <= bar.property("height") <= 14
        assert sweep.property("visible") is True

    def test_disappears_on_ready(self, qml_app, qt_app):
        _, _, _, engine = qml_app
        splash = _make_splash(engine)
        assert splash.property("visible") is True
        splash.setProperty("ready", True)
        # a kifakulás után (opacity → 0) a láthatóság hamisra vált
        assert _wait_until(qt_app, lambda: splash.property("visible") is False), (
            "a splash nem tűnt el ready=true után"
        )
        assert splash.property("busy") is False
        # a fénycsík is megáll (nem látszik)
        sweep = splash.findChild(QObject, "splashSweep")
        assert sweep.property("visible") is False
