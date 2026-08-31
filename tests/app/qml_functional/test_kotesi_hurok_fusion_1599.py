"""#1599 — a kötési hurok őre a FUSION stílussal, külön processzben.

**Miért külön processz.** A `QT_QUICK_CONTROLS_STYLE`-t a Qt a
`QGuiApplication` létrehozásakor olvassa be; a tesztkészletben addigra már
áll az alkalmazás, tehát egy teszt NEM tud stílust váltani. A #1599 hurka
viszont KIZÁRÓLAG Fusionnel jön elő (a fejlesztői alapstílussal nem) — ezért
maradt hónapokig észrevétlen, és ezért a tulajdonos jelentette, Windowsról.

Ez a teszt ezért gyerekprocesszt indít `QT_QUICK_CONTROLS_STYLE=Fusion`
környezettel, betölti benne az `ExportDialogs`-t, megnyitja a két
eredmény-párbeszédet hosszú üzenettel, és a Qt ÖSSZES üzenetét átnézi
kötési hurokra.

A `support/qml_warning_filter.py`-ba felvett `Binding loop detected` minta
a többi tesztet is őrzi — de csak azzal a stílussal, amivel futnak. Ez a
fájl a hiányzó stílust pótolja.
"""

from __future__ import annotations

import os
import subprocess
import sys
import textwrap
from pathlib import Path

import pytest

_GYEREK = textwrap.dedent(
    '''
    import os, sys
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    from PySide6.QtCore import QObject, QUrl, qInstallMessageHandler
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine
    from PySide6.QtQuick import QQuickItem  # a QQuickItem* konverterhez
    from pathlib import Path
    import picasapy.app

    uzenetek = []
    qInstallMessageHandler(lambda t, ctx, msg: uzenetek.append(msg))

    app = QGuiApplication(sys.argv[:1])
    motor = QQmlEngine()
    motor.addImportPath(str(Path(picasapy.app.__file__).parent / "qml"))
    komponens = QQmlComponent(motor)
    komponens.setData(b"""
    import QtQuick
    import QtQuick.Controls
    import PicasaPy 1.0
    ApplicationWindow { width: 900; height: 500; visible: true
      ExportDialogs { objectName: "exportDialogs"; appWindow: null } }
    """, QUrl())
    ablak = komponens.create()
    if ablak is None:
        print("LETREHOZASI-HIBA:", komponens.errorString())
        sys.exit(2)
    QQmlEngine.setObjectOwnership(ablak, QQmlEngine.ObjectOwnership.CppOwnership)
    app.processEvents()

    hosszu = ("Unable to save all files due to a disk error. "
              "IMG_20260827_183045_nyaralas_horvatorszag.jpg — "
              "error(28): No space left on device") * 2
    talalt = 0
    for nev in ("exportResultDialog", "earthResultDialog"):
        p = ablak.findChild(QObject, nev)
        if p is None:
            print("HIANYZO-PARBESZED:", nev)
            sys.exit(3)
        talalt += 1
        p.setProperty("message", hosszu)
        p.setProperty("visible", True)
        app.processEvents()
        print("SZELESSEG", nev, p.property("width"))
        p.setProperty("visible", False)
        app.processEvents()

    print("MEGNYITOTT-PARBESZEDEK", talalt)
    print("STILUS", os.environ.get("QT_QUICK_CONTROLS_STYLE"))
    for m in uzenetek:
        if "Binding loop" in m:
            print("HUROK:", m.replace(chr(10), " | "))
    print("VEGE")
    '''
)


@pytest.fixture(scope="module")
def gyerek_kimenet(tmp_path_factory):
    gyoker = Path(__file__).resolve().parents[3]
    szkript = tmp_path_factory.mktemp("hurok") / "fusion_proba.py"
    szkript.write_text(_GYEREK, encoding="utf-8")

    kornyezet = dict(os.environ)
    kornyezet["QT_QUICK_CONTROLS_STYLE"] = "Fusion"
    kornyezet["QT_QPA_PLATFORM"] = "offscreen"
    kornyezet["PYTHONPATH"] = os.pathsep.join(
        [str(gyoker / "src"), kornyezet.get("PYTHONPATH", "")]
    )
    eredmeny = subprocess.run(
        [sys.executable, str(szkript)],
        capture_output=True,
        text=True,
        timeout=180,
        cwd=str(gyoker),
        env=kornyezet,
    )
    assert eredmeny.returncode == 0, (
        f"a Fusion-próba {eredmeny.returncode} kóddal állt le\n"
        f"{eredmeny.stdout[-2000:]}\n{eredmeny.stderr[-2000:]}"
    )
    return eredmeny.stdout


class TestFusionKotesiHurok:
    def test_a_proba_tenyleg_lefutott_fusionnel(self, gyerek_kimenet):
        """Pozitív kontroll: üres kimenetre minden állítás zölden hazudna."""
        assert "VEGE" in gyerek_kimenet, gyerek_kimenet[-1500:]
        assert "STILUS Fusion" in gyerek_kimenet, (
            "a gyerekprocessz nem Fusion stílussal futott — a hurok ezzel a "
            "próbával nem is jönne elő"
        )
        assert "MEGNYITOTT-PARBESZEDEK 2" in gyerek_kimenet, (
            "nem mind a két eredmény-párbeszéd nyílt meg"
        )

    def test_nincs_kotesi_hurok(self, gyerek_kimenet):
        hurkok = [
            sor for sor in gyerek_kimenet.splitlines()
            if sor.startswith("HUROK:")
        ]
        assert hurkok == [], (
            "kötési hurok a Fusion stílusú megnyitáskor (#1599):\n"
            + "\n".join(hurkok)
        )
