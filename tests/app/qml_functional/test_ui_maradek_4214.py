"""#4214: a maradék címke-, lista-, film- és nyomtatási elemek kimenete."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import (
    QCoreApplication,
    QEvent,
    QPointF,
    Qt,
    QObject,
    QTranslator,
)
from PySide6.QtGui import QKeyEvent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    translator = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert translator.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(translator)
    yield
    qt_app.removeTranslator(translator)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML-főablak a magyar fordító telepítése után épüljön fel."""
    return qml_app

def _walk(item: QQuickItem):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(root, name: str):
    found = root.findChild(QObject, name)
    if found is not None:
        return found
    if isinstance(root, QQuickItem):
        found = next((item for item in _walk(root) if item.objectName() == name), None)
        if found is not None:
            return found
    elif hasattr(root, "contentItem"):
        content = root.contentItem()
        found = next((item for item in _walk(content) if item.objectName() == name), None)
        if found is not None:
            return found
    assert found is not None, f"{name} nem található"
    return found


def _qml_class_names(item) -> list[str]:
    names = []
    meta = item.metaObject()
    while meta is not None:
        names.append(meta.className())
        meta = meta.superClass()
    return names


def _wait_for(qt_app, condition, timeout: float = 3.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        QCoreApplication.processEvents()
        if condition():
            return True
        QTest.qWait(50)
    QCoreApplication.processEvents()
    return bool(condition())


def _click(item, *, x_fraction: float = 0.5, y_fraction: float = 0.5) -> None:
    window = item.window()
    point = item.mapToScene(
        QPointF(item.width() * x_fraction, item.height() * y_fraction)
    ).toPoint()
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        point,
    )
    QCoreApplication.processEvents()


def _drag_slider(item, target_fraction: float) -> None:
    window = item.window()
    left_padding = float(item.property("leftPadding"))
    available_width = float(item.property("availableWidth"))
    handle_width = float(item.property("handleWidth"))
    travel = available_width - handle_width
    position = float(item.property("visualPosition"))
    start = item.mapToScene(
        QPointF(
            left_padding + handle_width / 2 + travel * position,
            item.height() / 2,
        )
    ).toPoint()
    target = item.mapToScene(
        QPointF(item.width() * target_fraction, item.height() / 2)
    ).toPoint()
    QTest.mousePress(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, start
    )
    QCoreApplication.processEvents()
    QTest.mouseMove(window, target)
    QCoreApplication.processEvents()
    QTest.mouseRelease(
        window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, target
    )
    QCoreApplication.processEvents()


def _slider_value_at_fraction(item, fraction: float) -> float:
    left_padding = float(item.property("leftPadding"))
    available_width = float(item.property("availableWidth"))
    handle_width = float(item.property("handleWidth"))
    travel = available_width - handle_width
    local_x = float(item.width()) * fraction
    return max(0.0, min(1.0, (local_x - left_padding - handle_width / 2) / travel))


def _type_text(window, text: str) -> None:
    for character in text:
        event = QKeyEvent(
            QEvent.Type.KeyPress,
            ord(character.upper()),
            Qt.KeyboardModifier.NoModifier,
            character,
        )
        QCoreApplication.sendEvent(window, event)
        QCoreApplication.sendEvent(
            window,
            QKeyEvent(
                QEvent.Type.KeyRelease,
                ord(character.upper()),
                Qt.KeyboardModifier.NoModifier,
                character,
            ),
        )
    QCoreApplication.processEvents()


def _select_first_photo(window, qt_app) -> None:
    # A tesztkép kiválasztása csak a párbeszéd előfeltétele; a lefedett
    # felületi műveleteket lent valódi egérkattintással végezzük.
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()


def _open_print_options(window, qt_app):
    _select_first_photo(window, qt_app)
    _click(_item(window, "trayPrintButton"))
    dialog = _item(window, "printDialog")
    assert _wait_for(qt_app, lambda: dialog.property("visible") is True), (
        "a Fájl → Nyomtatás kattintása nem nyitotta meg a párbeszédet"
    )
    _click(_item(dialog, "printOptionsButton"))
    panel = _item(dialog, "printOptionsPanel")
    assert _wait_for(qt_app, lambda: panel.property("visible") is True), (
        "a nyomtatási opciók gombja nem nyitotta meg a panelt"
    )
    scroll = _item(panel, "printOptionScrollView")
    content = scroll.property("contentItem")
    content_y = max(
        0.0,
        float(content.property("contentHeight")) - float(scroll.height()),
    )
    content.setProperty("contentY", content_y)
    QCoreApplication.processEvents()
    return dialog, panel


def _visible_texts(root) -> list[str]:
    if isinstance(root, QQuickItem):
        items = _walk(root)
    else:
        items = _walk(root.contentItem())
    return [
        str(item.property("text"))
        for item in items
        if item.isVisible() and item.property("text") is not None
    ]


def test_tagpanel_input_es_keywordlist_valodi_kattintassal_minden_magassagon(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    _select_first_photo(window, qt_app)
    window.setProperty("activeDrawerTab", "tags")
    tags_panel = _item(window, "tagsPanel")
    assert _wait_for(qt_app, lambda: float(tags_panel.width()) > 100), (
        "a címkefiók nem nyílt ki a határidőn belül"
    )
    assert _item(window, "rightDrawerTitle").property("text") == "Tags:"
    assert _item(tags_panel, "input_group").isVisible()
    assert _item(tags_panel, "taglist_group").isVisible()
    base_height = int(window.height())

    for elteres in (-5, 0, 5):
        window.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        tag_input = _item(tags_panel, "tagInput")
        _click(tag_input)
        assert tag_input.property("activeFocus") is True
        tag_name = f"jegy4214_{elteres}"
        _type_text(window, tag_name)
        assert tag_input.property("text") == tag_name
        _click(_item(tags_panel, "tagAddButton"))
        assert _wait_for(
            qt_app,
            lambda tag_name=tag_name: tag_name
            in list(tags_panel.property("tags")),
        ), f"a címkelista nem jelenítette meg: {tag_name}"
        tag_list = _item(tags_panel, "tagList")
        assert int(tag_list.property("count")) > 0
        _item(tags_panel, f"tagRemove-{tag_name}")


def test_propertiespanel_lista_a_fooldal_fiokaban_minden_magassagon(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    _select_first_photo(window, qt_app)
    window.setProperty("activeDrawerTab", "properties")
    panel = _item(window, "propertiesPanel")
    assert _wait_for(qt_app, lambda: float(panel.width()) > 100), (
        "a tulajdonságfiók nem nyílt ki a határidőn belül"
    )
    base_height = int(window.height())

    for elteres in (-5, 0, 5):
        window.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        assert panel.property("visible") is True
        assert _item(window, "rightDrawerTitle").property("text") == "Properties"
        rows = _item(panel, "propertyList")
        assert int(rows.property("count")) > 0
        assert _wait_for(
            qt_app,
            lambda rows=rows: any(
                text == "File Path" for text in _visible_texts(rows)
            ),
        ), "a kijelölt kép fájlútvonala nem látszik a tulajdonságlistában"


def test_movie_duracio_es_atfedes_picasa_slider_kattintassal_minden_magassagon(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    _select_first_photo(window, qt_app)
    base_height = int(window.height())

    for elteres in (-5, 0, 5):
        window.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        _click(_item(window, "trayMovieButton"))
        movie_dialog = _item(window, "movieDialog")
        assert _wait_for(
            qt_app, lambda movie_dialog=movie_dialog: movie_dialog.property("visible") is True
        ), "a Filmkészítő gomb nem nyitotta meg a párbeszédet"
        assert _item(movie_dialog, "movieTabMotion").property("text") == "Movie"

        duration = _item(movie_dialog, "movieSeconds")
        overlap = _item(movie_dialog, "movieOverlapSlider")
        assert "PicasaSlider" in duration.metaObject().className(), (
            "a Dia időtartama vezérlő még nem a közös PicasaSlider"
        )
        assert "PicasaSlider" in overlap.metaObject().className(), (
            "az Átfedés vezérlő még nem a közös PicasaSlider"
        )
        duration.setProperty("value", 30)
        overlap.setProperty("value", 0.2)
        assert _item(movie_dialog, "movieSecondsValueLabel").property("text") == (
            "3.0 Sec"
        )
        for slider, label in ((duration, "Dia időtartama"), (overlap, "Átfedés")):
            before = float(slider.property("value"))
            _click(slider, x_fraction=0.75)
            after = float(slider.property("value"))
            assert after != before, (
                f"a {label} csúszka valódi kattintásra nem változtatta meg "
                f"az értéket ({before} → {after})"
            )
        movie_dialog.close()
        assert _wait_for(
            qt_app, lambda movie_dialog=movie_dialog: movie_dialog.property("visible") is False
        ), "a Filmkészítő párbeszéd bezárása nem fejeződött be"


def test_spacing_slider_a_kozos_picasa_slider_a_fooldalrol(
    qml_app, qt_app
):
    window, controller, _engine = qml_app
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    # A térköz-csoport a képességmaszk szerint a három rács-témánál látszik;
    # a Képkupacnál rejtett. Itt a Mozaik adja a látható felhasználói állapotot.
    controller.setCollageTheme("picturegrid")
    qt_app.processEvents()
    _click(_item(window, "trayCollageButton"))

    assert _wait_for(
        qt_app,
        lambda: window.findChild(QObject, "collageSettingsTab") is not None,
    ), "a főablak nem töltötte be a Kollázs beállításlapját"
    settings_tab = _item(window, "collageSettingsTab")
    slider = _item(settings_tab, "collageSpacingSlider")
    assert _wait_for(qt_app, lambda: slider.isVisible()), (
        "a Kollázs lap térköz-csúszkája nem jelent meg"
    )
    assert "PicasaSlider" in slider.metaObject().className(), (
        "a spacing_slider/bigslider még nem a közös PicasaSlider"
    )

    base_height = int(window.height())
    for elteres in (-5, 0, 5):
        window.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        slider.setProperty("value", 0.2)
        _wait_for(
            qt_app,
            lambda: abs(float(controller.property("collageSpacing")) - 0.2)
            < 0.0005,
        )
        _click(slider, x_fraction=0.8)
        assert _wait_for(
            qt_app,
            lambda: abs(float(controller.property("collageSpacing")) - 0.8)
            < 0.03,
        ), "a térközcsúszka valódi kattintása nem jutott el a kollázs-beállításig"


def test_zoom_es_szoveg_atlatszosag_csuszka_valodi_kattintassal(
    qml_app, qt_app
):
    window, _controller, engine = qml_app
    _select_first_photo(window, qt_app)
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    QCoreApplication.processEvents()
    zoom_slider = _item(window, "zoomSlider")
    assert _wait_for(qt_app, lambda: zoom_slider.isVisible()), (
        "a nagyításcsúszka nem jelent meg a szerkesztő nézőben"
    )
    assert any("PicasaSlider" in name for name in _qml_class_names(zoom_slider)), (
        "a zoomslider/scaleslider nem a PicasaSlider közös alapjára épül"
    )
    edit_controller = engine.rootContext().contextProperty("editController")
    assert _wait_for(
        qt_app,
        lambda: edit_controller.property("previewSource").startswith(
            "image://editpreview/"
        ),
    ), "a néző nem indította el a szerkesztési munkamenetet"
    editor_panel = _item(window, "viewerEditorPanel")
    editor_panel.setProperty("textActive", True)
    opacity_slider = _item(window, "textOpacitySlider")
    assert _wait_for(qt_app, lambda: opacity_slider.isVisible()), (
        "a szöveg átlátszóságcsúszkája nem jelent meg"
    )
    assert any(
        "PicasaSlider" in name for name in _qml_class_names(opacity_slider)
    ), "a textopacityslider/scaleslider nem a PicasaSlider közös alapjára épül"

    base_height = int(window.height())
    for elteres, fraction in zip(
        (-5, 0, 5), (0.25, 0.65, 0.9), strict=True
    ):
        window.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        zoom_expected = _slider_value_at_fraction(zoom_slider, fraction)
        _drag_slider(zoom_slider, fraction)
        assert _wait_for(
            qt_app,
            lambda zoom_expected=zoom_expected: abs(
                float(zoom_slider.property("value")) - zoom_expected
            )
            < 0.03,
        ), "a nagyításcsúszka valódi egérmozgásra nem mozdult"

        opacity_expected = _slider_value_at_fraction(opacity_slider, fraction)
        opacity_before = float(edit_controller.property("textOpacity"))
        _drag_slider(opacity_slider, fraction)
        assert _wait_for(
            qt_app,
            lambda opacity_expected=opacity_expected: abs(
                float(edit_controller.property("textOpacity")) - opacity_expected
            )
            < 0.03,
        ), (
            "a szöveg átlátszóságcsúszkája valódi kattintásra nem mozdult "
            f"({opacity_before})"
        )
    assert viewer.property("zoomMode") == "custom"


def test_nyomtatas_feliratok_angolul_a_fooldalrol_kattintva_minden_magassagon(
    qml_app, qt_app
):
    window, _controller, _engine = qml_app
    dialog, panel = _open_print_options(window, qt_app)
    base_height = int(dialog.height())

    for elteres in (-5, 0, 5):
        dialog.setHeight(base_height + elteres)
        QCoreApplication.processEvents()
        assert _item(panel, "printOptionBottomOnlyCheckBox").property("text") == (
            "Bottom only"
        )
        assert _item(panel, "printOptionEvenBorderCheckBox").property("text") == (
            "Even width border"
        )
        assert _item(panel, "printOptionBorderSizeLabel").property("text") == (
            "Border width"
        )
        assert _item(panel, "printOptionBorderMaxLabel").property("text") == (
            "Max."
        )
    dialog.close()
    assert _wait_for(qt_app, lambda: dialog.property("visible") is False)


def test_nyomtatas_feliratok_hivatalos_magyarul(qml_app_magyar, qt_app):
    window, _controller, _engine = qml_app_magyar
    dialog, panel = _open_print_options(window, qt_app)
    assert _item(panel, "printOptionBottomOnlyCheckBox").property("text") == (
        "Csak alul"
    )
    assert _item(panel, "printOptionEvenBorderCheckBox").property("text") == (
        "Egyenletes szélességű szegély"
    )
    assert _item(panel, "printOptionBorderSizeLabel").property("text") == (
        "Szegély szélessége"
    )
    assert _item(panel, "printOptionBorderMaxLabel").property("text") == (
        "Maximális"
    )
    dialog.close()
    assert _wait_for(qt_app, lambda: dialog.property("visible") is False)


def test_film_diaido_es_mertekegyseg_hivatalos_magyarul(qml_app_magyar, qt_app):
    window, _controller, _engine = qml_app_magyar
    _select_first_photo(window, qt_app)
    _click(_item(window, "trayMovieButton"))
    dialog = _item(window, "movieDialog")
    assert _wait_for(qt_app, lambda: dialog.property("visible") is True)
    assert _item(dialog, "movieTabMotion").property("text") == "Mozgófilm"
    assert _item(dialog, "movieSecondsValueLabel").property("text") == "3.0 mp"
    dialog.close()
    assert _wait_for(qt_app, lambda: dialog.property("visible") is False)
