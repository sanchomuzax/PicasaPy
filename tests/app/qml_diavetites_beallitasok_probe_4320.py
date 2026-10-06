"""A #4320 valódi kattintásos próba alfolyamata.

Egyetlen QML motorral próbáljuk a három ablakmagasságot. A sikeres
ellenőrzések után szándékosan azonnal kilépünk: a Qt Multimedia lejátszó
szabályos lebontása ebben a folyamatban GIL↔Qt deadlockra hajlamos.
"""

from __future__ import annotations

import importlib.util
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

    height = options.height()
    for offset in (-5, 0, 5):
        options.resize(options.width(), height + offset)
        assert _wait(app, lambda: options.isExposed() and loop.width() > 0)

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
    assert controller.slideshowLoop is False
    assert controller.slideshowMusicEnabled is True

    folder_dialog = _child(options, "optionsSlideshowMusicFolderDialog")
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
