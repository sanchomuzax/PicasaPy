"""#1401: `PassportPhotoController` — arcfelismerés a kijelölt képen, majd
a `picasapy.faces.passport` négyzet-kivágása.

Hamis (`_FakeDetector`) arc-detektorral, hogy a valódi YuNet-modell nélkül
(CI) is fedhető legyen a KÖRÜLÖTTE lévő vezérlő-logika: az érvénytelen sor,
a nulla/több arc, és a pontosan egy arc → kivágás → `passportReady` ág."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import dataclass

from PIL import Image
from PySide6.QtCore import QUrl
from PySide6.QtGui import QGuiApplication

from picasapy.app.passport_controller import PassportPhotoController
from picasapy.faces.detector import FaceDetection, FaceLandmarks
from picasapy.faces.passport import passport_crop_rect

from support.jpeg_factory import make_jpeg


def qt_app():
    return QGuiApplication.instance() or QGuiApplication([])


@dataclass
class _FakePhoto:
    folder_path: str
    name: str


_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


class _FakeDetector:
    """A `FaceDetector` felületét másoló teszt-dupla — a `faces` konstruktor-
    argumentumban megadott (kész) találatokat adja vissza, hívásonként."""

    def __init__(self, faces: tuple[FaceDetection, ...] = ()):
        self.available = True
        self.faces = faces
        self.calls: list = []

    def detect(self, image):
        self.calls.append(image)
        return self.faces


def _controller(photos, detector):
    qt_app()
    return PassportPhotoController(photo_source=lambda: photos, detector=detector)


class TestErvenytelenSor:
    def test_tartomanyon_kivuli_sor_nincs_arc_jelzest_ad(self):
        ctl = _controller([], _FakeDetector())
        events = []
        ctl.passportNoFace.connect(lambda: events.append("no_face"))
        ctl.preparePassportPhoto(0)
        assert events == ["no_face"]

    def test_negativ_sor_nincs_arc_jelzest_ad(self):
        ctl = _controller([_FakePhoto("/tmp", "a.jpg")], _FakeDetector())
        events = []
        ctl.passportNoFace.connect(lambda: events.append("no_face"))
        ctl.preparePassportPhoto(-1)
        assert events == ["no_face"]


class TestOlvashatatlanKep:
    def test_hianyzo_fajl_nincs_arc_jelzest_ad(self, tmp_path):
        photo = _FakePhoto(str(tmp_path), "nincs-ilyen.jpg")
        ctl = _controller([photo], _FakeDetector())
        events = []
        ctl.passportNoFace.connect(lambda: events.append("no_face"))
        ctl.preparePassportPhoto(0)
        assert events == ["no_face"]


class TestArcSzamDontesiFa:
    def test_nulla_arc_no_face_jelzest_ad(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        photo = _FakePhoto(str(tmp_path), source.name)
        ctl = _controller([photo], _FakeDetector(faces=()))
        events = []
        ctl.passportNoFace.connect(lambda: events.append("no_face"))
        ctl.preparePassportPhoto(0)
        assert events == ["no_face"]

    def test_ket_arc_multiple_faces_jelzest_ad(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        photo = _FakePhoto(str(tmp_path), source.name)
        ket_arc = (
            FaceDetection(left=10, top=10, right=40, bottom=50, score=0.9, landmarks=_LANDMARKS),
            FaceDetection(left=100, top=100, right=140, bottom=150, score=0.9, landmarks=_LANDMARKS),
        )
        ctl = _controller([photo], _FakeDetector(faces=ket_arc))
        events = []
        ctl.passportMultipleFaces.connect(lambda: events.append("multi"))
        ctl.preparePassportPhoto(0)
        assert events == ["multi"]

    def test_egy_arc_ready_jelzest_ad_a_kivagott_fajllal(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        photo = _FakePhoto(str(tmp_path), source.name)
        egy_arc = (
            FaceDetection(
                left=50, top=50, right=100, bottom=100, score=0.9,
                landmarks=_LANDMARKS,
            ),
        )
        ctl = _controller([photo], _FakeDetector(faces=egy_arc))
        events = []
        ctl.passportReady.connect(events.append)
        ctl.preparePassportPhoto(0)
        assert len(events) == 1
        url = QUrl(events[0])
        assert url.isLocalFile()
        cropped_path = url.toLocalFile()
        assert os.path.exists(cropped_path)

        # a kivágás mérete pontosan a képlet szerinti téglalap
        vart = passport_crop_rect(50, 50, 100, 100, 200, 200)
        with Image.open(cropped_path) as kep:
            assert kep.size == (vart.width, vart.height)

    def test_a_kep_maga_nem_modosul(self, tmp_path):
        """A jegy negyedik feltétele: „a kép maga nem módosul" — a
        kivágás egy MÁSIK, ideiglenes fájlba kerül, az eredeti fájl
        bájtjai érintetlenek."""
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        eredeti_bajtok = source.read_bytes()
        photo = _FakePhoto(str(tmp_path), source.name)
        egy_arc = (
            FaceDetection(
                left=50, top=50, right=100, bottom=100, score=0.9,
                landmarks=_LANDMARKS,
            ),
        )
        ctl = _controller([photo], _FakeDetector(faces=egy_arc))
        events = []
        ctl.passportReady.connect(events.append)
        ctl.preparePassportPhoto(0)
        assert len(events) == 1
        assert source.read_bytes() == eredeti_bajtok
        cropped_path = QUrl(events[0]).toLocalFile()
        assert os.path.abspath(cropped_path) != os.path.abspath(str(source))
