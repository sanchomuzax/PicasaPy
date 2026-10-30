"""#5827 — a törlés-megerősítő eredeti jelölőszövege és biztonságos Enterje.

Valódi QML-es eseménylánc: egy valódi bélyegkép kijelölése egérrel, Delete,
Enter a Mégse gombon, majd a „Delete Image” gomb tényleges kattintása.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import QObject, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional._racs_helyimenuk_5150_helpers import kattints

_ABLAKMAGASSAG_ELTERESEK = (-5, 0, 5)


@pytest.fixture
def qml_app_valodi_belyegkep(qt_app, tmp_path):
    """Színes, részletes próbakép valódi termék-bélyegkép-szolgáltatóval."""
    def kepeket(lib: Path) -> None:
        make_minta_jpeg(lib / "a.jpg", size=(640, 480), seed=7)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _gyerek(window, nev):
    elem = window.findChild(QObject, nev)
    assert elem is not None, f"a(z) {nev} nem található"
    return elem


def _vizualis_bejaras(item):
    for child in item.childItems():
        yield child
        yield from _vizualis_bejaras(child)


def _vizualis_elem(window, nev):
    return next(
        (
            item
            for item in _vizualis_bejaras(window.contentItem())
            if item.objectName() == nev
        ),
        None,
    )


def _valodi_belyegkep_kesz(window):
    for item in _vizualis_bejaras(window.contentItem()):
        if item.objectName() != "thumbImage" or not item.property("source"):
            continue
        expression = QQmlExpression(qmlContext(item), item, "status === Image.Ready")
        ready, error = expression.evaluate()
        if not error and ready:
            return True
    return False


def _varj(qt_app, feltetel, uzenet):
    assert var_feltetelre(qt_app, feltetel), uzenet


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTERESEK)
def test_delete_enter_keeps_photo_then_delete_image_button_removes_it(
    qml_app_valodi_belyegkep, qt_app, monkeypatch, tmp_path, magassag_elteres
):
    window, _controller, _engine = qml_app_valodi_belyegkep
    celmagassag = window.height() + magassag_elteres
    window.setHeight(celmagassag)
    _varj(qt_app, lambda: window.height() == celmagassag, "ablakmagasság")
    photo = tmp_path / "kepek" / "a.jpg"
    assert photo.is_file(), "a teszt valódi próbaképe hiányzik"
    test_trash = tmp_path / "test-trash"
    monkeypatch.setattr(
        "picasapy.fileops.trash.find_trash_dir",
        lambda _path, **_kwargs: test_trash,
    )

    _kijelol_belyegkep(window, qt_app)
    QTest.keyClick(window, Qt.Key.Key_Delete)
    _varj(
        qt_app,
        lambda: (
            (ablak := window.findChild(QObject, "deleteConfirmDialog")) is not None
            and ablak.property("visible") is True
        ),
        "a Delete nem nyitotta meg a megerősítőt",
    )

    dialog = _gyerek(window, "deleteConfirmDialog")
    assert dialog.property("visible") is True, "a Delete nem nyitotta meg a megerősítőt"
    remember = _gyerek(window, "confirmRememberCheck")
    remember_text = remember.property("text")
    yes = _gyerek(window, "confirmYesButton")
    no = _gyerek(window, "confirmNoButton")
    cancel = _gyerek(window, "confirmCancelButton")
    assert yes.property("visible") is True, "a Delete Image gomb nem látható"
    assert yes.property("text") == "Delete Image"
    assert no.property("visible") is False, "a fölösleges No gomb látható"
    assert cancel.property("visible") is True, "a Cancel gomb nem látható"
    cancel_focused = cancel.property("activeFocus") is True

    screenshot = window.grabWindow()
    assert not screenshot.isNull(), "üres lett a törlési párbeszéd képe"
    assert screenshot.save(str(tmp_path / "delete-confirm-5827.png")), (
        "nem menthető a valódi bélyegképes törlési párbeszéd képe"
    )

    QTest.keyClick(window, Qt.Key.Key_Return)
    enter_closed_dialog = var_feltetelre(
        qt_app, lambda: not dialog.property("visible")
    )
    enter_kept_photo = photo.is_file()

    if dialog.property("visible") and enter_kept_photo:
        kattints(window, qt_app, cancel)
        _varj(
            qt_app,
            lambda: not dialog.property("visible"),
            "a Mégse gombra kattintás nem zárta be a párbeszédet",
        )

    delete_image_clicked = False
    if enter_kept_photo and not dialog.property("visible"):
        QTest.keyClick(window, Qt.Key.Key_Delete)
        _varj(
            qt_app,
            lambda: dialog.property("visible"),
            "a második Delete nem nyitotta meg a megerősítőt",
        )
        yes_text = yes.property("text")
        kattints(window, qt_app, yes)
        _varj(qt_app, lambda: not photo.exists(), "a Delete Image nem törölte a képet")
        delete_image_clicked = not photo.exists() and not dialog.property("visible")
    else:
        yes_text = ""

    observed = {
        "remember_text": remember_text,
        "cancel_focused": cancel_focused,
        "enter_closed_dialog": enter_closed_dialog,
        "enter_kept_photo": enter_kept_photo,
        "delete_image_button": yes_text,
        "delete_image_clicked": delete_image_clicked,
    }
    assert observed == {
        "remember_text": "Don't ask again, always remove",
        "cancel_focused": True,
        "enter_closed_dialog": True,
        "enter_kept_photo": True,
        "delete_image_button": "Delete Image",
        "delete_image_clicked": True,
    }, f"a törlés-megerősítő eltér a kívánt működéstől: {observed!r}"


def _kijelol_belyegkep(window, qt_app):
    _varj(
        qt_app,
        lambda: _valodi_belyegkep_kesz(window),
        "a valódi bélyegkép nem töltődött be",
    )
    thumb = _vizualis_elem(window, "thumbMouseArea")
    assert isinstance(thumb, QQuickItem), "a kép valós egérterülete nem található"
    kattints(window, qt_app, thumb)
    assert window.property("selectedIndexes").toVariant() == [0]


@pytest.mark.parametrize("magassag_elteres", _ABLAKMAGASSAG_ELTERESEK)
def test_thumbnail_click_uses_its_actual_geometry_at_height_variants(
    qml_app_valodi_belyegkep, qt_app, magassag_elteres
):
    window, _controller, _engine = qml_app_valodi_belyegkep
    window.setHeight(window.height() + magassag_elteres)
    qt_app.processEvents()
    _kijelol_belyegkep(window, qt_app)
