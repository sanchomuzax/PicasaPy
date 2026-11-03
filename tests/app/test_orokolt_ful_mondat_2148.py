"""#6443: az összevont effektfül címe és nincs külön szürke fejléc."""

from __future__ import annotations

from pathlib import Path
import re

GYOKER = Path(__file__).resolve().parents[2] / "src" / "picasapy" / "app"
TABBAR = GYOKER / "qml" / "PicasaPy" / "EditorTabBar.qml"
LEGACY = GYOKER / "qml" / "PicasaPy" / "EditorLegacyTab.qml"
TS = GYOKER / "i18n" / "picasapy_hu.ts"
ANGOL = "Forgotten or deprecated effects brought back to life"
MAGYAR = "Régi elfeledett vagy kivezetett effektek újraélesztve"


def test_combined_tab_has_the_requested_tooltip_source():
    source = TABBAR.read_text(encoding="utf-8")
    block_start = source.index('objectName: "editTabEffects4"')
    block = source[block_start : source.index("    }", block_start)]
    assert f'description: qsTr("{ANGOL}")' in block
    assert 'objectName: "editTabLegacy"' not in source


def test_gray_intro_line_was_removed():
    source = LEGACY.read_text(encoding="utf-8")
    assert "legacyEffectsIntro" not in source


def test_requested_hungarian_copy_is_in_the_translation_source():
    source = TS.read_text(encoding="utf-8")
    match = re.search(
        rf"<source>{re.escape(ANGOL)}</source>.*?<translation>(.*?)</translation>",
        source,
        re.S,
    )
    assert match is not None
    assert match.group(1) == MAGYAR


def test_three_existing_legacy_access_points_stay_in_the_catalogue():
    from picasapy.render.legacy_effects import LEGACY_EFFECT_KEYS

    assert {"radtint", "autobacklight", "rainbow"} <= LEGACY_EFFECT_KEYS
