"""Videó-lejátszás (#14) QML-próbája — KÜLÖN PROCESSZBEN futtatandó.

A MediaPlayer + QML-engine ismételt fel/leépítése egy processzen belül
GIL↔Qt-lock deadlockra hajlamos (a #53-as hibaosztály), ezért a videós
nézet teljes ellenőrzése ebben az egy-engine-es szkriptben fut, amit a
test_qml_video.py alprocesszként indít. Kimenet: OK + exit 0, vagy
AssertionError + exit != 0.
"""

import os
import sys
import time
from pathlib import Path

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


def varj_kattintasablak_vegere(
    app,
    utolso_kattintas: float,
    intervallum_ms: int,
    *,
    ora=None,
    alvas=None,
    tartalek_ms: int = 100,
) -> None:
    """Várja meg a Qt duplakattintási ablakának végét, eseményeket kezelve."""
    ora = ora or time.monotonic
    alvas = alvas or time.sleep
    hatarido = utolso_kattintas + (intervallum_ms + tartalek_ms) / 1000
    while True:
        app.processEvents()
        hatralevo = hatarido - ora()
        if hatralevo <= 0:
            return
        alvas(min(0.05, hatralevo))


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
    from PySide6.QtCore import QEvent, QObject, QPointF, QSettings, Qt
    from PySide6.QtGui import QGuiApplication
    from PySide6.QtQml import QQmlApplicationEngine
    from PySide6.QtTest import QTest

    from support.jpeg_factory import make_jpeg

    app = QGuiApplication([])
    utolso_kattintas_ideje = None

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

    def kattintas(item, dupla=False):
        nonlocal utolso_kattintas_ideje
        if utolso_kattintas_ideje is not None:
            varj_kattintasablak_vegere(
                app,
                utolso_kattintas_ideje,
                QGuiApplication.styleHints().mouseDoubleClickInterval(),
            )
        pont = item.mapToScene(
            QPointF(item.property("width") / 2, item.property("height") / 2)
        ).toPoint()
        if dupla:
            QTest.mouseDClick(window, Qt.MouseButton.LeftButton, pos=pont)
        else:
            QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=pont)
        app.processEvents()
        utolso_kattintas_ideje = time.monotonic()

    def naplozott_dupla_kattintas(item):
        nonlocal utolso_kattintas_ideje
        if utolso_kattintas_ideje is not None:
            varj_kattintasablak_vegere(
                app,
                utolso_kattintas_ideje,
                QGuiApplication.styleHints().mouseDoubleClickInterval(),
            )
        pont = item.mapToScene(
            QPointF(item.property("width") / 2, item.property("height") / 2)
        ).toPoint()

        def naploz(nev):
            def allapot(*_args):
                print(
                    "SingleClickExit állóképes dupla kattintás "
                    f"MouseArea.{nev} után: "
                    f"viewerOpen={window.property('viewerOpen')!r}, "
                    "exitAfterDoubleClick="
                    f"{item.property('exitAfterDoubleClick')!r}",
                    flush=True,
                )

            return allapot

        class QtEsemenyNaplozo(QObject):
            def eventFilter(self, _cel, event):
                nev = {
                    QEvent.Type.MouseButtonPress: "press",
                    QEvent.Type.MouseButtonRelease: "release",
                    QEvent.Type.MouseButtonDblClick: "double-click",
                }.get(event.type())
                if nev is not None:
                    print(
                        "SingleClickExit Qt egéresemény érkezett "
                        f"({nev}); viewerOpen="
                        f"{window.property('viewerOpen')!r}, "
                        "exitAfterDoubleClick="
                        f"{item.property('exitAfterDoubleClick')!r}",
                        flush=True,
                    )
                return False

        item.pressed.connect(naploz("pressed"))
        item.released.connect(naploz("released"))
        item.doubleClicked.connect(naploz("doubleClicked"))
        esemenynaplozo = QtEsemenyNaplozo(window)
        window.installEventFilter(esemenynaplozo)
        QTest.mouseDClick(window, Qt.MouseButton.LeftButton, pos=pont)
        app.processEvents()
        utolso_kattintas_ideje = time.monotonic()
        window.removeEventFilter(esemenynaplozo)
        print(
            "SingleClickExit állóképes dupla kattintás után: "
            f"viewerOpen={window.property('viewerOpen')!r}, "
            "exitAfterDoubleClick="
            f"{item.property('exitAfterDoubleClick')!r}",
            flush=True,
        )

    def varj(feltetel, timeout_s=3.0):
        import time

        hatarido = time.monotonic() + timeout_s
        while time.monotonic() < hatarido:
            app.processEvents()
            if feltetel():
                return True
            time.sleep(0.05)
        app.processEvents()
        return bool(feltetel())

    assert controller.singleClickExitEnabled is False
    video_viewport = item.findChild(QObject, "videoViewport")
    assert video_viewport is not None
    kattintas(video_viewport)
    assert window.property("viewerOpen") is True, (
        "alapállapotban az egyszeres videókattintás bezárta a szerkesztőt"
    )
    kattintas(video_viewport, dupla=True)
    assert varj(lambda: window.property("viewerOpen") is False), (
        "alapállapotban a videóablak dupla kattintása nem tért vissza a könyvtárba"
    )

    window.setProperty("viewerOpen", True)
    controller.setSingleClickExitEnabled(True)
    assert varj(
        lambda: child("videoLoader").property("item") is not None
    ), "a videólejátszó nem épült újra a néző megnyitása után"
    video_item = child("videoLoader").property("item")
    video_viewport = video_item.findChild(QObject, "videoViewport")
    assert video_viewport is not None
    kattintas(video_viewport)
    assert varj(lambda: window.property("viewerOpen") is False), (
        "a SingleClickExit bekapcsolva nem vitte vissza a könyvtárba"
    )

    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    assert varj(lambda: child("viewerImage").property("visible")), (
        "az állóképes előnézet nem jelent meg"
    )
    viewer.setProperty("zoomValue", 1.0)
    pan_area = child("viewerPanArea")
    assert varj(lambda: pan_area.property("enabled")), (
        "a nagyított állóképes előnézet kattintási területe nem aktív"
    )
    kattintas(pan_area)
    assert varj(lambda: window.property("viewerOpen") is False), (
        "a SingleClickExit bekapcsolva az állóképes egyszeres kattintásra "
        "nem tért vissza a könyvtárba"
    )

    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    assert varj(lambda: child("viewerImage").property("visible")), (
        "az állóképes előnézet nem jelent meg újra a dupla kattintás próbájához"
    )
    viewer.setProperty("zoomValue", 1.0)
    pan_area = child("viewerPanArea")
    assert varj(lambda: pan_area.property("enabled"))
    naplozott_dupla_kattintas(pan_area)
    assert varj(lambda: window.property("viewerOpen") is False), (
        "SingleClickExit mellett a dupla kattintás után újranyílt vagy "
        "nyitva maradt az állóképes néző"
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
