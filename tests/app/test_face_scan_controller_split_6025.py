"""The face-scan QML contract survives the controller's thematic split."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QMetaMethod, QObject

from picasapy.app.face_scan_controller import FaceScanController


_QML = {
    "property": frozenset("""
        ignoredCount modelDownloadPercent scanPercent sortingPercent
        uncheckedFiles unnamedCount
    """.split()),
    "signal": frozenset("""
        _scanWorkerStopped embeddingCancelled embeddingFailed embeddingFinished
        embeddingModelUnavailable embeddingProgress embeddingStarted
        faceResetConfirmationRequested faceSuggestionsChanged facesStored
        modelDownloadFinished modelDownloadPercentChanged modelUnavailable
        scanCancelled scanFailed scanFinished scanPercentChanged scanProgress
        scanStarted sortingPercentChanged uncheckedFilesChanged unnamedCountChanged
        xmpAutoWriteFailed
    """.split()),
    "slot": frozenset("""
        _auto_group_after_scan _finish_reset_after_scan acceptSuggestion
        assignNameToFaces automaticDetectionEnabled cancelEmbedding
        cancelModelDownload cancelScan clusterThreshold computeEmbeddings
        confirmPersonSuggestions downloadModels embeddingUnavailableReason
        ignoreFaces ignoredGroups isAvailable isEmbeddingAvailable
        markUnnamedWelcomeShown modelDownloadOffer moreSuggestions pendingAmong
        persistFaceToFile personSuggestionCount personSuggestionIdsForPaths
        personSuggestionPaths rejectSuggestion removeAllFaceData
        removePersonSuggestions resetAllFaces resetFacesForPhotos scanAlbum
        scanFolder scanForFaces scanNewFaces setAutomaticDetectionEnabled
        setClusterThreshold setPersistFaceToFile setSuggestionThreshold
        setSuggestionsEnabled suggestionThreshold suggestionsEnabled
        unavailableReason unignoreFaces unnamedAlbum unnamedGroups
        unnamedWelcomeHasBeenShown
    """.split()),
}

_TEMAK = {
    "isAvailable": "FaceScanControllerSettingsMixin",
    "scanForFaces": "FaceScanControllerScanMixin",
    "assignNameToFaces": "FaceScanControllerUnnamedMixin",
    "acceptSuggestion": "FaceScanControllerSuggestionsMixin",
    "resetFacesForPhotos": "FaceScanControllerResetMixin",
    "computeEmbeddings": "FaceScanControllerEmbeddingMixin",
}


def test_controller_tematikus_es_a_qml_felulet_valtozatlan() -> None:
    """A teljes QML-metaobjektum maradjon meg az 800 sor alatti hídban."""
    controller_file = Path(FaceScanController.__module__.replace(".", "/") + ".py")
    repo_root = Path(__file__).resolve().parents[2]
    controller_path = repo_root / "src" / controller_file
    assert len(controller_path.read_text(encoding="utf-8").splitlines()) < 800

    mro = FaceScanController.__mro__
    for method, mixin_name in _TEMAK.items():
        mixin = next((base for base in mro if base.__name__ == mixin_name), None)
        assert mixin is not None, f"hiányzó témamixin: {mixin_name}"
        assert method in mixin.__dict__, f"{method} nincs a {mixin_name} témamixinben"

    meta = FaceScanController.staticMetaObject
    observed = {"property": set(), "signal": set(), "slot": set()}
    for index in range(QObject.staticMetaObject.propertyCount(), meta.propertyCount()):
        observed["property"].add(str(meta.property(index).name()))
    for index in range(QObject.staticMetaObject.methodCount(), meta.methodCount()):
        method = meta.method(index)
        name = bytes(method.name()).decode("utf-8")
        if method.methodType() == QMetaMethod.MethodType.Signal:
            observed["signal"].add(name)
        elif method.methodType() == QMetaMethod.MethodType.Slot:
            observed["slot"].add(name)

    assert observed == {key: set(values) for key, values in _QML.items()}
