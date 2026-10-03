"""#3924 — a Kiegyenesítés rácsa a valódi nézőképen, képpont szerint.

A képernyőméret és a két színminta a `ui-audit-editor.md` #69/#71
méréseiből jön. A teszt a `grabWindow()` képét ellenőrzi, és a Kiegyenesítés
csempéjére valódi egérkattintást ad.
"""

from __future__ import annotations

import math
import os
from pathlib import Path

from PySide6.QtCore import QObject, QPoint, QPointF, QRect, QSize, Qt
from PySide6.QtGui import QColor, QGuiApplication, QImage, QKeyEvent, QPainter
from PySide6.QtTest import QTest
import pytest


ABLAK = (1280, 1005)


def _item(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található a kirajzolt fában"
    return elem


def _vizualis_item(gyoker, nev: str):
    """A Repeater-csempéket a vizuális fa járja be, ne a QObject-fát."""
    kovetkezok = [gyoker]
    while kovetkezok:
        elem = kovetkezok.pop()
        if elem.objectName() == nev:
            return elem
        kovetkezok.extend(elem.childItems())
    raise AssertionError(f"{nev} nem található a kirajzolt fában")


def _kep_mentese(
    path: Path,
    size: int | tuple[int, int],
    *,
    szin: str,
    negyedes: bool = False,
) -> None:
    szelesseg, magassag = (size, size) if isinstance(size, int) else size
    kep = QImage(szelesseg, magassag, QImage.Format.Format_RGB32)
    kep.fill(QColor(szin))
    if negyedes:
        festo = QPainter(kep)
        fele = szelesseg // 2
        festo.fillRect(QRect(0, 0, fele, fele), QColor("red"))
        festo.fillRect(QRect(fele, 0, szelesseg - fele, fele), QColor("white"))
        festo.fillRect(QRect(0, fele, fele, magassag - fele), QColor("blue"))
        festo.fillRect(
            QRect(fele, fele, szelesseg - fele, magassag - fele), QColor("green")
        )
        festo.end()
    assert kep.save(str(path), "JPEG", 100), f"nem írható a próbakép: {path}"


def _forrasok(
    controller,
    *,
    negyedes: bool = False,
    masodik_meret: int | tuple[int, int] = 1024,
    masodik_szin: str = "white",
) -> None:
    """A két indexelt négyzetképet determinisztikus képre cseréli."""
    _kep_mentese(
        Path(str(controller.photos.filePathAt(0))), 800, szin="black",
        negyedes=negyedes,
    )
    _kep_mentese(
        Path(str(controller.photos.filePathAt(1))),
        masodik_meret,
        szin=masodik_szin,
    )


def _beallit_ablak(window, qt_app, ablak: tuple[int, int] = ABLAK) -> None:
    window.setProperty("width", ablak[0])
    window.setProperty("height", ablak[1])
    for _ in range(5):
        qt_app.processEvents()


def _pont(item, x: float, y: float) -> QPoint:
    pont = item.mapToScene(QPointF(x, y))
    return QPoint(round(pont.x()), round(pont.y()))


def _kattint(window, elem, qt_app) -> None:
    assert elem.width() > 0 and elem.height() > 0, "a vezérlő nem látható"
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(elem, elem.width() / 2, elem.height() / 2),
    )
    for _ in range(5):
        qt_app.processEvents()


def _kuldd_shift(tipus) -> None:
    esemeny = QKeyEvent(
        tipus,
        Qt.Key.Key_Shift,
        Qt.KeyboardModifier.ShiftModifier,
    )
    QGuiApplication.sendEvent(QGuiApplication.instance(), esemeny)


def _nezobe_lep(window, qt_app, index: int = 0):
    window.setProperty("viewerOpen", True)
    viewer = _item(window, "photoViewer")
    viewer.setProperty("currentIndex", index)
    for _ in range(8):
        qt_app.processEvents()
    return viewer


def _felvetel(window, utvonal: Path) -> QImage:
    kep = window.grabWindow()
    assert not kep.isNull(), "a néző ablaka nem rajzolódott ki"
    assert kep.save(str(utvonal), "PNG"), f"nem menthető a felvétel: {utvonal}"
    return kep


def _racs_mintapontok(area) -> tuple[QPoint, QPoint, QPoint, QPoint]:
    """A spec szerinti vonal, árnyék és a fázisukat őrző üres pixelek.

    A csempe kezdete a képfelület képernyőn mért közepéből számított
    `trunc(közép − (249,153))`. Az üres minták a ±1 képpontos fáziseltérést
    is kimutatják.
    """
    kozep = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
    x0 = math.trunc(kozep.x() - 249)
    y0 = math.trunc(kozep.y() - 153)
    return (
        QPoint(x0 + 41, y0 + 43),  # szürke vonal
        QPoint(x0 + 42, y0),  # fekete árnyék
        QPoint(x0 + 40, y0 + 43),  # a vonal előtti üres oszlop
        QPoint(x0 + 41, y0 + 1),  # a vonal üres szakasza
    )


def _rgb(kep: QImage, pont: QPoint) -> tuple[int, int, int]:
    szin = kep.pixelColor(pont.x(), pont.y())
    return szin.red(), szin.green(), szin.blue()


def _assert_rgb(kep: QImage, pont: QPoint, vart: tuple[int, int, int]) -> None:
    kapott = _rgb(kep, pont)
    assert all(abs(a - b) <= 2 for a, b in zip(kapott, vart, strict=True)), (
        f"a {pont.x()},{pont.y()} képpont RGB-je {kapott}, "
        f"a specifikáció szerint {vart} (±2)"
    )


def _assert_racs_csempe(
    kep: QImage, area, image, hatter: tuple[int, int, int] | QImage
) -> None:
    """A kirajzolt, képen belüli 44×44-es csempe minden pixele egyezzen."""
    kozep = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
    x0 = math.trunc(kozep.x() - 249)
    y0 = math.trunc(kozep.y() - 153)
    clip_x, clip_y, clip_szel, clip_mag = _kep_kivagas_scene(image)
    x0 += math.ceil((clip_x - x0) / 44) * 44
    y0 += math.ceil((clip_y - y0) / 44) * 44
    assert x0 + 44 <= clip_x + clip_szel
    assert y0 + 44 <= clip_y + clip_mag
    szurke = "G..GGG..GGG..GGG..GGG..GGG..GGG..GGG..GGG.GG"
    arnyek = "kk..kkk..kkk..kkk..kkk..kkk..kkk..kkk..kkG.k"

    for y in range(44):
        for x in range(44):
            szurke_vonal = (
                (x == 41 and szurke[y] == "G")
                or (y == 41 and szurke[x] == "G")
            )
            arnyek_vonal = (
                (x == 42 and arnyek[y] == "k")
                or (y == 42 and arnyek[x] == "k")
            )
            pont = QPoint(x0 + x, y0 + y)
            alap = _rgb(hatter, pont) if isinstance(hatter, QImage) else hatter
            if szurke_vonal:
                vart = tuple(((csatorna * 128) >> 8) + 128 for csatorna in alap)
            elif arnyek_vonal:
                vart = tuple((csatorna * 179) >> 8 for csatorna in alap)
            else:
                vart = alap
            _assert_rgb(kep, pont, vart)


def _vezerlo_rect(elem) -> QRect:
    bal_felso = elem.mapToScene(QPointF(0, 0))
    return QRect(
        round(bal_felso.x()),
        round(bal_felso.y()),
        round(elem.width()),
        round(elem.height()),
    )


def _rect_azonos(egy: QImage, ketto: QImage, rect: QRect) -> bool:
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            if egy.pixelColor(x, y) != ketto.pixelColor(x, y):
                return False
    return True


def _kulonbozo_pixelek(egy: QImage, ketto: QImage, rect: QRect) -> int:
    db = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            if egy.pixelColor(x, y) != ketto.pixelColor(x, y):
                db += 1
    return db


def _max_csatornaelteres(egy: QImage, ketto: QImage, rect: QRect) -> int:
    legnagyobb = 0
    for y in range(rect.top(), rect.bottom() + 1):
        for x in range(rect.left(), rect.right() + 1):
            a = egy.pixelColor(x, y)
            b = ketto.pixelColor(x, y)
            legnagyobb = max(
                legnagyobb,
                abs(a.red() - b.red()),
                abs(a.green() - b.green()),
                abs(a.blue() - b.blue()),
            )
    return legnagyobb


def _tile_tipus(x: int, y: int, x0: int, y0: int) -> str:
    szurke = "G..GGG..GGG..GGG..GGG..GGG..GGG..GGG..GGG.GG"
    arnyek = "kk..kkk..kkk..kkk..kkk..kkk..kkk..kkk..kkG.k"
    tx = (x - x0) % 44
    ty = (y - y0) % 44
    if (tx == 41 and szurke[ty] == "G") or (ty == 41 and szurke[tx] == "G"):
        return "G"
    if (tx == 42 and arnyek[ty] == "k") or (ty == 42 and arnyek[tx] == "k"):
        return "k"
    return "."


def _kep_teglalap_scene(image) -> tuple[float, float, float, float]:
    """A kirajzolt kép folytonos téglalapja a jelenet koordinátáiban."""
    bal = (image.width() - image.property("paintedWidth")) / 2
    fent = (image.height() - image.property("paintedHeight")) / 2
    szel = image.property("paintedWidth")
    mag = image.property("paintedHeight")
    pontok = [
        image.mapToScene(QPointF(bal, fent)),
        image.mapToScene(QPointF(bal + szel, fent)),
        image.mapToScene(QPointF(bal, fent + mag)),
        image.mapToScene(QPointF(bal + szel, fent + mag)),
    ]
    return (
        min(p.x() for p in pontok),
        min(p.y() for p in pontok),
        max(p.x() for p in pontok),
        max(p.y() for p in pontok),
    )


def _kep_kivagas_scene(image) -> tuple[int, int, int, int]:
    """A forgatott kép tört téglalapjának floor-ral csonkolt határai."""
    bal, fent, jobb, lent = _kep_teglalap_scene(image)
    bal = math.floor(bal)
    jobb = math.floor(jobb)
    fent = math.floor(fent)
    lent = math.floor(lent)
    return bal, fent, jobb - bal, lent - fent


def _kep_pixel_teljesen_fedett(image, kep: QImage, x: int, y: int) -> bool:
    """A teljes képernyőpixel a kép tört téglalapján belül van-e."""
    bal, fent, jobb, lent = _kep_teglalap_scene(image)
    pixel_meret = 1 / kep.devicePixelRatio()
    pixel_bal = x * pixel_meret
    pixel_fent = y * pixel_meret
    return (
        bal <= pixel_bal
        and pixel_bal + pixel_meret <= jobb
        and fent <= pixel_fent
        and pixel_fent + pixel_meret <= lent
    )


def _assert_racs_szelen(
    racsos: QImage,
    racs_nelkul: QImage,
    area,
    image,
    toolbar,
) -> None:
    """A négy képszélen a teljes képpontokat szigorúan ellenőrzi.

    A tört képkerettel metsződő szélpixelek színe a háttér és a klip
    lefedettségétől is függ, ezért azokon nem várható teljes csempeszín.
    """
    kozep = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
    x0 = math.trunc(kozep.x() - 249)
    y0 = math.trunc(kozep.y() - 153)
    bal, fent, szel, mag = _kep_kivagas_scene(image)
    jobb, lent = bal + szel, fent + mag
    toolbar_rect = _vezerlo_rect(toolbar)
    # A tesztben a külső photoArea.clip ki van kapcsolva, hogy a belső,
    # csonkolt képkivágás négy oldala a teljes ablakban megfigyelhető legyen.
    area_rect = racsos.rect()

    # A befogadott pixelközök a csonkolt képtéglalap határain belül vannak.
    szelek = (
        ("bal", ((bal, y) for y in range(fent, lent))),
        ("jobb", ((jobb - 1, y) for y in range(fent, lent))),
        ("felso", ((x, fent) for x in range(bal, jobb))),
        ("also", ((x, lent - 1) for x in range(bal, jobb))),
    )
    for _nev, pontok in szelek:
        pontlista = list(pontok)
        for x, y in pontlista:
            if not area_rect.contains(x, y):
                continue
            if toolbar_rect.contains(x, y):
                continue
            # A képszélre eső tört pixel csak részben fedi a fotót: a
            # néző háttérszínével is keveredik. A teljes képpontokat továbbra
            # is pontosan a specifikáció szerint ellenőrizzük.
            if not _kep_pixel_teljesen_fedett(image, racsos, x, y):
                continue
            tipus = _tile_tipus(x, y, x0, y0)
            if tipus == ".":
                continue
            alap = _rgb(racs_nelkul, QPoint(x, y))
            if tipus == "G":
                vart = tuple(((csatorna * 128) >> 8) + 128 for csatorna in alap)
            else:
                vart = tuple((csatorna * 179) >> 8 for csatorna in alap)
            _assert_rgb(racsos, QPoint(x, y), vart)

    # A szomszédos, levágott sávokban nem jelenhet meg rács egyetlen képpontja sem.
    for nev, pontok in (
        ("bal", ((bal - 1, y) for y in range(fent, lent))),
        ("jobb", ((jobb, y) for y in range(fent, lent))),
        ("felso", ((x, fent - 1) for x in range(bal, jobb))),
        ("also", ((x, lent) for x in range(bal, jobb))),
    ):
        for x, y in pontok:
            if not area_rect.contains(x, y):
                continue
            assert _rgb(racsos, QPoint(x, y)) == _rgb(racs_nelkul, QPoint(x, y)), (
                f"a {nev} szélen túllógott a háló a {x},{y} képpontnál"
            )


@pytest.mark.parametrize(
    ("filter_id", "tab_name", "button_name", "shift"),
    [
        ("tilt", "editTabFixes", "editToolTilt", False),
        ("radblur", "editTabEffects", "effectRadblur", False),
        ("radsat", "editTabEffects", "effectRadsat", False),
        ("dir_tint", "editTabEffects", "effectDirTint", False),
        ("radtint", "editTabEffects", "effectDirTint", True),
        ("linblur", "editTabLegacy", "legacyEffect_linblur", False),
        ("dir_sat", "editTabLegacy", "legacyEffect_dir_sat", False),
        ("dir_brite", "editTabLegacy", "legacyEffect_dir_brite", False),
        ("dir_sharp", "editTabLegacy", "legacyEffect_dir_sharp", False),
    ],
)
def test_forcefit_szuro_nyitasa_illesztesre_valt(
    qml_app_negyzet_kepek, qt_app, filter_id, tab_name, button_name, shift
):
    """#4021: a `filterdesc.xml` mind a kilenc forcefit szűrője illesszen."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    panel = _item(window, "viewerEditorPanel")
    viewer.setProperty("zoomValue", 0.7)
    for _ in range(8):
        qt_app.processEvents()
    assert viewer.property("zoomFactor") > 1.01, "a próbaképnek nagyítva kell lennie"

    _kattint(window, _item(window, tab_name), qt_app)
    if tab_name == "editTabLegacy":
        assert panel.property("activeTab") == 6
        legacy_column = _item(window, "legacyEffectsColumn")
        assert legacy_column.property("visible") is True
        assert legacy_column.property("effects"), "a régi effektfül katalógusa üres"
        button = _vizualis_item(legacy_column, button_name)
    else:
        button = _item(window, button_name)
    if shift:
        _kuldd_shift(QKeyEvent.Type.KeyPress)
    try:
        if shift:
            assert panel.property("shiftMasodlagos") is True
        _kattint(window, button, qt_app)
    finally:
        if shift:
            _kuldd_shift(QKeyEvent.Type.KeyRelease)
    qt_app.processEvents()

    if filter_id == "tilt":
        assert panel.property("tiltActive") is True
    elif filter_id in {"radblur", "radsat", "dir_tint", "radtint"}:
        assert panel.property("paramPanelActive") is True
        assert panel.property("paramEffectName") == filter_id
    else:
        effect_counts = viewer.property("editCtl").property("effectChainCounts")
        assert effect_counts.get(filter_id, 0) == 1, (
            f"a {filter_id} legacy eszköz felületi kattintása nem alkalmazódott"
        )

    assert viewer.property("zoomValue") == 0, (
        f"a {filter_id} eszköz megnyitása után a néző maradjon kitöltő nézetben"
    )


def test_nagyitott_nezobol_nyitott_kiegyenesitesnel_a_racs_a_teljes_kepet_fedi(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """#4021: a valódi felvételen a háló a teljes képtéglalapot fedi."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    viewer.setProperty("zoomValue", 0.7)
    for _ in range(8):
        qt_app.processEvents()
    assert viewer.property("zoomFactor") > 1.01, "a próbaképnek nagyítva kell lennie"

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    overlay = _item(window, "straightenGridOverlay")
    area = _item(window, "viewerPhotoArea")
    image = _item(window, "viewerImage")
    toolbar = _item(window, "editorToolBar")
    area.setProperty("clip", False)
    overlay.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    racs_nelkul = _felvetel(window, tmp_path / "forcefit-racs-nelkul.png")
    overlay.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()
    racsos = _felvetel(window, tmp_path / "forcefit-racs.png")

    _assert_racs_szelen(racsos, racs_nelkul, area, image, toolbar)
    assert viewer.property("zoomValue") == 0, (
        "a Kiegyenesítés megnyitása után a nézőnek illesztett nézetre kell váltania"
    )
    _kattint(window, _item(window, "tiltCancelButton"), qt_app)
    assert viewer.property("zoomValue") == 0, (
        "bezáráskor az illesztett nagyítás maradjon meg"
    )


def test_a_racs_latszik_es_alkalmazas_megse_vagy_lapozas_utan_eltunik(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller)
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app)
    area = _item(window, "viewerPhotoArea")
    panel = _item(window, "viewerEditorPanel")
    vonalpont, arnyekpont, vonal_elotti, vonal_ures = _racs_mintapontok(area)

    alap_fekete = _felvetel(window, tmp_path / "racs-nelkul-fekete.png")
    _assert_rgb(alap_fekete, vonalpont, (0, 0, 0))

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    assert panel.property("tiltActive") is True
    grid_image = _item(window, "straightenGridImage")
    assert grid_image.property("sourceSize") == QSize(44, 44)
    racsos = _felvetel(window, tmp_path / "kiegyenesites-nyitva-fekete.png")
    _assert_rgb(racsos, vonalpont, (128, 128, 128))
    _assert_rgb(racsos, vonal_elotti, (0, 0, 0))
    _assert_rgb(racsos, vonal_ures, (0, 0, 0))
    # Az abszolút hely (#69: x=397, 441…) a néző kép-területén múlik, ami
    # nálunk ma (−1, −5) képponttal eltér — külön jegy (#4028); a háló a
    # kép-terület közepéhez mérve képpontra helyes (a fenti mintapontok).

    _kattint(window, _item(window, "tiltCancelButton"), qt_app)
    assert panel.property("tiltActive") is False
    megse_utan = _felvetel(window, tmp_path / "megse-utan-fekete.png")
    _assert_rgb(megse_utan, vonalpont, (0, 0, 0))

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    racs_alatt = _felvetel(window, tmp_path / "alkalmazas-elott-fekete.png")
    _assert_rgb(racs_alatt, vonalpont, (128, 128, 128))
    _kattint(window, _item(window, "tiltApplyButton"), qt_app)
    alkalmazas_utan = _felvetel(window, tmp_path / "alkalmazas-utan-fekete.png")
    _assert_rgb(alkalmazas_utan, vonalpont, (0, 0, 0))

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    racs_lapozas_elott = _felvetel(window, tmp_path / "lapozas-elott-fekete.png")
    _assert_rgb(racs_lapozas_elott, vonalpont, (128, 128, 128))
    _kattint(window, _item(window, "viewerNextButton"), qt_app)
    assert viewer.property("currentIndex") == 1
    assert panel.property("tiltActive") is False
    lapozas_utan = _felvetel(window, tmp_path / "lapozas-utan-feher.png")
    _assert_rgb(lapozas_utan, arnyekpont, (255, 255, 255))

    _kattint(window, _item(window, "editToolTilt"), qt_app)
    feher_racs = _felvetel(window, tmp_path / "kiegyenesites-nyitva-feher.png")
    _assert_rgb(feher_racs, arnyekpont, (178, 178, 178))
    _assert_rgb(feher_racs, vonal_elotti, (255, 255, 255))
    _kattint(window, _item(window, "tiltCancelButton"), qt_app)
    feher_megse_utan = _felvetel(window, tmp_path / "megse-utan-feher.png")
    _assert_rgb(feher_megse_utan, arnyekpont, (255, 255, 255))


def test_a_csempe_44_logikai_pixel_es_vonalai_elesek_minden_dpi_n(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    """A rögzített csempe 1×, 1,5× és 2× kijelzőn is élesen rajzolódik."""
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, masodik_szin="black")
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    meretarany = float(window.devicePixelRatio())
    vart_arany = float(os.environ.get("QT_SCALE_FACTOR", "1"))
    assert meretarany == pytest.approx(vart_arany)
    assert meretarany >= 1

    grid_image = _item(window, "straightenGridImage")
    assert grid_image.property("sourceSize") == QSize(44, 44), (
        "a megjelenített csempét fix 44×44-es forrásméretre kell kérni"
    )

    overlay = _item(window, "straightenGridOverlay")
    overlay.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    hatterkep = _felvetel(window, tmp_path / f"racs-nelkul-{meretarany:g}x.png")
    overlay.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()
    racsos = _felvetel(window, tmp_path / f"racs-{meretarany:g}x.png")
    assert racsos.width() == round(window.width() * meretarany)
    assert racsos.height() == round(window.height() * meretarany)

    kozep = area.mapToScene(QPointF(area.width() / 2, area.height() / 2))
    y0 = math.trunc(kozep.y() - 153)
    kep_bal, kep_fent, kep_szel, kep_mag = _kep_kivagas_scene(
        _item(window, "viewerImage")
    )
    kep_jobb = kep_bal + kep_szel
    kep_lent = kep_fent + kep_mag
    y_sor = next(
        (
            y
            for y in range(racsos.height())
            if y0 + 43 <= (y + 0.5) / meretarany < y0 + 44
        ),
        None,
    )
    assert y_sor is not None, "nem található a szürke vonal vizsgálható sora"
    elso_x = max(0, math.ceil((kep_bal + 2) * meretarany))
    utolso_x = min(racsos.width(), math.floor((kep_jobb - 2) * meretarany))
    vonalszakaszok: list[tuple[int, int]] = []
    elozo_vonal = False
    for x in range(elso_x, utolso_x):
        if not kep_fent <= (y_sor + 0.5) / meretarany < kep_lent:
            continue
        alap = _rgb(hatterkep, QPoint(x, y_sor))
        kapott = _rgb(racsos, QPoint(x, y_sor))
        if kapott != alap:
            vart = tuple(((csatorna * 128) >> 8) + 128 for csatorna in alap)
            _assert_rgb(racsos, QPoint(x, y_sor), vart)
            if elozo_vonal:
                kezdet, szel = vonalszakaszok[-1]
                vonalszakaszok[-1] = (kezdet, szel + 1)
            else:
                vonalszakaszok.append((x, 1))
            elozo_vonal = True
        else:
            elozo_vonal = False
    assert len(vonalszakaszok) >= 6, "nem látszik elég függőleges rácsvonal"
    cella = round(44 * meretarany)
    for _, szel in vonalszakaszok:
        assert math.floor(meretarany) <= szel <= math.ceil(meretarany), (
            f"az 1 logikai képpontos vonal szélessége {szel} raszterpixel"
        )
    for (x1, _), (x2, _) in zip(
        vonalszakaszok, vonalszakaszok[1:], strict=False
    ):
        assert abs((x2 - x1) - cella) <= 1, (
            f"a csempék távolsága {x2 - x1}, nem 44×{meretarany:g}"
        )


def test_nagyitas_kozben_az_eszkozsav_a_kep_aljahoz_igazodik(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller)
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    image = _item(window, "viewerImage")
    toolbar = _item(window, "editorToolBar")

    image.setProperty("scale", 1.3)
    image.setProperty("x", image.x() + 31)
    image.setProperty("y", image.y() - 17)
    for _ in range(8):
        qt_app.processEvents()

    x = (image.width() - toolbar.width()) / 2 + toolbar.width() / 2
    y = (image.height() + image.property("paintedHeight")) / 2
    y -= toolbar.height() / 2 + 10
    vart = image.mapToScene(QPointF(x, y))
    kapott = toolbar.mapToScene(QPointF(toolbar.width() / 2, toolbar.height() / 2))
    _felvetel(window, tmp_path / "racs-nagyitott-eszkozsav.png")
    assert abs(vart.x() - kapott.x()) <= 1 and abs(vart.y() - kapott.y()) <= 1, (
        "a nagyított kép elmozdult az eszközsáv alól"
    )


def test_a_racs_all_es_a_kep_fordul_a_valodi_csuszka_huzasakor(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, negyedes=True)
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app)
    area = _item(window, "viewerPhotoArea")
    image = _item(window, "viewerImage")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    kezdo = _felvetel(window, tmp_path / "huzas-elott.png")
    vonalpont, arnyekpont, _, _ = _racs_mintapontok(area)
    nyitott = _felvetel(window, tmp_path / "racs-nyitva-huzas-elott.png")
    _assert_rgb(nyitott, vonalpont, (255, 128, 128))
    _assert_racs_csempe(nyitott, area, image, (255, 0, 0))

    slider = _item(window, "tiltSlider")
    apply = _item(window, "tiltApplyButton")
    cancel = _item(window, "tiltCancelButton")
    toolbar_geometria = tuple(
        (elem.width(), elem.height(), _vezerlo_rect(elem))
        for elem in (slider, apply, cancel)
    )

    QTest.mousePress(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(slider, slider.width() / 2, slider.height() / 2),
    )
    QTest.mouseMove(
        window,
        _pont(slider, slider.width() * 0.78, slider.height() / 2),
        10,
    )
    for _ in range(8):
        qt_app.processEvents()
    assert slider.property("pressed") is True, "a próba nem húzás közben készült"
    assert abs(float(slider.property("value"))) >= 0.2
    huzas_kozben = _felvetel(window, tmp_path / "huzas-kozben.png")

    racs_elem = _item(window, "straightenGridOverlay")
    racs_elem.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()

    kep_a_racs_alatt = _felvetel(window, tmp_path / "fordult-kep-racs-nelkul.png")
    hatter = _rgb(kep_a_racs_alatt, vonalpont)
    vart_vonal = tuple(((csatorna * 128) >> 8) + 128 for csatorna in hatter)
    _assert_rgb(huzas_kozben, vonalpont, vart_vonal)
    alap_hatter = _rgb(kep_a_racs_alatt, arnyekpont)
    vart_arnyek = tuple((csatorna * 179) >> 8 for csatorna in alap_hatter)
    _assert_rgb(huzas_kozben, arnyekpont, vart_arnyek)

    area_scene = area.mapToScene(QPointF(0, 0))
    area_rect = QRect(
        round(area_scene.x()),
        round(area_scene.y()),
        round(area.width()),
        round(area.height()),
    )
    assert _kulonbozo_pixelek(kezdo, kep_a_racs_alatt, area_rect) > 200, (
        "a kép nem változott a Kiegyenesítés csúszkájának húzásakor"
    )

    racs_elem.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()

    racs_ujra = _felvetel(window, tmp_path / "huzas-kozben-racs.png")
    for elem, (szelesseg, magassag, rect) in zip(
        (slider, apply, cancel), toolbar_geometria, strict=True
    ):
        assert (elem.width(), elem.height(), _vezerlo_rect(elem)) == (
            szelesseg,
            magassag,
            rect,
        ), "a csúszka vagy a gomb elmozdult a rács kirajzolásakor"
    assert _kulonbozo_pixelek(
        racs_ujra, kep_a_racs_alatt, _vezerlo_rect(slider)
    ) > 0, "a csúszka sávja fölött eltűnt a Picasában látható rács"
    apply_rect = _vezerlo_rect(apply)
    cancel_rect = _vezerlo_rect(cancel)
    gombpar = QRect(
        min(apply_rect.left(), cancel_rect.left()),
        min(apply_rect.top(), cancel_rect.top()),
        max(apply_rect.right(), cancel_rect.right())
        - min(apply_rect.left(), cancel_rect.left())
        + 1,
        max(apply_rect.bottom(), cancel_rect.bottom())
        - min(apply_rect.top(), cancel_rect.top())
        + 1,
    )
    assert _kulonbozo_pixelek(racs_ujra, kep_a_racs_alatt, gombpar) == 0, (
        "a gombpár befoglaló téglalapján — a rést is beleértve — "
        "átlátszik a háló"
    )

    QTest.mouseRelease(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        _pont(slider, slider.width() * 0.78, slider.height() / 2),
    )
    for _ in range(5):
        qt_app.processEvents()


def test_a_paratlan_meretu_kep_nem_mozditja_el_a_racsot(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    _forrasok(controller, masodik_meret=1023, masodik_szin="black")
    _beallit_ablak(window, qt_app)
    viewer = _nezobe_lep(window, qt_app, index=1)
    area = _item(window, "viewerPhotoArea")
    panel = _item(window, "viewerEditorPanel")
    _kattint(window, _item(window, "editToolTilt"), qt_app)

    assert viewer.property("currentIndex") == 1
    assert panel.property("tiltActive") is True
    kep = _felvetel(window, tmp_path / "paratlan-meretu-kep-racs.png")
    vonalpont, arnyekpont, vonal_elotti, vonal_ures = _racs_mintapontok(area)
    _assert_rgb(kep, vonalpont, (128, 128, 128))
    _assert_rgb(kep, arnyekpont, (0, 0, 0))
    _assert_rgb(kep, vonal_elotti, (0, 0, 0))
    _assert_rgb(kep, vonal_ures, (0, 0, 0))


def test_tort_illesztesu_nagy_kepen_mindket_iranyu_vonal_megjelenik(
    qml_app_negyzet_kepek, qt_app, tmp_path
):
    window, controller, _ = qml_app_negyzet_kepek
    # A 700×467-es kép kisebb a Kiegyenesítés nézőterületénél, ezért a
    # #4063 szerinti 1:1-es illesztés nem ad tört méretet. Nagyobb forrás kell
    # a tört PreserveAspectFit és a rács két irányú raszterpróbájához.
    _forrasok(controller, masodik_meret=(1400, 934), masodik_szin="black")
    _beallit_ablak(window, qt_app)
    _nezobe_lep(window, qt_app, index=1)
    image = _item(window, "viewerImage")
    assert image.property("paintedHeight") % 1 != 0, (
        "a nézőterületnél nagyobb próbának tört illesztési magasságot kell adnia"
    )
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    racsos = _felvetel(window, tmp_path / "1400x934-tort-illesztes.png")

    _assert_racs_csempe(racsos, area, image, (0, 0, 0))


def _forgatott_300x500_kepek(lib: Path) -> None:
    _kep_mentese(lib / "a.jpg", (300, 500), szin="black")
    _kep_mentese(lib / "b.jpg", (800, 600), szin="black")
    (lib / ".picasa.ini").write_text(
        "[a.jpg]\nrotate=rotate(1)\n", encoding="utf-8"
    )


@pytest.fixture
def qml_app_forgatott_kep(qt_app, tmp_path):
    from tests.app.qml_functional.conftest import _build_qml_app

    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_forgatott_300x500_kepek,
    )


@pytest.mark.parametrize(
    "ablak",
    [
        pytest.param((1280, 1000), id="tort-szelen-ugyanaz-a-hiba"),
        pytest.param((1280, 1002), id="magassag-minusz-3"),
        pytest.param((1280, 1004), id="magassag-minusz-1"),
        pytest.param((1279, 1005), id="szelesseg-minusz-1"),
        pytest.param(ABLAK, id="alap"),
        pytest.param((1281, 1005), id="szelesseg-plusz-1"),
        pytest.param((1280, 1006), id="magassag-plusz-1"),
    ],
)
def test_rotate_1_300x500_kepehez_igazodik_a_negy_oldali_kivagas(
    qml_app_forgatott_kep, qt_app, tmp_path, ablak
):
    window, _controller, _ = qml_app_forgatott_kep
    _beallit_ablak(window, qt_app, ablak)
    _nezobe_lep(window, qt_app)
    image = _item(window, "viewerImage")
    assert image.property("iniSteps") == 1
    area = _item(window, "viewerPhotoArea")
    _kattint(window, _item(window, "editToolTilt"), qt_app)
    toolbar = _item(window, "editorToolBar")
    overlay = _item(window, "straightenGridOverlay")
    area.setProperty("clip", False)
    overlay.setProperty("visible", False)
    for _ in range(5):
        qt_app.processEvents()
    racs_nelkul = _felvetel(window, tmp_path / "rotate-1-racs-nelkul.png")
    overlay.setProperty("visible", True)
    for _ in range(5):
        qt_app.processEvents()
    racsos = _felvetel(window, tmp_path / "rotate-1-racs.png")

    clip_x, clip_y, clip_szel, clip_mag = _kep_kivagas_scene(image)
    bal_fent = overlay.mapToScene(QPointF(0, 0))
    jobb_lent = overlay.mapToScene(QPointF(overlay.width(), overlay.height()))
    assert (math.floor(bal_fent.x()), math.floor(bal_fent.y())) == (clip_x, clip_y)
    assert (math.floor(jobb_lent.x()), math.floor(jobb_lent.y())) == (
        clip_x + clip_szel,
        clip_y + clip_mag,
    )
    _assert_racs_csempe(racsos, area, image, racs_nelkul)
    _assert_racs_szelen(racsos, racs_nelkul, area, image, toolbar)
