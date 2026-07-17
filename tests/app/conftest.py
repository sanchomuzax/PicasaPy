"""Qt tesztkörnyezet: offscreen platform, egyetlen alkalmazás-példány."""

import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")


@pytest.fixture(scope="session")
def qt_app():
    from PySide6.QtGui import QGuiApplication

    app = QGuiApplication.instance() or QGuiApplication([])
    yield app
