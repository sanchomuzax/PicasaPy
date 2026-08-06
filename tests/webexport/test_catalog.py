"""A csomagolt gyári sablonok felsorolása (#351)."""

from picasapy.webexport.catalog import list_bundled_templates


class TestListBundledTemplates:
    def test_includes_feher_template(self):
        templates = list_bundled_templates()
        ids = [t.id for t in templates]
        assert "feher" in ids

    def test_feher_has_name_and_description_from_header(self):
        templates = {t.id: t for t in list_bundled_templates()}
        feher = templates["feher"]
        assert feher.name == "Fehér"
        assert "hátterű" in feher.description or len(feher.description) > 0

    def test_path_points_to_directory_with_index_tpl(self):
        templates = {t.id: t for t in list_bundled_templates()}
        feher = templates["feher"]
        assert (feher.path / "index.tpl").is_file()
