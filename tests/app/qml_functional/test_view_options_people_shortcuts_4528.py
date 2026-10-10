"""#4528: a folderviewpopup embersorrendje és Shortcuts almenüje."""

from __future__ import annotations

import time

from PySide6.QtCore import QObject, QPoint, QPointF, Qt
from PySide6.QtQml import QQmlExpression, qmlContext
from PySide6.QtTest import QTest

from picasapy.ini import parse_document, update_document
from tests.app.qml_functional.conftest import _build_qml_app
from tests.support.jpeg_factory import make_jpeg


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


def _varj(qt_app, feltetel, masodperc: float = 3.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        qt_app.processEvents()
        if feltetel():
            return True
        time.sleep(0.05)
    qt_app.processEvents()
    return bool(feltetel())


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
        menu = _gyerek(window, "menuViewFolderView")
        rendezesek = (
            ("menuViewSortPeopleByName", "name", list(_NEVEK)),
            ("menuViewSortPeopleByAmount", "count", ["Zoe", *_NEVEK[:-1]]),
            ("menuViewSortPeopleByTop10", "top", ["Zoe", *_NEVEK[:-2]]),
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

            _kattint(gomb, qt_app)
            assert _varj(qt_app, lambda: menu.property("opened") is True), (
                "a ▾ gomb nem nyitotta meg a Mappanézet menüt"
            )

            emberek_tetelek = (
                "menuViewSortPeopleByName",
                "menuViewSortPeopleByAmount",
                "menuViewSortPeopleByTop10",
            )
            for nev in emberek_tetelek:
                _gyerek(window, nev)

            menu_sor_nevek = []
            for index in range(int(menu.property("count"))):
                elem = _menu_sor(menu, index)
                nev = elem.objectName()
                if not nev:
                    szoveg = elem.property("text") or elem.property("title") or ""
                    nev = str(szoveg).replace("&", "").strip()
                menu_sor_nevek.append(nev)
            vart_sorrend = (
                "menuViewSortByDate",
                "menuViewSortByRecent",
                "menuViewSortBySize",
                "menuViewSortByName",
                "menuViewSortReverse",
                *emberek_tetelek,
                "Shortcuts",
                "menuViewAlbumThumbnails",
                "menuViewSimplifiedTreeView",
            )
            sorrendi_indexek = [menu_sor_nevek.index(nev) for nev in vart_sorrend]
            assert sorrendi_indexek == sorted(sorrendi_indexek), (
                "a Sort People és Shortcuts tételek sorrendje nem követi a specet"
            )

            shortcuts = _menu_objektum(window, "menuViewFolderViewShortcuts")
            gyors_tetelek = (
                "menuViewShortcutMyComputer",
                "menuViewShortcutMyPictures",
                "menuViewShortcutMyDocuments",
                "menuViewShortcutDesktop",
            )
            assert [
                _menu_sor(shortcuts, index).objectName()
                for index in range(int(shortcuts.property("count")))
            ] == list(gyors_tetelek), "a Shortcuts almenü tételeinek sorrendje hibás"
            for nev in gyors_tetelek:
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
