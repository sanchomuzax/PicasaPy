"""#7090: a kötegelt effekt és a forgatás FIGYELMEZTET, ha videó kimaradt.

## Mit mér ez a fájl

A vezérlő-szintű teszt (`tests/app/test_kotegelt_effekt_tipushiba_7090.py`)
a jelzés kibocsátását méri. Ez a fájl a másik felét: a felhasználó LÁT-e
valamit. Az állítások ezért a **lebegő értesítősáv** (#1129) olvasóira
szólnak (`cellCount`, `lastTitle`), azt a szöveget mérve, ami a képernyőn
megjelenik.

A jelzést a VALÓDI QML-komponensek váltják ki: a Kép menü
`batchApplyEffectRequested` jelzése (a Csoportos szerkesztés és a forgatás
tételei ezt küldik), illetve a rács helyi menüjének
`rotateRightRequested` jelzése.

## Miért angol szövegeket állít

A fixture nem telepít `QTranslator`-t, tehát a `qsTr()` a FORRÁSSZTRINGET
adja vissza. A magyar felirat a `picasapy_hu.ts`-ből mért állításokban él
(`test_kotegelt_effekt_tipushiba_7090.py`).

## A várt szöveg KIÍRT literál

A várt szöveget nem a termék saját konstansából olvassuk (a #1576 első
köre így nyelte el az elrontott feliratot): minden szöveg betű szerint ki
van írva, az eredeti `stringres.xml` szerint.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from conftest import _build_qml_app
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt
from support.jpeg_factory import make_jpeg
from support.qt_wait import wait_for_photo_op

from picasapy.ini import load_document
from tests.support.varakozas import var_feltetelre

#: `IDS_SOME_EDITS_FAILED_TYPE` angol forrása (két szóköz az eredetié).
EFFEKT_SZOVEG = (
    "Some images were not modified because of the file type.  "
    "Note that effects cannot be applied to movies."
)
#: `IDS_ROT_TYPEFAILED` angol forrása.
FORGATAS_SZOVEG = (
    "One or more images could not be rotated because of the file type."
)


def _kepek_es_videot(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(320, 160))
    make_jpeg(lib / "b.jpg", size=(100, 100))
    # szándékosan érvénytelen videó: a típust a kiterjesztés dönti el
    (lib / "c.mp4").write_bytes(b"\x00" * 64)


def _csak_kepek(lib: Path) -> None:
    make_jpeg(lib / "a.jpg", size=(320, 160))
    make_jpeg(lib / "b.jpg", size=(100, 100))


@pytest.fixture
def vegyes_app(qt_app, tmp_path):
    """A teljes alkalmazás: két kép és egy videó a rácsban."""
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_kepek_es_videot)


@pytest.fixture
def kepes_app(qt_app, tmp_path):
    """A teljes alkalmazás: csak két kép a rácsban."""
    yield from _build_qml_app(qt_app, tmp_path, kepeket_keszit=_csak_kepek)


def _sav(window) -> QObject:
    sav = window.findChild(QObject, "picasaNotifier")
    assert sav is not None, "a lebegő értesítősáv nincs a fában"
    return sav


def _info_ablak(window) -> QObject:
    """#7121: a figyelmeztetés az eredeti modális Információ-ablakában jelenik meg."""
    ablak = window.findChild(QObject, "operationInfoDialog")
    assert ablak is not None, "az Információ-ablak nincs a fában"
    return ablak


def _info_szoveg(window) -> str:
    elem = window.findChild(QObject, "operationInfoText")
    return elem.property("text") if elem is not None else ""


def _menusor(window) -> QObject:
    bar = window.property("menuBar")
    assert bar is not None, "a menüsor nincs a fában"
    return bar


def _mindent_kijelol(window, controller, qt_app) -> list[int]:
    sorok = list(range(len(controller.photos.photos)))
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()
    return sorok


def _csak_kepeket_kijelol(window, controller, qt_app) -> list[int]:
    sorok = [
        i
        for i, photo in enumerate(controller.photos.photos)
        if photo.kind != "video"
    ]
    window.setProperty("selectedIndexes", sorok)
    window.setProperty("selectedIndex", sorok[0])
    qt_app.processEvents()
    return sorok


def _filters(controller, name: str) -> str | None:
    photo = next(p for p in controller.photos.photos if p.name == name)
    ini = Path(photo.folder_path) / ".picasa.ini"
    if not ini.exists():
        return None
    section = load_document(ini).section(name)
    return section.get("filters") if section is not None else None


def _kotegelt_effekt(window, controller, qt_app, nev: str) -> None:
    """A Kép menü Csoportos szerkesztés jelzése: a háttérszál bevárva."""
    wait_for_photo_op(
        controller,
        lambda: _menusor(window).batchApplyEffectRequested.emit(nev),
        qt_app=qt_app,
    )
    qt_app.processEvents()


def _helyi_menu(window, qt_app, row: int = 0) -> QObject:
    grid = window.findChild(QObject, "photoGrid")
    assert grid is not None, "photoGrid nem található"
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", row),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()
    menu = window.findChild(QObject, "photoContextMenu")
    assert menu is not None, "photoContextMenu nem található"
    return menu


class TestKotegeltEffektFigyelmeztet:
    def test_vegyes_kijeloles_utan_LATSZIK_a_figyelmeztetes(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        sav = _sav(window)
        assert sav.property("cellCount") == 0, "a sáv nem üresen indult"
        _mindent_kijelol(window, controller, qt_app)

        _kotegelt_effekt(window, controller, qt_app, "sepia")

        ablak = _info_ablak(window)
        assert var_feltetelre(
            qt_app, lambda: ablak.property("opened") is True, 5.0
        ), "a kihagyott videóról a felhasználó SEMMIT nem lát"
        assert _info_szoveg(window) == EFFEKT_SZOVEG, _info_szoveg(window)

    def test_a_kepek_modosulnak_a_video_nem(self, vegyes_app, qt_app):
        window, controller, _engine = vegyes_app
        _mindent_kijelol(window, controller, qt_app)

        _kotegelt_effekt(window, controller, qt_app, "sepia")

        for nev in ("a.jpg", "b.jpg"):
            assert "sepia" in (_filters(controller, nev) or ""), nev
        assert _filters(controller, "c.mp4") is None

    def test_csak_kepes_kijelolesnel_NINCS_figyelmeztetes(
        self, kepes_app, qt_app
    ):
        window, controller, _engine = kepes_app
        sav = _sav(window)
        _csak_kepeket_kijelol(window, controller, qt_app)

        _kotegelt_effekt(window, controller, qt_app, "sepia")

        assert sav.property("cellCount") == 0, (
            "tisztán képes kijelölésnél nem jelenhet meg semmi: "
            f"{sav.property('lastTitle')!r}"
        )

    def test_csak_kepes_kijelolesnel_a_vegyes_app_sem_zajos(
        self, vegyes_app, qt_app
    ):
        """Ugyanabban a mappában, de a videó nélkül kijelölve is hallgat."""
        window, controller, _engine = vegyes_app
        sav = _sav(window)
        _csak_kepeket_kijelol(window, controller, qt_app)

        _kotegelt_effekt(window, controller, qt_app, "bw")

        assert sav.property("cellCount") == 0


class TestForgatasFigyelmeztet:
    def test_vegyes_kijeloles_forgatasa_utan_LATSZIK_a_figyelmeztetes(
        self, vegyes_app, qt_app
    ):
        window, controller, _engine = vegyes_app
        _mindent_kijelol(window, controller, qt_app)

        menu = _helyi_menu(window, qt_app, row=0)
        menu.rotateRightRequested.emit()
        qt_app.processEvents()

        ablak = _info_ablak(window)
        assert var_feltetelre(
            qt_app, lambda: ablak.property("opened") is True, 5.0
        ), "a kihagyott videóról a felhasználó SEMMIT nem lát"
        assert _info_szoveg(window) == FORGATAS_SZOVEG, _info_szoveg(window)
        # A forgatás maga változatlan: a fotók elfordultak, a videó nem.
        for photo in controller.photos.photos:
            if photo.kind != "video":
                assert photo.rotate_steps == 1, photo.name

    def test_a_menusor_forgatasa_is_figyelmeztet(self, vegyes_app, qt_app):
        """A Kép ▸ Forgatás jobbra tétel útja: ugyanaz a jelzés."""
        window, controller, _engine = vegyes_app
        _mindent_kijelol(window, controller, qt_app)

        _menusor(window).batchApplyEffectRequested.emit("rotate_cw")
        qt_app.processEvents()

        ablak = _info_ablak(window)
        assert var_feltetelre(qt_app, lambda: ablak.property("opened") is True, 5.0)
        assert _info_szoveg(window) == FORGATAS_SZOVEG

    def test_csak_kepes_kijelolesnel_a_forgatas_NEM_figyelmeztet(
        self, kepes_app, qt_app
    ):
        window, controller, _engine = kepes_app
        sav = _sav(window)
        _csak_kepeket_kijelol(window, controller, qt_app)

        menu = _helyi_menu(window, qt_app, row=0)
        menu.rotateRightRequested.emit()
        qt_app.processEvents()

        assert sav.property("cellCount") == 0, sav.property("lastTitle")
