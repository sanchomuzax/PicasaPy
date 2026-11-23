"""A szerkesztő állapotsora effektparancs után mappa és számláló nélküli rövid alakra váltson (#7390).

A jegy követelményei:
- Alaphelyzet / képváltás után hosszú alak: `folder > name   datum   felbontas   meret   (szamlalo)`.
- Sepia csempekattintás után a sáv rövid alakú mappa és számláló nélkül: `name   datum   felbontas   meret`.
- Undo után újra a hosszú alak.
- Redo után a hosszú alak.
- Soft Focus panel nyitásakor még a hosszú alak.
- Soft Focus Mégse / Escape után a rövid alak.
- QML-szinten a TrayInfoBar szövege reaktívan követi az állapotot.
"""

from __future__ import annotations

from pathlib import Path
import pytest

from picasapy.app.controller import AppController
from picasapy.app.edit_controller import EditController
from picasapy.app.edit_preview import EditPreviewProvider
from picasapy.app.thumbnail_provider import ThumbnailProvider
from picasapy.index import open_index, sync_tree
from picasapy.thumbs import ThumbnailCache
from support.jpeg_factory import make_jpeg
from support.varakozas import var_feltetelre


@pytest.fixture
def test_env(tmp_path: Path):
    lib = tmp_path / "PicasaTeszt"
    lib.mkdir()
    make_jpeg(lib / "color_patches.jpg", size=(800, 800))
    make_jpeg(lib / "second_photo.jpg", size=(640, 480))
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, lib)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    controller = AppController(db, (str(lib),), provider)
    controller.selectFolder(str(lib))

    edit_preview = EditPreviewProvider()
    edit_controller = EditController(edit_preview)
    controller.set_edit_controllers(edit_controller)
    from picasapy.app.application_startup_controllers import kosd_be_az_allapotsor_alakjat

    kosd_be_az_allapotsor_alakjat(controller, edit_controller)

    photo_path = str(lib / "color_patches.jpg")
    photo_id = controller.photos.idAt(0)
    edit_controller.beginEdit(photo_id, photo_path)

    return controller, edit_controller, str(lib)


def test_viewer_info_alaphelyzetben_hosszu_alak(test_env):
    controller, edit_controller, lib_path = test_env
    info = controller.viewerInfo(0)
    assert info.startswith("PicasaTeszt > color_patches.jpg")
    assert "(1 / 2)" in info
    assert "800x800" in info or "800×800" in info


def test_viewer_info_effekt_utan_rovid_alak(test_env):
    controller, edit_controller, lib_path = test_env
    edit_controller.applyEffect("sepia")
    info = controller.viewerInfo(0)
    assert not info.startswith("PicasaTeszt > ")
    assert info.startswith("color_patches.jpg")
    assert "(" not in info
    assert "800x800" in info or "800×800" in info


def test_viewer_info_undo_utan_visszater_hosszu_alakra(test_env):
    controller, edit_controller, lib_path = test_env
    edit_controller.applyEffect("sepia")
    assert not controller.viewerInfo(0).startswith("PicasaTeszt > ")

    edit_controller.undo()
    info = controller.viewerInfo(0)
    assert info.startswith("PicasaTeszt > color_patches.jpg")
    assert "(1 / 2)" in info


def test_viewer_info_redo_utan_hosszu_alak(test_env):
    controller, edit_controller, lib_path = test_env
    edit_controller.applyEffect("sepia")
    edit_controller.undo()
    assert controller.viewerInfo(0).startswith("PicasaTeszt > color_patches.jpg")

    edit_controller.redo()
    info = controller.viewerInfo(0)
    assert info.startswith("PicasaTeszt > color_patches.jpg")
    assert "(1 / 2)" in info


def test_viewer_info_megse_utan_rovid_alak(test_env):
    controller, edit_controller, lib_path = test_env
    # Kiindulás: hosszú alak
    assert controller.viewerInfo(0).startswith("PicasaTeszt > color_patches.jpg")

    # Mégse (discardEffectPreview) után: rövid alak
    edit_controller.discardEffectPreview()
    info = controller.viewerInfo(0)
    assert not info.startswith("PicasaTeszt > ")
    assert info.startswith("color_patches.jpg")
    assert "(" not in info


def test_viewer_info_paneles_alkalmaz_utan_rovid_alak(test_env):
    controller, edit_controller, lib_path = test_env
    edit_controller.applyEffectWithParams("radblur", [50.0])
    info = controller.viewerInfo(0)
    assert not info.startswith("PicasaTeszt > ")
    assert info.startswith("color_patches.jpg")
    assert "(" not in info


def test_viewer_info_kepvaltas_utan_hosszu_alak(test_env):
    controller, edit_controller, lib_path = test_env
    edit_controller.applyEffect("sepia")
    assert not controller.viewerInfo(0).startswith("PicasaTeszt > ")

    # Képváltás a második képre
    second_path = str(Path(lib_path) / "second_photo.jpg")
    second_id = controller.photos.idAt(1)
    edit_controller.beginEdit(second_id, second_path)

    info = controller.viewerInfo(1)
    assert info.startswith("PicasaTeszt > second_photo.jpg")
    assert "(2 / 2)" in info


def test_viewer_info_short_property_es_signal(test_env):
    controller, edit_controller, lib_path = test_env
    valtozott = []
    controller.viewerInfoShortChanged.connect(lambda v: valtozott.append(v))

    assert controller.viewerInfoShort is False
    controller.viewerInfoShort = True
    assert controller.viewerInfoShort is True
    assert valtozott == [True]

    controller.setViewerInfoShort(False)
    assert controller.viewerInfoShort is False
    assert valtozott == [True, False]


def _sav_szovege(window):
    def bejar(item):
        for child in item.childItems():
            yield child
            yield from bejar(child)
    for elem in bejar(window.contentItem()):
        if elem.objectName() == "trayInfoText":
            return str(elem.property("text"))
    raise AssertionError("trayInfoText not found")


def test_qml_tray_info_bar_koveti_az_effekt_allapotot(qml_app, qt_app):
    """QML-szintű integrációs teszt: a TrayInfoBar szövege reaktívan vált."""
    window, controller, _lib, _engine = qml_app
    window.openPhotoViewer(0)
    assert var_feltetelre(qt_app, lambda: _sav_szovege(window) != "", 5.0), "A sáv szövege nem épült fel"

    # 1. Alaphelyzet: hosszú alak (benne van a mappa és a számláló)
    sav = _sav_szovege(window)
    assert "kepek > " in sav or "kepek" in sav
    assert "(" in sav

    # 2. Effekt beállítása (rövid alak):
    controller.setViewerInfoShort(True)
    assert var_feltetelre(qt_app, lambda: "kepek > " not in _sav_szovege(window), 5.0)
    sav = _sav_szovege(window)
    assert "(" not in sav
    assert "a.jpg" in sav

    # 3. Undo / képváltás (hosszú alak vissza):
    controller.setViewerInfoShort(False)
    assert var_feltetelre(qt_app, lambda: "kepek > " in _sav_szovege(window) or "kepek" in _sav_szovege(window), 5.0)
    sav = _sav_szovege(window)
    assert "(" in sav
