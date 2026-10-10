"""#4610: a weboldal-export méretválasztója és mozgókép-módja az eredeti
`webexport.fen` szerint (spec: `docs/specs/picasa-menu-parancsok-viselkedes.md`
6.1).

- EGY méretválasztó van (a nagy kép mérete), öt fogással, alapérték 640;
- a bélyegkép méretét a sablon `define thumbnailWidth`-je adja, hiányában 144;
- a sablon `define imageWidth`-je felülírja a választást;
- „Első képkocka": a film állóképként kerül a galériába (`isImage`);
- „Teljes mozgófilm": a nagy kép maga a filmfájl, bájthű másolat, és a
  sablon a beágyazó ágat kapja (`isSimpleEmbed`)."""

from __future__ import annotations

import pytest

from picasapy.index import PhotoRecord
from picasapy.webexport.context import WebExportSettings, image_loop_variables
from picasapy.webexport.images import prepare_photo_exports
from picasapy.webexport.sizes import (
    DEFAULT_SIZE_INDEX,
    DEFAULT_THUMBNAIL_SIZE,
    SIZE_CHOICES,
    image_size_for_index,
    settings_for_template,
)
from support.jpeg_factory import make_jpeg


def _record(folder, name, **overrides):
    path = folder / name
    if not path.exists():
        make_jpeg(path, size=(80, 60))
    defaults = dict(
        id=1, folder_path=str(folder), name=name, kind="photo",
        size=path.stat().st_size, mtime_ns=0, star=False, caption=None,
        keywords=None, rotate_steps=0, filters=None, taken_at=None,
        orientation=1, width=80, height=60,
    )
    defaults.update(overrides)
    return PhotoRecord(**defaults)


def _video(path, size=(320, 240)):
    import cv2
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    width, height = size
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), 10.0, size)
    for value in (40, 120, 200):
        writer.write(np.full((height, width, 3), value, dtype=np.uint8))
    writer.release()
    if not path.exists() or path.stat().st_size == 0:
        pytest.skip("a gépen nincs mp4-kódoló — a mérés nem érvényes")
    return path


def _template(tmp_path, *lines):
    folder = tmp_path / "sablon"
    folder.mkdir()
    (folder / "index.tpl").write_text(
        '#templatefile -v "1.0" -n "T" -d ""\n' + "\n".join(lines) + "\n",
        encoding="utf-8",
    )
    return folder


class TestAMeretvalaszto:
    def test_ot_fogas_a_fen_sorrendjeben(self):
        # webexport.fen 4–8. sor: Original Size · 1024 · 800 · 640 · 320
        assert SIZE_CHOICES == (0, 1024, 800, 640, 320)

    def test_alaperteke_640(self):
        # Preferences\WebExportSize alapértéke 3 (0x007f5310) → 3. index
        assert DEFAULT_SIZE_INDEX == 3
        assert image_size_for_index(DEFAULT_SIZE_INDEX) == 640

    def test_ismeretlen_index_eredeti_meret(self):
        # 0x7f5bf0: a táblán kívüli érték a 0. indexre (Eredeti méret) esik
        assert image_size_for_index(99) == 0
        assert image_size_for_index(-1) == 0


class TestASablonMeretei:
    def test_belyegkep_alap_144_ha_a_sablon_nem_adja(self, tmp_path):
        folder = _template(tmp_path, "define exportFileName index.html")
        settings = settings_for_template(folder, 800, WebExportSettings())
        assert DEFAULT_THUMBNAIL_SIZE == 144
        assert settings.thumbnail_max_dimension == 144
        assert settings.image_max_dimension == 800

    def test_a_sablon_belyegkep_define_ja_nyer(self, tmp_path):
        folder = _template(
            tmp_path, "define thumbnailWidth 120", "define thumbnailHeight 120"
        )
        settings = settings_for_template(folder, 800, WebExportSettings())
        assert settings.thumbnail_max_dimension == 120

    def test_a_sablon_imagewidth_je_felulirja_a_valasztast(self, tmp_path):
        folder = _template(tmp_path, "define imageWidth 600", "define imageHeight 600")
        settings = settings_for_template(folder, 1024, WebExportSettings())
        assert settings.image_max_dimension == 600

    def test_kikommentezett_define_nem_szamit(self, tmp_path):
        folder = _template(tmp_path, "# define imageWidth 600", "#define thumbnailWidth 80")
        settings = settings_for_template(folder, 320, WebExportSettings())
        assert settings.image_max_dimension == 320
        assert settings.thumbnail_max_dimension == 144

    def test_eredeti_meret_valasztas(self, tmp_path):
        folder = _template(tmp_path)
        settings = settings_for_template(folder, 0, WebExportSettings())
        assert settings.image_max_dimension is None

    def test_a_tobbi_beallitas_megmarad(self, tmp_path):
        folder = _template(tmp_path)
        base = WebExportSettings(movie_full=True, shadowed_images=True)
        settings = settings_for_template(folder, 640, base)
        assert settings.movie_full is True
        assert settings.shadowed_images is True


class TestAKimenetKepmerete:
    def test_320_es_valasztasnal_a_nagy_kep_320(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        make_jpeg(library / "a.jpg", size=(800, 600))
        record = _record(library, "a.jpg", width=800, height=600)
        folder = _template(tmp_path)
        settings = settings_for_template(folder, image_size_for_index(4), WebExportSettings())
        report = prepare_photo_exports((record,), tmp_path / "ki", settings)
        photo = report.photos[0]
        assert max(photo.large_width, photo.large_height) == 320
        assert max(photo.thumbnail_width, photo.thumbnail_height) == 144

    def test_az_itemwidth_az_exportalt_kep_merete(self, tmp_path):
        """`web/documentation/index.html`: „itemWidth — Actual width of the
        exported picture, in pixels." — nem az eredetié; különben a lap a
        320-as képet 800 képpontra nagyítva mutatná."""
        library = tmp_path / "kepek"
        library.mkdir()
        make_jpeg(library / "a.jpg", size=(800, 600))
        record = _record(library, "a.jpg", width=800, height=600)
        settings = WebExportSettings(thumbnail_max_dimension=144, image_max_dimension=320)
        report = prepare_photo_exports((record,), tmp_path / "ki", settings)
        variables = image_loop_variables(report.photos, 0)
        assert (variables["itemWidth"], variables["itemHeight"]) == ("320", "240")


class TestAMozgokepMod:
    @pytest.fixture(autouse=True)
    def _helyben_dekodol(self, monkeypatch):
        """Az elszigetelt dekóder gyermekfolyamatot indít 5 mp-es
        határidővel, ami terhelt gépen lejár, és a teszt a terhelést mérné,
        nem a webexportot. Itt ugyanaz a kocka-kinyerés fut, helyben."""
        from picasapy.thumbs import cache

        monkeypatch.setattr(
            cache,
            "_decode_video_frame_isolated",
            lambda source, **_kw: cache._decode_video_frame(source),
        )

    def test_alapertek_elso_kepkocka(self):
        assert WebExportSettings().movie_full is False

    def test_elso_kepkocka_allokepet_ad(self, tmp_path):
        video = _video(tmp_path / "kepek" / "v.mp4")
        record = _record(video.parent, "v.mp4", kind="video", width=320, height=240)
        settings = WebExportSettings(
            thumbnail_max_dimension=144, image_max_dimension=160, movie_full=False
        )
        report = prepare_photo_exports((record,), tmp_path / "ki", settings)

        assert report.skipped == ()
        photo = report.photos[0]
        assert photo.large_rel_path.endswith(".jpg")
        assert photo.thumbnail_rel_path.endswith(".jpg")
        assert max(photo.large_width, photo.large_height) == 160
        variables = image_loop_variables(report.photos, 0)
        assert variables["isImage"] == "true"
        assert variables["isSimpleEmbed"] == ""

    def test_teljes_mozgofilm_a_filmet_masolja(self, tmp_path):
        video = _video(tmp_path / "kepek" / "v.mp4")
        record = _record(video.parent, "v.mp4", kind="video", width=320, height=240)
        settings = WebExportSettings(
            thumbnail_max_dimension=144, image_max_dimension=160, movie_full=True
        )
        target = tmp_path / "ki"
        report = prepare_photo_exports((record,), target, settings)

        assert report.skipped == ()
        photo = report.photos[0]
        assert photo.large_rel_path == "image/v.mp4"
        assert (target / photo.large_rel_path).read_bytes() == video.read_bytes()
        # a bélyegkép az első kocka, a sablon méretében
        assert photo.thumbnail_rel_path.endswith(".jpg")
        assert max(photo.thumbnail_width, photo.thumbnail_height) == 144
        # a film saját mérete (nem a választott 160)
        assert (photo.large_width, photo.large_height) == (320, 240)
        variables = image_loop_variables(report.photos, 0)
        assert variables["isImage"] == ""
        assert variables["isSimpleEmbed"] == "true"
        assert variables["isExtendedEmbed"] == ""

    def test_teljes_mozgofilm_a_fenykepet_nem_erinti(self, tmp_path):
        library = tmp_path / "kepek"
        library.mkdir()
        record = _record(library, "a.jpg")
        settings = WebExportSettings(movie_full=True)
        report = prepare_photo_exports((record,), tmp_path / "ki", settings)
        variables = image_loop_variables(report.photos, 0)
        assert variables["isImage"] == "true"
        assert variables["isSimpleEmbed"] == ""

    @pytest.mark.parametrize("movie_full", [False, True])
    def test_olvashatatlan_film_kimarad_okkal(self, tmp_path, movie_full):
        library = tmp_path / "kepek"
        library.mkdir()
        (library / "v.mp4").write_bytes(b"nem-igazi-video")
        record = _record(library, "v.mp4", kind="video")
        settings = WebExportSettings(movie_full=movie_full)
        report = prepare_photo_exports((record,), tmp_path / "ki", settings)
        assert report.photos == ()
        assert len(report.skipped) == 1
        assert "v.mp4" in report.skipped[0]
        assert "videó" in report.skipped[0]


def _film_album():
    from picasapy.webexport.context import AlbumExportData, PhotoExportData

    film = PhotoExportData(
        name="v.mp4", caption="", original_width=320, original_height=240,
        size_bytes=2048, thumbnail_rel_path="thumbnail/v.jpg",
        thumbnail_width=144, thumbnail_height=108,
        large_rel_path="image/v.mp4", large_width=320, large_height=240,
        movie_embed=True,
    )
    kep = PhotoExportData(
        name="a.jpg", caption="", original_width=800, original_height=600,
        size_bytes=1024, thumbnail_rel_path="thumbnail/a.jpg",
        thumbnail_width=144, thumbnail_height=108,
        large_rel_path="image/a.jpg", large_width=640, large_height=480,
    )
    return AlbumExportData(name="Film", photos=(film, kep))


_HTML_SABLONOK = ("feher", "feher-keret", "fekete", "fekete-keret", "szurke", "szurke-keret")


@pytest.mark.parametrize("sablon_id", _HTML_SABLONOK)
def test_a_csomagolt_sablon_a_teljes_filmet_lejatszhatoan_agyazza_be(tmp_path, sablon_id):
    """Az eredeti sablonok az `isSimpleEmbed` ágon `<embed>`-et adnak
    (`blackbg/targetlistelement.html` 8–10. sor); a mi sablonjaink a mai
    böngészőben lejátszható `<video>`-t. A filmre `<img>` nem mutathat."""
    from picasapy.webexport import list_bundled_templates, run_web_export

    sablon = next(t for t in list_bundled_templates() if t.id == sablon_id)
    target = tmp_path / "ki"
    run_web_export(sablon.path, target, _film_album())
    oldalak = "".join(
        p.read_text(encoding="utf-8") for p in sorted(target.glob("index*.html"))
    )
    assert '<video src="image/v.mp4"' in oldalak
    assert '<img src="image/v.mp4"' not in oldalak
    assert '<img src="image/a.jpg"' in oldalak
