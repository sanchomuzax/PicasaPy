"""Az Effekt-térszelvény QML-bekötése és nézőbeli helye (#6522)."""

# SAJÁT FUNKCIÓ (#6522): a forrásőrök a térszelvény saját felületi szerződését védik.

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QML = ROOT / "src/picasapy/app/qml/PicasaPy"


def test_a_termetszet_doboz_a_histogram_felett_4_px_re_kap_helyet():
    drawer = (QML / "PhotoViewerLeftDrawer.qml").read_text(encoding="utf-8")

    assert drawer.index("EffectSliceBox {") < drawer.index("HistogramBox {")
    assert "viewerHistogramBox.height + viewerHistogramBox.anchors.bottomMargin" in drawer
    assert "effectSliceBox.height + 4" in drawer
    assert 'objectName: "viewerEffectSliceBox"' in drawer


def test_a_nezet_menu_aljan_sajat_radio_almenu_tartozik():
    menu = (QML / "PicasaViewMenu.qml").read_text(encoding="utf-8")

    assert menu.index("menuViewEffectSlice") > menu.index("PicasaFolderViewMenu {")
    assert 'objectName: "menuViewEffectSliceAlways"' in menu
    assert 'objectName: "menuViewEffectSliceEditing"' in menu
    assert 'objectName: "menuViewEffectSliceNever"' in menu
    assert "ButtonGroup.group: effectSliceModeGroup" in menu
    assert "sajat: true" in menu


def test_a_doboz_python_festett_3d_elemre_epul_canvas_nelkul():
    box = (QML / "EffectSliceBox.qml").read_text(encoding="utf-8")

    assert "image://effectslice/" in box
    assert "Canvas {" not in box
    assert "Theme.chromeBg" in box
    assert "Theme.chromeBorder" in box
    assert "ctl.setSpinning" in box
