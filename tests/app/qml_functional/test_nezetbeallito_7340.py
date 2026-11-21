"""#7340: a View options gomb és a Nézet ▸ Mappanézet menü paritása."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from PySide6.QtCore import QPoint, QPointF, QObject, Qt
from PySide6.QtGui import QColor
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from tests.app.qml_functional._nezet_menu_5150_helpers import (
    almenu_nyit,
    nezet_app_epitese,
)
from tests.support.varakozas import var_feltetelre


@pytest.fixture
def nezet_app(qt_app, tmp_path):
    yield from nezet_app_epitese(qt_app, tmp_path)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _menu_sor(menu, index: int):
    kifejezes = QQmlExpression(qmlContext(menu), menu, f"itemAt({index})")
    elem, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert elem is not None, f"a menü {index}. tétele hiányzik"
    return elem


def _sorok(menu) -> list[tuple[str, bool]]:
    sorok = []
    for index in range(int(menu.property("count"))):
        elem = _menu_sor(menu, index)
        tipus = elem.metaObject().className()
        kifejezes = QQmlExpression(
            qmlContext(menu),
            menu,
            "(function () {"
            f"  var elem = itemAt({index});"
            "  return elem.subMenu ? elem.subMenu.objectName : elem.objectName;"
            "})()",
        )
        nev, hiba = kifejezes.evaluate()
        assert not hiba, kifejezes.error()
        nev = str(nev if isinstance(nev, str) else nev.toString())
        sorok.append((nev, "MenuSeparator" in tipus))
    return sorok


def _kattints(elem, qt_app) -> None:
    assert elem is not None and elem.width() > 0 and elem.height() > 0
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2))
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(pont.x()), round(pont.y())),
    )
    qt_app.processEvents()


def _varj(qt_app, feltetel) -> bool:
    return var_feltetelre(qt_app, feltetel, 10.0)


def _kirajzolt_jelolo_szin(menu_item) -> QColor:
    """A 14×14-es pipamezőt olvassa, nem a gépenként változó feliratsort."""
    jelolo = menu_item.property("indicator")
    assert jelolo is not None, f"{menu_item.objectName()} pipája hiányzik"
    vart_szin = QColor(jelolo.property("pipaSzin"))
    ablak = menu_item.window()
    kep = ablak.grabWindow()
    assert not kep.isNull(), "a megnyitott menü nem rajzolódott ki"
    dpr = kep.devicePixelRatio()
    bal_felso = jelolo.mapToScene(QPointF(0, 0))
    legjobb = 1000
    for dx in range(round(jelolo.width())):
        for dy in range(round(jelolo.height())):
            x = round((bal_felso.x() + dx + 0.5) * dpr)
            y = round((bal_felso.y() + dy + 0.5) * dpr)
            if not (0 <= x < kep.width() and 0 <= y < kep.height()):
                continue
            pixel = kep.pixelColor(x, y)
            tav = (
                abs(pixel.red() - vart_szin.red())
                + abs(pixel.green() - vart_szin.green())
                + abs(pixel.blue() - vart_szin.blue())
            )
            legjobb = min(legjobb, tav)
    assert legjobb < 120, (
        f"a {menu_item.objectName()} kipipált jelölője nem látszik a renderben "
        f"(a várt színhez mért legkisebb eltérés: {legjobb})"
    )
    return vart_szin


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_a_toolbar_nyil_a_sajat_14_rekordos_legordulot_nyitja(
    nezet_app, qt_app, magassag_eltolas
):
    window, _controller, _engine = nezet_app
    alapmagassag = window.height()
    window.setHeight(alapmagassag + magassag_eltolas)
    assert _varj(
        qt_app, lambda: window.height() == alapmagassag + magassag_eltolas
    ), f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
    gomb = _gyerek(window, "toolbarFolderViewPopupButton")
    _kattints(gomb, qt_app)

    menu = _gyerek(window, "toolbarFolderListMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True), (
        "a ▾ gomb nem nyitotta meg a saját legördülőjét"
    )
    assert _gyerek(window, "menuViewFolderView").property("opened") is False
    assert _sorok(menu) == [
        ("toolbarFolderListMenuSortByDate", False),
        ("toolbarFolderListMenuSortByChanged", False),
        ("toolbarFolderListMenuSortBySize", False),
        ("toolbarFolderListMenuSortByName", False),
        ("toolbarFolderListMenuSortReverse", False),
        ("", True),
        ("toolbarFolderListMenuSortPeopleByName", False),
        ("toolbarFolderListMenuSortPeopleByCount", False),
        ("toolbarFolderListMenuSortPeopleByTopList", False),
        ("", True),
        ("toolbarFolderListMenuShortcuts", False),
        ("", True),
        ("toolbarFolderListMenuShowThumbnails", False),
        ("toolbarFolderListMenuSimplifiedTree", False),
    ]
    shortcuts = _gyerek(window, "toolbarFolderListMenuShortcuts")
    assert _sorok(shortcuts) == [
        ("toolbarFolderListMenuDesktop", False),
        ("toolbarFolderListMenuMyDocuments", False),
        ("toolbarFolderListMenuMyPictures", False),
        ("", True),
        ("toolbarFolderListMenuMyComputer", False),
    ]
    menu.close()
    qt_app.processEvents()

    menubar_menu = almenu_nyit(window, qt_app, ("menuViewFolderView",))
    assert _sorok(menubar_menu) == [
        ("menuViewFlatFolderView", False),
        ("menuViewTreeView", False),
        ("", True),
        ("menuViewSortByDate", False),
        ("menuViewSortByRecent", False),
        ("menuViewSortBySize", False),
        ("menuViewSortByName", False),
        ("menuViewSortReverse", False),
        ("", True),
        ("menuViewFolderViewShortcuts", False),
        ("", True),
        ("menuViewAlbumThumbnails", False),
        ("menuViewSimplifiedTreeView", False),
    ]
    shortcuts = _gyerek(window, "menuViewFolderViewShortcuts")
    assert _sorok(shortcuts) == [
        ("menuViewShortcutDesktop", False),
        ("menuViewShortcutMyDocuments", False),
        ("menuViewShortcutMyPictures", False),
        ("", True),
        ("menuViewShortcutMyComputer", False),
    ]


@pytest.mark.parametrize("magassag_eltolas", (-5, 0, 5))
def test_a_lapos_es_fanezetben_a_letiltas_render_es_kattintas_szerint_mukodik(
    nezet_app, qt_app, magassag_eltolas
):
    window, controller, engine = nezet_app
    alapmagassag = window.height()
    window.setHeight(alapmagassag + magassag_eltolas)
    assert _varj(
        qt_app, lambda: window.height() == alapmagassag + magassag_eltolas
    ), f"az ablakmagasság nem állt be ({magassag_eltolas:+} px)"
    folder_ctl = engine.rootContext().contextProperty("folderHierarchyController")
    assert folder_ctl is not None
    assert folder_ctl.treeView is False
    controller.setPeopleSort("top")
    folder_ctl.toggleAlbumThumbs()
    assert folder_ctl.albumThumbs is True

    gomb = _gyerek(window, "toolbarFolderViewPopupButton")
    _kattints(gomb, qt_app)
    menu = _gyerek(window, "toolbarFolderListMenu")
    assert _varj(qt_app, lambda: menu.property("opened") is True)
    top10 = _gyerek(window, "toolbarFolderListMenuSortPeopleByTopList")
    thumbnails = _gyerek(window, "toolbarFolderListMenuShowThumbnails")
    assert _kirajzolt_jelolo_szin(top10) != _kirajzolt_jelolo_szin(thumbnails), (
        "lapos nézetben a tiltott Top 10 jelölője nem szürke az engedélyezett "
        "Indexképek jelölőjéhez képest"
    )
    controller.setPeopleSort("name")
    _kattints(top10, qt_app)
    assert controller.peopleSort == "name", "lapos nézetben a tiltott Top 10 aktiválódott"
    _kattints(thumbnails, qt_app)
    assert folder_ctl.albumThumbs is False, "az engedélyezett Indexképek nem kapcsolt"

    tree_button = _gyerek(window, "toolbarTreeViewButton")
    _kattints(tree_button, qt_app)
    assert _varj(qt_app, lambda: folder_ctl.treeView is True), (
        "a Fanézet gomb nem váltott fanézetre"
    )
    controller.setPeopleSort("top")
    folder_ctl.toggleAlbumThumbs()
    assert folder_ctl.albumThumbs is True

    _kattints(gomb, qt_app)
    assert _varj(qt_app, lambda: menu.property("opened") is True)
    assert _kirajzolt_jelolo_szin(top10) != _kirajzolt_jelolo_szin(thumbnails), (
        "fanézetben a tiltott Indexképek jelölője nem szürke az engedélyezett "
        "Top 10 jelölőjéhez képest"
    )
    controller.setPeopleSort("name")
    _kattints(top10, qt_app)
    assert controller.peopleSort == "top", "fanézetben az engedélyezett Top 10 nem aktiválódott"
    _kattints(gomb, qt_app)
    assert _varj(qt_app, lambda: menu.property("opened") is True)
    folder_ctl.toggleAlbumThumbs()
    _kattints(thumbnails, qt_app)
    assert folder_ctl.albumThumbs is False, "fanézetben a tiltott Indexképek aktiválódott"


def test_a_none_mnemonikmarkere_es_a_magyar_felirat_hivatalos(nezet_app, qt_app):
    window, _controller, _engine = nezet_app
    menubar_menu = almenu_nyit(window, qt_app, ("menuViewThumbnailCaption",))
    assert menubar_menu.property("opened") is True
    none = _gyerek(window, "menuViewThumbCaptionNone")
    # Qt Quick MenuItem kezeli a `&`-tel jelölt billentyűt; az offscreen
    # backend nem küldi tovább a szintetikus Alt+N-t menü-parancsként.
    assert none.property("text") == "&None"

    gyoker = Path(__file__).resolve().parents[3]
    ts = ET.parse(gyoker / "src/picasapy/app/i18n/picasapy_hu.ts")
    context = next(
        elem for elem in ts.findall(".//context")
        if elem.findtext("name") == "PicasaViewMenu"
    )
    uzenet = next(
        elem for elem in context.findall("message")
        if elem.findtext("source") == "&None"
    )
    assert uzenet.findtext("translation") == "&Nincs"
    assert "stringres:eMenuView::ID_CAPNONE" in (uzenet.findtext("extracomment") or "")
