"""A forgatás két JELZŐ ága — #1755.

Az eredeti Picasa a forgatásnál két esetben megszólal, mi mindkettőben
némák voltunk:

* **vegyes kijelölés** (fotó + videó): `IDS_ROT_TYPEFAILED` — „One or more
  images could not be rotated because of the file type." A videókat a #103
  óta hallgatólagosan kihagyjuk; a felhasználó csak annyit látott, hogy nem
  forgott el minden, magyarázat nélkül.
* **nincs kijelölés**: `IDS_MUST_SELECT_TO_ROT` — „Must have selected
  images to rotate." Nálunk néma visszatérés volt.

Mindkét szöveg HIVATALOS erőforrás; a magyar is a szövegtárból való
(`stringres`), nem a mi fogalmazásunk — ezt a `TestAFeliratok` állítja.

A vezérlő csak a TÉNYT jelenti, a szöveg a felületen él
(`PicasaNotifier.qml`) — a `saveCopyReady` mintája szerint.
"""

from __future__ import annotations

from pathlib import Path

import picasapy.app
import pytest
from support.jpeg_factory import make_jpeg

_NOTIFIER = (
    Path(picasapy.app.__file__).parent
    / "qml" / "PicasaPy" / "PicasaNotifier.qml"
).read_text(encoding="utf-8")
_TS = (
    Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.ts"
).read_text(encoding="utf-8")

#: A két hivatalos erőforrás — angol forrás és a szövegtárból vett magyar.
HIVATALOS = {
    "One or more images could not be rotated because of the file type.":
        "Egy vagy több képet nem lehetett elforgatni a fájltípus miatt.",
    "Must have selected images to rotate.":
        "Ki kell jelölnie képeket a forgatáshoz.",
}


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg")
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg")
    return root


@pytest.fixture
def controller(qt_app, tmp_path, library):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache
    from PySide6.QtCore import QSettings

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(
        str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
    )
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl._reload()
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _videoval(controller, library) -> int:
    """Egy videó a mappába, majd a SORA — a `test_controller` mintája."""
    from picasapy.index import open_index, sync_tree

    (library / "nyaralas" / "film.mp4").write_bytes(b"\x00" * 32)
    with open_index(controller._db_path) as conn:
        sync_tree(conn, library)
    controller.selectFolder(str(library / "nyaralas"))
    return next(
        i
        for i, photo in enumerate(controller.photos.photos)
        if photo.name == "film.mp4"
    )


class TestAJelzesek:
    def test_vegyes_kijeloles_JELZI_a_kihagyottakat(self, controller, library):
        """A lelet magja: fotó + videó együtt — a videó kimarad, és ezt
        MEGMONDJUK."""
        video_row = _videoval(controller, library)
        photo_rows = [
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.kind == "photo"
        ]
        kaptunk: list[int] = []
        controller.rotationTypeFailed.connect(kaptunk.append)

        controller.rotateRightMany([*photo_rows, video_row])

        assert kaptunk == [1], "a kihagyott videóról nem jött jelzés"
        # A forgatás maga VÁLTOZATLAN: a fotók elfordultak.
        for row in photo_rows:
            assert controller.photos.photos[row].rotate_steps == 1

    def test_csak_fotok_eseten_NINCS_jelzes(self, controller, library):
        """A jelzés nem lehet zajos: ha nincs kihagyott elem, hallgat."""
        photo_rows = [
            i
            for i, photo in enumerate(controller.photos.photos)
            if photo.kind == "photo"
        ]
        kaptunk: list[int] = []
        controller.rotationTypeFailed.connect(kaptunk.append)

        controller.rotateRightMany(photo_rows)

        assert kaptunk == []

    def test_ures_kijeloles_a_MASIK_jelzest_adja(self, controller):
        """Üres kijelölés nem „típushiba" — saját erőforrása van."""
        tipus: list[int] = []
        kijeloles: list[int] = []
        controller.rotationTypeFailed.connect(tipus.append)
        controller.rotationNeedsSelection.connect(
            lambda: kijeloles.append(1)
        )

        controller.rotateRightMany([])

        assert kijeloles == [1]
        assert tipus == []

    def test_csak_videot_tartalmazo_kijeloles_TIPUSHIBA(
        self, controller, library
    ):
        """Nem üres kijelölés — csak épp egyik elem sem forgatható."""
        video_row = _videoval(controller, library)
        tipus: list[int] = []
        kijeloles: list[int] = []
        controller.rotationTypeFailed.connect(tipus.append)
        controller.rotationNeedsSelection.connect(
            lambda: kijeloles.append(1)
        )

        controller.rotateLeftMany([video_row])

        assert tipus == [1]
        assert kijeloles == [], "a videó-kijelölés nem »nincs kijelölés«"


class TestAFelulet:
    def test_a_notifier_MINDKET_jelzest_felveszi(self):
        assert "function onRotationTypeFailed(" in _NOTIFIER
        assert "function onRotationNeedsSelection(" in _NOTIFIER

    def test_nulla_kihagyottra_a_notifier_HALLGAT(self):
        """A vezérlő ugyan csak pozitív számmal emitál, de a felület se
        villantson fel semmit nullára — a #1168 őre ugyanezt méri az
        üres útvonalra."""
        kezd = _NOTIFIER.index("function onRotationTypeFailed(")
        assert "if (skipped <= 0)" in _NOTIFIER[kezd : kezd + 260]


class TestAFeliratok:
    def test_a_ket_szoveg_HIVATALOS_forrasa_a_felulete(self):
        for angol in HIVATALOS:
            assert f'qsTr("{angol}")' in _NOTIFIER, angol

    def test_a_magyar_a_SZOVEGTARBOL_valo(self):
        for angol, magyar in HIVATALOS.items():
            assert f"<source>{angol}</source>" in _TS
            assert f"<translation>{magyar}</translation>" in _TS
