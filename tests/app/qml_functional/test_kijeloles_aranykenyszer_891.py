"""A kijelölő-téglalap ARÁNY-KÉNYSZERE módosítóbillentyűre (#891).

## Az eredeti — bizonyíték

A `ytSelectionDragHandler` (vftable `0x008da768`, 4. bejegyzés
`0x00a6f450`) a `.tre` szerint a szerkesztő HÁROM téglalapjához van kötve:
`editpanel/cropselection`, `editpanel/redselection`,
`editpanel/addfaceselection`. A húzás közben három vizsgálat fut
**egymás után**, mindegyik felülírja az előzőt:

```asm
0x00a6fa56  push 0x10   ; VK_SHIFT   → fld1            → 1,0
0x00a6fa6f  push 0x11   ; VK_CONTROL → [0xcf4cd0]      → 1,3333333
0x00a6fa8c  push 0x12   ; VK_MENU    → [0xcf3ec4]      → 1,5
```

tehát **Alt üt Ctrl-t, Ctrl üt Shiftet**, és felengedéskor a kényszer
megszűnik (`0x00a6fae6` nullázza a mezőt).

⚠️ **A szorzó NEM abszolút arány.** Az alkalmazó (`0x00a6ef20`) a
`[eax+0x10] / [eax]` hányadost — a KÉP saját szélesség/magasság arányát —
szorozza meg vele. Shifttel tehát a kijelölés a fénykép arányát veszi fel,
NEM négyzetet. Ez a jegy legkönnyebben félreérthető pontja.

## Amit ez a fájl mér

**Valódi egéreseménnyel** húz — nem a `updateCreation()`-t hívja —, és a
KIRAJZOLT téglalap (a `cropSelection` / `faceDraftRect` / `redeyeDragRect`
vezérlő) szélességét-magasságát olvassa. A #1148 és a #1200 is azért
maradt zöld egy használhatatlan funkció fölött, mert a teszt a kezelőt
hívta közvetlenül.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QEvent, QObject, QPointF, QUrl, Qt
from PySide6.QtGui import QMouseEvent, QPointingDevice
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickView

#: a szintetikus események időbélyege — enélkül a Qt dupla kattintást lát
_ORA = [1000]

#: a próba-doboz: 300 × 200 → a „kép" saját aránya 1,5
DOBOZ_SZEL = 300
DOBOZ_MAG = 200
KEP_ARANY = DOBOZ_SZEL / DOBOZ_MAG

#: a három szorzó az eredetiből
SHIFT_SZORZO = 1.0
CTRL_SZORZO = 4 / 3
ALT_SZORZO = 1.5

#: a húzás két pontja (szabadon 120 × 40 → arány 3,0; mindhárom
#: kényszerített arány ettől és egymástól is jól elkülönül)
KEZDET = QPointF(30, 30)
VEG = QPointF(150, 70)
SZABAD_ARANY = 3.0

_KEEPALIVE: list[object] = []

SHIFT = Qt.KeyboardModifier.ShiftModifier
CTRL = Qt.KeyboardModifier.ControlModifier
ALT = Qt.KeyboardModifier.AltModifier
NINCS = Qt.KeyboardModifier.NoModifier


def _qml_gyoker() -> Path:
    return Path(__file__).resolve().parents[3] / "src" / "picasapy" / "app" / "qml"


def _betolt(qt_app, forras: str):
    """Egyetlen komponens valódi QML-motorban, KIRAJZOLVA és egérezhetően."""
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
    view.resize(DOBOZ_SZEL, DOBOZ_MAG)
    view.show()
    qt_app.processEvents()
    _KEEPALIVE.extend([view, komponens, elem])
    return view, elem


def _egeresemeny(cel, qt_app, tipus, pont, gomb, gombok, mods) -> None:
    _ORA[0] += 1000
    esemeny = QMouseEvent(
        tipus, pont, pont, gomb, gombok, mods,
        QPointingDevice.primaryPointingDevice(),
    )
    esemeny.setTimestamp(_ORA[0])
    qt_app.sendEvent(cel, esemeny)
    qt_app.processEvents()


def _huz(cel, qt_app, kezdet, veg, mods, *, felenged=True):
    """VALÓDI egérhúzás `kezdet`-től `veg`-ig a megadott módosítókkal."""
    _egeresemeny(
        cel, qt_app, QEvent.Type.MouseButtonPress, kezdet,
        Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, mods,
    )
    _egeresemeny(
        cel, qt_app, QEvent.Type.MouseMove, veg,
        Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, mods,
    )
    if felenged:
        _egeresemeny(
            cel, qt_app, QEvent.Type.MouseButtonRelease, veg,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, mods,
        )


def _arany(szelesseg: float, magassag: float) -> float:
    assert magassag > 0, "a kirajzolt téglalap magassága nulla"
    return szelesseg / magassag


def _elvart(kep_arany: float, szorzo: float) -> float:
    return kep_arany * szorzo


class TestVagoTeglalap:
    """`editpanel/cropselection` — a vágó kijelölő-téglalapja."""

    def _overlay(self, qt_app):
        view, elem = _betolt(
            qt_app,
            "import QtQuick\nimport PicasaPy\n"
            "CropOverlay {\n"
            f"    width: {DOBOZ_SZEL}; height: {DOBOZ_MAG}\n"
            "}\n",
        )
        return view, elem

    def _huzott_arany(self, qt_app, mods, *, felenged=True) -> float:
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, KEZDET, VEG, mods, felenged=felenged)
        # a KIRAJZOLT keretet olvassuk, nem a számított tulajdonságot
        keret = overlay.findChild(QObject, "cropSelection")
        assert keret is not None, "a vágó-keret vezérlő nem található"
        assert keret.property("visible"), "a húzás nem hozott létre keretet"
        return _arany(keret.property("width"), keret.property("height"))

    def test_modosito_nelkul_szabad_az_arany(self, qt_app):
        assert self._huzott_arany(qt_app, NINCS) == pytest.approx(
            SZABAD_ARANY, abs=0.01
        )

    def test_shift_a_kep_sajat_aranyat_adja(self, qt_app):
        """⚠️ NEM négyzet: a szorzó 1,0, de a KÉP arányára szorzódik."""
        assert self._huzott_arany(qt_app, SHIFT) == pytest.approx(
            _elvart(KEP_ARANY, SHIFT_SZORZO), abs=0.01
        )

    def test_ctrl_negy_harmad(self, qt_app):
        assert self._huzott_arany(qt_app, CTRL) == pytest.approx(
            _elvart(KEP_ARANY, CTRL_SZORZO), abs=0.01
        )

    def test_alt_harom_ketted(self, qt_app):
        assert self._huzott_arany(qt_app, ALT) == pytest.approx(
            _elvart(KEP_ARANY, ALT_SZORZO), abs=0.01
        )

    def test_alt_ut_ctrlt(self, qt_app):
        """A három vizsgálat egymás után fut: az Alt írja felül az utolsót."""
        assert self._huzott_arany(qt_app, ALT | CTRL) == pytest.approx(
            _elvart(KEP_ARANY, ALT_SZORZO), abs=0.01
        )

    def test_ctrl_ut_shiftet(self, qt_app):
        assert self._huzott_arany(qt_app, CTRL | SHIFT) == pytest.approx(
            _elvart(KEP_ARANY, CTRL_SZORZO), abs=0.01
        )

    def test_mindharom_egyutt_altot_ad(self, qt_app):
        assert self._huzott_arany(qt_app, ALT | CTRL | SHIFT) == pytest.approx(
            _elvart(KEP_ARANY, ALT_SZORZO), abs=0.01
        )

    def test_shifttel_mas_teglalap_mint_nelkule(self, qt_app):
        """A »Kész, ha« kifejezett pontja: azonos húzás, MÁS eredmény."""
        assert self._huzott_arany(qt_app, SHIFT) != pytest.approx(
            self._huzott_arany(qt_app, NINCS), abs=0.05
        )

    def test_a_kenyszer_a_huzas_kozben_mar_el(self, qt_app):
        """Nem csak felengedéskor: a keret MÁR HÚZÁS KÖZBEN arányos."""
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, KEZDET, VEG, SHIFT, felenged=False)
        keret = overlay.findChild(QObject, "cropSelection")
        assert _arany(
            keret.property("width"), keret.property("height")
        ) == pytest.approx(_elvart(KEP_ARANY, SHIFT_SZORZO), abs=0.01)
        _egeresemeny(
            view, qt_app, QEvent.Type.MouseButtonRelease, VEG,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, SHIFT,
        )

    def test_felengedeskor_a_kenyszer_megszunik(self, qt_app):
        """`0x00a6fae6`: a mező nullázódik — a következő lépés már szabad."""
        view, overlay = self._overlay(qt_app)
        _egeresemeny(
            view, qt_app, QEvent.Type.MouseButtonPress, KEZDET,
            Qt.MouseButton.LeftButton, Qt.MouseButton.LeftButton, SHIFT,
        )
        _egeresemeny(
            view, qt_app, QEvent.Type.MouseMove, VEG,
            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, SHIFT,
        )
        # a Shiftet elengedi, de az egeret nem: a következő húzás-lépés szabad
        _egeresemeny(
            view, qt_app, QEvent.Type.MouseMove, VEG,
            Qt.MouseButton.NoButton, Qt.MouseButton.LeftButton, NINCS,
        )
        keret = overlay.findChild(QObject, "cropSelection")
        assert _arany(
            keret.property("width"), keret.property("height")
        ) == pytest.approx(SZABAD_ARANY, abs=0.01)

    def test_a_beallitott_arany_valtozatlan_marad(self, qt_app):
        """A kényszer PILLANATNYI: a panel `aspectRatio`-ját nem írja át."""
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, KEZDET, VEG, ALT)
        assert overlay.property("aspectRatio") == 0, (
            "a módosító beragadt a tartós arány-beállításba"
        )

    def test_a_kenyszeritett_teglalap_a_kepen_belul_marad(self, qt_app):
        """A származtatott magasság kifuthatna a képből — akkor a
        SZÉLESSÉGET is vissza kell venni, különben az arány romlik el."""
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, QPointF(20, 150), QPointF(260, 170), SHIFT)
        keret = overlay.findChild(QObject, "cropSelection")
        x, y = keret.property("x"), keret.property("y")
        w, h = keret.property("width"), keret.property("height")
        assert x >= -0.01 and y >= -0.01
        assert x + w <= DOBOZ_SZEL + 0.01, "a keret kilóg a kép jobb szélén"
        assert y + h <= DOBOZ_MAG + 0.01, "a keret kilóg a kép alján"
        assert _arany(w, h) == pytest.approx(
            _elvart(KEP_ARANY, SHIFT_SZORZO), abs=0.01
        ), "a levágás után az arány elromlott"


class TestArcHozzaadasTeglalap:
    """`editpanel/addfaceselection` — az arc-hozzáadás téglalapja."""

    def _overlay(self, qt_app):
        return _betolt(
            qt_app,
            "import QtQuick\nimport PicasaPy\n"
            "FacesOverlay {\n"
            f"    width: {DOBOZ_SZEL}; height: {DOBOZ_MAG}\n"
            "    editMode: true\n"
            "}\n",
        )

    def _huzott_arany(self, qt_app, mods) -> float:
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, KEZDET, VEG, mods)
        keret = overlay.findChild(QObject, "faceDraftRect")
        assert keret is not None, "az arc-draft téglalap vezérlő nem található"
        assert keret.property("visible"), "a húzás nem hozott létre téglalapot"
        return _arany(keret.property("width"), keret.property("height"))

    def test_modosito_nelkul_szabad_az_arany(self, qt_app):
        assert self._huzott_arany(qt_app, NINCS) == pytest.approx(
            SZABAD_ARANY, abs=0.01
        )

    def test_shift_a_kep_sajat_aranyat_adja(self, qt_app):
        assert self._huzott_arany(qt_app, SHIFT) == pytest.approx(
            _elvart(KEP_ARANY, SHIFT_SZORZO), abs=0.01
        )

    def test_ctrl_negy_harmad(self, qt_app):
        assert self._huzott_arany(qt_app, CTRL) == pytest.approx(
            _elvart(KEP_ARANY, CTRL_SZORZO), abs=0.01
        )

    def test_alt_harom_ketted(self, qt_app):
        assert self._huzott_arany(qt_app, ALT) == pytest.approx(
            _elvart(KEP_ARANY, ALT_SZORZO), abs=0.01
        )

    def test_alt_ut_ctrlt(self, qt_app):
        assert self._huzott_arany(qt_app, ALT | CTRL) == pytest.approx(
            _elvart(KEP_ARANY, ALT_SZORZO), abs=0.01
        )

    def test_ctrl_ut_shiftet(self, qt_app):
        assert self._huzott_arany(qt_app, CTRL | SHIFT) == pytest.approx(
            _elvart(KEP_ARANY, CTRL_SZORZO), abs=0.01
        )

    def test_a_kenyszeritett_teglalap_a_kepen_belul_marad(self, qt_app):
        view, overlay = self._overlay(qt_app)
        _huz(view, qt_app, QPointF(20, 150), QPointF(260, 170), SHIFT)
        keret = overlay.findChild(QObject, "faceDraftRect")
        x, y = keret.property("x"), keret.property("y")
        w, h = keret.property("width"), keret.property("height")
        assert x + w <= DOBOZ_SZEL + 0.01, "a téglalap kilóg a kép jobb szélén"
        assert y + h <= DOBOZ_MAG + 0.01, "a téglalap kilóg a kép alján"
        assert _arany(w, h) == pytest.approx(
            _elvart(KEP_ARANY, SHIFT_SZORZO), abs=0.01
        ), "a levágás után az arány elromlott"


class TestVorosszemTeglalap:
    """`editpanel/redselection` — a vörösszem kézi kijelölő-téglalapja.

    Ez a TELJES appban él (a `PhotoViewer` belsejében), ezért itt a valódi
    ablakot húzzuk — a doboz a fénykép ténylegesen kirajzolt területe, így
    az elvárt arányt a mért doboz-méretből számoljuk."""

    def _overlay(self, qml_app, qt_app):
        window, _controller, _ = qml_app
        window.setProperty("viewerOpen", True)
        viewer = window.findChild(QObject, "photoViewer")
        assert viewer is not None, "photoViewer nem található"
        viewer.setProperty("currentIndex", 0)
        qt_app.processEvents()
        panel = window.findChild(QObject, "viewerEditorPanel")
        assert panel is not None, "viewerEditorPanel nem található"
        panel.setProperty("redeyeActive", True)
        qt_app.processEvents()
        overlay = window.findChild(QObject, "redeyeOverlay")
        assert overlay is not None, "redeyeOverlay nem található"
        if overlay.property("width") < 60 or overlay.property("height") < 60:
            pytest.skip("a kirajzolt kép túl kicsi a húzás-próbához")
        return window, overlay

    def _huzott_arany(self, qml_app, qt_app, mods) -> float:
        window, overlay = self._overlay(qml_app, qt_app)
        szel = overlay.property("width")
        mag = overlay.property("height")
        kezdet = overlay.mapToScene(QPointF(szel * 0.10, mag * 0.10))
        veg = overlay.mapToScene(QPointF(szel * 0.50, mag * 0.25))
        _huz(window, qt_app, kezdet, veg, mods, felenged=False)
        keret = window.findChild(QObject, "redeyeDragRect")
        assert keret is not None, "a vörösszem-téglalap vezérlő nem található"
        assert keret.property("visible"), "a húzás nem hozott létre téglalapot"
        eredmeny = _arany(keret.property("width"), keret.property("height"))
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonRelease, veg,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, mods,
        )
        return eredmeny / (szel / mag)   # a KÉP arányának hányszorosa

    def test_modosito_nelkul_szabad_az_arany(self, qml_app, qt_app):
        window, overlay = self._overlay(qml_app, qt_app)
        szel = overlay.property("width")
        mag = overlay.property("height")
        szorzo = self._huzott_arany(qml_app, qt_app, NINCS)
        # szabadon: (0,40·szél) / (0,15·mag) — a kép arányának hányszorosa
        assert szorzo == pytest.approx((0.40 * szel) / (0.15 * mag) / (szel / mag),
                                       abs=0.02)

    def test_shift_a_kep_sajat_aranyat_adja(self, qml_app, qt_app):
        assert self._huzott_arany(qml_app, qt_app, SHIFT) == pytest.approx(
            SHIFT_SZORZO, abs=0.01
        )

    def test_ctrl_negy_harmad(self, qml_app, qt_app):
        assert self._huzott_arany(qml_app, qt_app, CTRL) == pytest.approx(
            CTRL_SZORZO, abs=0.01
        )

    def test_alt_harom_ketted(self, qml_app, qt_app):
        assert self._huzott_arany(qml_app, qt_app, ALT) == pytest.approx(
            ALT_SZORZO, abs=0.01
        )

    def test_alt_ut_ctrlt(self, qml_app, qt_app):
        assert self._huzott_arany(qml_app, qt_app, ALT | CTRL) == pytest.approx(
            ALT_SZORZO, abs=0.01
        )

    def test_ctrl_ut_shiftet(self, qml_app, qt_app):
        assert self._huzott_arany(qml_app, qt_app, CTRL | SHIFT) == pytest.approx(
            CTRL_SZORZO, abs=0.01
        )

    def test_a_kenyszeritett_teglalap_a_kepen_belul_marad(self, qml_app, qt_app):
        window, overlay = self._overlay(qml_app, qt_app)
        szel = overlay.property("width")
        mag = overlay.property("height")
        kezdet = overlay.mapToScene(QPointF(szel * 0.05, mag * 0.75))
        veg = overlay.mapToScene(QPointF(szel * 0.95, mag * 0.85))
        _huz(window, qt_app, kezdet, veg, SHIFT, felenged=False)
        keret = window.findChild(QObject, "redeyeDragRect")
        y = keret.property("y")
        w, h = keret.property("width"), keret.property("height")
        _egeresemeny(
            window, qt_app, QEvent.Type.MouseButtonRelease, veg,
            Qt.MouseButton.LeftButton, Qt.MouseButton.NoButton, SHIFT,
        )
        assert y + h <= mag + 0.01, "a téglalap kilóg a kép alján"
        assert _arany(w, h) / (szel / mag) == pytest.approx(
            SHIFT_SZORZO, abs=0.01
        ), "a levágás után az arány elromlott"
