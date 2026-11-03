"""#6477: az egyesített effektfül rácsa nem csúszhat a hisztogram alá.

A tulajdonos az 1.0.29 saját kiadásképén vette észre: kis ablakmagasságnál
a Glimmer és a régi effektek rácsának (#6443) alsó sora a bal fiók aljára
dokkolt „Hisztogram és fényképezőgép-adatok” doboz alá került. Az ok: a
rács mindig legalább 4,5 sor magas volt, a szerkesztőpanel pedig nem tudott
a hisztogramról, és a Visszavonás/Újra sor is a fiók legaljáig mehetett.

A teszt a kirajzolt elemek helyét méri: a rács alja és a Visszavonás/Újra
sor alja is a hisztogram teteje fölött van, kis és nagy ablakmagasságnál is.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest
from PySide6.QtCore import QObject
from PySide6.QtQml import QQmlEngine, QQmlExpression
from PySide6.QtQuick import QQuickItem

from support.jpeg_factory import make_minta_jpeg
from tests.app.qml_functional.conftest import (
    _build_qml_app,
    _module_qml_warnings,  # noqa: F401 - modul-fixture
    _module_user_folder_guard,  # noqa: F401 - modul-fixture
)
from tests.support.varakozas import var_feltetelre


def _kep(folder):
    make_minta_jpeg(folder / "a.jpg", size=(320, 240), seed=6477)


@pytest.fixture(scope="module")
def app(qt_app, tmp_path_factory, _module_qml_warnings, _module_user_folder_guard):  # noqa: F811
    from picasapy.app.effect_thumbnails import EffectThumbnailProvider
    from picasapy.index import open_index, photos_in_folder
    from tests.support.szinkron_kepszolgaltato import SzinkronValodiBelyegkep

    root = tmp_path_factory.mktemp("effektracs-6477")
    generator = _build_qml_app(qt_app, root, kepeket_keszit=_kep, valodi_belyegkep=True)
    window, _controller, engine = next(generator)
    # valódi effekt-előnézet: a kiadásképen egyszínű csempe nem lehet
    with open_index(root / "index.db") as conn:
        rekordok = {str(r.id): r for r in photos_in_folder(conn, root / "kepek")}
    engine.addImageProvider(
        "effectthumb", SzinkronValodiBelyegkep(EffectThumbnailProvider(rekordok.get))
    )
    yield window
    generator.close()


def _walk(item: QQuickItem):
    yield item
    for child in item.childItems():
        yield from _walk(child)


def _item(window, name: str):
    for item in _walk(window.contentItem()):
        if item.objectName() == name:
            return item
    found = window.findChild(QObject, name)
    assert found is not None, f"{name} nincs a kirajzolt felületen"
    return found


def _kesz_elonezet(kep) -> bool:
    forras = kep.property("source")
    forras = forras.toString() if hasattr(forras, "toString") else str(forras)
    return (
        forras.startswith("image://effectthumb/")
        and bool(QQmlExpression(QQmlEngine.contextForObject(kep), kep, "status === 1").evaluate())
        and kep.property("paintedWidth") > 0
        and max(kep.property("implicitWidth"), kep.property("implicitHeight")) > 16
    )


def _also(item) -> float:
    return item.mapToScene(item.boundingRect().bottomLeft()).y()


def _teteje(item) -> float:
    return item.mapToScene(item.boundingRect().topLeft()).y()


@pytest.mark.parametrize("magassag", [600, 680, 760, 1000])
def test_a_racs_es_a_gombsor_a_hisztogram_folott_er_veget(app, qt_app, magassag):
    window = app
    window.resize(window.width(), magassag)
    assert var_feltetelre(qt_app, lambda: abs(window.height() - magassag) < 1
                          or window.height() > magassag, 5.0)
    window.setProperty("viewerOpen", True)
    _item(window, "photoViewer").setProperty("currentIndex", 0)
    panel = _item(window, "viewerEditorPanel")
    panel.setProperty("activeTab", 5)
    viewport = _item(window, "effectsGrid4Viewport")
    hisztogram = _item(window, "viewerHistogramBox")
    gombsor = _item(window, "editorGlobalUndoRow")
    assert var_feltetelre(qt_app, lambda: viewport.isVisible() and viewport.height() > 0, 10.0)
    elonezet = _item(window, "effectNightVisionThumb")
    assert var_feltetelre(qt_app, lambda: _kesz_elonezet(elonezet), 20.0), (
        "a csempén nem töltődött be valódi előnézet"
    )
    for _ in range(5):
        qt_app.processEvents()
    window.grabWindow()

    hisztogram_teteje = _teteje(hisztogram)
    assert _also(viewport) <= hisztogram_teteje + 0.5, (
        f"{window.height()} px magas ablakban a rács alja ({_also(viewport):.0f}) "
        f"a hisztogram teteje ({hisztogram_teteje:.0f}) alá csúszott"
    )
    assert _also(gombsor) <= hisztogram_teteje + 0.5, (
        f"{window.height()} px magas ablakban a Visszavonás/Újra sor a hisztogram alá került"
    )
    sor = _item(window, "effectRoundedEdges").y() - _item(window, "effectMatte").y()
    assert viewport.height() >= sor - 0.5, "legalább egy csemposor látsszon"
    assert viewport.height() <= sor * 4.5 + 0.5
    if window.height() >= 1000:
        assert viewport.height() == pytest.approx(sor * 4.5, abs=0.5), (
            "elég helynél a mért 4,5 sor maradjon"
        )

    kimenet = os.environ.get("PICASAPY_RENDER_KIMENET")
    if kimenet:
        Path(kimenet).mkdir(parents=True, exist_ok=True)
        window.grabWindow().save(str(Path(kimenet) / f"effektracs-6477-{magassag}.png"))
