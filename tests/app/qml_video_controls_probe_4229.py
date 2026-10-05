"""Alfolyam: videós főablak-próbák valódi klippel és kattintással.

A Qt Multimedia motor leállítása GIL/Qt-deadlockosztályba futhat, ezért a
probe a meglévő `qml_video_probe.py` mintájára külön processzben fut.
"""

from __future__ import annotations

import os
import sys
import time
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QGuiApplication
from PySide6.QtTest import QTest

from app.qml_functional.conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.video_factory import make_mp4


def _elem(ablak, nev: str):
    elem = ablak.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} elem nincs a főablakban"
    return elem


def _vard_meg(feltetel, qt_app, leiras: str, hatarido: float = 3.0):
    vege = time.monotonic() + hatarido
    while time.monotonic() < vege:
        qt_app.processEvents()
        if feltetel():
            return
        time.sleep(0.05)
    raise AssertionError(f"időkorláton belül nem teljesült: {leiras}")


def _kattint(ablak, elem, x_arany: float = 0.5) -> None:
    pont = elem.mapToScene(QPointF(elem.width() * x_arany, elem.height() / 2))
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _proba_kepek(mappa: Path) -> None:
    make_jpeg(mappa / "a.jpg", size=(320, 160))
    make_jpeg(mappa / "b.jpg", size=(100, 100))
    make_mp4(mappa / "probaklip.mp4", size=(64, 32), frames=40, fps=10)


def main() -> None:
    proba_mappa = Path(sys.argv[1])
    proba_mappa.mkdir(parents=True, exist_ok=True)
    qt_app = QGuiApplication.instance() or QGuiApplication([])
    epito = _build_qml_app(qt_app, proba_mappa, kepeket_keszit=_proba_kepek)
    ablak, vezerlo, _engine = next(epito)
    video_sor = next(
        i
        for i in range(vezerlo.photos.rowCount())
        if vezerlo.photos.isVideoAt(i)
    )

    # Előbb a nézőt nyitjuk meg üres kijelöléssel; a látható főablak utána
    # kapja meg a klipsort, ahogy a projekt meglévő Qt Multimedia-probe teszi.
    ablak.setProperty("viewerOpen", True)
    qt_app.processEvents()
    nezo = _elem(ablak, "photoViewer")
    nezo.setProperty("currentIndex", video_sor)
    qt_app.processEvents()

    betolto = _elem(ablak, "videoLoader")
    _vard_meg(
        lambda: betolto.property("status") == 1,
        qt_app,
        "a videólejátszó betöltése a főablakban",
    )
    lejatszo = _elem(ablak, "viewerMediaPlayer")
    _vard_meg(
        lambda: lejatszo.property("duration") > 1000,
        qt_app,
        "a próbaklip hosszának dekódolása",
    )
    hossz = lejatszo.property("duration")

    play = _elem(ablak, "videoPlayButton")
    if lejatszo.property("playbackState") == 1:
        _kattint(ablak, play)
        _vard_meg(
            lambda: lejatszo.property("playbackState") != 1,
            qt_app,
            "a videó leállítása a pozíciópróbához",
        )

    seek = _elem(ablak, "videoSeekSlider")
    volume = _elem(ablak, "videoVolumeSlider")
    elvart_hangeroszint = vezerlo.movieVolume
    assert 0 <= elvart_hangeroszint <= 1000
    _vard_meg(
        lambda: abs(volume.property("value") - elvart_hangeroszint / 1000) < 0.01,
        qt_app,
        "a hangerőcsúszka a mentett movievolume értéket mutatja",
    )
    alapmagassag = ablak.height()
    for elteres in (-5, 0, 5):
        celmagassag = alapmagassag + elteres
        ablak.setHeight(celmagassag)
        _vard_meg(
            lambda celmagassag=celmagassag: ablak.height() == celmagassag,
            qt_app,
            f"a főablak {elteres:+d} képpontos magasságváltozása",
        )

        _kattint(ablak, seek, 0.78)
        _vard_meg(
            lambda: lejatszo.property("position") > hossz * 0.5,
            qt_app,
            "a pozíciócsúszka kattintásának lejátszó-kimenete",
        )
        _kattint(ablak, seek, 0.25)
        _vard_meg(
            lambda: lejatszo.property("position") < hossz * 0.5,
            qt_app,
            "a pozíciócsúszka második kattintásának lejátszó-kimenete",
        )

        _kattint(ablak, volume, 0.25)
        assert 0.15 <= volume.property("value") <= 0.4
        assert vezerlo.movieVolume == round(volume.property("value") * 1000)
        _kattint(ablak, volume, 0.75)
        assert 0.6 <= volume.property("value") <= 0.9
        assert vezerlo.movieVolume == round(volume.property("value") * 1000)

    export = _elem(ablak, "movieeditpanel/export_movie")
    assert not export.isEnabled()
    vezerlo.setMovieTrim(video_sor, 200, 1600)
    _vard_meg(
        lambda: lejatszo.property("trimmed"),
        qt_app,
        "a vágott klip exportgombjának engedélyezése",
    )
    assert export.isEnabled()
    kert_export = []
    lejatszo.exportClipRequested.connect(lambda: kert_export.append(True))
    _kattint(ablak, export)
    assert kert_export == [True]
    if sys.platform.startswith("linux"):
        ertesites = _elem(ablak, "videoCaptureNotice")
        _vard_meg(
            lambda: "This feature is not supported for Linux"
            in str(ertesites.property("text")),
            qt_app,
            "a LinuxNomovie felhasználói üzenet",
        )

    print("OK #4229: seek, volume, export_movie", flush=True)
    # A projekt qml_video_probe.py-ja is közvetlen kilépést használ; a Qt
    # Multimedia motor rendes felszámolása GIL/Qt deadlockot okozhat.
    os._exit(0)


if __name__ == "__main__":
    main()
