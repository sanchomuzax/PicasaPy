"""#3005: a komponensek vezérlő NÉLKÜL sem dobhatnak `ReferenceError`-t.

## A kiváltó eset

A #798-ban egy kötés így épült fel:

```qml
property bool x: (editController && editController.shiftAktiv !== undefined)
                 ? editController.shiftAktiv : false
```

A `scripts/qml_undefined_or.py` **átengedte**: a `!== undefined` záradékot
őrzésnek látta. A QML viszont a **csupasz névnél** eldobja a kiértékelést,
ha a kontextus-tulajdonság nincs beállítva — a `&&` már el sem indul. A
CI ubuntu-lába három QML-tesztfájlt bukott el rá; helyben minden zöld volt,
mert azok a próbák beállítják a vezérlőt.

A helyes alak a `typeof`-fal kezdődik:

```qml
property bool x: (typeof editController !== "undefined" && editController
                  && editController.shiftAktiv !== undefined)
                 ? editController.shiftAktiv : false
```

## Miért VISELKEDÉSI őr, és nem forrás-szabály

Mérve: a fában **296 kötés** hivatkozik vezérlőre `typeof` nélkül, 35
fájlban. A többségük soha nem épül fel vezérlő nélkül (a `Main.qml`
egésze ilyen), tehát a forrás-szintű tiltás 296 hamis riasztás lenne — és
egy zajos őrt a következő kör kikapcsol.

Ez az őr ehelyett **felépíti** mind a komponenst kontextus-tulajdonság
nélkül, és a Qt üzenetnaplóját nézi. Az alapállapot a mai fa 14 fájlja; a
lista **rövidülhet, de nem hízhat** — új komponensnek `typeof`-fal kell
írnia a vezérlő-hivatkozásait.

⚠️ A `TypeError: Cannot read property 'x' of undefined` SZÁNDÉKOSAN nem
számít: az a `&&`-idióm normális mellékhatása, a kötés `undefined`-ot ad,
de a komponens felépül.
"""

from __future__ import annotations

import re
from pathlib import Path

import picasapy.app
import pytest
from PySide6.QtCore import QUrl, qInstallMessageHandler
from PySide6.QtQml import QQmlComponent, QQmlEngine

_QML = Path(picasapy.app.__file__).parent / "qml"

#: A mai fa állapota (mérve 2026-09-11). Ezek a komponensek vezérlő nélkül
#: `ReferenceError`-t adnak; egyik sem épül fel így a próbákban, ezért ma
#: nem fáj. A lista NEM hízhat: új tétel azt jelenti, hogy egy komponens
#: elvesztette a `typeof`-őrét.
ALAPALLAPOT: frozenset[str] = frozenset(
    {
        "AboutDialog.qml",
        "CreateDialogs.qml",
        "FolderManagerDialog.qml",
        "FolderPane.qml",
        "HelpDialog.qml",
        "LightboxFeed.qml",
        "MainToolbar.qml",
        "OptionsDialog.qml",
        "OptionsTabGeneral.qml",
        "PhotoViewer.qml",
        "PicasaImportDialog.qml",
        "PicasaMenuBar.qml",
        "PlacesPanel.qml",
        "TrayBar.qml",
    }
)


def _hibas_komponensek(qt_app) -> dict[str, list[str]]:
    """Fájlnév → a `ReferenceError`-ok, vezérlő NÉLKÜLI felépítéskor."""
    uzenetek: list[str] = []
    korabbi = qInstallMessageHandler(
        lambda tipus, kontextus, uzenet: uzenetek.append(uzenet)
    )
    talalat: dict[str, list[str]] = {}
    try:
        for fajl in sorted((_QML / "PicasaPy").glob("*.qml")):
            uzenetek.clear()
            motor = QQmlEngine()
            motor.addImportPath(str(_QML))
            komponens = QQmlComponent(motor, QUrl.fromLocalFile(str(fajl)))
            elem = komponens.create()
            hibak = sorted(
                {
                    re.sub(r".*ReferenceError: ", "", uzenet)
                    for uzenet in uzenetek
                    if "ReferenceError" in uzenet
                }
            )
            if hibak:
                talalat[fajl.name] = hibak
            if elem is not None:
                elem.deleteLater()
            motor.deleteLater()
    finally:
        qInstallMessageHandler(korabbi)
    return talalat


@pytest.fixture(scope="module")
def merés(qt_app):
    return _hibas_komponensek(qt_app)


class TestAFelepules:
    def test_a_lista_NEM_hizhat(self, merés):
        ujak = sorted(set(merés) - ALAPALLAPOT)
        assert not ujak, (
            "vezérlő nélkül `ReferenceError`-t dobó ÚJ komponens(ek): "
            + ", ".join(
                f"{nev} ({', '.join(merés[nev])})" for nev in ujak
            )
            + " — a vezérlő-hivatkozást `typeof VEZERLO !== \"undefined\"`"
            " őrrel kell kezdeni"
        )

    def test_az_alapallapot_nem_avult_el(self, merés):
        """Ha egy tétel megjavult, kerüljön ki a listából — különben a
        lista hamis tartozást tart életben."""
        eltuntek = sorted(ALAPALLAPOT - set(merés))
        assert not eltuntek, (
            "ezek MÁR nem dobnak hibát, vedd ki az alapállapotból: "
            + ", ".join(eltuntek)
        )

    def test_a_mero_talalt_is_valamit(self, merés):
        """Pozitív kontroll: üres halmazon az őr semmit nem őrizne."""
        assert merés, "egyetlen komponenst sem sikerült felépíteni — a mérő vak"
