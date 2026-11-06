"""A QML image provider Python-burka élje túl az engine-t (#6625)."""

import gc
import weakref

import shiboken6
from PySide6.QtCore import QCoreApplication, QEvent, QObject
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


def test_engine_lebontasa_nem_torol_mas_fuggoben_levo_qt_objektumot(qt_app):
    engine = QQmlApplicationEngine()
    unrelated = QObject(qt_app)
    unrelated.deleteLater()

    try:
        _destroy_qml_engine(engine, qt_app)

        assert shiboken6.isValid(unrelated), (
            "a QML-engine lebontása csak a saját DeferredDelete eseményét "
            "kézbesítheti"
        )
    finally:
        if shiboken6.isValid(unrelated):
            unrelated.deleteLater()
            QCoreApplication.sendPostedEvents(
                unrelated, QEvent.Type.DeferredDelete
            )
