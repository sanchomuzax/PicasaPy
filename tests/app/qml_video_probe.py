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


QTEST_EGER_DELAY_MS = 10


def qtest_egerlepes(
    qtest,
    window,
    point,
    button,
    double_click_interval_ms: int,
    *,
    dupla: bool,
    elozo_gesztus_volt: bool,
) -> None:
    """Valós Qt-időbélyeggel választja el az egérgesztusokat.

    A QTest saját eseményórát léptet; a falióra szerinti várakozás nem hat rá.
    Egy előző gesztus után ezért egy, a duplakattintási ablaknál hosszabb
    időbélyegű egérmozgás zárja le a korábbi kattintást. A dupla kattintás
    négy eseményén belül rövid, explicit késleltetés marad.
    """
    if elozo_gesztus_volt:
        from PySide6.QtCore import QPoint

        qtest.mouseMove(
            window, point + QPoint(1, 0), delay=double_click_interval_ms + 1
        )
    fuggveny = qtest.mouseDClick if dupla else qtest.mouseClick
    fuggveny(
        window,
        button,
        pos=point,
        delay=QTEST_EGER_DELAY_MS,
    )


def main(work_dir: Path) -> None:
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
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
    effect_thumb_provider = EffectThumbnailProvider(
        provider.photo_record, max_threads=1
    )
    controller = AppController(db, (str(lib),), provider, settings=settings)
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", effect_thumb_provider)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    engine.rootContext().setContextProperty("discoveryController", None)
    engine.rootContext().setContextProperty("timelineController", None)
    engine.rootContext().setContextProperty(
        "fileOpsController", fileops_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    print("PROBE-INIT before Main.qml load", flush=True)
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    print("PROBE-INIT after Main.qml load", flush=True)
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    app.processEvents()
    print("PROBE-INIT after initial processEvents", flush=True)

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

    aktiv_lepes = {"nev": "előkészítés", "elem": None}

    def elem_tulajdonsag(elem, nev):
        if elem is None:
            return None
        try:
            return elem.property(nev)
        except RuntimeError:
            return "<destroyed>"

    def elem_nev(elem):
        if elem is None:
            return None
        try:
            return elem.objectName()
        except RuntimeError:
            return "<destroyed>"

    def nezo_allapot(elem=None):
        return (
            f"viewerOpen={window.property('viewerOpen')!r}, "
            f"currentIndex={viewer.property('currentIndex')!r}, "
            f"isCurrentVideo={viewer.property('isCurrentVideo')!r}, "
            f"singleClickExit={controller.singleClickExitEnabled!r}, "
            "exitAfterDoubleClick="
            f"{elem_tulajdonsag(elem, 'exitAfterDoubleClick')!r}, "
            f"clickTarget={elem_nev(elem)!r}, "
            f"targetEnabled={elem_tulajdonsag(elem, 'enabled')!r}, "
            f"targetVisible={elem_tulajdonsag(elem, 'visible')!r}"
        )

    class QtEsemenyNaplozo(QObject):
        def eventFilter(self, _cel, event):
            nev = {
                QEvent.Type.MouseButtonPress: "press",
                QEvent.Type.MouseButtonRelease: "release",
                QEvent.Type.MouseButtonDblClick: "double-click",
                QEvent.Type.MouseMove: "move",
            }.get(event.type())
            if nev is not None:
                elem = aktiv_lepes["elem"]
                print(
                    "PROBE-MOUSE "
                    f"step={aktiv_lepes['nev']} event={nev} "
                    f"timestamp={event.timestamp()} "
                    f"monotonic={time.monotonic():.6f} "
                    f"{nezo_allapot(elem)}",
                    flush=True,
                )
            return False

    esemenynaplozo = QtEsemenyNaplozo(window)
    window.installEventFilter(esemenynaplozo)
    elozo_gesztus_volt = False

    def naplozott_kattintas(nev, elem, *, dupla=False):
        nonlocal elozo_gesztus_volt
        aktiv_lepes.update(nev=nev, elem=elem)
        print(f"PROBE-STEP START {nev} {nezo_allapot(elem)}", flush=True)
        try:
            pont = elem.mapToScene(
                QPointF(
                    elem.property("width") / 2,
                    elem.property("height") / 2,
                )
            ).toPoint()
            qtest_egerlepes(
                QTest,
                window,
                pont,
                Qt.MouseButton.LeftButton,
                QGuiApplication.styleHints().mouseDoubleClickInterval(),
                dupla=dupla,
                elozo_gesztus_volt=elozo_gesztus_volt,
            )
            app.processEvents()
            elozo_gesztus_volt = True
        finally:
            print(f"PROBE-STEP END {nev} {nezo_allapot(elem)}", flush=True)

    def varj(feltetel, timeout_s=3.0):
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
    naplozott_kattintas("video-single-click", video_viewport)
    assert window.property("viewerOpen") is True, (
        "alapállapotban az egyszeres videókattintás bezárta a szerkesztőt"
    )
    naplozott_kattintas("video-double-click", video_viewport, dupla=True)
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
    naplozott_kattintas("video-single-click-exit-click", video_viewport)
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
    naplozott_kattintas("photo-single-click-exit-click", pan_area)
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
    naplozott_kattintas(
        "photo-double-click-exit-click", pan_area, dupla=True
    )
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
