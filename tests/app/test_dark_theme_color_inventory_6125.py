"""Leltárőr: a QML-ben maradó világos színállandók csak fogyhatnak (#6125)."""

from collections import Counter
from pathlib import Path
import re


_BINDING = re.compile(
    r"\b(?:border\.color|placeholderTextColor|selectedTextColor|"
    r"highlightedTextColor|styleColor|fillStyle|strokeStyle|color)\s*:\s*([^;]+)"
)
_LITERAL = re.compile(r"(?P<quote>['\"])(?P<value>#[0-9a-fA-F]{3,8}|white)\1", re.I)

# path -> (maximalis darabszám, indoklás). A régi, még indokolt színek helye
# itt van; egy későbbi átvezetés törölheti vagy csökkentheti a keretet, növelni
# nem szabad. A Theme.qml token-definíciói nem részei a leltárnak.
REMAINING_FIXED_LIGHT_COLORS: dict[str, tuple[int, str]] = {
    "src/picasapy/app/qml/PicasaPy/CollageNode.qml": (
        1,
        "A kollázsba renderelt polaroid papírjának tartalomszíne.",
    ),
    "src/picasapy/app/qml/PicasaPy/CropOverlay.qml": (
        2,
        "A vágókeret és fogantyú a fénykép fölé rajzolt réteg.",
    ),
    "src/picasapy/app/qml/PicasaPy/EditorActionBadge.qml": (
        4,
        "A fehér jelölők a fotószerkesztő képrétegére rajzoltak.",
    ),
    "src/picasapy/app/qml/PicasaPy/EditorToolBar.qml": (
        1,
        "A felirat a képre rajzolt sötét szerkesztőgomb kontrasztszíne.",
    ),
    "src/picasapy/app/qml/PicasaPy/EffectFocalPuck.qml": (
        3,
        "A fókuszpont és kerete közvetlenül a fényképre rajzolt effektjelölő.",
    ),
    "src/picasapy/app/qml/PicasaPy/FacesOverlay.qml": (
        10,
        "Arc- és kijelöléskeretek, illetve feliratok a fotó fölött maradnak.",
    ),
    "src/picasapy/app/qml/PicasaPy/ImportDropArea.qml": (
        1,
        "A fehér szöveg a fix, áttetsző fekete húzás-visszajelző rétegen ül.",
    ),
    "src/picasapy/app/qml/PicasaPy/MoviePreviewFrame.qml": (
        1,
        "A feliratot a videóképkockára rajzoljuk, a forrás képszínéhez igazítva.",
    ),
    "src/picasapy/app/qml/PicasaPy/MovieTitleDialog.qml": (
        1,
        "A felhasználó által választott videó-feliratszín, nem app-króm.",
    ),
    "src/picasapy/app/qml/PicasaPy/PeoplePanelRow.qml": (
        2,
        "Az arcjelölő fehér rétege a bélyegképre rajzolódik.",
    ),
    "src/picasapy/app/qml/PicasaPy/PhotoViewerFilmstrip.qml": (
        1,
        "A világos belső keret az aktív fénykép bélyegképének kijelölése.",
    ),
    "src/picasapy/app/qml/PicasaPy/PhotoViewerOverlayControls.qml": (
        1,
        "A vezérlő ikon a fénykép fölé rajzolt réteg.",
    ),
    "src/picasapy/app/qml/PicasaPy/PhotoViewerRetouchArea.qml": (
        1,
        "A retusáló ecsetkeret a fotón látszó kurzorjelölő.",
    ),
    "src/picasapy/app/qml/PicasaPy/SlideshowControls.qml": (
        4,
        "A diavetítés kezelői és jelölései a képre rajzolt rétegek.",
    ),
    "src/picasapy/app/qml/PicasaPy/TextColorSwatches.qml": (
        4,
        "A szöveg-/színpaletta felhasználó által választható színei.",
    ),
    "src/picasapy/app/qml/PicasaPy/ThumbDelegate.qml": (
        1,
        "A lejátszásjel a videó-bélyegképre kerül.",
    ),
    "src/picasapy/app/qml/PicasaPy/TimelineView.qml": (
        0,
        "Az idővonalablak fekete háttere; a vizuális panel a külön komponensben van.",
    ),
    "src/picasapy/app/qml/PicasaPy/TimelinePanel.qml": (
        5,
        "Fotóköteg-papír és a fényképre rajzolt idővonal-feliratok.",
    ),
    "src/picasapy/app/qml/PicasaPy/UnnamedFacesViewGrid.qml": (
        1,
        "Az X-jelölő fehér lapja a fényképcsempére rajzolt réteg.",
    ),
}


def _is_fixed_light(value: str) -> bool:
    if value.lower() == "white":
        return True
    if not value.startswith("#"):
        return False
    digits = value[1:]
    if len(digits) == 3:
        rgb = "".join(char * 2 for char in digits)
    elif len(digits) == 6:
        rgb = digits
    elif len(digits) == 8:
        if digits[:2].lower() != "ff":
            return False
        rgb = digits[2:]
    else:
        return False
    red, green, blue = (int(rgb[offset : offset + 2], 16) for offset in (0, 2, 4))
    return (
        (red == green == blue and red >= 120)
        or value.lower().startswith(("#e", "#f"))
    )


def _fixed_light_occurrences(root: Path) -> Counter[str]:
    qml_root = root / "src/picasapy/app/qml"
    found: Counter[str] = Counter()
    for path in sorted(qml_root.rglob("*.qml")):
        if path.name == "Theme.qml":
            continue
        relative = path.relative_to(root).as_posix()
        for line in path.read_text(encoding="utf-8").splitlines():
            stripped = line.lstrip()
            if stripped.startswith(("//", "/*", "*")):
                continue
            for binding in _BINDING.finditer(line):
                expression = binding.group(1)
                # A literal in a dark/light binding is not a bypass: the
                # Theme.dark branch supplies the paired dark value.
                if "Theme.dark" in expression:
                    continue
                for literal in _LITERAL.finditer(expression):
                    if _is_fixed_light(literal.group("value")):
                        found[relative] += 1
    return found


def test_remaining_fixed_light_colors_are_reasoned_and_only_decrease():
    root = Path(__file__).resolve().parents[2]
    found = _fixed_light_occurrences(root)
    unlisted = sorted(set(found) - set(REMAINING_FIXED_LIGHT_COLORS))
    over_budget = {
        path: (count, REMAINING_FIXED_LIGHT_COLORS[path][0])
        for path, count in found.items()
        if path in REMAINING_FIXED_LIGHT_COLORS
        and count > REMAINING_FIXED_LIGHT_COLORS[path][0]
    }
    empty_reasons = [
        path
        for path, (_, reason) in REMAINING_FIXED_LIGHT_COLORS.items()
        if not reason.strip()
    ]
    assert not unlisted and not over_budget and not empty_reasons, (
        f"Indoklás nélküli világos színállandó: {unlisted}; "
        f"leltárkeret túllépése (tényleges, engedélyezett): {over_budget}; "
        f"üres indoklás: {empty_reasons}"
    )


def test_audited_surfaces_use_paired_theme_tokens():
    root = Path(__file__).resolve().parents[2]
    qml_root = root / "src/picasapy/app/qml/PicasaPy"
    required = {
        "MainToolbar.qml": {
            "Theme.contentPanel": 4,
            "Theme.searchClearBg": 1,
            "Theme.panelSelectionText": 1,
        },
        "../Main.qml": {
            "Theme.filterResultsBg": 1,
            "Theme.filterNoticeBg": 2,
        },
        "CollageClipsTab.qml": {
            "Theme.collageMissingBg": 1,
            "Theme.collageMissingBorder": 1,
            "Theme.collageMissingText": 1,
        },
        "CollageGroupNode.qml": {"Theme.collageGroupBorder": 1},
        "LightboxHeaderButtons.qml": {
            "Theme.headerPlayButtonBg": 1,
            "Theme.headerPlayButtonHoverBg": 1,
        },
        "OptionsTabNameTags.qml": {"Theme.optionsSliderTick": 2},
        "OptionsTabPrinting.qml": {"Theme.settingsDivider": 1},
        "TrayScratchPanel.qml": {"Theme.trayScratchLabel": 1},
        "FolderTreeItem.qml": {"Theme.panelSelectionText": 2},
        "UnnamedFacesView.qml": {
            "Theme.controlBase": 1,
            "Theme.inputBorder": 1,
            "Theme.panelSelectionText": 4,
            "Theme.unnamedGroupLabel": 1,
            "Theme.unnamedWelcomeBg": 1,
            "Theme.unnamedWelcomeBorder": 1,
            "Theme.unnamedWelcomeButtonBorder": 2,
        },
        "UnnamedFacesViewGrid.qml": {
            "Theme.controlBase": 2,
            "Theme.inputBorder": 2,
        },
        "UnnamedFacesViewIgnoredGroups.qml": {
            "Theme.controlBase": 1,
            "Theme.inputBorder": 1,
        },
        "CollageSheet.qml": {"Theme.collageSheetBorder": 1},
        "PhotoViewerPhotoArea.qml": {"Theme.mediaOverlayText": 2},
        "VideoPlayerView.qml": {"Theme.mediaOverlayText": 3},
        "VideoTrimSlider.qml": {
            "Theme.mediaOverlayText": 2,
            "Theme.mediaControlThumbBg": 2,
        },
    }
    missing = {}
    for filename, token_counts in required.items():
        source_path = (
            qml_root / filename
        )
        source = source_path.read_text(encoding="utf-8")
        for token, count in token_counts.items():
            if source.count(token) < count:
                missing[f"{filename}:{token}"] = count - source.count(token)
    assert not missing, f"A sötét módot megkerülő felületi kötés maradt: {missing}"

    theme = (qml_root / "Theme.qml").read_text(encoding="utf-8")
    light_values = {
        "contentPanel": "#ffffff",
        "searchClearBg": "#b0b0b0",
        "inputBorder": "#8a8a8a",
        "unnamedGroupLabel": "#68564f",
        "unnamedWelcomeBg": "#606060",
        "unnamedWelcomeBorder": "#999999",
        "unnamedWelcomeButtonBorder": "#dddddd",
        "headerPlayButtonBg": "#ffffff",
        "headerPlayButtonHoverBg": "#f0f0ee",
        "filterResultsBg": "#5aa865",
        "filterNoticeBg": "#f0e3b0",
        "collageMissingBg": "#c8c8c8",
        "collageMissingBorder": "#787878",
        "collageMissingText": "#787878",
        "collageGroupBorder": "#f85e0f",
        "collageSheetBorder": "#9a9a9a",
        "optionsSliderTick": "#c4c4c4",
        "settingsDivider": "#a0a0a0",
        "trayScratchLabel": "#c3c3c3",
        "mediaControlThumbBg": "#d5d5d5",
    }
    changed_light_values = {}
    for token, expected in light_values.items():
        match = re.search(
            rf'readonly property color {token}: tema\.dark \? "#[^"]+"\s*:\s*"([^"]+)"',
            theme,
        )
        if match is None or match.group(1).lower() != expected:
            changed_light_values[token] = (
                None if match is None else match.group(1),
                expected,
            )
    assert not changed_light_values, (
        f"A sötét mód párosítása megváltoztatta a világos értéket: "
        f"{changed_light_values}"
    )
