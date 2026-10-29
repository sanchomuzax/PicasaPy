"""A filmelőnézet időzített átmenete a komponenshatáron át is bekötött (#6205)."""

from tests.app.qml_functional.test_kotesi_hurok_minden_parbeszed_1748 import (
    _KOTELEZO_VALTOZATOK,
)
from tests.support.create_dialogs_components_6051 import create_dialogs_sources


def test_film_elo_nezeti_atmenet_explicit_bekotese_a_preview_komponensbe():
    sources = create_dialogs_sources()
    preview = sources["MovieMakerPreview.qml"]
    dialog = sources["MovieMakerDialog.qml"]

    assert "required property var moviePreviewTransition" in preview
    assert "&& root.moviePreviewTransition.running" in preview
    assert "&& moviePreviewTransition.running" not in preview
    assert "moviePreviewTransition: moviePreviewRuntime.transition" in dialog
    assert "required property var moviePreviewMusicLoader" in preview
    assert "if (root.moviePreviewMusicLoader.item)" in preview
    assert "root.moviePreviewMusicLoader.item.volume = value / 1000" in preview
    assert "moviePreviewMusicLoader: moviePreviewRuntime.musicLoader" in dialog

    preview_valtozat = " ".join(_KOTELEZO_VALTOZATOK["MovieMakerPreview"])
    assert "moviePreviewMusicLoader: ({})" in preview_valtozat
    assert "moviePreviewTransition: ({})" in preview_valtozat
