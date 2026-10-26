"""#5926: a három keretes webexport-sablon egyoldalas, kétkeretes galériát ad."""

from pathlib import Path

import pytest

import picasapy.webexport as webexport_pkg
from picasapy.webexport.context import AlbumExportData, PhotoExportData
from picasapy.webexport.engine import run_web_export

_TEMPLATES = Path(webexport_pkg.__file__).resolve().parent / "templates"
_FRAME_TEMPLATES = ("szurke-keret", "fekete-keret", "feher-keret")
_STANDARD_TEMPLATES = ("szurke", "fekete", "feher")


def _album(*photos: PhotoExportData) -> AlbumExportData:
    return AlbumExportData(
        name="Nyári album",
        caption="Két kép",
        date="2026",
        photos=photos,
    )


def _photo(name: str, *, caption: str = "") -> PhotoExportData:
    return PhotoExportData(
        name=name,
        caption=caption,
        original_width=800,
        original_height=600,
        size_bytes=1024,
        thumbnail_rel_path=f"thumbnail/{name}",
        thumbnail_width=120,
        thumbnail_height=90,
        large_rel_path=f"image/{name}",
        large_width=800,
        large_height=600,
    )


@pytest.mark.parametrize("template_id", _FRAME_TEMPLATES)
def test_keretes_sablon_kimenete_galeria_a_ket_frameben(tmp_path, template_id):
    album = _album(
        _photo("elso.jpg", caption="Első kép"),
        _photo("masodik.jpg", caption="Második kép"),
    )
    output = tmp_path / template_id

    report = run_web_export(_TEMPLATES / template_id, output, album)

    index = (output / "index.html").read_text(encoding="utf-8")
    assert "<frameset" in index
    assert '<frame src="thumbnail-index0.html" name="thumbnail-index">' in index
    assert '<frame src="index0.html" name="large-view">' in index

    left_frame = (output / "thumbnail-index0.html").read_text(encoding="utf-8")
    assert 'href="image/elso.jpg" target="large-view"' in left_frame
    assert 'href="image/masodik.jpg" target="large-view"' in left_frame
    assert 'src="thumbnail/elso.jpg"' in left_frame
    assert 'src="thumbnail/masodik.jpg"' in left_frame
    large_view = (output / "index0.html").read_text(encoding="utf-8")
    assert 'href="index.html" target="_top"' in large_view
    assert "overflow-y: auto" in (output / "style.css").read_text(encoding="utf-8")
    assert {
        "index.html",
        "index0.html",
        "index1.html",
        "thumbnail-index0.html",
        "thumbnail-index1.html",
    } <= {path.name for path in report.output_files}


@pytest.mark.parametrize("template_id", _FRAME_TEMPLATES)
def test_keretes_sablon_uress_albumhoz_is_ad_ket_frameet(tmp_path, template_id):
    output = tmp_path / template_id

    run_web_export(_TEMPLATES / template_id, output, _album())

    index = (output / "index.html").read_text(encoding="utf-8")
    assert "<frameset" in index
    assert '<frame src="thumbnail-index0.html" name="thumbnail-index">' in index
    assert '<frame src="about:blank" name="large-view">' in index
    assert (output / "thumbnail-index0.html").is_file()


@pytest.mark.parametrize("template_id", _STANDARD_TEMPLATES)
def test_nem_keretes_sablonok_megtartjak_a_kulon_kepoldalakat(tmp_path, template_id):
    output = tmp_path / template_id
    album = _album(_photo("elso.jpg"), _photo("masodik.jpg"))

    report = run_web_export(_TEMPLATES / template_id, output, album)

    index = (output / "index.html").read_text(encoding="utf-8")
    assert "<frameset" not in index
    assert 'class="thumb-grid"' in index
    assert (output / "index0.html").is_file()
    assert (output / "index1.html").is_file()
    assert {"index.html", "index0.html", "index1.html"} <= {
        path.name for path in report.output_files
    }
