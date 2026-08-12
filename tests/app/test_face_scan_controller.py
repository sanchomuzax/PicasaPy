"""#26 (1. lépcső): `FaceScanController` — a saját arc-detektálás
háttérfolyamata és a „Névtelenek" album.

A HÁLÓZATOT/modellt igénylő valódi YuNet-detektálás helyett egy hamis
detektor van injektálva (a `FaceDetector` konstruktora ELVÁRJA a modellt —
ez a teszt a KÖRÜLÖTTE lévő vezérlő-logikát nézi: kihagyás névcímkés
fotónál, a „Névtelenek" album feltöltése, `modelUnavailable` valódi modell
nélkül). Önálló, host nélküli teszt — a `DedupController`/`PeopleMixin`
mintáját követi (a `controller.py`-beli bekötés az integrátor dolga)."""

from __future__ import annotations

from PySide6.QtCore import QEventLoop, QTimer

from support.jpeg_factory import make_jpeg


def _run(signal, action, timeout_ms=10000):
    """A `test_create_controller.py` mintája: feliratkozás ELŐBB, hívás UTÁNA."""
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


def _make_controller(qt_app, tmp_path, library, detector=None, embedder=None):
    from picasapy.app.face_scan_controller import FaceScanController
    from picasapy.index import open_index, sync_tree

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    ctl = FaceScanController(
        tmp_path / "index.db",
        detector=detector if detector is not None else _FakeDetector(),
        embedder=embedder if embedder is not None else _FakeEmbedder(),
    )
    return ctl


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
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(qt_app, tmp_path, root)
        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)
        arrived, args = _run(ctl.scanFinished, ctl.scanForFaces)
        assert arrived is True
        found, scanned = args
        assert found == 1  # nem duplázódott
        assert ctl.waitForBackgroundWorkers(5.0)


class TestComputeEmbeddings:
    """#26 (2. lépcső): a lenyomat-számítás + csoportosítás KÜLÖN,
    alacsonyabb prioritású sora — a detektálás UTÁN, önállóan indítható."""

    def test_embedding_model_unavailable_does_not_start_a_worker(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(
            qt_app, tmp_path, root, embedder=_FakeEmbedder(available=False)
        )
        assert ctl.isEmbeddingAvailable() is False
        arrived, _args = _run(ctl.embeddingModelUnavailable, ctl.computeEmbeddings)
        assert arrived is True
        assert ctl.waitForBackgroundWorkers(5.0)

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
        root = tmp_path / "kepek"
        root.mkdir()
        for name in ("a.jpg", "b.jpg", "c.jpg"):
            make_jpeg(root / name)
        ctl = _make_controller(qt_app, tmp_path, root)
        seen = []
        ctl.scanPercentChanged.connect(lambda: seen.append(ctl.scanPercent))

        _run(ctl.scanFinished, ctl.scanForFaces)
        assert ctl.waitForBackgroundWorkers(5.0)

        assert 100 in seen
        assert seen == sorted(seen[: seen.index(100) + 1]) + seen[seen.index(100) + 1 :]

    def test_a_scan_that_never_starts_leaves_it_idle(self, qt_app, tmp_path):
        root = tmp_path / "kepek"
        root.mkdir()
        make_jpeg(root / "a.jpg")
        ctl = _make_controller(
            qt_app, tmp_path, root, detector=_FakeDetector(available=False)
        )

        _run(ctl.modelUnavailable, ctl.scanForFaces)

        assert ctl.scanPercent == -1
