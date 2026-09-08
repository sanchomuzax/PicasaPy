"""A mappa arcfelismerés-kizárása MEGJELÖLI a fotóit (#2519).

Az eredeti Picasa a Mappakezelő kizárás-kapcsolójakor a képekre teszi ki a
saját jelzőjét (`facerect = 1`; `CFolderMgrDialog` → `FUN_005cef20` →
`FUN_00491210` → `FUN_00446960`, `0x00491627`), és mivel a téglalap írója
csak NULLA értékre ír, ez **megvédi a képeket az újra-detektálástól**. A
megerősítő kérdés („Biztosan eltávolítja az összes arcot és névcímkét a
kihagyott mappákból?") tehát nem csak töröl, hanem tartósan jelöl is.

⚠️ **Amit szándékosan NEM veszünk át:** a `.picasa.ini` `faces=` /
`[Contacts2]` sorait NEM töröljük. Az a felhasználó SAJÁT, a Picasában
felvett adata (a round-trip alapszabálya: „a Picasa döntései szentek"), és
egy visszavonhatatlan törlés nem fér bele egy kizárás-kapcsolóba. A mi
származtatott találatainkat (`face` tábla) viszont töröljük — azok
bármikor újraszámolhatók.
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def controller(qt_app, tmp_path):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    lib = tmp_path / "kepek"
    lib.mkdir()
    make_jpeg(lib / "a.jpg")
    alfa = lib / "2011"
    alfa.mkdir()
    make_jpeg(alfa / "b.jpg")
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, lib)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(lib),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
        exclude_file=tmp_path / "FRExcludeFolders.txt",
    )
    ctl._reload()
    yield ctl, lib, tmp_path
    assert ctl.waitForBackgroundWorkers(30.0)


def _sorok(tmp_path, tabla: str) -> int:
    from picasapy.index import open_index

    with open_index(tmp_path / "index.db") as conn:
        return int(conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0])


def _arcot_ir(tmp_path) -> None:
    """Egy származtatott arc-találat minden fotóra — ezt kell törölnie a
    kizárásnak."""
    from picasapy.faces.detector import FaceDetection, FaceLandmarks
    from picasapy.index import open_index, replace_faces

    jelek = FaceLandmarks(
        right_eye=(10.0, 20.0),
        left_eye=(30.0, 20.0),
        nose=(20.0, 30.0),
        mouth_right=(15.0, 40.0),
        mouth_left=(25.0, 40.0),
    )
    talalat = FaceDetection(left=5, top=10, right=40, bottom=50, score=0.9, landmarks=jelek)
    with open_index(tmp_path / "index.db") as conn:
        for (azonosito,) in conn.execute("SELECT id FROM photos").fetchall():
            replace_faces(conn, azonosito, (talalat,))
        conn.commit()


class TestKizarasJeloles:
    def test_a_kizaras_megjeloli_a_mappa_es_az_ALFAI_fotoit(self, controller):
        ctl, lib, tmp_path = controller
        from picasapy.index import open_index
        from picasapy.index.faces_detected import OK_KIZARVA, face_scan_done

        ctl.setFaceDetectionEnabled(str(lib), False)

        with open_index(tmp_path / "index.db") as conn:
            sorok = conn.execute("SELECT photo_id, ok FROM face_scan").fetchall()
            azonositok = [
                sor[0] for sor in conn.execute("SELECT id FROM photos").fetchall()
            ]
            for azonosito in azonositok:
                assert face_scan_done(conn, azonosito, mtime_ns=0, size=0), (
                    f"a(z) {azonosito}. fotó nem kapott jelölést — a kizárt "
                    f"mappa képei a következő szkennelésnél újra végigfutnának"
                )
        assert len(sorok) == 2, "az alfa fotója is jelölendő"
        assert {sor[1] for sor in sorok} == {OK_KIZARVA}

    def test_a_kizaras_torli_a_SAJAT_talalatainkat(self, controller):
        ctl, lib, tmp_path = controller
        _arcot_ir(tmp_path)
        assert _sorok(tmp_path, "face") == 2

        ctl.setFaceDetectionEnabled(str(lib), False)

        assert _sorok(tmp_path, "face") == 0, (
            "a megerősítő kérdés az arcok eltávolítását ígéri — a "
            "származtatott találatainknak el kell tűnniük"
        )

    def test_a_picasa_ini_ERINTETLEN_marad(self, controller):
        """A felhasználó SAJÁT, Picasában felvett adatát nem töröljük."""
        ctl, lib, tmp_path = controller
        ini = lib / ".picasa.ini"
        tartalom = "[a.jpg]\nfaces=rect64(3f840000c3509f84),0123456789abcdef;\n"
        ini.write_text(tartalom, encoding="utf-8")

        ctl.setFaceDetectionEnabled(str(lib), False)

        assert ini.read_text(encoding="utf-8") == tartalom

    def test_a_visszaengedes_NEM_torli_a_jelolest(self, controller):
        """A jelölés a visszaengedést is túléli: az eredeti jelzőjét sem
        írja felül a detektáló ág, tehát nem indulhat automatikus
        újra-detektálás a felhasználó külön szándéka nélkül (#2519)."""
        ctl, lib, tmp_path = controller
        ctl.setFaceDetectionEnabled(str(lib), False)
        assert _sorok(tmp_path, "face_scan") == 2

        ctl.setFaceDetectionEnabled(str(lib), True)

        assert _sorok(tmp_path, "face_scan") == 2, (
            "a visszaengedés eldobta a jelölést — így a következő szkennelés "
            "kérdés nélkül újra végigfutna a kizárt mappa képein"
        )
