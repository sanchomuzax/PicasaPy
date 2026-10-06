"""A #4320 valódi kattintásos próba alfolyamata.

Egyetlen QML motorral próbáljuk a három ablakmagasságot. A sikeres
ellenőrzések után szándékosan azonnal kilépünk: a Qt Multimedia lejátszó
szabályos lebontása ebben a folyamatban GIL↔Qt deadlockra hajlamos.
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
import time
import traceback
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")


def _wait(app, condition, timeout_s: float = 3.0) -> bool:
    from PySide6.QtCore import QEventLoop, QTimer

    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        if condition():
            return True
        app.processEvents()
        loop = QEventLoop()
        QTimer.singleShot(10, loop.quit)
        loop.exec()
    return bool(condition())


def _child(root, name: str):
    from PySide6.QtCore import QObject

    item = root.findChild(QObject, name)
    assert item is not None, f"{name} nem található"
    return item


def _scene_rect(item):
    from PySide6.QtCore import QPointF

    point = item.mapToScene(QPointF(0, 0))
    return (point.x(), point.y(), item.width(), item.height())


def _music_folder_label(root):
    from PySide6.QtCore import QObject

    matches = [
        item for item in root.findChildren(QObject)
        if item.property("text") in (
            "Select a folder of music tracks:",
            "Zeneszámok mappájának kiválasztása:",
        ) and item.width() > 0 and item.height() > 0
    ]
    assert len(matches) == 1, (
        "a zenemappa felirata nem egyértelműen található a kirajzolt fülön"
    )
    return matches[0]


def _click(app, window, item) -> None:
    from PySide6.QtCore import QPointF, Qt
    from PySide6.QtTest import QTest

    assert item.property("enabled") is True, f"{item.objectName()} le van tiltva"
    assert item.width() > 0 and item.height() > 0, (
        f"{item.objectName()} nem kapott kattintható méretet"
    )
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2)).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier,
                     point)
    app.processEvents()


def _run(work_dir: Path) -> None:
    from PySide6.QtCore import QObject, QUrl
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlComponent, QQmlEngine

    repo_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "picasapy_app_conftest", repo_root / "tests/app/conftest.py"
    )
    assert spec and spec.loader
    app_conftest = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = app_conftest
    spec.loader.exec_module(app_conftest)

    work_dir.mkdir(parents=True, exist_ok=True)
    fixture_dir = work_dir / "fixture"
    fixture_dir.mkdir()
    app = QGuiApplication.instance() or QGuiApplication([])
    app_generator = app_conftest._build_qml_app(app, fixture_dir)
    main, controller, _library, engine = next(app_generator)

    settings = controller._get_settings()
    settings.remove("view/slideshowLoop")
    settings.remove("view/slideshowMusicEnabled")
    settings.sync()
    assert bool(controller.slideshowLoop) is False
    assert bool(controller.slideshowMusicEnabled) is True

    options_path = (
        repo_root / "src/picasapy/app/qml/PicasaPy/OptionsDialog.qml"
    )
    component = QQmlComponent(engine, QUrl.fromLocalFile(str(options_path)))
    options = component.create()
    assert options is not None, component.errorString()
    QQmlEngine.setObjectOwnership(options, QQmlEngine.ObjectOwnership.CppOwnership)
    options.show()

    slideshow = _child(main, "slideshowView")
    tab = _child(options, "optionsTabSlideshow")
    loop = _child(options, "optionsSlideshowLoopCheck")
    music = _child(options, "optionsSlideshowPlayMusicCheck")
    browse = _child(options, "optionsSlideshowMusicBrowseButton")
    assert _wait(app, lambda: options.isExposed() and tab.width() > 0)
    _click(app, options, tab)
    assert _wait(app, lambda: tab.property("checked") is True)

    assert bool(loop.property("checked")) is False, (
        "új beállításfájlnál a diavetítés ismétlése alapból ki kell legyen "
        "kapcsolva (LoopSlideshow=0)"
    )
    assert bool(music.property("checked")) is True, (
        "új beállításfájlnál a zenelejátszás alapból legyen bekapcsolva "
        "(PlayMP3Tracks=1)"
    )
    assert bool(controller.slideshowLoop) is False
    assert bool(controller.slideshowMusicEnabled) is True

    label = _music_folder_label(options)
    music_indicator = music.property("indicator")
    assert music_indicator is not None, "a zene jelölőnégyzete nem rajzolódott ki"
    app.processEvents()
    rendered = options.grabWindow()
    assert not rendered.isNull(), "az opciófül renderelése üres képet adott"
    assert rendered.save(str(work_dir / "diavetites-beallitasok.png")), (
        "a kirajzolt diavetítés-fül képe nem menthető"
    )

    geometry_measurements = []
    height = options.height()
    for offset in (-5, 0, 5):
        options.resize(options.width(), height + offset)
        assert _wait(app, lambda: options.isExposed() and loop.width() > 0)

        label_x, label_y, _, label_height = _scene_rect(label)
        _, indicator_y, _, _ = _scene_rect(music_indicator)
        field_x, field_y, _, _ = _scene_rect(
            _child(options, "optionsSlideshowMusicPathField")
        )
        _, browse_y, _, _ = _scene_rect(browse)
        elteresek = {
            "felirat_mezo_x": round(label_x - field_x, 1),
            "mezo_indikator_dx": round(field_x - _scene_rect(music_indicator)[0], 1),
            "mezo_indikator_dy": round(field_y - indicator_y, 1),
            "tallozas_mezo_dy": round(browse_y - field_y, 1),
        }
        assert label_y + label_height <= field_y, (
            "a zenemappa felirata a mező mellett/alatt van, nem fölötte"
        )
        assert abs(elteresek["felirat_mezo_x"]) <= 3, (
            f"a felirat és a mező bal széle eltér: {elteresek}"
        )
        assert abs(elteresek["mezo_indikator_dx"] - 16) <= 3, (
            f"a mező behúzása eltér a referenciától (16 px): {elteresek}"
        )
        # A referencia 42 px-e a felirat magasságát is tartalmazza, ami
        # betűkészletfüggő (CI: 35 px); a mezőt ezért a saját feliratához mérjük.
        assert 0 <= field_y - (label_y + label_height) <= 8, (
            f"a mező nem közvetlenül a felirata alatt áll: {elteresek}"
        )
        assert elteresek["mezo_indikator_dy"] > label_height, (
            f"a mező a jelölőnégyzet fölé csúszott: {elteresek}"
        )
        assert abs(elteresek["tallozas_mezo_dy"]) <= 3, (
            f"a mező és a Tallózás gomb nem egy sorban van: {elteresek}"
        )
        geometry_measurements.append({"ablakmagassag": height + offset,
                                      "elteresek": elteresek})

        before_loop = bool(loop.property("checked"))
        _click(app, options, loop)
        loop_value = not before_loop
        assert bool(controller.slideshowLoop) is loop_value
        assert controller._get_settings().value("view/slideshowLoop") is loop_value
        assert bool(slideshow.property("loop")) is loop_value

        before_music = bool(music.property("checked"))
        _click(app, options, music)
        music_value = not before_music
        assert bool(controller.slideshowMusicEnabled) is music_value
        assert controller._get_settings().value(
            "view/slideshowMusicEnabled"
        ) is music_value
        assert bool(slideshow.property("musicEnabled")) is music_value
        assert bool(browse.property("enabled")) is music_value

    music_dir = work_dir / "music"
    music_dir.mkdir()
    track = music_dir / "01-track.mp3"
    track.write_bytes(b"test track")
    controller.setSlideshowMusicFolder(str(music_dir))
    assert _wait(app, lambda: options.findChild(QObject,
                                                    "optionsSlideshowMusicPathField")
                 .property("text") == str(music_dir))
    assert controller.slideshowMusicFolder == str(music_dir)
    track_urls = slideshow.property("musicTrackUrls")
    assert any(url.toLocalFile() == str(track) for url in track_urls), (
        "a kiválasztott zenemappa számlistája nem jutott el a vetítőig"
    )
    assert bool(controller.slideshowLoop) is True
    assert bool(controller.slideshowMusicEnabled) is False

    # #4448: a mappa saját zenéje felülírja az általános zenemappát, ha a
    # Beállításokban a vetítési zene be van kapcsolva.
    controller.setSlideshowMusicEnabled(True)
    folder_music = Path(controller.currentFolder) / "mappa-zene.mp3"
    folder_music.write_bytes(b"test folder track")
    controller.setFolderMusic(controller.currentFolder, True, str(folder_music))
    assert _wait(app, lambda: len(slideshow.property("musicTrackUrls")) == 1)
    folder_urls = slideshow.property("musicTrackUrls")
    assert folder_urls[0].toLocalFile() == str(folder_music), (
        "a mappa saját zene nem írta felül az általános zenemappát"
    )
    controller.setFolderMusic(controller.currentFolder, False, str(folder_music))
    assert _wait(app, lambda: any(
        url.toLocalFile() == str(track)
        for url in slideshow.property("musicTrackUrls")
    )), "kikapcsolt mappazenénél nem állt vissza az általános zenemappa"
    controller.setSlideshowMusicEnabled(False)

    (work_dir / "diavetites-geometria.json").write_text(
        json.dumps(geometry_measurements, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    folder_dialog = _child(options, "optionsSlideshowMusicFolderDialog")
    _click(app, options, music)
    assert bool(music.property("checked")) is True
    assert bool(browse.property("enabled")) is True
    _click(app, options, browse)
    assert _wait(app, lambda: folder_dialog.property("visible") is True), (
        "a Browse gomb nem nyitotta meg a zenemappa-választót"
    )

    player_qml = repo_root / "src/picasapy/app/qml/PicasaPy/SlideshowMusicPlayer.qml"
    player_component = QQmlComponent(engine, QUrl.fromLocalFile(str(player_qml)))
    assert player_component.isReady(), player_component.errorString()

    print("OK #4320", flush=True)


if __name__ == "__main__":
    try:
        _run(Path(sys.argv[1]))
    except BaseException:
        traceback.print_exc()
        sys.stdout.flush()
        sys.stderr.flush()
        os._exit(1)
    os._exit(0)
