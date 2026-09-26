"""#2187: az arc ↔ teljes kép nagyításváltó (`face_zoom` ↔ `picture_zoom`).

Az eredeti személy-album fejlécén (`faceheaderpanel/zoom_container`) két,
egymást kizáró 35 × 21-es gomb ül; MÉRT súgóik (15.4 tábla): „View zoomed in
to the face" — **Megjelenítés az arcra közelítve**, és „View zoomed out to
the full picture" — **Megjelenítés a teljes képre távolítva**.

Nálunk a váltás a bélyegkép-URL-en át hat: arc-nagyításban a személy-album
sorai `&fz=<bal>,<fent>,<jobb>,<lent>` cimkét kapnak (relatív keret), és a
szolgáltató a kész bélyegképet erre a keretre vágja. A cimke ugyanazért
az URL része, amiért a szint és a megjelenítési mód: a Qt URL szerint
gyorstáraz.

Amit ez a fájl MÉR: a cimke képzését és visszaolvasását, a vágás
geometriáját, a modell URL-jeit, és a vezérlő keret-térképét a
megerősített (ini) és a javasolt (index) arcokra.
Amit NEM mér: a fejléc gombjait (a QML-funkcionális próba dolga).
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, QSettings
from PySide6.QtGui import QColor, QImage

from picasapy.faces.detector import FaceDetection, FaceLandmarks
from support.jpeg_factory import make_jpeg

_ROY = "b8e4117cf1d6615b"
#: rect64 → (0,25 ; 0,25 ; 0,75 ; 0,75)
_RECT = "40004000c000c000"
_LANDMARKS = FaceLandmarks(
    right_eye=(10.0, 20.0),
    left_eye=(30.0, 20.0),
    nose=(20.0, 30.0),
    mouth_right=(15.0, 40.0),
    mouth_left=(25.0, 40.0),
)


# -- az URL-cimke ------------------------------------------------------------


class TestCimke:
    def test_cimke_es_visszaolvasas(self):
        from picasapy.app.arc_nagyitas_url import arc_cimke, arc_from_thumb_id

        cimke = arc_cimke((0.1, 0.2, 0.3, 0.4))
        assert cimke.startswith("&fz=")
        kulcs = "12?r=0" + cimke
        assert arc_from_thumb_id(kulcs) == pytest.approx((0.1, 0.2, 0.3, 0.4))

    def test_cimke_nelkul_none(self):
        from picasapy.app.arc_nagyitas_url import arc_from_thumb_id

        assert arc_from_thumb_id("12?r=0&m=1") is None
        assert arc_from_thumb_id("") is None

    @pytest.mark.parametrize(
        "ertek", ["x", "0.1,0.2,0.3", "0.5,0.5,0.4,0.9", "0.1,0.2,0.3,nan"]
    )
    def test_hibas_cimke_none(self, ertek):
        """Rossz cimkéből sosem lehet rossz vágás: a teljes kép a tartalék."""
        from picasapy.app.arc_nagyitas_url import arc_from_thumb_id

        assert arc_from_thumb_id(f"12?r=0&fz={ertek}") is None


# -- a vágás -----------------------------------------------------------------


def _kep(szel=200, mag=100):
    kep = QImage(szel, mag, QImage.Format.Format_RGB32)
    kep.fill(QColor("white"))
    return kep


class TestVagas:
    def test_negyzet_az_arc_kozeppontja_korul(self):
        from picasapy.app.arc_nagyitas_url import arcra_vag

        # arc: 20 × 20 képpont a (100,50) középpont körül
        vagott = arcra_vag(_kep(), (0.45, 0.4, 0.55, 0.6))
        assert vagott.width() == vagott.height()
        assert vagott.width() > 20  # környezet is kerül a keretbe
        assert vagott.width() < 100

    def test_a_kepbol_nem_log_ki(self):
        from picasapy.app.arc_nagyitas_url import arcra_vag

        vagott = arcra_vag(_kep(), (0.0, 0.0, 0.3, 0.9))
        assert vagott.width() <= 100 and vagott.height() <= 100

    def test_ures_kepre_valtozatlan(self):
        from picasapy.app.arc_nagyitas_url import arcra_vag

        assert arcra_vag(QImage(), (0.1, 0.1, 0.2, 0.2)).isNull()


# -- a modell ----------------------------------------------------------------


def _rekord(photo_id: int, nev: str):
    from picasapy.index import PhotoRecord

    return PhotoRecord(
        id=photo_id, folder_path="/x", name=nev, kind="photo", size=1,
        mtime_ns=1, star=False, caption=None, keywords=None, rotate_steps=0,
        filters=None, taken_at=None, orientation=1, width=None, height=None,
    )


@pytest.fixture
def modell(qt_app):
    from picasapy.app.models import PhotoGridModel

    m = PhotoGridModel()
    m.set_photos((_rekord(1, "a.jpg"), _rekord(2, "b.jpg")))
    return m


class TestModell:
    def test_alapbol_nincs_cimke(self, modell):
        assert "&fz=" not in modell.itemAt(0)["thumbUrl"]

    def test_bekapcsolva_a_kert_sor_kapja(self, modell):
        modell.set_face_zoom({1: (0.1, 0.2, 0.3, 0.4)})
        assert "&fz=" in modell.itemAt(0)["thumbUrl"]
        assert "&fz=" in modell.thumbUrlAt(0)
        # keret nélküli sor a teljes képet mutatja
        assert "&fz=" not in modell.itemAt(1)["thumbUrl"]

    def test_a_valtas_lepteti_a_reviziot(self, modell):
        elotte = modell.revision
        modell.set_face_zoom({1: (0.1, 0.2, 0.3, 0.4)})
        assert modell.revision > elotte

    def test_uj_tartalom_torli(self, modell):
        """Más nézetre váltva (új sorok) a vágás nem öröklődhet."""
        modell.set_face_zoom({1: (0.1, 0.2, 0.3, 0.4)})
        modell.set_photos((_rekord(1, "a.jpg"),))
        assert "&fz=" not in modell.itemAt(0)["thumbUrl"]


# -- a szolgáltató -----------------------------------------------------------


class TestSzolgaltato:
    def test_a_cimkes_keres_vagott_kepet_ad(self, qt_app, tmp_path):
        from picasapy.app.thumbnail_provider import ThumbnailProvider
        from picasapy.index import PhotoRecord
        from picasapy.thumbs import ThumbnailCache

        make_jpeg(tmp_path / "a.jpg", size=(400, 200))
        stat = (tmp_path / "a.jpg").stat()
        rekord = PhotoRecord(
            id=7, folder_path=str(tmp_path), name="a.jpg", kind="photo",
            size=stat.st_size, mtime_ns=stat.st_mtime_ns, star=False,
            caption=None, keywords=None, rotate_steps=0, filters=None,
            taken_at=None, orientation=1, width=400, height=200,
        )
        provider = ThumbnailProvider(ThumbnailCache(tmp_path / "cache"))
        provider.register_photos((rekord,))
        teljes = provider.requestImage("7?r=0", None, None)
        vagott = provider.requestImage(
            "7?r=0&fz=0.45,0.4,0.55,0.6", None, None
        )
        assert vagott.width() == vagott.height()
        assert vagott.width() < teljes.width()


# -- a vezérlő ---------------------------------------------------------------


@pytest.fixture
def library(tmp_path):
    """`a.jpg`: Roy MEGERŐSÍTVE (ini). `b.jpg`: Royra JAVASOLVA (face tábla)."""
    root = tmp_path / "kepek"
    root.mkdir()
    for nev in ("a.jpg", "b.jpg"):
        make_jpeg(root / nev)
    (root / ".picasa.ini").write_text(
        f"[Contacts2]\n{_ROY}=Roy Avery;;\n"
        f"[a.jpg]\nfaces=rect64({_RECT}),{_ROY};\n",
        encoding="utf-8",
    )
    return root


class _Modell:
    def __init__(self):
        self.teglalapok = "nem hívták"

    def set_face_zoom(self, teglalapok):
        self.teglalapok = teglalapok


@pytest.fixture
def host(qt_app, tmp_path, library):
    from picasapy.app.people_controller import PeopleMixin
    from picasapy.index import open_index, replace_faces, sync_tree
    from picasapy.index.faces_detected import set_suggested_name

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
        foto = conn.execute(
            "SELECT id FROM photos WHERE name = 'b.jpg'"
        ).fetchone()["id"]
        replace_faces(conn, foto, [FaceDetection(
            left=5.0, top=10.0, right=40.0, bottom=50.0, score=0.9,
            landmarks=_LANDMARKS)])
        arc = conn.execute(
            "SELECT id FROM face WHERE photo_id = ?", (foto,)
        ).fetchone()
        set_suggested_name(conn, arc["id"], "Roy Avery")
        conn.commit()

    class _Host(PeopleMixin, QObject):
        def __init__(self, db_path):
            super().__init__()
            self._db_path = db_path
            self._view_mode = ("folder", "")
            self._filter_active = False
            self._filter_status = ""
            self._shown: tuple = ()
            self._photos = _Modell()
            self._init_people()

        def _show(self, records):
            self._shown = records

        def _get_settings(self):
            if getattr(self, "_beallitasok", None) is None:
                self._beallitasok = QSettings(
                    str(Path(self._db_path).parent / "settings.ini"),
                    QSettings.Format.IniFormat,
                )
            return self._beallitasok

    return _Host(tmp_path / "index.db")


def _id(host, nev):
    return next(r.id for r in host._shown if r.name == nev)


class TestVezerlo:
    def test_alapbol_a_teljes_kep(self, host):
        """Alapállapot: a mai viselkedés (teljes kép) — nincs vágás."""
        assert host.personFaceZoom is False
        host.showPerson("Roy Avery")
        assert host._photos.teglalapok is None

    def test_bekapcsolva_a_megerositett_arc_kerete(self, host):
        host.showPerson("Roy Avery")
        host.setPersonFaceZoom(True)
        teglalapok = host._photos.teglalapok
        assert teglalapok[_id(host, "a.jpg")] == pytest.approx(
            (0.25, 0.25, 0.75, 0.75), abs=1e-3
        )

    def test_bekapcsolva_a_javasolt_arc_kerete(self, host):
        host.showPerson("Roy Avery")
        host.setPersonFaceZoom(True)
        assert _id(host, "b.jpg") in host._photos.teglalapok

    def test_visszakapcsolva_a_teljes_kep(self, host):
        host.showPerson("Roy Avery")
        host.setPersonFaceZoom(True)
        host.setPersonFaceZoom(False)
        assert host._photos.teglalapok is None
        assert host.personFaceZoom is False

    def test_szemely_album_nelkul_nem_hat(self, host):
        host.setPersonFaceZoom(True)
        assert host.personFaceZoom is False
        assert host._photos.teglalapok == "nem hívták"

    def test_a_kovetkezo_szemelynel_is_megmarad(self, host):
        """A váltó a nézet beállítása, nem az albumé: a következő
        személy-album is arcra nagyítva nyílik."""
        host.showPerson("Roy Avery")
        host.setPersonFaceZoom(True)
        host.showPerson("Roy Avery")
        assert host.personFaceZoom is True
        assert isinstance(host._photos.teglalapok, dict)

    def test_a_szuro_valtasa_utan_is_vag(self, host):
        host.showPerson("Roy Avery")
        host.setPersonFaceZoom(True)
        host.setPersonSuggestionsOnly(True)
        assert _id(host, "b.jpg") in host._photos.teglalapok

    def test_a_valto_jelez(self, host, qt_app):
        host.showPerson("Roy Avery")
        latott = []
        host.personViewChanged.connect(lambda: latott.append(1))
        host.setPersonFaceZoom(True)
        assert latott
