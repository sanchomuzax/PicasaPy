"""#4036 — a Kiegyenesítés sávja áttetsző a valódi főablak képén.

A mérce a `picasa-colab-jobs job-69, 4. kép` felvételén, a 800×800-as
`color_patches.jpg` alsó lila mezőjén mért RGB. A referencia PNG-t nem
tároljuk: a teszt ugyanazt a 800×800-as tesztábrát állítja elő ideiglenesen,
és a főablak `grabWindow()` kimenetét méri, nem a QML színtulajdonságait.
"""

from __future__ import annotations

import math
from pathlib import Path
from statistics import median

from PIL import Image, ImageDraw
from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtGui import QImage
from PySide6.QtTest import QTest
import pytest


# A 1280×1005-ös QML-ablakban a főnéző csak 776×776-ra tudná illeszteni a
# képet; a referencia 800×800-as 1:1-es felvételéhez 24 px-rel nagyobb magasság kell.
ABLAK = (1280, 1029)
FOTO_MERET = 800
LILA_MEZŐ = (119, 60, 140)
REFERENCIA_KITOLTES = (87, 75, 91)
REFERENCIA_KERET = (186, 173, 189)


def _color_patches(lib: Path) -> None:
    """Az eredeti 800×800-as színtábla tesztpéldánya, a mért lila mezővel."""
    sorok = (
        ((254, 0, 0), (0, 255, 1), (0, 0, 254), (255, 255, 0)),
        ((0, 255, 255), (255, 0, 254), (255, 255, 255), (0, 0, 0)),
        ((128, 128, 128), (200, 151, 121), (60, 90, 150), (91, 140, 59)),
        ((229, 200, 60), LILA_MEZŐ, (240, 240, 240), (30, 30, 30)),
    )
    kep = Image.new("RGB", (FOTO_MERET, FOTO_MERET))
    festo = ImageDraw.Draw(kep)
    for y, sor in enumerate(sorok):
        for x, szin in enumerate(sor):
            festo.rectangle(
                (x * 200, y * 200, (x + 1) * 200 - 1, (y + 1) * 200 - 1),
                fill=szin,
            )
    # A képfájl csak a pytest ideiglenes könyvtárába kerül.
    kep.save(lib / "color_patches.jpg", "JPEG", quality=100, subsampling=0)


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a valódi főablakban"
    return elem


def _ablak_meretezese(window, qt_app) -> None:
    window.setProperty("width", ABLAK[0])
    window.setProperty("height", ABLAK[1])
    for _ in range(5):
        qt_app.processEvents()


def _egyes_nezetre_hangol(window, qt_app) -> None:
    """A fit-nézet mérete a platform betűmetrikájától függ (a fejléc/sáv magassága).

    Mért: a CI ubuntu-lába 1029 px magas ablakban 805 px-es képet adott (helyben 800), ezért a
    teszt a tesztábra 1:1 mérése előtt az ablak magasságát a mért eltérés szerint igazítja."""
    foto = _item(window, "viewerImage")
    for _ in range(4):
        elteres = float(foto.property("paintedWidth")) - FOTO_MERET
        if abs(elteres) <= 1:
            return
        window.setProperty("height", round(float(window.property("height")) - elteres))
        for _ in range(8):
            qt_app.processEvents()


def _kattint(window, elem, qt_app) -> None:
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    for _ in range(5):
        qt_app.processEvents()


def _kozel_rgb(kep: QImage, x: int, y: int, vart: tuple[int, int, int]) -> None:
    szin = kep.pixelColor(x, y)
    kapott = (szin.red(), szin.green(), szin.blue())
    assert all(abs(a - b) <= 2 for a, b in zip(kapott, vart, strict=True)), (
        f"a renderelt ({x},{y}) RGB {kapott}, a job-69 4. képe szerint "
        f"{vart} (±2)"
    )


def _median_rgb(pixelek: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    return tuple(round(median(csatorna)) for csatorna in zip(*pixelek, strict=True))


def _tavolsag(a: tuple[int, int, int], b: tuple[int, int, int]) -> int:
    return sum(abs(x - y) for x, y in zip(a, b, strict=True))


def _kompozit(
    hatter: tuple[int, int, int],
    eloter: tuple[int, int, int],
    alfa: float,
) -> tuple[int, int, int]:
    return tuple(
        round(h * (1 - alfa) + e * alfa)
        for h, e in zip(hatter, eloter, strict=True)
    )


def _lekerekitett_pont_benne(
    x: float, y: float, szelesseg: float, magassag: float, sugar: float
) -> bool:
    cx = min(max(x, sugar), szelesseg - sugar)
    cy = min(max(y, sugar), magassag - sugar)
    return (x - cx) ** 2 + (y - cy) ** 2 <= sugar**2


def _grid_mintak(
    kep: QImage,
    photo: Image.Image,
    racs: Image.Image,
    racs_kezdete: QPointF,
    foto_kezdete: QPointF,
    kontroll,
    *,
    sugar: float,
    kizart_teglalapok: list[tuple[float, float, float, float]] | None = None,
    fogantyu=None,
    belso_sav: tuple[int, int, int, int] = (0, 0, 0, 0),
) -> tuple[int, int]:
    """A látható gridpixeleket a valódi csempe és a renderelt kép alapján méri."""
    kezdet = kontroll.mapToScene(QPointF(0, 0))
    szelesseg = round(kontroll.width())
    magassag = round(kontroll.height())
    kizarasok = kizart_teglalapok or []
    bal_behuzas, felso_behuzas, jobb_behuzas, also_behuzas = belso_sav
    fogantyu_teglalap = None
    if fogantyu is not None:
        f = fogantyu.mapToScene(QPointF(0, 0))
        fogantyu_teglalap = (
            f.x() - 1,
            f.y() - 1,
            f.x() + fogantyu.width() + 3,
            f.y() + fogantyu.height() + 4,
        )

    lathato = osszes = 0
    for y in range(magassag):
        for x in range(szelesseg):
            if (
                x < bal_behuzas
                or y < felso_behuzas
                or x >= szelesseg - jobb_behuzas
                or y >= magassag - also_behuzas
            ):
                continue
            px = x + 0.5
            py = y + 0.5
            if not _lekerekitett_pont_benne(px, py, szelesseg, magassag, sugar):
                continue
            if fogantyu_teglalap is not None:
                bal, fent, jobb, lent = fogantyu_teglalap
                if kezdet.x() + px >= bal and kezdet.x() + px < jobb:
                    if kezdet.y() + py >= fent and kezdet.y() + py < lent:
                        continue
            if any(
                bal <= kezdet.x() + px < jobb
                and fent <= kezdet.y() + py < lent
                for bal, fent, jobb, lent in kizarasok
            ):
                continue

            jelenet_x = kezdet.x() + px
            jelenet_y = kezdet.y() + py
            racs_x = math.floor(jelenet_x - racs_kezdete.x()) % 44
            racs_y = math.floor(jelenet_y - racs_kezdete.y()) % 44
            racs_rgb = racs.getpixel((racs_x, racs_y))
            # A teljes látható forrásmintát mérjük: a világos rácsvonalat és
            # a mellette futó sötét árnyékvonal pontjait is.
            if racs_rgb[3] == 0:
                continue

            foto_x = math.floor(jelenet_x - foto_kezdete.x())
            foto_y = math.floor(jelenet_y - foto_kezdete.y())
            if not (0 <= foto_x < photo.width and 0 <= foto_y < photo.height):
                continue
            # A JPEG színtáblája 200 px-es mezőkből áll; a mezőhatárokon a
            # kép-szűrés platformfüggő lehet, ezért azokat nem mérjük.
            if foto_x % 200 < 8 or foto_x % 200 > 191:
                continue
            if foto_y % 200 < 8 or foto_y % 200 > 191:
                continue

            # A próbakép 1:1-ben, Qt.Image.Tile 44×44-es mintával rajzolódik.
            # A sáv/gomb előtere a mért, 206-os hatásos alfájú (#4029) réteg.
            szin = (203, 202, 202) if x < 2 or y < 2 or x >= szelesseg - 2 or y >= magassag - 2 else (80, 80, 80)
            foto_rgb = photo.getpixel((foto_x, foto_y))
            grid_alatt = _kompozit(
                foto_rgb,
                racs_rgb[:3],
                racs_rgb[3] / 255,
            )
            racs_nelkul = _kompozit(foto_rgb, szin, 206 / 255)
            racs_folott = _kompozit(grid_alatt, szin, 206 / 255)
            sx = math.floor(jelenet_x)
            sy = math.floor(jelenet_y)
            actual_color = kep.pixelColor(sx, sy)
            actual = (actual_color.red(), actual_color.green(), actual_color.blue())
            lathato += _tavolsag(actual, racs_folott) < _tavolsag(actual, racs_nelkul)
            osszes += 1
    return lathato, osszes


def _szoveg_teglalapok(gomb) -> list[tuple[float, float, float, float]]:
    teglalapok = []
    elemek = list(gomb.childItems())
    while elemek:
        elem = elemek.pop()
        if elem.property("text") in ("APPLY", "CANCEL"):
            kezdet = elem.mapToScene(QPointF(0, 0))
            teglalapok.append(
                (
                    kezdet.x() - 3,
                    kezdet.y() - 3,
                    kezdet.x() + elem.width() + 3,
                    kezdet.y() + elem.height() + 3,
                )
            )
        elemek.extend(elem.childItems())
    return teglalapok


@pytest.fixture
def qml_app_color_patches(qt_app, tmp_path):
    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_color_patches)


def test_a_lila_foto_feletti_savkitoltes_es_keret_a_referenciat_adja(
    qml_app_color_patches, qt_app
):
    """A valódi főablak kimenetén, szöveg és fogantyú nélküli képpontokon mér."""
    window, controller, _engine = qml_app_color_patches
    _ablak_meretezese(window, qt_app)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    window.setProperty("viewerOpen", True)
    for _ in range(8):
        qt_app.processEvents()
    assert controller.photos.filePathAt(0).endswith("color_patches.jpg")

    _kattint(window, _item(window, "editTabFixes"), qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    for _ in range(5):
        qt_app.processEvents()
    _egyes_nezetre_hangol(window, qt_app)
    kep = window.grabWindow()
    assert not kep.isNull(), "a valódi főablak képe nem rajzolódott ki"

    slider = _item(window, "tiltSlider")
    container = _item(window, "toolSliderContainer")
    assert (container.width(), container.height()) == (267, 28)
    assert (slider.x(), slider.width(), slider.height()) == (7, 253, 28)
    hatter = slider.property("background")
    fogantyu = slider.property("handle")
    assert hatter is not None and fogantyu is not None
    assert (hatter.x(), hatter.y(), hatter.width(), hatter.height()) == (
        0,
        0,
        253,
        28,
    )
    assert (fogantyu.width(), fogantyu.height()) == (16, 24)
    assert abs(fogantyu.x() - (253 - 16) / 2) <= 1, (
        "a középállású fogantyú képernyőbeli helye megváltozott"
    )

    # A referencia-fotó 1:1-es. A pixelközéppontok a főablak tényleges
    # képtéglalapjából számolódnak, ezért a teszt nem a QML-szín tulajdonságát
    # olvassa, hanem a `grabWindow()` képét méri.
    photo = _item(window, "viewerImage")
    painted_width = float(photo.property("paintedWidth"))
    painted_height = float(photo.property("paintedHeight"))
    assert abs(painted_width - FOTO_MERET) <= 1
    assert abs(painted_height - FOTO_MERET) <= 1
    photo_origin = photo.mapToScene(
        QPointF(
            (photo.width() - painted_width) / 2,
            (photo.height() - painted_height) / 2,
        )
    )
    hatter_origin = hatter.mapToScene(QPointF(0, 0))
    assert 200 < (hatter_origin.x() + 45 - photo_origin.x()) < 400
    assert 600 < (hatter_origin.y() + 2 - photo_origin.y()) < 800

    slider_origin = slider.mapToScene(QPointF(0, 0))
    lila_xek = range(215, 396)
    felso_sorok = []
    for y in (0, 1):
        sor = []
        for photo_x in lila_xek:
            color = kep.pixelColor(
                math.floor(photo_origin.x() + photo_x + 0.5),
                math.floor(hatter_origin.y() + y + 0.5),
            )
            sor.append((color.red(), color.green(), color.blue()))
        felso_sorok.append(sor)
    assert _median_rgb(felso_sorok[0]) == pytest.approx(REFERENCIA_KERET, abs=2)
    assert _median_rgb(felso_sorok[1]) == pytest.approx(REFERENCIA_KERET, abs=2), (
        "a keret második (felső) sora is a referencia színét adja"
    )

    kitoltes = []
    for slider_y in range(2, 26):
        sy = math.floor(hatter_origin.y() + slider_y + 0.5)
        for photo_x in lila_xek:
            sx = math.floor(photo_origin.x() + photo_x + 0.5)
            helyi_x = sx - math.floor(slider_origin.x())
            if abs(helyi_x - fogantyu.x() - fogantyu.width() / 2) < 11:
                continue
            color = kep.pixelColor(sx, sy)
            kitoltes.append((color.red(), color.green(), color.blue()))
    assert _median_rgb(kitoltes) == pytest.approx(REFERENCIA_KITOLTES, abs=2)

    feher_mezo = []
    feher_x_kezd = max(415, math.ceil(hatter_origin.x() + 2 - photo_origin.x()))
    feher_x_vege = min(600, math.floor(hatter_origin.x() + hatter.width() - 2 - photo_origin.x()))
    assert feher_x_vege - feher_x_kezd >= 8, (
        "a csúszkának elég széles szakasza essen a #F0 mezőre az áttetszőség méréséhez"
    )
    for slider_y in range(2, 26):
        sy = math.floor(hatter_origin.y() + slider_y + 0.5)
        for photo_x in range(feher_x_kezd, feher_x_vege):
            sx = math.floor(photo_origin.x() + photo_x + 0.5)
            color = kep.pixelColor(sx, sy)
            feher_mezo.append((color.red(), color.green(), color.blue()))
    assert _median_rgb(feher_mezo) == pytest.approx((111, 110, 111), abs=2), (
        "a világosszürke (#F0) fotó fölött is látszania kell a sáv áttetszőségének"
    )


def test_a_kiegyenesito_racs_elso_megnyitaskor_atlatszik_a_savon_de_nem_a_gombokon(
    qml_app_color_patches, qt_app
):
    """Első megnyitás után, UI-s ki-be kapcsolás nélkül vizsgálja a rácsot."""
    window, controller, _engine = qml_app_color_patches
    _ablak_meretezese(window, qt_app)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", 0)
    window.setProperty("viewerOpen", True)
    for _ in range(8):
        qt_app.processEvents()
    _kattint(window, _item(window, "editTabFixes"), qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    for _ in range(8):
        qt_app.processEvents()
    _egyes_nezetre_hangol(window, qt_app)

    window_image = window.grabWindow()
    assert not window_image.isNull(), "a valódi főablak képe nem rajzolódott ki"
    assert window_image.devicePixelRatio() == pytest.approx(1)
    photo_item = _item(window, "viewerImage")
    painted_width = float(photo_item.property("paintedWidth"))
    painted_height = float(photo_item.property("paintedHeight"))
    assert (painted_width, painted_height) == pytest.approx((FOTO_MERET, FOTO_MERET), abs=1)
    photo_origin = photo_item.mapToScene(
        QPointF(
            (photo_item.width() - painted_width) / 2,
            (photo_item.height() - painted_height) / 2,
        )
    )

    slider = _item(window, "tiltSlider")
    background = slider.property("background")
    handle = slider.property("handle")
    overlay = _item(window, "straightenGridOverlay")
    grid_image = _item(window, "straightenGridImage")
    assert background is not None and handle is not None
    assert overlay.property("visible") is True
    assert overlay.property("gombparMaszkAktiv") is True

    dpr = float(window.devicePixelRatio())
    assert dpr == pytest.approx(1), "a 44×44-es referencia-rács tesztje 1× DPR-re épül"
    grid_path = (
        Path(__file__).resolve().parents[3]
        / "src/picasapy/app/assets/tools/straighten_grid.png"
    )
    grid = Image.open(grid_path).convert("RGBA")
    photo = Image.open(controller.photos.filePathAt(0)).convert("RGB")
    racs_kezdete = grid_image.mapToScene(QPointF(0, 0))
    kizart_jelolok = []
    bg_origin = background.mapToScene(QPointF(0, 0))
    for tick_x in (1, 126, 251):
        kizart_jelolok.append(
            (
                bg_origin.x() + tick_x - 1,
                bg_origin.y() + 1,
                bg_origin.x() + tick_x + 2,
                bg_origin.y() + background.height() - 1,
            )
        )
    savon_latszo = _grid_mintak(
        window_image,
        photo,
        grid,
        racs_kezdete,
        photo_origin,
        background,
        sugar=14,
        kizart_teglalapok=kizart_jelolok,
        fogantyu=handle,
    )
    assert savon_latszo[1] >= 200, (
        f"a teljes sávon túl kevés valódi rácsvonal-mintát mértünk: {savon_latszo[1]}"
    )
    arany = savon_latszo[0] / savon_latszo[1]
    assert arany >= 0.95, (
        f"első megnyitáskor a sáv alatti rácsvonalaknak legalább 95%-ban át kell "
        f"látszaniuk: {savon_latszo[0]}/{savon_latszo[1]} ({arany:.1%})"
    )

    gombok_latszo = 0
    gombok_osszes = 0
    for nev in ("tiltApplyButton", "tiltCancelButton"):
        button = _item(window, nev)
        latszo = _grid_mintak(
            window_image,
            photo,
            grid,
            racs_kezdete,
            photo_origin,
            button,
            sugar=7,
            kizart_teglalapok=_szoveg_teglalapok(button),
            belso_sav=(8, 0, 8, 0),
        )
        gombok_latszo += latszo[0]
        gombok_osszes += latszo[1]
    assert gombok_osszes >= 20, "a gombok alatt kevés háló-mintapont esik"
    assert gombok_latszo == 0, (
        f"a hálónak nem szabad a gombok alatt látszania: "
        f"{gombok_latszo}/{gombok_osszes} képpont"
    )

    # A számszerű geometriaőr a track helyét/méretét védi; az alábbi
    # RGB-ellenőrzés a vizuális egyezést ténylegesen a renderelt kimeneten méri.
