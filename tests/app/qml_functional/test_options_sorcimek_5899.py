"""Az Opciók E-mail és Web Albums fülének eredeti sorcímei (#5899)."""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QPointF, QTranslator
from PySide6.QtGui import QImage, QPainter
from PySide6.QtQuick import QQuickItem
from PySide6.QtQml import QQmlExpression, qmlContext

import picasapy.app
from support.jpeg_factory import make_minta_jpeg
from support.varakozas import var_feltetelre
from tests.app.qml_functional.conftest import _build_qml_app
from tests.app.qml_functional.test_menu_talca_egyeb_valodi_5135_b import (
    _elokeszit,
)
from tests.app.qml_functional.test_parbeszedek_valodi_5150_b import (
    _beallitasok_megnyit,
    _fulre_kattint,
    _zar,
)

_I18N_DIR = Path(picasapy.app.__file__).parent / "i18n"
_ELVART_WEB = {
    "JPEG Quality:",
    "Syncing:",
    "Watermarks:",
    "Stamp photos with your name, a web domain, or a copyright notice.",
}


@pytest.fixture
def qml_app(qt_app, tmp_path):
    """Valódi JPEG-ek és a termék bélyegkép-szolgáltatója a kiadásképhez."""

    def kepeket(lib: Path) -> None:
        cel = lib / "fotok"
        cel.mkdir()
        make_minta_jpeg(cel / "tengerpart.jpg", size=(640, 480), seed=5899)
        make_minta_jpeg(cel / "hegyek.jpg", size=(640, 480), seed=5900)

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=kepeket,
        belyegkep_meret=256,
        valodi_belyegkep=True,
    )


def _varj(qt_app, feltetel, uzenet: str, masodperc: float = 10.0) -> None:
    assert var_feltetelre(qt_app, feltetel, masodperc), uzenet


def _item(gyoker, nev: str) -> QQuickItem:
    elem = gyoker.findChild(QQuickItem, nev)
    assert elem is not None, f"hiányzó QML-elem: {nev}"
    return elem


def _kozeppont(item: QQuickItem) -> QPointF:
    return item.mapToScene(QPointF(item.width() / 2, item.height() / 2))


def _valodi_belyegkep_kesz(window) -> bool:
    def bejar(item):
        for gyerek in item.childItems():
            yield gyerek
            yield from bejar(gyerek)

    for item in bejar(window.contentItem()):
        if item.objectName() != "thumbImage" or not item.property("source"):
            continue
        kifejezes = QQmlExpression(qmlContext(item), item, "status === Image.Ready")
        ertek, hiba = kifejezes.evaluate()
        if not hiba and ertek:
            return True
    return False


def _lathato_szovegek(gyoker) -> set[str]:
    return {
        str(elem.property("text"))
        for elem in gyoker.findChildren(QQuickItem)
        if elem.isVisible()
        and elem.property("text") is not None
        and str(elem.property("text"))
    }


def _kepernyokep(window, options) -> tuple[QImage, QImage]:
    foablak = window.grabWindow()
    parbeszed = options.grabWindow()
    assert not foablak.isNull(), "a főablak kiadásképe üres"
    assert not parbeszed.isNull(), "az Opciók ablak kiadásképe üres"
    return foablak, parbeszed


def _ket_ful_kepe(ful_kepek: list[tuple[QImage, QImage]], cel: Path) -> None:
    """Két tabképet a saját, bélyegképes főablakuk fölé helyez egymás mellé."""
    viewport_szelesseg = max(fo.width() for fo, _ in ful_kepek)
    viewport_magassag = max(fo.height() for fo, _ in ful_kepek)
    kompozit = QImage(
        viewport_szelesseg * len(ful_kepek),
        viewport_magassag,
        QImage.Format.Format_ARGB32_Premultiplied,
    )
    kompozit.fill(0xFF202020)
    festo = QPainter(kompozit)
    for index, (foablak, parbeszed) in enumerate(ful_kepek):
        x = index * viewport_szelesseg
        festo.drawImage(x, 0, foablak)
        ablak_x = x + (foablak.width() - parbeszed.width()) // 2
        ablak_y = (foablak.height() - parbeszed.height()) // 2
        festo.drawImage(ablak_x, ablak_y, parbeszed)
    festo.end()
    cel.parent.mkdir(parents=True, exist_ok=True)
    assert kompozit.save(str(cel), "PNG"), f"nem menthető a kiadáskép: {cel}"


@pytest.mark.parametrize("magassageltolas", (-5, 0, 5))
def test_email_es_web_albums_sorcimei_es_sugoszovege_latszik(
    qml_app, qt_app, magassageltolas
):
    window, controller, engine = qml_app
    _elokeszit(window, qt_app, controller)
    _varj(qt_app, lambda: _valodi_belyegkep_kesz(window), "nem töltődött be valódi bélyegkép")

    translator = QTranslator(qt_app)
    assert translator.load("picasapy_en", str(_I18N_DIR)), "az angol fordítás nem tölthető be"
    qt_app.installTranslator(translator)
    engine.retranslate()

    options = _beallitasok_megnyit(window, qt_app)
    alapmagassag = options.height()
    options.setProperty("height", alapmagassag + magassageltolas)
    _varj(
        qt_app,
        lambda: options.height() == alapmagassag + magassageltolas,
        f"az Opciók ablak magassága nem vette fel a {magassageltolas:+d} px eltérést",
    )

    _fulre_kattint(qt_app, options, "optionsTabEmail", 1)
    email = _lathato_szovegek(options)
    assert "Output format:" in email, (
        "az E-mail fülön hiányzik az Output format: sorcím; "
        f"látható szövegek: {sorted(email)}"
    )
    kimenet = _item(options, "optionsMailOutputFormatLabel")
    levelezo = _item(options, "optionsMailProgramLabel")
    film = _item(options, "optionsMailMovieModeLabel")
    for masik in (levelezo, film):
        assert abs(kimenet.mapToScene(QPointF(0, 0)).x() - masik.mapToScene(QPointF(0, 0)).x()) <= 3, (
            "az Output format: sorcím bal széle eltér a többi E-mail sorcímétől"
        )
    html = _item(options, "optionsMailUseHtmlCheck")
    assert abs(_kozeppont(kimenet).y() - _kozeppont(html).y()) <= 3, (
        "az Output format: nincs az Outlook jelölő sorában"
    )

    ful_kepek = []
    if magassageltolas == 0 and os.environ.get("PICASAPY_5899_SCREENSHOT"):
        ful_kepek.append(_kepernyokep(window, options))

    _fulre_kattint(qt_app, options, "optionsTabWebAlbums", 6)
    web = _lathato_szovegek(options)
    assert _ELVART_WEB <= web, (
        "a Web Albums fülről hiányoznak az eredeti csoportcímek vagy a vízjel-"
        f"súgó; hiányzik: {sorted(_ELVART_WEB - web)}"
    )

    jpeg_label = _item(options, "optionsWebJpegQualityLabel")
    jpeg_check = _item(options, "optionsWebKeepJpegQualityCheck")
    sync_label = _item(options, "optionsWebSyncingLabel")
    sync_check = _item(options, "optionsWebStarredOnlyCheck")
    watermark_label = _item(options, "optionsWebWatermarksLabel")
    watermark_check = _item(options, "optionsWebWatermarkCheck")
    for label, control in (
        (jpeg_label, jpeg_check),
        (sync_label, sync_check),
        (watermark_label, watermark_check),
    ):
        if label is jpeg_label:
            kulonbseg = abs(_kozeppont(label).y() - _kozeppont(control).y())
        else:
            label_teteje = label.mapToScene(QPointF(0, 0)).y()
            vezerlo_teteje = control.mapToScene(QPointF(0, 0)).y()
            kulonbseg = abs(label_teteje - vezerlo_teteje)
        assert kulonbseg <= 3, f"a {label.property('text')} sorcím nincs a vezérlő sorában"

    web_tab = _item(options, "optionsWebAlbumsTab")
    watermark_field = _item(options, "optionsWebWatermarkTextField")
    watermark_help = _item(options, "optionsWebWatermarkHelp")
    assert web_tab.property("enabled") is False, "a Web Albums fül letiltott állapota megváltozott"
    assert watermark_field.property("enabled") is False, "a vízjelmező letiltott állapota megváltozott"
    mezovege = watermark_field.mapToScene(QPointF(0, watermark_field.height())).y()
    sugo_teteje = watermark_help.mapToScene(QPointF(0, 0)).y()
    assert sugo_teteje >= mezovege - 1, "a vízjel-súgó nem a mező alatt jelenik meg"

    if magassageltolas == 0 and os.environ.get("PICASAPY_5899_SCREENSHOT"):
        ful_kepek.append(_kepernyokep(window, options))
        _ket_ful_kepe(ful_kepek, Path(os.environ["PICASAPY_5899_SCREENSHOT"]))

    _zar(qt_app, options)
    qt_app.removeTranslator(translator)
