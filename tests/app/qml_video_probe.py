"""Videó-lejátszás (#14) QML-próbája — KÜLÖN PROCESSZBEN futtatandó.

A MediaPlayer + QML-engine ismételt fel/leépítése egy processzen belül
GIL↔Qt-lock deadlockra hajlamos (a #53-as hibaosztály), ezért a videós
nézet teljes ellenőrzése ebben az egy-engine-es szkriptben fut, amit a
test_qml_video.py alprocesszként indít. Kimenet: OK + exit 0, vagy
AssertionError + exit != 0.
"""

import os
import sys
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def main(work_dir: Path) -> None:
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from picasapy.version import version_string
    from PySide6.QtCore import QObject, QSettings
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine

    from support.jpeg_factory import make_jpeg

    app = QGuiApplication([])

    lib = work_dir / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=(320, 160))
    (lib / "b.mp4").write_bytes(b"\x00" * 64)  # szándékosan érvénytelen videó
    db = work_dir / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    settings = QSettings(
        str(work_dir / "settings.ini"), QSettings.Format.IniFormat
    )
    provider = ThumbnailProvider(ThumbnailCache(work_dir / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider, settings=settings)
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    app.processEvents()

    def child(name):
        obj = window.findChild(QObject, name)
        assert obj is not None, f"{name} nem található"
        return obj

    assert controller.photos.isVideoAt(1) is True, "a b.mp4 nem videó-sor"
    assert controller.photos.isVideoAt(0) is False

    window.setProperty("viewerOpen", True)
    viewer = child("photoViewer")

    # 1) fotó-sor: nincs lejátszó, a kép látszik, a szerkesztő él
    viewer.setProperty("currentIndex", 0)
    app.processEvents()
    assert viewer.property("isCurrentVideo") is False
    assert child("videoLoader").property("active") is False
    assert child("viewerImage").property("visible") is True
    assert child("viewerEditorPanel").property("enabled") is True

    # 2) videó-sor: lejátszó betöltve, kép rejtve/üres, szerkesztő tiltva
    viewer.setProperty("currentIndex", 1)
    app.processEvents()
    assert viewer.property("isCurrentVideo") is True
    loader = child("videoLoader")
    assert loader.property("active") is True
    image = child("viewerImage")
    assert image.property("visible") is False
    assert image.property("source").toString() == ""
    editor_panel = child("viewerEditorPanel")
    assert editor_panel.property("enabled") is False
    # #103: a tiltás LÁTSSZON is — az eszköz-oszlop halvány videónál
    tools_column = editor_panel.findChild(QObject, "toolsColumn")
    assert tools_column.property("opacity") < 1, (
        "az effekt-panel videónál nem szürkül el"
    )

    item = loader.property("item")
    assert item is not None, "a VideoPlayerView nem töltődött be"
    for name in (
        "videoPlayButton",
        "videoSeekSlider",
        "videoTimeLabel",
        "videoVolumeSlider",
        "viewerMediaPlayer",
        "videoControls",
    ):
        assert item.findChild(QObject, name) is not None, f"{name} hiányzik"

    # 3) idő-kijelzés: az (érvénytelen) videónál pozíció és hossz is 0
    time_label = item.findChild(QObject, "videoTimeLabel")
    assert time_label.property("text") == "0:00 / 0:00", (
        f"váratlan idő-címke: {time_label.property('text')!r}"
    )

    # 4) vissza fotóra: a lejátszó elenged, ÉS a kép AZONNAL szerkeszthető
    # (#218 — korábban a videó→kép átmenetnél a szerkesztő-munkamenet
    # NEM indult újra: a panel engedélyezettnek látszott, de az
    # editController-ben nem volt aktív session, amíg egy TOVÁBBI
    # lapozás nem történt)
    viewer.setProperty("currentIndex", 0)
    app.processEvents()
    assert child("videoLoader").property("active") is False
    assert child("viewerImage").property("visible") is True
    assert child("viewerEditorPanel").property("enabled") is True
    assert edit_controller.previewSource != "", (
        "a szerkesztő-munkamenet nem indult el a videó→kép átmenetnél (#218)"
    )

    # 5) #103: tálca ↺/↻ — nézőben fotón aktív, videón tiltott
    rotate_left = child("trayRotateLeft")
    rotate_right = child("trayRotateRight")
    assert rotate_left.property("enabled") is True
    assert rotate_right.property("enabled") is True
    viewer.setProperty("currentIndex", 1)
    app.processEvents()
    assert rotate_left.property("enabled") is False
    assert rotate_right.property("enabled") is False

    # 6) #103: könyvtár-nézetben a kijelölés dönt — csak-videó: tiltva;
    # fotó: aktív; vegyes: aktív (a controller a videókat kihagyja)
    window.setProperty("viewerOpen", False)
    window.setProperty("selectedIndexes", [1])
    window.setProperty("selectedIndex", 1)
    app.processEvents()
    assert rotate_left.property("enabled") is False
    assert rotate_right.property("enabled") is False
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    app.processEvents()
    assert rotate_left.property("enabled") is True
    assert rotate_right.property("enabled") is True
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    app.processEvents()
    assert rotate_left.property("enabled") is True
    assert rotate_right.property("enabled") is True

    print("OK", flush=True)  # os._exit nem üríti a puffert — flush kell!
    # Szándékosan NEM futtatunk rendes Qt-leállítást: a MediaPlayer/ffmpeg
    # szálak leépítése az, ami deadlockra hajlamos — a processz itt kilép,
    # az állapotot az OS takarítja (ezért fut az egész külön processzben).
    os._exit(0)


if __name__ == "__main__":
    main(Path(sys.argv[1]))
