"""#1905/1: a szerkesztő filmszalagja CSAK a saját mappa képeit mutatja.

## Mit látott a tulajdonos

Egymás mellé tett felvétel ugyanazon a mappán
(`research/Picasa3-vs-PicasaPy-fejlec-elteresek/`): a mappában **öt** kép
van.

| | mit mutat a fejléc filmszalagja |
|---|---|
| Picasa 3 | **pontosan a mappa képeit** — öt elem |
| PicasaPy | **nyolc** elem: köztük egy MÁSIK mappa kollázs-képei |

⇒ Nem geometriai, hanem **tartalmi** hiba: a szalag forrása rossz halmaz.
A felhasználó olyan képeket lát a szerkesztőben, amelyek nem abban a
mappában vannak, ahol dolgozik.

## Az ok

A szalag a TELJES rács-modellre kötött. A rács viszont FEED: több mappa
fotóit sorolja fel egymás után (`build_feed_groups`), a csillag-szűrő és
a keresés pedig végképp vegyít.

A ◀/▶ léptetés ezt már jól csinálta (`folderNeighbor`, #84) — a szalag
maradt le róla. Most ugyanazon a szerződésen áll: a mappa fotói folytonos
tartományt alkotnak.
"""

from __future__ import annotations

import time
from pathlib import Path

from PySide6.QtCore import QObject
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_jpeg


def _walk(item: QQuickItem):
    for gy in item.childItems():
        yield gy
        yield from _walk(gy)


def _elem(window, nev: str):
    for it in _walk(window.contentItem()):
        if it.objectName() == nev:
            return it
    return window.findChild(QObject, nev)


def _var(qt_app, feltetel, masodperc: float = 5.0) -> bool:
    hatarido = time.monotonic() + masodperc
    while time.monotonic() < hatarido:
        try:
            if feltetel():
                return True
        except (AttributeError, TypeError, RuntimeError):
            pass
        qt_app.processEvents()
        time.sleep(0.005)
    return False


def _ket_mappa(qml_app, qt_app):
    """`alma` 5 képpel, `korte` 3 képpel — a feed egymás után sorolja őket."""
    window, controller, _e = qml_app
    lib = Path(controller.watchedFolders[0])
    for mappa, darab in (("alma", 5), ("korte", 3)):
        (lib / mappa).mkdir(exist_ok=True)
        for i in range(darab):
            make_jpeg(lib / mappa / f"{mappa}{i}.jpg", size=(60, 40))
    controller.rescan()
    for _ in range(200):
        qt_app.processEvents()
        if controller.waitForBackgroundWorkers(0.05):
            break
    qt_app.processEvents()
    return window, controller


def _elso_sor(controller, mappanev: str) -> int:
    """A mappa első sora a rács-modellben (a próbakönyvtárban más képek is
    vannak, ezért nem kötünk fix indexet)."""
    modell = controller.photos
    for sor in range(modell.rowCount()):
        if mappanev in modell.filePathAt(sor):
            return sor
    raise AssertionError(f"a(z) {mappanev} mappa nincs a modellben")


class TestAModellSzerzodese:
    def test_folderRowRange_a_sajat_mappat_adja(self, qml_app, qt_app):
        _window, controller = _ket_mappa(qml_app, qt_app)
        modell = controller.photos
        alma = _elso_sor(controller, "alma")
        korte = _elso_sor(controller, "korte")
        assert modell.rowCount() > 8, "a rács TÖBB mappát sorol (feed)"

        kezdet_a, darab_a = modell.folderRowRange(alma)
        kezdet_b, darab_b = modell.folderRowRange(korte)
        assert (kezdet_a, darab_a) == (alma, 5)
        assert (kezdet_b, darab_b) == (korte, 3)

    def test_ervenytelen_sorra_ures_sav(self, qml_app, qt_app):
        _window, controller = _ket_mappa(qml_app, qt_app)
        assert list(controller.photos.folderRowRange(-1)) == [0, 0]
        assert list(controller.photos.folderRowRange(999)) == [0, 0]


class TestASzalagAKirajzoltAblakban:
    def _nyisd_meg(self, window, qt_app, sor: int):
        window.setProperty("selectedIndexes", [sor])
        window.setProperty("selectedIndex", sor)
        qt_app.processEvents()
        nezo = _elem(window, "photoViewer")
        nezo.setProperty("currentIndex", sor)
        window.setProperty("viewerOpen", True)
        qt_app.processEvents()
        return _elem(window, "viewerFilmstrip")

    def test_az_OTKEPES_mappaban_ot_elem(self, qml_app, qt_app):
        window, controller = _ket_mappa(qml_app, qt_app)
        alma = _elso_sor(controller, "alma")
        szalag = self._nyisd_meg(window, qt_app, alma + 1)
        assert _var(qt_app, lambda: szalag.property("mappaDarab") == 5), (
            f"a szalag {szalag.property('mappaDarab')} elemet mutat 5 helyett "
            "— idegen mappa képei is bekerültek (#1905)"
        )
        assert szalag.property("mappaKezdet") == alma

    def test_a_HAROMKEPES_mappaban_harom_elem_es_ELTOLAS(self, qml_app, qt_app):
        window, controller = _ket_mappa(qml_app, qt_app)
        korte = _elso_sor(controller, "korte")
        szalag = self._nyisd_meg(window, qt_app, korte)
        assert _var(qt_app, lambda: szalag.property("mappaDarab") == 3)
        assert szalag.property("mappaKezdet") == korte, (
            "az eltolás nélkül a szalag a MÁSIK mappa bélyegképeit rajzolná"
        )

    def test_a_szalag_SOSEM_hosszabb_a_mappajanal(self, qml_app, qt_app):
        """A foga: a teljes modellre visszakötve ez bukik."""
        window, controller = _ket_mappa(qml_app, qt_app)
        alma = _elso_sor(controller, "alma")
        korte = _elso_sor(controller, "korte")
        for sor in (alma, alma + 4, korte, korte + 2):
            szalag = self._nyisd_meg(window, qt_app, sor)
            _var(qt_app, lambda s=szalag: s.property("mappaDarab") > 0)
            assert szalag.property("mappaDarab") < controller.photos.rowCount()
