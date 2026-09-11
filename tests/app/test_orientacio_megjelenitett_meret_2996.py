"""#2996: a fogyasztók a MEGJELENÍTETT méretet kapják.

Az index a fájlban tárolt méretet őrzi (az marad a kanonikus adat), de
aki arányt vagy felbontást MUTAT, annak az EXIF-orientációval korrigált
értékre van szüksége — különben minden álló tájolású telefonfelvétel
fekvőnek látszik.

Három fogyasztó (a jegy mérése szerint):

1. `app/collage_layout.aspect_of` — a kollázs helyet oszt az aránnyal;
2. `app/models.pixelWidthAt` / `pixelHeightAt` — a néző 1:1 nagyítása;
3. a felbontás-felirat (`resolution` szerep és a rács-adat).
"""

from __future__ import annotations

import pytest

from support.jpeg_factory import make_jpeg


@pytest.fixture
def gyujtemeny(tmp_path):
    gyoker = tmp_path / "kepek"
    gyoker.mkdir()
    #: fekvő fájl, ÁLLÓ orientációval — pontosan a telefonos eset
    make_jpeg(gyoker / "allo.jpg", size=(60, 40), orientation=6)
    make_jpeg(gyoker / "fekvo.jpg", size=(60, 40), orientation=1)
    return gyoker


@pytest.fixture
def controller(qt_app, tmp_path, gyujtemeny):
    from PySide6.QtCore import QSettings

    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, gyujtemeny)
    ctl = AppController(
        tmp_path / "index.db",
        (str(gyujtemeny),),
        ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32)),
        settings=QSettings(
            str(tmp_path / "settings.ini"), QSettings.Format.IniFormat
        ),
    )
    ctl._reload()
    return ctl


def _sor(controller, nev: str) -> int:
    for i, foto in enumerate(controller.photos.photos):
        if foto.name == nev:
            return i
    raise AssertionError(f"nincs ilyen fotó: {nev}")


class TestANezo:
    def test_az_ALLO_kep_merete_allo(self, controller):
        sor = _sor(controller, "allo.jpg")
        assert (
            controller.photos.pixelWidthAt(sor),
            controller.photos.pixelHeightAt(sor),
        ) == (40, 60), "a néző fekvőnek látja az álló telefonképet"

    def test_a_FEKVO_kep_valtozatlan(self, controller):
        sor = _sor(controller, "fekvo.jpg")
        assert (
            controller.photos.pixelWidthAt(sor),
            controller.photos.pixelHeightAt(sor),
        ) == (60, 40)


class TestAFelbontasFelirat:
    def test_az_ALLO_kep_felirata_allo(self, controller):
        sor = _sor(controller, "allo.jpg")
        adat = controller.photos.itemAt(sor)
        assert adat["resolution"] == "40x60", (
            f"a felbontás-felirat fordítva mutat: {adat['resolution']}"
        )


class TestAKollazs:
    def test_az_ALLO_kep_aranya_kisebb_egynel(self, controller):
        from picasapy.app.collage_layout import sources_from_photos

        forrasok = sources_from_photos(controller.photos.photos, [_sor(controller, "allo.jpg")])
        assert forrasok[0].aspect < 1.0, (
            f"a kollázs fekvő helyet oszt az álló képnek (arány: {forrasok[0].aspect})"
        )

    def test_a_FEKVO_kep_aranya_nagyobb_egynel(self, controller):
        from picasapy.app.collage_layout import sources_from_photos

        forrasok = sources_from_photos(
            controller.photos.photos, [_sor(controller, "fekvo.jpg")]
        )
        assert forrasok[0].aspect > 1.0
