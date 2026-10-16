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
    időbélyegű egérmozgás zárja le a korábbi kattintást. A dupla kattintást
    két teljes kattintás alkotja: Windowson a magányos MouseButtonDblClick
    esemény nem mindig jut el a QML MouseArea-hoz.
    """
    if elozo_gesztus_volt:
        from PySide6.QtCore import QPoint

        qtest.mouseMove(
            window, point + QPoint(1, 0), delay=double_click_interval_ms + 1
        )
    kattintasok = 2 if dupla else 1
    for _ in range(kattintasok):
        qtest.mouseClick(
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
    # A szándékosan érvénytelen b.mp4 bélyegképe nem készül el, és a sérült
    # kép ajánlata (#459, „Picasa had a problem loading this file(s)") a
    # háttérszálas bélyegkép-készítés ütemében, ~400 ms-os gyűjtés után
    # modális felugróként nyílik meg a nézőre. A próba a kattintási
    # gesztust méri, nem az ajánlatot: ha a felugró épp egy kattintás előtt
    # nyílik (a lassú windowsos CI-n a fotós lépés alatt, #4683), az
    # átfedő lap fogja meg az egeret, és a MouseArea sosem kap eseményt.
    # Az ajánlat külön, determinisztikus tesztje a #459-é.
    for fotosor in controller._photos.photos:
        if fotosor.name == "b.mp4":
            controller._broken_photo_ids.add(fotosor.id)
    app.processEvents()
    print("PROBE-INIT after initial processEvents", flush=True)
    original_height = int(window.height())

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

    aktiv_lepes = {"nev": "előkészítés", "elem": None, "press_events": []}

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

    def elem_az_esemeny_pontjaban(event):
        """A QQuickWindow tartalmán belüli legfelső elem a kurzorpont alatt."""
        try:
            pont = event.position()
            item = window.contentItem()
            while item is not None:
                helyi_pont = item.mapFromScene(pont)
                gyermek = item.childAt(helyi_pont.x(), helyi_pont.y())
                if gyermek is None:
                    return item
                item = gyermek
            return None
        except (AttributeError, RuntimeError, TypeError):
            return None

    def elem_leiras(elem):
        """Az esemény alatti elem: osztály + a legközelebbi elnevezett ős.

        Az üres objectName semmit nem árul el arról, mi fogta meg a kattintást
        (a #4683 windowsos bukásánál `eventTarget=''` volt minden sorban).
        """
        if elem is None:
            return None
        try:
            osztaly = elem.metaObject().className()
            lanc = []
            cur = elem
            while cur is not None and len(lanc) < 6:
                nev = cur.objectName()
                lanc.append(
                    f"{cur.metaObject().className().split('_QML')[0]}"
                    f"[{nev}]@{int(cur.x())},{int(cur.y())}"
                    f"/{int(cur.width())}x{int(cur.height())}"
                )
                cur = cur.parentItem()
            return f"{osztaly}<{'<'.join(lanc)}>"
        except (AttributeError, RuntimeError, TypeError):
            return "<destroyed>"

    def timer_fut(elem):
        if elem is None:
            return None
        try:
            timer = elem.findChild(QObject, "singleClickExitTimer")
            return timer.property("running") if timer is not None else None
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
            f"singleClickExitTimerRunning={timer_fut(elem)!r}, "
            f"pressEventCount={elem_tulajdonsag(elem, 'pressEventCount')!r}, "
            f"lastPressBranch={elem_tulajdonsag(elem, 'lastPressBranch')!r}, "
            "timerRunningOnLastPress="
            f"{elem_tulajdonsag(elem, 'timerRunningOnLastPress')!r}, "
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
                talalat = elem_az_esemeny_pontjaban(event)
                talalat_nev = elem_leiras(talalat)
                timer_running = timer_fut(elem)
                if nev == "press":
                    aktiv_lepes["press_events"].append(
                        {"target": talalat_nev, "timer_running": timer_running}
                    )
                print(
                    "PROBE-MOUSE "
                    f"step={aktiv_lepes['nev']} event={nev} "
                    f"timestamp={event.timestamp()} "
                    f"monotonic={time.monotonic():.6f} "
                    f"eventTarget={talalat_nev!r} "
                    f"singleClickExitTimerRunning={timer_running!r} "
                    f"{nezo_allapot(elem)}",
                    flush=True,
                )
            return False

    esemenynaplozo = QtEsemenyNaplozo(window)
    window.installEventFilter(esemenynaplozo)
    elozo_gesztus_volt = False

    def naplozott_kattintas(nev, elem, *, dupla=False, height_offset=0):
        nonlocal elozo_gesztus_volt
        target_height = original_height + height_offset
        window.setHeight(target_height)
        elem.ensurePolished()
        szulo = elem.parentItem()
        if szulo is not None:
            szulo.ensurePolished()
        window.contentItem().ensurePolished()
        window.update()
        assert varj(
            lambda: int(window.height()) == target_height
            and elem.property("visible") is True
            and float(elem.property("width")) > 0
            and float(elem.property("height")) > 0
        ), f"{nev}: a kattintási célpont nem kapott kirajzolható méretet"

        # A látható, nem nulla méretű elem még őrizheti az előző ablakmagasság
        # jelenetkoordinátáit. A kattintást csak stabil mapToScene-geometriából
        # számoljuk, különben az esemény az ablakig jut, nem a MouseArea-ig.
        elozo_geometria = None
        stabil_mintak = 0

        def geometria_stabil():
            nonlocal elozo_geometria, stabil_mintak
            bal_felso = elem.mapToScene(QPointF(0, 0))
            kozep = elem.mapToScene(
                QPointF(
                    float(elem.property("width")) / 2,
                    float(elem.property("height")) / 2,
                )
            )
            most = tuple(
                round(float(ertek), 3)
                for ertek in (
                    bal_felso.x(),
                    bal_felso.y(),
                    kozep.x(),
                    kozep.y(),
                    elem.property("width"),
                    elem.property("height"),
                )
            )
            if most == elozo_geometria:
                stabil_mintak += 1
            else:
                elozo_geometria = most
                stabil_mintak = 0
            return stabil_mintak >= 2

        assert varj(geometria_stabil), (
            f"{nev}: az ablak átméretezése után nem stabilizálódott a "
            "kattintási célpont geometriája"
        )
        aktiv_lepes.update(nev=nev, elem=elem, press_events=[])
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

    def dupla_feltetelek():
        panel = child("viewerEditorPanel")
        return (
            controller.singleClickExitEnabled,
            viewer.property("layoutMode"),
            panel.property("tiltActive"),
        )

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
    naplozott_kattintas("video-single-click", video_viewport, height_offset=-5)
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
    naplozott_kattintas(
        "video-single-click-exit-click", video_viewport, height_offset=5
    )
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
    naplozott_kattintas(
        "photo-single-click-exit-click", pan_area, height_offset=-5
    )
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
    dupla_allapot = {"belepesek": 0}
    elotte_lenyomasok = pan_area.property("pressEventCount")

    def dupla_kattintas_kezelo():
        dupla_allapot["belepesek"] += 1
        single_exit, layout_mode, tilt_active = dupla_feltetelek()
        print(
            "PROBE-DOUBLECLICK "
            "step=photo-double-click-exit-click handler=entered "
            f"entries={dupla_allapot['belepesek']} "
            f"singleClickExitEnabled={single_exit!r} "
            f"layoutMode={layout_mode!r} tiltActive={tilt_active!r} "
            f"pressEvents={aktiv_lepes['press_events']!r} "
            f"pressEventCountBefore={elotte_lenyomasok!r} "
            f"pressEventCountAfter={pan_area.property('pressEventCount')!r} "
            f"lastPressBranch={pan_area.property('lastPressBranch')!r} "
            "timerRunningOnLastPress="
            f"{pan_area.property('timerRunningOnLastPress')!r}",
            flush=True,
        )

    pan_area.doubleClicked.connect(dupla_kattintas_kezelo)
    naplozott_kattintas(
        "photo-double-click-exit-click", pan_area, dupla=True, height_offset=5
    )
    if dupla_allapot["belepesek"] == 0:
        single_exit, layout_mode, tilt_active = dupla_feltetelek()
        print(
            "PROBE-DOUBLECLICK "
            "step=photo-double-click-exit-click handler=not-entered "
            "entries=0 "
            f"singleClickExitEnabled={single_exit!r} "
            f"layoutMode={layout_mode!r} tiltActive={tilt_active!r} "
            f"pressEvents={aktiv_lepes['press_events']!r} "
            f"pressEventCountBefore={elotte_lenyomasok!r} "
            f"pressEventCountAfter={pan_area.property('pressEventCount')!r} "
            f"lastPressBranch={pan_area.property('lastPressBranch')!r} "
            "timerRunningOnLastPress="
            f"{pan_area.property('timerRunningOnLastPress')!r}",
            flush=True,
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
    # (az előző lépés dupla kattintása a SingleClickExit mellett bezárta a
    # nézőt, ezért a visszalépés előtt újra meg kell nyitni — #4499)
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 0)
    app.processEvents()
    assert varj(lambda: child("viewerImage").property("visible") is True), (
        "a videó után az állóképes előnézet nem jelent meg"
    )
    assert child("videoLoader").property("active") is False
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
