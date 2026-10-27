"""A képművelet-vezérlő témamixinekre bontható a QML-felület megtartásával (#6023)."""

from pathlib import Path

import pytest

from picasapy.app.photo_ops_controller import PhotoOpsMixin


_QML_TAGS = {
    "_on_broken_image_detected",
    "_on_photo_field_updated",
    "_on_photo_write_aborted",
    "_on_photo_write_failed",
    "_on_rename_batch_done",
    "_photoFieldUpdated",
    "_photoWriteAborted",
    "_renameBatchDone",
    "addRowsToAlbum",
    "albumProperties",
    "albumWriteFailed",
    "allEffectsClipboardChanged",
    "brokenPhotosDetected",
    "canUndoPasteAllEffects",
    "cancelCaptionPaste",
    "cancelXmpFaces",
    "captionPasteConfirmationRequested",
    "confirmCaptionPaste",
    "copyAllEffects",
    "copyTextLayer",
    "createAlbum",
    "createAlbumWithProperties",
    "createEmptyAlbum",
    "deleteAlbum",
    "editAlbumMusic",
    "editAlbumProperties",
    "flipHorizontalMany",
    "flipVerticalMany",
    "hasAllEffectsClipboard",
    "hasTextLayerClipboard",
    "hasTextLayerInSelection",
    "hidePhotosByIds",
    "hoverPreviewFileUrlAt",
    "pasteAllEffects",
    "pasteTextLayer",
    "photoOpFailed",
    "removeRowsFromAlbum",
    "renamePhotosMany",
    "renamePreview",
    "renameSamplePreview",
    "renameUseDate",
    "renameUseSize",
    "reorderAlbumPhotos",
    "rotateLeft",
    "rotateLeftMany",
    "rotateRight",
    "rotateRightMany",
    "rotationNeedsSelection",
    "rotationTypeFailed",
    "saveSearchAsAlbum",
    "setCaption",
    "setPhotoAsDesktopBackground",
    "setRenameUseFlags",
    "showTagAsAlbum",
    "sortAlbum",
    "sortFolderBy",
    "textLayerClipboardChanged",
    "toggleHiddenRows",
    "toggleStar",
    "toggleStarMany",
    "undoPasteAllEffects",
    "writeFacesToXmp",
    "xmpFacesActive",
    "xmpFacesCancelled",
    "xmpFacesDone",
    "xmpFacesFinished",
    "xmpFacesStateChanged",
    "xmpFacesTotal",
}


def _defining_module(name: str) -> str:
    owner = next(base for base in PhotoOpsMixin.__mro__ if name in base.__dict__)
    return owner.__module__


def test_controller_facade_preserves_qml_names_and_stays_below_800_lines():
    qml_names = {name for name in _QML_TAGS if hasattr(PhotoOpsMixin, name)}
    assert qml_names == _QML_TAGS

    controller_file = Path(__import__("picasapy.app.photo_ops_controller", fromlist=["__file__"]).__file__)
    assert len(controller_file.read_text(encoding="utf-8").splitlines()) < 800


@pytest.mark.parametrize(
    ("method", "module"),
    [
        ("setCaption", "photo_ops_write_mixin"),
        ("renamePreview", "photo_ops_rename_mixin"),
        ("createAlbum", "photo_ops_album_mixin"),
        ("writeFacesToXmp", "photo_ops_xmp_mixin"),
        ("rotateRight", "photo_ops_transform_mixin"),
        ("copyAllEffects", "photo_ops_effect_clipboard_mixin"),
    ],
)
def test_operation_groups_live_in_topic_mixins(method, module):
    assert _defining_module(method).endswith(module)
