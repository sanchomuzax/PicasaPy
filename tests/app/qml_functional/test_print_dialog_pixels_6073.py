"""Egyszeri, átmeneti képfelvétel a #6073 végső képpontos összevetéséhez."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPointF, Qt
from PySide6.QtTest import QTest
from tests.app.qml_functional.test_nyomtatas_bekotes_1472 import (
    _kijelol,
    _menubol_nyit,
)
from tests.support.varakozas import var_feltetelre


def _elem(root, nev):
    objektum = root.findChild(QObject, nev)
    assert objektum is not None, f"{nev} nem található"
    return objektum


def _var(qt_app, feltetel):
    assert var_feltetelre(qt_app, feltetel, masodperc=10.0)


def _kep(dialog, cel: Path, qt_app):
    elozo_kep = None
    valtozatlan_kockak = 0
    stabil_kep = None

    def kep_stabil():
        nonlocal elozo_kep, valtozatlan_kockak, stabil_kep
        aktualis_kep = dialog.grabWindow()
        if elozo_kep is not None and aktualis_kep == elozo_kep:
            valtozatlan_kockak += 1
        else:
            elozo_kep = aktualis_kep
            valtozatlan_kockak = 1
        if valtozatlan_kockak >= 10:
            stabil_kep = aktualis_kep
            return True
        return False

    # A nyitott ComboBox görgetősávjának átlátszatlansága 150 ms-os QML-
    # animációval áll be. A modell elemszáma már korábban kész lehet, ezért
    # a rögzítés előtt tíz egymás utáni változatlan képkockát várunk a közös
    # 10 másodperces, CI-szorzós határidőn belül; így a szinkron a tényleges
    # renderelt kimenetre épül.
    _var(qt_app, kep_stabil)
    kep = stabil_kep
    assert kep is not None, f"a nyomtatási kép nem stabilizálódott: {cel.name}"
    assert not kep.isNull(), f"üres nyomtatási képernyőkép: {cel.name}"
    assert (kep.width(), kep.height()) == (
        round(dialog.width()),
        round(dialog.height()),
    )
    assert kep.save(str(cel), "PNG"), f"nem menthető: {cel}"
    return kep.width(), kep.height()


@pytest.mark.parametrize("magassag_elteres", (-5, 0, 5))
def test_vegso_allapotkepek(qml_app, qt_app, monkeypatch, tmp_path, magassag_elteres):
    from picasapy.app.print_controller import PrintController

    monkeypatch.setattr(PrintController, "listPrinters", lambda _self: [])
    kimenet = Path(
        os.environ.get(
            "PICASAPY_PRINT_DIALOG_6073_CAPTURE_DIR",
            str(tmp_path / "print-dialog-6073"),
        )
    ) / f"magassag-{magassag_elteres:+d}"
    kimenet.mkdir(parents=True, exist_ok=True)
    window, _controller, _engine = qml_app
    _kijelol(window, qt_app, [0])
    dialog = _menubol_nyit(window, qt_app)
    _var(qt_app, lambda: dialog.isVisible() and not dialog.property("meretezesFuggoben"))
    alap_magassag = round(dialog.height())

    def alkalmaz_magassag_elterest():
        _var(qt_app, lambda: not dialog.property("meretezesFuggoben"))
        elvart_magassag = alap_magassag + magassag_elteres
        if round(dialog.height()) != elvart_magassag:
            dialog.setHeight(elvart_magassag)
        _var(qt_app, lambda: round(dialog.height()) == elvart_magassag)

    alkalmaz_magassag_elterest()
    meretek = {"alap": _kep(dialog, kimenet / "alap.png", qt_app)}

    assert QMetaObject.invokeMethod(
        dialog,
        "openForRows",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", [0, 1]),
    )
    _var(qt_app, lambda: not dialog.property("meretezesFuggoben"))
    alkalmaz_magassag_elterest()
    meretek["tobb-kep"] = _kep(dialog, kimenet / "tobb-kep.png", qt_app)

    dialog.setProperty("quality", {"small": 1, "total": 2, "ready": False})
    dialog.setProperty(
        "reviewList",
        [
            {"name": "a.jpg", "dpi": 48, "qualityCode": 0, "row": 0},
            {"name": "b.jpg", "dpi": 72, "qualityCode": 0, "row": 1},
        ],
    )
    dialog.setProperty("reviewOpen", True)
    panel = _elem(dialog, "printReviewPanel")
    _var(qt_app, lambda: panel.property("visible") is True)
    alkalmaz_magassag_elterest()
    meretek["minosegi-figyelmeztetes"] = _kep(
        dialog, kimenet / "minosegi-figyelmeztetes.png", qt_app
    )

    dialog.setProperty("reviewOpen", False)
    dialog.setProperty("printers", ["6073 tesztnyomtató"])
    combo = _elem(dialog, "printPrinterBox")
    _var(qt_app, lambda: combo.property("count") == 2)
    combo.setProperty("currentIndex", 1)
    pont = combo.mapToScene(QPointF(combo.width() / 2, combo.height() / 2)).toPoint()
    QTest.mouseClick(
        dialog, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont
    )
    lista = _elem(combo, "picasaComboList")
    _var(qt_app, lambda: int(lista.property("count")) == 2)
    alkalmaz_magassag_elterest()
    meretek["nyomtato-valaszto"] = _kep(
        dialog, kimenet / "nyomtato-valaszto.png", qt_app
    )
    (kimenet / "meretek.txt").write_text(
        "\n".join(f"{nev}: {szel}x{mag}" for nev, (szel, mag) in meretek.items())
        + "\n",
        encoding="utf-8",
    )
