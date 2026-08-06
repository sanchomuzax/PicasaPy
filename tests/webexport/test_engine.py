"""A `.tpl` sablon teljes futtatása (#351) — a `tpl_lang` nyelvi motor +
`context` változó-táblák egysíkú (unit-szintű) tesztje szintetikus mini-
sablonokkal, ÉS a csomagolt gyári "Fehér" sablon teljes végigfuttatása."""

from pathlib import Path

import pytest

from picasapy.webexport.context import AlbumExportData, PhotoExportData, WebExportSettings
from picasapy.webexport.engine import (
    TemplateNotFoundError,
    WebExportReport,
    run_web_export,
)
from picasapy.webexport.tpl_lang import TplSyntaxError


def _photo(name, caption=""):
    return PhotoExportData(
        name=name,
        caption=caption,
        original_width=80,
        original_height=60,
        size_bytes=1024,
        thumbnail_rel_path=f"thumbnail/{name}",
        thumbnail_width=20,
        thumbnail_height=15,
        large_rel_path=f"image/{name}",
        large_width=80,
        large_height=60,
    )


def _album(*names):
    return AlbumExportData(name="Teszt album", caption="", photos=tuple(_photo(n) for n in names))


def _write(dir_path: Path, name: str, content: str) -> None:
    (dir_path / name).write_text(content, encoding="utf-8")


class TestDefineAndInclude:
    def test_define_sets_export_file_name(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "define exportFileName sajat.html\ninclude body.html\n")
        _write(template, "body.html", "Album: <%albumName%>")
        target = tmp_path / "out"
        report = run_web_export(template, target, _album())
        assert report.output_files == (target / "sajat.html",)
        assert (target / "sajat.html").read_text(encoding="utf-8") == "Album: Teszt album"

    def test_missing_include_raises(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "include hianyzik.html\n")
        with pytest.raises(TemplateNotFoundError):
            run_web_export(template, tmp_path / "out", _album())

    def test_missing_index_tpl_raises(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        with pytest.raises(TemplateNotFoundError):
            run_web_export(template, tmp_path / "out", _album())

    def test_unknown_command_raises(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "nemletezo x y\n")
        with pytest.raises(TplSyntaxError):
            run_web_export(template, tmp_path / "out", _album())


class TestLoop:
    def test_loop_repeats_per_image_file_for_each_photo(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "loop item.html\n")
        _write(template, "item.html", "[<%itemNumber%>:<%itemName%>]")
        album = _album("a.jpg", "b.jpg", "c.jpg")
        report = run_web_export(template, tmp_path / "out", album)
        text = report.output_files[0].read_text(encoding="utf-8")
        assert text == "[1:a.jpg][2:b.jpg][3:c.jpg]"

    def test_loop_on_empty_album_produces_nothing(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "loop item.html\n")
        _write(template, "item.html", "X")
        report = run_web_export(template, tmp_path / "out", _album())
        assert report.output_files[0].read_text(encoding="utf-8") == ""


class TestTargetloop:
    def test_generates_one_file_per_image_and_links_them(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(
            template, "index.tpl",
            "define exportFileName index.html\n"
            "targetloop detail.tpl link.html\n",
        )
        _write(template, "detail.tpl", "include detailbody.html\n")
        _write(
            template, "detailbody.html",
            "<%itemName%> ref=<%referrer%> prev=<%prevTarget%> next=<%nextTarget%>",
        )
        _write(template, "link.html", "[<%targetPath%>]")
        album = _album("a.jpg", "b.jpg")
        report = run_web_export(template, tmp_path / "out", album)
        names = sorted(p.name for p in report.output_files)
        assert names == ["index.html", "index0.html", "index1.html"]
        index_text = (tmp_path / "out" / "index.html").read_text(encoding="utf-8")
        assert index_text == "[index0.html][index1.html]"
        first = (tmp_path / "out" / "index0.html").read_text(encoding="utf-8")
        assert first == "a.jpg ref=index.html prev= next=index1.html"
        second = (tmp_path / "out" / "index1.html").read_text(encoding="utf-8")
        assert second == "b.jpg ref=index.html prev=index0.html next="


class TestCopy:
    def test_copies_directory_recursively(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        (template / "assets").mkdir()
        _write(template / "assets", "style.css", "body{color:red}")
        _write(template, "index.tpl", "copy assets\\\n")
        target = tmp_path / "out"
        run_web_export(template, target, _album())
        assert (target / "assets" / "style.css").read_text(encoding="utf-8") == "body{color:red}"

    def test_copy_missing_source_raises(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(template, "index.tpl", "copy nincs\\\n")
        with pytest.raises(TemplateNotFoundError):
            run_web_export(template, tmp_path / "out", _album())


class TestConditionalsInTemplate:
    def test_if_endif_reacts_to_command_variable(self, tmp_path):
        template = tmp_path / "tpl"
        template.mkdir()
        _write(
            template, "index.tpl",
            "define exportFileName index.html\ninclude body.html\n",
        )
        _write(
            template, "body.html",
            "<%if shadowedThumbnails%>ARNYEK<%endif%><%if !shadowedThumbnails%>SIMA<%endif%>",
        )
        settings = WebExportSettings(shadowed_thumbnails=True)
        report = run_web_export(template, tmp_path / "out", _album(), settings)
        assert report.output_files[0].read_text(encoding="utf-8") == "ARNYEK"


class TestBundledFeherTemplate:
    """A csomagolt "Fehér" gyári sablon teljes futtatása valódi JPEG-ekkel."""

    @pytest.fixture
    def feher_dir(self):
        import picasapy.webexport as webexport_pkg

        return Path(webexport_pkg.__file__).resolve().parent / "templates" / "feher"

    def test_full_run_with_real_images(self, tmp_path, feher_dir):
        from picasapy.index import PhotoRecord
        from picasapy.webexport.images import prepare_photo_exports
        from support.jpeg_factory import make_jpeg

        library = tmp_path / "kepek"
        library.mkdir()
        make_jpeg(library / "a.jpg", size=(400, 300))
        make_jpeg(library / "b.jpg", size=(400, 300))
        records = (
            PhotoRecord(
                id=1, folder_path=str(library), name="a.jpg", kind="photo",
                size=(library / "a.jpg").stat().st_size, mtime_ns=0, star=False,
                caption="Első kép", keywords=None, rotate_steps=0, filters=None,
                taken_at=None, orientation=1, width=400, height=300,
            ),
            PhotoRecord(
                id=2, folder_path=str(library), name="b.jpg", kind="photo",
                size=(library / "b.jpg").stat().st_size, mtime_ns=0, star=False,
                caption=None, keywords=None, rotate_steps=0, filters=None,
                taken_at=None, orientation=1, width=400, height=300,
            ),
        )
        target = tmp_path / "webexport"
        settings = WebExportSettings(thumbnail_max_dimension=120, image_max_dimension=800)
        image_report = prepare_photo_exports(records, target, settings)
        assert len(image_report.photos) == 2

        album = AlbumExportData(
            name="Nyaralás", caption="2026 nyara", date="2026. augusztus",
            photos=image_report.photos,
        )
        report = run_web_export(feher_dir, target, album, settings)

        assert isinstance(report, WebExportReport)
        names = sorted(p.name for p in report.output_files)
        assert names == ["index.html", "index0.html", "index1.html"]
        index_html = (target / "index.html").read_text(encoding="utf-8")
        assert "Nyaralás" in index_html
        assert "2026 nyara" in index_html
        assert "Első kép" in index_html  # itemCaption megjelenik
        assert "b" in index_html  # a caption nélküli kép name_only-ja megjelenik
        assert 'href="style.css"' in index_html
        # a `copy style.css` / `copy assets/` parancsok ténylegesen másolnak:
        assert (target / "style.css").is_file()
        assert (target / "assets" / "extra.css").is_file()
        detail_html = (target / "index0.html").read_text(encoding="utf-8")
        assert "index.html" in detail_html  # "vissza" hivatkozás a referrerre
