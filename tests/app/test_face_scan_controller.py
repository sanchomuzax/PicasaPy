"""#26 (1. lépcső): `FaceScanController` — a saját arc-detektálás
háttérfolyamata és a „Névtelenek" album.

A HÁLÓZATOT/modellt igénylő valódi YuNet-detektálás helyett egy hamis
detektor van injektálva (a `FaceDetector` konstruktora ELVÁRJA a modellt —
ez a teszt a KÖRÜLÖTTE lévő vezérlő-logikát nézi: kihagyás névcímkés
fotónál, a „Névtelenek" album feltöltése, `modelUnavailable` valódi modell
nélkül). Önálló, host nélküli teszt — a `DedupController`/`PeopleMixin`
mintáját követi (a `controller.py`-beli bekötés az integrátor dolga)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import Qt

from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


def _run(signal, action, timeout_ms=10000):
    """A `test_create_controller.py` mintája: feliratkozás ELŐBB, hívás UTÁNA.

    ⚠️ #2743 (folytatás): az argumentumokat a HUROK adja vissza
    (`jelzes_argumentumai`), nem egy saját, MÁSODIK szlot. A második szlot
    kézbesítése ugyanis nem garantáltan fut le a hurok kilépése előtt:
    mérve 60 futásból 2-3-ban `jelzes_megjott=True` mellett is ÜRES maradt
    a gyűjtő, és ebből lettek a gyors, véletlenszerű `arrived is False`
    bukások (CI: 34248206013, 34254846732). A hurok saját szlotja ELSŐNEK
    van bekötve, tehát ez a verseny nem áll fenn."""
    loop = hangos_hurok(signal, timeout_ms=timeout_ms)
    action()
    loop.exec()
    # #1467: a hívók egy része ELDOBJA a visszaadott `arrived` jelzőt
    # (`_run(ctl.scanFinished, ctl.scanForFaces)` önmagában), ilyenkor az
    # időtúllépés némán ment tovább, és a bukás egy későbbi, látszólag
    # független állításon jelentkezett. Az `exec()` most ott helyben bukik;
    # a visszatérési érték a régi hívók kedvéért marad.
    return (loop.jelzes_megjott, loop.jelzes_argumentumai)


class _FakeEmbedder:
    """A `FaceEmbedder` felületét másoló teszt-dupla — mindig ugyanazt a
    lenyomatot adja vissza, hogy a vezérlő logikáját (kihagyás modell
    nélkül, mentés, csoportosítás-hívás) modell nélkül is le lehessen
    fedni."""

    def __init__(self, available=True, vector=(1.0, 0.0, 0.0)):
        import numpy as np

        self.available = available
        self._vector = np.array(vector, dtype="float32")
        self.calls: list = []

    def compute(self, image, detection):
        self.calls.append((image, detection))
        return self._vector


class _FakeDetector:
    """A `FaceDetector` felületét másoló teszt-dupla — mindig „talál" egy
    arcot, hogy a vezérlő logikáját (kihagyás/mentés/album) modell nélkül
    is le lehessen fedni."""

    def __init__(self, available=True):
        self.available = available
        self.calls: list = []

    def detect(self, image):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks

        self.calls.append(image)
        landmarks = FaceLandmarks(
            right_eye=(10.0, 20.0),
            left_eye=(30.0, 20.0),
            nose=(20.0, 30.0),
            mouth_right=(15.0, 40.0),
            mouth_left=(25.0, 40.0),
        )
        return (FaceDetection(left=5, top=10, right=40, bottom=50, score=0.9, landmarks=landmarks),)


def _make_controller(
    qt_app,
    tmp_path,
    library,
    detector=None,
    embedder=None,
    settings=None,
    embedder_factory=None,
    face_detection_enabled=None,
):
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.index import open_index, sync_tree

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = FaceScanController(
        tmp_path / "index.db",
        detector=detector if detector is not None else _FakeDetector(),
        embedder=embedder if embedder is not None else _FakeEmbedder(),
        embedder_factory=embedder_factory,
        settings=settings,
        face_detection_enabled=face_detection_enabled,
    )
    return ctl


def _make_controller_with_faces_helper(qt_app, tmp_path, library, detector=None):
    """A `_make_controller` mintája, valódi `FacesHelper`-rel — a #3670
    ini-írásos teszteknek."""
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.app.faces_helper import FacesHelper
    from picasapy.index import open_index, sync_tree

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    faces_helper = FacesHelper()
    ctl = FaceScanController(
        tmp_path / "index.db",
        detector=detector if detector is not None else _FakeDetector(),
        embedder=_FakeEmbedder(),
        faces_helper=faces_helper,
    )
    return ctl, faces_helper


class TestModelUnavailable:
    def test_scan_emits_model_unavailable_and_does_not_start(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(qt_app, tmp_path, root, detector=_FakeDetector(available=False))
        arrived, _args = _run(ctl.modelUnavailable, ctl.scanForFaces)
        assert arrived is True
        assert ctl.isAvailable() is False
        assert ctl.waitForBackgroundWorkers(5.0)
        # nem indult szál → nincs eredmény az albumban
        assert ctl.unnamedAlbum() == []

    def test_modellhiany_oka_egyszer_a_hibanaploba_kerul(self, qt_app, tmp_path, caplog):
        """#4517: a tulajdonos naplójában nem volt nyoma, miért nem keres arcot."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(qt_app, tmp_path, root, detector=_FakeDetector(available=False))
        with caplog.at_level("WARNING", logger="picasapy.app.face_scan_controller"):
            _run(ctl.modelUnavailable, ctl.scanForFaces)
            _run(ctl.modelUnavailable, ctl.scanForFaces)
        sorok = [r for r in caplog.records if "arcfelismerés nem indul" in r.getMessage()]
        assert len(sorok) == 1
        assert sorok[0].levelname == "WARNING"


class TestResetFacesForPhotos:
    def test_reset_matches_windows_separator_variants(
        self, qt_app, tmp_path, monkeypatch
    ):
        import ntpath
        from types import SimpleNamespace

        import picasapy.app.face_scan_controller as controller_module
        from picasapy.index import (
            all_photos,
            detected_face_count,
            face_scan_done,
            mark_face_scan,
            open_index,
            replace_faces,
        )

        root = tmp_path / "kepek"
        root.mkdir()
        photo_path = root / "a.jpg"
        make_jpeg(photo_path)
        ctl = _make_controller(
            qt_app, tmp_path, root, detector=_FakeDetector(available=False)
        )
        with open_index(tmp_path / "index.db") as conn:
            photo = all_photos(conn)[0]
            replace_faces(conn, photo.id, _FakeDetector().detect(None))
            mark_face_scan(conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size)
            conn.commit()

        # Nyers, szándékosan kevert elválasztójú bemenet: a Path Windows alatt
        # a str() során egységesítené, mielőtt a teszt ellenőrizhetné az eltérést.
        windows_path = (
            str(photo_path.parent).replace("\\", "/")
            + "\\"
            + photo_path.name
        )
        assert windows_path != str(photo_path)
        monkeypatch.setattr(
            controller_module, "os", SimpleNamespace(path=ntpath), raising=False
        )

        assert ctl._reset_index_faces((windows_path,)) == 1

        with open_index(tmp_path / "index.db") as conn:
            assert detected_face_count(conn, photo.id) == 0
            assert not face_scan_done(
                conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
            )

    def test_reset_clears_index_and_rescans_through_the_background_path(
        self, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.app.face_scan_controller as controller_module
        from picasapy.index import (
            all_photos,
            clear_faces,
            detected_face_count,
            face_scan_done,
            forget_face_scan,
            mark_faces_named,
            open_index,
        )

        root = tmp_path / "kepek"
        root.mkdir()
        photo_path = root / "a.jpg"
        make_jpeg(photo_path)
        detector = _FakeDetector()
        ctl, faces_helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=detector
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(detector.calls) == 1
        assert faces_helper.addFace(str(photo_path), 0.1, 0.2, 0.4, 0.6, "Ada")
        with open_index(tmp_path / "index.db") as conn:
            photo = all_photos(conn)[0]
            assert detected_face_count(conn, photo.id) == 1
            assert face_scan_done(
                conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
            )
            face_id = conn.execute(
                "SELECT id FROM face WHERE photo_id = ?", (photo.id,)
            ).fetchone()[0]
            mark_faces_named(conn, [face_id], "Ada")
            conn.commit()

        inditasok = []
        torolt_arcok = []
        torolt_atnezettseg = []
        eredeti_inditas = ctl._start_face_scan
        eredeti_arc_torles = clear_faces
        eredeti_allapot_torles = forget_face_scan

        def figyelt_inditas(*, automatic):
            inditasok.append(automatic)
            eredeti_inditas(automatic=automatic)

        def figyelt_arc_torles(conn, photo_id):
            torolt_arcok.append(photo_id)
            return eredeti_arc_torles(conn, photo_id)

        def figyelt_allapot_torles(conn, *, photo_id=None, folder_path=None):
            torolt_atnezettseg.append(photo_id)
            return eredeti_allapot_torles(
                conn, photo_id=photo_id, folder_path=folder_path
            )

        monkeypatch.setattr(ctl, "_start_face_scan", figyelt_inditas)
        monkeypatch.setattr(
            controller_module, "clear_faces", figyelt_arc_torles, raising=False
        )
        monkeypatch.setattr(
            controller_module,
            "forget_face_scan",
            figyelt_allapot_torles,
            raising=False,
        )
        befejezes = hangos_hurok(ctl.scanFinished)
        assert ctl.resetFacesForPhotos([str(photo_path)]) == 1
        assert inditasok == [True], "a reset nem indította újra a háttérkeresést"
        assert torolt_arcok == [photo.id]
        assert torolt_atnezettseg == [photo.id]
        befejezes.exec()
        assert befejezes.jelzes_megjott
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(detector.calls) == 2, "a resetelt képen nem futott le újra a detektor"

        with open_index(tmp_path / "index.db") as conn:
            photo = all_photos(conn)[0]
            assert detected_face_count(conn, photo.id) == 1
            assert face_scan_done(
                conn, photo.id, mtime_ns=photo.mtime_ns, size=photo.size
            )
            state = conn.execute(
                "SELECT state FROM face WHERE photo_id = ?", (photo.id,)
            ).fetchone()[0]
            assert state == "unnamed"
        assert [item["name"] for item in ctl.unnamedAlbum()] == ["a.jpg"]

        from picasapy.ini import load_document

        document = load_document(root / ".picasa.ini")
        section = document.section("a.jpg")
        assert section is None or section.get("faces") is None
        assert document.section("Contacts2") is not None

    def test_reset_reports_when_the_detector_model_is_unavailable(
        self, qt_app, tmp_path
    ):
        root = tmp_path / "kepek"
        root.mkdir()
        photo_path = root / "a.jpg"
        make_jpeg(photo_path)
        ctl, faces_helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=_FakeDetector(available=False)
        )
        assert faces_helper.addFace(str(photo_path), 0.1, 0.2, 0.4, 0.6, "Ada")

        arrived, _args = _run(
            ctl.modelUnavailable,
            lambda: ctl.resetFacesForPhotos([str(photo_path)]),
            timeout_ms=2000,
        )

        assert arrived is True
        assert ctl.unavailableReason()


class TestScanForFaces:
    def test_populates_unnamed_album(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        make_jpeg(root / "b.jpg")
        ctl = _make_controller(qt_app, tmp_path, root)
        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        found, scanned = args
        assert found == 2  # egy-egy arc a fake detektortól
        assert scanned == 2
        assert ctl.waitForBackgroundWorkers(5.0)
        album = ctl.unnamedAlbum()
        assert {item["name"] for item in album} == {"a.jpg", "b.jpg"}

    def test_scan_does_not_hold_write_lock_during_next_photo_detection(
        self, qt_app, tmp_path, monkeypatch
    ):
        """Két szál írjon ugyanabba az indexbe: a szinkron közben az
        arcfelismerő a következő képet dolgozza fel."""
        from contextlib import contextmanager
        from threading import Event, Thread

        import picasapy.app.face_scan_controller as module
        from picasapy.index import open_index, photos_in_folder, sync_folder, sync_tree

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        make_jpeg(root / "b.jpg")
        index_path = tmp_path / "index.db"
        with open_index(index_path) as conn:
            sync_tree(conn, root)

        ctl = module.FaceScanController(
            index_path,
            detector=_FakeDetector(),
            embedder=_FakeEmbedder(),
        )
        open_index_original = module.open_index

        @contextmanager
        def open_index_short_timeout(path):
            with open_index_original(path) as conn:
                conn.execute("PRAGMA busy_timeout = 25")
                yield conn

        monkeypatch.setattr(module, "open_index", open_index_short_timeout)
        failures = []
        ctl.scanFailed.connect(failures.append)
        detections = 0
        detection_started = Event()
        continue_detection = Event()

        def detect(_path, **_kwargs):
            nonlocal detections
            detections += 1
            if detections == 2:
                detection_started.set()
                assert continue_detection.wait(10), (
                    "a párhuzamos szinkron nem ért véget"
                )
            return ()

        monkeypatch.setattr(ctl, "_detect", detect)
        scan_thread = Thread(target=ctl._run_scan, args=(Event(),), daemon=True)
        scan_thread.start()
        imported_folders = [root / f"import-{index}" for index in range(1, 13)]
        try:
            assert detection_started.wait(10), (
                "az arcfelismerő nem jutott a második képhez"
            )
            for folder in imported_folders:
                folder.mkdir()
                make_jpeg(folder / "uj.jpg")
            with open_index_short_timeout(index_path) as sync_conn:
                for folder in imported_folders:
                    sync_folder(sync_conn, root, folder)
        finally:
            continue_detection.set()
            scan_thread.join(10)

        assert not scan_thread.is_alive(), "az arcfelismerő szál nem állt le"
        assert failures == []
        with open_index_original(index_path) as conn:
            for folder in imported_folders:
                assert [photo.name for photo in photos_in_folder(conn, folder)] == [
                    "uj.jpg"
                ]

    def test_embedding_does_not_hold_write_lock_during_next_model_run(
        self, qt_app, tmp_path, monkeypatch
    ):
        """Az SFace számítás alatt egy másik mappaszinkronnak írnia kell
        tudnia; a modellfutás nem maradhat a DB-tranzakció része."""
        from contextlib import contextmanager
        from threading import Event

        import numpy as np
        import picasapy.app.face_scan_controller as module
        from picasapy.index import open_index, sync_folder, sync_tree

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        make_jpeg(root / "b.jpg")
        index_path = tmp_path / "index.db"
        with open_index(index_path) as conn:
            sync_tree(conn, root)

        ctl = module.FaceScanController(
            index_path,
            detector=_FakeDetector(),
            embedder=_FakeEmbedder(),
        )
        ctl._run_scan(Event())
        open_index_original = module.open_index

        @contextmanager
        def open_index_short_timeout(path):
            with open_index_original(path) as conn:
                conn.execute("PRAGMA busy_timeout = 25")
                yield conn

        monkeypatch.setattr(module, "open_index", open_index_short_timeout)
        failures = []
        ctl.embeddingFailed.connect(failures.append)
        computations = 0

        class SyncingEmbedder:
            available = True

            def compute(self, _image, _detection):
                nonlocal computations
                computations += 1
                if computations == 2:
                    make_jpeg(root / "uj.jpg")
                    with open_index_short_timeout(index_path) as sync_conn:
                        sync_folder(sync_conn, root, root)
                return np.array([1.0, 0.0, 0.0], dtype="float32")

        ctl._embedder = SyncingEmbedder()
        ctl._run_embedding(
            Event(), suggestions_enabled=False, suggest_step=0, cluster_step=0
        )

        assert failures == []
        with open_index_original(index_path) as conn:
            assert conn.execute(
                "SELECT COUNT(*) FROM face WHERE embedding IS NOT NULL"
            ).fetchone()[0] == 2
            assert conn.execute(
                "SELECT COUNT(*) FROM photos WHERE name = 'uj.jpg'"
            ).fetchone()[0] == 1

    def test_large_photo_detection_scales_input_and_keeps_full_photo_rect(
        self, qt_app, tmp_path
    ):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks
        from picasapy.index import open_index, unnamed_faces

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "nagy.jpg", size=(2560, 1696))
        detector = _FakeDetector()

        def detect(image):
            detector.calls.append(image)
            # A 960×636 képre adott, ahhoz viszonyított minta-találat.
            return (
                FaceDetection(
                    left=240,
                    top=127.2,
                    right=720,
                    bottom=508.8,
                    score=0.95,
                    landmarks=FaceLandmarks(
                        right_eye=(360, 254.4),
                        left_eye=(600, 254.4),
                        nose=(480, 318),
                        mouth_right=(420, 400),
                        mouth_left=(540, 400),
                    ),
                ),
            )

        detector.detect = detect
        ctl = _make_controller(qt_app, tmp_path, root, detector=detector)
        arrived, _args = _run(ctl.scanFinished, ctl.scanForFaces)

        assert arrived is True
        assert len(detector.calls) == 1
        assert max(detector.calls[0].shape[:2]) <= 960
        with open_index(tmp_path / "index.db") as conn:
            saved_rect = unnamed_faces(conn)[0].rect

        # A rect64-stílusú keret a teljes fotó szélességéhez/magasságához
        # képest relatív; a detektált képpontokat ezért mentés előtt vissza
        # kell skálázni erre a méretre.
        assert saved_rect == pytest.approx((0.25, 0.2, 0.75, 0.8))

    def test_photo_with_named_face_is_skipped(self, qt_app, tmp_path):
        # a Picasa döntése szent: névcímkés fotót a saját detektorunk nem
        # értékel újra (issue #26 terve)
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        make_jpeg(root / "b.jpg")
        contact_id = "b8e4117cf1d6615b"
        rect = "3f840000c3509f84"
        (root / ".picasa.ini").write_text(
            f"[Contacts2]\n{contact_id}=Roy Avery;;\n"
            f"[a.jpg]\nfaces=rect64({rect}),{contact_id};\n",
            encoding="utf-8",
        )
        detector = _FakeDetector()
        ctl = _make_controller(qt_app, tmp_path, root, detector=detector)
        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        found, scanned = args
        assert scanned == 1  # csak b.jpg-t vizsgáltuk
        assert found == 1
        album = ctl.unnamedAlbum()
        assert [item["name"] for item in album] == ["b.jpg"]

    def test_unidentified_picasa_face_does_not_block_our_detector(self, qt_app, tmp_path):
        # a fotón VAN Picasa arc-régió, de NINCS névcímke (azonosítatlan) —
        # ez nem "ember által adott névcímke", a saját detektorunk futhat
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        rect = "3f840000c3509f84"
        (root / ".picasa.ini").write_text(
            f"[a.jpg]\nfaces=rect64({rect}),ffffffffffffffff;\n",
            encoding="utf-8",
        )
        ctl = _make_controller(qt_app, tmp_path, root)
        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        found, scanned = args
        assert scanned == 1
        assert found == 1

    def test_second_scan_replaces_instead_of_duplicating(self, qt_app, tmp_path):
        """A második menet nem hoz létre második sort ugyanarra az arcra.

        ⚠️ #2519 óta a második menet a változatlan fotót MEG SEM NÉZI (a
        `face_scan` nyom miatt), tehát a `scanFinished` 0 találatot jelent —
        ez nem a duplikáció hiányát mutatja. A duplikáció-mentességet ezért
        az INDEXBŐL olvassuk ki, nem a jelzés paramétereiből. (Korábban itt
        `found == 1` állt: az a MÁSODIK detektálás eredménye volt, vagyis
        épp a fölösleges újrafutásé.)"""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        _found, scanned = args
        assert scanned == 0, "a változatlan fotót a második menet újra megvizsgálta"
        assert ctl.waitForBackgroundWorkers(5.0)

        from picasapy.index import open_index

        with open_index(tmp_path / "index.db") as conn:
            arcok = conn.execute("SELECT COUNT(*) FROM face").fetchone()[0]
        assert arcok == 1, "az arc duplikálódott az indexben"


class TestComputeEmbeddings:
    """#26 (2. lépcső): a lenyomat-számítás + csoportosítás KÜLÖN,
    alacsonyabb prioritású sora — a detektálás UTÁN, önállóan indítható."""

    def test_embedding_coordinates_are_rescaled_to_reduced_decode(
        self, qt_app, tmp_path, monkeypatch
    ):
        import numpy as np

        from picasapy.faces.detector import FaceDetection, FaceLandmarks
        from picasapy.index import all_photos, open_index, replace_faces

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "nagy.jpg", size=(4000, 2600))
        embedder = _FakeEmbedder()
        ctl = _make_controller(qt_app, tmp_path, root, embedder=embedder)
        detection = FaceDetection(
            left=1000,
            top=650,
            right=3000,
            bottom=1950,
            score=0.95,
            landmarks=FaceLandmarks(
                right_eye=(1400, 1100),
                left_eye=(2600, 1100),
                nose=(2000, 1400),
                mouth_right=(1700, 1700),
                mouth_left=(2300, 1700),
            ),
        )
        with open_index(tmp_path / "index.db") as conn:
            photo = all_photos(conn)[0]
            assert (photo.width, photo.height) == (4000, 2600)
            replace_faces(conn, photo.id, (detection,))
            conn.commit()

        monkeypatch.setattr(
            ctl,
            "_decode",
            lambda _path: np.zeros((1300, 2000, 3), dtype=np.uint8),
        )
        arrived, _args = _run(ctl.embeddingFinished, ctl.computeEmbeddings)

        assert arrived is True
        assert len(embedder.calls) == 1
        image, scaled = embedder.calls[0]
        assert image.shape[:2] == (1300, 2000)
        assert (scaled.left, scaled.top, scaled.right, scaled.bottom) == (
            500,
            325,
            1500,
            975,
        )
        assert scaled.landmarks.right_eye == (700, 550)

    def test_missing_embedding_model_starts_download_automatically(
        self, qt_app, tmp_path, monkeypatch
    ):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.embedder.bundled_model_path", lambda: None
        )
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(
            qt_app, tmp_path, root, embedder=_FakeEmbedder(available=False)
        )
        assert ctl.isEmbeddingAvailable() is False
        letoltesek = []
        elerhetetlensegek = []
        monkeypatch.setattr(ctl, "downloadModels", lambda: letoltesek.append(True))
        ctl.embeddingModelUnavailable.connect(lambda: elerhetetlensegek.append(True))

        ctl.computeEmbeddings()

        assert letoltesek == [True]
        assert elerhetetlensegek == []
        assert ctl.waitForBackgroundWorkers(5.0)

    def test_mocked_sface_download_resumes_grouping(self, qt_app, tmp_path, monkeypatch):
        from picasapy.faces.model_download import (
            EMBEDDER_SPEC,
            STATUS_OK,
            DownloadResult,
        )

        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "xdg"))
        monkeypatch.delenv("PICASAPY_FACE_EMBED_MODEL", raising=False)
        monkeypatch.setattr(
            "picasapy.faces.embedder.bundled_model_path", lambda: None
        )
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        letoltesek = []
        ctl = _make_controller(
            qt_app,
            tmp_path,
            root,
            embedder=_FakeEmbedder(available=False),
            embedder_factory=lambda: _FakeEmbedder(available=True),
            settings=_FaceSettings(),
        )
        monkeypatch.setattr(
            "picasapy.app.face_scan_controller.model_download.download_missing",
            lambda **_kwargs: (
                letoltesek.append(True)
                or (DownloadResult(STATUS_OK, EMBEDDER_SPEC, tmp_path / EMBEDDER_SPEC.filename),)
            ),
        )

        arrived, args = _run(ctl.embeddingFinished, ctl.computeEmbeddings)

        assert arrived is True
        assert args == (0, 0)
        assert letoltesek == [True]
        assert ctl.isEmbeddingAvailable() is True
        assert ctl.waitForBackgroundWorkers(5.0)


class _FaceSettings:
    def __init__(self, values=None):
        self.values = values or {}

    def value(self, key, default=None):
        return self.values.get(key, default)

    def setValue(self, key, value):
        self.values[key] = value


class TestNameTagOptions:
    def test_options_preferences_read_defaults_and_persist_changes(
        self, qt_app, tmp_path
    ):
        root = tmp_path / "kepek"
        root.mkdir()
        settings = _FaceSettings()
        ctl = _make_controller(qt_app, tmp_path, root, settings=settings)

        assert ctl.suggestionsEnabled() is True
        assert ctl.suggestionThreshold() == 85
        assert ctl.clusterThreshold() == 70
        assert ctl.persistFaceToFile() is True

        ctl.setSuggestionsEnabled(False)
        ctl.setSuggestionThreshold(90)
        ctl.setClusterThreshold(75)
        ctl.setPersistFaceToFile(False)

        assert settings.values[ctl.SUGGESTIONS_ENABLED_KEY] is False
        assert settings.values[ctl.SUGGEST_STEP_KEY] == 90
        assert settings.values[ctl.CLUSTER_STEP_KEY] == 75
        assert settings.values[ctl.XMP_ON_NAME_KEY] is False
        assert ctl.suggestionsEnabled() is False
        assert ctl.suggestionThreshold() == 90
        assert ctl.clusterThreshold() == 75
        assert ctl.persistFaceToFile() is False

    def test_embedding_uses_the_saved_suggestion_and_cluster_options(
        self, qt_app, tmp_path, monkeypatch
    ):
        import picasapy.app.face_scan_controller as controller_module
        from picasapy.faces.clustering import step_to_threshold

        root = tmp_path / "kepek"
        root.mkdir()
        settings = _FaceSettings(
            {
                "faces/suggestionsEnabled": False,
                "faces/suggestStep": 90,
                "faces/clusterStep": 75,
            }
        )
        ctl = _make_controller(qt_app, tmp_path, root, settings=settings)
        kapott = {}

        def csoportosits(_conn, **kwargs):
            kapott.update(kwargs)
            return 0

        monkeypatch.setattr(controller_module, "group_unnamed_faces", csoportosits)

        megjott, _ = _run(ctl.embeddingFinished, ctl.computeEmbeddings)

        assert megjott is True
        assert kapott == {
            "suggest_threshold": step_to_threshold(90),
            "cluster_threshold": step_to_threshold(75),
            "named_centroids": {},
        }
        assert ctl.waitForBackgroundWorkers(5.0)


class TestAutomaticFaceDetection:
    def test_automatic_detection_is_enabled_by_default(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        ctl = _make_controller(qt_app, tmp_path, root, settings=_FaceSettings())

        assert ctl.automaticDetectionEnabled() is True

    def test_automatic_detection_setting_is_saved(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        settings = _FaceSettings()
        ctl = _make_controller(qt_app, tmp_path, root, settings=settings)

        ctl.setAutomaticDetectionEnabled(False)

        assert settings.values[ctl.AUTOMATIC_DETECTION_KEY] is False
        assert ctl.automaticDetectionEnabled() is False

    def test_sync_scan_uses_automatic_detection_by_default(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detector = _FakeDetector()
        ctl = _make_controller(
            qt_app, tmp_path, root, detector=detector, settings=_FaceSettings()
        )

        arrived, args = _run(ctl.scanFinished, ctl.scanNewFaces)

        assert arrived is True
        assert args == (1, 1)
        assert len(detector.calls) == 1

    def test_automatic_detection_respects_folder_exclusion(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detector = _FakeDetector()
        ctl = _make_controller(
            qt_app,
            tmp_path,
            root,
            detector=detector,
            settings=_FaceSettings(),
            face_detection_enabled=lambda _path: False,
        )

        _run(ctl.scanFinished, ctl.scanNewFaces)

        assert detector.calls == []

    def test_disabled_setting_skips_automatic_detection(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        detector = _FakeDetector()
        ctl = _make_controller(
            qt_app,
            tmp_path,
            root,
            detector=detector,
            settings=_FaceSettings({"faces/automaticDetection": False}),
        )

        ctl.scanNewFaces()

        assert detector.calls == []

    def test_computes_embeddings_and_groups_unnamed_faces(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        make_jpeg(root / "b.jpg")
        ctl = _make_controller(qt_app, tmp_path, root)
        assert ctl.isEmbeddingAvailable() is True
        # előbb detektálás (a face-sorok forrása), utána — alacsonyabb
        # prioritású, KÜLÖN — a lenyomat-számítás
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        arrived, args = _run(ctl.embeddingFinished, ctl.computeEmbeddings)
        assert arrived is True
        embedded, grouped = args
        assert embedded == 2  # mindkét fotó egy-egy arca lenyomatot kapott
        assert grouped == 2  # a fake embedder mindkettőnek ugyanazt adja → egy csoport
        assert ctl.waitForBackgroundWorkers(5.0)

        from picasapy.index import face_groups, open_index

        with open_index(tmp_path / "index.db") as conn:
            groups = face_groups(conn)
        assert len(groups) == 1
        assert groups[0].face_count == 2


class TestUnnamedGroups:
    """#26 (3. lépcső): a „Névtelenek" album CSOPORTOSÍTOTT nézete és a
    tömeges névadás — a bekötés QML-mentes, közvetlen szintje."""

    def test_no_model_no_scan_gives_empty_groups(self, qt_app, tmp_path):
        # (j)(1): modell hiányában a „Névtelenek" album ÜRES, nem hibázik
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl = _make_controller(
            qt_app, tmp_path, root, detector=_FakeDetector(available=False)
        )
        assert ctl.unnamedGroups(True, True) == []
        flat = ctl.unnamedGroups(False, False)
        assert len(flat) == 1
        assert flat[0]["faces"] == []
        assert ctl.unnamedCount == 0

    def test_flat_mode_returns_a_single_group_with_all_faces(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        make_jpeg(root / "b.jpg", size=(100, 100))
        ctl = _make_controller(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        groups = ctl.unnamedGroups(False, False)
        assert len(groups) == 1
        assert len(groups[0]["faces"]) == 2
        assert "&fz=" in groups[0]["faces"][0]["thumbUrl"]
        assert ctl.unnamedCount == 2

    def test_grouped_mode_after_clustering(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        make_jpeg(root / "b.jpg", size=(100, 100))
        ctl = _make_controller(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        _run(ctl.embeddingFinished, ctl.computeEmbeddings)
        assert ctl.waitForBackgroundWorkers(5.0)
        # a fake embedder mindkét arcnak ugyanazt a lenyomatot adja → 1 csoport
        groups = ctl.unnamedGroups(True, True)
        assert len(groups) == 1
        assert len(groups[0]["faces"]) == 2


class TestAssignNameToFaces:
    """(j)(2)+(3): a tömeges névadás a MEGLÉVŐ `FacesHelper.addFace()` úton
    ír, minden kijelölt archoz — és az első névadás után a név megjelenik
    az Emberek-gyűjteményben (PeopleMixin úton)."""

    def _controller_with_faces_helper(self, qt_app, tmp_path, root):
        from picasapy.app.face_scan_controller import FaceScanController
        from picasapy.app.faces_helper import FacesHelper
        from picasapy.index import open_index, sync_tree

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
        faces_helper = FacesHelper()
        ctl = FaceScanController(
            tmp_path / "index.db",
            detector=_FakeDetector(),
            embedder=_FakeEmbedder(),
            faces_helper=faces_helper,
        )
        return ctl, faces_helper

    def test_assigns_name_to_all_selected_faces_via_faces_helper(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        make_jpeg(root / "b.jpg", size=(100, 100))
        ctl, _helper = self._controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        groups = ctl.unnamedGroups(False, False)
        face_ids = [face["faceId"] for face in groups[0]["faces"]]
        assert len(face_ids) == 2

        ok = ctl.assignNameToFaces(face_ids, "Roy Avery")
        assert ok is True

        # a .picasa.ini mindkét fotón megkapta a névcímkét
        from picasapy.ini import load_document, parse_faces

        document = load_document(root / ".picasa.ini")
        names = {c.person_id.casefold(): c.name for c in _contacts(document)}
        for photo_name in ("a.jpg", "b.jpg"):
            section = document.section(photo_name)
            faces = parse_faces(section.get("faces"))
            assert len(faces) == 1
            assert names.get(faces[0].contact_id.casefold()) == "Roy Avery"

        # a megnevezett arcok eltűnnek a „Névtelenek" albumból
        assert ctl.unnamedCount == 0
        flat = ctl.unnamedGroups(False, False)
        assert len(flat) == 1
        assert flat[0]["faces"] == []

    def test_first_naming_creates_a_people_entry(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, helper = self._controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        groups = ctl.unnamedGroups(False, False)
        face_ids = [face["faceId"] for face in groups[0]["faces"]]

        assert ctl.assignNameToFaces(face_ids, "Roy Avery") is True

        # a `sync_tree` a névadás RÉSZE (ld. face_scan_controller.py) —
        # a friss .picasa.ini-t külön szinkron nélkül is látja
        from picasapy.index import open_index, people_in_index

        with open_index(tmp_path / "index.db") as conn:
            people = people_in_index(conn)
        assert any(person.name == "Roy Avery" for person in people)

    def test_empty_name_or_no_selection_is_a_no_op(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = self._controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        groups = ctl.unnamedGroups(False, False)
        face_ids = [face["faceId"] for face in groups[0]["faces"]]

        assert ctl.assignNameToFaces([], "Roy Avery") is False
        assert ctl.assignNameToFaces(face_ids, "") is False
        assert ctl.assignNameToFaces(face_ids, "   ") is False
        # egyik sem írt semmit — a fotó még mindig névtelen
        assert ctl.unnamedCount == 1

    def test_without_faces_helper_returns_false(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl = _make_controller(qt_app, tmp_path, root)  # faces_helper=None
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        groups = ctl.unnamedGroups(False, False)
        face_ids = [face["faceId"] for face in groups[0]["faces"]]
        assert ctl.assignNameToFaces(face_ids, "Roy Avery") is False


# -- #3670: az elvetés/visszavétel az `ini/` API-n át a `faces=` régió -------
# személy-mezőjébe ír — élőben mérve (picasa-arcfelismeres.md 15.3/b.1):
# `ffffffffffffffff`, NEM `]ignoreface` token/album.


class TestIgnoreFacesWritesIni:
    def test_ignoring_writes_the_ffff_sentinel_for_the_region(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]

        assert ctl.ignoreFaces([face_id]) == 1

        from picasapy.ini import (
            UNIDENTIFIED_CONTACT,
            Rect64,
            decode_rect64,
            encode_rect64,
            load_document,
            parse_faces,
        )

        document = load_document(root / ".picasa.ini")
        faces = parse_faces(document.section("a.jpg").get("faces"))
        assert len(faces) == 1
        # a fake detektor a (5,10,40,50) pixel-keretet adja egy 100×100-as
        # képen — a rect64-rács pontosságára kerekítve
        expected_rect = decode_rect64(encode_rect64(Rect64(0.05, 0.10, 0.40, 0.50)))
        assert faces[0].rect == expected_rect
        assert faces[0].contact_id == UNIDENTIFIED_CONTACT
        assert not faces[0].is_identified

        # az index oldala is mellőzött
        assert ctl.unnamedCount == 0
        assert ctl.ignoredCount() == 1

    def test_ignoring_preserves_other_faces_on_the_photo(self, qt_app, tmp_path):
        # ellenpróba: EGY MÁSIK régió elnevezése a fotón a mellőzés ELŐTT —
        # a mellőzés nem írhatja felül/törölheti a `faces=` más bejegyzését
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        assert helper.addFace(str(root / "a.jpg"), 0.6, 0.6, 0.8, 0.8, "Roy Avery")

        assert ctl.ignoreFaces([face_id]) == 1

        from picasapy.ini import load_document, parse_faces

        document = load_document(root / ".picasa.ini")
        faces = parse_faces(document.section("a.jpg").get("faces"))
        assert len(faces) == 2
        named = [f for f in faces if f.is_identified]
        assert len(named) == 1
        assert named[0].rect.left == pytest.approx(0.6, abs=1e-3)

    def test_ignored_face_is_hidden_and_unignore_removes_its_ffff_entry(
        self, qt_app, tmp_path
    ):
        """A nézőből a mellőzött arc kimarad, a visszavétel pedig csak az
        ini mellőzési jelét távolítja el."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        photo = str(root / "a.jpg")
        assert helper.addFace(photo, 0.6, 0.6, 0.8, 0.8, "Kis Éva")
        assert ctl.ignoreFaces([face_id]) == 1
        assert [face["name"] for face in helper.facesFor(photo)] == ["Kis Éva"]

        assert ctl.unignoreFaces([face_id]) == 1

        from picasapy.ini import load_document, parse_faces

        document = load_document(root / ".picasa.ini")
        faces = parse_faces(document.section("a.jpg").get("faces"))
        assert len(faces) == 1
        assert all(face.is_identified for face in faces)
        assert [face["name"] for face in helper.facesFor(photo)] == ["Kis Éva"]
        assert ctl.unnamedCount == 1

    def test_unignoring_keeps_a_name_given_on_the_same_region(self, qt_app, tmp_path):
        """B3, a másik sorrend: a régió a nézőben előbb nevet kap, a saját
        találatát utána mellőzik — a `faces=` sorban ugyanazzal a kerettel
        egy névcímkés ÉS egy ffff-bejegyzés áll. A visszavétel csak az
        utóbbit viheti.

        # rontás-kontroll: a `removeIgnoredFace` hívás `removeFace`-re
        # cserélve (keret alapú, az ELSŐ egyező bejegyzést törli) → a név
        # tűnik el, ez a teszt bukik."""
        from picasapy.app.face_ignore_ini import quantize_rect

        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        photo = str(root / "a.jpg")
        assert helper.addFace(photo, *quantize_rect(_FAKE_RECT), "Roy Avery")
        assert ctl.ignoreFaces([face_id]) == 1
        assert len(_ini_faces(root, "a.jpg")) == 2

        assert ctl.unignoreFaces([face_id]) == 1

        assert [f["name"] for f in helper.facesFor(photo)] == ["Roy Avery"]

    def test_unignoring_removes_the_ffff_entry_but_not_the_named_one(
        self, qt_app, tmp_path
    ):
        """Az alapeset: a névcímke MÁSIK régión, a mellőzött régió ffff
        bejegyzése a visszavételkor eltűnik."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        assert helper.addFace(str(root / "a.jpg"), 0.6, 0.6, 0.8, 0.8, "Roy Avery")
        assert ctl.ignoreFaces([face_id]) == 1

        assert ctl.unignoreFaces([face_id]) == 1

        from picasapy.ini import load_document, parse_faces

        document = load_document(root / ".picasa.ini")
        faces = parse_faces(document.section("a.jpg").get("faces"))
        assert len(faces) == 1
        assert faces[0].is_identified
        assert faces[0].rect.left == pytest.approx(0.6, abs=1e-3)
        # az index oldala is visszaáll
        assert ctl.unnamedCount == 1
        assert ctl.ignoredCount() == 0

    def test_unignoring_the_only_entry_drops_the_faces_key(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        assert ctl.ignoreFaces([face_id]) == 1

        assert ctl.unignoreFaces([face_id]) == 1

        from picasapy.ini import load_document

        document = load_document(root / ".picasa.ini")
        section = document.section("a.jpg")
        assert (section.get("faces") if section is not None else None) is None

    def test_without_faces_helper_only_updates_the_index(self, qt_app, tmp_path):
        # visszamenőleges kompatibilitás: `FacesHelper` nélkül (mint eddig)
        # csak az index frissül, ini-írás nélkül — nem hibázik
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl = _make_controller(qt_app, tmp_path, root)  # faces_helper=None
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]

        assert ctl.ignoreFaces([face_id]) == 1
        assert ctl.ignoredCount() == 1
        assert not (root / ".picasa.ini").exists()

        assert ctl.unignoreFaces([face_id]) == 1
        assert ctl.ignoredCount() == 0


class TestIgnoreSurvivesRescan:
    """#3670, „kész, ha" 4. pont: a `.picasa.ini`-ben mellőzöttként jelölt
    régió egy friss újraindexelés után NEM kerül vissza a „Névtelenek"
    közé — a felismerés a `faces=…,ffffffffffffffff` bejegyzést a saját
    indexben is `'ignored'`-ra fordítja."""

    def test_a_rescan_keeps_a_previously_ignored_face_ignored(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        assert ctl.ignoreFaces([face_id]) == 1

        from picasapy.index import forget_face_scan, open_index

        with open_index(tmp_path / "index.db") as conn:
            photo_id = conn.execute(
                "SELECT id FROM photos WHERE name = 'a.jpg'"
            ).fetchone()["id"]
            forget_face_scan(conn, photo_id=photo_id)
            conn.commit()

        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        found, scanned = args
        assert scanned == 1
        assert found == 1
        assert ctl.waitForBackgroundWorkers(5.0)

        # a friss találat AZONNAL mellőzöttként jelenik meg — nem
        # javaslatként a „Névtelenek" albumban
        assert ctl.unnamedCount == 0
        assert ctl.ignoredCount() == 1

    def test_rescan_only_reignores_the_matching_region(self, qt_app, tmp_path):
        # a mellőzés RÉGIÓ-pontos: egy fotó MÁSIK, éppen most felbukkanó
        # arca nem lesz automatikusan mellőzött csak azért, mert a fotón
        # VAN egy másik, korábban mellőzött régió
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=_TwoFaceDetector()
        )
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        faces = ctl.unnamedGroups(False, False)[0]["faces"]
        assert len(faces) == 2
        ignored_id = faces[0]["faceId"]

        assert ctl.ignoreFaces([ignored_id]) == 1
        assert ctl.unnamedCount == 1
        assert ctl.ignoredCount() == 1

        from picasapy.index import forget_face_scan, open_index

        with open_index(tmp_path / "index.db") as conn:
            photo_id = conn.execute(
                "SELECT id FROM photos WHERE name = 'a.jpg'"
            ).fetchone()["id"]
            forget_face_scan(conn, photo_id=photo_id)
            conn.commit()

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        # a második arc VÁLTOZATLANUL névtelen maradt — csak az elvetett
        # régió lett újra mellőzött
        assert ctl.unnamedCount == 1
        assert ctl.ignoredCount() == 1


class _TwoFaceDetector:
    """Két, ELTÉRŐ régiójú arcot „talál" — a régió-pontos egyeztetés
    teszteléséhez (#3670): a `_FakeDetector` mintáját követi, de két
    `FaceDetection`-t ad vissza."""

    def __init__(self, available=True):
        self.available = available
        self.calls: list = []

    def detect(self, image):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks

        self.calls.append(image)
        landmarks = FaceLandmarks(
            right_eye=(10.0, 20.0),
            left_eye=(30.0, 20.0),
            nose=(20.0, 30.0),
            mouth_right=(15.0, 40.0),
            mouth_left=(25.0, 40.0),
        )
        return (
            FaceDetection(left=5, top=10, right=40, bottom=50, score=0.9, landmarks=landmarks),
            FaceDetection(left=55, top=55, right=90, bottom=95, score=0.8, landmarks=landmarks),
        )


# -- #3670 (átnézés): átfedés alapú egyeztetés, a Picasa ffff-régiói az
# albumban, kereten túllógó arc --------------------------------------------

#: a `_FakeDetector` kerete egy 100×100-as képen, relatívan
_FAKE_RECT = (0.05, 0.10, 0.40, 0.50)
#: ugyanez 1 px-lel jobbra tolva — az eredeti Picasa detektora sosem adja
#: bitre ugyanazt a keretet, mint a miénk
_FAKE_RECT_SHIFTED = (0.06, 0.10, 0.41, 0.50)
#: ugyanez az arc, ahogy az eredeti Picasa keretezi: 1,5× szélesebb és
#: magasabb, a képszélen vágva. A sima IoU-ja a miénkkel 0,48 — a mért
#: korpusz-medián 0,43 (ld. `test_the_overlap_is_measured_on_the_smaller_box`)
_FAKE_RECT_PICASA = (0.0, 0.0, 0.4875, 0.60)


def _write_ini_faces(root, name, entries, contacts=""):
    """Egy `.picasa.ini` az eredeti Picasa írta alakban — a tesztben
    közvetlenül, mert ez a KÜLSŐ bemenet (a termékkód az `ini/` API-n át
    ír)."""
    from picasapy.ini import Rect64, encode_rect64

    faces = "".join(
        f"rect64({encode_rect64(Rect64(*rect))}),{contact};"
        for rect, contact in entries
    )
    (root / ".picasa.ini").write_text(
        f"{contacts}[{name}]\nfaces={faces}\n", encoding="utf-8"
    )


def _face_states(tmp_path):
    from picasapy.index import open_index

    with open_index(tmp_path / "index.db") as conn:
        return [
            row["state"]
            for row in conn.execute("SELECT state FROM face ORDER BY id")
        ]


def _ini_faces(root, name):
    from picasapy.ini import load_document, parse_faces

    section = load_document(root / ".picasa.ini").section(name)
    raw = section.get("faces") if section is not None else None
    return parse_faces(raw) if raw else ()


_FFFF = "ffffffffffffffff"


class TestIgnoreMatchesByOverlap:
    """B2: a korpusz 1 995 mellőzött arcát az eredeti Picasa detektora
    jelölte ki — a keretük sosem bitre azonos a miénkkel. Az egyeztetés
    ezért átfedés (IoU) alapú."""

    def test_the_overlap_is_measured_on_the_smaller_box(self):
        """A mérés (2026-09-27, a tulajdonos könyvtára, 400 Picasa-keret a
        YuNet-találatokkal): a Picasa kerete területben ~2,3× NAGYOBB a
        miénknél, ezért a sima IoU mediánja 0,43 — a 0,5-ös IoU-küszöb a
        keretek 77%-át elvesztené. A kisebbik keretre vetített átfedés 0,5
        fölött a keretek 88%-át párosítja."""
        from picasapy.app.face_ignore_ini import IGNORE_MATCH_OVERLAP, region_overlap

        assert IGNORE_MATCH_OVERLAP == 0.5
        assert region_overlap(_FAKE_RECT, _FAKE_RECT) == pytest.approx(1.0)
        assert region_overlap(_FAKE_RECT, (0.5, 0.5, 0.9, 0.9)) == 0.0
        assert region_overlap(_FAKE_RECT, _FAKE_RECT_SHIFTED) > 0.9
        assert region_overlap(_FAKE_RECT, _FAKE_RECT_PICASA) == pytest.approx(1.0)

    def test_a_picasa_region_one_pixel_off_keeps_the_face_ignored(
        self, qt_app, tmp_path
    ):
        """# rontás-kontroll: a `_mark_previously_ignored` visszaállítva a
        bitre pontos egyezésre (`_quantize_rect(face.rect) in
        ignored_rects`) → unnamed 1, ignored 0, a teszt bukik."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT_SHIFTED, _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert ctl.unnamedCount == 0
        assert _face_states(tmp_path) == ["ignored"]

    def test_a_picasa_sized_region_keeps_the_face_ignored(self, qt_app, tmp_path):
        """# rontás-kontroll: az egyeztetés sima IoU ≥ 0,5-re állítva → a
        Picasa-méretű keret (IoU 0,48) nem párosul, unnamed 1, a teszt
        bukik."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT_PICASA, _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert ctl.unnamedCount == 0
        assert _face_states(tmp_path) == ["ignored"]

    def test_one_region_ignores_only_one_face(self, qt_app, tmp_path):
        """Páronként egy: egy Picasa-keret egyetlen saját találatot visz
        mellőzöttbe, akkor is, ha a keret két találatot is lefed."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [((0.0, 0.0, 1.0, 1.0), _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=_TwoFaceDetector()
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert sorted(_face_states(tmp_path)) == ["ignored", "unnamed"]

    def test_an_already_scanned_photo_is_matched_on_the_next_scan(
        self, qt_app, tmp_path
    ):
        """A mi indexünk a Picasa mellőzése ELŐTT is láthatta a képet: a
        következő keresés a már átnézett fotón is átveszi a mellőzést."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        assert ctl.unnamedCount == 1
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT_SHIFTED, _FFFF)])

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert ctl.unnamedCount == 0
        assert _face_states(tmp_path) == ["ignored"]

    def test_a_barely_overlapping_region_is_another_face(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [((0.30, 0.40, 0.65, 0.80), _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert ctl.unnamedCount == 1
        assert _face_states(tmp_path) == ["unnamed"]

    def test_ignoring_does_not_duplicate_a_picasa_region(self, qt_app, tmp_path):
        """Ha a Picasa már mellőzte (eltérő kerettel), a mi mellőzésünk
        nem ír mellé egy második ffff-bejegyzést ugyanarra az arcra."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT_SHIFTED, _FFFF)])

        assert ctl.ignoreFaces([face_id]) == 1

        assert len(_ini_faces(root, "a.jpg")) == 1

    def test_unignoring_removes_the_matching_picasa_region(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT_SHIFTED, _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.ignoredGroups()[0]["faces"][0]["faceId"]

        assert ctl.unignoreFaces([face_id]) == 1

        assert _ini_faces(root, "a.jpg") == ()
        assert ctl.unnamedCount == 1
        assert ctl.ignoredGroups() == []


class TestIgnoredAlbumShowsIniRegions:
    """B2: a „Mellőzött emberek" album az eredeti Picasa által mellőzött
    (`faces=…,ffffffffffffffff`) arcokat is mutatja — akkor is, ha a mi
    detektorunk a képet még nem nézte át."""

    def test_a_picasa_ignored_face_is_listed(self, qt_app, tmp_path):
        """# rontás-kontroll: az `ignoredGroups` visszaállítva a csak-index
        változatra → [] jön, a teszt bukik."""
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(root, "a.jpg", [(_FAKE_RECT, _FFFF)])
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)

        groups = ctl.ignoredGroups()

        assert len(groups) == 1
        faces = groups[0]["faces"]
        assert len(faces) == 1
        from picasapy.index import open_index

        with open_index(tmp_path / "index.db") as conn:
            photo_id = conn.execute(
                "SELECT id FROM photos WHERE name = 'a.jpg'"
            ).fetchone()["id"]
        assert faces[0]["thumbUrl"].startswith(f"image://thumbs/{photo_id}")
        assert ctl.ignoredCount() == 1

    def test_unignoring_it_removes_only_the_ffff_pair(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        _write_ini_faces(
            root, "a.jpg",
            [(_FAKE_RECT, _FFFF), ((0.6, 0.6, 0.8, 0.8), "8e62b2035b74b477")],
            contacts="[Contacts2]\n8e62b2035b74b477=Roy Avery;;\n",
        )
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        face_id = ctl.ignoredGroups()[0]["faces"][0]["faceId"]

        assert ctl.unignoreFaces([face_id]) == 1

        faces = _ini_faces(root, "a.jpg")
        assert [face.contact_id for face in faces] == ["8e62b2035b74b477"]
        assert ctl.ignoredGroups() == []

    def test_our_own_ignore_is_not_listed_twice(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        face_id = ctl.unnamedGroups(False, False)[0]["faces"][0]["faceId"]
        assert ctl.ignoreFaces([face_id]) == 1
        from picasapy.index import open_index, sync_tree

        # a mappa MOSTANTÓL ini-s — az újraszinkron ezt az indexbe is átviszi
        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
            conn.commit()

        faces = ctl.ignoredGroups()[0]["faces"]

        assert [face["faceId"] for face in faces] == [face_id]
        assert ctl.ignoredCount() == 1


class _OverhangDetector:
    """Egy KERETEN TÚLLÓGÓ (a YuNet negatív bal szélet is adhat) és egy
    rendes arc — J1."""

    def __init__(self, available=True):
        self.available = available

    def detect(self, image):
        from picasapy.faces.detector import FaceDetection, FaceLandmarks

        landmarks = FaceLandmarks(
            right_eye=(10.0, 20.0),
            left_eye=(30.0, 20.0),
            nose=(20.0, 30.0),
            mouth_right=(15.0, 40.0),
            mouth_left=(25.0, 40.0),
        )
        return (
            FaceDetection(left=-5, top=10, right=40, bottom=50, score=0.9, landmarks=landmarks),
            FaceDetection(left=55, top=55, right=90, bottom=95, score=0.8, landmarks=landmarks),
        )


class TestOutOfFrameFaces:
    """J1: a kereten túllógó arc keretét írás előtt [0..1]-re kell vágni —
    különben az `encode_rect64` `ValueError`-t dob, és a köteg többi arca
    is kimarad."""

    def _scan(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))
        ctl, _helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=_OverhangDetector()
        )
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        ids = [f["faceId"] for f in ctl.unnamedGroups(False, False)[0]["faces"]]
        assert len(ids) == 2
        return root, ctl, ids

    def test_ignoring_clamps_the_region_into_the_frame(self, qt_app, tmp_path):
        """# rontás-kontroll: a vágás kivéve (`clamp_rect` = azonosság) →
        `ValueError: rect64 koordináta a [0..1] tartományon kívül`, a
        teszt bukik."""
        root, ctl, ids = self._scan(qt_app, tmp_path)

        assert ctl.ignoreFaces(ids) == 2

        faces = _ini_faces(root, "a.jpg")
        assert len(faces) == 2
        assert all(face.contact_id == _FFFF for face in faces)
        assert min(face.rect.left for face in faces) == 0.0

    def test_naming_clamps_the_region_too(self, qt_app, tmp_path):
        root, ctl, ids = self._scan(qt_app, tmp_path)

        assert ctl.assignNameToFaces(ids, "Roy Avery") is True

        faces = _ini_faces(root, "a.jpg")
        assert len(faces) == 2
        assert all(face.is_identified for face in faces)


class TestBaseRuleRegression:
    """(j)(4): a már névcímkés arcok hozzárendelését SEM a csoportosítás,
    SEM a tömeges névadás nem írja felül — a meglévő, ember által adott
    névcímkék soha nem értékelődnek újra."""

    def test_existing_named_face_is_untouched_by_scan_and_bulk_naming(
        self, qt_app, tmp_path
    ):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg", size=(100, 100))  # már névcímkés (Roy Avery)
        make_jpeg(root / "b.jpg", size=(100, 100))  # névtelen, ezt fogja csoportosítani/elnevezni
        contact_id = "b8e4117cf1d6615b"
        rect = "3f840000c3509f84"
        (root / ".picasa.ini").write_text(
            f"[Contacts2]\n{contact_id}=Roy Avery;;\n"
            f"[a.jpg]\nfaces=rect64({rect}),{contact_id};\n",
            encoding="utf-8",
        )
        from picasapy.app.face_scan_controller import FaceScanController
        from picasapy.app.faces_helper import FacesHelper
        from picasapy.index import open_index, sync_tree

        with open_index(tmp_path / "index.db") as conn:
            sync_tree(conn, root)
        faces_helper = FacesHelper()
        ctl = FaceScanController(
            tmp_path / "index.db",
            detector=_FakeDetector(),
            embedder=_FakeEmbedder(),
            faces_helper=faces_helper,
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        # a.jpg-t a scan ki sem hagyta — csak b.jpg-n talált arcot
        groups = ctl.unnamedGroups(False, False)
        assert len(groups) == 1
        face_ids = [face["faceId"] for face in groups[0]["faces"]]
        assert len(face_ids) == 1

        assert ctl.assignNameToFaces(face_ids, "Someone Else") is True

        from picasapy.ini import load_document, parse_faces

        document = load_document(root / ".picasa.ini")
        # Roy Avery hozzárendelése a.jpg-n VÁLTOZATLAN
        section_a = document.section("a.jpg")
        faces_a = parse_faces(section_a.get("faces"))
        assert len(faces_a) == 1
        names = {c.person_id.casefold(): c.name for c in _contacts(document)}
        assert names.get(faces_a[0].contact_id.casefold()) == "Roy Avery"
        # b.jpg megkapta az új nevet, a.jpg-t nem érintette
        section_b = document.section("b.jpg")
        faces_b = parse_faces(section_b.get("faces"))
        assert len(faces_b) == 1
        assert names.get(faces_b[0].contact_id.casefold()) == "Someone Else"


def _contacts(document):
    from picasapy.ini import contacts_of

    return contacts_of(document)


class TestScanPercent:
    """#449: a haladás az ALBUMLISTÁBAN jelenik meg — ehhez a vezérlőnek
    deklaratívan kötött százalékot kell adnia, nem csak jelzést."""

    def test_it_is_idle_before_and_after_the_scan(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(qt_app, tmp_path, root)

        assert ctl.scanPercent == -1

        arrived, _args = _run(ctl.scanFinished, ctl.scanForFaces)

        assert arrived is True
        assert ctl.waitForBackgroundWorkers(5.0)
        # a sor magától eltűnik a bal hasábból
        assert ctl.scanPercent == -1

    def test_it_reaches_a_hundred_while_scanning(self, qt_app, tmp_path):
        """#1233: a mintavétel a KIBOCSÁTÁS pillanatában történik.

        A `scanPercentChanged` paraméter nélküli jelzés, és a százalékot a
        HÁTTÉRSZÁL állítja — sorbaállított (queued) kapcsolattal a slot
        csak később, a fő szál eseményhurkában futna le, és akkor a
        property MÁR a következő (a végén: −1) értéket mutatná. Így a
        100-as érték két mintavétel közé csúszhatott: húsz futásból egy
        bukott ezen.

        `Qt.DirectConnection`-nel a slot a kibocsátó szálban, AZONNAL fut,
        tehát a lista a tényleges értéksorozatot rögzíti — időzítéstől
        függetlenül. A termék viselkedése változatlan; a hiba a mérésben
        volt, nem benne."""
        root = tmp_path / "kepek"
        root.mkdir()
        for name in ("a.jpg", "b.jpg", "c.jpg"):
            make_jpeg(root / name)
        ctl = _make_controller(qt_app, tmp_path, root)
        seen = []
        ctl.scanPercentChanged.connect(
            lambda: seen.append(ctl.scanPercent), Qt.DirectConnection
        )

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert 100 in seen, f"a 100 nem szerepel a kibocsatott sorozatban: {seen}"
        # a 100-ig monoton nő, utána már csak a lezáró −1 jöhet
        assert seen == sorted(seen[: seen.index(100) + 1]) + seen[seen.index(100) + 1 :]
        assert seen[-1] == -1, f"a lezaro -1 hianyzik: {seen}"

    def test_a_scan_that_never_starts_leaves_it_idle(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(
            qt_app, tmp_path, root, detector=_FakeDetector(available=False)
        )

        _run(ctl.modelUnavailable, ctl.scanForFaces)

        assert ctl.scanPercent == -1


class TestGlobalFaceReset4627:
    """#4627: a két módosítós ág a teljes könyvtár .ini- és indexadatait kezeli."""

    @staticmethod
    def _scanned_library(qt_app, tmp_path):
        from picasapy.index import all_photos, mark_faces_named, open_index

        root = tmp_path / "kepek"
        first = root / "album-a"
        second = root / "album-b"
        first.mkdir(parents=True)
        second.mkdir()
        paths = [first / "a.jpg", second / "b.jpg"]
        for path in paths:
            make_jpeg(path)
        detector = _FakeDetector()
        ctl, helper = _make_controller_with_faces_helper(
            qt_app, tmp_path, root, detector=detector
        )
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(detector.calls) == 2

        for index, path in enumerate(paths):
            (path.parent / ".picasa.ini").write_text(
                f"[{path.name}]\ncaption=keep-{index}\nfacedata=123\n",
                encoding="utf-8",
            )
            assert helper.addFace(
                str(path), 0.1, 0.2, 0.4, 0.6, f"Person {index}"
            )

        with open_index(tmp_path / "index.db") as conn:
            for photo in all_photos(conn):
                face_id = conn.execute(
                    "SELECT id FROM face WHERE photo_id = ?", (photo.id,)
                ).fetchone()[0]
                mark_faces_named(conn, [face_id], f"Indexed {photo.name}")
            stale_group_id = conn.execute(
                "INSERT INTO face_group (centroid, face_count) VALUES (?, 1)",
                (b"stale centroid",),
            ).lastrowid
            conn.execute(
                "UPDATE face SET group_id = ? WHERE id = "
                "(SELECT id FROM face ORDER BY id LIMIT 1)",
                (stale_group_id,),
            )
            conn.commit()
        return ctl, helper, detector, paths

    def test_ctrl_branch_removes_all_ini_and_index_face_data_then_rescans(
        self, qt_app, tmp_path
    ):
        """# rontás-kontroll: removeAllFaceData törlését kiiktatva → 1 failed"""
        from picasapy.index import all_photos, open_index
        from picasapy.ini import load_document

        ctl, _helper, detector, paths = self._scanned_library(
            qt_app, tmp_path
        )

        megvaltozott = []
        arrived, _args = _run(
            ctl.scanFinished,
            lambda: megvaltozott.append(ctl.removeAllFaceData()),
        )

        assert arrived is True
        assert megvaltozott == [2]
        assert ctl.waitForBackgroundWorkers(5.0)
        assert len(detector.calls) == 4, "minden fotót újra kell keresni"
        for index, path in enumerate(paths):
            document = load_document(path.parent / ".picasa.ini")
            section = document.section(path.name)
            assert section is None or section.get("faces") is None
            assert section is None or section.get("facedata") is None
            assert section is None or section.get("caption") == f"keep-{index}"
            contacts = document.section("Contacts2")
            assert contacts is None or contacts.items() == ()

        with open_index(tmp_path / "index.db") as conn:
            photos = all_photos(conn)
            assert len(photos) == 2
            for photo in photos:
                row = conn.execute(
                    "SELECT state, person_name FROM face WHERE photo_id = ?",
                    (photo.id,),
                ).fetchone()
                assert row is not None and row["state"] == "unnamed"
                assert row["person_name"] is None
            assert conn.execute("SELECT COUNT(*) FROM face_scan").fetchone()[0] == 2
            assert conn.execute("SELECT COUNT(*) FROM face_group").fetchone()[0] == 0

    def test_shift_branch_keeps_face_rectangles_but_removes_people(
        self, qt_app, tmp_path
    ):
        """# rontás-kontroll: resetAllFaces név-ürítését kiiktatva → 1 failed"""
        from picasapy.index import all_photos, open_index
        from picasapy.ini import load_document, parse_faces

        ctl, _helper, detector, paths = self._scanned_library(
            qt_app, tmp_path
        )

        affected = ctl.resetAllFaces()

        assert affected == 2
        assert len(detector.calls) == 2, "a Shift-ág nem kér újra-arcfelismerést"
        for path in paths:
            document = load_document(path.parent / ".picasa.ini")
            section = document.section(path.name)
            assert section is not None
            faces = parse_faces(section.get("faces") or "")
            assert len(faces) == 1
            assert faces[0].contact_id == "0"
            assert section.get("facedata") == "123"
            contacts = document.section("Contacts2")
            assert contacts is None or contacts.items() == ()

        with open_index(tmp_path / "index.db") as conn:
            photos = all_photos(conn)
            assert len(photos) == 2
            for photo in photos:
                row = conn.execute(
                    "SELECT state, person_name, suggested_name, group_id "
                    "FROM face WHERE photo_id = ?",
                    (photo.id,),
                ).fetchone()
                assert row is not None
                assert tuple(row) == ("unnamed", None, None, None)
