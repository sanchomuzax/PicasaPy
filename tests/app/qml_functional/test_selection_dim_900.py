"""A kijelölésen KÍVÜLI terület elsötétítése: `#2F2F2F`, alfa 143 (#900).

Az eredeti `.tre` a `Property negativemode 8f2f2f2f` sorral **öt** elemen
adja meg ugyanezt az értéket (`cropselection`, `redselection`,
`addfaceselection`, `faces`, `nav/nav`); a parszer (`0x009c79ce`) HEXAKÉNT
olvassa, ARGB-ként. Nálunk fekete volt, alfa 160.

⚠️ **Ez nem szépészet.** A fekete elsötétítés KIOLTJA a képet, a `#2F2F2F`
viszont megtartja a kontúrokat — az eredetiben a levágandó rész halványan,
de olvashatóan látszik. Ezért az alfa-értéket is állítjuk, nem csak a
színt: a kettő együtt adja a hatást.

A teszt a MEGJELENÍTETT színt olvassa a vezérlőkről, nem a `Theme` token
definícióját — így akkor is elbukik, ha a token jó, de valamelyik átfedés
nem azt használja.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QRectF, QUrl
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

#: `8f2f2f2f` ARGB-ként: alfa 143 (56,1%), RGB 47/47/47 (semleges sötétszürke).
VART = QColor(47, 47, 47, 143)

_KEEPALIVE: list[object] = []


def _qml_gyoker() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


def _betolt(qt_app, forras: str):
    """Egyetlen komponens valódi QML-motorban, kirajzolva."""
    view = QQuickView()
    view.engine().addImportPath(str(_qml_gyoker()))
    komponens = QQmlComponent(view.engine())
    komponens.setData(
        forras.encode("utf-8"), QUrl.fromLocalFile(str(_qml_gyoker()) + "/")
    )
    assert komponens.status() == QQmlComponent.Status.Ready, komponens.errorString()
    elem = komponens.create()
    assert elem is not None, komponens.errorString()
    view.setContent(QUrl(), komponens, elem)
    view.resize(400, 300)
    view.show()
    qt_app.processEvents()
    _KEEPALIVE.extend([view, komponens, elem])
    return elem


def _szin(elem, nev: str) -> QColor:
    return QColor(elem.property(nev))


class TestVagoAtfedes:
    """`editpanel/cropselection` — a vágó-téglalapon kívüli terület."""

    def _overlay(self, qt_app, *, preview: bool):
        return _betolt(
            qt_app,
            "import QtQuick\nimport PicasaPy\n"
            "CropOverlay {\n"
            "    width: 400; height: 300\n"
            f"    previewHold: {str(preview).lower()}\n"
            "}\n",
        )

    def test_a_sotetites_2f2f2f_alfa_143(self, qt_app):
        overlay = self._overlay(qt_app, preview=False)
        assert _szin(overlay, "dimColor") == VART, (
            "a vágó-átfedés nem az eredeti #2F2F2F / alfa 143 értéket használja"
        )

    def test_az_elonezet_tartas_kulon_agon_marad(self, qt_app):
        """A `previewHold` a MI kiegészítésünk, nem az eredetié (#1187).

        Az eredetiben nincs ilyen állapot; nálunk az „Előnézet" gomb
        tartásakor a kijelölésen kívüli rész a néző hátterével TELJESEN
        fedett, hogy a vágás eredménye látszódjon. Ez tehát szándékosan
        NEM az elsötétítő szín — az őr ezt rögzíti, hogy egy későbbi kör ne
        „javítsa" össze a kettőt."""
        overlay = self._overlay(qt_app, preview=True)
        szin = _szin(overlay, "dimColor")
        assert szin != VART, "az előnézet-tartás nem elsötétítés, hanem fedés"
        assert szin.alpha() == 255, "az előnézet-tartásnak teljesen fednie kell"


class TestArcHozzaadasAtfedes:
    """`editpanel/addfaceselection` — az arc-téglalapon kívüli terület."""

    def _overlay(self, qt_app):
        return _betolt(
            qt_app,
            "import QtQuick\nimport PicasaPy\n"
            "FacesOverlay {\n"
            "    width: 400; height: 300\n"
            "    editMode: true\n"
            "}\n",
        )

    def test_van_sotetites_es_az_erteke_helyes(self, qt_app):
        overlay = self._overlay(qt_app)
        dim = overlay.findChild(QObject, "faceSelectionDim")
        assert dim is not None, (
            "az arc-hozzáadás téglalapján kívül nincs elsötétítés"
        )
        assert _szin(dim, "dimColor") == VART

    def test_draft_nelkul_nem_latszik(self, qt_app):
        overlay = self._overlay(qt_app)
        dim = overlay.findChild(QObject, "faceSelectionDim")
        assert dim.property("active") is False, (
            "téglalap nélkül nem szabad sötétíteni"
        )

    def test_drafttal_latszik(self, qt_app):
        overlay = self._overlay(qt_app)
        overlay.setProperty("draftRect", QRectF(50, 40, 120, 90))
        qt_app.processEvents()
        dim = overlay.findChild(QObject, "faceSelectionDim")
        assert dim.property("active") is True


class TestVorosszemAtfedes:
    """`editpanel/redselection` — a vörösszem-téglalapon kívüli terület."""

    def test_van_sotetites_a_nezoben(self, qml_app, qt_app):
        window = qml_app[0]
        window.setProperty("viewerOpen", True)
        for _ in range(5):
            qt_app.processEvents()
        dim = window.findChild(QObject, "redeyeSelectionDim")
        assert dim is not None, (
            "a vörösszem-téglalapon kívül nincs elsötétítés"
        )
        assert _szin(dim, "dimColor") == VART


class TestSotetitoKomponens:
    """A közös `SelectionDim`: pontosan a téglalapon KÍVÜLI részt fedi."""

    def test_a_negy_savmeret_kiadja_a_kulso_teruletet(self, qt_app):
        elem = _betolt(
            qt_app,
            "import QtQuick\nimport PicasaPy\n"
            "SelectionDim {\n"
            "    width: 400; height: 300\n"
            "    active: true\n"
            "    selX: 100; selY: 80; selW: 150; selH: 60\n"
            "}\n",
        )
        fedett = elem.property("coveredArea")
        assert fedett == pytest.approx(400 * 300 - 150 * 60), (
            "a sötétítés nem pontosan a kijelölésen kívüli területet fedi"
        )
