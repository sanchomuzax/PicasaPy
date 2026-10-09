"""A rendszer betűcsaládjai és a szöveg-eszköz ini-köre (#4546)."""

from __future__ import annotations

import pytest
from PySide6.QtGui import QFont, QFontDatabase, QFontInfo

from picasapy.ini import load_document
from picasapy.ini.text_overlay import parse_text
from picasapy.render.text_fonts import family_labels
from support.jpeg_factory import make_jpeg


@pytest.fixture
def edit_controller(qt_app):
    from picasapy.app.edit_controller import EditController
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditController(EditPreviewProvider())


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "font-test.jpg", size=(320, 160))


def test_catalogue_lists_the_installed_qt_system_families(qt_app):
    expected = sorted(
        set(QFontDatabase.families()), key=lambda family: (family.casefold(), family)
    )
    actual = [entry["key"] for entry in family_labels()]

    assert actual == expected, (
        "a szöveg-eszköz listája nem a Qt által elérhető rendszerbetűkből áll"
    )


def test_selected_family_is_rendered_saved_and_loaded_again(
    edit_controller, photo, qt_app, monkeypatch
):
    from picasapy.app import edit_preview as preview_module

    family = next(
        family
        for family in QFontDatabase.families()
        if family.casefold() != "arial"
    )
    assert QFontInfo(QFont(family)).family().casefold() == family.casefold()

    original = preview_module.apply_text_overlay
    rendered_families = []

    def track_render(*args, **kwargs):
        rendered_families.append(kwargs["font_family"])
        return original(*args, **kwargs)

    monkeypatch.setattr(preview_module, "apply_text_overlay", track_render)

    edit_controller.beginEdit("1", str(photo))
    edit_controller.enterTextTool()
    edit_controller.setTextFontFamily(family)
    edit_controller.setTextDraft("System font")
    edit_controller.previewTextPlacement(0.3, 0.6)
    assert rendered_families[-1] == family

    edit_controller.applyText()
    document = load_document(photo.parent / ".picasa.ini")
    section = document.section(photo.name)
    saved = parse_text(section.get("text"))
    assert saved.primary.font == family

    edit_controller.endEdit()
    edit_controller.beginEdit("1", str(photo))
    assert edit_controller.textFontFamily == family
