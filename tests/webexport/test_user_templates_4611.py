"""#4611: a felhasználó saját `.tpl` sablonjai is listázódnak és exportálnak,
és a videó-feltételek (`isImage`, `isSimpleEmbed`, `isExtendedEmbed`) —
docs/specs/picasa-web-template-nyelv.md 6. fejezet — definiáltak."""

from pathlib import Path

from picasapy.webexport.catalog import list_templates, user_templates_dir
from picasapy.webexport.context import (
    AlbumExportData,
    PhotoExportData,
    WebExportSettings,
    image_loop_variables,
)
from picasapy.webexport.engine import run_web_export


def _photo(name: str) -> PhotoExportData:
    return PhotoExportData(
        name=name,
        caption="",
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


def _write_template(root: Path, template_id: str, name: str, index_body: str) -> Path:
    folder = root / template_id
    folder.mkdir(parents=True)
    (folder / "index.tpl").write_text(
        f'#templatefile -v "1.0" -n "{name}" -d "Saját teszt"\n{index_body}',
        encoding="utf-8",
    )
    return folder


class TestUserTemplatesDir:
    def test_defaults_under_xdg_data_home(self, monkeypatch, tmp_path):
        monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
        assert user_templates_dir() == tmp_path / "picasapy" / "webexport" / "templates"

    def test_falls_back_to_local_share(self, monkeypatch, tmp_path):
        monkeypatch.delenv("XDG_DATA_HOME", raising=False)
        monkeypatch.setenv("HOME", str(tmp_path))
        assert user_templates_dir() == (
            tmp_path / ".local" / "share" / "picasapy" / "webexport" / "templates"
        )


class TestListTemplates:
    def test_lists_user_template_after_bundled_ones(self, tmp_path):
        _write_template(tmp_path, "sajat", "Saját sablon", "")
        ids = [t.id for t in list_templates(user_dir=tmp_path)]
        assert "feher" in ids
        assert ids[-1] == "sajat"

    def test_user_template_carries_name_and_path(self, tmp_path):
        folder = _write_template(tmp_path, "sajat", "Saját sablon", "")
        info = {t.id: t for t in list_templates(user_dir=tmp_path)}["sajat"]
        assert info.name == "Saját sablon"
        assert info.path == folder

    def test_folder_without_index_tpl_is_skipped(self, tmp_path):
        (tmp_path / "csonka").mkdir()
        ids = [t.id for t in list_templates(user_dir=tmp_path)]
        assert "csonka" not in ids

    def test_missing_user_dir_is_harmless(self, tmp_path):
        ids = [t.id for t in list_templates(user_dir=tmp_path / "nincs")]
        assert "feher" in ids

    def test_bundled_template_wins_over_same_id(self, tmp_path):
        _write_template(tmp_path, "feher", "Átírt Fehér", "")
        templates = [t for t in list_templates(user_dir=tmp_path) if t.id == "feher"]
        assert len(templates) == 1
        assert templates[0].name == "Fehér"


class TestVideoConditions:
    def test_stills_are_images_and_not_embeds(self):
        variables = image_loop_variables((_photo("a.jpg"),), 0)
        assert variables["isImage"] == "true"
        assert variables["isSimpleEmbed"] == ""
        assert variables["isExtendedEmbed"] == ""

    def test_own_template_renders_only_the_image_branch(self, tmp_path):
        template = _write_template(
            tmp_path / "src",
            "sajat",
            "Saját sablon",
            "define exportFileName index.html\nloop elem.html\n",
        )
        (template / "elem.html").write_text(
            "<%if isImage%>KEP:<%itemNameOnly%><%endif%>"
            "<%if isSimpleEmbed%>SIMPLE<%endif%>"
            "<%if isExtendedEmbed%>EXTENDED<%endif%>\n",
            encoding="utf-8",
        )
        album = AlbumExportData(name="Teszt", photos=(_photo("a.jpg"),))
        target = tmp_path / "ki"

        run_web_export(template, target, album, WebExportSettings())

        html = (target / "index.html").read_text(encoding="utf-8")
        assert "KEP:a" in html
        assert "SIMPLE" not in html
        assert "EXTENDED" not in html
