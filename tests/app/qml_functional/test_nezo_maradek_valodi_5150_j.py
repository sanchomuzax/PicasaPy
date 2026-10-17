"""A „Néző" csoport maradék vezérlői VALÓDI egérrel (#5150, 9. rész, J).

Az audit (`scripts/valodi_kattintas_audit.py`) szerinti maradék, a „Néző" csoportból:
- `capturemoviepanelpopup/outputsize` - a felvétel-beállítások felbontás-listája;
- `capturevbar/moviecontrols/play`, `…/pause` - a klip lejátszása és szüneteltetése;
- `capturemoviepanelpopup/capture` - a felvétel indítása és leállítása;
- `paintMaskArea` - a festőfelület kattintása ecsetvonást ír a képre;
- `textOverlayHitTarget_` - a képre írt szöveg kijelölése kattintással;
- `captionTrashButton` - a felirat törlése a feliratsorról;
- `viewerMenuAddToAlbumItem_` - a néző helyi menüjének Add to Album tétele.

A kamera és a médiafuttató nincs a tesztgépen: a felvétel-panel Loader-ébe egy
helyettesítő futtató kerül (`_FAKE_RUNTIME`), amely a hívásokat számlálja. A
tesztek a számlálót és a panel állapotát olvassák, nem a hívást magát.

Parancsot közvetlenül nem indítunk: nincs `triggered`/`clicked`/`activated`
hívás és nincs `.emit()`. Az állapot-előkészítés (klip, felirat, album) a
controlleren vagy a panel függvényeivel történik; a tesztelt tételt mindig
valódi egérkattintás éri.
"""

from __future__ import annotations

import pytest
from conftest import _build_qml_app, _negyzet_kepek
from PySide6.QtCore import QMetaObject, QPointF, QSettings, Qt, QUrl
from PySide6.QtGui import QGuiApplication
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickWindow
from PySide6.QtTest import QTest
from support.varakozas import hibaturo_feltetel, var_feltetelre
from tests.app.qml_functional._mappa_kep_menu_5150_helpers import app_epitese
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    album_darab,
    almenu_megnyitasa,
    elokeszit_str,
    gyerek,
    kattints,
    keres_vizualis_mindenablakban,
    vizualis,
)
from _szerkeszto_5150_helpers import figyel, item, nyitott_panel, szerkeszto

#: A felvétel-panel helyettesítő futtatója: ugyanazt a felületet adja, amit a
#: panel használ, a hívásokat számlálja (`playCount`, `pauseCount`, ...).
_FAKE_RUNTIME = b"""
import QtQuick
Item {
    id: runtime
    property var videoDevices: [{ "id": "kam-a", "description": "Kamera A" }]
    property var audioDevices: [{ "id": "mic-a", "description": "Mikrofon A" }]
    property bool cameraAvailable: true
    property bool cameraActive: true
    property bool recording: false
    property bool paused: false
    property bool clipPlaying: false
    property string currentPath: ""
    property int captureCount: 0
    property int playCount: 0
    property int pauseCount: 0
    property int recordCount: 0
    property int stopCount: 0
    readonly property QtObject recorder: QtObject {
        property string outputLocation: ""
        function record() { runtime.recordCount += 1; runtime.recording = true }
        function stop() { runtime.stopCount += 1; runtime.recording = false }
    }
    readonly property QtObject imageCapture: QtObject {
        function captureToFile(path) { runtime.captureCount += 1 }
    }
    function togglePause() { runtime.paused = !runtime.paused }
    function pauseClip() { runtime.pauseCount += 1; runtime.clipPlaying = false }
    function playClip(clip) { runtime.playCount += 1; runtime.clipPlaying = true }
    function stopClipPlayback() { runtime.clipPlaying = false }
}
"""

_KEEPALIVE: list[object] = []


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, hibaturo_feltetel(feltetel), masodperc)


def _szoveg_keres(window, szoveg: str):
    """A látható elem, amelynek `text` tulajdonsága egyezik, a főablakban vagy egy menü-ablakban."""
    for ablak in [window, *QGuiApplication.topLevelWindows()]:
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
                return elem
            sor.extend(elem.childItems())
    raise AssertionError(f"„{szoveg}” látható tétel nem található")


def _kattints_arany(window, qt_app, elem, fx: float, fy: float) -> None:
    """Valódi egérkattintás az elem `fx`, `fy` arányú pontján, a főablakba küldve."""
    pont = elem.mapToScene(QPointF(elem.width() * fx, elem.height() * fy))
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont.toPoint())
    qt_app.processEvents()


@pytest.fixture
def mappa_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.fixture
def szemszinezett_app(qt_app, tmp_path):
    """Két négyzetkép; az elsőn a mentett lánc tartalmaz Vámpírszemet (festhető effekt)."""

    def _keszit(lib):
        _negyzet_kepek(lib)
        (lib / ".picasa.ini").write_text(
            "[a.jpg]\nfilters=ReanimatedEyeColor=1,6.000000,20.000000;\n",
            encoding="utf-8",
        )

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_keszit)


def _felvevo_panel(window, qt_app, engine, tmp_path, monkeypatch):
    """A kamerás felvétel-panel megnyitva, helyettesítő futtatóval és valódi tárolóval."""
    import picasapy.app.camera_capture_controller as kamera_modul
    from picasapy.app.camera_capture_controller import CameraCaptureController

    monkeypatch.setattr(kamera_modul, "capture_folder", lambda: tmp_path / "felvetel")
    tarolo = CameraCaptureController(
        QSettings(str(tmp_path / "kamera.ini"), QSettings.Format.IniFormat)
    )
    gomb = gyerek(window, "toolbarWebcamCaptureButton")
    gomb.setProperty("enabled", True)
    kattints(window, qt_app, gomb)
    popup = gyerek(window, "captureMoviePanelPopup")
    assert _varj(qt_app, lambda: popup.property("visible") is True), (
        "a webkamerás gomb nem nyitotta meg a felvétel-panelt"
    )
    komponens = QQmlComponent(engine)
    komponens.setData(_FAKE_RUNTIME, QUrl())
    assert [e.toString() for e in komponens.errors()] == []
    _KEEPALIVE.append(komponens)
    loader = gyerek(popup, "captureMovieMediaLoader")
    loader.setProperty("sourceComponent", komponens)
    popup.setProperty("storage", tarolo)
    _KEEPALIVE.append(tarolo)
    futtato = loader.property("item")
    assert futtato is not None, "a Loader nem töltötte be a helyettesítő futtatót"
    assert _varj(qt_app, lambda: futtato.property("cameraAvailable") is True)
    return popup, futtato


def _klip_betoltese(popup, futtato, utvonal: str) -> None:
    """Állapot-előkészítés: egy klip a filmszalagon, szünetben (a lejátszás még nem indult)."""
    popup.setProperty("clips", [utvonal])
    popup.setProperty("clipIndex", 0)
    futtato.setProperty("clipPlaying", False)


class TestFelvetelPanel:
    """A kamerás felvétel-panel felbontó-listája, lejátszója és felvétel-gombja."""

    @pytest.mark.xfail(
        strict=True,
        reason=(
            "VALÓDI HIBA (#5150 J): a felbontás-lista (outputsize) kiválasztása "
            "a kattintás után a régi méretet írja a pendingSize-ba: a "
            "onCurrentIndexChanged a currentText-et a frissítés előtt olvassa. "
            "A lista szövege és a currentIndex helyes; ld. a jelentést."
        ),
    )
    def test_felbontas_lista_valodi_kattintassal_uj_meretet_valaszt(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, _futtato = _felvevo_panel(window, qt_app, engine, tmp_path, monkeypatch)
        QMetaObject.invokeMethod(popup, "showSettings", Qt.ConnectionType.DirectConnection)
        qt_app.processEvents()
        lista = gyerek(popup, "capturemoviepanelpopup/outputsize")
        assert _varj(qt_app, lambda: lista.isVisible()), "a felbontás-lista nem látszik"
        assert popup.property("pendingSize") != "1280x720", "a próba feltétele: nem 1280x720"

        kattints(window, qt_app, lista)
        kattints(window, qt_app, _szoveg_keres(window, "1280x720"))

        assert _varj(qt_app, lambda: popup.property("pendingSize") == "1280x720"), (
            "a felbontás-lista kattintás nem írta át a kimeneti méretet"
        )

    def test_lejatszas_gomb_valodi_kattintassal_elinditja_a_klipet(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, futtato = _felvevo_panel(window, qt_app, engine, tmp_path, monkeypatch)
        _klip_betoltese(popup, futtato, str(tmp_path / "klip.mp4"))
        gomb = gyerek(popup, "capturevbar/moviecontrols/play")
        assert _varj(qt_app, lambda: gomb.isVisible()), "a lejátszás gomb nem látszik szünetben"
        elotte = futtato.property("playCount")

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: futtato.property("playCount") == elotte + 1), (
            "a lejátszás kattintás nem indította el a klipet"
        )
        assert _varj(qt_app, lambda: futtato.property("clipPlaying") is True)

    def test_szunet_gomb_valodi_kattintassal_szuneteltet(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, futtato = _felvevo_panel(window, qt_app, engine, tmp_path, monkeypatch)
        _klip_betoltese(popup, futtato, str(tmp_path / "klip.mp4"))
        futtato.setProperty("clipPlaying", True)
        gomb = gyerek(popup, "capturevbar/moviecontrols/pause")
        assert _varj(qt_app, lambda: gomb.isVisible()), "a szünet gomb nem látszik lejátszás közben"

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: futtato.property("pauseCount") == 1), (
            "a szünet kattintás nem szüneteltette a klipet"
        )
        assert _varj(qt_app, lambda: futtato.property("clipPlaying") is False)

    def test_felvetel_gomb_valodi_kattintassal_indul_es_leall(
        self, qml_app, qt_app, tmp_path, monkeypatch
    ):
        window, _controller, engine = qml_app
        popup, futtato = _felvevo_panel(window, qt_app, engine, tmp_path, monkeypatch)
        gomb = gyerek(popup, "capturemoviepanelpopup/capture")
        assert _varj(qt_app, lambda: gomb.property("enabled") is True), (
            "a felvétel gomb nem lett engedélyezett kamera és tároló mellett"
        )

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: futtato.property("recordCount") == 1), (
            "a felvétel kattintás nem indította a rögzítést"
        )
        assert _varj(qt_app, lambda: gomb.property("text") == "Stop")

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: futtato.property("stopCount") == 1), (
            "a második kattintás nem állította le a rögzítést"
        )
        assert _varj(qt_app, lambda: futtato.property("recording") is False)


class TestNezoKepe:
    """A néző képén: festés, szövegkijelölés, felirattörlés és album-tétel."""

    def test_festoterulet_valodi_kattintasra_ecsetvonast_ir(
        self, szemszinezett_app, qt_app
    ):
        window, _controller, viewer, _panel = nyitott_panel(szemszinezett_app, qt_app)
        lanc = szerkeszto(viewer)
        assert _varj(qt_app, lambda: lanc.property("paintMaskSupported") is True), (
            "a próba feltétele: a képen van festhető (Vámpírszem) effekt"
        )
        kapott = figyel(lanc.paintMaskChanged)

        kattints(window, qt_app, item(window, "paintMaskArea"))

        assert _varj(qt_app, lambda: len(kapott) >= 1), (
            "a festőfelületre kattintás nem írt ecsetvonást"
        )

    def test_szovegre_kattintva_kijeloli_a_kepre_irt_szoveget(
        self, mappa_app, qt_app
    ):
        window, controller, engine = mappa_app
        elokeszit_str(window, qt_app, controller)
        window.setProperty("viewerOpen", True)
        gyerek(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        szerkeszto_vezerlo = engine.rootContext().contextProperty("editController")
        panel = gyerek(window, "viewerEditorPanel")
        panel.setProperty("textActive", True)
        szerkeszto_vezerlo.previewTextPlacement(0.3, 0.6)
        szerkeszto_vezerlo.setTextDraft("Nyaralás")
        szerkeszto_vezerlo.applyText()
        qt_app.processEvents()
        # az alkalmazott szöveg automatikusan kijelölődik: az üres képpontra kattintva töröljük
        _kattints_arany(window, qt_app, gyerek(window, "textClickArea"), 0.85, 0.15)
        assert _varj(qt_app, lambda: szerkeszto_vezerlo.textSelectedIndex == -1), (
            "a próba feltétele: nincs kijelölés"
        )

        kattints(window, qt_app, vizualis(window, "textOverlayHitTarget_" + str(0)))

        assert _varj(qt_app, lambda: szerkeszto_vezerlo.textSelectedIndex == 0), (
            "a szövegre kattintás nem jelölte ki a feliratot"
        )

    def test_feliratok_torles_gomb_valodi_kattintasra_uritti_a_feliratot(
        self, mappa_app, qt_app
    ):
        window, controller, _engine = mappa_app
        elokeszit_str(window, qt_app, controller)
        controller.setCaption(0, "Nyaralás")
        window.setProperty("viewerOpen", True)
        gyerek(window, "photoViewer").setProperty("currentIndex", 0)
        qt_app.processEvents()
        mezo = gyerek(window, "captionField")
        assert _varj(qt_app, lambda: mezo.property("text") == "Nyaralás"), (
            "a próba feltétele: a felirat látszik"
        )
        gomb = gyerek(window, "captionTrashButton")
        assert _varj(qt_app, lambda: gomb.property("enabled") is True)

        kattints(window, qt_app, gomb)

        assert _varj(qt_app, lambda: mezo.property("text") == ""), (
            "a törlés gomb nem ürítette ki a feliratot"
        )

    def test_add_to_album_tetel_valodi_kattintasra_hozzaadja_a_nezett_kepet(
        self, mappa_app, qt_app
    ):
        window, controller, _engine = mappa_app
        elokeszit_str(window, qt_app, controller)
        token = controller.createAlbum("Masik", [1])
        assert token, "az album nem jött létre"
        assert _varj(qt_app, lambda: album_darab(controller, token) == 1)
        window.setProperty("viewerOpen", True)
        nezo = gyerek(window, "photoViewer")
        nezo.setProperty("currentIndex", 0)
        qt_app.processEvents()
        kattints(window, qt_app, nezo, Qt.MouseButton.RightButton)
        menu = gyerek(window, "viewerContextMenu")
        assert _varj(qt_app, lambda: menu.property("opened") is True), (
            "a néző közepén végzett jobbklikk nem nyitotta meg a helyi menüt"
        )
        almenu_megnyitasa(window, qt_app, menu, "viewerMenuAddToAlbum")
        elotte = album_darab(controller, token)

        tetel = keres_vizualis_mindenablakban(window, "viewerMenuAddToAlbumItem_" + token)
        assert tetel is not None, "az album tétele nem jelent meg az Add to Album almenüben"
        kattints(window, qt_app, tetel)

        assert _varj(qt_app, lambda: album_darab(controller, token) == elotte + 1), (
            "az Add to Album kattintás nem adta hozzá a nézett képet az albumhoz"
        )
