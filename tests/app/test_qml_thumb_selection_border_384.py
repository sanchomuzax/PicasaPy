"""QML-teszt: a kijelölt indexkép KÉTSZÍNŰ kerete (#384, constants.ui
thumbsel_color1/2) — a `test_qml_edits_mark.py` mintáját követve, önálló
komponens-betöltéssel.

A kijelöléskor két, a `frame` mögé rajzolt teli téglalap adja a "kívül
kék, belül fehér rés" hatást (`selectionOuter`/`selectionInner`) — a
színt közvetlenül a QML-property-n ellenőrizzük."""

from PySide6.QtCore import QObject, QUrl
from PySide6.QtQml import QQmlComponent, QQmlEngine, QQmlProperty

_KEEPALIVE = []


def _border_color(item):
    # a `border` egy QQuickPen* csoportos property — PySide6-ban nincs
    # rá konverter, ezért a pontozott útvonalat QQmlProperty-vel olvassuk
    # (ld. próba: `QQmlProperty(obj, "border.color").read()`).
    return QQmlProperty(item, "border.color").read().name()


def _make_delegate(qml_engine, **overrides):
    import picasapy.app.application as app_module

    properties = {
        "name": "a.jpg",
        "thumbUrl": "image://thumbs/1",
        "star": False,
        "caption": "",
        "isVideo": False,
        "index": 0,
        "keywords": "",
        "resolution": "320x160",
    }
    properties.update(overrides)
    comp = QQmlComponent(
        qml_engine,
        QUrl.fromLocalFile(
            str(app_module._APP_DIR / "qml" / "PicasaPy" / "ThumbDelegate.qml")
        ),
    )
    delegate = comp.createWithInitialProperties(properties)
    assert comp.errors() == [], [e.toString() for e in comp.errors()]
    assert delegate is not None
    QQmlEngine.setObjectOwnership(delegate, QQmlEngine.ObjectOwnership.CppOwnership)
    _KEEPALIVE.append(comp)
    _KEEPALIVE.append(delegate)
    return delegate


import pytest  # noqa: E402


@pytest.fixture
def qml_engine(qt_app):
    import picasapy.app.application as app_module

    engine = QQmlEngine()
    engine.addImportPath(str(app_module._APP_DIR / "qml"))
    yield engine
    engine.deleteLater()


class TestThumbSelectionRingHiddenByDefault:
    def test_rings_hidden_when_not_selected(self, qml_engine):
        delegate = _make_delegate(qml_engine, selected=False)
        outer = delegate.findChild(QObject, "thumbSelectionOuter")
        inner = delegate.findChild(QObject, "thumbSelectionInner")
        assert outer is not None and inner is not None
        assert outer.property("visible") is False
        assert inner.property("visible") is False

    def test_frame_border_is_plain_gray_when_not_selected(self, qml_engine):
        delegate = _make_delegate(qml_engine, selected=False)
        frame = delegate.findChild(QObject, "thumbFrame")
        assert _border_color(frame) == "#d9d9d9"


class TestThumbSelectionRingTwoColored:
    def test_rings_visible_when_selected(self, qml_engine):
        delegate = _make_delegate(qml_engine, selected=True)
        outer = delegate.findChild(QObject, "thumbSelectionOuter")
        inner = delegate.findChild(QObject, "thumbSelectionInner")
        assert outer.property("visible") is True
        assert inner.property("visible") is True

    def test_outer_ring_is_the_azure_selection_color(self, qml_engine):
        # constants.ui thumbsel_color1 = #009EFF
        delegate = _make_delegate(qml_engine, selected=True)
        outer = delegate.findChild(QObject, "thumbSelectionOuter")
        assert outer.property("color").name() == "#009eff"

    def test_inner_ring_is_the_card_white_not_the_azure(self, qml_engine):
        # constants.ui thumbsel_color2 = #FFFFFF (a kártya színe — nálunk
        # Theme.thumbCard, ami világos témán fehér)
        delegate = _make_delegate(qml_engine, selected=True)
        inner = delegate.findChild(QObject, "thumbSelectionInner")
        assert inner.property("color").name() == "#ffffff"
        assert inner.property("color").name() != "#009eff"

    def test_outer_ring_is_larger_than_the_inner_ring(self, qml_engine, qt_app):
        delegate = _make_delegate(qml_engine, selected=True)
        qt_app.processEvents()
        outer = delegate.findChild(QObject, "thumbSelectionOuter")
        inner = delegate.findChild(QObject, "thumbSelectionInner")
        assert outer.property("width") > inner.property("width")
        assert outer.property("height") > inner.property("height")

    def test_toggling_selected_shows_and_hides_the_rings(self, qml_engine, qt_app):
        delegate = _make_delegate(qml_engine, selected=False)
        outer = delegate.findChild(QObject, "thumbSelectionOuter")
        delegate.setProperty("selected", True)
        qt_app.processEvents()
        assert outer.property("visible") is True
        delegate.setProperty("selected", False)
        qt_app.processEvents()
        assert outer.property("visible") is False
