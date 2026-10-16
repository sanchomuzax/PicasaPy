"""#4533: a fotó helyi menüjének „Társítás…" (Open With) tétele.

A tétel eddig helyfoglaló volt. Most a kattintás a társított alkalmazások
listáját nyitja meg, és a választott alkalmazással megnyitja a képet. A
teszt valódi kattintásokkal megy végig a menün és a párbeszéden; csak a
lista forrását (a `.desktop` fájlokat) és a tényleges indítást helyettesíti.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, QPoint, QPointF, Qt
from PySide6.QtTest import QTest

import picasapy.fileops.open_with as open_with_module
from picasapy.fileops.open_with import OpenWithApp
from tests.app.qml_functional._felsomenupontok_helpers_4329 import (
    _ABLAKMAGASSAG_ELTOLASOK,
    _kattints,
    _magassag,
    _objektum,
    _varj,
)

_ALKALMAZASOK = [
    OpenWithApp("gimp.desktop", "GNU Image Manipulation Program", "gimp %U"),
    OpenWithApp("eog.desktop", "Image Viewer", "eog --new-instance %F"),
]


def _elem(window, nev):
    """A menüpont a főablak, vagy a helyi menü gyermekfájából."""
    talalat = _objektum(window, nev)
    if talalat is None:
        menu = window.findChild(QObject, "photoContextMenu")
        talalat = menu.findChild(QObject, nev) if menu is not None else None
    return talalat


def _nyisd_meg_helyi_menut(window, qt_app, sor: int) -> None:
    grid = window.findChild(QObject, "photoGrid")
    QMetaObject.invokeMethod(
        window,
        "openPhotoContextMenu",
        Qt.ConnectionType.DirectConnection,
        Q_ARG("QVariant", sor),
        Q_ARG("QVariant", grid),
        Q_ARG("QVariant", 5),
        Q_ARG("QVariant", 5),
    )
    qt_app.processEvents()


def _kattints_ablakban(qt_app, window, item) -> None:
    """Kattintás a `window` (a fixture ablaka) koordinátáján.

    Az `item.window()` helyett a fixture ablakát adjuk át: a delegált
    `window()`-ja egy átmeneti Python-burkolót ad, és annak életciklusa
    alatt az ablak egyik kattintásnál eltűnt a teszt elől."""
    assert item.isEnabled(), f"{item.objectName()}: a sor le van tiltva"
    center = item.mapToScene(QPointF(item.width() / 2, item.height() / 2))
    QTest.mouseClick(
        window,
        Qt.MouseButton.LeftButton,
        Qt.KeyboardModifier.NoModifier,
        QPoint(round(center.x()), round(center.y())),
    )
    qt_app.processEvents()


def _lathato_sorok(lista, nev: str):
    """A lista látható delegáltjai, felülről lefelé.

    A delegáltak a ListView `contentItem`-jének VIZUÁLIS gyermekei; a
    QObject-fában a delegált-modell alatt élnek, a `findChildren` nem látja
    őket."""
    sorok = [
        item for item in lista.property("contentItem").childItems()
        if item.objectName() == nev and item.property("visible") is True
    ]
    return sorted(sorok, key=lambda item: item.mapToScene(QPointF(0, 0)).y())


@pytest.fixture
def linux_valaszto(monkeypatch):
    """A Linux-ág (a mi választónk) kényszerítése minden platformon.

    Windowson a `Társítás…` a héj saját párbeszédét hívja
    (`hasNativeOpenWith()`), és a mi `openWithDialog`-unk meg sem nyílik —
    ez a CI windowsos lábán a „a Társítás nem nyitotta meg a választót"
    bukás oka (a QML: `Main.qml` `onOpenWithRequested`). A választó-ág
    tesztjének ezért a platformot rögzítenie kell; a Windows-ágat külön teszt
    fedi."""
    monkeypatch.setattr(open_with_module, "_platform", lambda: "linux")


@pytest.fixture
def indulas_fake(monkeypatch, linux_valaszto):
    """A lista és az indítás helyettesítése; a hívásokat rögzíti."""
    inditasok = []
    monkeypatch.setattr(
        open_with_module, "apps_for_file", lambda path: list(_ALKALMAZASOK)
    )
    monkeypatch.setattr(
        open_with_module,
        "launch_app",
        lambda app, path: inditasok.append((app.app_id, Path(path))),
    )
    return inditasok


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_tarsitas_kattintas_listazza_es_megnyitja_a_kepet(
    qml_app, qt_app, indulas_fake, height_offset
):
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    _nyisd_meg_helyi_menut(window, qt_app, 0)
    tetel = _elem(window, "contextMenuOpenWith")
    assert tetel is not None, "a Társítás tétel nem található"
    assert tetel.property("enabled") is True, "a Társítás tétel le van tiltva"

    _kattints(qt_app, tetel)

    assert _varj(
        qt_app,
        lambda: (
            _objektum(window, "openWithDialog") is not None
            and _objektum(window, "openWithDialog").property("visible") is True
        ),
    ), "a Társítás nem nyitotta meg a választót"
    lista = _objektum(window, "openWithAppList")
    assert lista is not None
    assert lista.property("count") == len(_ALKALMAZASOK)

    assert _varj(
        qt_app,
        lambda: len(_lathato_sorok(lista, "openWithAppItem")) == len(_ALKALMAZASOK),
    ), "a lista sorai nem épültek fel"
    _kattints_ablakban(qt_app, window, _lathato_sorok(lista, "openWithAppItem")[1])
    _kattints(qt_app, _elem(window, "openWithOpenButton"))

    assert _varj(qt_app, lambda: len(indulas_fake) == 1)
    app_id, megnyitott = indulas_fake[0]
    assert app_id == "eog.desktop"
    assert megnyitott == Path(controller.photos.filePathAt(0))


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_tarsitas_ures_listanal_nem_indit_semmit(
    qml_app, qt_app, monkeypatch, linux_valaszto, height_offset
):
    inditasok = []
    monkeypatch.setattr(open_with_module, "apps_for_file", lambda path: [])
    monkeypatch.setattr(
        open_with_module,
        "launch_app",
        lambda app, path: inditasok.append(app),
    )
    window, _controller, _engine = qml_app
    _magassag(window, height_offset)
    _nyisd_meg_helyi_menut(window, qt_app, 0)
    _kattints(qt_app, _elem(window, "contextMenuOpenWith"))

    assert _varj(
        qt_app,
        lambda: _objektum(window, "openWithEmptyLabel") is not None
        and _objektum(window, "openWithEmptyLabel").property("visible") is True,
    ), "üres listánál nincs visszajelzés"
    assert _elem(window, "openWithOpenButton").property("enabled") is False
    assert inditasok == []


@pytest.mark.parametrize("height_offset", _ABLAKMAGASSAG_ELTOLASOK)
def test_tarsitas_windowson_a_hej_sajat_parbeszedet_hivja(
    qml_app, qt_app, monkeypatch, indulas_fake, height_offset
):
    """Windowson a kattintás a héj párbeszédét indítja, a mi választónk nem nyílik."""
    monkeypatch.setattr(open_with_module, "_platform", lambda: "win32")
    hejhivasok = []
    monkeypatch.setattr(
        open_with_module,
        "open_with_dialog_windows",
        lambda path: hejhivasok.append(Path(path)),
    )
    window, controller, _engine = qml_app
    _magassag(window, height_offset)
    _nyisd_meg_helyi_menut(window, qt_app, 0)
    _kattints(qt_app, _elem(window, "contextMenuOpenWith"))

    assert _varj(qt_app, lambda: len(hejhivasok) == 1), (
        "a Társítás nem hívta a héj párbeszédét"
    )
    assert hejhivasok[0] == Path(controller.photos.filePathAt(0))
    dialog = _objektum(window, "openWithDialog")
    assert dialog is None or dialog.property("visible") is not True
    assert indulas_fake == []
