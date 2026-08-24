"""A Névtelenek nézet a valódi arcvezérlőt kapja, kötési hurok nélkül (#1236)."""

from PySide6.QtCore import QObject, qInstallMessageHandler

from support.qml_warning_filter import is_qml_script_error


def test_a_nevtelenek_nezet_vezerloje_nem_hurkol(request, qt_app):
    """A figyelőt a Main.qml betöltése ELŐTT telepíti, majd a kötést is méri."""
    hurkok: list[str] = []
    qml_hibak: list[str] = []

    def kezelo(_tipus, _ctx, uzenet):
        if "Binding loop" in uzenet and "faceScanController" in uzenet:
            hurkok.append(uzenet)
        if is_qml_script_error(uzenet):
            qml_hibak.append(uzenet)

    elozo = qInstallMessageHandler(kezelo)
    try:
        window, _controller, engine = request.getfixturevalue("qml_app")
        qt_app.processEvents()
    finally:
        qInstallMessageHandler(elozo)

    nezet = window.findChild(QObject, "unnamedFacesView")
    assert nezet is not None
    kontextus_vezerlo = engine.rootContext().contextProperty("faceScanController")
    assert nezet.property("faceScanController") == kontextus_vezerlo
    assert not hurkok, "a faceScanController kötése önmagára hivatkozik"
    assert not qml_hibak, "QML-szkripthiba a vezérlőkötés betöltésekor:\n" + "\n".join(
        qml_hibak
    )
