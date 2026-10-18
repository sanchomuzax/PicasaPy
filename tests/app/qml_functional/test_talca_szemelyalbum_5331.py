"""#5331: személy-album megnyitásakor a tálcán megjelenik az „Album Selected - N photos” jelzés.

Az eredeti Picasa (picasa-colab-jobs job-213, 29. kép): a személy-album
megnyitásakor a tálca bal alsó sarkában a személy borítóképe áll az
„Album Selected - 2 photos” felirattal. Nálunk a tálca csak az album-tokent
ismerte (`currentAlbumToken`), személy módban az üres maradt.

Lefedve, VALÓDI kattintással a bal sáv személy-sorára:
- a kattintás előtt a tálcán nincs látszó token-felirat;
- a kattintás után a felirat „Album Selected - 2 photos", a borítókép pedig
  ugyanaz, mint a bal sáv személy-sorának arcképe.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from picasapy.ini import parse_document, update_document
from support.fixture_guards import qml_warning_guard
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _find_item,
    _make_portrait_photos,
    _save_window,
)
from tests.support.varakozas import var_feltetelre

_SZEMELY = "Teszt Elek"
_SZEMELY_ID = "bbbbbbbbbbbbbbbb"
_ARC = "1e00280045006e00"


@pytest.fixture
def qml_app_5331(qt_app, tmp_path, monkeypatch, request):
    """Teljes app, valódi portré-bélyegképekkel és izolált felhasználói profillal."""
    isolated_home = tmp_path / "home"
    for variable, folder in (
        ("HOME", isolated_home),
        ("XDG_CONFIG_HOME", isolated_home / ".config"),
        ("XDG_DATA_HOME", isolated_home / ".local" / "share"),
        ("XDG_CACHE_HOME", isolated_home / ".cache"),
        ("XDG_STATE_HOME", isolated_home / ".local" / "state"),
    ):
        folder.mkdir(parents=True, exist_ok=True)
        monkeypatch.setenv(variable, str(folder))

    warning_guard = qml_warning_guard()
    next(warning_guard)
    try:
        yield from _build_qml_app(
            qt_app,
            tmp_path,
            kepeket_keszit=_make_portrait_photos,
            belyegkep_meret=220,
            valodi_belyegkep=True,
            keep_modul=request.module,
        )
    finally:
        try:
            next(warning_guard)
        except StopIteration:
            pass


def _bejar(item):
    """Az elem összes leszármazottja, mélységi sorrendben."""
    for child in item.childItems():
        yield child
        yield from _bejar(child)


def _klikk(window, qt_app, item) -> None:
    """Valódi bal egérgomb-kattintás az elem közepén."""
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.width() > 0 and item.height() > 0
    pont = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _latszo_elem(qt_app, window, nev: str):
    """Az első LÁTSZÓ elem a nevével."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _bejar(window.contentItem()):
            if item.objectName() == nev and item.isVisible() and item.width() > 0:
                return item
        QTest.qWait(20)
    raise AssertionError(f"{nev} nem látszik")


def _latszo_tokenfeliratok(window) -> list:
    """A tálca látszó album-token feliratai (a `Repeater` delegáltjai)."""
    return [
        item
        for item in _bejar(window.contentItem())
        if item.objectName() == "trayAlbumTokenLabel" and item.isVisible()
    ]


def _seed_named_person(library: Path, db_path: Path) -> None:
    """Két fotó a megnevezett személlyel; a harmadik arc nélkül marad."""
    update_document(
        library / ".picasa.ini",
        lambda _old: parse_document(
            "[Contacts2]\n"
            f"{_SZEMELY_ID}={_SZEMELY};;\n"
            "[a.jpg]\n"
            f"faces=rect64({_ARC}),{_SZEMELY_ID}\n"
            "[b.jpg]\n"
            f"faces=rect64({_ARC}),{_SZEMELY_ID}\n"
        ),
        backup=False,
    )
    with open_index(db_path) as conn:
        sync_tree(conn, library)


def test_szemelyalbum_megnyitasakor_a_talcan_megjelenik_az_album_selected_jelzes(
    qml_app_5331, qt_app
):
    window, controller, _engine = qml_app_5331
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    library = Path(controller.photos.filePathAt(0)).parent
    _seed_named_person(library, Path(controller._db_path))
    controller._reload_after_sync()

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    assert _latszo_tokenfeliratok(window) == [], "a tálcán már kezdetben van token"

    sor = _latszo_elem(qt_app, window, f"personItem_{_SZEMELY}")
    _klikk(window, qt_app, sor)
    assert controller.currentPersonName == _SZEMELY

    assert var_feltetelre(
        qt_app, lambda: len(_latszo_tokenfeliratok(window)) == 1, 5.0
    ), "a személy-album megnyitása után nincs látszó tálca-felirat"
    felirat = _latszo_tokenfeliratok(window)[0]
    assert felirat.property("text") == "Album Selected - 2 photos"

    borito = next(
        item
        for item in _bejar(window.contentItem())
        if item.objectName() == "trayAlbumTokenCover"
    )
    avatar = _find_item(window, f"personThumbnailImage_{_SZEMELY}")
    assert avatar is not None
    assert borito.property("source").toString() != ""
    assert (
        borito.property("source").toString()
        == avatar.property("source").toString()
    ), "a tálca borítóképe nem a személy arcképe"
    # A borítókép aszinkron töltődik: a képernyőkép csak a betöltés után
    # mutat valódi arcot. Nincs Python-oldali `Image.Status`-konverter
    # (Qt-korlát, #664), ezért a ténylegesen kirajzolt méretet nézzük.
    assert var_feltetelre(
        qt_app,
        lambda: borito.property("paintedWidth") > 0
        and borito.property("paintedHeight") > 0,
        5.0,
    ), "a tálca borítóképe üres maradt (nincs kirajzolt méret)"
    _save_window(window, "kep_5331.png")
