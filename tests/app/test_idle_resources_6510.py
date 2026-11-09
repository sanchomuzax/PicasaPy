"""A főablak tétlen állapotában ne maradjon ciklikus QML-munka (#6510)."""

import time

from PySide6.QtCore import QObject, QTimer


def _qml_property_names(obj: QObject) -> set[str]:
    meta = obj.metaObject()
    return {
        meta.property(index).name()
        for index in range(meta.propertyCount())
    }


def _cyclic_idle_work(window: QObject) -> list[str]:
    violations = []
    for item in (window, *window.findChildren(QObject)):
        class_name = item.metaObject().className()
        if isinstance(item, QTimer) and item.isActive() and not item.isSingleShot():
            violations.append("QTimer: ismétlődő Timer fut")
            continue
        properties = _qml_property_names(item)
        if "running" not in properties or not item.property("running"):
            continue
        if "repeat" in properties and item.property("repeat"):
            violations.append(f"{class_name}: ismétlődő Timer fut")
        elif "Animation" in class_name:
            violations.append(f"{class_name}: animáció fut")
    return violations


def test_tetlen_foablakban_nincs_futo_ciklikus_qml_munka(qml_app, qt_app):
    window, _controller, _library, _engine = qml_app

    # Az induláskori véges áttűnések és egyszeri halasztások fussanak le;
    # a határidő védi a lassabb CI-t is.
    deadline = time.monotonic() + 3.0
    while time.monotonic() < deadline:
        qt_app.processEvents()
        time.sleep(0.01)

    violations = _cyclic_idle_work(window)

    assert not violations, "Tétlen főablakban aktív ciklikus QML-munka: " + "; ".join(violations)


def test_az_or_felismeri_a_futo_ismetlodo_qtimert(qml_app):
    window, _controller, _library, _engine = qml_app
    timer = QTimer(window)
    timer.setInterval(100)
    timer.start()

    try:
        violations = _cyclic_idle_work(window)
        assert any("QTimer: ismétlődő Timer fut" in item for item in violations)
    finally:
        timer.stop()


def test_a_szurt_belyegkep_memoriakerete_legfeljebb_16_mib():
    from picasapy.app.thumbnail_provider_constants import _FILTERED_MEMO_CAPACITY

    # A korlát bájtban számol; a bélyegkép mérete és a DPR nem skálázza.
    assert _FILTERED_MEMO_CAPACITY == 16 * 1024**2
