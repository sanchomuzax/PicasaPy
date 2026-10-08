"""#4616: a film uses the Picasa caption before the embedded EXIF description."""

# rontás-kontroll: picasapy.movie.slideshow.PICASA_INI_NAME = "missing.ini" → 1 failed

from PIL import Image, ImageDraw

from picasapy.movie import slideshow
from picasapy.movie.slideshow import MovieSettings, export_movie


def _write_photo(path, description):
    image = Image.new("RGB", (160, 90), (200, 100, 50))
    exif = Image.Exif()
    exif[270] = description
    image.save(path, format="JPEG", exif=exif)
    return path


def _render_caption(monkeypatch, photo, ini_text=None):
    if ini_text is not None:
        (photo.parent / ".picasa.ini").write_text(ini_text, encoding="utf-8")

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
    rendered_text = []
    with monkeypatch.context() as scoped:
        scoped.setattr(slideshow.cv2, "VideoWriter", lambda *args: writer)
        original_multiline_text = ImageDraw.ImageDraw.multiline_text

        def capture_multiline_text(draw, xy, text, *args, **kwargs):
            rendered_text.append(text)
            return original_multiline_text(draw, xy, text, *args, **kwargs)

        scoped.setattr(
            ImageDraw.ImageDraw, "multiline_text", capture_multiline_text
        )
        report = export_movie(
            [photo],
            photo.parent / "film.mp4",
            MovieSettings(
                width=160,
                height=90,
                fps=1,
                seconds_per_photo=1,
                transition_seconds=0,
                show_captions=True,
            ),
        )
    assert report.frames == 1
    assert len(writer.frames) == 1
    return writer.frames[0], rendered_text


def test_movie_uses_picasa_caption_and_falls_back_to_exif_description(
    tmp_path, monkeypatch
):
    photo = _write_photo(tmp_path / "photo.jpg", "EXIF description")

    frame, rendered_text = _render_caption(
        monkeypatch,
        photo,
        "[photo.jpg]\ncaption=Picasa caption\n",
    )

    assert "Picasa caption" in rendered_text
    assert "EXIF description" not in rendered_text
    # A szöveg nélküli, jobb alsó sarokban csak a feliratsáv sötétítése látszik.
    assert (frame[-1, -1] < (50, 100, 200)).all()

    frame, rendered_text = _render_caption(
        monkeypatch,
        photo,
        "[photo.jpg]\ncaption=\n",
    )

    assert "EXIF description" in rendered_text
    assert (frame[-1, -1] < (50, 100, 200)).all()

    (tmp_path / ".picasa.ini").unlink()
    frame, rendered_text = _render_caption(monkeypatch, photo)

    assert "EXIF description" in rendered_text
    assert (frame[-1, -1] < (50, 100, 200)).all()
