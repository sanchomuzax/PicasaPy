"""#5955: a főablak megerősítő párbeszédei külön komponensben maradnak."""

from pathlib import Path
import re


_GYOKER = Path(__file__).resolve().parents[1]
_MAIN = _GYOKER / "src/picasapy/app/qml/Main.qml"
_DIALOGS = _GYOKER / "src/picasapy/app/qml/PicasaPy/MainDialogs.qml"
_QMLDIR = _GYOKER / "src/picasapy/app/qml/PicasaPy/qmldir"


def test_foablak_megerositesei_komponensben_maradnak_az_azonositoikkal():
    main = _MAIN.read_text(encoding="utf-8")
    assert _DIALOGS.is_file(), "hiányzik a MainDialogs.qml komponens"
    dialogs = _DIALOGS.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert re.search(r"^MainDialogs 1\.0 MainDialogs\.qml$", qmldir, re.MULTILINE)
    assert re.search(r"^    MainDialogs\s*\{\n        id: mainDialogs", main, re.MULTILINE)
    for identifier in (
        "clearGeotagDialog",
        "bulkTagConfirmLoader",
        "setGeotagDialog",
        "dropGeotagDialog",
        "panelClearGeotagDialog",
        "undoAllEditsDialog",
        "languageConfirmDialog",
    ):
        assert not re.search(r"^\s*id: " + identifier + r"\s*$", main, re.MULTILINE), (
            f"a(z) {identifier} párbeszéd még a Main.qml-ben van"
        )
    for object_name in (
        "clearGeotagDialogLoader",
        "bulkTagConfirmDialogLoader",
        "bulkTagConfirmDialog",
        "setGeotagDialogLoader",
        "dropGeotagDialogLoader",
        "dropGeotagConfirm",
        "panelClearGeotagDialogLoader",
        "undoAllEditsDialogLoader",
        "undoAllEditsDialog",
        "menuLanguageConfirmDialogLoader",
        "menuLanguageConfirmDialog",
    ):
        assert f'objectName: "{object_name}"' in dialogs, (
            f"hiányzik a megőrzendő objectName: {object_name}"
        )
