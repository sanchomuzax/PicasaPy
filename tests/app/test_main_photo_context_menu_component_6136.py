"""A rács fotó-helyi menüjének gazda-bekötése önálló komponens (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainPhotoContextMenu.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_foto_helyi_menu_gazdakomponense_regisztralt_es_800_sor_alatti():
    assert _COMPONENT.is_file(), "hiányzik a MainPhotoContextMenu.qml"
    component = _COMPONENT.read_text(encoding="utf-8")
    qmldir = _QMLDIR.read_text(encoding="utf-8")

    assert len(component.splitlines()) < 800
    assert re.search(r"^PhotoContextMenu\s*\{", component, re.MULTILINE)
    assert "MainPhotoContextMenu 1.0 MainPhotoContextMenu.qml" in qmldir


def test_a_foablak_megtartja_a_fotomenunevet_es_atadja_a_gazdakat():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")

    assert re.search(
        r"MainPhotoContextMenu\s*\{\s*id:\s*photoContextMenu", main, re.DOTALL
    )
    for name in (
        "hostWindow",
        "hostController",
        "hostFileOpsController",
        "hostFileOpsDialogs",
        "hostMainDialogs",
        "hostMoveToNewPersonDialog",
        "hostOpenWithDialog",
        "hostRemoveFromAlbumDialog",
        "hostRemovePeopleFacesDialog",
        "hostSaveDialogs",
        "hostToolbar",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component), (
            f"hiányzó kötelező gazdatulajdonság: {name}"
        )
    assert 'objectName: "photoContextMenu"' in (
        (_QML / "PicasaPy/PhotoContextMenu.qml").read_text(encoding="utf-8")
    )
    assert "typeof fileOpsController !== \"undefined\"" in main


# rontás-kontroll: a MainPhotoContextMenu-regisztráció eltávolítva → piros.
