"""A diavetítés eredeti 22 átmenete kattintással választható és lejátszható (#4567)."""

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest
import pytest

from support.qt_wait import varj_feltetelre


_ATMENETKULCSOK = (
    "cut",
    "dissolve",
    "dissolveblack",
    "dissolvewhite",
    "wipeleft",
    "wiperight",
    "wipeup",
    "wipedown",
    "diagwipeul",
    "diagwipeur",
    "diagwipedl",
    "diagwipedr",
    "pushleft",
    "pushright",
    "pushtop",
    "pushdown",
    "circlein",
    "circleout",
    "rect",
    "kenburns",
    "kenburnsaoi",
    "timelapse",
)
_ATMENET_NEVEK = (
    "Cut",
    "Dissolve",
    "Dissolve through black",
    "Dissolve through white",
    "Wipe - left",
    "Wipe",
    "Wipe - top",
    "Wipe - bottom",
    "Wipe - up left",
    "Wipe - up right",
    "Wipe - down left",
    "Wipe - down right",
    "Push - left",
    "Push",
    "Push - top",
    "Push - bottom",
    "Circle - inwards",
    "Circle",
    "Rectangle",
    "Pan and Zoom",
    "Pan and Zoom - face",
    "Time Lapse",
)


def _gyerek(gyoker, nev):
    obj = gyoker.findChild(QObject, nev)
    assert obj is not None, f"{nev} nem található"
    return obj


def _kozep(item):
    return item.mapToScene(QPointF(item.width() / 2, item.height() / 2))


def _kattint(window, item):
    # A Qt Popup külön QQuickWindow-ban is megjelenhet. A sort a saját
    # ablakában kell kattintani; a főablakra küldött, globálisra visszamappelt
    # esemény a popupon kívülre eshet és bezárhatja azt.
    cel_ablak = item.window()
    pont = _kozep(item)
    QTest.mouseClick(
        cel_ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )


def _sor_index_szerint(lista, index):
    content = lista.property("contentItem")
    for item in content.childItems():
        if item.property("index") == index and item.property("modelData") is not None:
            if item.isVisible():
                return item
    return None


def _atmenet_kivalaszt(window, qt_app, combo, controls, popup, lista, index):
    QTest.mouseMove(window, QPoint(1, 1))
    qt_app.processEvents()
    pont = _kozep(combo)
    QTest.mouseMove(window, QPoint(round(pont.x()), round(pont.y())))
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") > 0, masodperc=3
    ), "az egérmozgatás nem jelenítette meg a vezérlősávot"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    assert varj_feltetelre(
        qt_app, lambda: popup.property("visible"), masodperc=3
    ), "az átmenetválasztó nem nyílt ki"

    tartalommagas = float(lista.property("contentHeight"))
    lista_magas = float(lista.property("height"))
    sor_magas = tartalommagas / len(_ATMENETKULCSOK)
    cel_y = max(
        0.0,
        min(
            index * sor_magas - (lista_magas - sor_magas) / 2,
            tartalommagas - lista_magas,
        ),
    )
    lista.setProperty("contentY", cel_y)
    assert varj_feltetelre(
        qt_app,
        lambda: _sor_index_szerint(lista, index) is not None,
        masodperc=3,
    ), f"a(z) {index}. átmenetsor nem jelent meg a listában"
    sor = _sor_index_szerint(lista, index)
    assert sor.property("modelData") == _ATMENET_NEVEK[index], (
        f"a specifikációs felirat nem stimmel a(z) {index}. átmenethez"
    )
    _kattint(window, sor)


@pytest.mark.parametrize(
    ("index", "kulcs"),
    list(enumerate(_ATMENETKULCSOK)),
    ids=_ATMENETKULCSOK,
)
def test_minden_atmenet_kattintassal_valaszthato_es_lejatszhato(
    qml_app, qt_app, index, kulcs
):
    window, controller, _engine = qml_app
    show = _gyerek(window, "slideshowView")
    combo = _gyerek(window, "slideshowTransitionBox")
    popup = _gyerek(window, "picasaComboPopup")
    lista = _gyerek(window, "picasaComboList")
    controls = _gyerek(window, "slideshowControls")
    next_button = _gyerek(window, "slideshowNextButton")
    animation = _gyerek(window, "slideshowTransition")
    previous_image = _gyerek(window, "slideshowPrevImage")
    slideshow_image = _gyerek(window, "slideshowImage")
    assert combo.property("count") == 22, (
        "a specifikáció vetítési átmenet-készlete 22 tétel "
        "(docs/specs/picasa-create-features.md, 3764–3794)"
    )

    controller.setSlideshowLoop(True)
    controller.setSlideshowTransition(kulcs)
    show.setProperty("currentIndex", 0)
    show.setProperty("visible", True)
    assert varj_feltetelre(
        qt_app, lambda: show.property("visible"), masodperc=5
    ), "a diavetítés nem vált láthatóvá"
    show.setProperty("playing", False)
    show.setProperty("transitionMs", 400)
    assert varj_feltetelre(
        qt_app, lambda: show.property("transitionKind") == kulcs
    )
    alapmagassag = window.height()
    for delta in (-5, 0, 5):
        window.setHeight(alapmagassag + delta)
        assert varj_feltetelre(
            qt_app,
            lambda: abs(show.height() - window.height()) < 0.5,
            masodperc=3,
        ), f"a vetítő nem követte az ablakmagasságot ({delta:+d} px)"
        assert controls.y() + controls.height() <= show.height() + 3, (
            f"a vezérlősáv kilóg a vetítőből ({delta:+d} px)"
        )
    kattintasi_elteres = -5 if index < 8 else (0 if index < 16 else 5)
    window.setHeight(alapmagassag + kattintasi_elteres)
    qt_app.processEvents()

    pont = _kozep(next_button)
    QTest.mouseMove(window, QPoint(round(pont.x()), round(pont.y())))
    assert varj_feltetelre(
        qt_app, lambda: controls.property("opacity") > 0, masodperc=3
    ), "az egérmozgatás nem jelenítette meg a vezérlősávot"
    elozo_index = int(show.property("currentIndex"))
    _kattint(window, next_button)
    assert varj_feltetelre(
        qt_app,
        lambda: show.property("currentIndex") != elozo_index,
        masodperc=3,
    ), f"a következő gomb nem váltott képet ({kulcs})"
    if kulcs == "cut":
        assert animation.property("running") is False
    elif kulcs.startswith("wipe") or kulcs.startswith("diagwipe"):
        assert varj_feltetelre(
            qt_app,
            lambda: slideshow_image.property("opacity") < 0.99,
            masodperc=3,
        ), f"a wipe nem fedte fel az új képet ({kulcs})"
        assert varj_feltetelre(
            qt_app,
            lambda: previous_image.property("x") != 0
            or previous_image.property("y") != 0,
            masodperc=3,
        ), f"a wipe nem mozgatta ki a régi képet ({kulcs})"
    else:
        assert varj_feltetelre(
            qt_app, lambda: animation.property("running"), masodperc=3
        ), f"a kiválasztott átmenet nem indított lejátszást: {kulcs}"
        assert varj_feltetelre(
            qt_app,
            lambda: not animation.property("running"),
            masodperc=3,
        ), f"az átmenet animációja nem fejeződött be: {kulcs}"

    masik = "cut" if kulcs != "cut" else "dissolve"
    controller.setSlideshowTransition(masik)
    _atmenet_kivalaszt(
        window, qt_app, combo, controls, popup, lista, index
    )
    assert varj_feltetelre(
        qt_app,
        lambda: controller.property("slideshowTransition") == kulcs,
        masodperc=3,
    ), f"a kattintás nem választotta ki ezt az átmenetet: {kulcs}"
