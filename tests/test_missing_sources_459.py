"""#459/3 — hiányzó fájlok projektekben: folytatás a maradékkal + KÜLÖN
tájékoztatás.

Az eredeti Picasa megkülönböztette a „nem található" és a „nem olvasható"
esetet: az előbbire megmondta, mi történhetett (elmozdítás, átnevezés,
törlés). Nálunk eddig mindkettő ugyanabba a semleges „kihagyva" számba
folyt bele.
"""

from __future__ import annotations

import pytest

from picasapy.collage.render import make_collage
from picasapy.movie.slideshow import MovieSettings, export_movie

from support.jpeg_factory import make_jpeg


@pytest.fixture
def sources(tmp_path):
    """Egy jó, egy hiányzó és egy meglévő, de olvashatatlan forrás."""
    good = tmp_path / "jo.jpg"
    make_jpeg(good)
    broken = tmp_path / "romlott.jpg"
    broken.write_bytes(b"ez nem jpeg")
    gone = tmp_path / "nincs.jpg"  # szándékosan nem jön létre
    return good, gone, broken


class TestCollageMissingSources:
    def test_missing_is_reported_separately(self, sources):
        good, gone, broken = sources
        report = make_collage([good, gone, broken])

        assert list(report.used) == [good]
        assert list(report.missing) == [gone]
        # a hiányzó a kihagyottak közt is ott van (a régi összesítés nem tört el)
        assert set(report.skipped) == {gone, broken}

    def test_work_continues_with_the_rest(self, sources):
        good, gone, _broken = sources
        report = make_collage([gone, good])
        assert report.used  # a hiányzó fájl nem állítja meg a munkát
        assert report.image is not None


class TestMovieMissingSources:
    def test_missing_is_reported_separately(self, tmp_path, sources):
        good, gone, broken = sources
        report = export_movie(
            [good, gone, broken],
            tmp_path / "film.mp4",
            MovieSettings(
                width=160,
                height=90,
                seconds_per_photo=0.2,
                transition_seconds=0.0,
            ),
        )

        assert list(report.used) == [good]
        assert list(report.missing) == [gone]
        assert set(report.skipped) == {gone, broken}
