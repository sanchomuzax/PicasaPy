"""A Létrehozás felületeinek bontás előtti képpontőre (#6051)."""

from __future__ import annotations

import math
import os
import time
from pathlib import Path

import numpy as np
import pytest
from PySide6.QtCore import QCoreApplication, QLocale, QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtQuick import QQuickItem, QQuickWindow
from PySide6.QtTest import QSignalSpy

from support.jpeg_factory import make_jpeg
from tests.app.qml_functional.conftest import _build_qml_app
from support.render_test_helpers import is_text_item
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
_RENDEZETT_FELVETELI_IDOK = (
    ("a.jpg", "2026-10-27T12:00:00"),
    ("b.jpg", "2026-10-27T11:00:00"),
)
_RENDEZETT_FELVETELI_IDOK_EXIF = (
    ("a.jpg", (320, 160), "2026:10:27 12:00:00"),
    ("b.jpg", (100, 100), "2026:10:27 11:00:00"),
)
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


def _letrehozza_a_proba_kepeket(konyvtar: Path) -> None:
    for nev, meret, felveteli_ido in _RENDEZETT_FELVETELI_IDOK_EXIF:
        make_jpeg(konyvtar / nev, size=meret, taken_at=felveteli_ido)


@pytest.fixture
def qml_app(rogzitett_betu, qt_app, tmp_path, request):
    """A render-fixture dátuma és sorrendje ne függjön az órától vagy mtime-tól."""
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_letrehozza_a_proba_kepeket,
        keep_modul=request.module,
    )


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
        if not is_text_item(objektum):
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


def _ablakkepek(qt_app, foor, foor_kep: QImage | None = None):
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
            kep = (
                foor_kep
                if ablak is foor and foor_kep is not None
                else ablak.grabWindow()
            )
        else:
            kep = qt_app.primaryScreen().grabWindow(int(ablak.winId())).toImage()
        assert not kep.isNull(), f"üres felvétel: {nev}"
        kepek[nev] = (ablak, kep)
    return kepek


def _exif_datum_megjelenik(vezerlo, ablak) -> bool:
    """A fejléc és az állapotsor már a próbakép EXIF-dátumát mutatja-e."""
    from picasapy.app.formatting import long_date

    rekordok = vezerlo.photos.photos
    vart_rekordok = list(_RENDEZETT_FELVETELI_IDOK)
    if [(rekord.name, rekord.taken_at) for rekord in rekordok] != vart_rekordok:
        return False

    vart_datum = long_date(vart_rekordok[1][1], QLocale())
    csoportok = vezerlo.feedGroups
    if len(csoportok) != 1 or csoportok[0].get("dateText") != vart_datum:
        return False

    feliratok = [
        elem
        for elem in _vizualis_elemek(ablak.contentItem())
        if elem.objectName() == "folderDateText" and elem.isVisible()
    ]
    return (
        any(elem.property("text") == vart_datum for elem in feliratok)
        and vart_datum in vezerlo.statusText
    )


def _varj_foablak_kepstabilizalodasara(ablak, qt_app) -> QImage:
    """Három egymás utáni, újrarajzolt képkockán várja ki a stabil kimenetet."""
    hatarido = time.monotonic() + 3.0
    elozo_pixelek = None
    azonos_kockak = 0

    while True:
        maradek = hatarido - time.monotonic()
        assert maradek > 0, "a főablak renderképe nem stabilizálódott 3 s alatt"

        kirajzolt = QSignalSpy(ablak.frameSwapped)
        ablak.requestUpdate()
        assert var_feltetelre(
            qt_app,
            hibaturo_feltetel(lambda spy=kirajzolt: spy.count() > 0),
            min(0.5, maradek),
        ), "a főablak nem rajzolt új képkockát 3 s alatt"

        kep = ablak.grabWindow()
        assert not kep.isNull(), "üres főablak-képkocka"
        pixelek = _pixelek(kep)
        if elozo_pixelek is not None and np.array_equal(elozo_pixelek, pixelek):
            azonos_kockak += 1
            if azonos_kockak >= 2:
                return kep
        else:
            azonos_kockak = 0
        elozo_pixelek = pixelek


def _foablak_kep_6140_fogantyumaszkkal(ablak, qt_app) -> QImage:
    """A #6140 árnyék-ingadozását a két érintett fogantyú geometriáján zárja ki.

    A nyers, látható fogantyús kép marad a referencia-összevetésé. A
    bájtra összehasonlított `.tmp` felvétel csak a két QML-fogantyú
    eltüntetésével készül; így a maszk pontosan az objektumok saját rajzolt
    területére korlátozódik, a párbeszéd pixeltűrése változatlan.
    """
    fogantyuk = []
    for nev in ("dateRangeFilterSlider", "traySizeSlider"):
        csuszka = ablak.findChild(QObject, nev)
        assert csuszka is not None, f"nem található a #6140-hez tartozó csúszka: {nev}"
        fogantyu = csuszka.property("handle")
        assert isinstance(fogantyu, QQuickItem), f"hiányzik a csúszka fogantyúja: {nev}"
        fogantyuk.append((fogantyu, fogantyu.isVisible()))
    try:
        for fogantyu, _lathato in fogantyuk:
            fogantyu.setVisible(False)
        return _varj_foablak_kepstabilizalodasara(ablak, qt_app)
    finally:
        for fogantyu, lathato in fogantyuk:
            fogantyu.setVisible(lathato)


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


def test_create_dialog_kepei_rendezett_felveteli_datummal_toltodnek(qml_app):
    """A renderképet az óra és a fájlrendszer létrehozási sorrendje ne változtassa."""
    _ablak, vezerlo, _engine = qml_app
    assert [(kep.name, kep.taken_at) for kep in vezerlo.photos.photos] == list(
        _RENDEZETT_FELVETELI_IDOK
    )


@pytest.mark.parametrize("ablakmagassag_delta", [-5, 0, 5])
def test_create_dialogs_render_bontas_elott_rogzitett_referenciakkal(
    ablakmagassag_delta, qml_app, qt_app
):
    """Mind a 13 megnyitható állapot kirajzolódik az eredeti kód referenciájára."""
    ablak, vezerlo, _engine = qml_app
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
    assert var_feltetelre(
        qt_app,
        hibaturo_feltetel(lambda: _exif_datum_megjelenik(vezerlo, ablak)),
        5.0,
    ), (
        "a főablak nem frissült a próbaképek EXIF-dátumára: "
        f"statusText={vezerlo.statusText!r}, feedGroups={vezerlo.feedGroups!r}"
    )

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
            hibaturo_feltetel(
                lambda: any(
                    lathato_ablak is ablak and lathato_ablak.isVisible()
                    for lathato_ablak in qt_app.allWindows()
                )
            ),
            5.0,
        ), "a főablak nem látható a párbeszéd megnyitása után"
        stabil_foablak_kep = _varj_foablak_kepstabilizalodasara(ablak, qt_app)
        aktualis_kepek = _ablakkepek(
            qt_app, ablak, foor_kep=stabil_foablak_kep
        )
        allapot_kimenet = kimenet / nev
        allapot_kimenet.mkdir(parents=True, exist_ok=True)
        for kepnev, (felvetelablak, aktualis) in aktualis_kepek.items():
            kimeneti_kep = (
                _foablak_kep_6140_fogantyumaszkkal(ablak, qt_app)
                if kepnev == "foablak"
                else aktualis
            )
            assert kimeneti_kep.save(str(allapot_kimenet / f"{kepnev}.png"))
            # #6124: a CI-n felvett (a referenciával azonos módon maszkolt) kép a
            # hibakép-artefaktumba is megy, hogy a referenciát a CI
            # környezetében lehessen rögzíteni.
            hibakep_mappa = os.environ.get("PICASAPY_RENDER_FAILURE_DIR")
            if hibakep_mappa and not kepnev.startswith("felugro-"):
                cel = (
                    Path(hibakep_mappa) / "create-dialogs-6051"
                    / f"{ablakmagassag_delta:+d}" / nev
                )
                cel.mkdir(parents=True, exist_ok=True)
                assert kimeneti_kep.save(str(cel / f"{kepnev}.png"))
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
                elt_pont = (
                    _kulon_ablak_terulete_az_ablakban(ablak, aktualis_kepek)
                    if nev in _QT_SAJAT_PARBESZEDEK
                    else _parbeszed_terulete_az_ablakban(parbeszed, ablak)
                )
                bal, felso, jobb, also = elt_pont
                bal = max(0, bal)
                felso = max(0, felso)
                jobb = min(ervenyes.shape[1], jobb)
                also = min(ervenyes.shape[0], also)
                assert bal < jobb and felso < also, f"üres párbeszéd-terület: {elt_pont}"
                aktualis_pixelek = aktualis_pixelek[felso:also, bal:jobb]
                referencia_pixelek = referencia_pixelek[felso:also, bal:jobb]
                ervenyes = ervenyes[felso:also, bal:jobb]
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
