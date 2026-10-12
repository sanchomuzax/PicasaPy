"""#4318 — a Nyomtatás beállítás valódi kattintással a nyomatba jut."""

from __future__ import annotations

import re
import time

import pytest
import numpy as np
from PySide6.QtCore import QLocale, QMetaObject, QObject, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest
from PIL import Image

from picasapy.app.language_controller import LANGUAGE_KEY


def _gyerek(gyoker, nev):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


#: A Repeater-delegáltak Python-burkolóit a teszt végéig életben tartjuk: a
#: burkoló átmeneti megszűnése a windowsos CI-n „Internal C++ object
#: (QQuickItem) already deleted" hibát adott a már lekért elemen
#: (hipotézis: PySide-tulajdonjog / GC-időzítés, a QML-fa maga statikus).
_ELO_DELEGALTAK: list = []


def _ismetlo_elem(gyoker, qt_app, ismetlo_nev, index, gyerek_nev):
    ismetlo = _gyerek(gyoker, ismetlo_nev)
    kifejezes = QQmlExpression(
        qmlContext(ismetlo), ismetlo, f"itemAt({index})"
    )

    def _delegalt_elkeszult():
        ertek, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        _delegalt_elkeszult.delegalt = ertek
        return ertek is not None

    _delegalt_elkeszult.delegalt = None
    assert _varj(qt_app, _delegalt_elkeszult), (
        f"a(z) {ismetlo_nev} {index}. delegáltja nem épült fel"
    )
    delegalt = _delegalt_elkeszult.delegalt
    _ELO_DELEGALTAK.append(delegalt)
    elem = (
        delegalt
        if delegalt.objectName() == gyerek_nev
        else delegalt.findChild(QObject, gyerek_nev)
    )
    assert elem is not None, f"{gyerek_nev} nem található a delegáltban"
    return elem


def _varj(qt_app, feltetel, masodperc=3.0):
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


def _kattints(ablak, qt_app, elem):
    assert _varj(qt_app, lambda: elem.width() > 0 and elem.height() > 0), (
        f"{elem.objectName()}: nincs kattintható mérete"
    )
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(ablak, Qt.MouseButton.LeftButton, Qt.KeyboardModifier.NoModifier, pont)
    qt_app.processEvents()


def _lista(ertek):
    return ertek.toVariant() if hasattr(ertek, "toVariant") else ertek


def _pixelek(kep):
    bits = memoryview(kep.constBits())[: kep.sizeInBytes()]
    return bytes(bits)


def _valassz_combo(ablak, qt_app, combo, index):
    _kattints(ablak, qt_app, combo)
    popup = combo.findChild(QObject, "picasaComboPopup")
    assert popup is not None, "a nyomtatásiméret-felugró nem épült fel"
    assert _varj(qt_app, lambda: popup.property("visible")), (
        "a nyomtatásiméret-lista nem nyílt le"
    )
    lista = combo.findChild(QObject, "picasaComboList")
    assert lista is not None
    assert _varj(
        qt_app,
        lambda: lista.property("count") > index
        and lista.property("contentHeight") > 0
        and lista.property("height") > 0,
    ), "a nyomtatásiméret-lista tartalma nem épült fel"
    sor_magassag = lista.property("contentHeight") / lista.property("count")
    cel_scroll = (index + 0.5) * sor_magassag - lista.property("height") / 2
    cel_scroll = max(
        0,
        min(cel_scroll, lista.property("contentHeight") - lista.property("height")),
    )
    lista.setProperty("contentY", cel_scroll)
    qt_app.processEvents()
    sor_y = (index + 0.5) * sor_magassag - lista.property("contentY")
    assert 0 <= sor_y < lista.property("height"), (
        f"a(z) {index}. méret nem látható a legördülő nézetben"
    )
    pont = lista.mapToScene(QPointF(lista.width() / 2, sor_y)).toPoint()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        pont,
    )
    assert _varj(qt_app, lambda: combo.property("currentIndex") == index), (
        f"a(z) {index}. méretet nem választotta ki a kattintás"
    )


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_metrikus_terulet_ot_alapmerete_a_nyomtatas_fulon_latszik(
    qml_app, qt_app, monkeypatch, magassag_elteres
):
    import picasapy.printing.dpi as dpi

    class MetrikusQLocale:
        MeasurementSystem = QLocale.MeasurementSystem

        def measurementSystem(self):
            return QLocale.MeasurementSystem.MetricSystem

    monkeypatch.setattr(dpi, "QLocale", MetrikusQLocale, raising=False)
    window, _controller, engine = qml_app
    menu = _gyerek(window, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: window.findChild(QObject, "optionsDialog") is not None
        and window.findChild(QObject, "optionsDialog").property("visible"),
    ), "a Beállítások ablaka nem nyílt meg"
    options = _gyerek(window, "optionsDialog")
    options.setProperty("height", options.height() + magassag_elteres)
    qt_app.processEvents()

    _kattints(options, qt_app, _gyerek(options, "optionsTabPrinting"))
    assert _varj(
        qt_app,
        lambda: _gyerek(options, "optionsTabStack").property("currentIndex") == 4,
    ), "a Nyomtatás fül nem nyílt meg"

    print_ctl = engine.rootContext().contextProperty("printController")
    print_ctl._settings.setValue(LANGUAGE_KEY, "en")
    vart = [
        ("M5X8CM", "5 x 8 cm"),
        ("M9X13CM", "9 x 13 cm"),
        ("M10X15CM", "10 x 15 cm"),
        ("M13X18CM", "13 x 18 cm"),
        ("M20X25CM", "20 x 25 cm"),
    ]
    meret_azonositok = _lista(print_ctl.printOptionSizes())
    for index, (nev, felirat) in enumerate(vart):
        combo = _ismetlo_elem(
            options,
            qt_app,
            "optionsPrintSizeRepeater",
            index,
            f"optionsPrintSizeCombo{index}",
        )
        assert _varj(
            qt_app,
            lambda combo=combo, nev=nev: combo.property("currentIndex")
            == meret_azonositok.index(nev),
        ), f"a(z) {index + 1}. gyorsválasztó nem a {nev} méretet jelzi"
        assert combo.property("currentText") == felirat, (
            f"a(z) {index + 1}. gyorsválasztó felirata nem a méretet mutatja"
        )


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_a_beallitott_meret_kattintassal_elmentodik_es_a_nyomatot_megvaltoztatja(
    qml_app, qt_app, magassag_elteres, tmp_path
):
    window, _controller, engine = qml_app
    from support.jpeg_factory import make_jpeg

    # A fixture képei szándékosan kicsik; ehhez az előnézeti minőség
    # különbségének kimutatásához egy nagyobb, kizárólag a BT-ben élő képet
    # írunk a saját tesztkönyvtárába.
    probe = tmp_path / "kepek" / "a.jpg"
    make_jpeg(probe, size=(1600, 1200))
    y, x = np.indices((1200, 1600))
    checker = ((x // 5 + y // 5) % 2 * 255).astype(np.uint8)
    pixels = np.stack((checker, x % 256, y % 256), axis=-1).astype(np.uint8)
    Image.fromarray(pixels, "RGB").save(probe, quality=100, subsampling=0)
    menu = _gyerek(window, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: window.findChild(QObject, "optionsDialog") is not None,
    ), "a Beállítások ablaka nem épült fel"
    options = _gyerek(window, "optionsDialog")
    assert _varj(qt_app, lambda: options.property("visible")), (
        "a Beállítások ablaka nem nyílt meg"
    )
    options.setProperty("height", options.property("height") + magassag_elteres)
    qt_app.processEvents()

    tab = _gyerek(options, "optionsTabPrinting")
    _kattints(options, qt_app, tab)
    assert _varj(
        qt_app,
        lambda: options.findChild(QObject, "optionsTabStack") is not None
        and options.findChild(QObject, "optionsTabStack").property("currentIndex") == 4,
    )
    combo = _ismetlo_elem(
        options,
        qt_app,
        "optionsPrintSizeRepeater",
        0,
        "optionsPrintSizeCombo0",
    )
    assert combo.property("enabled") is True, "a méretválasztó le van tiltva"
    print_ctl = engine.rootContext().contextProperty("printController")
    meretek = _lista(print_ctl.printOptionSizes())
    assert len(meretek) == 17, "a beállítási lista nem a 17 eredeti nyomatméret"
    elvart_meretek = ["M3_5X5", "M4X6", "M5X7", "M8X10", "M4X5"]
    for index, nev in enumerate(elvart_meretek):
        combo = _ismetlo_elem(
            options,
            qt_app,
            "optionsPrintSizeRepeater",
            index,
            f"optionsPrintSizeCombo{index}",
        )
        _valassz_combo(options, qt_app, combo, meretek.index(nev))
        assert print_ctl._settings.value(
            f"printing/sizePreset{index + 1}"
        ) == nev, (
            f"a(z) {index + 1}. kattintott méret nem mentődött el "
            f"(currentIndex={combo.property('currentIndex')}, "
            f"presets={print_ctl.printSizePresets()}, "
            f"keys={print_ctl._settings.allKeys()})"
        )

    proxy_png = tmp_path / "proxy-elonezet.png"
    high_quality_png = tmp_path / "jo-minosegu-elonezet.png"
    assert print_ctl.renderPreviewPage(
        [0, 1], "fit", "auto", 1, 0, str(proxy_png), ""
    ), "a proxy-előnézet nem készült el"

    preview_check = _gyerek(options, "optionsPrintHiResPreviewCheck")
    _kattints(options, qt_app, preview_check)
    assert print_ctl._settings.value("printing/proxyPreview") is False, (
        "a nagy felbontású előnézet kapcsolója nem kapcsolta ki a proxy-előnézetet"
    )

    sharp = _gyerek(options, "optionsPrintResizeSharpRadio")
    _kattints(options, qt_app, sharp)
    assert print_ctl._settings.value("printing/resamplerQuality") == 8, (
        "a Lanczos-8 választás nem jutott el a tárolt nyomtatási beállításhoz"
    )
    assert print_ctl.printResamplerQuality() == 8
    assert print_ctl.printOptions()["textSource"] == 0, (
        "a képpont-összehasonlítás próbalapján nem lehet felirat"
    )
    assert print_ctl.renderPreviewPage(
        [0, 1], "fit", "auto", 1, 0, str(high_quality_png), ""
    ), "a nagy minőségű előnézet nem készült el"
    proxy_image = QImage(str(proxy_png)).convertToFormat(
        QImage.Format.Format_RGBA8888
    )
    high_quality_image = QImage(str(high_quality_png)).convertToFormat(
        QImage.Format.Format_RGBA8888
    )
    assert proxy_image.size() == high_quality_image.size()
    assert _pixelek(proxy_image) != _pixelek(high_quality_image), (
        "a minőségi beállítás mentődött, de az előnézeti kép nem változott"
    )
    general = _gyerek(options, "optionsPrintResizeGeneralRadio")
    _kattints(options, qt_app, general)
    assert print_ctl._settings.value("printing/resamplerQuality") == 3
    lanczos3_png = tmp_path / "lanczos3-elonezet.png"
    assert print_ctl.renderPreviewPage(
        [0, 1], "fit", "auto", 1, 0, str(lanczos3_png), ""
    ), "a Lanczos-3 előnézet nem készült el"
    lanczos3_image = QImage(str(lanczos3_png)).convertToFormat(
        QImage.Format.Format_RGBA8888
    )
    assert _pixelek(lanczos3_image) != _pixelek(high_quality_image), (
        "a Lanczos-3 és Lanczos-8 beállítás azonos előnézeti képet adott"
    )

    quality_compatible = _gyerek(options, "optionsPrintQualityCompatibleRadio")
    quality_high = _gyerek(options, "optionsPrintQualityHighQualityRadio")
    if quality_compatible.isVisible():
        _kattints(options, qt_app, quality_high)
        _kattints(options, qt_app, quality_compatible)
    else:
        assert quality_compatible.property("visible") is False, (
            "a nyomtatóminőség csoport csak Windowson látható a FEN szerint"
        )
        print_ctl.setPrinterQuality("compatible")
    assert print_ctl._settings.value("printing/printerQuality") == "compatible"
    assert print_ctl._printer_output_scale() == 0.5
    compatible_pdf = tmp_path / "kompatibilis-fel-felbontasu-nyomat.pdf"
    assert print_ctl.renderPrintPreviewPdf(
        [0, 1], "fit", "auto", str(compatible_pdf)
    )
    if quality_high.isVisible():
        _kattints(options, qt_app, quality_high)
    else:
        print_ctl.setPrinterQuality("highQuality")
    assert print_ctl._settings.value("printing/printerQuality") == "highQuality"
    assert print_ctl._printer_output_scale() == 1.0
    high_pdf = tmp_path / "teljes-felbontasu-nyomat.pdf"
    assert print_ctl.renderPrintPreviewPdf(
        [0, 1], "fit", "auto", str(high_pdf)
    )
    print_ctl.setPrinterQuality("compatible")
    assert print_ctl._printer_output_scale() == 0.5
    assert compatible_pdf.read_bytes() != high_pdf.read_bytes(), (
        "a fél- és teljes felbontású nyomtatás azonos PDF-et adott"
    )

    options.setProperty("visible", False)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    menu_print = _gyerek(window, "menuFilePrint")
    QMetaObject.invokeMethod(
        menu_print, "triggered", Qt.ConnectionType.DirectConnection
    )
    assert _varj(
        qt_app,
        lambda: window.findChild(QObject, "printDialog") is not None
        and window.findChild(QObject, "printDialog").property("visible"),
    ), "a Nyomtatás ablaka nem nyílt meg"
    dialog = _gyerek(window, "printDialog")
    preset = _ismetlo_elem(
        dialog,
        qt_app,
        "printSizePresetRepeater",
        0,
        "printPresetSize0",
    )
    alap_lapok = print_ctl.printPageCount([0, 1], 1, "auto", "")
    _kattints(dialog, qt_app, preset)
    assert dialog.property("printSize") == "M3_5X5", (
        "a nyomtatási gyorsgomb nem az elmentett méretet választotta"
    )
    uj_lapok = print_ctl.printPageCount([0, 1], 1, "auto", "")
    assert uj_lapok < alap_lapok, (
        f"a gyorsgomb után a tényleges lapkiosztás nem változott: "
        f"{alap_lapok} → {uj_lapok}"
    )

    pdf = tmp_path / "beallitott-meret.pdf"
    assert print_ctl.renderPrintPreviewPdf([0, 1], "fit", "auto", str(pdf))
    assert pdf.is_file() and pdf.stat().st_size > 0
    lapok = len(re.findall(rb"/Type\s*/Page[^s]", pdf.read_bytes()))
    assert lapok == uj_lapok, (
        f"a PDF {lapok} lapot tartalmaz, a nyomtató elrendező {uj_lapok}-et jelzett"
    )


def _meret_combo_geometriak(options, tab, qt_app, kiserletek=5):
    """Az öt méretválasztó geometriája a méretrácshoz képest.

    Egy kísérleten belül minden elemet ÚJRA lekérünk a fa gyökeréből; ha a
    lekért burkoló közben érvénytelenné vált (RuntimeError), az egész mérést
    megismételjük. Az utolsó hiba a diagnosztikával együtt kerül elő — a
    hiba nem nyelődik el."""
    utolso_hiba = None
    for kiserlet in range(1, kiserletek + 1):
        index = -1
        try:
            meret_racs = _gyerek(tab, "optionsPrintSizeGrid")
            geometriak = []
            for index in range(5):
                combo = _ismetlo_elem(
                    options, qt_app, "optionsPrintSizeRepeater", index,
                    f"optionsPrintSizeCombo{index}",
                )
                cimke = _ismetlo_elem(
                    options, qt_app, "optionsPrintSizeRepeater", index,
                    f"optionsPrintSizeLabel{index}",
                )
                assert cimke.property("visible") is False, (
                    "a méretválasztó fölösleges sorszámcímkéje látható maradt"
                )
                geometriak.append(
                    (
                        combo.mapToItem(meret_racs, QPointF(0, 0)),
                        float(combo.width()),
                        float(combo.height()),
                    )
                )
            return geometriak
        except RuntimeError as hiba:
            utolso_hiba = f"{kiserlet}. kísérlet, {index}. delegált: {hiba}"
            qt_app.processEvents()
            time.sleep(0.1)
    raise AssertionError(
        f"a méretválasztók burkolója {kiserletek} kísérletre sem maradt "
        f"érvényes: {utolso_hiba}"
    )


@pytest.mark.parametrize("magassag_elteres", [-5, 0, 5])
def test_nyomtatas_ful_ketoszlopos_elrendezese_a_referencia_szerint(
    qml_app, qt_app, magassag_elteres, tmp_path
):
    window, _controller, _engine = qml_app
    menu = _gyerek(window, "menuToolsOptions")
    QMetaObject.invokeMethod(menu, "triggered", Qt.ConnectionType.DirectConnection)
    assert _varj(
        qt_app,
        lambda: window.findChild(QObject, "optionsDialog") is not None
        and window.findChild(QObject, "optionsDialog").property("visible"),
    ), "a Beállítások ablaka nem nyílt meg"
    options = _gyerek(window, "optionsDialog")
    options.setProperty("width", 768)
    options.setProperty("height", 436 + magassag_elteres)
    qt_app.processEvents()

    _kattints(options, qt_app, _gyerek(options, "optionsTabPrinting"))
    assert _varj(
        qt_app,
        lambda: _gyerek(options, "optionsTabStack").property("currentIndex") == 4,
    ), "a Nyomtatás fül nem nyílt meg"
    tab = _gyerek(options, "optionsTabPrintingPanel")
    meret_racs = _gyerek(tab, "optionsPrintSizeGrid")
    beallitas_racs = _gyerek(tab, "optionsPrintSettingsGrid")
    assert _varj(
        qt_app,
        lambda: meret_racs.width() > 0 and beallitas_racs.width() > 0,
    ), "a nyomtatási beállítások rácsa nem rendeződött el"

    combo_geometriak = _meret_combo_geometriak(options, tab, qt_app)
    meret_racs = _gyerek(tab, "optionsPrintSizeGrid")

    pontok = [adat[0] for adat in combo_geometriak]
    meret_racs_kozepe = meret_racs.mapToScene(
        QPointF(meret_racs.width() / 2, 0)
    ).x()
    assert abs(meret_racs_kozepe - options.width() / 2) <= 3, (
        "a kétoszlopos méretválasztó nincs középre igazítva: "
        f"rács={meret_racs_kozepe:.1f}, ablak={options.width() / 2:.1f}"
    )
    # A referencia-képen a vezérlők 150×23 px-esek, a két oszlop és a
    # három sor kezdőpontjának távolsága 157, illetve 30 px. A ±3 px-es
    # tűrés a renderelő és az ablakméret platformkülönbségét engedi meg.
    for _pont, szelesseg, magassag in combo_geometriak:
        assert abs(szelesseg - 150) <= 3, f"eltérő méretválasztó-szélesség: {szelesseg}"
        assert abs(magassag - 23) <= 3, f"eltérő méretválasztó-magasság: {magassag}"
    # Oszlopfolytonos sorrend, ahogy a referencián: balra 5x8, 9x13,
    # 10x15 cm, jobbra 13x18 és 20x25 cm.
    assert abs((pontok[3].x() - pontok[0].x()) - 157) <= 3
    assert abs((pontok[1].y() - pontok[0].y()) - 30) <= 3
    assert abs((pontok[2].y() - pontok[1].y()) - 30) <= 3
    assert abs((pontok[4].y() - pontok[3].y()) - 30) <= 3
    assert abs(pontok[0].x() - pontok[1].x()) <= 2
    assert abs(pontok[1].x() - pontok[2].x()) <= 2
    assert abs(pontok[3].x() - pontok[4].x()) <= 2
    assert abs(pontok[0].y() - pontok[3].y()) <= 2
    assert abs(pontok[1].y() - pontok[4].y()) <= 2

    cimke_nevek = (
        "optionsPrintPreviewsLabel",
        "optionsPrintQualityLabel",
        "optionsPrintResamplerLabel",
    )
    lathato_cimkek = [
        _gyerek(tab, nev)
        for nev in cimke_nevek
        if _gyerek(tab, nev).property("visible")
    ]
    assert len(lathato_cimkek) >= 2, "a beállításcsoportok bal oldali címkéi hiányoznak"
    cimke_jobb_szelek = [
        cimke.mapToItem(
            beallitas_racs, QPointF(cimke.width(), cimke.height() / 2)
        ).x()
        for cimke in lathato_cimkek
    ]
    assert max(cimke_jobb_szelek) - min(cimke_jobb_szelek) <= 2, (
        f"a csoportcímkék nem egy vonalra zárnak: {cimke_jobb_szelek}"
    )

    qt_app.processEvents()
    kep = options.grabWindow()
    assert not kep.isNull(), "a Nyomtatás fül képe nem renderelődött"
    assert kep.save(str(tmp_path / f"nyomtatas-{magassag_elteres:+d}.png")), (
        "a renderelt Nyomtatás fül képét nem sikerült elmenteni"
    )
