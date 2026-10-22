"""A feltöltési címkék a három tényleges helyi menüben (#5519)."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QObject, QUrl
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickWindow

from tests.support.varakozas import var_feltetelre

_KEEPALIVE: list[object] = []
_FELIRAT = "Upload to &Picasa Web Albums..."


def _menu_preview(engine: QQmlEngine):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Controls
import QtQuick.Window
import PicasaPy 1.0

Window {
    objectName: "menuPreview"
    visible: true
    width: 1200
    height: 500
    color: "#e5e5e5"

    FolderContextMenu {
        objectName: "folderContextMenu"
        popupType: Popup.Window
        x: 20
        y: 20
    }
    PhotoContextMenu {
        objectName: "photoContextMenu"
        popupType: Popup.Window
        x: 420
        y: 20
    }
    AlbumContextMenu {
        objectName: "albumContextMenu"
        popupType: Popup.Window
        x: 820
        y: 20
    }
}
""",
        QUrl(),
    )
    root = component.create()
    assert root is not None, component.errorString()
    assert component.status() == QQmlComponent.Status.Ready, component.errorString()
    QQmlEngine.setObjectOwnership(root, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.extend((component, root))
    return root


def _menu_item(menu: QObject, name: str) -> QObject | None:
    return menu.findChild(QObject, name)


def _grab_menu(qt_app, menu: QObject, item: QObject) -> QImage:
    menu.open()
    assert var_feltetelre(qt_app, lambda: bool(menu.property("visible")), 3.0)
    assert var_feltetelre(qt_app, lambda: bool(item.property("visible")), 3.0)
    window = item.window()
    assert isinstance(window, QQuickWindow)
    qt_app.processEvents()
    image = window.grabWindow()
    assert not image.isNull(), f"{item.objectName()} menüablaka üres képet adott"
    menu.close()
    qt_app.processEvents()
    return image


def _save_menu_sheet(images: list[QImage], target: Path) -> None:
    gap = 16
    width = sum(image.width() for image in images) + gap * (len(images) - 1)
    height = max(image.height() for image in images)
    sheet = QImage(width, height, QImage.Format.Format_ARGB32_Premultiplied)
    sheet.fill("#e5e5e5")
    painter = QPainter(sheet)
    x = 0
    for image in images:
        painter.drawImage(x, 0, image)
        x += image.width() + gap
    painter.end()
    target.parent.mkdir(parents=True, exist_ok=True)
    assert sheet.save(str(target), "PNG"), f"nem menthető a menükép: {target}"


def test_harom_helyi_menu_feltoltesi_tetele_es_kep(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    root = _menu_preview(engine)
    menuk = [
        (
            root.findChild(QObject, "folderContextMenu"),
            "folderMenuUploadToGooglePhotos",
            "Upload to Google &Photos...",
        ),
        (
            root.findChild(QObject, "photoContextMenu"),
            "contextMenuUploadToWebAlbums",
            _FELIRAT,
        ),
        (
            root.findChild(QObject, "albumContextMenu"),
            "albumMenuUploadToGooglePhotos",
            "Upload to Google &Photos...",
        ),
    ]
    assert all(menu is not None for menu, _, _ in menuk)

    hibak: list[str] = []
    images: list[QImage] = []
    for menu, item_name, expected_text in menuk:
        assert menu is not None
        item = _menu_item(menu, item_name)
        if item is None:
            hibak.append(f"{item_name}: hiányzik")
            continue
        actual_text = item.property("text")
        if actual_text != expected_text:
            hibak.append(f"{item_name}: {actual_text!r} != {expected_text!r}")
        if item.property("retired") is not True:
            hibak.append(f"{item_name}: a retired jelölés hiányzik")
        prefix = {
            "folderContextMenu": "folderMenuUploadTo",
            "photoContextMenu": "contextMenuUploadTo",
            "albumContextMenu": "albumMenuUploadTo",
        }[menu.objectName()]
        upload_to_items = [
            child
            for child in menu.findChildren(QObject)
            if child.objectName().startswith(prefix)
        ]
        if len(upload_to_items) != 1:
            hibak.append(
                f"{menu.objectName()}: {len(upload_to_items)} Upload to tétel van"
            )
        if menu.objectName() == "albumContextMenu" and _menu_item(
            menu, "albumMenuUploadToWebAlbums"
        ) is not None:
            hibak.append("az albummenüben megmaradt a második Web Albums tétel")
        images.append(_grab_menu(qt_app, menu, item))

    assert not hibak, "\n".join(hibak)
    _save_menu_sheet(images, Path(".bt/kep5519.png"))
    root.close()
    engine.deleteLater()
    qt_app.processEvents()
