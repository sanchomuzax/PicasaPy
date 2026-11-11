"""Az új mappába helyezés valódi menükattintással (#6844)."""
import os
from pathlib import Path

import pytest

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese, elokeszit, tetel_kattintasa, varj,
)
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import (
    gyerek, jobbklikk_fotón, kattints, kijelol, vizualis_bejaras,
)


@pytest.fixture
def app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


@pytest.mark.parametrize('height_offset', [-5, 0, 5])
@pytest.mark.parametrize('entry,count', [('file', 1), ('context', 1), ('context', 2)])
def test_uj_mappa_kattintassal(app, qt_app, height_offset, entry, count):
    window, controller, _ = app
    source = elokeszit(window, qt_app, controller)
    window.resize(window.width(), window.height() + height_offset)
    qt_app.processEvents()
    paths = [Path(controller.photos.filePathAt(i)) for i in range(count)]
    kijelol(window, qt_app, range(count))
    if entry == 'file':
        tetel_kattintasa(window, qt_app, '&File', 'menuFileMoveToNewFolder')
    else:
        jobbklikk_fotón(window, qt_app, 0)
        kattints(window, qt_app, gyerek(window, 'contextMenuMove'))
    dialog = gyerek(window, 'moveToNewFolderDialog')
    assert varj(qt_app, lambda: dialog.property('opened') is True)
    kepkonyvtar = os.environ.get('PICASA_6844_SCREENSHOTS')
    if kepkonyvtar and entry == 'context' and count == 2 and height_offset == 0:
        assert window.grabWindow().save(str(Path(kepkonyvtar) / 'ablak.png'))
    kattints(window, qt_app, gyerek(dialog, 'folderPropertiesOkButton'))
    target = source / 'Untitled'
    assert varj(qt_app, lambda: all((target / p.name).is_file() for p in paths))
    assert varj(qt_app, lambda: Path(controller.currentFolder) == target)
    assert varj(qt_app, lambda: all(
        str(target / p.name) in [controller.photos.filePathAt(i)
                                 for i in range(controller.photos.rowCount())]
        for p in paths
    ))
    assert varj(qt_app, lambda: controller.folders.rowOfPath(str(target)) >= 0)
    pane = gyerek(window, 'folderPane')
    assert varj(qt_app, lambda: Path(pane.property('selectedPath')) == target)
    assert controller.folders.data(
        controller.folders.index(controller.folders.rowOfPath(str(target)), 0),
        controller.folders.CountRole,
    ) == count
    assert controller.folders.data(
        controller.folders.index(controller.folders.rowOfPath(str(source)), 0),
        controller.folders.CountRole,
    ) == 3 - count
    assert varj(qt_app, lambda: window.property('selectedIndexes').toVariant() == [])
    assert varj(qt_app, lambda: any(
        item.objectName() == 'trayAlbumTokenLabel' and item.isVisible()
        and item.property('text')
        == f'Folder Selected - {count} ' + ('photo' if count == 1 else 'photos')
        for item in vizualis_bejaras(window.contentItem())
    ))
    if kepkonyvtar and entry == 'context' and count == 2 and height_offset == 0:
        assert window.grabWindow().save(str(Path(kepkonyvtar) / 'eredmeny.png'))
