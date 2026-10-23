"""A Mozgófilmkészítő a főablak dokumentumlapján jelenik meg (#5264)."""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import (
    Q_ARG,
    QMetaObject,
    QObject,
    QPoint,
    QPointF,
    QSettings,
    QTranslator,
    Qt,
)
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlProperty
from PySide6.QtQuick import QQuickItem
from PySide6.QtTest import QTest
from PIL import Image, ImageDraw

from conftest import _build_qml_app
from support.jpeg_factory import make_jpeg
from support.varakozas import var_feltetelre
from tests.app.qml_functional._fomenu_4420_menu import _megnyit

_MAPPA = "fotok"
# A világos téma színei: a Windows-os Picasa-képernyőkép mért értékei.
_SZURKE_ELOFOGULAT = "#808080"
_FEKETE = "#000000"
_KEK_SZEGELY = "#b4bfe0"
_HASAB_TOLTES = "#e8e8e8"
_KEK_FUL = "#6a80c1"
_FUL_KIVALASZTOTT = "#e8e8e8"
# A nem kijelölt fül átmenetének középértéke (#bec6df → #c5cde4).
_FUL_ALAP = "#c2cbe2"
_LETILTOTT_SZOVEG = "#bababa"
# Az Opciók lista letiltott felirata: a mérce legsötétebb képpontja.
_OPCIO_LETILTOTT = "#b1b1b1"
# A filmcsík bélyegképe a mércén képpontról mérve 50 × 50.
_BELYEG_MERET = 50
# A bélyegek közti rés a mércén 3 képpont (686-735, 739-788, …).
_BELYEG_RES = 3
# A bekapcsolt 1:1 gomb a mércén szürke keretű (nem az arany `_t` keret).
_SZURKE_KERET = "#bbbbbb"
_PIROS_X = "#b10000"
_ZOLD = "#3b8f00"
_KIVALASZTOTT_KEP_KERET = "#009eff"
# Az első fotó álló (240 × 320): a mérce első klipje is álló, és csak így
# látszik a letterbox (a fekete sáv a kép két oldalán).
_FOTO_MERETEK = {"a_elso.jpg": (240, 320), "b_masodik.jpg": (320, 240)}


def _pont(x, y, width, height):
    """A 320 × 240-as rajz koordinátáját a kért fotóméretre viszi."""
    return (round(x * width / 320), round(y * height / 240))


def _keszits_fotokat(library):
    folder = library / _MAPPA
    folder.mkdir()
    for index, (name, (width, height)) in enumerate(_FOTO_MERETEK.items()):
        path = make_jpeg(folder / name, size=(width, height))
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        for y in range(height):
            blend = y / height
            draw.line(
                (0, y, width, y),
                fill=(
                    int(92 - 35 * blend),
                    int(169 - 48 * blend),
                    int(213 - 61 * blend),
                ),
            )
        draw.ellipse(
            (*_pont(228, 28, width, height), *_pont(273, 73, width, height)),
            fill=(255, 220, 133),
        )
        draw.polygon(
            [_pont(x, y, width, height) for x, y in (
                (0, 177), (66, 103), (132, 181), (202, 91), (320, 177),
                (320, 240), (0, 240),
            )],
            fill=(70 + index * 16, 111 + index * 12, 116),
        )
        draw.polygon(
            [_pont(x, y, width, height) for x, y in (
                (0, 204), (100, 155), (187, 211), (260, 158), (320, 198),
                (320, 240), (0, 240),
            )],
            fill=(57, 125 + index * 14, 91),
        )
        image.save(path, "JPEG", quality=90)


@pytest.fixture
def movie_app(qt_app, tmp_path):
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fotokat,
    )

def _elem(window, name):
    item = window.findChild(QObject, name)
    if item is not None:
        return item
    pending = [window.contentItem()]
    while pending:
        current = pending.pop()
        if current.objectName() == name:
            return current
        pending.extend(current.childItems())
    raise AssertionError(f"{name} nem található a főablak QML-fájában")


def _kattints(qt_app, item):
    assert item.property("visible") is True, f"{item.objectName()} nem látható"
    assert item.width() > 0 and item.height() > 0
    point = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        item.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(point.x()), round(point.y())),
    )
    qt_app.processEvents()


def _varj(qt_app, condition, seconds=10.0):
    return var_feltetelre(qt_app, condition, seconds)


def _movie_menu_kattintas(window, qt_app):
    menu_bar = window.property("menuBar")
    create_menu = _megnyit(menu_bar, qt_app, "&Create")
    host_window = menu_bar.window()
    movie_menu = host_window.findChild(QObject, "menuCreateMovieMenu")
    assert movie_menu is not None

    # A Movie almenü sorát is valódi kattintás nyitja meg.
    pending = [create_menu.property("contentItem")]
    submenu_row = None
    while pending:
        parent = pending.pop()
        for child in parent.childItems():
            if (
                "MenuItem" in child.metaObject().className()
                and child.property("text") == movie_menu.property("title")
            ):
                submenu_row = child
                break
            pending.append(child)
        if submenu_row is not None:
            break
    assert submenu_row is not None, "a Movie almenü sora nem található"
    _kattints(qt_app, submenu_row)
    assert _varj(qt_app, lambda: movie_menu.property("opened") is True)
    _kattints(qt_app, host_window.findChild(QQuickItem, "menuCreateMovie"))
    return host_window


def _merd_a_respack_elrendezest(window):
    panel = _elem(window, "movieDialog")
    left = _elem(window, "movieLeftPanel")
    tabs = _elem(window, "movieTabs")
    rewind = _elem(window, "rewind")
    preview = _elem(window, "moviePreviewPanel")
    viewport = _elem(window, "moviePreviewViewport")
    filmstrip = _elem(window, "movieFilmstrip")

    assert isinstance(panel, QQuickItem), (
        "a Mozgófilmkészítő még külön Dialog, nem főablakba ágyazott panel"
    )
    assert panel.window() == window, "a Mozgófilmkészítő külön ablakban nyílt meg"
    assert left.parentItem() == panel
    assert preview.parentItem() == panel
    assert filmstrip.parentItem() == panel

    scale = min(1.0, panel.width() / 800.0, panel.height() / 534.0)

    def rect(item):
        top_left = item.mapToItem(panel, QPointF(0, 0))
        return (
            top_left.x(),
            top_left.y(),
            item.width(),
            item.height(),
        )

    left_rect = rect(left)
    tabs_rect = rect(tabs)
    rewind_rect = rect(rewind)
    preview_rect = rect(preview)
    viewport_rect = rect(viewport)
    filmstrip_rect = rect(filmstrip)
    for actual, expected, label in (
        (left_rect[0], 4 * scale, "bal hasáb x"),
        (left_rect[1], 20 * scale, "bal hasáb y"),
        (left_rect[2], 276 * scale, "bal hasáb szélesség"),
        (left_rect[3], 389 * scale, "bal hasáb magasság"),
        (tabs_rect[0], 5 * scale, "fülsáv x"),
        (tabs_rect[1], 21 * scale, "fülsáv y"),
        (tabs_rect[2], 274 * scale, "fülsáv szélesség"),
        (tabs_rect[3], 25 * scale, "fülsáv magasság"),
        (preview_rect[0], 287 * scale, "előnézet x"),
        (preview_rect[1], 11 * scale, "előnézet y"),
        (viewport_rect[0], 287 * scale, "előnézeti képkocka x"),
        (viewport_rect[1], 11 * scale, "előnézeti képkocka y"),
        (filmstrip_rect[0], 330 * scale, "filmcsík x"),
        (filmstrip_rect[1], panel.height() - 90 * scale, "filmcsík y"),
        (filmstrip_rect[2], panel.width() - 330 * scale, "filmcsík szélesség"),
        (filmstrip_rect[3], 72 * scale, "filmcsík magasság"),
    ):
        assert abs(actual - expected) <= 3, (
            f"{label}: mért={actual:.1f}, respack alapján={expected:.1f}"
        )

    # A 2.7 szakasz szerint a tervvászon-méretek kiinduló arányok: az előnézet
    # a főablak magasságát követi, nem rögzített 361 egység.
    assert viewport_rect[3] >= 361 * scale - 3, (
        f"az előnézeti képterület alacsonyabb a tervvászonnál: {viewport_rect[3]:.1f}"
    )
    assert preview_rect[0] > left_rect[0] + left_rect[2]
    assert rewind_rect[0] >= left_rect[0] - 3
    assert rewind_rect[0] + rewind_rect[2] <= left_rect[0] + left_rect[2] + 3, (
        "a visszaállító vezérlő kilóg a bal hasábból"
    )
    assert viewport_rect[2] >= 507 * scale - 3
    assert filmstrip_rect[1] > preview_rect[1]
    assert filmstrip_rect[1] + filmstrip_rect[3] <= panel.height() + 3


def test_a_mozgofilmkeszito_foablaklap_es_minden_bezarasi_utja(
    movie_app, qt_app
):
    window, controller, _engine = movie_app
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(Path(str(controller.watchedFolders[0])) / _MAPPA))
    assert _varj(qt_app, lambda: len(controller.photos.photos) == 2)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _movie_menu_kattintas(window, qt_app)
    assert _varj(qt_app, lambda: _elem(window, "movieDialog").property("visible"))
    window.resize(1087, 730)
    qt_app.processEvents()
    tab = _elem(window, "documentTab0")
    assert tab.property("title") == "Movie Maker"
    assert _elem(window, "documentTab0Close").property("visible") is True
    assert _elem(window, "movieTabMotion")
    assert _elem(window, "movieTabSlide")
    clips_tab = _elem(window, "movieTabClips")
    movie = _elem(window, "movieDialog")
    expected_clips_label = f"Clips ({len(movie.property('movieClipSources'))})"
    assert clips_tab.property("text") == expected_clips_label, (
        "a Klipek fül nem az eredeti Picasa darabszámos feliratát mutatja: "
        f"{clips_tab.property('text')!r} != {expected_clips_label!r}"
    )
    fo_vezerlok = [
        _elem(window, "audio_label"),
        _elem(window, "movieAudioOptionBox"),
        _elem(window, "movieTransitionBox"),
        _elem(window, "movieSeconds"),
        _elem(window, "movieOverlapSlider"),
        _elem(window, "movieHeightBox"),
        _elem(window, "movieShowCaptions"),
        _elem(window, "movieCropToFit"),
    ]
    y_poziciok = [
        item.mapToItem(movie, QPointF(0, 0)).y() for item in fo_vezerlok
    ]
    assert all(item.property("visible") for item in fo_vezerlok), (
        "a Mozgófilm fül fő vezérlői nem látszanak a görgetősáv elmozdítása nélkül"
    )
    assert y_poziciok == sorted(y_poziciok), (
        "a Mozgófilm fül vezérlősorrendje eltér a Picasa képi referenciájától: "
        f"{y_poziciok}"
    )
    motion_scroll = _elem(window, "movieTabPanelMotion")
    assert motion_scroll.property("contentItem").property("contentY") == 0
    for item in fo_vezerlok:
        top = item.mapToItem(motion_scroll, QPointF(0, 0)).y()
        bottom = top + item.height()
        assert top >= -3 and bottom <= motion_scroll.height() + 3, (
            f"{item.objectName()} nem látszik teljesen a görgetés nélküli "
            f"Mozgófilm fülön: y={top:.1f}…{bottom:.1f}, "
            f"nézőtér={motion_scroll.height():.1f}"
        )
    assert _elem(window, "video_control_bar2/controlbar")

    base_height = window.height()
    for delta in (-5, 0, 5):
        window.resize(1087, base_height + delta)
        qt_app.processEvents()
        assert _varj(
            qt_app,
            lambda: _elem(window, "movieDialog").height() > 0,
        )
        _merd_a_respack_elrendezest(window)
        if delta == 0:
            output = Path(__file__).resolve().parents[3] / ".bt"
            output.mkdir(parents=True, exist_ok=True)
            rendered = window.grabWindow()
            assert not rendered.isNull(), "a Mozgófilmkészítő képernyőképe üres"
            assert rendered.save(str(output / "movie-maker-5264.png"))

    _kattints(qt_app, _elem(window, "movieCancelButton"))
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "library",
    ), "a Bezárás nem tért vissza a Könyvtár lapra"

    _movie_menu_kattintas(window, qt_app)
    _kattints(qt_app, _elem(window, "movieTabClips"))
    _kattints(qt_app, _elem(window, "movieGetMoreClipsButton"))
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "library"
        and window.property("backToMovieMakerPrompted") is True,
    ), "a Továbbiak nem nyitotta meg a klipgyűjtő könyvtárnézetet"
    return_button = _elem(window, "traySingleActionReturn")
    assert return_button.property("text") == "Back to Movie Maker"
    _kattints(qt_app, return_button)
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "movieMaker"
        and window.property("backToMovieMakerPrompted") is False,
    ), "a Back to Movie Maker nem tért vissza a filmkészítőlapra"

    _movie_menu_kattintas(window, qt_app)
    _kattints(qt_app, _elem(window, "documentTab0Close"))
    roots = _engine.rootObjects()
    assert len(roots) == 1, "a lap X-e bezárta a főablakot"
    window = roots[0]
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "library",
    ), "a lap X-e nem tért vissza a Könyvtár lapra"

    _movie_menu_kattintas(window, qt_app)
    QTest.keyClick(window, Qt.Key.Key_Escape)
    qt_app.processEvents()
    window = _engine.rootObjects()[0]
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "library",
    ), "az Escape nem tért vissza a Könyvtár lapra"

    translator = QTranslator(qt_app)
    qm_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "picasapy"
        / "app"
        / "i18n"
        / "picasapy_hu.qm"
    )
    assert translator.load(str(qm_path)), "a magyar .qm nem tölthető be"
    assert qt_app.installTranslator(translator)
    _engine.retranslate()
    window.openMovieMakerTab()
    _elem(window, "movieTabs").setProperty("currentIndex", 0)
    assert _varj(
        qt_app,
        lambda: window.property("activeDocumentTabId") == "movieMaker",
    )
    assert _elem(window, "documentTab0").property("title") == "Mozgófilmkészítés"
    assert _elem(window, "movieCancelButton").property("text") == "Bezárás"
    assert _elem(window, "movieAudioPathLabel").property("text") == "Egyik sem"
    assert (
        _elem(window, "movieCropToFit").property("text")
        == "Teljes képkockás fotó körbevágása"
    )
    movie_qml = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "picasapy"
        / "app"
        / "qml"
        / "PicasaPy"
        / "CreateDialogs.qml"
    ).read_text(encoding="utf-8")
    assert movie_qml.count("font.pixelSize: Theme.fontSize - 4") == 2, (
        "a magyar Mozgófilm-fül keskeny jelölőfeliratai betűméretének "
        "forrás-őre eltűnt"
    )
    title_tab = _elem(window, "documentTab0")
    title_label = _elem(window, "documentTab0Label")
    assert title_tab.width() >= title_label.property("implicitWidth") + 28, (
        "a magyar Mozgófilmkészítés fül címe a bezáró X előtt ellipszissel végződik"
    )
    window.resize(1087, 730)
    qt_app.processEvents()
    dialog = _elem(window, "movieDialog")
    image = _elem(window, "moviePreviewTransitionImage")
    assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
    assert _varj(
        qt_app,
        lambda: int(dialog.property("previewDisplayedGeneration"))
        >= int(dialog.property("previewLatestRequestGeneration"))
        and float(image.property("paintedWidth")) > 0,
    ), "a magyar képernyőképhez nem készült el az előnézeti kép"
    localized = window.grabWindow()
    assert not localized.isNull()
    output = Path(__file__).resolve().parents[3] / ".bt"
    output.mkdir(parents=True, exist_ok=True)
    assert localized.save(str(output / "movie-maker-5264.png"))


def _szin(item):
    return QColor(item.property("color")).name()


def _keret(item):
    szin = QQmlProperty(item, "border.color").read()
    return QColor(szin).name(), int(QQmlProperty(item, "border.width").read())


def _szovegek(item):
    """A fa összes szövegét adja, a filmcsík bélyegképeinek feliratait is."""
    szovegek = []
    pending = [item]
    while pending:
        current = pending.pop()
        text = current.property("text")
        if isinstance(text, str):
            szovegek.append(text)
        pending.extend(current.childItems())
    return szovegek


def _leszarmazottak(item, nev):
    talalt = []
    pending = [item]
    while pending:
        current = pending.pop()
        if current.objectName() == nev:
            talalt.append(current)
        pending.extend(current.childItems())
    return talalt


def _ablak_rect(item):
    """Az elem téglalapja a főablak koordinátáiban (a képernyőképével egyezően)."""
    top_left = item.mapToScene(QPointF(0, 0))
    return top_left.x(), top_left.y(), item.width(), item.height()


def _pixel(kep, x, y):
    return kep.pixelColor(round(x), round(y)).name()


def _szin_kozel(szin, varhato, tures=4):
    a = QColor(szin)
    b = QColor(varhato)
    return all(
        abs(a.getRgb()[i] - b.getRgb()[i]) <= tures for i in range(3)
    )


def _merd_a_javitott_elemeket(window, kep):
    """A mérce (Windows HU Mozgófilm lap) öt pontja, rendre.

    A `kep` a főablak megjelenített képe: a letterbox, a fülek és a
    filmcsík színeit a képpontokból olvassuk ki, nem a számolt geometriából.
    """
    panel = _elem(window, "movieDialog")
    scale = min(1.0, panel.width() / 800.0, panel.height() / 534.0)

    def rect(item):
        top_left = item.mapToItem(panel, QPointF(0, 0))
        return top_left.x(), top_left.y(), item.width(), item.height()

    viewport = _elem(window, "moviePreviewViewport")
    viewport_bg = _elem(window, "moviePreviewViewportBg")
    frame = _elem(window, "moviePreviewFrameBox")
    preview = _elem(window, "moviePreviewPanel")
    bar = _elem(window, "video_control_bar2/controlbar")
    filmstrip = _elem(window, "movieFilmstrip")
    info = _elem(window, "makemoviepanel/infotext")

    # 1. Az előnézet szürke panel, benne középen a fekete, képarányos keret.
    assert _szin(viewport_bg) == _SZURKE_ELOFOGULAT, (
        f"az előnézet háttere {_szin(viewport_bg)}, nem a szürke panel"
    )
    assert _szin(frame) == _FEKETE, f"az előnézeti keret {_szin(frame)}, nem fekete"
    fx, fy, fw, fh = rect(frame)
    vx, vy, vw, vh = rect(viewport)
    assert abs((fx + fw / 2) - (vx + vw / 2)) <= 3, "a fekete keret vízszintesen nincs középen"
    assert abs((fy + fh / 2) - (vy + vh / 2)) <= 3, "a fekete keret függőlegesen nincs középen"
    assert abs(fw / fh - panel.property("previewAspectRatio")) <= 0.01, (
        "a fekete keret nem a kimeneti méret képarányát követi"
    )
    # Alapból valódi méret (1:1): a spec szerint a `makemovie1to1` alapja 1.
    # Ilyenkor a fekete keret a kimeneti méret (640 × 480), nem a panelhez igazított.
    assert panel.property("previewActualSizeEnabled") is True, (
        "az 1:1 nincs alapból bekapcsolva (spec: makemovie1to1 alapja 1)"
    )
    assert _elem(window, "video_control_bar2/1to1").property("checked") is True, (
        "az 1:1 gomb nem tükrözi a valódi méretet"
    )
    # A bekapcsolt 1:1 gomb a mércén szürke: semleges keret, felül belső árnyék.
    gomb = _elem(window, "video_control_bar2/1to1")
    gx, gy, gw, _gh = _ablak_rect(gomb)
    assert _keret(gomb.property("background")) == (_SZURKE_KERET, 1), (
        f"a bekapcsolt 1:1 keret {_keret(gomb.property('background'))}, "
        "a mércén szürke #bbbbbb"
    )
    assert _szin_kozel(_pixel(kep, gx + gw / 2, gy), _SZURKE_KERET, tures=6), (
        "a bekapcsolt 1:1 gomb felső szegélye nem szürke a képernyőképen"
    )
    assert QColor(_pixel(kep, gx + gw / 2, gy + 1)).red() < 190, (
        "a bekapcsolt 1:1 gombnak nincs felső belső árnyéka, mint a mércén"
    )
    assert (round(fw), round(fh)) == (640, 480), (
        f"az előnézeti keret {fw:.0f} × {fh:.0f}, nem a 640 × 480-as kimeneti méret"
    )
    # Letterbox, képpontról: az álló fotó két oldalán fekete sáv, középen kép.
    # A szürke panel a keret körül látszik (a mércén is így van).
    kx, ky, kw, kh = _ablak_rect(frame)
    vkx, _vky, _vkw, _vkh = _ablak_rect(viewport)
    kozep_y = ky + kh / 2
    assert _pixel(kep, kx + 6, kozep_y) == _FEKETE, (
        "az álló fotó bal oldalán nincs fekete letterbox-sáv"
    )
    assert _pixel(kep, kx + kw / 2, kozep_y) != _FEKETE, (
        "a fekete keret közepén nincs fotó"
    )
    assert _pixel(kep, vkx + 2, kozep_y) == _SZURKE_ELOFOGULAT, (
        "a fekete keret mellett nem a szürke előnézeti panel látszik"
    )
    assert _pixel(kep, kx - 3, kozep_y) == _SZURKE_ELOFOGULAT, (
        "a 1:1 keret közvetlenül mellett nincs szürke panelmargó"
    )

    # 2. A lejátszósor a panel alján, teljes szélességben, a filmcsík felett.
    px, _py, pw, _ph = rect(preview)
    bx, by, bw, bh = rect(bar)
    sx, sy, _sw, sh = rect(filmstrip)
    assert abs(bx - px) <= 3 and abs(bw - pw) <= 3, "a lejátszósor nem teljes szélességben fut"
    assert vy + vh <= by + 3, "a lejátszósor nem a képkocka alatt van"
    assert abs((by + bh) - sy) <= 6 * scale + 3, "a lejátszósor nem a filmcsík fölött van"

    # 3. A filmcsík bélyegképei feliratok nélkül, alatta az állapotsor.
    feliratok = [szoveg for szoveg in _szovegek(filmstrip) if szoveg.endswith(".jpg")]
    assert not feliratok, f"a filmcsík bélyegképei még feliratosak: {feliratok}"
    ix, iy, iw, _ih = rect(info)
    assert iy >= sy + sh - 3, "az állapotsor nem a filmcsík alatt van"
    assert abs((ix + iw / 2) - (px + pw / 2)) <= 3, "az állapotsor nem középre igazodik"
    assert "fotok > a_elso.jpg" in info.property("text"), (
        f"az állapotsor nem a mappa és a fájlnév szerint áll: {info.property('text')!r}"
    )
    kivalasztott = [
        _keret(keret)
        for keret in _leszarmazottak(filmstrip, "movieFilmstripFrame")
    ]
    assert (_KIVALASZTOTT_KEP_KERET, 2) in kivalasztott, (
        f"nincs kék kijelölő keret a filmcsíkon: {kivalasztott}"
    )
    # A bélyegek a filmcsík vízszintes közepén állnak (a bal oldali gombsor
    # nélkül), a + és az X gomb pedig bal oldalt, egymás alatt.
    belyegek = [
        _ablak_rect(keret)
        for keret in _leszarmazottak(filmstrip, "movieFilmstripFrame")
    ]
    bal = min(x for x, _y, _w, _h in belyegek)
    jobb = max(x + w for x, _y, w, _h in belyegek)
    sav_kx, _sav_ky, sav_kw, _sav_kh = _ablak_rect(filmstrip)
    assert abs((bal + jobb) / 2 - (sav_kx + sav_kw / 2)) <= 3, (
        "a bélyegek nincsenek a filmcsík közepén"
    )
    for keret in _leszarmazottak(filmstrip, "movieFilmstripFrame"):
        _kx, _ky, belyeg_w, belyeg_h = _ablak_rect(keret)
        assert (round(belyeg_w), round(belyeg_h)) == (_BELYEG_MERET, _BELYEG_MERET), (
            f"a bélyegkép {belyeg_w:.0f} × {belyeg_h:.0f}, a mércén 50 × 50"
        )
    # A bélyegek közti rés a mércén 3 képpont: a két klipes teszt két bélyeget ad.
    belyeg_x = sorted(
        _ablak_rect(keret)[0]
        for keret in _leszarmazottak(filmstrip, "movieFilmstripFrame")
    )
    assert len(belyeg_x) >= 2, "a rés méréséhez legalább két bélyeg kell"
    for elso, masodik in zip(belyeg_x, belyeg_x[1:], strict=False):
        res = masodik - elso - _BELYEG_MERET
        assert abs(res - _BELYEG_RES) <= 1, (
            f"a bélyegek közti rés {res:.1f} képpont, a mércén {_BELYEG_RES}"
        )
    hozzaad = _elem(window, "movieFilmstripAddButton")
    torol = _elem(window, "movieFilmstripDeleteButton")
    hx, hy, _hw, hh = _ablak_rect(hozzaad)
    tx, ty, _tw, _th = _ablak_rect(torol)
    assert abs(hx - tx) <= 1 and ty >= hy + hh - 1, (
        "a + és az X gomb nem egymás alatt áll"
    )
    assert hx + _hw <= sav_kx + 1, "a + és az X gomb nem a filmcsík bal oldalán van"
    assert _szin(torol.property("contentItem")) == _PIROS_X, (
        "az X gomb jele nem piros"
    )

    # 4. A bal hasáb lekerekített, kék szegélyű doboz, kék fülekkel.
    left_frame = _elem(window, "movieLeftPanelFrame")
    assert float(left_frame.property("radius")) > 0, "a bal hasáb nem lekerekített"
    assert _keret(left_frame) == (_KEK_SZEGELY, 2), (
        f"a bal hasáb szegélye {_keret(left_frame)}, nem a 2 képpontos kék szegély"
    )
    assert _szin(left_frame) == _HASAB_TOLTES, (
        f"a bal hasáb töltése {_szin(left_frame)}, nem a mért világos szürke"
    )
    kijelolt = _elem(window, "movieTabMotion")
    nem_kijelolt = _elem(window, "movieTabSlide")
    assert kijelolt.property("checked") is True and nem_kijelolt.property("checked") is False
    kx, ky, kw, kh = _ablak_rect(kijelolt)
    assert _pixel(kep, kx + kw / 2, ky) == _KEK_FUL, "a fül felső szegélye nem kék"
    # A felirat középen áll, ezért a fül jobb szélének testszínét mérjük.
    assert _pixel(kep, kx + kw - 6, ky + kh / 2) == _FUL_KIVALASZTOTT, (
        "a kijelölt fül nem a világos fülszín"
    )
    nx, ny, nw, nh = _ablak_rect(nem_kijelolt)
    assert _szin_kozel(_pixel(kep, nx + nw - 6, ny + nh / 2), _FUL_ALAP), (
        "a nem kijelölt fül nem a kékes fülszín"
    )

    # 5. A feliratok egy sorban, középen; a csúszka rövidebb és középen áll.
    motion = _elem(window, "movieTabPanelMotion")
    mx, _my, mw, _mh = rect(motion)
    for label_name, value_name, slider_name in (
        ("movieSecondsLabel", "movieSecondsValueLabel", "movieSeconds"),
        ("movieOverlapLabel", "movieOverlapValueLabel", "movieOverlapSlider"),
    ):
        label = _elem(window, label_name)
        value = _elem(window, value_name)
        slider = _elem(window, slider_name)
        lx, ly, lw, _lh = rect(label)
        vx2, vy2, vw2, _vh2 = rect(value)
        assert abs(ly - vy2) <= 2, f"{label_name} és értéke nincs egy sorban"
        csoport_kozep = (min(lx, vx2) + max(lx + lw, vx2 + vw2)) / 2
        assert abs(csoport_kozep - (mx + mw / 2)) <= 3, (
            f"{label_name} csoportja nincs középen"
        )
        assert slider.width() <= 0.6 * mw, f"{slider_name} nem rövidebb a sornál"
        sx2, _sy2, sw2, _sh2 = rect(slider)
        assert abs((sx2 + sw2 / 2) - (mx + mw / 2)) <= 3, f"{slider_name} nincs középen"

    audio_label = _elem(window, "movieAudioPathLabel")
    assert _szin(audio_label) == _ZOLD, (
        f"a hangsáv nélküli „Egyik sem” {_szin(audio_label)}, nem zöld"
    )
    assert _elem(window, "movieRemoveAudioButton").property("enabled") is False, (
        "a Törlés gomb hangsáv nélkül nincs letiltva"
    )
    assert _elem(window, "movieAudioOptionBox").property("enabled") is False, (
        "az Opciók lista hangsáv nélkül nincs letiltva"
    )
    # 2. A letiltott Törlés felirata szürke, nem a sötét gombfelirat.
    torles = _elem(window, "movieRemoveAudioButton")
    assert _szin(torles.property("contentItem")) == _LETILTOTT_SZOVEG, (
        f"a letiltott Törlés felirata {_szin(torles.property('contentItem'))}, "
        "nem szürke"
    )
    # Az Opciók lista letiltott felirata a mérce szerint #b1b1b1.
    opciok = _elem(window, "movieAudioOptionBox")
    assert _szin(opciok.property("contentItem")) == _OPCIO_LETILTOTT, (
        f"az Opciók letiltott felirata {_szin(opciok.property('contentItem'))}, "
        "nem #b1b1b1"
    )


def test_a_mozgofilm_elemei_a_mercehez_igazodnak(movie_app, qt_app):
    window, controller, _engine = movie_app
    # A korábbi teszt magyar fordítója a munkamenet-szintű qt_app-on maradt.
    for korabbi in qt_app.findChildren(QTranslator):
        qt_app.removeTranslator(korabbi)
    _engine.retranslate()
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(Path(str(controller.watchedFolders[0])) / _MAPPA))
    assert _varj(qt_app, lambda: len(controller.photos.photos) == 2)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()

    _movie_menu_kattintas(window, qt_app)
    assert _varj(qt_app, lambda: _elem(window, "movieDialog").property("visible"))
    window.resize(1087, 730)
    qt_app.processEvents()
    # A filmcsík kijelölése a klipek listájának aktuális eleme (kattintás szerint).
    _elem(window, "movieClipList").setProperty("currentIndex", 0)
    qt_app.processEvents()

    translator = QTranslator(qt_app)
    qm_path = (
        Path(__file__).resolve().parents[3]
        / "src"
        / "picasapy"
        / "app"
        / "i18n"
        / "picasapy_hu.qm"
    )
    assert translator.load(str(qm_path)), "a magyar .qm nem tölthető be"
    assert qt_app.installTranslator(translator)
    _engine.retranslate()
    assert _varj(
        qt_app,
        lambda: _elem(window, "movieAudioPathLabel").property("text") == "Egyik sem",
    )
    assert _elem(window, "movieSecondsLabel").property("text") == "Dia időtartama:"
    assert _elem(window, "movieSecondsValueLabel").property("text") == "4.0 mp"

    dialog = _elem(window, "movieDialog")
    image = _elem(window, "moviePreviewTransitionImage")
    assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
    assert _varj(
        qt_app,
        lambda: int(dialog.property("previewDisplayedGeneration"))
        >= int(dialog.property("previewLatestRequestGeneration"))
        and float(image.property("paintedWidth")) > 0,
    ), "a magyar képernyőképhez nem készült el az előnézeti kép"
    rendered = window.grabWindow()
    assert not rendered.isNull()
    output = Path(__file__).resolve().parents[3] / ".bt"
    output.mkdir(parents=True, exist_ok=True)
    assert rendered.save(str(output / "movie-maker-5264-hu-1087x730.png"))
    assert rendered.save(str(output / "movie-maker-5288.png"))
    # A pixelellenőrzések a mentett, magyar képernyőképen futnak.
    _merd_a_javitott_elemeket(window, rendered)
    _negyzetes_fotonal_nincs_fekete_csik(window, qt_app)


def _negyzetes_fotonal_nincs_fekete_csik(window, qt_app):
    """A 4:3-as fotó kitölti a keretet: a jobb szélén nem marad fekete csík.

    Az első klip álló, ezért a letterbox-sávok a teszt másik részében látszanak.
    Ez a fotó a kimeneti képaránnyal egyezik, tehát a keret szélén kép van.
    """
    dialog = _elem(window, "movieDialog")
    image = _elem(window, "moviePreviewTransitionImage")
    # A QML-függvény argumentuma típusnélküli (QVariant), ezért nem int.
    assert QMetaObject.invokeMethod(
        dialog, "selectMovieFilmstripItem", Q_ARG("QVariant", 1)
    )
    assert QMetaObject.invokeMethod(dialog, "requestPreviewFrame")
    assert _varj(
        qt_app,
        lambda: int(dialog.property("previewDisplayedGeneration"))
        >= int(dialog.property("previewLatestRequestGeneration"))
        and float(image.property("paintedWidth")) > 0,
    ), "a 4:3-as klip előnézeti képe nem készült el"
    kep = window.grabWindow()
    kx, ky, kw, kh = _ablak_rect(_elem(window, "moviePreviewFrameBox"))
    kozep_y = ky + kh / 2
    assert _pixel(kep, kx + 1, kozep_y) != _FEKETE, (
        "a 4:3-as fotó bal szélén fekete csík van"
    )
    assert _pixel(kep, kx + kw - 1, kozep_y) != _FEKETE, (
        "a 4:3-as fotó jobb szélén fekete csík van"
    )


def _nyisd_a_mozgofilmkeszitot(window, controller, qt_app, engine):
    """A két fotós mappát kijelöli, és a Create > Movie menüből megnyitja."""
    # A munkamenet-szintű qt_app a korábbi teszt magyar fordítóját is megtartja;
    # a `&Create` menüút angol feliratot vár.
    for korabbi in qt_app.findChildren(QTranslator):
        qt_app.removeTranslator(korabbi)
    engine.retranslate()
    window.show()
    window.requestActivate()
    qt_app.processEvents()
    controller.selectFolder(str(Path(str(controller.watchedFolders[0])) / _MAPPA))
    assert _varj(qt_app, lambda: len(controller.photos.photos) == 2)
    window.setProperty("selectedIndexes", [0, 1])
    window.setProperty("selectedIndex", 0)
    qt_app.processEvents()
    _movie_menu_kattintas(window, qt_app)
    assert _varj(qt_app, lambda: _elem(window, "movieDialog").property("visible"))
    window.resize(1087, 730)
    qt_app.processEvents()
    return _elem(window, "movieDialog")


@pytest.fixture
def movie_app_kikapcsolt_1to1(qt_app, tmp_path):
    """A korábbi indításban kikapcsolt 1:1: az INI-ben szövegként `false` áll."""
    beallitas = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    beallitas.setValue("makemovie1to1", "false")
    beallitas.sync()
    yield from _build_qml_app(
        qt_app,
        tmp_path,
        kepeket_keszit=_keszits_fotokat,
    )


def test_a_1to1_valasztas_mentodik_es_visszakapcsolhato(movie_app, qt_app, tmp_path):
    window, controller, engine = movie_app
    # A spec szerint a `Preferences\makemovie1to1` alapja 1 (bekapcsolva).
    assert controller.moviePreference("actualSize") is True
    _nyisd_a_mozgofilmkeszitot(window, controller, qt_app, engine)
    gomb = _elem(window, "video_control_bar2/1to1")

    _kattints(qt_app, gomb)
    assert gomb.property("checked") is False
    assert controller.moviePreference("actualSize") is False
    # A lemezen a spec szerinti kulcs áll, a kikapcsolt érték szövegként.
    controller._get_settings().sync()
    mentett = QSettings(str(tmp_path / "settings.ini"), QSettings.Format.IniFormat)
    assert str(mentett.value("makemovie1to1")).lower() == "false"

    _kattints(qt_app, gomb)
    assert gomb.property("checked") is True
    assert controller.moviePreference("actualSize") is True


def test_a_mentett_kikapcsolt_1to1_indulaskor_kikapcsolva_nyilik(
    movie_app_kikapcsolt_1to1, qt_app
):
    window, controller, engine = movie_app_kikapcsolt_1to1
    # A szövegként olvasott `false` ne ébredjen vissza igazra (bool("false") == True).
    assert controller.moviePreference("actualSize") is False
    dialog = _nyisd_a_mozgofilmkeszitot(window, controller, qt_app, engine)
    gomb = _elem(window, "video_control_bar2/1to1")
    assert dialog.property("previewActualSizeEnabled") is False
    assert gomb.property("checked") is False
    # Kikapcsolva nincs belső árnyék a gombon.
    arnyek = _leszarmazottak(gomb, "picasaButtonCheckedShadeTop")
    assert arnyek and all(item.property("visible") is False for item in arnyek)
