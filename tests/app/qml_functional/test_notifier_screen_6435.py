"""#6435: az értesítősáv a valódi főablak képernyőjére kerül."""

from __future__ import annotations

import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile

import pytest


_ROOT = Path(__file__).resolve().parents[3]
_QML_DIR = _ROOT / "src" / "picasapy" / "app" / "qml"
_STARTUP_QML = _ROOT / "src" / "picasapy" / "app" / "application_startup_qml.py"
_CHILD = r'''
import json
import sys
import time

from PySide6.QtCore import QSize, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQuick import QQuickWindow
from PySide6.QtQml import QQmlComponent, QQmlEngine
from picasapy.app.notifier_screen_geometry import NotifierScreenGeometry


config_path, target_name, height_delta, qml_dir = sys.argv[1:]
app = QGuiApplication([])
screens = {screen.name(): screen for screen in app.screens()}
assert set(screens) == {"BAL", "JOBB"}, sorted(screens)
assert screens["BAL"].geometry().getRect() == (0, 0, 1920, 1080)
assert screens["JOBB"].geometry().getRect() == (1920, 0, 1920, 1080)


def varj_feltetelre(feltetel, leiras):
    hatarido = time.monotonic() + 3.0
    while time.monotonic() < hatarido:
        app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"Időtúllépés: {leiras}")


celozott = screens[target_name]
masik_nev = "JOBB" if target_name == "BAL" else "BAL"
masik = screens[masik_nev]
engine = QQmlEngine()
engine.addImportPath(qml_dir)
screen_geometry = NotifierScreenGeometry()
engine.rootContext().setContextProperty(
    "notifierScreenGeometry", screen_geometry
)
foablak_component = QQmlComponent(engine)
foablak_component.setData(
    b'import QtQuick; import QtQuick.Window; '
    b'Window { objectName: "mainWindow"; visible: false; '
    b'width: 640; height: 600 }',
    QUrl(),
)
foablak = foablak_component.create()
assert isinstance(foablak, QQuickWindow), foablak_component.errorString()
foablak.setGeometry(
    celozott.geometry().x() + 100,
    celozott.geometry().y() + 100,
    640,
    600 + int(height_delta),
)
foablak.show()
varj_feltetelre(
    lambda: foablak.screen().name() == target_name,
    f"a főablak a {target_name} képernyőre kerüljön",
)
component = QQmlComponent(
    engine, qml_dir + "/PicasaPy/PicasaNotifier.qml"
)
notifier = component.createWithInitialProperties({"_hostWindow": foablak})
assert notifier is not None, component.errorString()


def vart_pozicio(screen):
    area = screen.availableGeometry()
    return (
        area.x() + area.width() - notifier.width(),
        area.y() + area.height() - notifier.property("anchorOffsetPx"),
    )


def ellenoriz_poziciot(screen, leiras):
    x, y = vart_pozicio(screen)
    lk = notifier.property("_lastKnownScreen")
    allapot = (
        f"főablak: visible={foablak.isVisible()} visibility={foablak.visibility()} "
        f"{foablak.width()}x{foablak.height()} képernyő={foablak.screen().name()}; "
        f"utolsó={lk.property('name') if lk else None}"
    )
    assert notifier.x() == x, f"{leiras}: x={notifier.x()}, várt x={x}; {allapot}"
    assert notifier.y() == y, f"{leiras}: y={notifier.y()}, várt y={y}"


try:
    ellenoriz_poziciot(celozott, f"induláskor a {target_name} képernyőn")
    notifier.notify("screen-test", "Rendered", "", "")
    varj_feltetelre(
        lambda: notifier.isVisible(),
        "az értesítő megjelenjen",
    )
    oszlop = notifier.contentItem().childItems()[0]
    varj_feltetelre(
        lambda: oszlop.opacity() >= 0.99,
        "az értesítő megjelenési animációja befejeződjön",
    )
    kep = notifier.grabWindow()
    assert not kep.isNull(), "az értesítő ablakáról készüljön renderelt kép"

    # Rejtett főablaknál a legutóbbi használható képernyő maradjon meg.
    foablak.hide()
    foablak.setPosition(masik.geometry().x() + 100, masik.geometry().y() + 100)
    app.processEvents()
    ellenoriz_poziciot(celozott, "rejtett főablaknál")

    # A látható, használható főablak képernyőváltása költöztesse az értesítőt.
    foablak.show()
    foablak.setPosition(masik.geometry().x() + 100, masik.geometry().y() + 100)
    varj_feltetelre(
        lambda: foablak.screen().name() == masik_nev,
        f"a főablak a {masik_nev} képernyőre kerüljön",
    )
    varj_feltetelre(
        lambda: notifier.x() == vart_pozicio(masik)[0],
        f"az értesítő a {masik_nev} képernyőre kerüljön",
    )
    ellenoriz_poziciot(masik, "képernyőváltás után")

    # Az 1x1-es, használhatatlan főablak képernyőváltása se írja felül az
    # utolsó használható képernyőt.
    foablak.setMinimumSize(QSize(1, 1))
    foablak.setWidth(1)
    foablak.setHeight(1)
    # A méretváltás a platformon aszinkron is lehet: a képernyőváltás csak
    # azután jöjjön, hogy a főablak már ténylegesen 1x1-es.
    varj_feltetelre(
        lambda: foablak.width() <= 1 and foablak.height() <= 1,
        "a főablak 1x1-es legyen a képernyőváltás előtt",
    )
    foablak.setPosition(celozott.geometry().x() + 100, celozott.geometry().y() + 100)
    app.processEvents()
    ellenoriz_poziciot(masik, "kis méretű főablaknál")
    print(json.dumps({"target": target_name, "height_delta": int(height_delta)}))
finally:
    notifier.close()
    foablak.close()
    engine.deleteLater()
    app.processEvents()
'''


def test_az_inditas_a_kepernyosegedet_a_qml_kornyezetbe_regisztralja() -> None:
    startup = _STARTUP_QML.read_text(encoding="utf-8")
    assert "notifier_screen_geometry = NotifierScreenGeometry(parent=app)" in startup
    assert '"notifierScreenGeometry", notifier_screen_geometry' in startup
    assert "state.notifier_screen_geometry = notifier_screen_geometry" in startup


@pytest.mark.parametrize("screen_name", ["BAL", "JOBB"])
@pytest.mark.parametrize("height_delta", [-5, 0, 5])
def test_a_valodi_foablak_kepernyojen_renderel_es_megtartja_az_utolsot(
    screen_name: str, height_delta: int
) -> None:
    with tempfile.TemporaryDirectory(prefix="notifier-screen-6435-") as temp_dir:
        config_path = Path(temp_dir) / "ket-kepernyo.json"
        config_path.write_text(
            json.dumps(
                {
                    "synchronousWindowSystemEvents": False,
                    "windowFrameMargins": False,
                    "screens": [
                        {
                            "name": "BAL",
                            "x": 0,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "logicalDpi": 96,
                            "logicalBaseDpi": 96,
                            "dpr": 1,
                        },
                        {
                            "name": "JOBB",
                            "x": 1920,
                            "y": 0,
                            "width": 1920,
                            "height": 1080,
                            "logicalDpi": 96,
                            "logicalBaseDpi": 96,
                            "dpr": 1,
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        kornyezet = os.environ.copy()
        kornyezet["QT_QPA_PLATFORM"] = f"offscreen:configfile={config_path}"
        kornyezet["QT_QUICK_BACKEND"] = "software"
        pythonpath = [str(_ROOT / "src"), str(_ROOT / "tests")]
        if kornyezet.get("PYTHONPATH"):
            pythonpath.append(kornyezet["PYTHONPATH"])
        kornyezet["PYTHONPATH"] = os.pathsep.join(pythonpath)
        eredmeny = subprocess.run(
            [
                sys.executable,
                "-c",
                _CHILD,
                str(config_path),
                screen_name,
                str(height_delta),
                str(_QML_DIR),
            ],
            cwd=_ROOT,
            env=kornyezet,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=20,
            check=False,
        )
        assert eredmeny.returncode == 0, (
            f"A {screen_name} képernyőre célzott QML-próba elbukott "
            f"({eredmeny.returncode}).\nstdout:\n{eredmeny.stdout}"
            f"\nstderr:\n{eredmeny.stderr}"
        )
        assert json.loads(eredmeny.stdout.strip().splitlines()[-1]) == {
            "target": screen_name,
            "height_delta": height_delta,
        }
