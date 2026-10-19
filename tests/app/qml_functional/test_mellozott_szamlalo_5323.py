"""#5323: egy arc mellőzése után a bal sáv „Ignored (N)” sora azonnal a helyes számot mutatja.

Az eredeti Picasa (picasa-colab-jobs job-210, 13. és 16. kép): az első arc „x”-e
és a „Ignore Person” után a „Show ignored faces” váltó aktív; a normál nézetben
a bal sávban csak az „Unnamed (5)” sor látszik (13. kép), a mellőzött nézetben
a helyén az „Ignored (1)” (16. kép, #5341). Nálunk a sor darabszáma egy
metódushívás volt (`ignoredCount()`), amelyre a QML-kötés nem figyelt, ezért a
mellőzés után 0 maradt.

Lefedve, VALÓDI kattintásokkal:
- a mellőzés előtt a mellőzött-sor rejtett (nincs mellőzött arc);
- az arc „x”-e, majd a megerősítő „Ignore Person” után a sor szövege azonnal
  az egyet mutatja, a sor a normál nézetben rejtve marad;
- a mellőzött nézetben a sor látszik, „Ignored (1)” felirattal;
- a „Show ignored faces” aktív lesz, és a „Back to Unnamed” visszaváltja a
  Névtelenek nézetet, az öt arcos darabszámmal.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.fixture_guards import qml_warning_guard
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_unnamed_faces_view_5183 import (
    _find_item,
    _find_object,
    _make_portrait_photos,
    _save_window,
    _seed_six_faces,
)
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def qml_app_5323(qt_app, tmp_path, monkeypatch, request):
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
    """Valódi bal egérgomb-kattintás az elem közepén. Az ablakot a hívótól
    kapja, nem az elemtől kérdezi."""
    assert item is not None, "A kattintandó felületi elem hiányzik."
    assert item.property("enabled") is not False
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
    """Az első LÁTSZÓ elem a nevével. A rács több példányt ad ugyanarra a névre."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _bejar(window.contentItem()):
            if item.objectName() == nev and item.isVisible() and item.width() > 0:
                return item
        QTest.qWait(20)
    raise AssertionError(f"{nev} nem látszik")


def _latszo_gomb(qt_app, window, felirat: str):
    """A látszó gomb felirat szerint. A megerősítő párbeszéd (Popup) az ablak
    overlay-ében él, az overlay pedig a tartalomfa gyereke, így a bejárás éri el."""
    for _ in range(150):
        qt_app.processEvents()
        for item in _bejar(window.contentItem()):
            if (
                item.property("text") == felirat
                and item.isVisible()
                and item.width() > 0
                and item.metaObject().indexOfSignal("clicked()") >= 0
            ):
                return item
        QTest.qWait(20)
    raise AssertionError(f"a(z) {felirat!r} gomb nem látszik")


def test_mellozes_utan_a_bal_sav_sora_a_helyes_szamot_mutatja(qml_app_5323, qt_app):
    window, controller, engine = qml_app_5323
    window.setWidth(1280)
    window.setHeight(1005)
    qt_app.processEvents()

    face_scan = engine.rootContext().contextProperty("faceScanController")
    _seed_six_faces(Path(controller._db_path))
    face_scan.unnamedCountChanged.emit()
    assert var_feltetelre(qt_app, lambda: face_scan.unnamedCount == 6, 3.0)

    folder_pane = _find_item(window, "folderPane")
    assert folder_pane is not None
    folder_pane.setProperty("peopleCollapsed", False)
    unnamed_row = _latszo_elem(qt_app, window, "unnamedFacesItem")
    _klikk(window, qt_app, unnamed_row)

    view = _find_item(window, "unnamedFacesView")
    assert var_feltetelre(
        qt_app, lambda: view is not None and view.property("visible") is True, 3.0
    )
    welcome_close = _latszo_elem(qt_app, window, "unnamedWelcomeCloseButton")
    _klikk(window, qt_app, welcome_close)

    ignored_row = _find_item(window, "ignoredFacesItem")
    ignored_label = _find_item(window, "ignoredFacesLabel")
    assert ignored_row is not None and ignored_label is not None
    # Mellőzés előtt nincs mellőzött arc: a sor rejtett, a darabszám nulla.
    assert ignored_row.property("visible") is False
    assert ignored_label.property("text") == "Ignored (0)"
    _save_window(window, "kep_5323_elotte.png")

    # Valódi kattintás az első arc „x”-én, majd a megerősítő „Ignore Person”.
    x_gomb = _latszo_elem(qt_app, window, "faceIgnoreX_1")
    _klikk(window, qt_app, x_gomb)
    confirm = _find_object(window, "ignoreFacesDialog")
    assert confirm is not None
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is True, 3.0)
    igen_gomb = _latszo_gomb(qt_app, window, "Ignore Person")
    _klikk(window, qt_app, igen_gomb)
    assert var_feltetelre(qt_app, lambda: confirm.property("visible") is False, 3.0)

    # A bal sáv sora a mellőzés után azonnal az egyet mutatja, de a normál
    # nézetben rejtve marad (job-210, 13. kép).
    assert var_feltetelre(
        qt_app,
        lambda: ignored_label.property("text") == "Ignored (1)",
        3.0,
    ), f"a mellőzött-sor szövege: {ignored_label.property('text')!r}"
    assert ignored_row.property("visible") is False
    assert face_scan.unnamedCount == 5
    _save_window(window, "kep_5323_utana.png")

    # „Show ignored faces” aktív lett, és a váltóval a mellőzöttek nézetére megyünk.
    show_ignored = _find_item(window, "unknownfaceheaderpanel/showignored")
    assert show_ignored is not None
    assert var_feltetelre(
        qt_app, lambda: show_ignored.property("enabled") is True, 3.0
    )
    _klikk(window, qt_app, show_ignored)
    assert var_feltetelre(
        qt_app, lambda: window.property("facesAlbumMode") == "ignored", 3.0
    )
    assert var_feltetelre(
        qt_app, lambda: ignored_row.property("visible") is True, 3.0
    )

    # „Back to Unnamed” visszavált a Névtelenek albumra, az öt arcos darabszámmal.
    back_to_unnamed = _find_item(window, "unknownfaceheaderpanel/showunknown")
    assert back_to_unnamed is not None
    assert var_feltetelre(
        qt_app, lambda: back_to_unnamed.property("visible") is True, 3.0
    )
    _klikk(window, qt_app, back_to_unnamed)
    assert var_feltetelre(
        qt_app, lambda: window.property("facesAlbumMode") == "unnamed", 3.0
    )
    assert _find_item(window, "unnamedAlbumFaceCount").property("text") == "5 Face(s)"
