"""#5670: az Arcfilm beállításai a külön Options fülön vannak."""

from __future__ import annotations

import os
from pathlib import Path

from PySide6.QtCore import QObject, QPointF, Qt
from PySide6.QtTest import QTest

from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_minta_jpeg
from tests.support.varakozas import var_feltetelre


_SZEMELY = "1111111111111111"


def _arcfilm_kep(lib: Path) -> None:
    make_minta_jpeg(lib / "arcfilm.jpg", size=(640, 400), seed=56)
    ini = (
        "[Contacts2]\n"
        f"{_SZEMELY}=Anna;;\n"
        "[arcfilm.jpg]\n"
        f"faces=rect64(1e00280045006e00),{_SZEMELY}\n"
    )
    update_document(lib / ".picasa.ini", lambda _old: parse_document(ini), backup=False)


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _elem(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _kattints(window, qt_app, elem) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látható"
    pont = elem.mapToScene(
        QPointF(elem.property("width") / 2, elem.property("height") / 2)
    ).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, pos=pont)
    qt_app.processEvents()


def test_arcfilm_options_tab_and_default_values_are_reachable_by_click(
    qt_app, tmp_path
):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_arcfilm_kep)
    window, controller, _engine = next(gen)
    dialog = None
    try:
        assert _varj(qt_app, lambda: controller.photos.rowCount() == 1)
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        alapmagassag = window.height()

        for eltolás in (-5, 0, 5):
            window.setHeight(alapmagassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: window.height() == alapmagassag + eltolás,
            )

            create_menu = _elem(window, "menuCreateRoot")
            create_menu.open()
            assert _varj(
                qt_app, lambda create_menu=create_menu: create_menu.property("visible")
            )
            movie_menu = _elem(window, "menuCreateMovieMenu")
            movie_menu.open()
            from_faces = _elem(window, "menuCreateMovieFromFaces")
            assert _varj(
                qt_app, lambda from_faces=from_faces: from_faces.property("visible")
            )
            _kattints(from_faces.window(), qt_app, from_faces)

            if dialog is None:
                assert _varj(qt_app, lambda: window.findChild(QObject, "movieDialog"))
                dialog = _elem(window, "movieDialog")
            assert _varj(qt_app, lambda dialog=dialog: dialog.property("visible"))
            assert dialog.property("personMovieMode") is True

            tabs = (
                _elem(window, "movieTabMotion"),
                _elem(window, "movieTabSlide"),
                _elem(window, "movieTabOptions"),
            )
            assert [tab.property("text") for tab in tabs] == [
                "Movie",
                "Slide",
                "Options",
            ]
            assert all(tab.property("visible") for tab in tabs)

            _kattints(window, qt_app, tabs[2])
            assert _varj(
                qt_app, lambda: _elem(window, "movieTabs").property("currentIndex") == 2
            ), (
                "az Options fül kattintása nem váltott át: "
                f"currentIndex={_elem(window, 'movieTabs').property('currentIndex')}, "
                f"gomb={tabs[2].property('x')}, {tabs[2].property('y')}, "
                f"{tabs[2].property('width')}×{tabs[2].property('height')}"
            )
            options_page = _elem(window, "movieTabPanelOptions")
            assert _varj(
                qt_app,
                lambda options_page=options_page: options_page.property("visible"),
            ), (
                "az Options lap nem látható: "
                f"active={options_page.property('active')}, "
                f"tab={_elem(window, 'movieTabs').property('currentIndex')}, "
                f"third={_elem(window, 'movieTabPanelThirdPage').property('visible')}"
            )
            controls = {
                "movieHeightBox": ("currentIndex", 3),
                "movieShowCaptions": ("checked", False),
                "movieCropToFit": ("checked", False),
                "movieShowDates": ("checked", False),
                "movieRemoveLowResFaces": ("checked", False),
                "movieSmartOrder": ("checked", True),
                "movieAlbumOrder": ("checked", False),
                "movieChronologicalOrder": ("checked", False),
                "lengthslider/scaleslider": ("value", 1.0),
                "burstslider/scaleslider": ("value", 0.0),
            }
            for name, (prop, expected) in controls.items():
                control = _elem(window, name)
                assert control.property("visible") is True, (
                    f"{name} nem látszik az Options fülön"
                )
                assert control.property(prop) == expected, (
                    f"{name}.{prop}: {control.property(prop)!r} != {expected!r}"
                )

            # A valódi egérkattintás igazolja, hogy az Opciók lapon lévő
            # vezérlő továbbra is működik, és nem csak a modell értékét mérjük.
            captions = _elem(window, "movieShowCaptions")
            _kattints(window, qt_app, captions)
            assert captions.property("checked") is True
            _kattints(window, qt_app, captions)
            assert captions.property("checked") is False

            screenshot = os.environ.get("PICASAPY_5670_SCREENSHOT")
            if screenshot and eltolás == 5:
                assert window.grabWindow().save(screenshot), (
                    f"a kiadáskép nem menthető: {screenshot}"
                )

            dialog.close()
            assert _varj(
                qt_app, lambda dialog=dialog: not dialog.property("visible")
            )
    finally:
        if dialog is not None:
            dialog.close()
            qt_app.processEvents()
        try:
            gen.close()
        except RuntimeError:
            pass
