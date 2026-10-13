"""#4876 — a „nincs borító" jelölőtől a LÁTHATÓ mappaikonig, renderelve.

A szolgáltató borító nélkül 1 × 1-es, átlátszó, de érvényes képet ad
(`Image.Ready`, `implicitWidth == 1`). Hogy a felhasználó ilyenkor a
mappaikont látja-e, azt a QML `boritoLatszik` feltétele dönti el — ezt a
szöveget kereső őr nem méri. Itt VALÓDI `foldercover` szolgáltató áll a
motoron (a betöltés ELŐTT regisztrálva), és mindkét nézet kirajzolt elemeit
nézzük: a lapos lista (`FolderPane`: `folderRowIcon`) és a fa
(`FolderHierarchyView`: `hierFolderIcon:<út>`).
"""

from __future__ import annotations

import time

import pytest
from PySide6.QtCore import QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine
from PySide6.QtQuick import QQuickItem, QQuickView

from picasapy.app.folder_cover_provider import FolderCoverProvider
from picasapy.app.folder_hierarchy_controller import FolderHierarchyController
from support.jpeg_factory import make_jpeg

#: A `status` enumot a PySide nem tudja kiolvasni (`Can't find converter for
#: 'QQuickImageBase::Status'`), ezért az `Image.Ready` jele az
#: `implicitWidth`: betöltés előtt és hibánál 0, a betöltött képé a kép
#: szélessége (a jelölőé 1). A `boritoLatszik` maga a `status === Ready`-t is
#: tartalmazza, tehát a valódi borítónál az is a Ready bizonyítéka.
_BORITOS_NEV = "boritos"
_BORITO_NELKUL_NEV = "boritonelkuli"
_KEEPALIVE: list[object] = []


def _walk(item: QQuickItem):
    for gyerek in item.childItems():
        yield gyerek
        yield from _walk(gyerek)


def _betoltott(kep) -> bool:
    """`Image.Ready`: a kép betöltődött (az `implicitWidth` > 0)."""
    return kep is not None and kep.property("implicitWidth") > 0


def _var(qt_app, feltetel, masodperc: float = 8.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        time.sleep(0.01)
    return False


def _elem(pane, nev: str):
    for elem in _walk(pane):
        if elem.objectName() == nev:
            return elem
    return None


def _lapos_borito_kep(pane, nev: str):
    """A lapos lista azon sorának borító-`Image`-e, amely a `nev` mappát kéri."""
    for elem in _walk(pane):
        if elem.objectName() == "folderRowCoverImage":
            # Windowson az útvonal `\` elválasztóval végződik (#4914).
            forras = str(elem.property("source").toString()).replace("\\", "/")
            if forras.endswith("/" + nev):
                return elem
    return None


@pytest.fixture
def megjelenit(qt_app, tmp_path):
    """FolderPane valódi `foldercover` szolgáltatóval; a hívó választ nézetet."""
    import picasapy.app.application as app_module
    from picasapy.app.models import FolderListModel
    from picasapy.index import open_index, sync_tree

    gyoker = tmp_path / "felhasznalo" / "kepek"
    for nev in (_BORITOS_NEV, _BORITO_NELKUL_NEV):
        (gyoker / nev).mkdir(parents=True)
        make_jpeg(gyoker / nev / "a.jpg", size=(160, 120))
    boritos_kep = gyoker / _BORITOS_NEV / "a.jpg"
    db = tmp_path / "index.db"
    with open_index(db) as conn:
        sync_tree(conn, gyoker)
        modell = FolderListModel()
        modell.load(conn)
    utak = {n: str(gyoker / n) for n in (_BORITOS_NEV, _BORITO_NELKUL_NEV)}

    def lekerdezo(mappa: str):
        return [boritos_kep] if mappa == utak[_BORITOS_NEV] else []

    def _epit(*, fa: bool):
        hierarchy = FolderHierarchyController()
        hierarchy.setFolders([{"path": u, "count": 1} for u in utak.values()])
        hierarchy.setAlbumThumbs(True)  # a lapos listában ez kapcsolja be
        engine = QQmlEngine()
        # ⚠️ A motor betöltése ELŐTT: a szolgáltatót a motor veszi át.
        engine.addImageProvider("foldercover", FolderCoverProvider(lekerdezo))
        engine.addImportPath(str(app_module._APP_DIR / "qml"))
        engine.rootContext().setContextProperty("controller", None)
        url = QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "FolderPane.qml")
        )
        component = QQmlComponent(engine, url)
        pane = component.createWithInitialProperties(
            {
                "hierarchyController": hierarchy,
                "treeViewMode": fa,
                "foldersModel": modell,
            }
        )
        assert component.errors() == [], [e.toString() for e in component.errors()]
        view = QQuickView(engine, None)
        view.setResizeMode(QQuickView.ResizeMode.SizeRootObjectToView)
        view.setContent(url, component, pane)
        view.resize(260, 600)
        view.show()
        if fa:
            hierarchy.expandAll()
        _KEEPALIVE.extend((engine, component, view, pane, hierarchy, modell))
        return pane, utak

    return _epit


class TestLaposLista:
    def test_borito_nelkul_a_mappaikon_LATSZIK(self, megjelenit, qt_app):
        pane, _utak = megjelenit(fa=False)
        assert _var(
            qt_app,
            lambda: _betoltott(_lapos_borito_kep(pane, _BORITO_NELKUL_NEV)),
        ), "a borító nélküli sor jelölő-képe nem töltődött be"
        kep = _lapos_borito_kep(pane, _BORITO_NELKUL_NEV)
        tarolo = kep.parentItem()
        ikon = next(
            gy for gy in _walk(tarolo) if gy.objectName() == "folderRowIcon"
        )
        assert kep.property("implicitWidth") == 1  # az érvényes 1 × 1 jelölő
        assert tarolo.property("boritoLatszik") is False
        assert ikon.isVisible(), "borító nélkül a mappaikon eltűnt (üres sor)"
        assert not kep.isVisible()

    def test_valodi_boritonal_a_borito_LATSZIK(self, megjelenit, qt_app):
        pane, _utak = megjelenit(fa=False)
        assert _var(
            qt_app,
            lambda: _betoltott(_lapos_borito_kep(pane, _BORITOS_NEV))
            and _lapos_borito_kep(pane, _BORITOS_NEV)
            .parentItem()
            .property("boritoLatszik"),
        ), "a valódi borító nem jelent meg"
        kep = _lapos_borito_kep(pane, _BORITOS_NEV)
        ikon = next(
            gy for gy in _walk(kep.parentItem()) if gy.objectName() == "folderRowIcon"
        )
        assert kep.property("implicitWidth") > 1
        assert kep.isVisible()
        assert not ikon.isVisible()


class TestFanezet:
    def test_borito_nelkul_a_mappaikon_LATSZIK(self, megjelenit, qt_app):
        pane, utak = megjelenit(fa=True)
        ut = utak[_BORITO_NELKUL_NEV]
        assert _var(
            qt_app, lambda: _betoltott(_elem(pane, "hierFolderCoverImage:" + ut))
        ), "a fasor jelölő-képe nem töltődött be"
        kep = _elem(pane, "hierFolderCoverImage:" + ut)
        ikon = _elem(pane, "hierFolderIcon:" + ut)
        assert kep.property("implicitWidth") == 1
        assert kep.parentItem().property("boritoLatszik") is False
        assert ikon is not None and ikon.isVisible(), (
            "borító nélkül a fasor mappaikonja eltűnt (üres sor)"
        )
        assert not kep.isVisible()

    def test_valodi_boritonal_a_borito_LATSZIK(self, megjelenit, qt_app):
        pane, utak = megjelenit(fa=True)
        ut = utak[_BORITOS_NEV]
        nev = "hierFolderCoverImage:" + ut
        assert _var(
            qt_app,
            lambda: _betoltott(_elem(pane, nev))
            and _elem(pane, nev).parentItem().property("boritoLatszik"),
        ), "a fasor valódi borítója nem jelent meg"
        kep = _elem(pane, nev)
        ikon = _elem(pane, "hierFolderIcon:" + ut)
        assert kep.property("implicitWidth") > 1
        assert kep.isVisible()
        assert ikon is not None and not ikon.isVisible()
