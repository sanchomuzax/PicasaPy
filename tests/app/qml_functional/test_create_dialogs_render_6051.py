"""A Létrehozás felületeinek bontás előtti képpontőre (#6051)."""

from __future__ import annotations

import math
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem, QQuickWindow

from tests.support.qml_halasztott import epitsd_fel
from tests.support.varakozas import hibaturo_feltetel, var_feltetelre

# Keep FileDialog and ColorDialog renderable in the offscreen QML test.
QCoreApplication.setAttribute(Qt.ApplicationAttribute.AA_DontUseNativeDialogs, True)


_QML = Path(__file__).resolve().parents[3] / "src/picasapy/app/qml/PicasaPy"
_ARANY = Path(__file__).parent / "golden" / "create_dialogs_6051"
# A rendszer-fájlválasztót nyitó állapotok (a QML FileDialog magassága platformfüggő).
_FAJLVALASZTOK = frozenset({"collage-target", "movie-target", "movie-audio"})
# A Qt saját színválasztóját nyitó állapotok (a ColorDialog szélessége platformfüggő).
_SZINVALASZTOK = frozenset({"movie-text-color", "movie-background-color"})
_QT_SAJAT_PARBESZEDEK = _FAJLVALASZTOK | _SZINVALASZTOK
_ALLAPOTOK = (
    ("poster", "posterDialog", "open"),
    ("collage", "collageDialog", "open"),
    ("collage-target", "file:Picture Collage...", "open"),
    ("movie-maker", "movieDialog", "openForSelection"),
    ("movie-title", "movieTitleDialog", "open"),
    ("movie-target", "file:Movie", "open"),
    ("movie-audio", "movieAudioDialog", "open"),
    ("movie-text-color", "text_picker_panel", "open"),
    ("movie-background-color", "bkg_picker_panel", "open"),
    ("movie-replace", "movieReplaceDialog", "open"),
    ("movie-progress", "movieProgressDialog", "open"),
    ("create-result", "createResultDialog", "open"),
    ("timestamp", "adjustTimestampDialog", "open"),
)


def _pixelek(kep: QImage) -> np.ndarray:
    rgba = kep.convertToFormat(QImage.Format.Format_RGBA8888)
    adat = np.frombuffer(rgba.constBits(), dtype=np.uint8)
    return adat.reshape(rgba.height(), rgba.bytesPerLine())[:, : rgba.width() * 4].reshape(
        rgba.height(), rgba.width(), 4
    ).copy()


def _vizualis_elemek(gyoker: QQuickItem):
    """A vizuális fában beágyazott QML-elemeket is bejárja."""
    feldolgozando = [gyoker]
    while feldolgozando:
        elem = feldolgozando.pop()
        yield elem
        feldolgozando.extend(elem.childItems())


def _szovegteruletek_kimaszkolasa(ablak, ervenyes: np.ndarray) -> None:
    """A betűkörnyezetet kihagyja, a többi képpontot változatlanul méri."""
    magassag, szelesseg = ervenyes.shape
    for objektum in _vizualis_elemek(ablak.contentItem()):
        if not objektum.metaObject().className().startswith("QQuickText"):
            continue
        if not objektum.isVisible() or objektum.width() <= 0 or objektum.height() <= 0:
            continue
        try:
            pont = objektum.mapToScene(QPointF(0, 0))
        except RuntimeError:
            continue
        bal = max(0, math.floor(pont.x()) - 4)
        felso = max(0, math.floor(pont.y()) - 4)
        jobb = min(szelesseg, math.ceil(pont.x() + objektum.width()) + 4)
        also = min(magassag, math.ceil(pont.y() + objektum.height()) + 4)
        if bal < jobb and felso < also:
            ervenyes[felso:also, bal:jobb] = False


def _parbeszed_terulete_az_ablakban(parbeszed, ablak: QQuickWindow):
    """A megnyitott párbeszéd határait adja vissza a főablak képpontjaiban."""
    if isinstance(parbeszed, QQuickItem):
        bal_felso = parbeszed.mapToItem(ablak.contentItem(), QPointF(0, 0))
        szelesseg = parbeszed.width()
        magassag = parbeszed.height()
    else:
        szulo = parbeszed.property("parent")
        x = float(parbeszed.property("x") or 0)
        y = float(parbeszed.property("y") or 0)
        szelesseg = float(parbeszed.property("width") or 0)
        magassag = float(parbeszed.property("height") or 0)
        bal_felso = (
            szulo.mapToItem(ablak.contentItem(), QPointF(x, y))
            if isinstance(szulo, QQuickItem)
            else QPointF(x, y)
        )
    assert szelesseg > 0 and magassag > 0, (
        f"nincs mérhető párbeszéd-terület: {parbeszed.objectName()} "
        f"({szelesseg}×{magassag})"
    )
    dpr = ablak.devicePixelRatio()
    bal = math.floor(bal_felso.x() * dpr)
    felso = math.floor(bal_felso.y() * dpr)
    jobb = math.ceil((bal_felso.x() + szelesseg) * dpr)
    also = math.ceil((bal_felso.y() + magassag) * dpr)
    return bal, felso, jobb, also


def _kulon_ablak_terulete_az_ablakban(ablak, kepek):
    """A Qt saját popupablakának főablaki átfedését adja vissza."""
    popupok = [
        felvetelablak
        for nev, (felvetelablak, _) in kepek.items()
        if nev.startswith("felugro-")
    ]
    assert popupok, "a Qt-párbeszédablak nem nyitott külön ablakot"
    popup = popupok[-1]
    bal_felso = ablak.mapFromGlobal(popup.mapToGlobal(QPoint(0, 0)))
    dpr = ablak.devicePixelRatio()
    bal = math.floor(bal_felso.x() * dpr)
    felso = math.floor(bal_felso.y() * dpr)
    jobb = math.ceil((bal_felso.x() + popup.width()) * dpr)
    also = math.ceil((bal_felso.y() + popup.height()) * dpr)
    return bal, felso, jobb, also


def _parbeszedi_pixelelteres(aktualis, referencia, ervenyes, terulet) -> int:
    """A párbeszéd területén számol; a referenciát legfeljebb ±3 px-szel illeszti."""
    bal, felso, jobb, also = terulet
    bal = max(0, bal)
    felso = max(0, felso)
    jobb = min(ervenyes.shape[1], jobb)
    also = min(ervenyes.shape[0], also)
    assert bal < jobb and felso < also, f"üres párbeszéd-terület: {terulet}"
    aktualis_resz = aktualis[felso:also, bal:jobb]
    ervenyes_resz = ervenyes[felso:also, bal:jobb]
    legjobb = None
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            ref_bal = bal + dx
            ref_felso = felso + dy
            ref_jobb = min(ref_bal + aktualis_resz.shape[1], referencia.shape[1])
            ref_also = min(ref_felso + aktualis_resz.shape[0], referencia.shape[0])
            if ref_bal < 0 or ref_felso < 0 or ref_bal >= ref_jobb or ref_felso >= ref_also:
                continue
            szelesseg = ref_jobb - ref_bal
            magassag = ref_also - ref_felso
            eltero = np.any(
                aktualis_resz[:magassag, :szelesseg]
                != referencia[ref_felso:ref_also, ref_bal:ref_jobb],
                axis=2,
            ) & ervenyes_resz[:magassag, :szelesseg]
            darab = int(np.count_nonzero(eltero))
            if legjobb is None or darab < legjobb:
                legjobb = darab
    assert legjobb is not None, f"nincs érvényes referencia-terület: {terulet}"
    return legjobb


def _ablakkepek(qt_app, foor):
    """A fő QQuickWindow-t és az összes látható popupablakot is felveszi."""
    ablakok = [ablak for ablak in qt_app.allWindows() if ablak.isVisible()]
    ablakok.sort(key=lambda ablak: (ablak is not foor, ablak.title(), ablak.metaObject().className()))
    kepek = {}
    for index, ablak in enumerate(ablakok):
        if ablak is foor:
            nev = "foablak"
        else:
            nev = f"felugro-{index}-{ablak.title() or ablak.metaObject().className()}"
        if isinstance(ablak, QQuickWindow):
            kep = ablak.grabWindow()
        else:
            kep = qt_app.primaryScreen().grabWindow(int(ablak.winId())).toImage()
        assert not kep.isNull(), f"üres felvétel: {nev}"
        kepek[nev] = (ablak, kep)
    return kepek


def _parbeszed(gyoker, nev: str):
    if not nev.startswith("file:"):
        return gyoker.findChild(QObject, nev)
    cim = nev.removeprefix("file:")
    talalatok = [
        objektum
        for objektum in gyoker.findChildren(QObject)
        if "FileDialog" in objektum.metaObject().className()
        and objektum.property("title") == cim
    ]
    assert len(talalatok) == 1, (
        f"{cim!r} fájlválasztó: {len(talalatok)} találat; "
        f"objektumok: {[(o.objectName(), o.metaObject().className(), o.property('title')) for o in gyoker.findChildren(QObject)]}"
    )
    return talalatok[0]


def _felulet_meretek_800_sor_alatt() -> None:
    fajlok = sorted(_QML.glob("*Create*.qml")) + sorted(_QML.glob("MovieMaker*.qml"))
    hosszak = {fajl.name: len(fajl.read_text(encoding="utf-8").splitlines()) for fajl in fajlok}
    assert hosszak and all(hossz <= 800 for hossz in hosszak.values()), hosszak


@pytest.mark.parametrize("ablakmagassag_delta", [-5, 0, 5])
def test_create_dialogs_render_bontas_elott_rogzitett_referenciakkal(
    ablakmagassag_delta, qml_app, qt_app
):
    """Mind a 13 megnyitható állapot kirajzolódik az eredeti kód referenciájára."""
    ablak, _vezerlo, _engine = qml_app
    ablak.show()
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: ablak.isExposed()),
        10.0,
    )
    epitsd_fel(ablak, "createDialogs")
    create_dialogs = ablak.findChild(QObject, "createDialogs")
    assert create_dialogs is not None

    ablakmagassag = ablak.height()
    ablak.resize(ablak.width(), ablakmagassag + ablakmagassag_delta)
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(
            lambda: ablak.height() == ablakmagassag + ablakmagassag_delta
        ),
        5.0,
    )
    ablak.setProperty("selectedIndexes", [0, 1])
    ablak.setProperty("selectedIndex", 0)

    kimenet = Path.cwd() / ".tmp" / "create-dialogs-6051" / f"{ablakmagassag_delta:+d}"
    kimenet.mkdir(parents=True, exist_ok=True)
    hianyzo = []
    elteresek = []
    movie_dialog = _parbeszed(create_dialogs, "movieDialog")
    for nev, cel, muvelet in _ALLAPOTOK:
        parbeszed = _parbeszed(create_dialogs, cel)
        assert parbeszed is not None, f"nem található: {cel}"
        assert parbeszed.metaObject().invokeMethod(parbeszed, muvelet), (
            f"nem hívható: {cel}.{muvelet}()"
        )
        assert var_feltetelre(
            qt_app,
            hibaturo_feltetel(lambda p=parbeszed: bool(p.property("visible"))),
            5.0,
        ), f"nem nyílt meg: {nev}"
        if nev == "movie-maker":
            preview = create_dialogs.findChild(QObject, "moviePreviewTransitionImage")
            viewport = create_dialogs.findChild(QObject, "moviePreviewViewport")
            assert preview is not None, "nem található a film előnézeti képe"
            assert viewport is not None, "nem található a film előnézeti területe"
            assert var_feltetelre(
                qt_app,
                hibaturo_feltetel(
                    lambda v=viewport: float(v.property("width")) > 16
                    and float(v.property("height")) > 16
                ),
                5.0,
            ), "a film előnézeti területe nem épült fel"
            if bool(movie_dialog.property("previewTransitionServiceAvailable")):
                assert movie_dialog.metaObject().invokeMethod(
                    movie_dialog,
                    "requestPreviewFrame",
                ), "nem kérhető film-előnézeti képkocka"
                elonezet_kesz = var_feltetelre(
                    qt_app,
                    hibaturo_feltetel(
                        lambda p=preview: int(movie_dialog.property("previewLatestRequestGeneration")) > 0
                        and int(movie_dialog.property("previewDisplayedGeneration"))
                        >= int(movie_dialog.property("previewLatestRequestGeneration"))
                        and float(p.property("paintedWidth")) > 0
                        and bool(movie_dialog.property("previewTransitionFrameSource"))
                    ),
                    5.0,
                )
                assert elonezet_kesz, (
                    "a film előnézeti képe nem töltődött be: "
                    f"items={movie_dialog.property('previewItemCount')}, "
                    f"paintedWidth={preview.property('paintedWidth')}, "
                    f"latest={movie_dialog.property('previewLatestRequestGeneration')}, "
                    f"displayed={movie_dialog.property('previewDisplayedGeneration')}"
                )
            else:
                assert var_feltetelre(
                    qt_app,
                    hibaturo_feltetel(
                        lambda: int(movie_dialog.property("previewImageWidth")) > 0
                        and int(movie_dialog.property("previewImageHeight")) > 0
                    ),
                    5.0,
                ), "a film helyi előnézeti képe nem töltődött be"
        assert var_feltetelre(
            qt_app,
            hibaturo_feltetel(lambda: bool(_ablakkepek(qt_app, ablak))),
            5.0,
        )
        aktualis_kepek = _ablakkepek(qt_app, ablak)
        allapot_kimenet = kimenet / nev
        allapot_kimenet.mkdir(parents=True, exist_ok=True)
        for kepnev, (felvetelablak, aktualis) in aktualis_kepek.items():
            assert aktualis.save(str(allapot_kimenet / f"{kepnev}.png"))
            referencia_fajl = (
                _ARANY / f"{ablakmagassag_delta:+d}" / nev / f"{kepnev}.png"
            )
            referencia = QImage(str(referencia_fajl))
            if referencia.isNull():
                hianyzo.append(str(referencia_fajl))
                continue
            if nev in _QT_SAJAT_PARBESZEDEK and kepnev.startswith("felugro-"):
                # A Qt saját FileDialog/ColorDialog ablaka: mérete és belseje
                # platformonként más (a CI-n a fájlválasztó 600x445 és
                # ~100 000 képpontban eltér, a színválasztó 336 széles a
                # helyi 384 és a referencia 374 helyett), és nem a mi
                # kódunk. Itt csak azt mérjük, hogy megnyílt.
                assert not aktualis.isNull() and aktualis.width() > 0, (
                    f"{nev}/{kepnev}: a Qt-párbeszédablak nem nyílt meg"
                )
                continue
            szelesseg = min(aktualis.width(), referencia.width())
            magassag = min(aktualis.height(), referencia.height())
            assert abs(aktualis.width() - referencia.width()) <= 3, (
                f"{nev}/{kepnev}: eltérő szélesség, "
                f"aktuális={aktualis.width()}, referencia={referencia.width()}"
            )
            assert abs(aktualis.height() - referencia.height()) <= 3, (
                f"{nev}/{kepnev}: eltérő magasság, "
                f"aktuális={aktualis.height()}, referencia={referencia.height()}"
            )
            ervenyes = np.ones((magassag, szelesseg), dtype=bool)
            _szovegteruletek_kimaszkolasa(felvetelablak, ervenyes)
            aktualis_pixelek = _pixelek(aktualis)[:magassag, :szelesseg]
            referencia_pixelek = _pixelek(referencia)[:magassag, :szelesseg]
            if kepnev == "foablak":
                if nev in _QT_SAJAT_PARBESZEDEK:
                    elt_pont = _kulon_ablak_terulete_az_ablakban(
                        ablak,
                        aktualis_kepek,
                    )
                else:
                    elt_pont = _parbeszed_terulete_az_ablakban(parbeszed, ablak)
                    eltero_db = _parbeszedi_pixelelteres(
                    aktualis_pixelek,
                    referencia_pixelek,
                    ervenyes,
                    elt_pont,
                )
            else:
                eltero = np.any(
                    aktualis_pixelek != referencia_pixelek, axis=2
                ) & ervenyes
                eltero_db = int(np.count_nonzero(eltero))
            if eltero_db:
                elteresek.append(
                    f"{nev}/{kepnev}: {eltero_db} szövegen kívüli képpont"
                )
        parbeszed.metaObject().invokeMethod(parbeszed, "close")
        if nev == "create-result":
            movie_dialog.metaObject().invokeMethod(movie_dialog, "close")
        qt_app.processEvents()

    assert not hianyzo, (
        "A bontás előtti referencia-képek hiányoznak; a felvételek a "
        f"{kimenet} könyvtárban vannak: {hianyzo}"
    )
    assert not elteresek, "Eltérő képpontok: " + "; ".join(elteresek)


def test_create_dialogs_es_reszei_legfeljebb_800_sorosak():
    """A #5951 korlátját őrzi: minden létrehozás-komponens legfeljebb 800 sor."""
    _felulet_meretek_800_sor_alatt()
