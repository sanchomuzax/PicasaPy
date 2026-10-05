"""#4212 — a két Emberek-fejléc-filmgomb valódi főablakos útja."""

from __future__ import annotations

import time

from PySide6.QtCore import (
    QEventLoop,
    QObject,
    QPoint,
    QPointF,
    QTimer,
    QTranslator,
    Qt,
    QUrl,
)
from PySide6.QtQml import QQmlComponent
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest

import picasapy.app.application as app_module
from picasapy.lazy_cv2 import cv2
from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg


_SZEMELY_AZONOSITO = "1111111111111111"
_KEEP_ALIVE: list[QObject] = []


_FILM_VARAKOZAS_MP = 90


def _anna_kepei(lib) -> None:
    for nev in ("anna-a.jpg", "anna-b.jpg"):
        make_jpeg(lib / nev, size=(640, 400))
    ini = (
        "[Contacts2]\n"
        f"{_SZEMELY_AZONOSITO}=Anna;;\n"
        "[anna-a.jpg]\n"
        f"faces=rect64(1e00280045006e00),{_SZEMELY_AZONOSITO}\n"
        "[anna-b.jpg]\n"
        f"faces=rect64(22002a0048007000),{_SZEMELY_AZONOSITO}\n"
    )
    update_document(
        lib / ".picasa.ini",
        lambda _regi: parse_document(ini),
        backup=False,
    )


def _keres(elem: QQuickItem, object_name: str):
    if elem.objectName() == object_name:
        return elem
    for child in elem.childItems():
        found = _keres(child, object_name)
        if found is not None:
            return found
    return None


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.01)
    qt_app.processEvents()
    return bool(feltetel())


def _nyugalomba_jut(qt_app, elem: QQuickItem, masodperc: float = 5.0) -> bool:
    """Megvárja, hogy az elem helye a képernyőn ne változzon (a felugró
    párbeszéd belépő átmenete és elrendezése lezáruljon). Az `opened` jelző
    az átmenet elején már igaz lehet, ezért a valódi hely a mérce: egy
    még mozgó gombra adott kattintás mellé megy."""
    hatarido = time.monotonic() + masodperc
    elozo = None
    stabil_mintak = 0
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        hely = elem.mapToScene(QPointF(0, 0))
        mostani = (round(hely.x(), 2), round(hely.y(), 2))
        stabil_mintak = stabil_mintak + 1 if mostani == elozo else 0
        elozo = mostani
        if stabil_mintak >= 15:
            return True
        time.sleep(0.02)
    return False


def _sugo_probe(engine, cel: QObject) -> QObject:
    komponens = QQmlComponent(engine)
    komponens.setData(
        b"""import QtQuick
import QtQuick.Controls
Item {
    property var targetItem
    readonly property bool tooltipVisible:
        targetItem && targetItem.ToolTip.toolTip
            ? targetItem.ToolTip.toolTip.visible : false
    readonly property string tooltipText:
        targetItem && targetItem.ToolTip.toolTip
            ? String(targetItem.ToolTip.toolTip.text) : ""
}""",
        QUrl(),
    )
    assert komponens.isReady(), [hiba.toString() for hiba in komponens.errors()]
    proba = komponens.createWithInitialProperties({"targetItem": cel})
    assert proba is not None, [hiba.toString() for hiba in komponens.errors()]
    _KEEP_ALIVE.extend((komponens, proba))
    return proba


def _kattints(ablak, qt_app, elem: QQuickItem) -> None:
    kozep = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseMove(ablak, kozep, 10)
    qt_app.processEvents()
    QTest.mouseClick(
        ablak,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(kozep.x(), kozep.y()),
    )
    qt_app.processEvents()


def test_a_ket_arcfilm_gomb_minden_szemelykepet_a_meglevo_filmkeszitobe_adja(
    qt_app, tmp_path
):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_anna_kepei)
    ablak, vezerlo, motor = next(gen)
    try:
        vezerlo.showPerson("Anna")
        assert _varj(
            qt_app,
            lambda: vezerlo.currentPersonName == "Anna"
            and vezerlo.photos.rowCount() == 2,
        ), "Anna két fényképes albuma nem nyílt meg"
        assert len(vezerlo.movieSourceUrls([0, 1])) == 2, (
            f"a két személy-sor nem ad filmforrást: "
            f"{vezerlo.movieSourceUrls([0, 1])!r}"
        )
        ablak.setProperty("selectedIndexes", [0])
        ablak.setProperty("selectedIndex", 0)

        fordito = QTranslator(qt_app)
        assert fordito.load("picasapy_hu", str(app_module._APP_DIR / "i18n")), (
            "a hivatalos magyar fordítás nem tölthető be"
        )
        qt_app.installTranslator(fordito)
        motor.retranslate()
        ablak.requestActivate()
        assert _varj(qt_app, lambda: ablak.isActive()), (
            "a főablak nem vált aktívvá az egérpróbához"
        )

        eredeti_magassag = ablak.height()
        film = None
        try:
            for eltolás in (-5, 0, 5):
                ablak.setHeight(eredeti_magassag + eltolás)
                assert _varj(
                    qt_app,
                    lambda eltolás=eltolás: ablak.height()
                    == eredeti_magassag + eltolás,
                ), f"a főablak magassága nem állt be ({eltolás:+} px)"

                for nev, eredeti_sugo, magyar_sugo in (
                    (
                        "faceHeaderMovieButton",
                        "Create Movie Presentation",
                        "Mozgófilmes prezentáció létrehozása",
                    ),
                    (
                        "faceHeaderFaceMovieButton",
                        "Create Face Movie",
                        "Mozgófilm létrehozása arcokból",
                    ),
                ):
                    gomb = _keres(ablak.contentItem(), nev)
                    assert gomb is not None, f"{nev} hiányzik a személy-fejlécből"
                    assert isinstance(gomb, QQuickItem) and gomb.isVisible(), (
                        f"{nev} nem látható Anna albumában"
                    )
                    proba = _sugo_probe(motor, gomb)
                    kozep = gomb.mapToScene(
                        QPointF(gomb.width() / 2, gomb.height() / 2)
                    ).toPoint()
                    QTest.mouseMove(ablak, QPoint(1, 1), 10)
                    QTest.mouseMove(ablak, kozep, 10)
                    assert _varj(
                        qt_app,
                        lambda proba=proba: proba.property("tooltipVisible"),
                    ), (
                        f"{nev} buboréksúgója nem jelent meg; "
                        f"hovered={gomb.property('hovered')!r}, "
                        f"size=({gomb.width()}, {gomb.height()}), "
                        f"point={kozep}, windowActive={ablak.isActive()}, "
                        f"attached={proba.property('tooltipText')!r}"
                    )
                    assert proba.property("tooltipText") == magyar_sugo, (
                        f"{nev}: {eredeti_sugo!r} hivatalos magyar alakja eltér"
                    )
                    QTest.mouseMove(ablak, QPoint(1, 1), 10)
                    assert _varj(
                        qt_app,
                        lambda proba=proba: not proba.property("tooltipVisible"),
                    ), f"{nev} buboréksúgója nem tűnt el az egér elmozdítása után"
                    kattintasok = []
                    gomb.clicked.connect(
                        lambda kattintasok=kattintasok: kattintasok.append(True)
                    )
                    _kattints(ablak, qt_app, gomb)
                    assert kattintasok, (
                        f"{nev} valódi egérkattintása nem jutott el a gombig; "
                        f"enabled={gomb.isEnabled()}, hovered={gomb.property('hovered')}, "
                        f"down={gomb.property('down')}, point={kozep}, "
                        f"geometry=({gomb.x()}, {gomb.y()}, {gomb.width()}, {gomb.height()})"
                    )
                    if film is None:
                        assert _varj(
                            qt_app,
                            lambda: ablak.findChild(QObject, "movieDialog")
                            is not None,
                        ), (
                            "a gomb kattintása után nem jött létre a Filmkészítő; "
                            f"createDialogs={ablak.findChild(QObject, 'createDialogs')!r}, "
                            f"gombpont={kozep}, ablakméret="
                            f"{ablak.width()}x{ablak.height()}"
                        )
                        film = ablak.findChild(QObject, "movieDialog")
                    assert film is not None
                    assert _varj(
                        qt_app, lambda film=film: film.property("visible")
                    ), (
                        f"{nev} kattintása nem nyitotta meg a Filmkészítőt"
                    )
                    indexes = film.property("movieClipIndexes")
                    if hasattr(indexes, "toVariant"):
                        indexes = indexes.toVariant()
                    assert indexes == [0, 1], (
                        f"{nev} nem az album összes képét adta át"
                    )
                    forrasok = film.property("movieClipSources")
                    if hasattr(forrasok, "toVariant"):
                        forrasok = forrasok.toVariant()
                    utak = [
                        QUrl(str(url)).toLocalFile()
                        for url in forrasok
                    ]
                    assert len(utak) == 2, (
                        f"a Filmkészítő nem kapott két forrásképet: "
                        f"indexes={indexes!r}, sources={forrasok!r}, utak={utak!r}"
                    )
                    assert {utak[0].split("/")[-1], utak[1].split("/")[-1]} == {
                        "anna-a.jpg", "anna-b.jpg",
                    }, f"a Filmkészítő forrásai nem Anna albumának képei: {utak!r}"
                    meret = ablak.findChild(QObject, "movieHeightBox")
                    assert meret is not None
                    assert meret.property("currentIndex") == vezerlo.movieResolutionIndex, (
                        "a személy-album gomb nem a normál filmfelbontást használja"
                    )
                    film.close()
                    assert _varj(
                        qt_app, lambda film=film: not film.property("visible")
                    )

            ablak.setHeight(eredeti_magassag)
            gomb = _keres(ablak.contentItem(), "faceHeaderMovieButton")
            assert gomb is not None
            _kattints(ablak, qt_app, gomb)
            film = ablak.findChild(QObject, "movieDialog")
            assert film is not None and _varj(
                qt_app, lambda: film.property("visible")
            )
            film.setProperty("targetFile", QUrl.fromLocalFile(
                str(tmp_path / "anna-film.mp4")
            ).toString())
            ablak.findChild(QObject, "movieHeightBox").setProperty("currentIndex", 0)
            ablak.findChild(QObject, "movieSeconds").setProperty("value", 10)
            ablak.findChild(QObject, "lengthslider/scaleslider").setProperty(
                "value", 1.0
            )
            atmenet = ablak.findChild(QObject, "movieTransitionBox")
            atfedes = ablak.findChild(QObject, "movieOverlapSlider")
            atmenet.setProperty("currentIndex", 0)
            atfedes.setProperty("value", 0.0)
            assert atmenet.property("currentIndex") == 0, (
                "a rövid próbafilmhez a leggyorsabb, vágásos átmenet kell"
            )
            assert atfedes.property("value") == 0.0, (
                "a rövid próbafilmhez minimális átfedés kell"
            )
            assert film.property("movieUsedPhotoCount") == 2
            letrehozas = ablak.findChild(QObject, "movieCreateButton")
            assert _varj(qt_app, lambda: film.property("opened")), (
                "a Filmkészítő nem fejezte be a megnyílását"
            )
            assert _nyugalomba_jut(qt_app, letrehozas), (
                "a Filmkészítő Létrehozás gombja nem állt meg a helyén"
            )

            kesz = []
            hibak = []
            hurok = QEventLoop()
            idozito = QTimer(hurok)
            idozito.setSingleShot(True)
            idozito.timeout.connect(hurok.quit)
            vezerlo.movieFinished.connect(
                lambda *args: (kesz.append(args), hurok.quit())
            )
            vezerlo.movieFailed.connect(
                lambda message: (hibak.append(message), hurok.quit())
            )
            idozito.start(_FILM_VARAKOZAS_MP * 1000)
            _kattints(ablak, qt_app, letrehozas)
            hurok.exec()
            idozito.stop()
            assert not hibak, f"a személyalbum filmkimenete hibát jelzett: {hibak}"
            assert kesz, (
                f"a Filmkészítő nem jelzett kész kimenetet {_FILM_VARAKOZAS_MP} s alatt"
            )

            videofajl = tmp_path / "anna-film.mp4"
            assert videofajl.is_file() and videofajl.stat().st_size > 0
            olvaso = cv2.VideoCapture(str(videofajl))
            olvashato, kep = olvaso.read()
            olvaso.release()
            assert olvashato and kep.shape[:2] == (240, 320), (
                "a Filmkészítő kimenete nem olvasható 320 × 240-es filmként"
            )
        finally:
            if film is not None:
                film.close()
                qt_app.processEvents()
            for nev in ("movieProgressDialog", "createResultDialog"):
                parbeszed = ablak.findChild(QObject, nev)
                if parbeszed is not None:
                    parbeszed.close()
            qt_app.removeTranslator(fordito)
            motor.retranslate()
            ablak.setHeight(eredeti_magassag)
    finally:
        try:
            gen.close()
        except RuntimeError:
            pass


def test_a_szovegek_eredeti_angol_qstr_forrasai_megmaradnak():
    qml = (
        app_module._APP_DIR / "qml" / "PicasaPy" / "LightboxHeader.qml"
    ).read_text(encoding="utf-8")
    assert 'ToolTip.text: qsTr("Create Movie Presentation")' in qml
    assert 'ToolTip.text: qsTr("Create Face Movie")' in qml
