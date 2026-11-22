"""A Kép menü effektjei a nézőben a hozzájuk tartozó csempét jelölik (#7353)."""

from __future__ import annotations

import pytest
from PySide6.QtCore import QMetaObject, Qt

from tests.app.qml_functional._mappa_kep_menu_5150_helpers import (
    app_epitese,
    elokeszit,
    gyerek,
    kijelol,
    szures,
    tetel_kattintasa,
    varj,
)
from tests.app.qml_functional._felsomenupontok_helpers_4329 import _kattints

_BATCH = ("menuPictureBatchEdit",)

# Menütétel, filters-kulcs/vezérlőazonosító, fül, csempe.
_EFFEKTEK = (
    ("menuBatchAutoContrast", "autolight", 0, "editToolAutolight"),
    ("menuBatchAutoColor", "autocolor", 0, "editToolAutocolor"),
    ("menuBatchEnhance", "enhance", 0, "editToolEnhance"),
    ("menuBatchSepia", "sepia", 2, "effectSepia"),
    ("menuBatchSharpen", "unsharp", 2, "effectUnsharp"),
    ("menuBatchWarmify", "warm", 2, "effectWarm"),
    ("menuBatchFilmGrain", "grain2", 2, "effectGrain2"),
    ("menuBatchBlackWhite", "bw", 2, "effectBw"),
)


@pytest.fixture
def kep_app(qt_app, tmp_path):
    yield from app_epitese(qt_app, tmp_path)


def test_nezoben_a_kep_menu_a_celcsempehez_navigal_koteghatas_nelkul(
    kep_app, qt_app
):
    window, controller, _engine = kep_app
    elokeszit(window, qt_app, controller)

    viewer = gyerek(window, "photoViewer")
    panel = gyerek(window, "viewerEditorPanel")
    window.setProperty("viewerOpen", True)
    viewer.setProperty("currentIndex", 1)
    qt_app.processEvents()

    alap_lancok = [szures(controller, sor) for sor in range(3)]
    alap_magassag = window.height()

    for index, (tetel, _kulcs, ful, celcsempe) in enumerate(_EFFEKTEK):
        # Mindkét kijelölési mód megmarad, miközben a néző a kijelöléstől
        # különböző, második képet mutat. A három magasság a menükattintást is
        # ellenőrzi platformfüggetlen geometriával.
        sorok = [0] if index % 2 == 0 else [0, 1]
        window.resize(window.width(), alap_magassag + (-5, 0, 5)[index % 3])
        kijelol(window, qt_app, sorok)
        viewer.setProperty("currentIndex", 1)
        panel.setProperty("activeTab", 2 if ful == 0 else 0)
        qt_app.processEvents()

        tetel_kattintasa(
            window, qt_app, "&Picture", tetel, almenu_utvonal=_BATCH
        )

        cel = gyerek(window, celcsempe)
        assert varj(
            qt_app,
            lambda ful=ful, cel=cel: panel.property("activeTab") == ful
            and cel.isVisible()
            and cel.property("active") is True,
        ), (
            f"a {tetel} nem a megfelelő csempét jelölte ki "
            f"(fül={panel.property('activeTab')}, csempe={celcsempe})"
        )
        for _masik_tetel, _masik_kulcs, _masik_ful, masik_csempe in _EFFEKTEK:
            if masik_csempe != celcsempe:
                assert gyerek(window, masik_csempe).property("active") is False, (
                    f"a {tetel} mellett a {masik_csempe} is kijelölt maradt"
                )

        assert window.property("viewerOpen") is True
        assert viewer.property("currentIndex") == 1
        assert window.property("selectedIndex") == sorok[0]
        assert list(window.property("selectedIndexes")) == sorok
        assert [szures(controller, sor) for sor in range(3)] == alap_lancok, (
            f"a nézőben a {tetel} módosította valamelyik filters= láncot"
        )
        assert controller.batchEditActive is False
        assert controller.canUndoBatchEdit is False


def test_menu_kijeloles_torlese_kep_csempe_es_fulvaltas_utan(kep_app, qt_app):
    window, _controller, _engine = kep_app
    elokeszit(window, qt_app, _controller)

    viewer = gyerek(window, "photoViewer")
    panel = gyerek(window, "viewerEditorPanel")
    window.setProperty("viewerOpen", True)
    panel.setProperty("activeTab", 0)
    viewer.setProperty("currentIndex", 1)
    qt_app.processEvents()

    alap_magassag = window.height()
    hibak = []

    def menuvalasztas() -> None:
        panel.setProperty("activeTab", 0)
        tetel_kattintasa(
            window,
            qt_app,
            "&Picture",
            "menuBatchSepia",
            almenu_utvonal=_BATCH,
        )
        assert varj(
            qt_app,
            lambda: panel.property("menuEffectSelection") == "sepia",
        ), "a menü nem jelölte ki a Szépia vezérlőt"

    def ellenorizd_torolt(eszemeny: str) -> None:
        qt_app.processEvents()
        aktivak = [
            nev
            for _tetel, _kulcs, _ful, nev in _EFFEKTEK
            if gyerek(window, nev).property("active") is True
        ]
        if panel.property("menuEffectSelection") != "" or aktivak:
            hibak.append(
                f"{eszemeny}: menuEffectSelection="
                f"{panel.property('menuEffectSelection')!r}, active={aktivak}"
            )

    for eltol in (-5, 0, 5):
        window.resize(window.width(), alap_magassag + eltol)

        menuvalasztas()
        masik_index = 2 if viewer.property("currentIndex") == 1 else 1
        viewer.setProperty("currentIndex", masik_index)
        assert varj(
            qt_app,
            lambda masik_index=masik_index: viewer.property("currentIndex")
            == masik_index,
        )
        ellenorizd_torolt(f"másik képre lépés ({eltol:+d} px)")

        menuvalasztas()
        _kattints(qt_app, gyerek(window, "effectBw"))
        ellenorizd_torolt(f"másik csempe kattintása ({eltol:+d} px)")

        menuvalasztas()
        _kattints(qt_app, gyerek(window, "editTabFixes"))
        assert varj(qt_app, lambda: panel.property("activeTab") == 0), (
            "a Gyakori javítások fül nem nyílt meg valódi kattintásra"
        )
        ellenorizd_torolt(f"fülváltás ({eltol:+d} px)")

    menuvalasztas()
    assert QMetaObject.invokeMethod(
        viewer, "kerBezaras", Qt.ConnectionType.DirectConnection
    ), "a néző bezárási útja nem hívható"
    assert varj(qt_app, lambda: window.property("viewerOpen") is False), (
        "a néző bezárási útja nem zárta be a nézőt"
    )
    ellenorizd_torolt("néző bezárása")
    assert not hibak, "a menüből kijelölt csempe ragadt: " + "; ".join(hibak)

