"""#4577: a Címkék-panel „+" és fogaskerék gombja súgót kap, a gyorscímke-felirat „Quick Tags:".

A főablak kirajzolt felületét használja. A beviteli mezőt valódi egérkattintással
és billentyűzettel tölti ki, a gombokra valódi egérmozgatással mutat rá, és a
főablak magasságát ±5 képponttal is megmozgatja.
"""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import (
    QElapsedTimer,
    QObject,
    QPoint,
    QTranslator,
    QUrl,
    Qt,
)
from PySide6.QtQml import QQmlComponent
from PySide6.QtTest import QTest

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


def _click(window, item, qt_app):
    assert item.width() > 0 and item.height() > 0, "a kattintási cél mérete nulla"
    point = item.mapToScene(item.boundingRect().center()).toPoint()
    QTest.mouseClick(window, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, point)
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


def _varj_nyugalmi_helyzet(qt_app, item, timeout_ms: int = 3000) -> None:
    """Megvárja, míg a fiók csúszkázása véget ér: az elem helye egymás után kétszer ugyanaz.

    A fiók megnyitása animált, és a kattintás a mozgó helyre nem érne el.
    """
    utolso = []

    def nyugalom() -> bool:
        hely = (item.x(), item.y(), item.width(), item.height())
        mozdulatlan = bool(utolso) and utolso[-1] == hely
        utolso.append(hely)
        return mozdulatlan and item.isVisible()

    assert _wait_for(qt_app, nyugalom, timeout_ms), "a fiók nem állt meg nyitás után"


def _sugo_probe(engine, target):
    """A célelem csatolt ToolTip-jének állapota (szöveg, késleltetés, láthatóság)."""
    component = QQmlComponent(engine)
    component.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    function attachedTip() {
        return targetItem ? targetItem.ToolTip.toolTip : null
    }
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


def _buborek_hoverre(qt_app, window, probe, target) -> bool:
    """Az egeret a célra viszi, és kivárja, hogy a buborék megjelenjen."""
    pont = target.mapToScene(target.boundingRect().center()).toPoint()
    # előbb el a céltól: ugyanarra a pontra mozgatás nem ad belépést (hover)
    QTest.mouseMove(window, QPoint(1, 1))
    qt_app.processEvents()

    def ra_mutat() -> bool:
        QTest.mouseMove(window, pont)
        return bool(probe.property("isVisible"))

    # a 600 ms-os késleltetés a terhelt CI-gépen lassabban jár le
    return _wait_for(qt_app, ra_mutat, timeout_ms=8000)


def _buborek_eltunik(qt_app, window, probe) -> bool:
    QTest.mouseMove(window, QPoint(1, 1))
    return _wait_for(qt_app, lambda: not probe.property("isVisible"))


class TestCimkeSugo4577:
    def test_plusz_es_fogaskerek_sugo_es_quick_tags_felirat_magassagra_is(
        self, qml_app, qt_app
    ):
        window, _controller, engine = qml_app
        window.requestActivate()
        assert _wait_for(qt_app, lambda: window.isActive())
        window.setProperty("selectedIndexes", [0])
        window.setProperty("selectedIndex", 0)
        window.setProperty("activeDrawerTab", "tags")
        assert _wait_for(
            qt_app, lambda: window.findChild(QObject, "tagInput") is not None
        )
        eredeti_magassag = int(window.height())

        for eltolás in (-5, 0, 5):
            window.setHeight(eredeti_magassag + eltolás)
            qt_app.processEvents()

            mezo = _item(window, "tagInput")
            _varj_nyugalmi_helyzet(qt_app, mezo)
            _click(window, mezo, qt_app)
            assert mezo.property("activeFocus"), "a beviteli mező kattintásra nem kapott fókuszt"
            for betu in "alma":
                QTest.keyClick(window, getattr(Qt.Key, f"Key_{betu.upper()}"))
            qt_app.processEvents()
            assert mezo.property("text") == "alma", "a valódi billentyűzetes beírás nem jutott el"

            plusz = _item(window, "tagAddButton")
            assert _wait_for(
                qt_app, lambda plusz=plusz: bool(plusz.property("enabled"))
            ), (
                "a + gomb a beírt szöveg után sem kattintható"
            )
            plusz_sugo = _sugo_probe(engine, plusz)
            assert _buborek_hoverre(qt_app, window, plusz_sugo, plusz), (
                f"a + gomb buborékja nem jelent meg ({eltolás:+} px)"
            )
            assert plusz_sugo.property("tipDelay") == 600
            assert plusz_sugo.property("tipText") == (
                "Add tag to the currently selected items"
            )
            assert _buborek_eltunik(qt_app, window, plusz_sugo)

            fogaskerek = _item(window, "quickTagsGearButton")
            fogaskerek_sugo = _sugo_probe(engine, fogaskerek)
            assert _buborek_hoverre(qt_app, window, fogaskerek_sugo, fogaskerek), (
                f"a fogaskerék buborékja nem jelent meg ({eltolás:+} px)"
            )
            assert fogaskerek_sugo.property("tipDelay") == 600
            assert fogaskerek_sugo.property("tipText") == "Configure Quick Tags"
            assert _buborek_eltunik(qt_app, window, fogaskerek_sugo)

            felirat = _item(window, "quickTagsLabel")
            assert felirat.property("text") == "Quick Tags:"

            mezo.setProperty("text", "")
            qt_app.processEvents()


class TestCimkeSugoHuFordítas4577:
    def test_a_hivatalos_magyar_szoveg_van_a_qm_fajlban(self, qt_app):
        import picasapy.app

        qm = Path(picasapy.app.__file__).parent / "i18n" / "picasapy_hu.qm"
        translator = QTranslator()
        assert translator.load(str(qm)), f"nem tölthető be: {qm}"
        feliratok = {
            "Add tag to the currently selected items": (
                "Címke hozzáadása az aktuálisan kijelölt elemekhez"
            ),
            "Configure Quick Tags": "Gyorscímkék konfigurálása",
            "Quick Tags:": "Gyorscímkék:",
        }
        for forras, magyar in feliratok.items():
            assert translator.translate("TagsPanel", forras) == magyar, forras
