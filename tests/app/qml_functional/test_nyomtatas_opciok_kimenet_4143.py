"""A #4143 nyomtatási opciói főablakos kattintással frissítik az előnézetet."""

from __future__ import annotations

import time
from pathlib import Path

import pytest
from PySide6.QtCore import QCoreApplication, QPointF, QMetaObject, Qt, QObject, QTranslator, QUrl
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest


@pytest.fixture
def magyar_forditas(qt_app):
    from picasapy.app import application

    fordito = QTranslator(qt_app)
    qm = Path(application.__file__).parent / "i18n" / "picasapy_hu.qm"
    assert fordito.load(str(qm)), f"a magyar fordítás nem tölthető be: {qm}"
    assert qt_app.installTranslator(fordito)
    yield
    qt_app.removeTranslator(fordito)


@pytest.fixture
def qml_app_magyar(magyar_forditas, qml_app):
    """A QML-ablak a magyar fordító telepítése után töltődjön be."""
    return qml_app


def _child(root, name):
    child = root.findChild(QObject, name)
    if child is None and isinstance(root, QQuickItem):
        pending = list(root.childItems())
        while pending:
            candidate = pending.pop()
            if candidate.objectName() == name:
                child = candidate
                break
            pending.extend(candidate.childItems())
    assert child is not None, f"{name} nem található"
    return child


def _variant(value):
    return value.toVariant() if hasattr(value, "toVariant") else value


def _click(item, *, x_fraction=0.5, y_fraction=0.5):
    ablak = item.window()
    pont = item.mapToScene(
        QPointF(item.width() * x_fraction, item.height() * y_fraction)
    ).toPoint()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    QCoreApplication.processEvents()


def _hataridon_belul(feltetel, *, masodperc=3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        QCoreApplication.processEvents()
        if feltetel():
            return True
        QTest.qWait(50)
    QCoreApplication.processEvents()
    return bool(feltetel())


def _szovegszin_kivalasztasa(panel, dialog, popup, szinindex, vart_szin):
    elozo_szin = _variant(panel.property("options"))["textColor"]
    _click(_child(panel, "printOptionTextColorBevel"))
    assert _hataridon_belul(
        lambda: popup.property("visible") is True
    ), "a szövegszín-választó nem nyílt meg"
    szinminta = _child(popup, f"printOptionTextColor{szinindex}")
    minta_kozepe = szinminta.mapToItem(
        panel, QPointF(szinminta.width() / 2, szinminta.height() / 2)
    )
    popup_x = float(popup.property("x"))
    popup_y = float(popup.property("y"))
    popup_width = float(popup.property("width"))
    popup_height = float(popup.property("height"))
    assert (
        popup_x - 3 <= minta_kozepe.x() <= popup_x + popup_width + 3
        and popup_y - 3 <= minta_kozepe.y() <= popup_y + popup_height + 3
    ), (
        "a popup befoglaló téglalapja nem fedi a kattintott színmintát: "
        f"minta=({minta_kozepe.x():.1f}, {minta_kozepe.y():.1f}), "
        f"popup=({popup_x:.1f}, {popup_y:.1f}, "
        f"{popup_width:.1f}, {popup_height:.1f}), "
        f"ablak=({dialog.width()}, {dialog.height()})"
    )
    assert elozo_szin != vart_szin, "a próbaszíneknek váltakozniuk kell"
    _click(szinminta)
    assert _hataridon_belul(
        lambda vart_szin=vart_szin: _variant(
            panel.property("options")
        )["textColor"]
        == vart_szin
    ), f"a {szinindex}. színminta kattintása nem frissítette a színt"
    assert _hataridon_belul(
        lambda: popup.property("visible") is False
    ), "a szövegszín-választó nem záródott be a kattintás után"
    assert panel.property("textColorPickerRequested") is False


def _megnyit_nyomtatas(window, qt_app):
    window.setProperty("selectedIndexes", [0])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    QMetaObject.invokeMethod(
        _child(window, "menuFilePrint"),
        "triggered",
        Qt.ConnectionType.DirectConnection,
    )
    qt_app.processEvents()
    return _child(window, "printDialog")


def _elo_nezeti_kep(dialog):
    forras = str(dialog.property("previewSource"))
    url = QUrl(forras)
    assert url.isValid() and url.toLocalFile(), (
        "nincs nyomtatási előnézeti kép: "
        f"rows={_variant(dialog.property('rows'))}, "
        f"oldalak={dialog.property('printPageCount')}, "
        f"hibaszöveg={dialog.property('lastError')}"
    )
    kep = QImage(url.toLocalFile()).convertToFormat(QImage.Format.Format_RGB32)
    assert not kep.isNull(), "a nyomtatási előnézet képe nem tölthető be"
    return kep


class TestNyomtatasOpcioKimenet:
    def test_kattintas_es_magassagvaltozas_utan_a_valasztas_a_lapon_latszik(
        self, qml_app_magyar, qt_app, monkeypatch, tmp_path
    ):
        # A Qt-előnézet gyorstárja is maradjon a pytest írható ideiglenes
        # területén, ne a felhasználó könyvtárában.
        monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path / "qt-cache"))
        main_window, _controller, _engine = qml_app_magyar
        dialog = _megnyit_nyomtatas(main_window, qt_app)
        panel = _child(dialog, "printOptionsPanel")

        _click(_child(dialog, "printOptionsButton"))
        assert panel.property("visible") is True

        felirat = _child(panel, "printOptionCaptionLabel")
        assert felirat.property("text") == "Képfeliratok"
        szinvalaszto = _child(panel, "printOptionTextPickerPanel")
        assert szinvalaszto.property("visible") is False

        _click(_child(panel, "printOptionSource2"))

        # A 420 px-es párbeszédablakban az utolsó sorra görgetünk: ez
        # reprodukálja a CI-ben levágott, alul megnyíló választót.
        dialog.setHeight(425)
        qt_app.processEvents()
        scroll = _child(panel, "printOptionScrollView")
        tartalom = scroll.property("contentItem")
        tartalommagassag = float(tartalom.property("contentHeight"))
        scrollmagassag = float(scroll.height())
        tartalom.setProperty("contentY", max(0.0, tartalommagassag - scrollmagassag))
        qt_app.processEvents()
        _szovegszin_kivalasztasa(
            panel, dialog, szinvalaszto, 4, 0xFF00AA00
        )

        # A CI ablakmagasságát ±5 px-en is bejárjuk. A nagy nézetben minden
        # opció kezelhető, így a próba a teljes kattintásos utat is lefedi.
        dialog.setHeight(800)
        qt_app.processEvents()
        alapmagassag = int(dialog.height())
        for elteres in (-5, 0, 5):
            dialog.setHeight(alapmagassag + elteres)
            qt_app.processEvents()
            _click(_child(panel, "printOptionSource0"))
            assert _variant(panel.property("options"))["textSource"] == 0

        _click(_child(dialog, "printOptionSource2"))
        _click(_child(dialog, "printOptionPlacement0"))
        _click(_child(dialog, "printOptionWrapCheckBox"))

        # Minden magasságnál más színre váltunk; a végső piros kell az
        # előnézeti kimenet-őrnek is.
        for elteres, szinindex, vart_szin in (
            (-5, 3, 0xFFFF0000),
            (0, 4, 0xFF00AA00),
            (5, 3, 0xFFFF0000),
        ):
            dialog.setHeight(alapmagassag + elteres)
            qt_app.processEvents()
            _szovegszin_kivalasztasa(
                panel, dialog, szinvalaszto, szinindex, vart_szin
            )

        _click(_child(panel, "printOptionBorderCheckBox"))
        _click(_child(panel, "printOptionEvenBorderCheckBox"))
        _click(_child(panel, "printOptionBottomOnlyCheckBox"))
        _click(_child(panel, "printOptionBorderColor5"))
        csuszka = _child(panel, "printOptionBorderSlider")
        _click(csuszka, x_fraction=0.65)

        options = _variant(panel.property("options"))
        assert options["textSource"] == 2
        assert options["textPlacement"] == 0
        assert options["wrap"] is True
        assert options["textColor"] == 0xFFFF0000
        assert options["border"] is True
        assert options["evenBorder"] is False
        assert options["borderEdge"] is True
        assert options["borderColor"] == 0xFF0000FF
        assert options["borderSize"] > 0

        verzio = int(dialog.property("elonezetValtozat"))
        _click(_child(panel, "printOptionsApplyButton"))
        qt_app.processEvents()
        assert int(dialog.property("elonezetValtozat")) > verzio
        elo_nezet = _elo_nezeti_kep(dialog)

        # A képfájl piros tesztkép; a kék képpontokat ezért a szegély adja.
        # Feliratképpontot és betűméretet nem mérünk.
        szinpixelek = [
            elo_nezet.pixel(x, y) & 0x00FFFFFF
            for y in range(elo_nezet.height())
            for x in range(elo_nezet.width())
        ]
        kek_szin = szinpixelek.count(0x0000FF)
        piros_szin = szinpixelek.count(0xFF0000)
        assert kek_szin > 0, "a kattintott kék szegély nem látszik az előnézetben"
        assert piros_szin > 0, "a kattintott piros feliratszín nem látszik az előnézetben"
