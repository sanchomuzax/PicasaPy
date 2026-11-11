"""A kép helyi menüjének új mappába helyezési bekötése (#6844)."""
from pathlib import Path


def test_helyi_menu_mappa_tulajdonsagait_nyitja():
    qml = Path('src/picasapy/app/qml/PicasaPy/MainPhotoContextMenu.qml').read_text(encoding="utf-8")
    assert 'onMoveRequested: hostFileOpsDialogs.ensure().openMoveToNewFolder(' in qml
