"""#4528/#7340: a saját View options menü embersorrendje és Shortcuts almenüje."""

from __future__ import annotations

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg
from tests.support.varakozas import var_feltetelre


_ARC = "1e00280045006e00"
_NEVEK = (
    "Ada",
    "Bea",
    "Cal",
    "Dee",
    "Eve",
    "Fay",
    "Gia",
    "Hal",
    "Ida",
    "Joy",
    "Zoe",
)


def _emberek_letrehozasa(lib):
    kontaktsorok = []
    kep_szakaszok = []
    for index, nev in enumerate(_NEVEK, start=1):
        szemely_id = f"{index:016x}"
        kontaktsorok.append(f"{szemely_id}={nev};;")
        darab = 2 if nev == "Zoe" else 1
        for kep_index in range(darab):
            fajlnev = f"szemely-{index:02}-{kep_index}.jpg"
            make_jpeg(lib / fajlnev, size=(160, 120))
            kep_szakaszok.extend(
                (
                    f"[{fajlnev}]",
                    f"faces=rect64({_ARC}),{szemely_id}",
                )
            )

    ini = "[Contacts2]\n" + "\n".join(kontaktsorok + kep_szakaszok) + "\n"
    update_document(
        lib / ".picasa.ini", lambda _old: parse_document(ini), backup=False
    )


def _varj(qt_app, feltetel, masodperc: float = 10.0) -> bool:
    return var_feltetelre(qt_app, feltetel, masodperc)


def _gyerek(gyoker, nev: str):
    elem = gyoker.findChild(QObject, nev)
    assert elem is not None, f"{nev} nem található"
    return elem


def _menu_objektum(gyoker, nev: str):
    for elem in gyoker.findChildren(QObject):
        osztaly = elem.metaObject().className()
        if (
            elem.objectName() == nev
            and "Menu" in osztaly
            and "MenuItem" not in osztaly
            and elem.property("count") is not None
        ):
            return elem
    raise AssertionError(f"{nev} menüobjektum nem található")


def _menu_sor(menu, index: int):
    kifejezes = QQmlExpression(qmlContext(menu), menu, f"itemAt({index})")
    elem, hiba = kifejezes.evaluate()
    assert not hiba, kifejezes.error()
    assert elem is not None, f"a menü {index}. tétele hiányzik"
    return elem


def _menu_sor_neve(menu, index: int) -> str:
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
    return str(nev if isinstance(nev, str) else nev.toString())


def _menu_sor_nev_szerint(menu, nev: str):
    for index in range(int(menu.property("count"))):
        elem = _menu_sor(menu, index)
        if elem.objectName() == nev:
            return elem
    raise AssertionError(f"a menüben nincs {nev} tétel")


def _kattint(elem, qt_app) -> None:
    assert elem.property("visible") is True, f"{elem.objectName()} nem látható"
    assert elem.property("enabled") is True, f"{elem.objectName()} le van tiltva"
    pont = elem.mapToScene(QPointF(elem.width() / 2, elem.height() / 2)).toPoint()
    QTest.mouseClick(
        elem.window(),
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(pont),
    )
    qt_app.processEvents()


def test_folderviewpopup_people_sort_es_shortcuts(qt_app, tmp_path):
    gen = _build_qml_app(qt_app, tmp_path, kepeket_keszit=_emberek_letrehozasa)
    window, controller, _engine = next(gen)
    try:
        assert _varj(qt_app, lambda: len(controller.people) == len(_NEVEK)), (
            "a próba Emberek-listája nem töltődött be"
        )
        assert controller.peopleSort == "name"

        # Az első kattintás is tényleges sorrendváltás legyen.
        controller.setPeopleSort("count")
        assert [ember["name"] for ember in controller.people] == (
            ["Zoe", *_NEVEK[:-1]]
        )

        alapmagassag = window.height()
        gomb = _gyerek(window, "toolbarFolderViewPopupButton")
        menu = _gyerek(window, "toolbarFolderListMenu")
        tree_button = _gyerek(window, "toolbarTreeViewButton")
        rendezesek = (
            ("toolbarFolderListMenuSortPeopleByName", "name", list(_NEVEK)),
            ("toolbarFolderListMenuSortPeopleByCount", "count", ["Zoe", *_NEVEK[:-1]]),
            ("toolbarFolderListMenuSortPeopleByTopList", "top", ["Zoe", *_NEVEK[:-2]]),
        )

        for eltolás, (azon, mod, vart_nevek) in zip(
            (-5, 0, 5), rendezesek, strict=True
        ):
            window.setHeight(alapmagassag + eltolás)
            assert _varj(
                qt_app,
                lambda eltolás=eltolás: window.height() == alapmagassag + eltolás,
            ), (
                f"az ablakmagasság nem állt be ({eltolás:+} px)"
            )

            if mod == "top":
                _kattint(tree_button, qt_app)
                assert _varj(
                    qt_app,
                    lambda: window.property("menuBar").property("folderViewCtl")
                    .property("treeView") is True,
                ), "a Top 10 próbához nem kapcsolt be a fanézet"

            _kattint(gomb, qt_app)
            assert _varj(qt_app, lambda: menu.property("opened") is True), (
                "a ▾ gomb nem nyitotta meg a saját View options menüt"
            )

            emberek_tetelek = (
                "toolbarFolderListMenuSortPeopleByName",
                "toolbarFolderListMenuSortPeopleByCount",
                "toolbarFolderListMenuSortPeopleByTopList",
            )
            for nev in emberek_tetelek:
                _gyerek(window, nev)

            menu_sor_nevek = []
            for index in range(int(menu.property("count"))):
                elem = _menu_sor(menu, index)
                nev = _menu_sor_neve(menu, index)
                if not nev:
                    szoveg = elem.property("text") or elem.property("title") or ""
                    nev = str(szoveg).replace("&", "").strip()
                menu_sor_nevek.append(nev)
            assert menu_sor_nevek == [
                "toolbarFolderListMenuSortByDate",
                "toolbarFolderListMenuSortByChanged",
                "toolbarFolderListMenuSortBySize",
                "toolbarFolderListMenuSortByName",
                "toolbarFolderListMenuSortReverse",
                "",
                *emberek_tetelek,
                "",
                "toolbarFolderListMenuShortcuts",
                "",
                "toolbarFolderListMenuShowThumbnails",
                "toolbarFolderListMenuSimplifiedTree",
            ], "a View options menü sorrendje vagy elválasztói eltérnek a 2.1 táblától"

            shortcuts = _menu_objektum(window, "toolbarFolderListMenuShortcuts")
            assert [
                _menu_sor(shortcuts, index).objectName()
                for index in range(int(shortcuts.property("count")))
            ] == [
                "toolbarFolderListMenuDesktop",
                "toolbarFolderListMenuMyDocuments",
                "toolbarFolderListMenuMyPictures",
                "",
                "toolbarFolderListMenuMyComputer",
            ], "a Shortcuts almenü tételeinek sorrendje hibás"
            for nev in (
                "toolbarFolderListMenuDesktop",
                "toolbarFolderListMenuMyDocuments",
                "toolbarFolderListMenuMyPictures",
                "toolbarFolderListMenuMyComputer",
            ):
                _gyerek(window, nev)

            tetel = _gyerek(window, azon)
            _kattint(tetel, qt_app)
            assert _varj(qt_app, lambda mod=mod: controller.peopleSort == mod), (
                f"a {mod} rendezés menükattintásra nem kapcsolt be"
            )
            assert [ember["name"] for ember in controller.people] == vart_nevek, (
                f"a {mod} rendezés nem a várt személylistát adta"
            )
    finally:
        try:
            gen.close()
        except RuntimeError:
            pass
