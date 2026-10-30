"""A főablak QML-családjának minden darabja maradjon 800 sor alatt (#6136)."""

from pathlib import Path


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_DIALOG_STACK = _QML / "PicasaPy/MainWindowDialogStack.qml"
_PERIPHERAL_LAYERS = _QML / "PicasaPy/MainWindowPeripheralLayers.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_main_qml_es_kiemelt_reszei_800_sor_alatt_maradnak():
    fajlok = (_QML / "Main.qml", *sorted((_QML / "PicasaPy").glob("Main*.qml")))
    tulhosszu = {
        fajl.relative_to(_QML).as_posix(): len(fajl.read_text(encoding="utf-8").splitlines())
        for fajl in fajlok
        if len(fajl.read_text(encoding="utf-8").splitlines()) >= 800
    }

    assert not tulhosszu, f"A 800 soros QML-plafont átlépő fájlok: {tulhosszu}"


def test_a_foablak_parbeszedretege_onallo_es_regisztralt():
    assert _DIALOG_STACK.is_file(), "hiányzik a MainWindowDialogStack.qml"
    assert len(_DIALOG_STACK.read_text(encoding="utf-8").splitlines()) < 800
    assert _PERIPHERAL_LAYERS.is_file(), "hiányzik a MainWindowPeripheralLayers.qml"
    qmldir = _QMLDIR.read_text(encoding="utf-8")
    for nev in (
        "MainWindowDialogStack",
        "MainWindowCommands",
        "MainWindowWorkspace",
        "MainWindowPeripheralLayers",
        "MainWindowLibraryActions",
    ):
        assert f"{nev} 1.0 {nev}.qml" in qmldir
    main = (_QML / "Main.qml").read_text(encoding="utf-8")
    reteg = _PERIPHERAL_LAYERS.read_text(encoding="utf-8")
    assert "MainWindowPeripheralLayers {" in main
    assert "MainWindowDialogStack {" in reteg
    assert "id: mainWindowDialogStack" in reteg
