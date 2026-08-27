"""Az „Exportált képek" csomópontra KATTINTVA is meg kell jelenniük a
képeknek (#1565).

A jegy hibája nem a mag hibája volt, hanem a felületé: a bal hasáb sora ott
állt (a nyilvántartás a beállításokban él, a létezést a fájlrendszerből
nézzük), a `selectFolder` viszont kizárólag az indexből olvas — az
exportcél pedig minden figyelt gyökéren kívül van. Ezért mér ez a fájl
KATTINTÁSSAL: a `selectFolder` közvetlen hívása attól még zöld lett volna,
hogy a sor kattinthatatlan vagy rossz utat ad tovább (MEMORY: „a vezérlőre
KATTINTS, ne a metódust hívd").

A lánc, amit végigmérünk: `exportedFolderRepeater` sora → egérkattintás →
`ProjectsSection.folderChosen` → `FolderPane.folderChosen` → a Main.qml
kötése (`controller.selectFolder`) → a rács tartalma.
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import (
    Q_ARG,
    Q_RETURN_ARG,
    QMetaObject,
    QObject,
    QPointF,
    QSettings,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

from support.jpeg_factory import make_jpeg

try:
    from PySide6.QtTest import QTest

    _QTTEST_VAN = True
except ImportError:  # pragma: no cover — csak a hiányos telepítésen fut
    QTest = None
    _QTTEST_VAN = False

pytestmark = pytest.mark.skipif(
    not _QTTEST_VAN,
    reason=(
        "a PySide6.QtTest modul hiányzik ezen a gépen. Debian/Ubuntu alatt "
        "így pótolható: sudo apt install python3-pyside6.qttest"
    ),
)

_KEEPALIVE: list[object] = []


def _var(qt_app, feltetel, masodperc: float = 20.0) -> bool:
    """Határidős várakozás a feltételre, nem az órára (#1463)."""
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.02)
    try:
        return bool(feltetel())
    except (AttributeError, TypeError, RuntimeError):
        return False


def _child(root, name):
    obj = root.findChild(QObject, name)
    assert obj is not None, f"{name} nem található"
    return obj


def _repeater_item(pane, repeater_name, index):
    """A `Repeater` index. delegate-példánya — a `findChild` nem látja."""
    item = QMetaObject.invokeMethod(
        _child(pane, repeater_name),
        "itemAt",
        Qt.ConnectionType.DirectConnection,
        Q_RETURN_ARG(QQuickItem),
        Q_ARG(int, index),
    )
    assert item is not None, f"{repeater_name}[{index}] nem jött létre"
    return item


@pytest.fixture
def exportalt_hasab(qt_app, tmp_path):
    """Valódi vezérlő + valódi export + kirajzolt FolderPane.

    A hasáb `exportedFolders` property-je és a `folderChosen` kötése
    UGYANÚGY áll, ahogy a `Main.qml` állítja (1202–1203. sor)."""
    import picasapy.app.application as app_module
    from picasapy.app.controller import AppController
    from picasapy.app.models import FolderListModel
    from picasapy.app.thumbnail_provider import ThumbnailProvider
    from picasapy.index import open_index, sync_tree
    from picasapy.thumbs import ThumbnailCache

    library = tmp_path / "kepek"
    (library / "forras").mkdir(parents=True)
    for i in range(1, 4):
        make_jpeg(library / "forras" / f"IMG_{i:04d}.jpg", size=(20, 20))
    with open_index(tmp_path / "index.db") as conn:
        sync_tree(conn, library)

    provider = ThumbnailProvider(ThumbnailCache(tmp_path / "thumbs", size=32))
    settings = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    ctl = AppController(
        tmp_path / "index.db",
        (str(library),),
        provider,
        settings=settings,
        watched_file=tmp_path / "WatchedFolders.txt",
    )
    ctl.start()
    _var(qt_app, lambda: not ctl._sync_running)
    if ctl._watcher is not None:
        ctl._watcher.stop()
        ctl._watcher = None
    if ctl._folder_poll_timer is not None:
        ctl._folder_poll_timer.stop()
    _var(qt_app, lambda: not ctl._sync_running)
    ctl.selectFolder(str(library / "forras"))
    assert _var(qt_app, lambda: ctl.photos.rowCount() == 3)

    # a felhasználó exportál — a figyelt gyökereken KÍVÜLRE, ahogy az
    # export alapértelmezett helye is oda mutat
    cel = tmp_path / "Kepek" / "Picasa" / "Exports" / "nyar"
    kesz = []
    ctl.exportFinished.connect(lambda *a: kesz.append(a))
    ctl.exportRows([0, 1, 2], str(cel), 0, 85, False, "", False, False)
    assert _var(qt_app, lambda: kesz, 60.0), "az export nem futott le"
    assert len(list(cel.glob("*.jpg"))) == 3, f"az export nem írt fájlt: {kesz}"

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    engine.rootContext().setContextProperty("controller", ctl)
    url = QUrl.fromLocalFile(
        str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
    )
    component = QQmlComponent(engine, url)
    folders_model = FolderListModel()
    with open_index(tmp_path / "index.db") as conn:
        folders_model.load(conn)
    pane = component.createWithInitialProperties({"foldersModel": folders_model})
    errors = [error.toString() for error in component.errors()]
    assert errors == [], errors
    assert pane is not None
    folders_model.setParent(pane)

    view = QQuickView(engine, None)
    view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
    view.setContent(url, component, pane)
    view.resize(230, 700)
    view.show()
    QTest.qWaitForWindowExposed(view)

    pane.setProperty("projectsCollapsed", False)
    # a Main.qml 1203. sorának megfelelője
    pane.setProperty("exportedFolders", ctl.exportedFolders)
    # a Main.qml kötése: a hasáb választása a vezérlő mappaváltása
    pane.folderChosen.connect(ctl.selectFolder)
    assert _var(qt_app, lambda: pane.property("exportedFolders") != [])
    # a ColumnLayout a tördelést a következő polish-körben végzi: a sor
    # addig 0×0, és a rá küldött kattintás a semmibe menne (mérve)
    assert _var(
        qt_app,
        lambda: _repeater_item(pane, "exportedFolderRepeater", 0).height() > 0,
    ), "az exportált mappa sora nem tördelődött ki"

    _KEEPALIVE.extend((engine, component, view, pane, folders_model))
    yield view, pane, ctl, cel
    pane.folderChosen.disconnect(ctl.selectFolder)
    ctl.shutdown()
    assert ctl.waitForBackgroundWorkers(30.0), "háttérszál nem állt le"


def _kattints(qt_app, view, item) -> None:
    kozep = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    assert 0 <= kozep.y() <= view.height(), (
        f"a kattintási pont ({kozep.y():.0f}) az ablakon kívülre esik — a "
        "teszt így nem mérne semmit"
    )
    QTest.mouseClick(
        view,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        kozep.toPoint(),
    )
    qt_app.processEvents()


class TestAzExportaltKepekSoraraKattintva:
    def test_a_sor_a_helyes_utat_adja_tovabb(self, exportalt_hasab, qt_app):
        """Ellenpróba: a kattintás egyáltalán eljut a vezérlőig.

        Enélkül a lenti állítást egy soha be nem következő kattintás is
        „teljesítené", ha a rács valamiért amúgy is megtelne."""
        view, pane, ctl, cel = exportalt_hasab
        sor = _repeater_item(pane, "exportedFolderRepeater", 0)

        _kattints(qt_app, view, sor)

        assert _var(qt_app, lambda: ctl.currentFolder == str(cel)), (
            "az Exportált képek sorára kattintva a vezérlő nem az "
            f"exportcélra váltott: {ctl.currentFolder!r}"
        )

    def test_a_racs_megtelik_az_exportalt_kepekkel(self, exportalt_hasab, qt_app):
        """A jegy állítása: a csomópont NE tartósan üres rácsot nyisson."""
        from pathlib import Path

        view, pane, ctl, cel = exportalt_hasab
        sor = _repeater_item(pane, "exportedFolderRepeater", 0)

        _kattints(qt_app, view, sor)

        def latszik():
            return sum(
                1
                for p in ctl.photos.photos
                if str(Path(p.folder_path)) == str(cel)
            )

        assert _var(qt_app, lambda: latszik() == 3), (
            f"a csomópontra kattintva a három exportált képből {latszik()} "
            "látszik — a mappa a figyelt gyökereken kívül van, tehát az "
            "indexbe SAJÁT GYÖKÉRKÉNT kell bekerülnie (#1565)"
        )
