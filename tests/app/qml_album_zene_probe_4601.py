"""#4601 QML-próba külön folyamatban (a MediaPlayer lebontása GIL-deadlockos)."""

from __future__ import annotations

import importlib.util
import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
os.environ.setdefault("QT_QUICK_BACKEND", "software")


def _wait(app, condition, timeout_s: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout_s
    while time.monotonic() < deadline:
        app.processEvents()
        if condition():
            return True
        time.sleep(0.01)
    app.processEvents()
    return bool(condition())


def _child(root, name: str):
    from PySide6.QtCore import QObject

    child = root.findChild(QObject, name)
    assert child is not None, f"{name} nem található"
    return child


def _click(window, item) -> None:
    from PySide6.QtCore import QPoint, QPointF, Qt
    from PySide6.QtTest import QTest

    assert item.property("enabled") is True, f"{item.objectName()} le van tiltva"
    assert float(item.property("width")) > 0
    assert float(item.property("height")) > 0
    center = item.mapToScene(
        QPointF(float(item.property("width")) / 2,
                float(item.property("height")) / 2)
    ).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(center.x(), center.y()),
    )


def _url_matches_path(url, path: Path) -> bool:
    from PySide6.QtCore import QUrl

    try:
        candidate = url if isinstance(url, QUrl) else QUrl(str(url))
        return Path(candidate.toLocalFile()).samefile(path)
    except (OSError, RuntimeError, ValueError):
        return False


def _install_album_music(controller, library: Path, folder_track: Path) -> None:
    from picasapy.index import open_index, sync_tree
    from picasapy.ini import parse_document, save_document, with_folder_music
    from picasapy.ini.albums import ensure_album, with_album, with_album_fields

    token = "46014601460146014601460146014601"
    document = with_folder_music(parse_document(""), True, str(folder_track))
    document = ensure_album(document, token, "Nyári album")
    document = with_album_fields(
        document,
        token,
        use_music=False,
        music_file="",
    )
    for photo_name in ("a.jpg", "b.jpg"):
        document = with_album(document, photo_name, token)
    save_document(document, library / ".picasa.ini")
    with open_index(controller._db_path) as connection:
        sync_tree(connection, library)
    controller._reload()
    controller.showAlbum(token)


def _run(work_dir: Path) -> None:
    from PySide6.QtGui import QGuiApplication

    import picasapy.app.application as app_module

    repo_root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "picasapy_qml_functional_conftest",
        repo_root / "tests/app/qml_functional/conftest.py",
    )
    assert spec and spec.loader
    conftest = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = conftest
    spec.loader.exec_module(conftest)
    build_qml_app = conftest._build_qml_app

    app_module.allitsd_be_a_stilust()
    app = QGuiApplication.instance() or QGuiApplication([])
    app_module._install_ui_font(app)
    work_dir.mkdir(parents=True, exist_ok=True)
    generator = build_qml_app(app, work_dir)
    window, controller, _engine = next(generator)

    library = work_dir / "kepek"
    album_track = library / "album-zene.mp3"
    folder_track = library / "mappa-zene.mp3"
    album_track.write_bytes(b"album track")
    folder_track.write_bytes(b"folder track")
    shared_music = work_dir / "kozos-zene"
    shared_music.mkdir()
    shared_track = shared_music / "kozos.mp3"
    shared_track.write_bytes(b"shared track")
    _install_album_music(controller, library, folder_track)
    controller.setSlideshowMusicFolder(str(shared_music))
    controller.setSlideshowMusicEnabled(True)

    # A párbeszéd valódi OK gombja menti az album saját usemusic/music mezőit.
    dialog = _child(window, "folderPropertiesDialog")
    dialog.setProperty("mode", "album")
    dialog.setProperty("albumToken", "46014601460146014601460146014601")
    dialog.setProperty("albumName", "Nyári album")
    dialog.setProperty("currentMusicEnabled", False)
    dialog.setProperty("currentMusicFile", "")
    dialog.open()
    assert _wait(app, lambda: dialog.property("visible"))
    music_check = _child(window, "folderPropertiesUseMusic")
    music_path = _child(window, "folderPropertiesMusicPath")
    music_path.setProperty("text", str(album_track))
    _click(window, music_check)
    assert music_check.property("checked") is True
    _click(window, _child(window, "folderPropertiesOkButton"))
    assert _wait(app, lambda: not dialog.property("visible"))
    saved = controller.albumProperties("46014601460146014601460146014601")
    assert saved["use_music"] is True
    assert Path(saved["music_file"]) == album_track
    assert any(
        _url_matches_path(url, album_track)
        for url in controller.slideshowMusicTrackUrls
    ), "a diavetítés zeneválasztása nem az album zenéjét adta"

    original_height = window.height()
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    slideshow = _child(window, "slideshowView")
    create_dialogs = _child(window, "createDialogs").ensure()
    for delta in (-5, 0, 5):
        window.setHeight(original_height + delta)
        assert _wait(
            app,
            lambda delta=delta: window.height() == original_height + delta,
        )

        # A vetítő zenelistája a QML-kötésen át is az album saját zenéje.
        urls = slideshow.property("musicTrackUrls")
        assert any(_url_matches_path(url, album_track) for url in urls), (
            "a vetítés nem az album zenéjét választotta a mappa- és közös zene helyett"
        )

        # A menü ezt a CreateDialogs belépőt hívja; a dialógus audio mezőjét
        # ellenőrizzük, miután a fenti beállító párbeszédet kattintással mentettük.
        create_dialogs.openMovie()
        movie_dialog = _child(create_dialogs, "movieDialog")
        assert _wait(
            app, lambda movie_dialog=movie_dialog: movie_dialog.property("visible")
        )
        assert Path(movie_dialog.property("audioFile")) == album_track, (
            "a filmkészítő nem az album zenéjét választotta alapértelmezett sávnak"
        )
        movie_dialog.close()
        assert _wait(
            app, lambda movie_dialog=movie_dialog: not movie_dialog.property("visible")
        )

    print("OK #4601", flush=True)


if __name__ == "__main__":
    _run(Path(sys.argv[1]))
    # A Qt Multimedia MediaPlayer szabályos QML-lebontása ebben a folyamatban
    # GIL↔Qt deadlockot okozhat; a sikeres ellenőrzések után közvetlenül kilépünk.
    os._exit(0)
