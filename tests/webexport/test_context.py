"""Album-, kép-hurok- és cél-oldal-változó táblák (#351,
docs/specs/picasa-program-resources.md 2.4. alfejezet)."""

from picasapy.webexport.context import (
    AlbumExportData,
    PhotoExportData,
    WebExportSettings,
    album_variables,
    command_variables,
    image_loop_variables,
    target_page_variables,
)


def _photo(name="a.jpg", caption="Első kép"):
    return PhotoExportData(
        name=name,
        caption=caption,
        original_width=800,
        original_height=600,
        size_bytes=204800,
        thumbnail_rel_path=f"thumbnail/{name}",
        thumbnail_width=200,
        thumbnail_height=150,
        large_rel_path=f"image/{name}",
        large_width=800,
        large_height=600,
    )


class TestPhotoExportDataNameOnly:
    def test_strips_extension(self):
        assert _photo("kutya.jpg").name_only == "kutya"

    def test_no_extension_returns_full_name(self):
        assert _photo("kutya").name_only == "kutya"


class TestCommandVariables:
    def test_zero_means_original_size(self):
        variables = command_variables(WebExportSettings())
        assert variables["imageWidth"] == "0"
        assert variables["thumbnailHeight"] == "0"

    def test_explicit_dimensions(self):
        variables = command_variables(
            WebExportSettings(thumbnail_max_dimension=160, image_max_dimension=1024)
        )
        assert variables["thumbnailWidth"] == "160"
        assert variables["imageWidth"] == "1024"

    def test_shadow_flags_are_tpl_booleans(self):
        variables = command_variables(
            WebExportSettings(shadowed_thumbnails=True, shadowed_images=False)
        )
        assert variables["shadowedThumbnails"] == "true"
        assert variables["shadowedImages"] == ""


class TestAlbumVariables:
    def test_basic_fields(self):
        album = AlbumExportData(
            name="Nyaralás", caption="2026 nyara", date="2026. augusztus",
            photos=(_photo(), _photo("b.jpg")),
        )
        variables = album_variables(album)
        assert variables["albumName"] == "Nyaralás"
        assert variables["albumCaption"] == "2026 nyara"
        assert variables["albumDate"] == "2026. augusztus"
        assert variables["albumItemCount"] == "2"
        assert variables["albumNumber"] == "1"


class TestImageLoopVariables:
    def test_single_photo_is_first_and_last(self):
        photos = (_photo(),)
        variables = image_loop_variables(photos, 0)
        assert variables["isFirstImage"] == "true"
        assert variables["isLastImage"] == "true"
        assert variables["isNextImage"] == ""
        assert variables["isPrevImage"] == ""
        assert variables["itemNumber"] == "1"
        assert variables["itemSize"] == "200"  # 204800 bájt → 200 KB

    def test_middle_photo_has_next_and_prev(self):
        photos = (_photo("a.jpg"), _photo("b.jpg"), _photo("c.jpg"))
        variables = image_loop_variables(photos, 1)
        assert variables["isFirstImage"] == ""
        assert variables["isLastImage"] == ""
        assert variables["nextImage"] == "image/c.jpg"
        assert variables["prevImage"] == "image/a.jpg"
        assert variables["nextThumbnail"] == "thumbnail/c.jpg"
        assert variables["prevThumbnail"] == "thumbnail/a.jpg"

    def test_first_and_last_image_always_point_to_ends(self):
        photos = (_photo("a.jpg"), _photo("b.jpg"), _photo("c.jpg"))
        variables = image_loop_variables(photos, 1)
        assert variables["firstImage"] == "image/a.jpg"
        assert variables["lastImage"] == "image/c.jpg"

    def test_empty_caption_falls_back_gracefully(self):
        photos = (_photo("a.jpg", caption=""),)
        variables = image_loop_variables(photos, 0)
        assert variables["itemCaption"] == ""


class TestTargetPageVariables:
    def test_first_target(self):
        names = ("index0.html", "index1.html", "index2.html")
        variables = target_page_variables(names, 0, "index.html")
        assert variables["isFirstTarget"] == "true"
        assert variables["isPrevTarget"] == ""
        assert variables["nextTarget"] == "index1.html"
        assert variables["prevTarget"] == ""
        assert variables["referrer"] == "index.html"
        assert variables["outputIndex"] == "0"

    def test_last_target(self):
        names = ("index0.html", "index1.html", "index2.html")
        variables = target_page_variables(names, 2, "index.html")
        assert variables["isLastTarget"] == "true"
        assert variables["isNextTarget"] == ""
        assert variables["nextTarget"] == ""
        assert variables["prevTarget"] == "index1.html"

    def test_first_and_last_target_constant_across_pages(self):
        names = ("index0.html", "index1.html", "index2.html")
        for index in range(3):
            variables = target_page_variables(names, index, "index.html")
            assert variables["firstTarget"] == "index0.html"
            assert variables["lastTarget"] == "index2.html"
