"""A Pan and Zoom kattintásra elindul, és az eltolt kivágás látszik (#5258)."""

from itertools import cycle
import importlib.util

from PIL import Image
import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

from support.qt_wait import varj_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app


def _gyerek(gyoker, nev):
    from PySide6.QtCore import QObject

    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _mintakepeket_keszit(konyvtar):
    szelesseg, magassag = 800, 450
    pixelek = [
        (round(255 * x / (szelesseg - 1)), round(255 * y / (magassag - 1)), 30)
        for y in range(magassag)
        for x in range(szelesseg)
    ]
    for nev in ("a.png", "b.png"):
        kep = Image.new("RGB", (szelesseg, magassag))
        kep.putdata(pixelek)
        kep.save(konyvtar / nev)


def _kozep(elem):
    return elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))


def _lista_sor(lista, index):
    content = lista.property("contentItem")
    for item in content.childItems():
        if item.property("index") == index and item.property("modelData") is not None:
            if item.isVisible():
                return item
    return None


@pytest.fixture
def pan_zoom_app(qt_app, tmp_path, monkeypatch):
    """A rögzített, pozitív x-eltolás minden nézetmagasságon megmarad."""
    if importlib.util.find_spec("picasapy.app.slideshow_pan_zoom") is not None:
        from picasapy.app import slideshow_pan_zoom

        # A két forrás (helyi: csere-bitek és u, v; CRT: ρ0…ρ3) külön
        # sorozatot kap, hívási sorrendben: előbb a helyi, aztán a CRT.
        sorozatok = cycle([
            cycle([0.0, 0.0, 0.9, 0.1]),
            cycle([0.9, 0.9, 0.1, 0.1]),
        ])

        def forras_gyar():
            sorozat = next(sorozatok)
            return lambda: next(sorozat)

        monkeypatch.setattr(
            slideshow_pan_zoom, "_lcg_fraction_source", forras_gyar
        )
    yield from _build_qml_app(
        qt_app, tmp_path, kepeket_keszit=_mintakepeket_keszit
    )


@pytest.mark.parametrize(
    "delta", (-5, 0, 5), ids=("magassag-minus-5", "magassag-alap", "magassag-plus-5")
)
def test_kattintasra_a_pan_and_zoom_eltolt_kivagast_mutat(
    pan_zoom_app, qt_app, tmp_path, delta
):
    window, controller, _engine = pan_zoom_app
    vart_ablakmagassag = window.height() + delta
    window.setHeight(vart_ablakmagassag)
    assert varj_feltetelre(
        qt_app,
        lambda: abs(window.height() - vart_ablakmagassag) < 0.5,
        masodperc=10.0,
    ), f"az ablak nem vette fel a kért magasságot ({delta:+d} px)"
    show = _gyerek(window, "slideshowView")
    assert float(show.height()) > 0, "a vetítőnek nincs kirajzolási területe"

    controller.setSlideshowCaptionMode("none")
    controller.setSlideshowSeconds(30)
    QMetaObject.invokeMethod(
        show, "start", Qt.ConnectionType.DirectConnection, Q_ARG("QVariant", 0)
    )
    show.setProperty("playing", False)
    show.setProperty("transitionMs", 400)

    controls = _gyerek(window, "slideshowControls")
    combo = _gyerek(window, "slideshowTransitionBox")
    popup = _gyerek(window, "picasaComboPopup")
    lista = _gyerek(window, "picasaComboList")
    combo_pont = _kozep(combo)
    QTest.mouseMove(window, QPoint(round(combo_pont.x()), round(combo_pont.y())))
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") > 0, masodperc=10.0
    ), "a kattintás nem mutatta meg a vetítő vezérlősávját"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(combo_pont.x()), round(combo_pont.y())),
    )
    assert varj_feltetelre(
        qt_app, lambda: popup.property("visible"), masodperc=10.0
    ), "a Pan and Zoom választó nem nyílt ki"
    sor = _lista_sor(lista, 1)
    assert sor is not None and sor.property("modelData") == "Pan and Zoom"
    sor_ablaka = sor.window()
    sor_pont = _kozep(sor)
    QTest.mouseClick(
        sor_ablaka,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(sor_pont.x()), round(sor_pont.y())),
    )
    assert varj_feltetelre(
        qt_app,
        lambda: controller.property("slideshowTransition") == "kenburns",
        masodperc=10.0,
    ), "a valódi kattintás nem választotta ki a Pan and Zoom átmenetet"

    next_button = _gyerek(window, "slideshowNextButton")
    next_pont = _kozep(next_button)
    QTest.mouseMove(window, QPoint(round(next_pont.x()), round(next_pont.y())))
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") > 0, masodperc=10.0
    ), "a következő gomb nem vált láthatóvá"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(next_pont.x()), round(next_pont.y())),
    )
    assert varj_feltetelre(
        qt_app, lambda: show.property("currentIndex") == 1, masodperc=10.0
    ), "a kattintás nem indította el a következő diát"
    slide = _gyerek(window, "slideshowImage")
    transition = _gyerek(window, "slideshowTransition")
    assert varj_feltetelre(
        qt_app,
        lambda: slide.property("implicitWidth") > 0,
        masodperc=10.0,
    ), (
        "a Pan and Zoom átmenet nem töltötte be a bejövő képet: "
        f"implicitWidth={slide.property('implicitWidth')}, "
        f"source={slide.property('source').toString()}"
    )
    assert varj_feltetelre(
        qt_app, lambda: not transition.property("running"), masodperc=10.0
    ), "a Pan and Zoom átmenet nem fejeződött be"
    assert float(slide.property("opacity")) > 0.99, (
        f"a bejövő kép nem vált láthatóvá: opacity={slide.property('opacity')}"
    )

    ablak_kep = window.grabWindow()
    assert not ablak_kep.isNull(), "a diavetítés képernyőképe üres"
    kozeppont = show.mapToScene(QPointF(show.width() / 2, show.height() / 2))
    dpr = ablak_kep.devicePixelRatio()
    kozeppont_szin = ablak_kep.pixelColor(
        round(kozeppont.x() * dpr), round(kozeppont.y() * dpr)
    )
    # A forrás közepe R≈128; a kivágás a saját alaptéglalapja közepéről indul,
    # a ρ-eltolással, így a jobbra tolt kivágás ennél világosabb.
    assert kozeppont_szin.red() > 128, (
        "a kirajzolt kivágás közepe nem tolódott el a forrás közepétől: "
        f"R={kozeppont_szin.red()}"
    )
    assert float(slide.property("x")) < -3, (
        "a képkeret nem mozdult el a középre igazított helyéről"
    )
    assert float(slide.property("width")) > float(show.width()) + 3
    assert ablak_kep.save(str(tmp_path / "5258-pan-and-zoom.png")), (
        "a Pan and Zoom kiadási képernyőképe nem menthető"
    )
