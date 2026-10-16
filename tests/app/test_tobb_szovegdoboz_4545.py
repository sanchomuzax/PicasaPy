"""Több feliratelem szerkesztése és előnézeti adata (#4545)."""

import pytest

from picasapy.ini.text_overlay import parse_text
from support.jpeg_factory import make_jpeg


@pytest.fixture
def provider(qt_app):
    from picasapy.app.edit_preview import EditPreviewProvider

    return EditPreviewProvider()


@pytest.fixture
def controller(qt_app, provider):
    from picasapy.app.edit_controller import EditController

    return EditController(provider)


@pytest.fixture
def photo(tmp_path):
    return make_jpeg(tmp_path / "IMG_0001.jpg", size=(8, 6))

def _hozzaad(controller, content: str, x: float, y: float) -> None:
    controller.enterTextTool()
    controller.setTextDraft(content)
    controller.previewNewTextPlacement(x, y)
    controller.applyText()


def test_ket_felirat_hozzaadhato_es_iniben_round_trip(controller, photo):
    controller.beginEdit("1", str(photo))
    _hozzaad(controller, "Első doboz", 0.2, 0.3)
    _hozzaad(controller, "Második doboz", 0.7, 0.8)

    raw = next(
        line.removeprefix("text=")
        for line in (photo.parent / ".picasa.ini").read_text(encoding="utf-8").splitlines()
        if line.startswith("text=")
    )
    overlay = parse_text(raw)

    assert [block.content for block in overlay.blocks] == [
        "Első doboz",
        "Második doboz",
    ]
    assert overlay.blocks[0].geometry.x == 0.2
    assert overlay.blocks[1].geometry.x == 0.7


def test_elonezeti_spec_minden_mentett_feliratot_tartalmaz(controller, photo):
    controller.beginEdit("1", str(photo))
    _hozzaad(controller, "Első doboz", 0.2, 0.3)
    _hozzaad(controller, "Második doboz", 0.7, 0.8)

    specs = controller._current_text_spec()

    assert isinstance(specs, tuple)
    assert [spec.content for spec in specs] == ["Első doboz", "Második doboz"]


def test_elonezeti_szolgaltato_minden_feliratot_megrajzol(
    controller, provider, photo, monkeypatch
):
    from picasapy.app import edit_preview

    controller.beginEdit("1", str(photo))
    _hozzaad(controller, "Első doboz", 0.2, 0.3)
    _hozzaad(controller, "Második doboz", 0.7, 0.8)
    drawn = []

    def track_draw(image, content, x, y, **_style):
        drawn.append(content)
        return image

    monkeypatch.setattr(edit_preview, "apply_text_overlay", track_draw)
    provider.register("1", photo, (), text=controller._current_text_spec())
    assert not provider.requestImage("1", None, None).isNull()

    assert drawn == ["Első doboz", "Második doboz"]
