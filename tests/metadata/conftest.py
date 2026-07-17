"""Metadata-tesztek fixture-jei — a JPEG-gyár a tests/support alatt él."""

import pytest

from support.jpeg_factory import make_jpeg

__all__ = ["make_jpeg"]


@pytest.fixture
def jpeg_factory(tmp_path):
    def _make(name="kep.jpg", **kwargs):
        return make_jpeg(tmp_path / name, **kwargs)

    return _make
