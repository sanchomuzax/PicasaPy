"""A #4615 szövegdia-animációi a film kimeneti képkockáin."""

import numpy as np

from picasapy.movie import slideshow
from picasapy.movie.slideshow import MovieSettings, export_movie, render_text_slide


def _export_text_slide(monkeypatch, tmp_path, slide):
    class Writer:
        def __init__(self):
            self.frames = []

        def isOpened(self):
            return True

        def write(self, frame):
            self.frames.append(frame.copy())

        def release(self):
            pass

    writer = Writer()
    monkeypatch.setattr(slideshow.cv2, "VideoWriter", lambda *args: writer)
    settings = MovieSettings(
        width=320,
        height=180,
        fps=10,
        seconds_per_photo=2.0,
        transition_seconds=0.5,
        text_slides=(slide,),
    )
    report = export_movie(
        [tmp_path / "nincs.jpg"],
        tmp_path / "film.mp4",
        settings,
    )
    assert report.frames == settings.frames_per_photo - settings.transition_frames
    assert len(writer.frames) == report.frames
    return writer.frames, settings


def test_fade_move_text_slides_change_in_the_exported_frames(monkeypatch, tmp_path):
    for style in (1, 8):
        frames, _ = _export_text_slide(
            monkeypatch,
            tmp_path,
            {
                "text": "Szöveges dia",
                "font": "DejaVuSans",
                "size": 36,
                "style": style,
                "textColor": "#ffffff",
                "backgroundColor": "#123456",
            },
        )

        assert not np.array_equal(frames[0], frames[-1]), (
            f"a {style} stílus képkockái változatlanok maradtak"
        )
        assert np.array_equal(frames[0][0, 0], frames[-1][0, 0])


def test_typewriter_uses_utf8_bytes_without_drawing_a_partial_character(
    monkeypatch, tmp_path
):
    slide = {
        "text": "Á",
        "font": "DejaVuSans",
        "size": 36,
        "style": 11,
        "textColor": "#ffffff",
        "backgroundColor": "#123456",
    }
    frames, settings = _export_text_slide(monkeypatch, tmp_path, slide)
    ures = render_text_slide(
        {**slide, "text": ""},
        settings,
    )

    # Az első UTF-8 bájt még nem alkot rajzolható ékezetes karaktert.
    assert all(np.array_equal(frame, ures) for frame in frames[:4])
    assert not np.array_equal(frames[4], ures)
    assert not np.array_equal(frames[-1], ures)
