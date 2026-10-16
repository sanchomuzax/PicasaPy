"""A „Szerkesztő" táblázat kollázs-tételei VALÓDI kattintással (#5135, 2. rész, B).

A kollázs-panelt a #947/#949 közös harnessze adja (`collage_canvas_harness`):
a vezérlő valódi, kirajzolt ablakban él, és az egérkattintás a vásznon át
ér el a gombig.

Lefedve:
- `collageDeselectArea` - a vászon üres részére kattintva törlődik a kijelölés;
- `collageReplaceCancelButton` - a csere-párbeszéd „Mégse" gombja zárja a
  párbeszédet, és nem indít mentést;
- `collageCancelCollageButton` - a megszakítás-párbeszéd „Cancel Collage"
  gombja megszakítási kérést küld a háttérszálnak;
- `collageSettingsTabButton` - a „Beállítások" fül visszavált a beállítások lapra.

Kamerás felvétel-panel (a `CaptureMoviePanelPopup`), valódi kamera nélkül:
- `capturemoviepanelpopup/snapshot`, `…/record_pause` - a médiafuttató
  helyettesítője (`_FAKE_RUNTIME`) a Loader `captureMovieMediaLoader`
  helyén; a gombok ugyanazt a felületet hívják, mint a valódi futtató;
- `capturemoviepanelpopup/videosrc`, `…/audiosrc` - a beállítások lap
  választója (a kézi tárolót a valódi `CameraCaptureController` adja,
  a mappa a teszt ideiglenes könyvtárába mutat).

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. A párbeszédek megnyitásához a Popup `open` hívása
szabad (állapot-előkészítés); a tesztelt gombot mindig valódi kattintás éri.
"""

from __future__ import annotations


import pytest
from PySide6.QtCore import QMetaObject, QObject, QPoint, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QTest
from PySide6.QtWidgets import QApplication
from support.collage_canvas_harness import (
    _child,
    _panel,
    keszits_kepeket,
    nyitott_vezerlo,
)
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def library(tmp_path):
    return keszits_kepeket(tmp_path)


@pytest.fixture
def controller(qt_app, tmp_path, library):
    yield from nyitott_vezerlo(tmp_path, library)


@pytest.fixture
def panel(controller):
    return _panel(controller)


def _kattints_pontra(panel, pont: QPoint) -> None:
    QTest.mouseClick(
        panel.property("_view"),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    QTest.qWait(50)


def _kattints(panel, item) -> None:
    kozep = item.mapToScene(item.boundingRect().center())
    _kattints_pontra(panel, QPoint(round(kozep.x()), round(kozep.y())))


def _parbeszed(panel, nev: str):
    dialog = panel.findChild(QObject, nev)
    assert dialog is not None, f"{nev} nincs a fában"
    return dialog


def _gomb(panel, parbeszed_nev: str, gomb_nev: str):
    gomb = _parbeszed(panel, parbeszed_nev).findChild(QObject, gomb_nev)
    assert gomb is not None, f"{gomb_nev} nincs a(z) {parbeszed_nev} párbeszédben"
    return gomb


def _var(feltetel, ms: int = 10000) -> bool:
    return var_feltetelre(QApplication.instance(), feltetel, ms / 1000)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints_ablakban(qt_app, ablak, elem) -> None:
    """Valódi egérkattintás `elem` középpontjára, az `ablak`-ra küldve."""
    assert elem.width() > 0 and elem.height() > 0, (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


def _nyisd_meg(panel, parbeszed_nev: str) -> None:
    """Állapot-előkészítés: a párbeszéd `open` hívása (nem a tesztelt gomb)."""
    dialog = _parbeszed(panel, parbeszed_nev)
    QMetaObject.invokeMethod(dialog, "open", Qt.ConnectionType.DirectConnection)
    assert _var(lambda: dialog.property("visible") is True), (
        f"a(z) {parbeszed_nev} nem nyílt meg"
    )


class TestVaszonHattere:
    """`collageDeselectArea`: az üres vászon-terület törli a kijelölést."""

    def test_az_ures_vaszonra_kattintva_torlodik_a_kijeloles(self, panel, controller):
        controller.selectAllNodes()
        assert len(controller.collageSelection) > 0, "a próba feltétele: van kijelölés"
        area = _child(panel, "collageDeselectArea")
        assert area.isVisible(), "a vászon háttere nem látszik"
        # a vászon bal-felső sarka a csomópontok és a gyűrűk mellett van: üres terület
        sarok = area.mapToScene(QPointF(4, 4)).toPoint()
        _kattints_pontra(panel, sarok)

        assert _var(lambda: controller.collageSelection == []), (
            "az üres vászonra kattintás nem törölte a kijelölést"
        )


class TestCsereMegse:
    """`collageReplaceCancelButton`: a Mégse bezárja a csere-kérdést, nem ment."""

    def test_a_megse_bezarja_a_kerdest_es_nem_menti_a_kollazst(self, panel, controller):
        _nyisd_meg(panel, "collageReplaceDialog")
        dialog = _parbeszed(panel, "collageReplaceDialog")
        gomb = _gomb(panel, "collageReplaceDialog", "collageReplaceCancelButton")

        _kattints(panel, gomb)

        assert _var(lambda: dialog.property("visible") is False), (
            "a Mégse gomb nem zárta be a csere-párbeszédet"
        )
        assert controller.collageOpen is True, "a Mégse után a kollázs lap zárult be"
        assert _child(panel, "collageProgressOverlay").isVisible() is False, (
            "a Mégse mentést indított: a folyamatjelző megjelent"
        )


class TestMegszakitasVegleges:
    """`collageCancelCollageButton`: a „Cancel Collage" megszakítási kérést küld."""

    def test_a_cancel_collage_megszakitja_a_mentest(self, panel, controller):
        _nyisd_meg(panel, "collageCancelConfirmDialog")
        dialog = _parbeszed(panel, "collageCancelConfirmDialog")
        gomb = _gomb(panel, "collageCancelConfirmDialog", "collageCancelCollageButton")
        # a megszakítás-jelző a vezérlő belső Eventje (collage_save.cancelCollage);
        # ezt olvassuk, mert futó mentés nélkül a vezérlő nem ad másik jelet
        jelzo = controller._collage_panel_cancel
        assert jelzo.is_set() is False, "a próba feltétele: nincs megszakítási kérés"

        _kattints(panel, gomb)

        assert _var(lambda: dialog.property("visible") is False), (
            "a Cancel Collage gomb nem zárta be a megszakítás-kérdést"
        )
        assert _var(lambda: jelzo.is_set()), (
            "a Cancel Collage gomb nem küldött megszakítási kérést"
        )


class TestBeallitasokFul:
    """`collageSettingsTabButton`: a Beállítások fül visszavált a beállítások lapra."""

    def test_a_beallitasok_fulre_kattintva_visszavalt_a_lapra(self, panel):
        klip_fül = _child(panel, "collageClipsTabButton")
        beallitas_fül = _child(panel, "collageSettingsTabButton")
        _kattints(panel, klip_fül)
        assert _var(lambda: _child(panel, "collageSettingsTab").isVisible() is False), (
            "a próba feltétele: a Klipek lap látszik"
        )

        _kattints(panel, beallitas_fül)

        assert _var(lambda: _child(panel, "collageSettingsTab").isVisible() is True), (
            "a Beállítások fülre kattintás nem váltott vissza a beállítások lapra"
        )
        assert beallitas_fül.property("checked") is True


#: A médiafuttató helyettesítője: ugyanazt a felületet adja, amit a panel használ
#: (kamera-, hang- és eszközlista, rögzítő, pillanatkép-készítő, szünet).
#: A hívásokat a `captureCount`/`lastCapture` és a jelzők rögzítik, hogy a teszt lássa őket.
_FAKE_RUNTIME = b"""
import QtQuick
Item {
    id: runtime
    property var videoDevices: [
        { "id": "kam-a", "description": "Kamera A" },
        { "id": "kam-b", "description": "Kamera B" }
    ]
    property var audioDevices: [
        { "id": "mic-a", "description": "Mikrofon A" },
        { "id": "mic-b", "description": "Mikrofon B" }
    ]
    property bool cameraAvailable: true
    property bool cameraActive: true
    property bool recording: false
    property bool paused: false
    property bool clipPlaying: false
    property string currentPath: ""
    property int captureCount: 0
    property string lastCapture: ""
    readonly property QtObject recorder: QtObject {
        property string outputLocation: ""
        function record() { runtime.recording = true }
        function stop() { runtime.recording = false }
    }
    readonly property QtObject imageCapture: QtObject {
        function captureToFile(path) {
            runtime.lastCapture = path
            runtime.captureCount += 1
        }
    }
    function togglePause() { runtime.paused = !runtime.paused }
    function pauseClip() { }
    function playClip(clip) { runtime.clipPlaying = true }
    function stopClipPlayback() { runtime.clipPlaying = false }
}
"""

_KEEPALIVE: list[object] = []


def _kamerasan_panel(window, qt_app, engine, tmp_path, monkeypatch):
    """A kamerás panel megnyitva, helyettesítő futtatóval és valódi tárolóval.

    A tároló a valódi `CameraCaptureController`, a beállításai és a mappája a
    teszt ideiglenes könyvtárában élnek (nem a felhasználói beállításokban)."""
    import picasapy.app.camera_capture_controller as kamera_modul
    from picasapy.app.camera_capture_controller import CameraCaptureController

    monkeypatch.setattr(kamera_modul, "capture_folder", lambda: tmp_path / "felvetel")
    tarolo = CameraCaptureController(
        QSettings(str(tmp_path / "kamera.ini"), QSettings.Format.IniFormat)
    )
    # a gombot a 4137-es próba mintájára engedélyezzük: a fixture nem ad médiavezérlőt
    gomb = _gyerek(window, "toolbarWebcamCaptureButton")
    gomb.setProperty("enabled", True)
    _kattints_ablakban(qt_app, window, gomb)
    popup = _gyerek(window, "captureMoviePanelPopup")
    assert _varj(qt_app, lambda: popup.property("visible") is True), (
        "a webkamerás gomb nem nyitotta meg a panelt"
    )
    # a helyettesítő futtató a tároló előtt áll be, hogy a Loader már ezt töltse
    komponens = QQmlComponent(engine)
    komponens.setData(_FAKE_RUNTIME, QUrl())
    assert [e.toString() for e in komponens.errors()] == []
    _KEEPALIVE.append(komponens)
    loader = _gyerek(popup, "captureMovieMediaLoader")
    loader.setProperty("sourceComponent", komponens)
    popup.setProperty("storage", tarolo)
    _KEEPALIVE.append(tarolo)
    futtato = loader.property("item")
    assert futtato is not None, "a Loader nem töltötte be a futtatót"
    assert _varj(qt_app, lambda: futtato.property("cameraAvailable") is True), (
        "a helyettesítő futtató nem töltődött be"
    )
    return popup, futtato


def _kereses_szoveg(szoveg: str) -> tuple[QQuickWindow, QQuickItem]:
    """Az összes nyitott ablakban a látható elem, amelynek szövege egyezik.

    A legördülő lista tételei külön ablakban/rétegben élnek, ezért nem elég
    a főablak fáját bejárni."""
    for ablak in QGuiApplication.topLevelWindows():
        if not isinstance(ablak, QQuickWindow):
            continue
        sor = [ablak.contentItem()]
        while sor:
            elem = sor.pop()
            if (
                elem.property("text") == szoveg
                and elem.isVisible()
                and elem.width() > 0
                and elem.height() > 0
            ):
                return ablak, elem
            sor.extend(elem.childItems())
    raise AssertionError(f"„{szoveg}” látható tétel nem található")


class TestKameraPanel:
    """A kamerás felvétel-panel gombjai és választói valódi kattintással."""

    def test_pillanatkep_valodi_kattintasra_a_felvetel_utjat_keri(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, futtato = _kamerasan_panel(window, qt_app, engine, tmp_path, monkeypatch)
        gomb = _gyerek(popup, "capturemoviepanelpopup/snapshot")
        assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
            "a Pillanatkép gomb nem lett engedélyezett a kamera mellett"
        )

        _kattints_ablakban(qt_app, window, gomb)

        assert _varj(qt_app, lambda: futtato.property("captureCount") == 1), (
            "a Pillanatkép kattintás nem kérte a képfelvételt"
        )
        utvonal = str(futtato.property("lastCapture"))
        assert utvonal.startswith(str(tmp_path / "felvetel")), (
            f"a pillanatkép nem a felvétel-mappába kerül: {utvonal}"
        )

    def test_felvetel_szunet_valodi_kattintasra_szuneteltet(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, futtato = _kamerasan_panel(window, qt_app, engine, tmp_path, monkeypatch)
        futtato.setProperty("recording", True)
        gomb = _gyerek(popup, "capturemoviepanelpopup/record_pause")
        assert _varj(qt_app, lambda: gomb.property("visible") is True), (
            "felvétel közben nem látszik a Szünet gomb"
        )
        assert gomb.property("text") == "Pause", "a próba feltétele: a szünet felirat"

        _kattints_ablakban(qt_app, window, gomb)

        assert _varj(qt_app, lambda: futtato.property("paused") is True), (
            "a Szünet kattintás nem szüneteltette a felvételt"
        )
        assert _varj(qt_app, lambda: gomb.property("text") == "Resume")

    @pytest.mark.parametrize(
        ("nev", "szoveg", "valasztott_index_kulcs"),
        [
            ("capturemoviepanelpopup/videosrc", "Kamera B", "pendingVideoIndex"),
            ("capturemoviepanelpopup/audiosrc", "Mikrofon B", "pendingAudioIndex"),
        ],
    )
    def test_forraslista_valodi_kattintasra_a_masodik_eszkozt_valasztja(
        self, qml_app, qt_app, tmp_path, monkeypatch, nev, szoveg, valasztott_index_kulcs
    ):
        window, _controller, engine = qml_app
        popup, _futtato = _kamerasan_panel(window, qt_app, engine, tmp_path, monkeypatch)
        # állapot-előkészítés: a beállítások lap megnyitása a panel saját függvényével
        QMetaObject.invokeMethod(popup, "showSettings", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        lista = _gyerek(popup, nev)
        assert _varj(qt_app, lambda: lista.isVisible()), f"{nev} nem látszik a beállításokban"
        assert popup.property(valasztott_index_kulcs) != 1, "a próba feltétele: nem a 2. tétel"

        _kattints_ablakban(qt_app, window, lista)
        ablak, tetel = _kereses_szoveg(szoveg)
        _kattints_ablakban(qt_app, ablak, tetel)

        assert _varj(qt_app, lambda: popup.property(valasztott_index_kulcs) == 1), (
            f"a(z) {nev} választó nem írta át a kiválasztott eszközt"
        )
