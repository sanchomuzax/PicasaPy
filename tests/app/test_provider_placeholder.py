"""#151/7: a placeholder-szín egyetlen helyen definiált — a két provider
(thumbnail, edit-előnézet) ugyanazt a konstanst használja."""

from picasapy.app import edit_preview, thumbnail_provider


def test_placeholder_color_shared():
    assert (
        edit_preview._PLACEHOLDER_COLOR is thumbnail_provider.PLACEHOLDER_COLOR
    )
