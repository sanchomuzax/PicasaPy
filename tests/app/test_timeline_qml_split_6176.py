"""A teljes képernyős Időrend QML-komponenshatárai (#6176)."""

from pathlib import Path
import re


_QML = Path(__file__).resolve().parents[2] / "src/picasapy/app/qml/PicasaPy"
_ROOT = _QML / "TimelineView.qml"
_PANEL = _QML / "TimelinePanel.qml"
_PUBLIC_TAGOK = (
    "fullscreenVisibility",
    "windowedVisibility",
    "panelWidth",
    "panelHeight",
    "collectionsModel",
    "currentIndex",
    "previousIndex",
    "animationDurationMs",
    "transitionProgress",
    "animating",
    "draggingSlider",
    "dragX",
    "pendingSliderIndex",
    "animationStartedAt",
    "currentOffset",
    "previousOffset",
    "frameTransforms",
    "currentLayerAlpha",
    "currentLayerOpacity",
    "previousLayerOpacity",
    "dotsModel",
    "currentCardsLoaded",
    "currentPhotoCardGeometry",
    "closed",
    "slideshowRequested",
    "collectionAt",
    "photoAt",
    "sliderValues",
    "selectedSliderPosition",
    "animateTo",
    "step",
    "startCurrentSlideshow",
    "resetForOpen",
    "updateSliderFromX",
    "releaseSlider",
)


def test_timeline_panel_is_an_internal_component_and_both_files_are_under_800_lines():
    assert _ROOT.is_file()
    assert _PANEL.is_file(), "a vizuális panel kerüljön önálló QML-komponensbe"

    qmldir = (_QML / "qmldir").read_text(encoding="utf-8")
    assert re.search(r"(?m)^internal TimelinePanel TimelinePanel\.qml$", qmldir)
    assert re.search(r"(?m)^\s*TimelinePanel\s*\{", _ROOT.read_text(encoding="utf-8"))

    for path in (_ROOT, _PANEL):
        assert len(path.read_text(encoding="utf-8").splitlines()) < 800, path.name


def test_timeline_window_keeps_its_existing_qml_visible_members():
    source = _ROOT.read_text(encoding="utf-8")
    assert 'objectName: "timelineView"' in source
    for name in _PUBLIC_TAGOK:
        assert re.search(
            rf"\b(?:property\s+(?:\w+\s+)?|signal\s+|function\s+){name}\b",
            source,
        ), f"a TimelineView nyilvános QML-tagja eltűnt: {name}"
