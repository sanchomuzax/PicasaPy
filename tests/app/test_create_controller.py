"""A Létrehozás-szelet (kollázs, mozgófilm — #29) vezérlő-tesztjei.

A háttérszálas munkát a jelzésekre váró QEventLoop-minta követi (a
test_controller.py `_quit_on` mintája szerint).
"""

import cv2
import numpy as np
import pytest
from PySide6.QtCore import QEventLoop, QSettings, QTimer

from support.jpeg_factory import make_jpeg


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", size=(120, 80))
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg", size=(80, 120))
    make_jpeg(root / "nyaralas" / "IMG_0003.jpg", size=(100, 100))
    return root


def _piszkozat_mappa(tmp_path):
    """A kollázs-piszkozat mappája a tesztben (#960).

    A piszkozat a „Kollázsok" album mappájába kerül (`collage/outputDir`) —
    a fixture ezt tmp_path alá állítja, hogy egyetlen teszt se írjon a
    felhasználó valódi képmappájába."""
    return tmp_path / "kollazsok"


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.collage_prefs import OUTPUT_DIR_KEY
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    settings.setValue(OUTPUT_DIR_KEY, str(_piszkozat_mappa(tmp_path)))
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    # #438: a kollázs/mozgófilm háttérszála bevárva, MÍG a controller még
    # él — a #430 SIGSEGV-osztály elkerülése (BackgroundWorkerMixin).
    assert ctl.waitForBackgroundWorkers(30.0), "a create-worker szál nem állt le"


def _run(signal, action, timeout_ms=10000):
    """A műveletet a jelzésre FELIRATKOZVA indítja, majd bevárja azt.

    A sorrend lényeges: a hibautak (üres kijelölés, hiányzó célfájl) még a
    hívó szálon, azonnal jeleznek — utólagos feliratkozás lemaradna róluk.
    Visszatérés: (megjött-e, argumentumok)."""
    loop = QEventLoop()
    received = {}

    def _on(*args):
        received["args"] = args
        loop.quit()

    signal.connect(_on)
    action()
    if "args" not in received:
        QTimer.singleShot(timeout_ms, loop.quit)
        loop.exec()
    return ("args" in received, received.get("args", ()))


def _skip_without_codec(target):
    writer = cv2.VideoWriter(
        str(target), cv2.VideoWriter_fourcc(*"mp4v"), 24.0, (64, 64)
    )
    opened = writer.isOpened()
    writer.release()
    if not opened:
        pytest.skip("Nincs elérhető MP4-kodek ezen a rendszeren.")


class TestMakeCollage:
    def test_creates_file_from_selection(self, controller, tmp_path):
        target = tmp_path / "kollazs.jpg"
        arrived, args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 1, 2], "regulargrid", str(target)),
        )
        assert arrived, "nem érkezett collageFinished"
        path, used, skipped, missing = args
        assert target.exists()
        assert used == 3 and skipped == 0 and missing == 0
        decoded = cv2.imdecode(
            np.frombuffer(target.read_bytes(), np.uint8), cv2.IMREAD_COLOR
        )
        assert decoded is not None and decoded.shape[2] == 3

    def test_file_url_target_is_accepted(self, controller, tmp_path):
        target = tmp_path / "url-kollazs.jpg"
        arrived, _ = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 1], "picturegrid", target.as_uri()),
        )
        assert arrived and target.exists()

    def test_empty_selection_fails_with_message(self, controller, tmp_path):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([], "regulargrid", str(tmp_path / "x.jpg")), 2000,
        )
        assert arrived and args[0]

    def test_missing_target_fails(self, controller):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([0], "regulargrid", ""), 2000,
        )
        assert arrived and args[0]

    def test_unknown_kind_fails(self, controller, tmp_path):
        arrived, args = _run(
            controller.collageFailed,
            lambda: controller.makeCollage([0], "mandala", str(tmp_path / "x.jpg")), 2000,
        )
        assert arrived and args[0]

    def test_out_of_range_rows_are_ignored(self, controller, tmp_path):
        target = tmp_path / "k.jpg"
        arrived, args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage([0, 99], "regulargrid", str(target)),
        )
        assert arrived and args[1] == 1


class TestExportMovie:
    def test_creates_video_from_selection(self, controller, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        target = tmp_path / "film.mp4"
        arrived, args = _run(
            controller.movieFinished,
            lambda: controller.exportMovie([0, 1, 2], str(target), 720, 0.5), 20000,
        )
        assert arrived, "nem érkezett movieFinished"
        path, used, skipped, missing = args
        assert target.exists() and target.stat().st_size > 0
        assert used == 3 and skipped == 0 and missing == 0

    def test_progress_is_emitted(self, controller, tmp_path):
        _skip_without_codec(tmp_path / "proba.mp4")
        seen = []
        controller.movieProgress.connect(lambda done, total: seen.append(done))
        arrived, _ = _run(
            controller.movieFinished,
            lambda: controller.exportMovie(
                [0, 1], str(tmp_path / "film.mp4"), 720, 0.4
            ),
            20000,
        )
        assert arrived
        assert seen == [1, 2]

    def test_empty_selection_fails(self, controller, tmp_path):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie(
                [], str(tmp_path / "film.mp4"), 720, 1.0
            ),
            2000,
        )
        assert arrived and args[0]

    def test_invalid_settings_fail_with_message(self, controller, tmp_path):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie([0], str(tmp_path / "film.mp4"), 720, 0.0), 2000,
        )
        assert arrived and args[0]

    def test_missing_target_fails(self, controller):
        arrived, args = _run(
            controller.movieFailed,
            lambda: controller.exportMovie([0], "", 720, 1.0), 2000,
        )
        assert arrived and args[0]


class TestBackgroundThreadTeardown:
    """#438 (a #430 SIGSEGV-osztály maradéka): a kollázs/mozgófilm
    háttérszála bevárható legyen, mielőtt a controller megsemmisül."""

    def test_wait_without_a_run_returns_immediately(self, controller):
        assert controller.waitForBackgroundWorkers(0.0)

    def test_wait_joins_the_collage_worker_thread(self, controller, tmp_path):
        arrived, _args = _run(
            controller.collageFinished,
            lambda: controller.makeCollage(
                [0, 1], "regulargrid", (tmp_path / "kollazs.jpg").as_uri()
            ),
            20000,
        )
        assert arrived
        assert controller.waitForBackgroundWorkers(30.0)
        assert not controller.backgroundWorkersRunning()


class TestCollagePiszkozat:
    """#960: a `.cxf` piszkozat (`autosave.cxf`) bekötése.

    A #431 elkészítette a piszkozat életciklusát, de **hívó nélkül**: egyetlen
    kódút sem írt piszkozatot. Ezek a tesztek a KIMENETET állítják — a lemezre
    került fájlt olvassák vissza, és a benne álló csomópont-szögeket vetik
    össze a ténylegesen kirajzolt vászonéval. Egy „meghívtuk a függvényt"
    jellegű állítás pont azt nem fogná meg, amiért a jegy külön született.
    """

    KEPEK = [0, 1, 2]
    TEMA = "picturepile"
    KERET = "polaroid"

    def _elonezet(self, controller):
        arrived, _ = _run(
            controller.collagePreviewReady,
            lambda: controller.requestCollagePreview(
                self.KEPEK, self.TEMA, self.KERET
            ),
        )
        assert arrived, "nem érkezett collagePreviewReady"

    def _vaszon(self, controller):
        """A vászon, amit az élő előnézet rajzolt — ugyanazokkal a
        beállításokkal újraszámolva."""
        from picasapy.app.create_controller import _PREVIEW_SIZE
        from picasapy.collage.picasa_render import (
            PicasaCollageSettings,
            make_picasa_collage,
        )

        beallitas = PicasaCollageSettings(
            theme=self.TEMA,
            border=self.KERET,
            width=_PREVIEW_SIZE[0],
            height=_PREVIEW_SIZE[1],
            seed=controller.collageSeed,
        )
        return make_picasa_collage(
            list(controller._sources_for(self.KEPEK)), beallitas
        )

    def test_a_szerkesztes_kozben_keletkezik_piszkozat(self, controller, tmp_path):
        from picasapy.collage.autosave import read_autosave

        self._elonezet(controller)
        projekt = read_autosave(_piszkozat_mappa(tmp_path))
        assert projekt is not None, "az előnézet nem írt piszkozatot"
        assert projekt.theme == self.TEMA
        assert len(projekt.nodes) == len(self.KEPEK)

    def test_a_kiirt_szogek_a_VASZON_szogei(self, controller, tmp_path):
        from picasapy.collage.autosave import read_autosave

        self._elonezet(controller)
        projekt = read_autosave(_piszkozat_mappa(tmp_path))
        vaszon = self._vaszon(controller)
        assert [n.theta for n in projekt.nodes] == pytest.approx(
            [n.theta for n in vaszon.nodes], abs=1e-6
        )
        # az őrnek legyen foga: a Képkupac tényleg forgat, tehát a csupa
        # nulla szög nem menne át
        assert any(abs(n.theta) > 1e-3 for n in vaszon.nodes)

    def test_a_kiirt_geometria_a_VASZONE(self, controller, tmp_path):
        from picasapy.collage.autosave import read_autosave
        from picasapy.collage.draft import nodes_from_project

        self._elonezet(controller)
        vissza = nodes_from_project(read_autosave(_piszkozat_mappa(tmp_path)))
        vaszon = self._vaszon(controller)
        for uj, regi in zip(vissza, vaszon.nodes, strict=True):
            assert uj.center_x == pytest.approx(regi.center_x, abs=1e-2)
            assert uj.center_y == pytest.approx(regi.center_y, abs=1e-2)
            assert uj.width == pytest.approx(regi.width, abs=1e-2)
            assert uj.height == pytest.approx(regi.height, abs=1e-2)
            assert uj.border == regi.border

    def test_a_sikeres_mentes_ELDOBJA_a_piszkozatot(self, controller, tmp_path):
        from picasapy.collage.autosave import autosave_path

        self._elonezet(controller)
        assert autosave_path(_piszkozat_mappa(tmp_path)).exists()
        arrived, _ = _run(
            controller.collageFinished,
            lambda: controller.makeCollage(
                self.KEPEK, self.TEMA, str(tmp_path / "kollazs.jpg"), self.KERET
            ),
        )
        assert arrived
        assert not autosave_path(_piszkozat_mappa(tmp_path)).exists()
        assert controller.collageDraftAvailable is False

    def test_a_MEGHIUSULT_mentes_megtartja_a_piszkozatot(self, controller, tmp_path):
        """A piszkozat épp az elveszett munka ellen van: ha a mentés
        elszáll, maradnia KELL."""
        from picasapy.collage.autosave import autosave_path

        akadaly = tmp_path / "foglalt.jpg"
        akadaly.mkdir()  # a célfájl helyén mappa áll → az írás elbukik
        arrived, _ = _run(
            controller.collageFailed,
            lambda: controller.makeCollage(
                self.KEPEK, self.TEMA, str(akadaly), self.KERET
            ),
        )
        assert arrived
        assert autosave_path(_piszkozat_mappa(tmp_path)).exists()

    def test_a_felajanlas_property_koveti_a_piszkozatot(self, controller, tmp_path):
        """A vezérlő-oldali horog a visszaállítás felajánlásához: a QML erre
        a property-re és a jelzésére köt rá (a párbeszéd a kollázs-panel
        sorozatáé)."""
        valtozasok = []
        controller.collageDraftAvailableChanged.connect(
            lambda: valtozasok.append(controller.collageDraftAvailable)
        )
        assert controller.collageDraftAvailable is False

        self._elonezet(controller)
        assert controller.collageDraftAvailable is True
        assert valtozasok and valtozasok[-1] is True

        controller.discardCollageDraft()
        assert controller.collageDraftAvailable is False
        assert valtozasok[-1] is False
