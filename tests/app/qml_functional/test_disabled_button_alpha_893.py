"""A letiltott gomb NEGYEDÁTLÁTSZATLANSÁGGAL rajzolódik (#893).

Az eredeti Picasa csomópont-rajzolója (`0x009e2a60`) a letiltott csomópont
alfáját egyszerűen **néggyel osztja** (`0x009e3178: shr [edx+0x5c], 2`),
mielőtt rajzolna — nincs külön „letiltott" kép a `respack.yt`-ben, mert nem
kell. Nálunk ez 55% volt, és az akcentusos (zöld) gomb ráadásul teljesen
átlátszatlan maradt, holott a rajzolóban **erre nincs kivétel**.

## Miért a GYÖKÉR átlátszatlanságát mérjük

Az eredetiben az osztás a csomópontra hat, és a QML-ben — akárcsak ott — az
átlátszatlanság a gyerekekre **öröklődik** (szorzódik). Ha csak a háttér
kapná meg, a felirat teljes erővel maradna ott, ami épp az ellenkezője
annak, amit a rajzoló csinál: a felirat a gomb GYEREKcsomópontja, tehát
ugyanazt a 25%-ot kapja.

Ezért az állítás a `PicasaButton` gyökerén mér, nem a `background`-en.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

#: Az eredeti `shr …, 2` pontos aránya.
LETILTOTT_ALFA = 0.25

_KEEPALIVE: list[object] = []


def _qml_gyoker():
    return Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


def _gomb(qt_app, *, enabled: bool, accent: str | None):
    """Egyetlen `PicasaButton` valódi QML-motorban, kirajzolva."""
    view = QQuickView()
    view.engine().addImportPath(str(_qml_gyoker()))
    akcentus = f'accent: "{accent}"\n' if accent else ""
    forras = (
        "import QtQuick\n"
        "import PicasaPy\n"
        "PicasaButton {\n"
        '    objectName: "probaGomb"\n'
        '    text: "Próba"\n'
        f"    enabled: {str(enabled).lower()}\n"
        f"    {akcentus}"
        "}\n"
    )
    komponens = QQmlComponent(view.engine())
    komponens.setData(forras.encode("utf-8"), QUrl.fromLocalFile(str(_qml_gyoker()) + "/"))
    assert komponens.status() == QQmlComponent.Status.Ready, komponens.errorString()
    elem = komponens.create()
    assert elem is not None, komponens.errorString()
    view.setContent(QUrl(), komponens, elem)
    view.show()
    qt_app.processEvents()
    _KEEPALIVE.extend([view, komponens, elem])
    return elem


class TestLetiltottGombAlfa:
    def test_a_letiltott_gomb_negyedatlatszatlansaggal_rajzolodik(self, qt_app):
        gomb = _gomb(qt_app, enabled=False, accent=None)
        assert gomb.property("opacity") == pytest.approx(LETILTOTT_ALFA, abs=0.001), (
            "a letiltott gomb nem az eredeti 25%-os alfát kapja"
        )

    def test_az_engedelyezett_gomb_teljesen_atlatszatlan(self, qt_app):
        gomb = _gomb(qt_app, enabled=True, accent=None)
        assert gomb.property("opacity") == pytest.approx(1.0, abs=0.001)

    def test_a_zold_gombra_sincs_kivetel(self, qt_app):
        """A rajzolóban NINCS akcentus-kivétel: a zöld gomb is negyedel."""
        gomb = _gomb(qt_app, enabled=False, accent="#3c8f3c")
        assert gomb.property("opacity") == pytest.approx(LETILTOTT_ALFA, abs=0.001), (
            "az akcentusos gomb kivételt kapott, holott a rajzolóban nincs ilyen"
        )

    def test_a_felirat_a_szulo_atlatszosagat_orokli(self, qt_app):
        """A felirat gyerekcsomópont: ugyanazt a 25%-ot kapja, nem külön
        szürkítést. Ezért a letiltott és az engedélyezett gomb SZÖVEGSZÍNE
        azonos — a különbséget az öröklött alfa adja."""
        letiltott = _gomb(qt_app, enabled=False, accent=None)
        engedelyezett = _gomb(qt_app, enabled=True, accent=None)
        assert letiltott.property("inkColor") == engedelyezett.property("inkColor"), (
            "a letiltott gomb felirata külön szürkítést kap a szülő "
            "átlátszatlanságának öröklése helyett"
        )
