"""A #6076-ban kiemelt képrács-QML részei maradjanak 800 sor alatt."""

from pathlib import Path


_QML_DIR = Path(__file__).parents[2] / "src" / "picasapy" / "app" / "qml" / "PicasaPy"


def test_lightboxfeed_components_are_at_most_800_lines():
    components = sorted(_QML_DIR.glob("LightboxFeed*.qml"))
    assert components, "nem található LightboxFeed QML-komponens"

    line_counts = {
        component.name: len(component.read_text(encoding="utf-8").splitlines())
        for component in components
    }
    oversize = {name: count for name, count in line_counts.items() if count > 800}
    assert not oversize, f"a LightboxFeed-részek meghaladják a 800 sort: {oversize}"
