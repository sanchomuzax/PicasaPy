"""#7131: a képmenük közvetlenül adnak hozzá, a többi út marad megerősített."""

from pathlib import Path

import picasapy.app

_QML = Path(picasapy.app.__file__).parent / "qml" / "PicasaPy"


def _forras(fajl: str) -> str:
    return (_QML / fajl).read_text(encoding="utf-8")


def test_a_fotomenuk_azonnal_adnak_a_kezpernyovedohoz_es_a_menuut_megerosit(
):
    foto = _forras("MainPhotoContextMenu.qml")
    nezo = _forras("PhotoViewerContextActions.qml")
    menu = _forras("MainMenuBar.qml")
    talca = _forras("MainTrayBar.qml")

    assert (
        "onScreensaverRequested:\n"
        "        hostWindow.addPhotosToScreensaver(" in foto
    )
    assert "hostWindow.photoActionPaths())" in foto
    assert "viewer.appWindow.addPhotosToScreensaver(" in nezo
    assert "viewer.appWindow.photoActionPaths())" in nezo
    assert "onAddToScreensaverRequested: hostWindow.requestAddToScreensaver()" in menu
    assert "onAddSelectedToScreensaverRequested: hostWindow.requestAddToScreensaver()" in talca


def test_a_talca_uj_album_ma_datummal_indul_es_a_fotomenus_datumkulon_marad():
    talca = _forras("MainTrayBar.qml")
    dialogusok = _forras("FileOpsDialogs.qml")
    foto = _forras("MainPhotoContextMenu.qml")

    assert 'Qt.formatDate(new Date(), "yyyy-MM-dd")' in talca
    assert "openNewAlbumProperties(controller.currentFolder, rows)" in dialogusok
    assert "openAddToNewAlbum(hostWindow.selectedRows())" in foto
