"""#1401: `PassportPhotoController` — arcfelismerés a kijelölt képen, majd
a `picasapy.faces.passport` négyzet-kivágása, HÁTTÉRSZÁLON.

Hamis (`_FakeDetector`) arc-detektorral, hogy a valódi YuNet-modell nélkül
(CI) is fedhető legyen a körülötte lévő vezérlő-logika: az érvénytelen sor,
a nulla/több arc, az olvasási és írási hiba, a csökkentett felbontású
keresés visszaskálázása, a forgatás, és a pontosan egy arc → kivágás →
`passportReady` ág."""

from __future__ import annotations

import os

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")

from dataclasses import dataclass
from pathlib import Path

import numpy as np
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
    rotate_steps: int = 0


_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


def _arc(left, top, right, bottom) -> FaceDetection:
    return FaceDetection(
        left=left, top=top, right=right, bottom=bottom, score=0.9,
        landmarks=_LANDMARKS,
    )


class _FakeDetector:
    """A `FaceDetector` felületét másoló teszt-dupla — a megadott (kész)
    találatokat adja vissza, és megjegyzi, milyen képet kapott."""

    def __init__(self, faces: tuple[FaceDetection, ...] = ()):
        self.available = True
        self.faces = faces
        self.shapes: list[tuple[int, ...]] = []

    def detect(self, image):
        self.shapes.append(tuple(image.shape))
        return self.faces


class _Esemenyek:
    def __init__(self, ctl: PassportPhotoController):
        self.lista: list[tuple[str, object]] = []
        ctl.passportNoFace.connect(lambda: self.lista.append(("no_face", None)))
        ctl.passportMultipleFaces.connect(
            lambda: self.lista.append(("multi", None))
        )
        ctl.passportFailed.connect(lambda k: self.lista.append(("failed", k)))
        ctl.passportReady.connect(lambda u: self.lista.append(("ready", u)))


def _futtat(ctl: PassportPhotoController, row: int) -> None:
    app = qt_app()
    ctl.preparePassportPhoto(row)
    assert ctl.waitForBackgroundWorkers(20.0)
    app.processEvents()


def _controller(photos, detector, cache_dir):
    qt_app()
    return PassportPhotoController(
        photo_source=lambda: photos, detector=detector, cache_dir=cache_dir
    )


class TestErvenytelenSor:
    def test_tartomanyon_kivuli_sor_nem_indit_semmit(self, tmp_path):
        detektor = _FakeDetector()
        ctl = _controller([], detektor, tmp_path / "gyorstar")
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert esemenyek.lista == []
        assert detektor.shapes == []

    def test_negativ_sor_nem_indit_semmit(self, tmp_path):
        detektor = _FakeDetector()
        ctl = _controller(
            [_FakePhoto(str(tmp_path), "a.jpg")], detektor, tmp_path / "gy"
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, -1)
        assert esemenyek.lista == []


class TestOlvasasiEsIrasiHiba:
    def test_hianyzo_fajl_olvasasi_hibat_ad_nem_nincs_arcot(self, tmp_path):
        photo = _FakePhoto(str(tmp_path), "nincs-ilyen.jpg")
        ctl = _controller([photo], _FakeDetector(), tmp_path / "gy")
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert esemenyek.lista == [("failed", "read")]

    def test_irhatatlan_gyorstar_irasi_hibat_ad_nem_nincs_arcot(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        # a gyorstár helyén egy FÁJL áll — a mappa nem hozható létre
        akadaly = tmp_path / "gyorstar"
        akadaly.write_bytes(b"x")
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)],
            _FakeDetector(faces=(_arc(50, 50, 100, 100),)),
            akadaly,
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert esemenyek.lista == [("failed", "write")]


class TestArcSzamDontesiFa:
    def test_nulla_arc_no_face_jelzest_ad(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)],
            _FakeDetector(faces=()),
            tmp_path / "gy",
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert esemenyek.lista == [("no_face", None)]

    def test_ket_arc_multiple_faces_jelzest_ad(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)],
            _FakeDetector(faces=(_arc(10, 10, 40, 50), _arc(100, 100, 140, 150))),
            tmp_path / "gy",
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert esemenyek.lista == [("multi", None)]

    def test_egy_arc_ready_jelzest_ad_a_kivagott_fajllal(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        gyorstar = tmp_path / "gy"
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)],
            _FakeDetector(faces=(_arc(50, 50, 100, 100),)),
            gyorstar,
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert [e[0] for e in esemenyek.lista] == ["ready"]
        url = QUrl(esemenyek.lista[0][1])
        assert url.isLocalFile()
        cropped_path = url.toLocalFile()
        # a kivágás a MEGADOTT gyorstárba kerül, nem a felhasználói ~/.cache-be
        assert Path(cropped_path).parent == gyorstar
        vart = passport_crop_rect(50, 50, 100, 100, 200, 200)
        with Image.open(cropped_path) as kep:
            assert kep.size == (vart.width, vart.height)

    def test_a_kep_maga_nem_modosul(self, tmp_path):
        source = make_jpeg(tmp_path / "kep.jpg", size=(200, 200))
        eredeti_bajtok = source.read_bytes()
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)],
            _FakeDetector(faces=(_arc(50, 50, 100, 100),)),
            tmp_path / "gy",
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert [e[0] for e in esemenyek.lista] == ["ready"]
        assert source.read_bytes() == eredeti_bajtok


class TestCsokkentettFelbontasuKereses:
    """A keresés a `_DETECT_MAX_DIMENSION` (960) szerint csökkentett képen
    fut, a kivágás viszont a TELJES felbontású képből készül. (A JPEG-
    dekóder csak kellő ráhagyásnál csökkent, ezért kell a 4000 képpontos
    próbakép.)"""

    def test_a_detektor_csokkentett_kepet_kap(self, tmp_path):
        source = make_jpeg(tmp_path / "nagy.jpg", size=(4000, 2600))
        detektor = _FakeDetector(faces=())
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)], detektor, tmp_path / "gy"
        )
        _futtat(ctl, 0)
        assert len(detektor.shapes) == 1
        magas, szeles = detektor.shapes[0][:2]
        assert max(magas, szeles) < 4000

    def test_a_keret_visszaskalazva_a_teljes_kepbol_vag(self, tmp_path):
        source = make_jpeg(tmp_path / "nagy.jpg", size=(4000, 2600))
        detektor = _FakeDetector()

        # a detektor a KAPOTT kép méretéhez viszonyítva ad arcot: a
        # szélesség/magasság 40–60 %-a
        def _detect(image):
            detektor.shapes.append(tuple(image.shape))
            m, s = image.shape[:2]
            return (_arc(0.4 * s, 0.4 * m, 0.6 * s, 0.6 * m),)

        detektor.detect = _detect
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name)], detektor, tmp_path / "gy"
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert [e[0] for e in esemenyek.lista] == ["ready"]
        vart = passport_crop_rect(1600, 1040, 2400, 1560, 4000, 2600)
        with Image.open(QUrl(esemenyek.lista[0][1]).toLocalFile()) as kep:
            szeles, magas = kep.size
        assert abs(szeles - vart.width) <= 3
        assert abs(magas - vart.height) <= 3


class TestForgatas:
    """A Picasa `rotate_steps`-e a keresés és a kivágás ELŐTT érvényesül."""

    def test_negyedfordulatnal_a_detektor_elforgatott_kepet_kap(self, tmp_path):
        source = make_jpeg(tmp_path / "fekvo.jpg", size=(300, 200))
        detektor = _FakeDetector(faces=())
        ctl = _controller(
            [_FakePhoto(str(tmp_path), source.name, rotate_steps=1)],
            detektor,
            tmp_path / "gy",
        )
        _futtat(ctl, 0)
        magas, szeles = detektor.shapes[0][:2]
        assert (szeles, magas) == (200, 300)

    def test_a_kivagas_az_elforgatott_kepbol_keszul(self, tmp_path):
        # bal fele fekete, jobb fele fehér — az óramutató járásával
        # megegyező negyedfordulat után a FELSŐ fele fekete, az alsó fehér
        kep = np.zeros((200, 300, 3), dtype=np.uint8)
        kep[:, 150:] = 255
        Image.fromarray(kep).save(tmp_path / "felek.png")
        ctl = _controller(
            [_FakePhoto(str(tmp_path), "felek.png", rotate_steps=1)],
            _FakeDetector(faces=(_arc(80, 120, 120, 160),)),
            tmp_path / "gy",
        )
        esemenyek = _Esemenyek(ctl)
        _futtat(ctl, 0)
        assert [e[0] for e in esemenyek.lista] == ["ready"]
        vart = passport_crop_rect(80, 120, 120, 160, 200, 300)
        with Image.open(QUrl(esemenyek.lista[0][1]).toLocalFile()) as ki:
            assert ki.size == (vart.width, vart.height)
            szurke = np.asarray(ki.convert("L"))
        hatar = 150 - vart.top
        assert szurke[: hatar - 2].mean() < 10
        assert szurke[hatar + 2 :].mean() > 245
