"""A QML image provider Python-burka élje túl az engine-t (#6625)."""

import gc
import weakref

from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickImageProvider

from picasapy.app.application_startup_qml import (
    _destroy_qml_engine,
    _register_image_provider,
)


def test_provider_python_hivatkozasa_a_motor_torlese_utan_szabadul_fel(qt_app):
    sorrend = []
    engine = QQmlApplicationEngine()
    engine.destroyed.connect(lambda *_: sorrend.append("engine"))

    class ProbeProvider(QQuickImageProvider):
        def __init__(self):
            super().__init__(QQuickImageProvider.ImageType.Image)

        def __del__(self):
            sorrend.append("provider")

    provider = ProbeProvider()
    provider_ref = weakref.ref(provider)
    _register_image_provider(engine, "lifetimeprobe", provider)
    del provider
    gc.collect()
    assert provider_ref() is not None, "a provider-burok nem maradt életben az engine mellett"

    _destroy_qml_engine(engine, qt_app)
    gc.collect()

    assert sorrend == ["engine", "provider"], (
        "a provider Python-burka csak az engine tényleges megszűnése után "
        f"szabadulhat fel: {sorrend}"
    )
    assert provider_ref() is None
