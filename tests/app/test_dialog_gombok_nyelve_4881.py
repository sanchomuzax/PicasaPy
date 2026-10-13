"""#4881: a párbeszédek szabványos gombjai a VÁLASZTOTT felületi nyelven
jelennek meg, nem a rendszer nyelvén — a területi beállítás (tizedesjel,
mértékegység) viszont a rendszeré marad (ADR-004).

Nyelvenként KÜLÖN folyamatban fut, magyar RENDSZERLOCALE-lal (`LANG`/`LC_ALL`):
a nyelv az indításkor dől el (#3555), és a Quick Controls az első használatkor
megjegyzi a Qt saját fordítását, tehát egy folyamatban nem lehet nyelvet cserélni.
"""

from __future__ import annotations

import os
import subprocess
import sys

import pytest

_PROBA = """
import os
os.environ["QT_QPA_PLATFORM"] = "offscreen"
from PySide6.QtCore import Q_RETURN_ARG, QLocale, QMetaObject, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine
from picasapy.app import application
from picasapy.printing import dpi

app = QGuiApplication([])
application._install_translator(app)
application.allitsd_be_a_stilust()
engine = QQmlApplicationEngine()
engine.addImportPath(str(application._APP_DIR / "qml"))
engine.loadData(b'''
import QtQuick
import QtQuick.Controls
ApplicationWindow {
    function cancelFelirat() { return String(proba.standardButton(Dialog.Cancel).text) }
    Dialog { id: proba; standardButtons: Dialog.Ok | Dialog.Cancel }
}
''')
ablak = engine.rootObjects()[0]
print("FELIRAT=" + str(QMetaObject.invokeMethod(
    ablak, "cancelFelirat", Qt.ConnectionType.DirectConnection, Q_RETURN_ARG("QVariant"))))
print("TIZEDESJEL=" + QLocale().decimalPoint())
print("NEV=" + QLocale().name())
print("METRIKUS=" + str(dpi.keszlet_teruleti_mereshez() == dpi.METRIKUS_KESZLET))
"""


#: A „magyar rendszer” a LANG/LC_ALL környezeti változóval utánzott; Windowson
#: a Qt a területi beállítást az operációs rendszerből veszi, ezért ott ez a
#: próba nem a mért helyzetet állítaná elő.
_CSAK_POSIX_LOCALE = pytest.mark.skipif(
    sys.platform == "win32", reason="Windowson a LANG nem állítja a Qt területi beállítását"
)


def _futtasd(nyelv: str, monkeypatch) -> dict[str, str]:
    monkeypatch.setenv("PICASAPY_LANG", nyelv)
    monkeypatch.setenv("LANG", "hu_HU.UTF-8")
    monkeypatch.setenv("LC_ALL", "hu_HU.UTF-8")
    monkeypatch.setenv("PYTHONPATH", os.pathsep.join(sys.path))
    # Windowson a gyermek stdout-ja különben a konzol kódlapján (cp1252)
    # menne ki, és az ékezet a UTF-8 olvasáskor elveszne.
    monkeypatch.setenv("PYTHONIOENCODING", "utf-8")
    futas = subprocess.run(
        [sys.executable, "-c", _PROBA],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    vege = f"\nstdout: {futas.stdout[-600:]}\nstderr: {futas.stderr[-600:]}"
    assert futas.returncode == 0, "a próbafolyamat elbukott" + vege
    ertekek = dict(
        sor.split("=", 1) for sor in futas.stdout.splitlines() if "=" in sor
    )
    for kulcs in ("FELIRAT", "TIZEDESJEL", "NEV", "METRIKUS"):
        assert kulcs in ertekek, f"hiányzik: {kulcs}" + vege
    return ertekek


@_CSAK_POSIX_LOCALE
@pytest.mark.parametrize(
    ("nyelv", "varhato"),
    [("de", "Abbrechen"), ("hu", "Mégse"), ("en", "Cancel")],
)
def test_a_cancel_gomb_a_valasztott_nyelven_van_magyar_rendszeren(
    nyelv, varhato, monkeypatch
):
    assert _futtasd(nyelv, monkeypatch)["FELIRAT"] == varhato


@_CSAK_POSIX_LOCALE
def test_angol_felulet_magyar_rendszeren_a_teruleti_beallitast_megtartja(monkeypatch):
    from PySide6.QtCore import QLocale

    if QLocale(QLocale.Language.English, QLocale.Country.Hungary).name() != "en_HU":
        pytest.skip("ennek a Qt-nek nincs en_HU területi adata (pl. a rendszer Qt 6.8-a)")
    ertekek = _futtasd("en", monkeypatch)
    assert ertekek["TIZEDESJEL"] == ","
    assert ertekek["NEV"] == "en_HU"
    assert ertekek["METRIKUS"] == "True"


@_CSAK_POSIX_LOCALE
def test_nemet_felulet_magyar_rendszeren_de_de_nevet_kap(monkeypatch):
    assert _futtasd("de", monkeypatch)["NEV"] == "de_DE"


def test_a_mertekegyseget_a_rendszer_donti_el_nem_az_alapertelmezett_locale():
    """B1: az alapértelmezett QLocale a felület nyelvéhez igazodik, a
    mértékegység viszont a rendszeré (ADR-004)."""
    from PySide6.QtCore import QLocale

    from picasapy.printing import dpi

    rendszer_metrikus = (
        QLocale.system().measurementSystem() == QLocale.MeasurementSystem.MetricSystem
    )
    eredeti = QLocale()
    try:
        for alapertelmezett in ("en_US", "hu_HU", "de_DE"):
            QLocale.setDefault(QLocale(alapertelmezett))
            assert dpi._metrikus_teruleti_meres() == rendszer_metrikus
    finally:
        QLocale.setDefault(eredeti)
