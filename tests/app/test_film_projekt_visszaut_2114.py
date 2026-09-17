"""A film kimenetétől VISSZA a projekthez (#2114).

## A mérés

Az eredetiben a szerkesztő két ikergombot ismer: `editpanel/editcollage`
(„Kollázs szerkesztése") és `editpanel/editslideshow` („Mozgófilm
szerkesztése"), **ugyanabban a kezelőben** (`0x00567a00`), mindkettő
`m_hidden` — csak akkor jön elő, ha a megnyitott kép egy PROJEKT kimenete.

Nálunk a kollázs-ág megvolt (`hasCollageProject` + `.cxf`), a film-ágé nem.
A #3191 óta a film mellé is kiírjuk a projektfájlt (`.mxf`), tehát a
visszaút feltétele adott: ez a modul a vezérlő-oldali két lekérdezést adja.

## Amit ez az őr állít

- `hasMovieProject` akkor és csak akkor igaz, ha a kimenet mellett ott a
  `.mxf` pár;
- `movieProject` a projektfájlból adja vissza a **forrásképeket sorrendben**
  és a **diaidőt**.

## ⛔ Amit a projektfájl NEM tárol

A videó FELBONTÁSÁT: a `_film_projekt` a `curresolution`-t nem tölti ki (a
mező jelentése a mi modellünkben nincs mérve). Az újranyitás ezért a
felbontás alapértelmezését hozza — ezt a hívó felület mondja ki, nem
találgatjuk.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from picasapy.movie.mxf import MxfAtmenet, MxfForras, MxfProjekt, write_mxf


@pytest.fixture
def controller(qt_app, tmp_path):
    """A két lekérdezés a `CreateMixin`-é, tehát a teljes vezérlőn él.

    A könyvtár üres: ezek a slotok csak a fájlrendszert nézik (a kimenet
    mellett áll-e a `.mxf`), nem az indexet."""
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index
    from picasapy.thumbs import ThumbnailCache

    konyvtar = tmp_path / "kepek"
    konyvtar.mkdir()
    with open_index(tmp_path / "index.db"):
        pass
    szolgaltato = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    ctl = AppController(tmp_path / "index.db", (str(konyvtar),), szolgaltato)
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0)


def _projektet_ir(video: Path, kepek: list[Path], masodperc: float) -> Path:
    projekt = MxfProjekt(
        defaulttrans=MxfAtmenet(advanceinterval=masodperc),
        atmenetek=tuple(
            MxfAtmenet(
                advanceinterval=masodperc,
                forras=MxfForras(index=i, filename=str(ut)),
            )
            for i, ut in enumerate(kepek)
        ),
    )
    return write_mxf(video.with_suffix(".mxf"), projekt)


class TestVanEProjekt:
    def test_projektfajl_nelkul_hamis(self, controller, tmp_path):
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        assert controller.hasMovieProject(str(video)) is False

    def test_a_melle_irt_mxf_igazza_teszi(self, controller, tmp_path):
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        _projektet_ir(video, [tmp_path / "a.jpg"], 3.0)
        assert controller.hasMovieProject(str(video)) is True

    def test_ures_utvonalra_hamis(self, controller):
        assert controller.hasMovieProject("") is False

    def test_url_alakot_is_ert(self, controller, tmp_path):
        """A QML `file://`-alakban adja tovább a néző útvonalát."""
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        _projektet_ir(video, [tmp_path / "a.jpg"], 3.0)
        assert controller.hasMovieProject(video.as_uri()) is True


class TestAProjektTartalma:
    def test_a_forraskepek_SORRENDBEN_jonnek(self, controller, tmp_path):
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        kepek = [tmp_path / "a.jpg", tmp_path / "b.jpg", tmp_path / "c.jpg"]
        _projektet_ir(video, kepek, 2.5)

        projekt = controller.movieProject(str(video))
        assert list(projekt["sources"]) == [str(ut) for ut in kepek]

    def test_a_diaido_a_projektbol_jon(self, controller, tmp_path):
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        _projektet_ir(video, [tmp_path / "a.jpg"], 4.5)

        assert controller.movieProject(str(video))["seconds"] == pytest.approx(4.5)

    def test_projektfajl_nelkul_URES_szotar(self, controller, tmp_path):
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        assert controller.movieProject(str(video)) == {}

    def test_serult_projektfajl_sem_dob(self, controller, tmp_path):
        """A visszaút nem boríthatja a felületet — üres szótár a válasz."""
        video = tmp_path / "film.mp4"
        video.write_bytes(b"")
        video.with_suffix(".mxf").write_text("nem xml", encoding="utf-8")
        assert controller.movieProject(str(video)) == {}
