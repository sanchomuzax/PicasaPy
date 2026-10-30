"""A könyvtári főnézet elrendezése önálló QML-komponensben él (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainLibraryWorkspace.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_konyvtari_munkaterulet_regisztralt_800_sor_alatti_komponens():
    assert _COMPONENT.is_file(), "hiányzik a MainLibraryWorkspace.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800
    assert "MainLibraryWorkspace 1.0 MainLibraryWorkspace.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )


def test_a_foablak_megtartja_a_konyvtari_objektumneveket():
    main = _MAIN.read_text(encoding="utf-8")
    assert re.search(
        r"MainLibraryWorkspace\s*\{\s*id:\s*mainLibraryWorkspace",
        main,
        re.DOTALL,
    )
    for nev in (
        "documentTabStrip",
        "mainSplit",
        "folderPane",
        "mainLibraryCanvas",
        "jobbFiok",
        "jobbFiokFogo",
        "peoplePanel",
    ):
        assert re.search(rf"property\s+alias\s+{nev}\s*:", main), (
            f"eltűnt vagy nem alias a főablak {nev} neve"
        )


def test_a_komponens_kotelezoen_kapja_a_gazdaobjektumokat_es_a_forditott_cimeket():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")
    for nev in (
        "hostWindow",
        "hostController",
        "hostToolbar",
        "hostPhotoViewer",
        "hostMainDialogs",
        "hostBackupHost",
        "hostGiftCdHost",
        "hostSearchSuggestionsBox",
        "hostCollectionPasswordDialog",
        "hostFileOpsDialogs",
        "hostFileOpsController",
        "hostFaceScanController",
        "hostFolderHierarchyController",
    ):
        assert re.search(rf"required\s+property\s+var\s+{nev}\b", component), (
            f"hiányzó kötelező gazdatulajdonság: {nev}"
        )
    for nev, szoveg in (
        ("propertiesLabel", "Properties"),
        ("tagsLabel", "Tags:"),
        ("peopleLabel", "People"),
        ("placesLabel", "Places"),
    ):
        assert re.search(rf"required\s+property\s+string\s+{nev}\b", component)
        assert f'{nev}: qsTr("{szoveg}")' in main
    assert 'typeof fileOpsController !== "undefined"' in main
    assert 'typeof faceScanController !== "undefined"' in main
    assert 'typeof folderHierarchyController !== "undefined"' in main
    assert "qsTr(" not in component, "a fordítási kontextusnak Main.qml-ben kell maradnia"
