"""A `qml_app` lebontása tényleg elengedi a QML-motort (#4871).

A `deleteLater()` esemény-ciklus nélkül (pytest) a `processEvents()`-től NEM
fut le: a `DeferredDelete`-et külön ki kell küldeni. Enélkül minden teszt
~88 MB-ot hagyott maga után, és a 24 tesztes fájl elérte a memóriaplafont.
"""

from __future__ import annotations

from tests.app.qml_functional.conftest import _build_qml_app


def test_a_lebontas_utan_a_qml_motor_megsemmisul(qt_app, tmp_path):
    kiepitett = _build_qml_app(qt_app, tmp_path)
    _window, _controller, engine = next(kiepitett)
    megsemmisult = []
    engine.destroyed.connect(lambda *_: megsemmisult.append(True))

    try:
        next(kiepitett)
    except StopIteration:
        pass

    assert megsemmisult, "a motor a fixture lebontása után is él (deleteLater nem fut)"
