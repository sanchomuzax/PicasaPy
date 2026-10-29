"""A személyalbum javaslatállapota önálló QML-komponens (#6136)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml"
_MAIN = _QML / "Main.qml"
_COMPONENT = _QML / "PicasaPy/MainPeopleAlbumState.qml"
_QMLDIR = _QML / "PicasaPy/qmldir"


def test_a_szemelyalbum_allapot_onallo_kisebb_800_soros_komponens():
    assert _COMPONENT.is_file(), "hiányzik a MainPeopleAlbumState.qml"
    assert len(_COMPONENT.read_text(encoding="utf-8").splitlines()) < 800
    assert "MainPeopleAlbumState 1.0 MainPeopleAlbumState.qml" in (
        _QMLDIR.read_text(encoding="utf-8")
    )


def test_a_foablak_megtartja_a_neveket_es_a_gazdaatadast():
    main = _MAIN.read_text(encoding="utf-8")
    component = _COMPONENT.read_text(encoding="utf-8")

    assert re.search(
        r"MainPeopleAlbumState\s*\{\s*id:\s*mainPeopleAlbumState", main, re.DOTALL
    )
    for name in (
        "hostWindow",
        "hostController",
        "hostFaceScanController",
        "hostRemovePeopleFacesDialog",
        "hostCreateDialogs",
    ):
        assert re.search(rf"required\s+property\s+var\s+{name}\b", component)
    assert "hostFaceScanController: typeof faceScanController !== \"undefined\"" in main

    for name in (
        "_javaslatRevizio",
        "personAlbumName",
        "personAlbumAvatarUrl",
        "personAlbumCanRemoveSelection",
        "personAlbumCanSetThumbnail",
        "personSuggestionCount",
        "personSelectedSuggestionIds",
        "personSuggestionsOnly",
        "personFaceZoom",
    ):
        assert re.search(rf"property\s+(?:alias|(?:string|bool|int|var))\s+{name}\b", main)
    for name in (
        "removePersonAlbumSelection",
        "setPersonAlbumThumbnailFromSelection",
        "openPersonAlbumMovie",
        "openPeopleAlbumsMovie",
        "selectPersonSuggestions",
        "confirmPersonSuggestions",
        "removePersonSuggestions",
        "setPersonSuggestionsOnly",
        "setPersonFaceZoom",
        "findMoreSuggestions",
        "_javaslatFrissult",
    ):
        assert re.search(rf"function\s+{name}\s*\(", main)
