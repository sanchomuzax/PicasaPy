"""#4271: a Címkék-panel kiválasztásfüggő fejléce és gyorscímke-súgói.

A főablak kirajzolt felületét használja. A fotókat és a panel gombjait
valódi egérkattintással működteti; a nézőterület magasságát ±5 képponttal
is megmozgatja, hogy a próba ne egyetlen ablakméretre illeszkedjen.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    QObject,
    QPoint,
    QElapsedTimer,
    QTranslator,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

from picasapy.index import open_index, sync_tree
from support.jpeg_factory import make_jpeg

_KEEPALIVE = []


def _walk(item):
    for child in item.childItems():
        yield child
        yield from _walk(child)


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"A kirajzolt felületen nincs ilyen elem: {name}"
    return found


def _click(window, item, qt_app, modifiers=Qt.KeyboardModifier.NoModifier):
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    point = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, modifiers, point)
    qt_app.processEvents()


def _wait_for(qt_app, predicate, timeout_ms: int = 3000) -> bool:
    """Késleltetett QML-állapot kivárása határidős ciklussal."""
    timer = QElapsedTimer()
    timer.start()
    while timer.elapsed() < timeout_ms:
        qt_app.processEvents()
        if predicate():
            return True
        QTest.qWait(50)
    qt_app.processEvents()
    return bool(predicate())


def _thumb(window, row: int):
    for item in _walk(window.contentItem()):
        if item.objectName() != "thumbMouseArea":
            continue
        cell = item.parentItem()
        if cell is not None and int(cell.property("index")) == row:
            return item
    raise AssertionError(f"A(z) {row}. indexkép nem látható a főablakban")


def _tooltip_probe(engine, target):
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    function attachedTip() {
        return targetItem ? targetItem.ToolTip.toolTip : null
    }
    readonly property bool attachedVisible:
        targetItem ? targetItem.ToolTip.visible : false
    readonly property bool isVisible:
        attachedTip() ? attachedTip().visible : false
    readonly property string tipText:
        attachedTip() ? String(attachedTip().text) : ""
    readonly property int tipDelay:
        targetItem ? targetItem.ToolTip.delay : -1
}""",
        QUrl(),
    )
    assert component.isReady(), component.errors()
    probe = component.createWithInitialProperties({"targetItem": target})
    assert probe is not None, component.errors()
    _KEEPALIVE.extend((component, probe))
    return probe


def _make_three_photo_feed(window, controller, library, qt_app):
    make_jpeg(library / "c.jpg", size=(120, 90))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, str(library))
    controller._reload()
    controller.selectFolder(str(library))
    window.setProperty("selectedIndexes", [])
    window.setProperty("selectedIndex", -1)
    window.setProperty("activeDrawerTab", "tags")
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 3)
    qt_app.processEvents()


class TestCimkePanelFejlec4271:
    def test_a_harom_fejlec_valodi_kijelolessel_valtozik(
        self, qml_app, qt_app
    ):
        window, controller, _engine = qml_app
        library = Path(controller._roots[0])
        _make_three_photo_feed(window, controller, library, qt_app)
        heading = _item(window, "tagsSelectionHeading")
        eredeti_magassag = int(window.height())

        for eltolás in (-5, 0, 5):
            window.setHeight(eredeti_magassag + eltolás)
            qt_app.processEvents()

            _click(window, _thumb(window, 0), qt_app)
            assert window.property("selectedIndexes").toVariant() == [0]
            assert heading.property("text") == "Tags in a.jpg:"

            _click(
                window,
                _thumb(window, 1),
                qt_app,
                Qt.KeyboardModifier.ControlModifier,
            )
            assert window.property("selectedIndexes").toVariant() == [0, 1]
            assert heading.property("text") == "Tags in the current selection:"

            _click(
                window,
                _thumb(window, 2),
                qt_app,
                Qt.KeyboardModifier.ControlModifier,
            )
            assert window.property("selectedIndexes").toVariant() == [0, 1, 2]
            assert heading.property("text") == (
                "Tags in the current selection (whole album):"
            )


class TestGyorscimkeSugo4271:
    def test_a_feliratok_a_hivatalos_magyar_szoveget_hasznaljak(
        self, qt_app
    ):
        import picasapy.app

        qm = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.qm"
        translator = QTranslator()
        assert translator.load(str(qm)), f"nem tölthető be: {qm}"
        feliratok = {
            "Tags in %s:": "%s címkéi:",
            "Tags in the current selection:": "Címkék az aktuális kijelölésben:",
            "Tags in the current selection (whole album):": (
                "Címkék az aktuális kijelölésben (teljes album):"
            ),
            "Type in a tag (word or phrase) in the text box to the left "
            "of the button you just pressed.\n\n"
            "Then press the button again to add the tag to the selected "
            "items.\n\n"
            "(TIP: Press <ENTER> after you type in your tag to "
            "automatically add the tag without pressing the button)": (
                "Írjon be egy címkét (szót vagy kifejezést) a szövegmezőbe "
                "attól a gombtól balra, amelyre az imént kattintott.\n\n"
                "Ezután ismét kattintson a gombra, így hozzáadja a címkét "
                "a kijelölt elemekhez.\n\n"
                "(TIPP: Ha automatikusan, a gombra kattintás nélkül "
                "szeretné hozzáadni a megadott címkét, nyomja le az "
                "<ENTER> billentyűt.)"
            ),
            "Click to configure quick tags": (
                "Ide kattintva konfigurálhatja a gyorscímkéket"
            ),
            "Some of the text you entered could not be added as a tag.": (
                "A beírt szöveg egy része nem adható hozzá címkeként."
            ),
            "You have a fairly large number of items selected.\n\n"
            "Are you sure you want to apply this tag to all %d items?": (
                "Meglehetősen nagy számú elemet jelölt ki.\n\n"
                "Biztosan az összes (%d) elemre alkalmazni szeretné ezt a címkét?"
            ),
            "OK": "OK",
            "Cancel": "Mégse",
        }
        for forras, magyar in feliratok.items():
            contextus = (
                "Main"
                if forras.startswith("You have a fairly large number")
                or forras in {"OK", "Cancel"}
                else "TagsPanel"
            )
            assert translator.translate(contextus, forras) == magyar, forras

    def test_uresslot_kattintasa_tanit_es_hoverre_buborekot_mutat(
        self, qml_app, qt_app
    ):
        window, _controller, engine = qml_app
        window.requestActivate()
        assert _wait_for(qt_app, lambda: window.isActive())
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        window.setProperty("activeDrawerTab", "tags")
        assert _wait_for(
            qt_app,
            lambda: window.findChild(
                QObject, "quickTagButton0"
            )
            is not None,
        )
        button = _item(window, "quickTagButton0")
        eredeti_magassag = int(window.height())

        for eltolás in (-5, 0, 5):
            window.setHeight(eredeti_magassag + eltolás)
            qt_app.processEvents()
            assert _wait_for(qt_app, lambda: button.isVisible())
            assert button.property("text") == "?"
            assert button.isEnabled(), "az üres ? gomb nem kattintható"

            QTest.mouseMove(window, QPoint(1, 1))
            tip = _tooltip_probe(engine, button)

            def buborek_latszik_ra_mutataskor(tip=tip, button=button, window=window):
                pont = button.mapToScene(button.boundingRect().center()).toPoint()
                QTest.mouseMove(window, pont)
                return bool(button.property("hovered")) and bool(
                    tip.property("isVisible")
                )

            assert _wait_for(qt_app, buborek_latszik_ra_mutataskor), (
                f"a buborék nem jelent meg: attached={tip.property('attachedVisible')}, "
                f"hovered={button.property('hovered')}, "
                f"label={button.property('label')!r}, "
                f"text={tip.property('tipText')!r}, delay={tip.property('tipDelay')}"
            )
            assert tip.property("tipDelay") == 600
            assert tip.property("tipText") == "Click to configure quick tags"

            QTest.mouseMove(window, QPoint(1, 1))
            assert _wait_for(qt_app, lambda tip=tip: not tip.property("isVisible"))
            _click(window, button, qt_app)
            help_dialog = _item(window, "tagNoTextDialog")
            assert _wait_for(
                qt_app, lambda help_dialog=help_dialog: help_dialog.property("visible")
            )
            help_text = _item(window, "tagNoTextMessage")
            assert help_text.property("text") == (
                "Type in a tag (word or phrase) in the text box to the left "
                "of the button you just pressed.\n\n"
                "Then press the button again to add the tag to the selected "
                "items.\n\n"
                "(TIP: Press <ENTER> after you type in your tag to "
                "automatically add the tag without pressing the button)"
            )
            help_dialog.close()
            qt_app.processEvents()


@pytest.mark.parametrize("magassag_eltolas", [-5, 0, 5])
def test_tomeges_cimkezes_30_es_31_kepnel_megerositeses(
    qml_app, qt_app, magassag_eltolas
):
    """A 30/31-es küszöb és mindkét döntési ág valódi felületi kattintás."""
    window, controller, _engine = qml_app
    library = Path(controller._roots[0])
    for index in range(29):
        make_jpeg(library / f"tomeges_{index:02d}.jpg", size=(120, 90))
    with open_index(controller._db_path) as conn:
        sync_tree(conn, str(library))
    controller._reload()
    controller.selectFolder(str(library))
    window.setProperty("activeDrawerTab", "tags")
    window.setHeight(int(window.height()) + magassag_eltolas)
    assert _wait_for(qt_app, lambda: controller.photos.rowCount() == 31)

    # A kiválasztás pontos határértékét a teszt állítja be; a címkekérést,
    # a Mégsét és az OK-t tényleges felületi kattintás indítja.
    window.setProperty("selectedIndexes", list(range(30)))
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    def cimke_beirasa_es_kattintas(cimke):
        mező = _item(window, "tagInput")
        mező.setProperty("text", cimke)
        qt_app.processEvents()
        _click(window, _item(window, "tagAddButton"), qt_app)

    def minden_sor_tartalmazza(sorok, cimke):
        return all(
            cimke.casefold()
            in (controller.photos.photos[sor].keywords or "").casefold()
            for sor in sorok
        )

    cimke_beirasa_es_kattintas("harminc kep")
    assert window.findChild(QObject, "bulkTagConfirmDialog") is None
    assert _wait_for(
        qt_app, lambda: minden_sor_tartalmazza(range(30), "harminc kep")
    )

    window.setProperty("selectedIndexes", list(range(31)))
    qt_app.processEvents()
    cimke_beirasa_es_kattintas("harmincegy kep")
    dialog = window.findChild(QObject, "bulkTagConfirmDialog")
    assert dialog is not None, "31 kijelölt képnél meg kell jelennie a kérdésnek"
    assert _wait_for(qt_app, lambda: bool(dialog.property("visible")))
    assert dialog.property("message") == (
        "You have a fairly large number of items selected.\n\n"
        "Are you sure you want to apply this tag to all 31 items?"
    )

    _click(window, _item(window, "bulkTagConfirmCancelButton"), qt_app)
    assert _wait_for(qt_app, lambda: not dialog.property("visible"))
    assert not any(
        "harmincegy kep" in (photo.keywords or "").casefold()
        for photo in controller.photos.photos
    ), "a Mégse után egyetlen kijelölt képre sem kerülhet címke"

    cimke_beirasa_es_kattintas("harmincegy kep")
    assert _wait_for(qt_app, lambda: bool(dialog.property("visible")))
    _click(window, _item(window, "bulkTagConfirmOkButton"), qt_app)
    assert _wait_for(qt_app, lambda: not dialog.property("visible"))
    assert _wait_for(
        qt_app,
        lambda: minden_sor_tartalmazza(range(31), "harmincegy kep"),
    )
