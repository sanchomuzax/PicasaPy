"""QML-funkcionális teszt — #415: a "Gyakori javítások" fülön a Derítőfény-
csúszka húzása közben egy ÁLLÓ (magas) kép megjelenítési szélessége nem
változhat.

Gyökérok (mérve, ld. lent): a `GpuPointFilterPreview` réteg (PhotoViewer.qml)
`anchors.fill: photo`-val a `photo` Image TELJES befoglaló dobozára igazodott
(`photo.width`/`photo.height` — a rendelkezésre álló terület, NEM a
letterboxolt, ténylegesen kirajzolt terület). A `photo` maga `fillMode:
Image.PreserveAspectFit`-tel a doboznál KISEBB, középre igazított téglalapot
fest (`paintedWidth`/`paintedHeight`) — álló képnél ez keskenyebb, mint a
doboz. Amíg a húzás alatt (finetunePreview → finetuneCommit között) a GPU-
réteg látszik, a doboz TELJES szélességére nyúlik szét (Stretch-szerű
hatás), és a réteg elrejtésekor (elengedéskor) a `photo` alatta lévő,
helyesen illesztett képe válik újra láthatóvá — ez a bejelentett "kiugrás".

A teszt-környezetben (offscreen/software rendering) a GPU-réteg SOSEM válik
LÁTHATÓVÁ (nincs RHI, ld. `test_gpu_finetune_preview.py`), de a QML-kötések
ATTÓL FÜGGETLENÜL kiértékelődnek — a `width`/`height` property tehát a
bug-ot LÁTHATÓSÁG NÉLKÜL is méri: a húzás előtt/alatt/után a GPU-réteg
méretének mindig a `photo` TÉNYLEGESEN kirajzolt (`paintedWidth`/
`paintedHeight`) méretével kell egyeznie, sosem a teljes dobozéval.
"""

from __future__ import annotations

import pytest
from PySide6.QtCore import QObject

from picasapy.index import open_index, sync_tree
from picasapy.version import version_string
from support.jpeg_factory import make_jpeg


def _build_app(qt_app, tmp_path, photo_size):
    """A `conftest.py` `qml_app` fixture mása, egyetlen fotóval, a hívó
    által megadott (szélesség, magasság) mérettel — a megosztott fixture
    fix 320×160/100×100 képei nem alkalmasak az ÁLLÓ-kép reprodukcióra.

    GENERÁTOR (nem sima függvény): a `Python`-oldali kontroller-objektumok
    (`edit_controller` stb.) csak addig élnek, amíg valaki Python-oldalról
    hivatkozik rájuk — a QML-kontextus property NEM veszi át a tulajdonjogot.
    Ha ez a függvény egyszerű `return`-nel adná vissza a `(window, controller,
    engine)` hármast, a helyi változók (és velük a `editController`) a
    függvény visszatérésekor elveszthetnék az utolsó Python-referenciájukat,
    és a GC menet közben szabadíthatná fel őket — ez a teszt futása KÖZBEN
    néma `TypeError: Cannot call method … of null` QML-hibákat okozott (ld.
    a #305 QML-figyelmeztetés-őr). A generátor `yield`-nél megállított
    kerete életben tartja ezeket a helyi változókat a hívó fixture teljes
    élettartama alatt — ugyanaz a minta, mint a `conftest.py` `qml_app`-ja."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.discovery_controller import DiscoveryController
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper
    from picasapy.app.fileops_controller import FileOpsController
    from picasapy.app.folder_tree_controller import FolderTreeController
    from picasapy.app.import_source_controller import ImportSourceController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.app.timeline_controller import TimelineController
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings
    from PySide6.QtQml import QQmlApplicationEngine

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg", size=photo_size)
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider, settings=settings)
    from picasapy.app.confirm_settings_bridge import ConfirmSettingsBridge

    confirm_settings = ConfirmSettingsBridge(settings=settings)
    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    effect_thumb_provider = EffectThumbnailProvider(provider.photo_record)
    engine = QQmlApplicationEngine()
    engine.addImageProvider("thumbs", provider)
    engine.addImageProvider("editpreview", edit_preview)
    engine.addImageProvider("effectthumb", effect_thumb_provider)
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", controller)
    engine.rootContext().setContextProperty("editController", edit_controller)
    fileops_controller = FileOpsController()
    app_module.wire_fileops(fileops_controller, controller)
    engine.rootContext().setContextProperty("fileOpsController", fileops_controller)
    discovery_controller = DiscoveryController(add_folder=controller.addWatchedFolder)
    engine.rootContext().setContextProperty(
        "discoveryController", discovery_controller
    )
    folder_tree_controller = FolderTreeController()
    engine.rootContext().setContextProperty(
        "folderTreeController", folder_tree_controller
    )
    faces_helper = FacesHelper()
    engine.rootContext().setContextProperty("facesHelper", faces_helper)
    face_scan_controller = FaceScanController(db, faces_helper=faces_helper)
    engine.rootContext().setContextProperty(
        "faceScanController", face_scan_controller
    )
    timeline_controller = TimelineController(db, provider)
    controller.syncFinished.connect(timeline_controller.reload)
    engine.rootContext().setContextProperty("timelineController", timeline_controller)
    import_source_controller = ImportSourceController(
        provider, add_folder=controller.addWatchedFolder
    )
    engine.rootContext().setContextProperty(
        "importSourceController", import_source_controller
    )
    engine.rootContext().setContextProperty("appVersion", version_string())
    engine.rootContext().setContextProperty("confirmSettings", confirm_settings)
    engine.load(str(app_module._APP_DIR / "qml" / "Main.qml"))
    assert engine.rootObjects(), "Main.qml betöltése sikertelen"
    window = engine.rootObjects()[0]
    controller._reload()
    controller.selectFolder(str(lib))
    qt_app.processEvents()
    yield window, controller, engine
    engine.deleteLater()
    qt_app.processEvents()


@pytest.fixture
def qml_app_portrait(qt_app, tmp_path):
    # erősen álló kép (1:2 arány) — a doboz szélesnél jóval keskenyebb
    # letterboxolt sávot ad, így a doboz-méretre tapadás jól mérhető
    yield from _build_app(qt_app, tmp_path, (400, 800))


@pytest.fixture
def qml_app_landscape(qt_app, tmp_path):
    yield from _build_app(qt_app, tmp_path, (800, 400))


def _open_viewer(window, qt_app):
    window.setProperty("viewerOpen", True)
    viewer = window.findChild(QObject, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    qt_app.processEvents()
    return viewer


class TestGpuPreviewMeretKiugras415:
    """A GPU-előnézeti réteg mérete a csúszka `pressed → moved → released`
    ciklusa alatt VÉGIG a `photo` ténylegesen kirajzolt méretét kövesse."""

    def _run(self, qml_app, qt_app, *, expect_letterbox_width):
        window, _controller, _engine = qml_app
        viewer = _open_viewer(window, qt_app)
        panel = window.findChild(QObject, "viewerEditorPanel")
        photo = window.findChild(QObject, "viewerImage")
        gpu_layer = window.findChild(QObject, "gpuFinetunePreview")
        slider = panel.findChild(QObject, "fixesFillSlider")
        assert panel.property("activeTab") == 0, (
            "a Derítőfény a 0. (Gyakori javítások) fülön él"
        )

        box_width = photo.property("width")
        painted_width = photo.property("paintedWidth")
        if expect_letterbox_width:
            # a tesztfeltevés önellenőrzése: az álló képnél a doboz
            # SZÉLESEBB, mint a ténylegesen kirajzolt kép — enélkül a
            # teszt nem tudná megkülönböztetni a helyes/hibás kötést
            assert painted_width < box_width, (
                "a teszt-fixture mérete nem ad letterboxot — "
                f"box={box_width}, painted={painted_width}"
            )

        def assert_matches_painted(step):
            width = gpu_layer.property("width")
            height = gpu_layer.property("height")
            assert width == pytest.approx(photo.property("paintedWidth")), (
                f"[{step}] a GPU-előnézet szélessége ({width}) nem a "
                f"kirajzolt kép szélességét ({photo.property('paintedWidth')}) "
                f"követi — a doboz teljes szélességére ({box_width}) tapadt"
            )
            assert height == pytest.approx(photo.property("paintedHeight"))

        assert_matches_painted("húzás előtt")

        slider.setProperty("pressed", True)
        qt_app.processEvents()
        assert_matches_painted("megfogva")

        for value in (0.2, 0.55, 0.9):
            slider.setProperty("value", value)
            qt_app.processEvents()
            assert viewer.property("gpuFinetuneActive") is True
            assert_matches_painted(f"húzás közben (value={value})")

        slider.setProperty("pressed", False)
        qt_app.processEvents()
        assert viewer.property("gpuFinetuneActive") is False
        assert_matches_painted("elengedés után")

    def test_allo_kep_szelessege_nem_ugrik_ki(self, qml_app_portrait, qt_app):
        self._run(qml_app_portrait, qt_app, expect_letterbox_width=True)

    def test_fekvo_kep_is_a_kirajzolt_meretet_koveti(
        self, qml_app_landscape, qt_app
    ):
        # fekvő képnél is a helyes invariánst várjuk (esetfedés, #415) —
        # a doboz itt nem feltétlenül szélesebb a kirajzolt képnél, ezért
        # az önellenőrzés nélkül fut
        self._run(qml_app_landscape, qt_app, expect_letterbox_width=False)
