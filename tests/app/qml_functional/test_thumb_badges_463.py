"""#463: az indexkép-jelvények tényleg meg is jelennek a FŐ RÁCSBAN.

A jelvények (geo-pin, „van rajta arc", „arc-javaslat vár jóváhagyásra")
a `ThumbDelegate`-ben rég megvoltak, de a `LightboxFeed` delegátuma nem
kötötte be a hozzájuk tartozó tulajdonságokat — így a modell adata megvolt,
a jelvény mégsem jelent meg soha. Ez a teszt épp ezt a hibaosztályt fogja
meg: MINDEN jelvény-tulajdonságot, amit a delegátum kitesz, a rácsnak be
kell kötnie.
"""

from __future__ import annotations

import re
from pathlib import Path

import pytest

_QML_DIR = (
    Path(__file__).resolve().parents[3]
    / "src" / "picasapy" / "app" / "qml" / "PicasaPy"
)
_DELEGATE = (_QML_DIR / "ThumbDelegate.qml").read_text(encoding="utf-8")
_FEED = (_QML_DIR / "LightboxFeed.qml").read_text(encoding="utf-8")

#: a delegátum jelvény-kapcsolói — mindegyiket a rácsnak kell töltenie
_BADGE_PROPERTIES = (
    "star",
    "isVideo",
    "hasEdits",
    "hasGeo",
    "hasFaces",
    "hasFaceSuggestion",
    "held",
)


class TestBadgePropertiesAreBoundByTheGrid:
    @pytest.mark.parametrize("name", _BADGE_PROPERTIES)
    def test_delegate_exposes_the_property(self, name: str) -> None:
        assert re.search(rf"property bool {name}\b", _DELEGATE) or re.search(
            rf"required property bool {name}\b", _DELEGATE
        ), f"a ThumbDelegate nem teszi ki a(z) {name} jelvény-kapcsolót"

    @pytest.mark.parametrize("name", _BADGE_PROPERTIES)
    def test_feed_binds_the_property(self, name: str) -> None:
        assert re.search(rf"^\s+{name}:", _FEED, re.MULTILINE), (
            f"a LightboxFeed nem köti be a(z) {name} jelvény-kapcsolót — a "
            "jelvény sosem jelenne meg a rácsban"
        )
