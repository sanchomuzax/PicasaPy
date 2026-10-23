"""#5676: a Film készítése kimeneti fájlneve kövesse az eredeti Picasát.

Az eredeti (`docs/specs/picasa-create-features.md`, „Fájlnév" sor és a
0x00620998 / 0x00620ab1 / 0x00993030 táblázat) három szabályt követ:

1. ha a munkamenetben már készült kimenet, a következő automatikus cél ANNAK
   a nevét használja, a mappájával együtt (`0x00620998`);
2. különben a felület nyelvének honosított alapnevét (`CMakeMoviePanel::
   deffilename`, `0x00620ab1`), a forrásmappa neve NEM számít;
3. ütközéskor szóköz nélküli sorszám: `név1.mp4`, `név2.mp4` (`0x00993030`).

A teszt a valódi `AppController`-t használja. A kodeket viszont egy hamis
`export_movie` helyettesíti: a névképzés a vezérlő dolga, a kodek nem, és
így a teszt nem függ az OpenCV `mp4v` kodektől.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QSettings

from picasapy.app import collage_output
from picasapy.app import create_controller as cc
from picasapy.app import movie_output
from picasapy.app.language_controller import SUPPORTED_LANGUAGES
from support.jpeg_factory import make_jpeg
from support.qt_wait import hangos_hurok


class TestHonositottAlapnev:
    @pytest.mark.parametrize(
        ("nyelv", "varhato"),
        [
            ("hu", "diavetites_jellegu_film"),
            ("en", "slideshowmovie"),
            ("enUK", "slideshow video"),
            ("de", "Diashow-Film"),
            ("xx", "slideshowmovie"),
            (None, "slideshowmovie"),
        ],
    )
    def test_a_nyelv_szerinti_alapnev(self, nyelv, varhato):
        """Ismeretlen nyelvnél az angol `slideshowmovie` a tartalék."""
        assert movie_output.honositott_alapnev(nyelv) == varhato

    def test_minden_tamogatott_nyelvnek_van_alapneve(self):
        assert set(movie_output.HONOSITOTT_ALAPNEV) == set(SUPPORTED_LANGUAGES)

    def test_ures_cimre_a_nyelv_alapneve_jon_a_celfajlban(self, tmp_path):
        cel = movie_output.output_path(tmp_path, "", "hu")
        assert cel == tmp_path / "diavetites_jellegu_film.mp4"


@pytest.fixture
def library(tmp_path):
    root = tmp_path / "kepek"
    (root / "nyaralas").mkdir(parents=True)
    make_jpeg(root / "nyaralas" / "IMG_0001.jpg", size=(120, 80))
    make_jpeg(root / "nyaralas" / "IMG_0002.jpg", size=(80, 120))
    return root


class _HamisJelentes:
    """Az `export_movie` jelentésének annyi mezője, amennyit a vezérlő olvas."""

    def __init__(self, cel: Path, kepek: list):
        self.target = cel
        self.used = kepek
        self.skipped = ()
        self.missing = ()
        self.used_face_rects = ()


@pytest.fixture
def hamis_export(monkeypatch):
    """A kodek helyett: célfájlt ír (üres), és a jelentést adja vissza."""

    def export(sources, target, settings, progress=None):
        Path(target).parent.mkdir(parents=True, exist_ok=True)
        Path(target).write_bytes(b"")
        return _HamisJelentes(Path(target), list(sources))

    monkeypatch.setattr(cc, "export_movie", export)


@pytest.fixture
def vezerlo(qt_app, tmp_path, library, hamis_export):
    from picasapy.app.controller import AppController
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)
    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    # a teszt NEM írhat a felhasználó valódi Filmek-mappájába (#1054)
    settings.setValue(movie_output.OUTPUT_DIR_KEY, str(tmp_path / "filmek"))
    ctl = AppController(
        tmp_path / "index.db", (str(library),), provider, settings=settings
    )
    ctl.selectFolder(str(library / "nyaralas"))
    yield ctl
    assert ctl.waitForBackgroundWorkers(30.0), "a film háttérszála nem állt le"


@pytest.fixture
def nyelv(monkeypatch):
    """A felület nyelvét rögzíti: a valódi QSettings ne számítson bele."""

    def allit(kod: str) -> None:
        monkeypatch.setattr(collage_output, "_felulet_nyelve", lambda: kod)

    return allit


def _keszit(vezerlo, cel: str = "") -> Path:
    """Exportál a kijelölt képekből, és visszaadja a kész kimenet útvonalát."""
    loop = hangos_hurok(
        vezerlo.movieFinished, leiras="a film elkészültét", timeout_ms=20000
    )
    vezerlo.exportMovie([0], cel, 720, 1.0)
    loop.exec()
    assert loop.jelzes_megjott, "nem érkezett movieFinished"
    return Path(loop.jelzes_argumentumai[0])


class TestEgyMappabolJovoKepek:
    @pytest.mark.parametrize(
        ("nyelv_kod", "alapnev"),
        [("hu", "diavetites_jellegu_film"), ("en", "slideshowmovie")],
    )
    def test_a_honositott_alapnev_lesz_a_nev_nem_a_forrasmappa(
        self, vezerlo, tmp_path, nyelv, nyelv_kod, alapnev
    ):
        """A forrásmappa `nyaralas`: régen ebből lett volna `nyaralas.mp4`."""
        nyelv(nyelv_kod)
        cel = _keszit(vezerlo)
        assert cel == tmp_path / "filmek" / f"{alapnev}.mp4"


class TestUtkozes:
    def test_utkozeskor_szokoz_nelkuli_sorszam(self, vezerlo, tmp_path, nyelv):
        nyelv("hu")
        (tmp_path / "filmek").mkdir()
        (tmp_path / "filmek" / "diavetites_jellegu_film.mp4").write_bytes(b"")
        cel = _keszit(vezerlo)
        assert cel == tmp_path / "filmek" / "diavetites_jellegu_film1.mp4"


class TestElozoKimenet:
    def test_sikeres_export_utan_az_elozo_nev_jon_sorszammal(
        self, vezerlo, tmp_path, nyelv
    ):
        """A felhasználó célt adott (`Nyaralas.mp4`); a következő üres céllal
        indított film ugyanannak a nevét kapja, mivel az létezik: sorszámmal."""
        nyelv("hu")
        _keszit(vezerlo, str(tmp_path / "filmek" / "Nyaralas.mp4"))
        cel = _keszit(vezerlo)
        assert cel == tmp_path / "filmek" / "Nyaralas1.mp4"

    def test_az_elozo_kimenet_MAPPAJA_is_az_uj_cel_mappaja(
        self, vezerlo, tmp_path, nyelv
    ):
        """Az „annak a nevét és mappáját" olvasat: az előző kimenet mappája
        nyer, nem a beállított Filmek-mappa."""
        nyelv("hu")
        masik = tmp_path / "masik"
        masik.mkdir()
        _keszit(vezerlo, str(masik / "Nyaralas.mp4"))
        cel = _keszit(vezerlo)
        assert cel == masik / "Nyaralas1.mp4"

    def test_ha_az_elozo_kimenet_MAR_nincs_meg_a_nev_sorszam_nelkul_jon(
        self, vezerlo, tmp_path, nyelv
    ):
        nyelv("hu")
        kezi = tmp_path / "filmek" / "Nyaralas.mp4"
        _keszit(vezerlo, str(kezi))
        kezi.unlink()
        cel = _keszit(vezerlo)
        assert cel == tmp_path / "filmek" / "Nyaralas.mp4"
