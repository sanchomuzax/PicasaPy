"""#4570: az `AutoPlayMovies` a lejátszóban — megnyitáskor indul-e a videó.

Kikapcsolva a lejátszó áll marad, és a lejátszás gombra indul; bekapcsolva
magától elindul. A próba a valódi `VideoPlayerView.qml`-t tölti be, egy
ffmpeg-gel generált rövid klippel, és a valódi `AppearanceMixin`-t kapja
vezérlőnek (a `autoPlayMovies` kapcsoló ugyanaz, mint a Beállítások-fülön).

Csak lejátszó-hardver/hangkimenet nélkül nem mérhető a tényleges indulás,
ezért a teszt kimarad, ha nincs ffmpeg vagy Qt Multimedia.
"""

from __future__ import annotations

import shutil
import subprocess
import time
from pathlib import Path

import pytest

pytest.importorskip("PySide6.QtMultimedia")

from PySide6.QtCore import QObject, QSettings, QUrl, QMetaObject, Qt  # noqa: E402
from PySide6.QtQml import QQmlComponent, QQmlEngine  # noqa: E402

import picasapy.app  # noqa: E402
from picasapy.app.appearance_controller import AppearanceMixin  # noqa: E402

_APP = Path(picasapy.app.__file__).parent
_LEJATSZO = _APP / "qml" / "PicasaPy" / "VideoPlayerView.qml"
_PLAYING = 1  # MediaPlayer.PlaybackState.PlayingState


def _lejatszik(media) -> bool:
    """A PySide a `playbackState` enum-ot adja vissza, nem egész számot."""
    allapot = media.property("playbackState")
    return getattr(allapot, "value", allapot) == _PLAYING


class _Vezerlo(AppearanceMixin, QObject):
    def __init__(self, settings):
        super().__init__()
        self._settings = settings
        self._init_appearance()

    def _get_settings(self):
        return self._settings

    @property
    def movieVolume(self):  # noqa: N802 — a QML-kötés neve
        return 500


def _klip(tmp_path: Path) -> QUrl:
    if shutil.which("ffmpeg") is None:
        pytest.skip("ffmpeg hiányzik: nincs mit lejátszani")
    kimenet = tmp_path / "klip.mp4"
    subprocess.run(
        [
            "ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi",
            "-i", "testsrc=duration=3:size=64x64:rate=10",
            "-c:v", "mpeg4", "-pix_fmt", "yuv420p", str(kimenet),
        ],
        check=True,
        timeout=60,
    )
    return QUrl.fromLocalFile(str(kimenet))


def _varj(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _lejatszo(qt_app, tmp_path, auto_play: bool, magassag: int = 320):
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    vezerlo = _Vezerlo(settings)
    vezerlo.setAutoPlayMovies(auto_play)

    engine = QQmlEngine()
    engine.addImportPath(str(_APP / "qml"))
    engine.rootContext().setContextProperty("controller", vezerlo)
    komponens = QQmlComponent(engine, QUrl.fromLocalFile(str(_LEJATSZO)))
    assert not komponens.isError(), komponens.errorString()
    nezo = komponens.create()
    assert nezo is not None, komponens.errorString()
    nezo.setProperty("width", 480)
    nezo.setProperty("height", magassag)
    nezo.setProperty("source", _klip(tmp_path))
    return engine, komponens, nezo, vezerlo


def _media(nezo):
    from PySide6.QtCore import QObject as _Q

    media = nezo.findChild(_Q, "viewerMediaPlayer")
    assert media is not None
    return media


@pytest.mark.parametrize("magassag", (315, 320, 325))
def test_kikapcsolva_nem_indul_magatol(qt_app, tmp_path, magassag):
    engine, komponens, nezo, _v = _lejatszo(
        qt_app, tmp_path, auto_play=False, magassag=magassag
    )
    media = _media(nezo)
    # Egy időablak: ha magától indulna, már most játszana.
    _varj(qt_app, lambda: _lejatszik(media), masodperc=1.5)
    assert not _lejatszik(media), (
        "kikapcsolt AutoPlayMovies mellett a videó magától elindult"
    )
    del nezo, komponens, engine


@pytest.mark.parametrize("magassag", (315, 320, 325))
def test_lejatszas_gomb_inditja_kikapcsolva(qt_app, tmp_path, magassag):
    engine, komponens, nezo, _v = _lejatszo(
        qt_app, tmp_path, auto_play=False, magassag=magassag
    )
    media = _media(nezo)
    gomb = nezo.findChild(QObject, "videoPlayButton")
    assert gomb is not None
    QMetaObject.invokeMethod(gomb, "click", Qt.ConnectionType.DirectConnection)
    assert _varj(qt_app, lambda: _lejatszik(media)), (
        "a lejátszás gomb nem indította el a videót"
    )
    del nezo, komponens, engine


@pytest.mark.parametrize("magassag", (315, 320, 325))
def test_bekapcsolva_magatol_indul(qt_app, tmp_path, magassag):
    engine, komponens, nezo, _v = _lejatszo(
        qt_app, tmp_path, auto_play=True, magassag=magassag
    )
    media = _media(nezo)
    assert _varj(qt_app, lambda: _lejatszik(media)), (
        "bekapcsolt AutoPlayMovies mellett a videó nem indult el magától"
    )
    del nezo, komponens, engine
