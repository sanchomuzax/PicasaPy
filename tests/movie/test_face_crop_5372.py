"""#5372: az arcfilmklipek képkockája a mért arckivágást használja."""

from pathlib import Path

import numpy as np
import pytest

from tests.support.create_dialogs_components_6051 import create_dialogs_source_text


@pytest.mark.parametrize(
    "viewport, source, cropfit, face, vart_bitek, egesz_rect",
    [
        (
            (1024, 768),
            (1024, 768),
            True,
            (200, 200, 500, 400),
            (0x431B19C9, 0x432A1C47, 0x440856AA, 0x43D723C2),
            (155, 170, 545, 430),
        ),
        (
            (1024, 768),
            (1024, 768),
            True,
            (100, 100, 200, 200),
            (0x41B01D40, 0x41B01D40, 0x438B171F, 0x438B171F),
            (22, 22, 278, 278),
        ),
        (
            (1024, 768),
            (2000, 1000),
            True,
            (800, 400, 1200, 600),
            (0x439C583A, 0x438E2C1D, 0x443213C3, 0x43F213C3),
            (312, 284, 712, 484),
        ),
        (
            (1024, 768),
            (2000, 1000),
            False,
            (800, 400, 1200, 600),
            (0x43AABFF6, 0x43955FFB, 0x442ABFF5, 0x43EABFF5),
            (341, 298, 683, 469),
        ),
    ],
)
def test_a_qemu_crop_rect_bitre_egyezik_a_spec_mereseivel(
    viewport, source, cropfit, face, vart_bitek, egesz_rect
):
    from picasapy.movie.face_crop import calculate_face_crop

    eredmeny = calculate_face_crop(
        face,
        source_size=source,
        viewport_size=viewport,
        cropfit=cropfit,
    )

    bitek = tuple(
        int(value)
        for value in np.asarray(eredmeny.rectangle, dtype=np.float32).view(np.uint32)
    )
    assert bitek == vart_bitek
    assert eredmeny.rounded_rectangle == egesz_rect


def test_a_rect64_pixella_valtasa_a_65535_os_nevezot_hasznalja():
    from picasapy.movie.face_crop import rect64_to_pixel_rect

    assert rect64_to_pixel_rect((1, 1, 100, 100), 32768, 32768) == (
        np.float32(1), np.float32(1), np.float32(50), np.float32(50)
    )


def test_a_rect64_konverzio_a_kep_szelen_is_ervenyes_egypixeles_rectet_ad():
    from picasapy.movie.face_crop import rect64_to_pixel_rect

    assert rect64_to_pixel_rect((65535, 65535, 65535, 65535), 100, 80) == (
        np.float32(99), np.float32(79), np.float32(100), np.float32(80)
    )


def test_a_crop_rect_metszese_megelozi_a_skala_es_zoom_szamitasat():
    from picasapy.movie.face_crop import calculate_face_crop

    eredmeny = calculate_face_crop(
        (800, 400, 1200, 600),
        source_size=(2000, 1000),
        viewport_size=(1024, 768),
        cropfit=True,
        crop_rect=(900, 450, 1100, 550),
    )

    assert eredmeny.source_rectangle == tuple(
        np.float32(value) for value in (900, 450, 1100, 550)
    )


@pytest.mark.parametrize(
    "face_width, remove_low_res_faces, included",
    [(136, True, False), (136.5, True, True), (137, True, True), (136, False, True)],
)
def test_a_kis_feluletu_arcot_csak_a_136_5_os_kapcsolo_szuri(
    face_width, remove_low_res_faces, included
):
    from picasapy.movie.face_crop import face_is_usable

    assert face_is_usable(
        (0, 0, face_width, 200), remove_low_res_faces=remove_low_res_faces
    ) is included


def test_az_arcfilm_exportja_kihagyja_a_kis_arcot_es_1024x768_ben_kozepre_vag(
    tmp_path, monkeypatch
):
    import picasapy.movie.slideshow as slideshow
    from picasapy.movie import MovieSettings, export_movie

    narrow = tmp_path / "narrow.jpg"
    wide = tmp_path / "wide.jpg"
    narrow.write_bytes(b"synthetic input")
    wide.write_bytes(b"synthetic input")
    # 1000 px szélességnél a 8900 rect64-egységből 136 px, a 9000-ből
    # 137 px lesz a bináris 65535-ös skáláján.
    (tmp_path / ".picasa.ini").write_text(
        "[narrow.jpg]\n"
        "faces=rect64(0000271022c49c40),1\n"
        "[wide.jpg]\n"
        "faces=rect64(0000271023289c40),1\n",
        encoding="utf-8",
    )
    image = np.zeros((500, 1000, 3), np.uint8)
    image[:] = (255, 0, 0)
    image[180:205, 56:82] = (0, 0, 255)
    monkeypatch.setattr(slideshow, "_decode", lambda _path: image.copy())

    writers = []

    class Writer:
        def __init__(self, *_args):
            self.frames = []
            writers.append(self)

        def isOpened(self):
            return True

        def write(self, frame):
            self.frames.append(frame.copy())

        def release(self):
            pass

    monkeypatch.setattr(slideshow.cv2, "VideoWriter", Writer)
    settings = MovieSettings(
        width=1024,
        height=768,
        fps=1,
        seconds_per_photo=1.0,
        transition_seconds=0.0,
        transition_type="cut",
        face_movie=True,
        remove_low_res_faces=True,
    )

    report = export_movie((narrow, wide), tmp_path / "faces.mp4", settings)

    assert report.used == (wide,)
    assert report.skipped == (narrow,)
    assert report.used_face_rects == ((0, 76, 137, 305),)
    assert len(writers) == 1 and len(writers[0].frames) == 1
    frame = writers[0].frames[0]
    assert frame.shape == (768, 1024, 3)
    assert frame[384, 512, 2] > 200


def test_az_arcfilm_beallitasa_es_mxf_projektje_megorzi_a_kivagast():
    from picasapy.app.create_controller import CreateMixin

    settings = CreateMixin._film_beallitas(
        1024,
        768,
        1.0,
        transition_seconds=0.0,
        transition_type="cut",
        options={"faceMovie": True, "removelowresfaces": True},
    )
    project = CreateMixin._film_projekt(
        (Path("face.jpg"),),
        settings,
        used_face_rects=((10, 20, 150, 180),),
    )

    assert (settings.width, settings.height) == (1024, 768)
    assert settings.face_movie is True
    assert project.facemovie is True
    assert project.removelowresfaces is True
    source = project.atmenetek[0].forras.szovegparam
    assert source.facemoviesrc == 1
    assert (
        source.facerectx0,
        source.facerecty0,
        source.facerectx1,
        source.facerecty1,
    ) == (10, 20, 150, 180)


def test_a_filmdialog_atadja_az_arcfilm_modot_az_exportnak():
    qml = create_dialogs_source_text()

    assert "faceMovie: movieDialog.personMovieMode" in qml
